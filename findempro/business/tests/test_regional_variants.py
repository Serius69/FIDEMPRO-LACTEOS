"""
Tests de variantes regionales por ciudad (business.data.bolivia_regions +
IndustrySeeder.seed_regional + seed_bolivia --regions).

Cubre: mapeo ciudad→región con fallback 1.0, escalado de precios por factor, y
que sembrar 2 ciudades del mismo tipo no viola el UNIQUE(name, fk_user) activo.
"""
from io import StringIO

import pytest
from django.contrib.auth.models import User
from django.core.management import call_command

from business.data import bolivia_regions as reg
from business.data.bolivia_industries import get_spec
from business.models import Business
from product.models import Product
from questionary.models import Answer, QuestionaryResult
from simulate.views.simulate_init_view import SimulateShowView
from business.services.seed_service import IndustrySeeder, scale_baseline


# ─────────────────────────────────────────────────────────────────────────────
# Mapeo ciudad → región + factor (unidad, sin DB)
# ─────────────────────────────────────────────────────────────────────────────
_PRESSURES = {  # como los devolvería regional_price_pressure() (media ≈ 1.0)
    "Conurbación La Paz": 1.01,
    "Oruro": 1.015,
    "Tarija": 0.98,
}


def test_city_price_factor_maps_conurbation():
    # El Alto y La Paz comparten "Conurbación La Paz".
    assert reg.city_price_factor("El Alto", _PRESSURES) == 1.01
    assert reg.city_price_factor("La Paz", _PRESSURES) == 1.01
    assert reg.city_price_factor("Oruro", _PRESSURES) == 1.015
    assert reg.city_price_factor("Tarija", _PRESSURES) == 0.98


def test_city_price_factor_unmapped_falls_back_to_one():
    # Santa Cruz no está mapeada → 1.0 (sin sesgo). Cochabamba SÍ está mapeada
    # (→ "Región Metropolitana Kanata") pero cae a 1.0 aquí porque Kanata no está
    # en este dict de señal de prueba (fallback por región ausente).
    assert reg.city_price_factor("Santa Cruz", _PRESSURES) == 1.0
    assert reg.city_price_factor("Cochabamba", _PRESSURES) == 1.0
    assert reg.city_price_factor("Ciudad Inexistente", _PRESSURES) == 1.0


def test_city_price_factor_cochabamba_maps_to_kanata():
    # Con Kanata en la señal, Cochabamba toma su factor real (conurbación).
    pressures = {**_PRESSURES, "Región Metropolitana Kanata": 1.0365}
    assert reg.city_price_factor("Cochabamba", pressures) == 1.0365


def test_city_price_factor_without_signal_is_one():
    # Sin señal IPC (dict vacío) → 1.0 aunque la ciudad esté mapeada.
    assert reg.city_price_factor("Oruro", {}) == 1.0
    # Ciudad mapeada pero región ausente en el dict de señal → 1.0.
    assert reg.city_price_factor("Potosí", _PRESSURES) == 1.0


def test_city_price_factor_none_reads_live_signal(monkeypatch):
    # pressures=None delega en regional_price_pressure(); con señal inyectada usa
    # esa; sin señal (None) cae a 1.0.
    monkeypatch.setattr(reg, "regional_price_pressure", lambda: _PRESSURES)
    assert reg.city_price_factor("Oruro") == 1.015
    monkeypatch.setattr(reg, "regional_price_pressure", lambda: None)
    assert reg.city_price_factor("Oruro") == 1.0


# ─────────────────────────────────────────────────────────────────────────────
# Escalado de baseline (unidad)
# ─────────────────────────────────────────────────────────────────────────────
def test_scale_baseline_scales_price_and_cost():
    base = get_spec(7).products[0]
    scaled = scale_baseline(base, 1.10)
    assert scaled is not base                                   # no muta el catálogo
    assert scaled.price == round(base.price * 1.10, 2)
    assert scaled.unit_cost == round(base.unit_cost * 1.10, 2)
    assert scaled.daily_demand == base.daily_demand            # demanda intacta
    assert scaled.name == base.name


def test_scale_baseline_factor_one_is_noop():
    base = get_spec(7).products[0]
    assert scale_baseline(base, 1.0) is base


# ─────────────────────────────────────────────────────────────────────────────
# seed_regional — dos ciudades del mismo tipo sin colisión de unique
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture
def user(db):
    return User.objects.create_user(username="region-tester", password="x")


def test_seed_two_cities_same_type_no_unique_clash(user):
    spec = get_spec(7)  # 'Otros' — pocos productos, rápido
    seeder = IndustrySeeder(user)
    b_alto = seeder.seed_regional(spec, "El Alto", price_factor=1.05)
    b_scz = seeder.seed_regional(spec, "Santa Cruz", price_factor=1.0)

    assert b_alto.id != b_scz.id
    assert b_alto.type == b_scz.type == 7
    # Nombres distintos (incluyen la ciudad) → no viola UNIQUE(name, fk_user).
    assert b_alto.name != b_scz.name
    assert "El Alto" in b_alto.name and "Santa Cruz" in b_scz.name
    assert b_alto.location == "El Alto" and b_scz.location == "Santa Cruz"
    # Ambos activos y contados.
    assert Business.objects.filter(fk_user=user, type=7, is_active=True).count() == 2


def test_seed_regional_scales_prices_in_db(user):
    spec = get_spec(7)
    base_price = spec.products[0].price
    business = IndustrySeeder(user).seed_regional(spec, "El Alto", price_factor=1.20)

    product = Product.objects.get(fk_business=business, name=spec.products[0].name)
    qr = QuestionaryResult.objects.filter(
        fk_questionary__fk_product=product, is_active=True).first()
    pvp = Answer.objects.filter(
        fk_questionary_result=qr, fk_question__fk_variable__initials="PVP").first()
    assert float(pvp.answer) == round(base_price * 1.20, 2)


def test_seed_regional_is_idempotent_by_name(user):
    spec = get_spec(7)
    seeder = IndustrySeeder(user)
    b1 = seeder.seed_regional(spec, "Oruro", price_factor=1.0)
    b2 = seeder.seed_regional(spec, "Oruro", price_factor=1.0)
    assert b1.id == b2.id
    assert Business.objects.filter(fk_user=user, type=7, is_active=True).count() == 1


def test_regional_variant_simulates_end_to_end(user):
    """La variante regional produce demanda histórica leíble por el motor."""
    business = IndustrySeeder(user).seed_regional(get_spec(7), "El Alto", price_factor=1.1)
    product = Product.objects.filter(fk_business=business, is_active=True).first()
    qr = QuestionaryResult.objects.filter(
        fk_questionary__fk_product=product, is_active=True).first()
    series = SimulateShowView()._extract_demand_data(qr)
    assert isinstance(series, list) and len(series) >= 30


# ─────────────────────────────────────────────────────────────────────────────
# Comando seed_bolivia --regions
# ─────────────────────────────────────────────────────────────────────────────
def test_command_regions_seeds_variants(user):
    out = StringIO()
    call_command("seed_bolivia", "--user", user.username, "--types", "7",
                 "--regions", "El Alto,Santa Cruz", stdout=out)
    text = out.getvalue()
    assert "Variantes sembradas: 2" in text
    names = set(Business.objects.filter(
        fk_user=user, is_active=True).values_list("name", flat=True))
    assert any("El Alto" in n for n in names)
    assert any("Santa Cruz" in n for n in names)
