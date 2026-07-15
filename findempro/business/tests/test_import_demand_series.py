"""
Tests del importador de series de demanda reales
(business.services.demand_import + management command import_demand_series).
"""
import json
from io import StringIO

import pandas as pd
import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError

from business.services import demand_import as di
from business.services.seed_service import IndustrySeeder
from business.data.bolivia_industries import get_spec
from questionary.models import Answer, QuestionaryResult
from simulate.views.simulate_init_view import SimulateShowView


# ─────────────────────────────────────────────────────────────────────────────
# Unidad — limpieza / agrupación / advertencias (sin DB)
# ─────────────────────────────────────────────────────────────────────────────
def test_clean_series_drops_invalid():
    clean, dropped = di.clean_series([10, "20", -5, float("nan"), float("inf"), "x", 30])
    assert clean == [10.0, 20.0, 30.0]
    assert dropped == 4


def test_sample_warnings_thresholds():
    assert di.sample_warnings(45) == []                      # suficiente
    assert any("recomendados" in w for w in di.sample_warnings(20))   # 10..29
    assert any("abortar" in w for w in di.sample_warnings(5))         # <10


def test_group_series_long_format_orders_by_date():
    df = pd.DataFrame({
        "product": ["Leche", "Leche", "Queso", "Leche"],
        "date": ["2025-01-03", "2025-01-01", "2025-01-02", "2025-01-02"],
        "demand": [30, 10, 99, 20],
    })
    g = di.group_series(df)
    assert g[("Leche", None)] == [10, 20, 30]     # ordenado por fecha
    assert g[("Queso", None)] == [99]


def test_group_series_single_product_no_product_col():
    df = pd.DataFrame({"demand": [1, 2, 3]})
    g = di.group_series(df, single_product="Leche")
    assert g == {("Leche", None): [1, 2, 3]}


def test_group_series_missing_demand_col_raises():
    with pytest.raises(KeyError):
        di.group_series(pd.DataFrame({"foo": [1]}))


def test_load_dataframe_csv_bolivian_format(tmp_path):
    p = tmp_path / "d.csv"
    p.write_text("product;date;demand\nLeche;2025-01-01;2450,5\n", encoding="utf-8")
    df = di.load_dataframe(str(p), sep=";", decimal=",")
    assert df["demand"].iloc[0] == pytest.approx(2450.5)


# ─────────────────────────────────────────────────────────────────────────────
# Integración — con un producto sembrado real
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture
def dairy_product(db):
    """Siembra el negocio lácteo y devuelve (user, primer producto)."""
    user = User.objects.create_user(username="tester", password="x")
    seeder = IndustrySeeder(user)
    seeder.seed_business(get_spec(1))
    from product.models import Product
    product = Product.objects.filter(fk_business__fk_user=user, is_active=True).first()
    return user, product


def _reader_series(product):
    """La serie exacta que el motor extraería para este producto."""
    qr = QuestionaryResult.objects.filter(
        fk_questionary__fk_product=product, is_active=True).first()
    return SimulateShowView()._extract_demand_data(qr)


def test_resolve_product_found_and_ambiguity(dairy_product):
    user, product = dairy_product
    assert di.resolve_product(product.name, user=user).id == product.id
    with pytest.raises(LookupError):
        di.resolve_product("No Existe", user=user)


def test_write_series_replaces_synthetic(dairy_product):
    user, product = dairy_product
    before = _reader_series(product)
    assert before, "el seed debe dejar una serie sintética"

    real = [100.0 + i for i in range(40)]
    res = di.write_series(product, real, replace=True)

    assert res.status == "imported"
    assert res.n_previous_deleted >= 1          # borró la sintética
    # Una sola answer DH activa por resultado, con la serie real:
    got = _reader_series(product)
    assert got == real
    qr = QuestionaryResult.objects.filter(
        fk_questionary__fk_product=product, is_active=True).first()
    dh_answers = [a for a in qr.fk_question_result_answer.all()
                  if a.fk_question.question == di.DEMAND_QUESTION_TEXT]
    assert len(dh_answers) == 1
    assert json.loads(dh_answers[0].answer) == real


def test_write_series_append_prepends_existing(dairy_product):
    user, product = dairy_product
    di.write_series(product, [1.0, 2.0, 3.0], replace=True)
    di.write_series(product, [4.0, 5.0], replace=False)   # append
    assert _reader_series(product) == [1.0, 2.0, 3.0, 4.0, 5.0]


def test_dry_run_writes_nothing(dairy_product):
    user, product = dairy_product
    before = _reader_series(product)
    res = di.write_series(product, [7.0] * 40, replace=True, dry_run=True)
    assert res.results_updated == 1
    assert _reader_series(product) == before   # intacto


# ─────────────────────────────────────────────────────────────────────────────
# End-to-end — el management command
# ─────────────────────────────────────────────────────────────────────────────
def test_command_imports_from_csv(dairy_product, tmp_path):
    user, product = dairy_product
    csv = tmp_path / "demanda.csv"
    rows = ["product,date,demand"]
    for i in range(35):
        rows.append(f"{product.name},2025-01-{(i % 28) + 1:02d},{500 + i}")
    csv.write_text("\n".join(rows), encoding="utf-8")

    out = StringIO()
    call_command("import_demand_series", str(csv), "--user", "tester", stdout=out)

    assert "Importadas: 1" in out.getvalue()
    assert len(_reader_series(product)) == 35


def test_command_missing_file_errors(dairy_product):
    with pytest.raises(CommandError):
        call_command("import_demand_series", "/no/existe.csv", "--user", "tester")
