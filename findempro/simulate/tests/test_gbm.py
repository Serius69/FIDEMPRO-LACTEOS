"""
test_gbm.py
===========
Tests del Movimiento Browniano Geométrico (GBM) como proceso de demanda con
memoria temporal (``simulate/core/gbm.py``) y su integración en el generador
Monte Carlo escalar y vectorizado.

Validan:
  · Calibración: round-trip de (deriva, volatilidad) por MLE + corrección de Itô.
  · Simulación: trayectorias positivas, con memoria (cumsum), y marginal correcto.
  · Integración: ``distribution='gbm'`` produce paths con memoria en ambos motores,
    mientras las distribuciones i.i.d. existentes quedan intactas (regresión).
  · Determinismo por semilla.

Se ejecutan en CPU (NumPy), sin base de datos Django:

  cd findempro
  python -m pytest simulate/tests/test_gbm.py -v
"""

import numpy as np
import pytest

from simulate.core import gbm
from simulate.core.monte_carlo import MonteCarloConfig, ScenarioGenerator
from simulate.core.vectorized_engine import _sample_demand_grid


# ── Calibración ──────────────────────────────────────────────────────────────

def test_calibrar_gbm_recupera_parametros():
    """La calibración recupera la media/σ de los log-retornos generados."""
    rng = np.random.default_rng(42)
    m_true, s_true = 0.0008, 0.02
    r = rng.normal(m_true, s_true, size=50_000)
    p = gbm.calibrar_gbm(r, periodos_anio=365)
    assert p['media_d'] == pytest.approx(m_true, abs=2e-4)
    assert p['sigma_d'] == pytest.approx(s_true, abs=2e-4)


def test_calibrar_gbm_correccion_ito():
    """mu_a incluye la corrección de Itô y sigma_a anualiza por √períodos."""
    rng = np.random.default_rng(1)
    r = rng.normal(0.001, 0.03, size=10_000)
    p = gbm.calibrar_gbm(r, periodos_anio=365)
    assert p['mu_a'] == pytest.approx((p['media_d'] + 0.5 * p['sigma_d'] ** 2) * 365, rel=1e-9)
    assert p['sigma_a'] == pytest.approx(p['sigma_d'] * np.sqrt(365), rel=1e-9)


def test_calibrar_gbm_datos_insuficientes():
    """Con menos de 2 observaciones devuelve un proceso degenerado (todo 0)."""
    p = gbm.calibrar_gbm([1.0])
    assert p == {'media_d': 0.0, 'sigma_d': 0.0, 'mu_a': 0.0, 'sigma_a': 0.0, 'n': 1}


def test_calibrar_desde_niveles():
    """Desde una serie de niveles GBM recupera σ y expone s0 = último nivel."""
    rng = np.random.default_rng(3)
    niveles = [1000.0]
    for _ in range(3000):
        niveles.append(niveles[-1] * np.exp(rng.normal(0.0005, 0.03)))
    p = gbm.calibrar_gbm_desde_niveles(niveles)
    assert p['sigma_d'] == pytest.approx(0.03, abs=2e-3)
    assert p['s0'] == pytest.approx(niveles[-1])
    assert p['n'] == 3000


def test_params_desde_momentos_relacion_lognormal():
    """La σ log por período sale de CV vía s = √(ln(1+CV²)); sin tendencia m=0."""
    p = gbm.params_gbm_desde_momentos(mean=1000.0, std=150.0)
    cv = 150.0 / 1000.0
    assert p['sigma_d'] == pytest.approx(np.sqrt(np.log1p(cv ** 2)))
    assert p['media_d'] == 0.0
    assert p['s0'] == 1000.0


# ── Simulación ───────────────────────────────────────────────────────────────

def test_simular_grid_positivo_y_shape():
    g = gbm.simular_gbm_grid(1000.0, 0.0, 0.05, T=30, N=5000,
                             xp=np, rng=np.random.default_rng(7))
    assert g.shape == (30, 5000)
    assert float(g.min()) > 0.0


def test_simular_grid_tiene_memoria():
    """Períodos consecutivos están correlacionados (cumsum), a diferencia de i.i.d."""
    g = gbm.simular_gbm_grid(1000.0, 0.0, 0.05, T=20, N=8000,
                             xp=np, rng=np.random.default_rng(11))
    corr = np.corrcoef(g[10], g[11])[0, 1]
    assert corr > 0.8


def test_grid_marginal_teorico():
    """E[S_t] ≈ s0·exp((m+½σ²)·pasos); aquí m=0 ⇒ leve crecimiento por convexidad."""
    s0, m, s, T, N = 1000.0, 0.0, 0.05, 30, 40_000
    g = gbm.simular_gbm_grid(s0, m, s, T, N, xp=np, rng=np.random.default_rng(5))
    pasos = T  # período 0-based T-1 ⇒ T pasos
    e_teo = s0 * np.exp((m + 0.5 * s ** 2) * pasos)
    assert g[T - 1].mean() == pytest.approx(e_teo, rel=0.02)


def test_marginal_consistente_con_grid():
    """gbm_marginal(period_idx) reproduce la dispersión de la columna del grid."""
    g = gbm.simular_gbm_grid(1000.0, 0.0, 0.05, T=30, N=20_000,
                             xp=np, rng=np.random.default_rng(7))
    mg = gbm.gbm_marginal(1000.0, 0.0, 0.05, period_idx=29, n=20_000,
                          xp=np, rng=np.random.default_rng(9))
    assert g[29].std() == pytest.approx(float(mg.std()), rel=0.05)


