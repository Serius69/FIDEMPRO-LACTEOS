"""
Tests de simulate.utils.simulation_core_utils.SimulationCore (motor escalar,
path síncrono invocado desde simulate_init_view._handle_simulation_execution):

  · execute_simulation ya NO se traga silenciosamente los días que fallan
    (antes: except Exception: continue, sin dejar rastro) — ahora los cuenta
    y los expone en el resumen devuelto.
  · random_seed (capturado del form pero antes ignorado por el motor escalar,
    que usaba el estado global de np.random) ahora sí se usa: dos corridas
    con la misma semilla producen resultados idénticos.

    cd findempro
    python -m pytest simulate/tests/test_simulation_core_utils.py -v
"""
import pytest
from django.contrib.auth.models import User

from business.data.bolivia_industries import get_spec
from business.services.seed_service import IndustrySeeder
from product.models import Product
from questionary.models import QuestionaryResult
from simulate.models import ProbabilisticDensityFunction, ResultSimulation
from simulate.utils.simulation_core_utils import SimulationCore
from simulate.views.simulate_init_view import SimulateShowView


def _seed_product(username):
    user = User.objects.create_user(username=username, password="x")
    IndustrySeeder(user).seed_business(get_spec(7))  # 'Otros', rápido
    product = Product.objects.filter(fk_business__fk_user=user, is_active=True).first()
    qr = QuestionaryResult.objects.filter(
        fk_questionary__fk_product=product, is_active=True).first()
    fdp = ProbabilisticDensityFunction.objects.filter(
        fk_business=product.fk_business).first()
    demand = SimulateShowView()._extract_demand_data(qr)
    return user, product, qr, fdp, demand


def _create_simulation(qr, fdp, demand, *, quantity_time=5, random_seed=None):
    return SimulationCore().create_simulation({
        'fk_questionary_result': qr.id,
        'quantity_time': quantity_time,
        'unit_time': 'days',
        'demand_history': demand,
        'fk_fdp_id': fdp.id,
        'random_seed': random_seed,
    })


# ─────────────────────────────────────────────────────────────────────────────
# [P1] Días fallidos ya no se tragan en silencio
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_execute_simulation_reports_skipped_days_instead_of_fake_success(monkeypatch):
    user, product, qr, fdp, demand = _seed_product("skip-day-tester")
    sim = _create_simulation(qr, fdp, demand, quantity_time=5)

    original = SimulationCore._simulate_single_day_complete

    def flaky(self, simulation_instance, simulation_data, day_index, simulation_state):
        if day_index == 2:
            raise RuntimeError("boom: día 2 simulado falla a propósito")
        return original(self, simulation_instance, simulation_data, day_index, simulation_state)

    monkeypatch.setattr(SimulationCore, "_simulate_single_day_complete", flaky)

    core = SimulationCore()
    summary = core.execute_simulation(sim)

    # El resumen marca el hueco -- ya no finge éxito completo.
    assert summary['days_total'] == 5
    assert summary['days_completed'] == 4
    assert summary['days_skipped'] == 1
    assert summary['skipped_day_indices'] == [2]

    # Solo se guardaron los 4 días que sí calcularon.
    saved = ResultSimulation.objects.filter(fk_simulation=sim)
    assert saved.count() == 4
    saved_day_indices = sorted(
        r.variables['_metadata']['day_index'] for r in saved
    )
    assert saved_day_indices == [0, 1, 3, 4]
    assert 2 not in saved_day_indices


@pytest.mark.django_db
def test_execute_simulation_no_failures_reports_zero_skipped():
    user, product, qr, fdp, demand = _seed_product("no-skip-tester")
    sim = _create_simulation(qr, fdp, demand, quantity_time=3)

    summary = SimulationCore().execute_simulation(sim)

    assert summary['days_skipped'] == 0
    assert summary['skipped_day_indices'] == []
    assert summary['days_completed'] == summary['days_total'] == 3
    assert ResultSimulation.objects.filter(fk_simulation=sim).count() == 3


# ─────────────────────────────────────────────────────────────────────────────
# [P1] random_seed reproducible en el motor escalar
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_same_random_seed_gives_identical_results():
    user, product, qr, fdp, demand = _seed_product("seed-tester-a")
    sim_a = _create_simulation(qr, fdp, demand, quantity_time=10, random_seed=12345)
    SimulationCore().execute_simulation(sim_a)
    demands_a = list(
        ResultSimulation.objects.filter(fk_simulation=sim_a)
        .order_by('date').values_list('demand_mean', flat=True)
    )

    # Segunda simulación, mismo producto/cuestionario, misma semilla.
    sim_b = _create_simulation(qr, fdp, demand, quantity_time=10, random_seed=12345)
    SimulationCore().execute_simulation(sim_b)
    demands_b = list(
        ResultSimulation.objects.filter(fk_simulation=sim_b)
        .order_by('date').values_list('demand_mean', flat=True)
    )

    assert demands_a == demands_b
    assert len(demands_a) == 10


@pytest.mark.django_db
def test_different_random_seed_gives_different_results():
    user, product, qr, fdp, demand = _seed_product("seed-tester-b")
    sim_a = _create_simulation(qr, fdp, demand, quantity_time=10, random_seed=111)
    SimulationCore().execute_simulation(sim_a)
    demands_a = list(
        ResultSimulation.objects.filter(fk_simulation=sim_a)
        .order_by('date').values_list('demand_mean', flat=True)
    )

    sim_b = _create_simulation(qr, fdp, demand, quantity_time=10, random_seed=222)
    SimulationCore().execute_simulation(sim_b)
    demands_b = list(
        ResultSimulation.objects.filter(fk_simulation=sim_b)
        .order_by('date').values_list('demand_mean', flat=True)
    )

    assert demands_a != demands_b
