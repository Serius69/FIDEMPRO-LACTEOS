"""
Tests del sembrado multi-industria boliviano (business.services.seed_service
+ management command seed_bolivia).
"""
import ast

import pytest
from django.contrib.auth.models import User

from business.models import Business
from business.data.bolivia_industries import INDUSTRIES, get_spec
from business.services.seed_service import IndustrySeeder, generate_answers, ProductBaseline
from product.models import Product
from variable.models import Variable, Equation
from questionary.models import Questionary, Question, QuestionaryResult, Answer
from simulate.models import ProbabilisticDensityFunction


def test_catalog_covers_19_types():
    """El catálogo debe cubrir los 19 BusinessType con al menos 1 producto cada uno."""
    assert set(INDUSTRIES.keys()) == set(range(1, 20))
    for bt, spec in INDUSTRIES.items():
        assert spec.business_type == bt
        assert spec.products, f"tipo {bt} sin productos"
        for p in spec.products:
            assert p.price > p.unit_cost, f"{p.name}: precio debe superar el costo"
            assert p.daily_demand > 0 and p.employees > 0


# Arquetipos micro emblemáticos (expansión 2026-07) → (producto, tipo).
_MICRO_ARCHETYPES = {
    "Internet y Fotocopias": 7,
    "Prenda de Confección": 9,          # textiles El Alto
    "Artículos de Ferretería": 10,
    "Venta de Puesto de Mercado": 10,   # comercio informal
    "Corte de Cabello": 12,             # belleza
    "Reparación Mecánica": 12,          # talleres
    "Lavado de Ropa": 12,
    "Venta de Medicamentos": 13,        # farmacia de barrio
    "Tour Turístico": 16,               # turismo
    "Cambio de Divisas": 19,            # casa de cambio (serie real forex)
}


def test_catalog_includes_micro_archetypes():
    """Los rubros micro emblemáticos deben existir, en su tipo, a escala micro."""
    for name, bt in _MICRO_ARCHETYPES.items():
        match = [p for p in INDUSTRIES[bt].products if p.name == name]
        assert match, f"falta el arquetipo '{name}' en el tipo {bt}"
        p = match[0]
        # Escala micro: pocos empleados y sueldos coherentes (≥ ~mínimo/empleado).
        assert p.employees <= 4, f"{name}: {p.employees} empleados no es escala micro"
        assert p.monthly_salaries >= 2750 * p.employees * 0.9, \
            f"{name}: sueldos por debajo del salario mínimo"


def test_generate_answers_shape():
    """generate_answers produce drivers económicos + histórico de demanda >=30 pts."""
    base = ProductBaseline(
        name="Test", unit="unidades", price=10.0, unit_cost=6.0, daily_demand=500,
        daily_clients=100, employees=5, monthly_salaries=15000, daily_fixed_cost=400,
        transport_unit_cost=0.2, marketing_monthly=800, seasonal=True, peak_months=[12],
    )
    ans = generate_answers(base, n_history=40)
    assert ans["PVP"] == 10.0
    assert ans["CUIP"] == 6.0
    assert ans["NEPP"] == 5
    assert ans["ED"] == "Sí"
    assert isinstance(ans["DH"], list) and len(ans["DH"]) >= 30
    assert all(v >= 0 for v in ans["DH"])


@pytest.mark.django_db
def test_seed_single_type_builds_full_chain():
    """Sembrar un tipo crea la cadena completa lista para simular."""
    user = User.objects.create_user(username="seed_tester", password="x")
    spec = get_spec(7)  # 'Otros' — pocos productos (rápido)
    seeder = IndustrySeeder(user)
    business = seeder.seed_business(spec)

    assert business is not None
    assert business.type == 7
    assert Business.objects.filter(fk_user=user, type=7).count() == 1

    products = Product.objects.filter(fk_business=business)
    assert products.count() == len(spec.products)

    # El producto del PRIMER baseline del spec (el orden de products no está garantizado).
    product = products.get(name=spec.products[0].name)
    assert Variable.objects.filter(fk_product=product).count() > 100
    assert Equation.objects.filter(fk_area__fk_product=product).count() > 50
    assert Questionary.objects.filter(fk_product=product).exists()

    # PDF de negocio.
    assert ProbabilisticDensityFunction.objects.filter(fk_business=business).exists()

    # QuestionaryResult con respuestas, incluida la demanda histórica >=30 pts.
    qr = QuestionaryResult.objects.filter(
        fk_questionary__fk_product=product).first()
    assert qr is not None
    assert Answer.objects.filter(fk_questionary_result=qr).count() >= 40

    dh = Answer.objects.filter(
        fk_questionary_result=qr, fk_question__fk_variable__initials="DH").first()
    assert dh is not None
    series = ast.literal_eval(dh.answer)
    assert isinstance(series, list) and len(series) >= 30

    # El precio sembrado coincide con el baseline boliviano.
    pvp = Answer.objects.filter(
        fk_questionary_result=qr, fk_question__fk_variable__initials="PVP").first()
    assert float(pvp.answer) == spec.products[0].price