def test_simular_grid_determinista():
    a = gbm.simular_gbm_grid(500.0, 0.001, 0.04, 12, 1000, xp=np, rng=np.random.default_rng(2))
    b = gbm.simular_gbm_grid(500.0, 0.001, 0.04, 12, 1000, xp=np, rng=np.random.default_rng(2))
    assert np.allclose(np.asarray(a), np.asarray(b))


# ── resolve_gbm_params en MonteCarloConfig ───────────────────────────────────

def test_resolve_gbm_params_explicitos():
    cfg = MonteCarloConfig(distribution='gbm', gbm_volatility=0.04,
                           gbm_drift=0.001, gbm_s0=1234.0)
    s0, m, s = cfg.resolve_gbm_params()
    assert (s0, m, s) == (1234.0, 0.001, 0.04)


def test_resolve_gbm_params_desde_momentos():
    cfg = MonteCarloConfig(distribution='gbm', demand_mean=2000.0, demand_std=300.0)
    s0, m, s = cfg.resolve_gbm_params()
    cv = 300.0 / 2000.0
    assert s0 == 2000.0 and m == 0.0
    assert s == pytest.approx(np.sqrt(np.log1p(cv ** 2)))


# ── Integración: generador escalar ───────────────────────────────────────────

def test_scenario_generator_gbm_no_construye_scipy():
    cfg = MonteCarloConfig(distribution='gbm', gbm_volatility=0.04, gbm_s0=1000.0)
    gen = ScenarioGenerator(cfg)
    assert gen._is_gbm and gen._distribution is None


def test_generate_time_series_gbm_tiene_memoria():
    cfg = MonteCarloConfig(n_scenarios=5000, n_periods=20, random_seed=1,
                           distribution='gbm', gbm_volatility=0.04,
                           gbm_drift=0.001, gbm_s0=1000.0)
    ts = ScenarioGenerator(cfg).generate_time_series()
    assert len(ts) == 20 and len(ts[0]) == 5000
    D = np.array([[s.demand_value for s in period] for period in ts])
    assert float(D.min()) > 0.0
    assert np.corrcoef(D[5], D[6])[0, 1] > 0.8       # memoria
    assert D[19].mean() > D[0].mean()                # deriva positiva


def test_generate_for_period_gbm_positivo():
    cfg = MonteCarloConfig(n_scenarios=2000, random_seed=1,
                           distribution='gbm', gbm_volatility=0.05, gbm_s0=800.0)
    scen = ScenarioGenerator(cfg).generate_for_period(period_idx=4)
    demandas = np.array([s.demand_value for s in scen])
    assert len(demandas) == 2000 and float(demandas.min()) > 0.0


def test_regresion_normal_iid_sin_memoria():
    """La distribución i.i.d. por defecto no debe cambiar: sin memoria temporal."""
    cfg = MonteCarloConfig(n_scenarios=3000, n_periods=10, random_seed=1,
                           distribution='normal', demand_mean=1000, demand_std=150)
    gen = ScenarioGenerator(cfg)
    assert not gen._is_gbm and gen._distribution is not None
    D = np.array([[s.demand_value for s in p] for p in gen.generate_time_series()])
    assert abs(np.corrcoef(D[5], D[6])[0, 1]) < 0.1
    assert D.mean() == pytest.approx(1000, abs=30)


# ── Integración: motor vectorizado ───────────────────────────────────────────

def test_sample_demand_grid_gbm():
    cfg = MonteCarloConfig(n_scenarios=4000, n_periods=15, random_seed=2,
                           distribution='gbm', gbm_volatility=0.05,
                           gbm_drift=0.0, gbm_s0=500.0)
    rng = np.random.default_rng(cfg.random_seed)
    grid = np.asarray(_sample_demand_grid(cfg, T=15, N=4000, xp=np, rng=rng))
    assert grid.shape == (15, 4000)
    assert float(grid.min()) > 0.0
    assert np.corrcoef(grid[7], grid[8])[0, 1] > 0.8


# ── from_simulation calibra GBM desde la demanda histórica ───────────────────

class _FakeFDP:
    distribution_type = 7  # → 'gbm'


class _FakeSimulation:
    fk_fdp = _FakeFDP()
    confidence_level = 0.95
    duration_in_days = 12
    random_seed = 3

    def get_demand_history_array(self):
        rng = np.random.default_rng(0)
        niveles = [800.0]
        for _ in range(400):
            niveles.append(niveles[-1] * np.exp(rng.normal(0.0006, 0.025)))
        return np.array(niveles)

    def get_demand_statistics(self):
        h = self.get_demand_history_array()
        return {'mean': float(h.mean()), 'std': float(h.std())}


def test_from_simulation_calibra_gbm():
    cfg = MonteCarloConfig.from_simulation(_FakeSimulation(), None, n_scenarios=100)
    assert cfg.distribution == 'gbm'
    assert cfg.gbm_volatility == pytest.approx(0.025, abs=3e-3)
    assert cfg.gbm_s0 is not None and cfg.gbm_s0 > 0
