"""
Tests del adaptador forex→demanda (business.services.forex_adapter +
management command import_forex_demand): la única serie REAL por-negocio
disponible (casa de cambio, forex-erp) cableada al simulador.
"""
from io import StringIO

import pandas as pd
import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError

from business.services import forex_adapter as fa
from business.services.seed_service import IndustrySeeder
from business.data.bolivia_industries import get_spec
from questionary.models import QuestionaryResult
from simulate.views.simulate_init_view import SimulateShowView


# ─────────────────────────────────────────────────────────────────────────────
# Fixture sintética con la MISMA forma que el export real: sin fecha exacta,
# solo mes + día de semana. 2025-06 = mes parcial (pocas ops).
# ─────────────────────────────────────────────────────────────────────────────
def _ops_df():
    rows = []
    # Mes parcial: 4 ops (vs ~60 de los completos → < 50 % de la mediana).
    rows += [("2025-06", "Monday", 1000.0)] * 4
    # Dos meses completos con forma semanal marcada (domingo casi cerrado).
    for mes, n_mon in (("2025-07", 20), ("2025-08", 30)):
        rows += [(mes, "Monday", 1000.0)] * n_mon
        rows += [(mes, "Wednesday", 2000.0)] * 20
        rows += [(mes, "Saturday", 500.0)] * 9
        rows += [(mes, "Sunday", 500.0)] * 1
    return pd.DataFrame(rows, columns=["mes", "dia_semana", "total_bs"])


def _month_sum(daily, mes):
    return sum(v for d, v in zip(daily.dates, daily.values)
               if f"{d.year}-{d.month:02d}" == mes)


def test_disaggregation_preserves_monthly_totals():
    daily = fa.build_daily_series(_ops_df(), metric="ops")
    # Total mensual EXACTO al real (50 y 60 ops), repartido en días calendario.
    assert _month_sum(daily, "2025-07") == pytest.approx(50, abs=0.1)
    assert _month_sum(daily, "2025-08") == pytest.approx(60, abs=0.1)
    assert len(daily.values) == 31 + 31          # jul + ago, todos los días


def test_disaggregation_metric_bs():
    daily = fa.build_daily_series(_ops_df(), metric="bs")
    # jul: 20×1000 + 20×2000 + 9×500 + 1×500 = 65.000 Bs
    assert _month_sum(daily, "2025-07") == pytest.approx(65000, abs=1)
    assert daily.metric == "bs"


def test_weekday_shape_is_real():
    daily = fa.build_daily_series(_ops_df(), metric="ops")
    w = daily.weekday_weights
    # Ops por día en la fixture: Mon 54 (4+20+30) > Wed 40 > Sat 18 > Sun 2.
    assert w["Sunday"] < w["Saturday"] < w["Wednesday"] < w["Monday"]
    # Y la serie diaria refleja esa forma: domingos = los valores mínimos.
    sundays = [v for d, v in zip(daily.dates, daily.values) if d.weekday() == 6]
    wednesdays = [v for d, v in zip(daily.dates, daily.values) if d.weekday() == 2]
    assert max(sundays) < min(wednesdays)


def test_partial_months_dropped_by_default():
    daily = fa.build_daily_series(_ops_df())
    assert daily.months_dropped == ["2025-06"]
    assert daily.months_used == ["2025-07", "2025-08"]
    kept = fa.build_daily_series(_ops_df(), include_partial=True)
    assert kept.months_dropped == []
    assert "2025-06" in kept.months_used


def test_load_operations_rejects_foreign_csv(tmp_path):
    p = tmp_path / "otra_cosa.csv"
    p.write_text("a,b\n1,2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="faltan columnas"):
        fa.load_operations(str(p))


# ─────────────────────────────────────────────────────────────────────────────
# End-to-end — arquetipo tipo 19 sembrado + comando + reader real del motor
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture
def financial_business(db):
    user = User.objects.create_user(username="forex-tester", password="x")
    IndustrySeeder(user).seed_business(get_spec(19))
    return user


def test_spec_19_includes_casa_de_cambio():
    names = [p.name for p in get_spec(19).products]
    assert "Cambio de Divisas" in names


def test_command_end_to_end_replaces_synthetic(financial_business, tmp_path):
    user = financial_business
    csv = tmp_path / "ops.csv"
    _ops_df().to_csv(csv, index=False)

    out = StringIO()
    call_command("import_forex_demand", str(csv), "--user", user.username,
                 stdout=out)
    assert "Serie real importada" in out.getvalue()

    from product.models import Product
    product = Product.objects.get(
        name="Cambio de Divisas", fk_business__fk_user=user, is_active=True)
    qr = QuestionaryResult.objects.filter(
        fk_questionary__fk_product=product, is_active=True).first()
    got = SimulateShowView()._extract_demand_data(qr)

    daily = fa.build_daily_series(_ops_df(), metric="ops")
    assert len(got) == len(daily.values) == 62
    assert got == pytest.approx(daily.values)     # la que lee el motor = la real


def test_command_missing_product_hints_seed(db, tmp_path):
    User.objects.create_user(username="sin-seed", password="x")
    csv = tmp_path / "ops.csv"
    _ops_df().to_csv(csv, index=False)
    with pytest.raises(CommandError, match="seed_bolivia"):
        call_command("import_forex_demand", str(csv), "--user", "sin-seed",
                     stdout=StringIO())