@pytest.mark.django_db
def test_seed_is_idempotent():
    user = User.objects.create_user(username="idem_tester", password="x")
    spec = get_spec(7)
    seeder = IndustrySeeder(user)
    b1 = seeder.seed_business(spec)
    b2 = seeder.seed_business(spec)  # segunda vez: no duplica
    assert b1.id == b2.id
    assert Business.objects.filter(fk_user=user, type=7, is_active=True).count() == 1


@pytest.mark.django_db
def test_seed_force_recreates_without_unique_clash():
    """--force debe recrear el negocio liberando el UNIQUE(name, fk_user) NOCASE,
    aun cuando el modelo title-casea el nombre al guardar (regresión)."""
    user = User.objects.create_user(username="force_tester", password="x")
    spec = get_spec(7)
    seeder = IndustrySeeder(user)
    b1 = seeder.seed_business(spec)
    b2 = seeder.seed_business(spec, force=True)  # no debe lanzar IntegrityError
    assert b2.id != b1.id
    # Sólo queda un negocio activo del tipo; el anterior fue desactivado+renombrado.
    assert Business.objects.filter(fk_user=user, type=7, is_active=True).count() == 1
    old = Business.objects.get(id=b1.id)
    assert old.is_active is False
    assert old.name != b2.name  # nombre liberado para el nuevo


def test_seed_command_defaults_to_one_demo_with_simulation():
    from business.management.commands.seed_bolivia import Command

    options = Command().create_parser("manage.py", "seed_bolivia").parse_args([])

    assert options.types == "7"
    assert options.run_sim is True
    assert options.mc_scenarios == 200


@pytest.mark.django_db
def test_onboarding_get_shows_type_selector(client):
    """La pantalla de onboarding ofrece el selector de los 19 rubros."""
    from django.urls import reverse
    user = User.objects.create_user(username="onb_get", password="x")
    client.force_login(user)
    resp = client.get(reverse("pages:pages.register_elements"))
    assert resp.status_code == 200
    assert b'name="business_type"' in resp.content


@pytest.mark.django_db
@pytest.mark.slow
def test_onboarding_post_routes_to_selected_industry(client):
    """POST con business_type crea el negocio del rubro elegido (no lácteo)."""
    from django.urls import reverse
    user = User.objects.create_user(username="onb_post", password="x")
    client.force_login(user)
    resp = client.post(
        reverse("pages:pages.register_elements_create"),
        {"confirm_setup": "true", "business_type": "7"},
    )
    assert resp.status_code == 302
    biz = Business.objects.filter(fk_user=user, type=7).first()
    assert biz is not None
    assert Product.objects.filter(fk_business=biz).count() == len(get_spec(7).products)


@pytest.mark.django_db
@pytest.mark.slow
def test_seeded_business_runs_simulation():
    """Verifica el pipeline Monte Carlo end-to-end sobre un tipo no lácteo."""
    from simulate.models import Simulation
    from simulate.services.simulation_service import SimulationService

    user = User.objects.create_user(username="sim_tester", password="x")
    spec = get_spec(7)
    business = IndustrySeeder(user).seed_business(spec)

    qr = QuestionaryResult.objects.filter(
        fk_questionary__fk_product__fk_business=business).first()
    fdp = ProbabilisticDensityFunction.objects.filter(fk_business=business).first()
    dh = Answer.objects.filter(
        fk_questionary_result=qr, fk_question__fk_variable__initials="DH").first()
    demand_history = ast.literal_eval(dh.answer)

    sim = Simulation.objects.create(
        quantity_time=10, unit_time="days", fk_fdp=fdp,
        demand_history=demand_history, fk_questionary_result=qr,
        confidence_level=0.95, random_seed=7, is_active=True,
    )
    res = SimulationService().run_full_pipeline(sim, n_monte_carlo=50)
    assert "period_results" in res
    assert len(res["period_results"]) == 10
    assert res["period_results"][0]["revenue_mean"] > 0
    # Baselines calibrados: una línea no estacional debe simular utilidad positiva
    # (regresión — antes el overhead de todo el negocio hundía cada producto).
    assert res["period_results"][0]["profit_mean"] > 0
