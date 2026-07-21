"""
test_vectorized_engine.py
=========================
Tests del motor Monte Carlo vectorizado (CPU NumPy / GPU CuPy).

Validan:
  · Equivalencia numérica EXACTA con el motor escalar por celda (mismas demandas).
  · Equivalencia de estadísticos agregados con muestreo aleatorio.
  · El guard ``can_vectorize`` acepta modelos aritméticos y rechaza los que
    divergen del escalar.
  · Selección de backend y fallback a CPU vía ``FINDEMPRO_GPU=off``.

Se ejecutan en CPU (NumPy) en CI; la ruta GPU se ejercita en hosts con CuPy.

  cd findempro
  python -m pytest simulate/tests/test_vectorized_engine.py -v
"""

import numpy as np
import pytest

from simulate.core.discrete_engine import (
    CompanyConfig, DiscreteEventEngine, OperationScenario,
)
from simulate.core.monte_carlo import MonteCarloConfig
from simulate.core import gpu_backend
from simulate.core.vectorized_engine import VectorizedMonteCarlo, can_vectorize


# ── Helpers ──────────────────────────────────────────────────────────────────

class _MockArea:
    def __init__(self, name='General'):
        self.name = name


class _MockEquation:
    def __init__(self, expression: str, area: str = 'General'):
        self.expression = expression
        self.fk_area = _MockArea(area)


def _standard_company(T=12) -> CompanyConfig:
    """Modelo PyME estándar: IT=DE*PVU, CTV=DE*CUP, TG=CTV+CF, GT=IT-TG."""
    return CompanyConfig(
        sector='retail', business_name='PYME Test',
        demand_variable='DE', revenue_variable='IT',
        cost_variable='TG', profit_variable='GT',
        equations=[
            _MockEquation('IT = DE * PVU'),
            _MockEquation('CTV = DE * CUP'),
            _MockEquation('TG = CTV + CF'),
            _MockEquation('GT = IT - TG'),
        ],
        system_constants={'PVU': 15.0, 'CUP': 9.0, 'CF': 2000.0},
        total_periods=T,
    )


@pytest.fixture(autouse=True)
def _force_cpu_backend(monkeypatch):
    """Fuerza NumPy/CPU para reproducibilidad en CI y resetea el backend."""
    monkeypatch.setenv('FINDEMPRO_GPU', 'off')
    gpu_backend.reset_backend_for_tests()
    yield
    gpu_backend.reset_backend_for_tests()


# ── Tests ────────────────────────────────────────────────────────────────────

def test_backend_off_uses_numpy():
    assert gpu_backend.backend_name() == 'numpy/cpu'
    assert gpu_backend.on_gpu() is False


def test_can_vectorize_accepts_standard_model():
    assert can_vectorize(_standard_company()) is True


def test_can_vectorize_rejects_divergent_model():
    # División por una constante cero: el motor escalar captura ZeroDivisionError
    # y devuelve 0.0; el vectorizado (arrays) produce inf. El guard detecta la
    # divergencia y devuelve False → el pipeline usará el motor escalar.
    company = CompanyConfig(
        demand_variable='DE', revenue_variable='IT',
        cost_variable='TG', profit_variable='GT',
        equations=[_MockEquation('IT = DE / CERO')],
        system_constants={'CERO': 0.0},
        total_periods=5,
    )
    assert can_vectorize(company) is False


def test_vectorized_matches_scalar_per_cell():
    """Equivalencia EXACTA por celda con demandas deterministas."""
    company = _standard_company(T=1)
    demands = [500.0, 1000.0, 1500.0, 2000.0, 3333.0]

    xp = gpu_backend.get_array_module()
    from simulate.core.vectorized_engine import _build_vectorized_table, _solve_vectorized
    grid = xp.asarray(demands).reshape(1, len(demands))
    table = _build_vectorized_table(company, {}, grid, xp.asarray([1.0]).reshape(1, 1), xp)
    vres = _solve_vectorized(company, table, xp)
    combined = {**table, **vres}

    engine = DiscreteEventEngine(company)
    for i, d in enumerate(demands):
        engine.reset_state()
        r = engine.run_period(OperationScenario(period_index=0, demand_value=d, seasonality_factor=1.0))
        for name, sval in (('IT', r.revenue), ('TG', r.costs), ('GT', r.profit)):
            vval = float(gpu_backend.asnumpy(xp.asarray(combined[name])).reshape(-1)[i])
            assert np.isclose(vval, float(sval), rtol=1e-9, atol=1e-6), f"{name}@{d}: {vval} != {sval}"


