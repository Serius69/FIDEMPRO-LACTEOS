"""
test_gbm_ui.py
==============
Exposición del modo **GBM** en la UI de configuración de simulación.

Valida el cableado de punta a punta de la elección de distribución del usuario:
  · (a) elegir 'gbm' (Simulation.demand_distribution='gbm') → MonteCarloConfig
        usa el branch GBM con parámetros calibrados desde la demanda histórica,
        con prioridad sobre la FDP y sobre la preferencia 'auto'.
  · (b) sin elección (campo vacío) → se conserva el comportamiento i.i.d. previo
        (distribución derivada de fk_fdp.distribution_type).
  · e2e: el validador + SimulationCore.create_simulation persisten el campo y
        from_simulation() sobre la fila real produce 'gbm'.

    cd findempro
    python -m pytest simulate/tests/test_gbm_ui.py -v
"""
from types import SimpleNamespace

import numpy as np
import pytest

from simulate.core.monte_carlo import MonteCarloConfig


# ── Serie GBM sintética reutilizable (niveles positivos con memoria) ─────────
def _gbm_levels(n=400, seed=7):
    rng = np.random.default_rng(seed)
    levels = [1000.0]
    for _ in range(n - 1):
        levels.append(levels[-1] * float(np.exp(rng.normal(0.0005, 0.02))))
    return levels


def _fake_simulation(demand_distribution, dist_type=1, seed=7):
    """Stub mínimo con la superficie que consume MonteCarloConfig.from_simulation."""
    levels = _gbm_levels(seed=seed)
    arr = np.asarray(levels, dtype=float)
    return SimpleNamespace(
        demand_distribution=demand_distribution,
        fk_fdp=SimpleNamespace(distribution_type=dist_type),
        confidence_level=0.95,
        random_seed=42,
        duration_in_days=30,
        get_demand_history_array=lambda: arr,
        get_demand_statistics=lambda: {
            'mean': float(arr.mean()), 'std': float(arr.std()),
            'min': float(arr.min()), 'max': float(arr.max()),
            'median': float(np.median(arr)), 'count': int(arr.size),
        },
    )


# ── (a) Elegir GBM en la UI activa el branch GBM ─────────────────────────────
def test_ui_choice_gbm_activates_gbm_branch():
    sim = _fake_simulation('gbm', dist_type=1)   # FDP diría 'normal'
    cfg = MonteCarloConfig.from_simulation(sim, company_profile=None, n_scenarios=50)
    assert cfg.distribution == 'gbm'                 # override gana sobre la FDP
    # Parámetros GBM calibrados desde la demanda histórica (no None).
    assert cfg.gbm_volatility is not None and cfg.gbm_volatility > 0
    assert cfg.gbm_s0 is not None
    s0, media_d, sigma_d = cfg.resolve_gbm_params()
    assert sigma_d > 0 and s0 > 0


def test_ui_choice_gbm_overrides_auto_preference():
    """GBM elegido explícitamente gana incluso sobre distribution_preference='auto'."""
    sim = _fake_simulation('gbm', dist_type=1)
    profile = SimpleNamespace(
        distribution_preference='auto',
        get_seasonality_factors=lambda: [1.0] * 12,
    )
    cfg = MonteCarloConfig.from_simulation(sim, company_profile=profile, n_scenarios=50)
    assert cfg.distribution == 'gbm'


# ── (b) Sin elección se conserva el comportamiento i.i.d. previo ─────────────
@pytest.mark.parametrize("dist_type,expected", [
    (1, 'normal'), (3, 'lognormal'), (4, 'gamma'), (6, 'poisson'),
])
def test_empty_choice_preserves_iid_from_fdp(dist_type, expected):
    sim = _fake_simulation('', dist_type=dist_type)
    cfg = MonteCarloConfig.from_simulation(sim, company_profile=None, n_scenarios=50)
    assert cfg.distribution == expected
    assert cfg.gbm_volatility is None            # sin calibración GBM en i.i.d.


def test_invalid_override_falls_back_to_fdp():
    """Un valor basura en el campo no fuerza nada: cae al comportamiento por FDP."""
    sim = _fake_simulation('no-existe', dist_type=3)
    cfg = MonteCarloConfig.from_simulation(sim, company_profile=None, n_scenarios=50)
    assert cfg.distribution == 'lognormal'


# ── e2e: validador + create_simulation persisten el campo; from_simulation ok ─
@pytest.mark.django_db
def test_create_simulation_persists_and_calibrates_gbm():
    from django.contrib.auth.models import User
    from business.services.seed_service import IndustrySeeder
    from business.data.bolivia_industries import get_spec
    from product.models import Product
    from questionary.models import QuestionaryResult
    from simulate.models import ProbabilisticDensityFunction
    from simulate.utils.simulation_core_utils import SimulationCore
    from simulate.views.simulate_init_view import SimulateShowView

    user = User.objects.create_user(username="gbm-ui-tester", password="x")
    IndustrySeeder(user).seed_business(get_spec(7))   # 'Otros', rápido
    product = Product.objects.filter(fk_business__fk_user=user, is_active=True).first()
    qr = QuestionaryResult.objects.filter(
        fk_questionary__fk_product=product, is_active=True).first()
    fdp = ProbabilisticDensityFunction.objects.filter(
        fk_business=product.fk_business).first()
    demand = SimulateShowView()._extract_demand_data(qr)

    sim = SimulationCore().create_simulation({
        'fk_questionary_result': qr.id,
        'quantity_time': 30,
        'unit_time': 'days',
        'demand_history': demand,
        'fk_fdp_id': fdp.id,
        'demand_distribution': 'gbm',
    })
    sim.refresh_from_db()
    assert sim.demand_distribution == 'gbm'          # persistido

    cfg = MonteCarloConfig.from_simulation(sim, company_profile=None, n_scenarios=50)
    assert cfg.distribution == 'gbm'
    assert cfg.gbm_volatility is not None and cfg.gbm_volatility > 0


@pytest.mark.django_db
def test_create_simulation_default_is_iid():
    """Sin demand_distribution en el POST, la simulación queda en modo i.i.d. (vacío)."""
    from django.contrib.auth.models import User
    from business.services.seed_service import IndustrySeeder
    from business.data.bolivia_industries import get_spec
    from product.models import Product
    from questionary.models import QuestionaryResult
    from simulate.models import ProbabilisticDensityFunction
    from simulate.utils.simulation_core_utils import SimulationCore
    from simulate.views.simulate_init_view import SimulateShowView

    user = User.objects.create_user(username="iid-ui-tester", password="x")
    IndustrySeeder(user).seed_business(get_spec(7))
    product = Product.objects.filter(fk_business__fk_user=user, is_active=True).first()
    qr = QuestionaryResult.objects.filter(
        fk_questionary__fk_product=product, is_active=True).first()
    fdp = ProbabilisticDensityFunction.objects.filter(
        fk_business=product.fk_business).first()
    demand = SimulateShowView()._extract_demand_data(qr)

    sim = SimulationCore().create_simulation({
        'fk_questionary_result': qr.id,
        'quantity_time': 30,
        'unit_time': 'days',
        'demand_history': demand,
        'fk_fdp_id': fdp.id,
        # sin 'demand_distribution'
    })
    sim.refresh_from_db()
    assert sim.demand_distribution == ''             # default retrocompatible
    cfg = MonteCarloConfig.from_simulation(sim, company_profile=None, n_scenarios=50)
    assert cfg.distribution != 'gbm'                 # i.i.d. según la FDP
    assert cfg.gbm_volatility is None