def test_vectorized_aggregate_matches_scalar():
    """Estadísticos agregados coinciden bajo muestreo aleatorio (mismo seed)."""
    company = _standard_company(T=20)
    mc = MonteCarloConfig(n_scenarios=2000, n_periods=20, random_seed=7,
                          distribution='normal', demand_mean=1000.0, demand_std=150.0)

    # Vectorizado
    d_v, r_v, _c_v, p_v = VectorizedMonteCarlo(mc, company).run()

    # Escalar de referencia (mismo muestreo stateless-per-scenario)
    rng = np.random.default_rng(mc.random_seed)
    engine = DiscreteEventEngine(company)
    prof = []
    for _t in range(company.total_periods):
        demands = np.maximum(rng.normal(mc.demand_mean, mc.demand_std, mc.n_scenarios), 0.0)
        for d in demands:
            engine.reset_state()
            prof.append(engine.run_period(
                OperationScenario(period_index=_t, demand_value=float(d), seasonality_factor=1.0)
            ).profit)
    prof = np.array(prof)

    assert np.isclose(p_v.mean(), prof.mean(), rtol=1e-3)
    assert np.isclose(p_v.std(), prof.std(), rtol=2e-2)


def test_run_grid_shapes():
    company = _standard_company(T=15)
    mc = MonteCarloConfig(n_scenarios=500, n_periods=15, random_seed=1,
                          distribution='normal', demand_mean=800.0, demand_std=100.0)
    d, r, c, p = VectorizedMonteCarlo(mc, company).run_grid()
    assert d.shape == r.shape == c.shape == p.shape == (15, 500)
    assert np.all(np.isfinite(p))


def test_vectorized_seasonality_maps_day_to_month():
    """La estacionalidad MENSUAL se aplica por mes (día // 30) % 12, no por día % 12.

    Bug previo: el índice de día módulo len(factors) comprimía el año a un ciclo de
    12 días. Aquí, con σ diminuta, la media de demanda por período revela el factor
    del mes correcto: días 0-29 → mes 0, 30-59 → mes 1, 60-89 → mes 2.
    """
    factors = [1.0, 2.0, 3.0] + [1.0] * 9
    T = 90  # 3 meses de 30 días
    company = _standard_company(T=T)
    mc = MonteCarloConfig(
        n_scenarios=400, n_periods=T, random_seed=11,
        distribution='normal', demand_mean=1000.0, demand_std=1.0,
        seasonality_factors=factors,
    )
    d_grid, _r, _c, _p = VectorizedMonteCarlo(mc, company).run_grid()
    assert np.isclose(d_grid[0].mean(),  1000.0 * factors[0], rtol=0.05)  # mes 0
    assert np.isclose(d_grid[29].mean(), 1000.0 * factors[0], rtol=0.05)  # mes 0
    assert np.isclose(d_grid[30].mean(), 1000.0 * factors[1], rtol=0.05)  # mes 1
    assert np.isclose(d_grid[60].mean(), 1000.0 * factors[2], rtol=0.05)  # mes 2


@pytest.mark.parametrize('dist', ['normal', 'lognormal', 'gamma', 'uniform', 'exponential', 'poisson'])
def test_all_distributions_run(dist):
    company = _standard_company(T=6)
    mc = MonteCarloConfig(n_scenarios=300, n_periods=6, random_seed=3,
                          distribution=dist, demand_mean=1000.0, demand_std=150.0)
    d, r, c, p = VectorizedMonteCarlo(mc, company).run()
    assert d.shape == (6 * 300,)
    assert np.all(d >= 0.0)  # demanda no-negativa
    assert np.all(np.isfinite(p))
