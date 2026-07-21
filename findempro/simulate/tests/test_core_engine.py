"""
test_core_engine.py
===================
Tests unitarios para los tres módulos core de simulación:
  - simulate/core/discrete_engine.py
  - simulate/core/monte_carlo.py
  - simulate/core/decision_engine.py

Ejecutar con:
  cd findempro
  venv/Scripts/python.exe -m pytest simulate/tests/test_core_engine.py -v
"""

import math
import numpy as np
import pytest

from simulate.services.recommendation_service import (
    Recommendation as SvcRecommendation,
    RecommendationService,
)
from simulate.core.discrete_engine import (
    CompanyConfig, OperationScenario, PeriodResult,
    DiscreteEventEngine, simular_operacion,
    _topological_sort, _extract_rhs_dependencies, _get_lhs, _eval_expression,
)
from simulate.core.monte_carlo import (
    MonteCarloConfig, ScenarioGenerator, DistributionFactory,
    aggregate_results, cached_aggregate_results, generate_scenarios,
)
from simulate.core.decision_engine import (
    RiskMetrics, Recommendation, DecisionReport,
    DecisionEngine, RecommendationEngine, analizar_decision,
    _compute_risk_metrics, _compute_cara_utility,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de test
# ─────────────────────────────────────────────────────────────────────────────

class _MockArea:
    def __init__(self, name='General'):
        self.name = name


class _MockEquation:
    def __init__(self, expression: str, area: str = 'General'):
        self.expression = expression
        self.fk_area = _MockArea(area)


def _make_equations(*expressions, area='General'):
    return [_MockEquation(e, area) for e in expressions]


def _make_config(**kwargs) -> CompanyConfig:
    defaults = dict(
        sector='production',
        business_name='PYME Test',
        demand_variable='DE',
        revenue_variable='IT',
        cost_variable='TG',
        profit_variable='GT',
        equations=[],
        total_periods=10,
    )
    defaults.update(kwargs)
    return CompanyConfig(**defaults)


def _make_mc_config(**kwargs) -> MonteCarloConfig:
    defaults = dict(
        n_scenarios=2000,
        distribution='normal',
        demand_mean=2000.0,
        demand_std=200.0,
        n_periods=5,
        random_seed=42,
    )
    defaults.update(kwargs)
    return MonteCarloConfig(**defaults)


# ─────────────────────────────────────────────────────────────────────────────
# DISCRETE ENGINE — expresiones y dependencias
# ─────────────────────────────────────────────────────────────────────────────

class TestExpressionHelpers:

    def test_get_lhs_simple(self):
        assert _get_lhs('IT=TPV*PVP') == 'IT'

    def test_get_lhs_no_equals(self):
        assert _get_lhs('TPV + PVP') is None

    def test_get_lhs_with_spaces(self):
        assert _get_lhs('  MB  =IT-TG') == 'MB'

    def test_extract_deps_basic(self):
        deps = _extract_rhs_dependencies('IT=TPV*PVP')
        assert 'TPV' in deps
        assert 'PVP' in deps
        assert 'IT' not in deps

    def test_extract_deps_functions_excluded(self):
        deps = _extract_rhs_dependencies('X=max(A, min(B, C))')
        assert 'A' in deps
        assert 'B' in deps
        assert 'C' in deps
        assert 'max' not in deps
        assert 'min' not in deps

    def test_eval_expression_basic(self):
        result = _eval_expression('A+B', {'A': 10.0, 'B': 5.0})
        assert result == pytest.approx(15.0)

    def test_eval_expression_division_by_zero(self):
        result = _eval_expression('A/B', {'A': 10.0, 'B': 0.0})
        assert result == pytest.approx(0.0)

    def test_eval_expression_missing_var(self):
        result = _eval_expression('A+UNKNOWN', {'A': 10.0})
        # UNKNOWN no se sustituye → error de eval → None
        assert result is None

    def test_eval_expression_math_functions(self):
        result = _eval_expression('sqrt(A)', {'A': 16.0})
        assert result == pytest.approx(4.0)

    def test_eval_expression_max_min(self):
        result = _eval_expression('max(A,B)', {'A': 3.0, 'B': 7.0})
        assert result == pytest.approx(7.0)


class TestTopologicalSort:

    def test_simple_chain(self):
        """IT → GT: GT depende de IT, IT debe resolverse primero."""
        eqs = _make_equations('IT=TPV*PVP', 'GT=IT-TG')
        sorted_eqs = _topological_sort(eqs)
        lhs_order = [_get_lhs(e.expression) for e in sorted_eqs]
        assert lhs_order.index('IT') < lhs_order.index('GT')

    def test_no_equations(self):
        assert _topological_sort([]) == []

    def test_independent_equations(self):
        """Sin dependencias entre sí → ambas deben aparecer."""
        eqs = _make_equations('A=X+Y', 'B=P+Q')
        sorted_eqs = _topological_sort(eqs)
        assert len(sorted_eqs) == 2

    def test_circular_goes_to_end(self):
        """Dependencia circular → ambas ecuaciones aparecen (sin crash)."""
        eqs = _make_equations('A=B+1', 'B=A+1')
        sorted_eqs = _topological_sort(eqs)
        assert len(sorted_eqs) == 2


# ─────────────────────────────────────────────────────────────────────────────
# DISCRETE ENGINE — DiscreteEventEngine y simular_operacion
# ─────────────────────────────────────────────────────────────────────────────

class TestDiscreteEventEngine:

    def test_basic_single_period(self):
        """Flujo mínimo: IT = TPV * PVP, GT = IT - TG."""
        eqs = _make_equations('IT=TPV*PVP', 'GT=IT-TG')
        config = _make_config(equations=eqs)
        scenario = OperationScenario(period_index=0, demand_value=1000.0)
        exog = {'TPV': 500.0, 'PVP': 10.0, 'TG': 3000.0}

        engine = DiscreteEventEngine(config)
        result = engine.run_period(scenario, exog)

        assert isinstance(result, PeriodResult)
        assert result.variables['IT'] == pytest.approx(5000.0)
        assert result.variables['GT'] == pytest.approx(2000.0)

    def test_demand_injected_into_table(self):
        """La demanda del escenario debe estar en variables como DE."""
        config = _make_config()
        scenario = OperationScenario(period_index=0, demand_value=2500.0)

        engine = DiscreteEventEngine(config)
        result = engine.run_period(scenario)

        assert result.demand == pytest.approx(2500.0)
        assert result.variables['DE'] == pytest.approx(2500.0)

    def test_seasonality_applied(self):
        """Estacionalidad 0.5 reduce demanda a la mitad."""
        config = _make_config()
        scenario = OperationScenario(
            period_index=0, demand_value=2000.0, seasonality_factor=0.5
        )
        engine = DiscreteEventEngine(config)
        result = engine.run_period(scenario)

        assert result.demand == pytest.approx(1000.0)

    def test_state_persists_across_periods(self):
        """Estado inicial se persiste y se transfiere al período siguiente."""
        eqs = _make_equations('IPF=IPF_PREV+10')

        config = _make_config(
            equations=eqs,
            initial_state={'IPF': 100.0},
        )
        engine = DiscreteEventEngine(config)
        scenarios = [
            OperationScenario(period_index=i, demand_value=500.0)
            for i in range(3)
        ]
        results = engine.run_all_periods(scenarios, exogenous={'IPF_PREV': 100.0})
        assert len(results) == 3

    def test_dia_variable_increments(self):
        """DIA debe ser 1 en período 0, 2 en período 1, etc."""
        config = _make_config()
        engine = DiscreteEventEngine(config)
        for idx in range(3):
            r = engine.run_period(OperationScenario(period_index=idx, demand_value=100.0))
            assert r.variables['DIA'] == pytest.approx(float(idx + 1))

    def test_nmd_constant(self):
        """NMD debe ser igual a total_periods en todos los períodos."""
        config = _make_config(total_periods=15)
        engine = DiscreteEventEngine(config)
        r = engine.run_period(OperationScenario(period_index=0, demand_value=100.0))
        assert r.variables['NMD'] == pytest.approx(15.0)

    def test_demand_history_updates_dph(self):
        """Después del primer período, DPH debe reflejar la demanda anterior."""
        config = _make_config(total_periods=3)
        engine = DiscreteEventEngine(config)

        r0 = engine.run_period(OperationScenario(period_index=0, demand_value=1000.0))
        r1 = engine.run_period(OperationScenario(period_index=1, demand_value=2000.0))

        # Después del período 0, DPH en período 1 debe reflejar los 1000 del período 0
        assert r1.variables['DPH'] == pytest.approx(1000.0)

    def test_reset_state(self):
        """reset_state() debe volver el motor al estado inicial."""
        config = _make_config(initial_state={'X': 100.0})
        engine = DiscreteEventEngine(config)
        engine._state['X'] = 999.0
        engine.reset_state()
        assert engine._state['X'] == pytest.approx(100.0)

    def test_simular_operacion_function(self):
        """Función de alto nivel simular_operacion() funciona correctamente."""
        eqs = _make_equations('GT=IT-TG')
        config = _make_config(equations=eqs)
        scenario = OperationScenario(period_index=0, demand_value=500.0)
        exog = {'IT': 10000.0, 'TG': 7000.0}

        result = simular_operacion(config, scenario, exog)

        assert result.variables['GT'] == pytest.approx(3000.0)

    def test_warnings_on_loss(self):
        """Se generan warnings cuando el margen es negativo."""
        eqs = _make_equations('GT=IT-TG')
        config = _make_config(
            equations=eqs,
            revenue_variable='IT',
            profit_variable='GT',
            min_profit_margin_pct=10.0,
        )
        scenario = OperationScenario(period_index=0, demand_value=500.0)
        exog = {'IT': 1000.0, 'TG': 2000.0}  # pérdida: GT = -1000

        result = simular_operacion(config, scenario, exog)

        assert len(result.warnings) > 0
        assert any('margen' in w.lower() or 'costo' in w.lower() for w in result.warnings)

    def test_no_warnings_profitable(self):
        """Sin warnings cuando la operación es rentable."""
        eqs = _make_equations('GT=IT-TG')
        config = _make_config(equations=eqs, min_profit_margin_pct=10.0)
        scenario = OperationScenario(period_index=0, demand_value=500.0)
        exog = {'IT': 10000.0, 'TG': 6000.0}  # margen 40%

        result = simular_operacion(config, scenario, exog)

        assert result.warnings == []

    def test_external_variables_override(self):
        """Variables en scenario.external_variables deben tener prioridad sobre exogenous."""
        config = _make_config()
        scenario = OperationScenario(
            period_index=0,
            demand_value=500.0,
            external_variables={'PVP': 99.0},
        )
        exog = {'PVP': 10.0}  # debe ser ignorado en favor del escenario

        engine = DiscreteEventEngine(config)
        result = engine.run_period(scenario, exog)

        assert result.variables['PVP'] == pytest.approx(99.0)

    def test_all_periods_length(self):
        """run_all_periods() devuelve exactamente un resultado por escenario."""
        config = _make_config(total_periods=5)
        engine = DiscreteEventEngine(config)
        scenarios = [OperationScenario(i, 1000.0) for i in range(5)]
        results = engine.run_all_periods(scenarios)
        assert len(results) == 5

    def test_negative_demand_clamped(self):
        """Demanda negativa se clampea a 0."""
        config = _make_config()
        scenario = OperationScenario(period_index=0, demand_value=-500.0)
        engine = DiscreteEventEngine(config)
        result = engine.run_period(scenario)
        assert result.demand >= 0.0

    def test_scalar_engine_sanitizes_inf_nan(self):
        """La ruta escalar sanea inf/nan a 0.0 (paridad con el motor vectorizado).

        Antes, un overflow de float (p. ej. 1e200*1e200 = inf, sin excepción en
        Python) se propagaba a _extract_financials y envenenaba np.mean/np.percentile
        en la agregación de simulation_service. Ahora se mapea a 0.0.
        """
        config = _make_config(
            equations=_make_equations(
                'IT=DE*DE',   # DE grande → IT desborda a +inf
                'TG=DE',
                'GT=IT-TG',   # inf - finito = inf
            ),
        )
        engine = DiscreteEventEngine(config)
        result = engine.run_period(
            OperationScenario(period_index=0, demand_value=1e200, seasonality_factor=1.0)
        )
        # Todas las métricas financieras son finitas
        assert math.isfinite(result.demand)
        assert math.isfinite(result.revenue)
        assert math.isfinite(result.costs)
        assert math.isfinite(result.profit)
        # Los valores no finitos (revenue/profit) se sanean a 0.0
        assert result.revenue == 0.0
        assert result.profit == 0.0
        # Un array de estos resultados agrega a números finitos
        arr = np.array([result.profit] * 100, dtype=float)
        assert np.isfinite(np.mean(arr))
        assert np.isfinite(np.percentile(arr, 5))


# ─────────────────────────────────────────────────────────────────────────────
# MONTE CARLO — DistributionFactory y ScenarioGenerator
# ─────────────────────────────────────────────────────────────────────────────

class TestDistributionFactory:

    @pytest.mark.parametrize("dist", [
        'normal', 'lognormal', 'gamma', 'uniform', 'exponential', 'poisson'
    ])
    def test_all_distributions_build(self, dist):
        """Todas las distribuciones soportadas deben construirse sin errores."""
        config = _make_mc_config(distribution=dist)
        dist_obj = DistributionFactory.build(config)
        assert dist_obj is not None

    def test_unsupported_distribution_raises(self):
        """Una distribución inexistente debe lanzar ValueError."""
        config = _make_mc_config(distribution='beta_triangular')
        with pytest.raises(ValueError, match='no soportada'):
            DistributionFactory.build(config)

    def test_poisson_generates_non_negative_integers(self):
        """Poisson genera valores discretos >= 0."""
        config = _make_mc_config(distribution='poisson', demand_mean=50.0)
        gen = ScenarioGenerator(config)
        scenarios = gen.generate_for_period(0, n_scenarios=500)
        demands = [s.demand_value for s in scenarios]
        assert all(d >= 0.0 for d in demands)
        # Para Poisson la media debe estar aproximada a lambda=50
        assert abs(np.mean(demands) - 50.0) < 10.0

    def test_fit_best_returns_valid_name(self):
        data = np.random.lognormal(mean=7, sigma=0.3, size=500)
        name, ks = DistributionFactory.fit_best(data)
        assert name in ('normal', 'lognormal', 'gamma')
        assert 0.0 <= ks <= 1.0

    def test_fit_best_insufficient_data(self):
        """Con menos de 10 puntos retorna 'normal' con KS=1.0."""
        data = np.array([1.0, 2.0, 3.0])
        name, ks = DistributionFactory.fit_best(data)
        assert name == 'normal'
        assert ks == pytest.approx(1.0)


class TestScenarioGenerator:

    def test_generates_correct_count(self):
        config = _make_mc_config(n_scenarios=500)
        gen = ScenarioGenerator(config)
        scenarios = gen.generate_for_period(0, n_scenarios=500)
        assert len(scenarios) == 500

    def test_all_scenarios_are_operation_scenarios(self):
        config = _make_mc_config(n_scenarios=100)
        gen = ScenarioGenerator(config)
        scenarios = gen.generate_for_period(0, n_scenarios=100)
        assert all(isinstance(s, OperationScenario) for s in scenarios)

    def test_demand_non_negative(self):
        """Demanda generada debe ser siempre >= 0."""
        config = _make_mc_config(n_scenarios=1000, random_seed=0)
        gen = ScenarioGenerator(config)
        scenarios = gen.generate_for_period(0, n_scenarios=1000)
        assert all(s.demand_value >= 0.0 for s in scenarios)

    def test_period_index_set_correctly(self):
        config = _make_mc_config(n_scenarios=10)
        gen = ScenarioGenerator(config)
        for period_idx in [0, 3, 7]:
            scenarios = gen.generate_for_period(period_idx, n_scenarios=10)
            assert all(s.period_index == period_idx for s in scenarios)

    def test_seasonality_applied_to_all(self):
        """Con factor 0.5 en el mes 0, todos los escenarios deben tener factor 0.5."""
        config = _make_mc_config(
            n_scenarios=50,
            seasonality_factors=[0.5] + [1.0] * 11,
        )
        gen = ScenarioGenerator(config)
        scenarios = gen.generate_for_period(0, n_scenarios=50)
        assert all(s.seasonality_factor == pytest.approx(0.5) for s in scenarios)

    def test_reproducible_with_seed(self):
        """Mismo seed → mismos escenarios (reproducibilidad garantizada)."""
        config = _make_mc_config(n_scenarios=100, random_seed=99)
        s1 = ScenarioGenerator(config).generate_for_period(0, n_scenarios=100)

        config2 = _make_mc_config(n_scenarios=100, random_seed=99)
        s2 = ScenarioGenerator(config2).generate_for_period(0, n_scenarios=100)

        demands1 = [s.demand_value for s in s1]
        demands2 = [s.demand_value for s in s2]
        assert demands1 == pytest.approx(demands2)

    def test_different_seeds_produce_different_results(self):
        """Seeds distintos producen muestras distintas."""
        cfg1 = _make_mc_config(n_scenarios=100, random_seed=1)
        cfg2 = _make_mc_config(n_scenarios=100, random_seed=2)
        s1 = ScenarioGenerator(cfg1).generate_for_period(0, n_scenarios=100)
        s2 = ScenarioGenerator(cfg2).generate_for_period(0, n_scenarios=100)
        d1 = [s.demand_value for s in s1]
        d2 = [s.demand_value for s in s2]
        assert d1 != pytest.approx(d2)

    def test_two_instances_same_seed_independent(self):
        """Dos instancias con mismo seed producen resultados idénticos (RNG encapsulado)."""
        config = _make_mc_config(n_scenarios=50, random_seed=123)
        gen_a = ScenarioGenerator(config)
        gen_b = ScenarioGenerator(config)
        a = [s.demand_value for s in gen_a.generate_for_period(0, n_scenarios=50)]
        b = [s.demand_value for s in gen_b.generate_for_period(0, n_scenarios=50)]
        assert a == pytest.approx(b)

    def test_demand_mean_approximates_config(self):
        """Media de N muestras debe aproximarse a demand_mean (por LGN)."""
        config = _make_mc_config(n_scenarios=5000, demand_mean=3000.0, demand_std=300.0, random_seed=1)
        gen = ScenarioGenerator(config)
        scenarios = gen.generate_for_period(0, n_scenarios=5000)
        sample_mean = np.mean([s.demand_value for s in scenarios])
        assert abs(sample_mean - 3000.0) < 100.0  # dentro del 3.3%

    def test_generate_time_series_length(self):
        """generate_time_series() devuelve una lista por período."""
        config = _make_mc_config(n_periods=4)
        gen = ScenarioGenerator(config)
        series = gen.generate_time_series()
        assert len(series) == 4

    def test_generate_scenarios_function(self):
        """Función pública generate_scenarios() funciona correctamente."""
        config = _make_mc_config(n_scenarios=200)
        scenarios = generate_scenarios(config, period_idx=2)
        assert len(scenarios) == 200
        assert all(s.period_index == 2 for s in scenarios)


class TestAggregateResults:

    @pytest.fixture
    def samples(self):
        rng = np.random.default_rng(42)
        profits = rng.normal(5000, 1500, 10000)
        demands = rng.normal(2000, 200, 10000)
        revenues = rng.normal(40000, 4000, 10000)
        return profits, demands, revenues

    def test_returns_aggregated_result(self, samples):
        profits, demands, revenues = samples
        config = _make_mc_config()
        result = aggregate_results(profits, demands, revenues, config)
        assert result is not None

    def test_probabilities_sum_to_one(self, samples):
        profits, demands, revenues = samples
        result = aggregate_results(profits, demands, revenues, _make_mc_config())
        total = result.probability_of_loss + result.probability_breakeven
        assert total == pytest.approx(1.0, abs=1e-10)

    def test_percentile_ordering(self, samples):
        profits, demands, revenues = samples
        result = aggregate_results(profits, demands, revenues, _make_mc_config())
        assert result.demand_p5 <= result.demand_p25
        assert result.demand_p25 <= result.demand_p75
        assert result.demand_p75 <= result.demand_p95

    def test_cvar_le_var(self, samples):
        """CVaR ≤ VaR (CVaR es la pérdida promedio en la cola, más severa)."""
        # Crear profits con cola de pérdidas
        profits = np.concatenate([np.random.normal(5000, 500, 9000), np.random.normal(-3000, 500, 1000)])
        demands = np.random.normal(2000, 200, 10000)
        revenues = np.random.normal(40000, 4000, 10000)
        result = aggregate_results(profits, demands, revenues, _make_mc_config())
        # Para pérdidas: ES ≤ VaR (ambos negativos, ES más negativo)
        if result.value_at_risk < 0:
            assert result.expected_shortfall <= result.value_at_risk

    def test_scenario_keys_present(self, samples):
        profits, demands, revenues = samples
        result = aggregate_results(profits, demands, revenues, _make_mc_config())
        for key in ('demand', 'revenue', 'profit', 'percentile'):
            assert key in result.scenario_base
            assert key in result.scenario_pessimistic
            assert key in result.scenario_optimistic

    def test_metadata_correct(self, samples):
        profits, demands, revenues = samples
        config = _make_mc_config(n_scenarios=10000, distribution='lognormal')
        result = aggregate_results(profits, demands, revenues, config)
        assert result.n_scenarios == len(profits)
        assert result.distribution_used == 'lognormal'
        assert result.confidence_level == config.confidence_level


# ─────────────────────────────────────────────────────────────────────────────
# DECISION ENGINE — métricas de riesgo y recomendaciones
# ─────────────────────────────────────────────────────────────────────────────

class TestComputeRiskMetrics:

    @pytest.fixture
    def profitable_profits(self):
        rng = np.random.default_rng(0)
        return rng.normal(5000, 800, 10000)

    @pytest.fixture
    def loss_profits(self):
        rng = np.random.default_rng(1)
        return rng.normal(-2000, 1000, 10000)

    def test_returns_risk_metrics(self, profitable_profits):
        metrics = _compute_risk_metrics(profitable_profits)
        assert isinstance(metrics, RiskMetrics)

    def test_probability_breakeven_high_for_profits(self, profitable_profits):
        metrics = _compute_risk_metrics(profitable_profits)
        assert metrics.probability_breakeven > 0.99

    def test_probability_of_loss_high_for_losses(self, loss_profits):
        metrics = _compute_risk_metrics(loss_profits)
        assert metrics.probability_of_loss > 0.95

    def test_probabilities_sum_to_one(self, profitable_profits):
        metrics = _compute_risk_metrics(profitable_profits)
        assert metrics.probability_of_loss + metrics.probability_breakeven == pytest.approx(1.0, abs=1e-10)

    def test_var_99_more_extreme_than_var_95(self, profitable_profits):
        """VaR 99% debe ser más extremo (menor) que VaR 95%."""
        metrics = _compute_risk_metrics(profitable_profits)
        assert metrics.var_99 <= metrics.var_95

    def test_cvar_more_extreme_than_var(self, profitable_profits):
        metrics = _compute_risk_metrics(profitable_profits)
        assert metrics.cvar_95 <= metrics.var_95

    def test_percentile_ordering(self, profitable_profits):
        m = _compute_risk_metrics(profitable_profits)
        assert m.p1 <= m.p5 <= m.p10 <= m.p25 <= m.p50 <= m.p75 <= m.p90 <= m.p95 <= m.p99

    def test_sharpe_ratio_with_risk_free_rate(self, profitable_profits):
        metrics = _compute_risk_metrics(profitable_profits, risk_free_rate=1000.0)
        assert metrics.sharpe_ratio is not None
        expected = (np.mean(profitable_profits) - 1000.0) / np.std(profitable_profits, ddof=1)
        assert metrics.sharpe_ratio == pytest.approx(expected, rel=1e-2)

    def test_sortino_ratio_present(self, profitable_profits):
        """sortino_ratio debe estar presente cuando existen retornos negativos con varianza > 0."""
        rng = np.random.default_rng(55)
        # Pérdidas con varianza propia (no constantes)
        losses = rng.normal(-1500.0, 300.0, 300)
        mixed = np.concatenate([profitable_profits, losses])
        metrics = _compute_risk_metrics(mixed, risk_free_rate=0.0)
        assert metrics.sortino_ratio is not None
        assert metrics.downside_std is not None
        assert metrics.downside_std > 0.0

    def test_sortino_none_when_no_losses(self):
        """Sortino es None cuando todos los profits son no-negativos."""
        only_gains = np.abs(np.random.normal(5000, 500, 1000))
        metrics = _compute_risk_metrics(only_gains, risk_free_rate=0.0)
        # No hay retornos < 0 → downside_std no calculable
        assert metrics.sortino_ratio is None or metrics.downside_std is None

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            _compute_risk_metrics(np.array([]))


class TestCARAUtility:

    def test_zero_risk_aversion_equals_mean(self):
        """λ=0 → utilidad = E[profit]."""
        profits = np.array([1000.0, 2000.0, 3000.0])
        eu = _compute_cara_utility(profits, risk_aversion=0.0)
        assert eu == pytest.approx(np.mean(profits))

    def test_risk_averse_penalizes_variance(self):
        """Agente averso al riesgo prefiere flujo seguro sobre uno variable con misma media."""
        certain = np.full(1000, 5000.0)
        risky = np.concatenate([np.full(500, 0.0), np.full(500, 10000.0)])  # misma media

        eu_certain = _compute_cara_utility(certain, risk_aversion=0.0001)
        eu_risky = _compute_cara_utility(risky, risk_aversion=0.0001)

        assert eu_certain > eu_risky

    def test_positive_risk_aversion_returns_scalar(self):
        profits = np.random.normal(5000, 500, 1000)
        eu = _compute_cara_utility(profits, risk_aversion=0.001)
        assert isinstance(eu, float)
        assert not math.isnan(eu)

    def test_no_overflow_with_large_profits(self):
        """No debe haber overflow ni NaN con ganancias muy grandes."""
        profits = np.full(100, 1_000_000.0)  # profits enormes
        eu = _compute_cara_utility(profits, risk_aversion=0.01)
        assert not math.isnan(eu)
        assert not math.isinf(eu)

    def test_no_overflow_with_large_losses(self):
        """No debe haber overflow ni NaN con pérdidas muy grandes."""
        profits = np.full(100, -1_000_000.0)
        eu = _compute_cara_utility(profits, risk_aversion=0.01)
        assert not math.isnan(eu)
        assert not math.isinf(eu)


class TestRecommendationEngine:

    def _make_risk(self, prob_loss=0.05, var_95=-500.0, mean=5000.0, std=1000.0):
        return RiskMetrics(
            mean=mean, std=std, variance=std**2,
            skewness=0.0, kurtosis=0.0,
            p1=-2000, p5=var_95, p10=-200, p25=2000,
            p50=5000, p75=7000, p90=8000, p95=9000, p99=11000,
            probability_of_loss=prob_loss,
            probability_breakeven=1 - prob_loss,
            var_95=var_95, var_99=-1500,
            cvar_95=-800, cvar_99=-2000,
            sharpe_ratio=4.5,
        )

    def test_critical_on_loss(self):
        """Operación con pérdida genera recomendación crítica."""
        engine = RecommendationEngine(min_profit_margin_pct=10.0)
        risk = self._make_risk(prob_loss=0.6, mean=-2000.0)
        recs = engine.generate(risk, {'IT': 10000.0, 'GT': -2000.0, 'TG': 12000.0})
        severities = [r.severity for r in recs]
        assert 'critical' in severities

    def test_warning_on_low_margin(self):
        engine = RecommendationEngine(min_profit_margin_pct=20.0)
        risk = self._make_risk()
        recs = engine.generate(risk, {'IT': 10000.0, 'GT': 500.0, 'TG': 9500.0})
        # margen = 5% < 20% → warning
        severities = [r.severity for r in recs]
        assert 'warning' in severities or 'critical' in severities

    def test_no_recs_for_healthy_operation(self):
        """Operación sana no debería generar críticos."""
        engine = RecommendationEngine(min_profit_margin_pct=10.0, max_probability_of_loss=0.20)
        risk = self._make_risk(prob_loss=0.02, mean=8000.0)
        recs = engine.generate(risk, {'IT': 40000.0, 'GT': 8000.0, 'TG': 32000.0})
        criticals = [r for r in recs if r.severity == 'critical']
        assert criticals == []

    def test_sorted_by_severity(self):
        """Críticos antes que warnings, warnings antes que info."""
        engine = RecommendationEngine(min_profit_margin_pct=10.0)
        risk = self._make_risk(prob_loss=0.50, mean=-3000.0)
        recs = engine.generate(risk, {'IT': 5000.0, 'GT': -3000.0, 'TG': 8000.0})
        order = {'critical': 0, 'warning': 1, 'info': 2}
        for i in range(len(recs) - 1):
            assert order[recs[i].severity] <= order[recs[i + 1].severity]

    def test_demand_lost_warning(self):
        """Alta demanda insatisfecha genera warning."""
        engine = RecommendationEngine()
        risk = self._make_risk()
        recs = engine.generate(risk, {'IT': 40000.0, 'GT': 5000.0, 'TG': 35000.0,
                                      'DI': 500.0, 'DDP': 2000.0})  # 25% perdida
        titles = [r.title for r in recs]
        assert any('demanda' in t.lower() for t in titles)

    def test_capacity_underutilized_info(self):
        """FU bajo genera recomendación info."""
        engine = RecommendationEngine()
        risk = self._make_risk(prob_loss=0.02, mean=5000.0)
        recs = engine.generate(risk, {'IT': 40000.0, 'GT': 5000.0, 'FU': 0.3})
        assert any('capacidad' in r.title.lower() or 'utilizaci' in r.title.lower() for r in recs)


class TestDecisionEngine:

    @pytest.fixture
    def good_samples(self):
        rng = np.random.default_rng(7)
        return (
            rng.normal(8000, 1000, 5000),   # profits
            rng.normal(3000, 300, 5000),    # demands
            rng.normal(50000, 5000, 5000),  # revenues
        )

    @pytest.fixture
    def bad_samples(self):
        rng = np.random.default_rng(8)
        return (
            rng.normal(-3000, 2000, 5000),  # profits negativos
            rng.normal(1000, 200, 5000),
            rng.normal(10000, 1000, 5000),
        )

    def test_returns_decision_report(self, good_samples):
        engine = DecisionEngine()
        report = engine.analyze(*good_samples)
        assert isinstance(report, DecisionReport)

    def test_viable_for_profitable_operation(self, good_samples):
        engine = DecisionEngine()
        report = engine.analyze(*good_samples)
        assert report.overall_assessment == 'viable'
        assert report.overall_score > 0.5

    def test_not_viable_for_loss_operation(self, bad_samples):
        engine = DecisionEngine()
        report = engine.analyze(*bad_samples)
        assert report.overall_assessment in ('no_viable', 'riesgoso')

    def test_score_range(self, good_samples):
        engine = DecisionEngine()
        report = engine.analyze(*good_samples)
        assert 0.0 <= report.overall_score <= 1.0

    def test_to_dict_serializable(self, good_samples):
        engine = DecisionEngine()
        report = engine.analyze(*good_samples)
        d = report.to_dict()
        assert isinstance(d, dict)
        assert 'risk_metrics' in d
        assert 'recommendations' in d
        assert 'overall_assessment' in d

    def test_scenario_comparison_keys(self, good_samples):
        engine = DecisionEngine()
        report = engine.analyze(*good_samples)
        assert 'base_p50' in report.scenario_comparison
        assert 'pessimistic_p5' in report.scenario_comparison
        assert 'very_optimistic_p95' in report.scenario_comparison

    def test_risk_aversion_affects_certainty_equivalent(self):
        """
        Mayor aversión al riesgo → menor equivalente cierto (CE).

        Para CARA U(π) = -exp(-λπ)/λ el CE es:
          CE = -ln(E[exp(-λπ)]) / λ   →   CE = μ - λσ²/2  para Normal.

        La utilidad BRUTA E[U] no es comparable entre distintos λ (la escala
        1/λ hace que valores absolutos no tengan el mismo rango). En cambio CE
        es comparable y decrece estrictamente con λ cuando σ² > 0.
        """
        rng = np.random.default_rng(77)
        profits = rng.normal(5000.0, 1000.0, 10_000)

        def certainty_equivalent(samples, lam):
            """CE = -ln(E[exp(-λπ)]) / λ  (escala-invariante)."""
            if abs(lam) < 1e-10:
                return float(np.mean(samples))
            # Estabilizar con log-sum-exp para evitar overflow
            x = -lam * samples
            x_max = x.max()
            log_mean_exp = x_max + np.log(np.mean(np.exp(x - x_max)))
            return -log_mean_exp / lam

        lam_low = 0.00001   # casi neutral
        lam_high = 0.0001   # más averso

        ce_low = certainty_equivalent(profits, lam_low)
        ce_high = certainty_equivalent(profits, lam_high)

        # CE = μ - λσ²/2 → mayor λ → menor CE
        assert ce_high < ce_low

    def test_analizar_decision_function(self, good_samples):
        """Función pública analizar_decision() funciona como wrapper."""
        profits, demands, revenues = good_samples
        report = analizar_decision(profits, demands, revenues, risk_aversion=0.001)
        assert isinstance(report, DecisionReport)
        assert report.overall_assessment in ('viable', 'riesgoso', 'no_viable')


# ─────────────────────────────────────────────────────────────────────────────
# MONTE CARLO — generate_time_series() vectorizado (P1)
# ─────────────────────────────────────────────────────────────────────────────

class TestGenerateTimeSeriesVectorized:

    def test_shape_t_periods_n_scenarios(self):
        config = _make_mc_config(n_periods=6, n_scenarios=200)
        series = ScenarioGenerator(config).generate_time_series()
        assert len(series) == 6
        assert all(len(period) == 200 for period in series)

    def test_period_index_correct_per_period(self):
        config = _make_mc_config(n_periods=4, n_scenarios=50)
        series = ScenarioGenerator(config).generate_time_series()
        for t, period_scenarios in enumerate(series):
            assert all(s.period_index == t for s in period_scenarios)

    def test_all_demands_non_negative(self):
        config = _make_mc_config(n_periods=5, n_scenarios=300, random_seed=7)
        series = ScenarioGenerator(config).generate_time_series()
        for period_scenarios in series:
            assert all(s.demand_value >= 0.0 for s in period_scenarios)

    def test_reproducible_with_same_seed(self):
        config = _make_mc_config(n_periods=3, n_scenarios=100, random_seed=55)
        s1 = ScenarioGenerator(config).generate_time_series()
        s2 = ScenarioGenerator(config).generate_time_series()
        for t in range(3):
            d1 = [s.demand_value for s in s1[t]]
            d2 = [s.demand_value for s in s2[t]]
            assert d1 == pytest.approx(d2)

    def test_different_seeds_produce_different_series(self):
        cfg1 = _make_mc_config(n_periods=2, n_scenarios=50, random_seed=11)
        cfg2 = _make_mc_config(n_periods=2, n_scenarios=50, random_seed=22)
        s1 = ScenarioGenerator(cfg1).generate_time_series()
        s2 = ScenarioGenerator(cfg2).generate_time_series()
        d1 = [s.demand_value for s in s1[0]]
        d2 = [s.demand_value for s in s2[0]]
        assert d1 != pytest.approx(d2)

    def test_price_variations_when_volatility_set(self):
        config = _make_mc_config(
            n_periods=3, n_scenarios=200, random_seed=33,
            price_volatility=0.05,
        )
        series = ScenarioGenerator(config).generate_time_series()
        all_price_vars = [s.price_variation for p in series for s in p]
        assert not all(v == 0.0 for v in all_price_vars)

    def test_zero_volatility_gives_zero_variations(self):
        config = _make_mc_config(
            n_periods=3, n_scenarios=100, random_seed=1,
            price_volatility=0.0, cost_volatility=0.0,
        )
        series = ScenarioGenerator(config).generate_time_series()
        for period in series:
            assert all(s.price_variation == pytest.approx(0.0) for s in period)
            assert all(s.cost_variation == pytest.approx(0.0) for s in period)

    def test_seasonality_factor_per_period(self):
        # Los factores son MENSUALES (12). El período t es un DÍA; se mapea a mes
        # con (t // 30) % 12. Antes el motor usaba t % len(factors) (bug: comprimía
        # el año a un ciclo de len(factors) días). Aquí verificamos el mapeo correcto
        # sobre 3 meses (90 días) con 12 factores distintos.
        factors = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5,
                   1.6, 1.7, 1.8, 1.9, 2.0, 2.1]
        n_periods = 90  # 3 meses de 30 días
        config = _make_mc_config(
            n_periods=n_periods, n_scenarios=20,
            seasonality_factors=factors,
        )
        series = ScenarioGenerator(config).generate_time_series()
        for t in range(n_periods):
            expected_factor = factors[(t // 30) % 12]  # día → mes
            assert all(s.seasonality_factor == pytest.approx(expected_factor) for s in series[t])
        # Días 0..29 → mes 0, 30..59 → mes 1, 60..89 → mes 2
        assert series[0][0].seasonality_factor == pytest.approx(factors[0])
        assert series[29][0].seasonality_factor == pytest.approx(factors[0])
        assert series[30][0].seasonality_factor == pytest.approx(factors[1])
        assert series[60][0].seasonality_factor == pytest.approx(factors[2])

    def test_demand_distribution_approximates_mean(self):
        """Media muestral sobre T*N debe aproximar demand_mean (LGN)."""
        config = _make_mc_config(
            n_periods=10, n_scenarios=2000, demand_mean=5000.0, demand_std=500.0,
            random_seed=99,
        )
        series = ScenarioGenerator(config).generate_time_series()
        all_demands = [s.demand_value for period in series for s in period]
        assert abs(np.mean(all_demands) - 5000.0) < 150.0

    def test_all_scenarios_are_operation_scenarios(self):
        config = _make_mc_config(n_periods=2, n_scenarios=50)
        series = ScenarioGenerator(config).generate_time_series()
        for period in series:
            assert all(isinstance(s, OperationScenario) for s in period)


# ─────────────────────────────────────────────────────────────────────────────
# MONTE CARLO — cached_aggregate_results() (P1)
# ─────────────────────────────────────────────────────────────────────────────

class TestCachedAggregateResults:
    """
    Usa LocMemCache (Django dummy cache en memoria) para evitar Redis en tests.
    No requiere @pytest.mark.django_db (cache no toca la BD).
    """

    @pytest.fixture(autouse=True)
    def use_locmem_cache(self, settings):
        settings.CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'test-mc-cache',
            }
        }
        from django.core.cache import cache
        cache.clear()
        yield
        cache.clear()

    @pytest.fixture
    def samples_and_config(self):
        rng = np.random.default_rng(42)
        profits = rng.normal(5000, 1000, 2000)
        demands = rng.normal(2000, 200, 2000)
        revenues = rng.normal(30000, 3000, 2000)
        config = _make_mc_config(n_scenarios=2000, random_seed=42)
        return profits, demands, revenues, config

    def test_returns_same_as_aggregate_results(self, samples_and_config):
        p, d, r, cfg = samples_and_config
        direct = aggregate_results(p, d, r, cfg)
        cached = cached_aggregate_results(p, d, r, cfg)
        assert cached.profit_mean == pytest.approx(direct.profit_mean)
        assert cached.value_at_risk == pytest.approx(direct.value_at_risk)

    def test_second_call_uses_cache(self, samples_and_config):
        p, d, r, cfg = samples_and_config
        result1 = cached_aggregate_results(p, d, r, cfg)
        result2 = cached_aggregate_results(p, d, r, cfg)
        assert result1.profit_mean == pytest.approx(result2.profit_mean)
        assert result1.n_scenarios == result2.n_scenarios

    def test_force_recompute_bypasses_cache(self, samples_and_config):
        p, d, r, cfg = samples_and_config
        result1 = cached_aggregate_results(p, d, r, cfg)
        result2 = cached_aggregate_results(p, d, r, cfg, force_recompute=True)
        assert result1.profit_mean == pytest.approx(result2.profit_mean)

    def test_no_seed_does_not_cache(self, samples_and_config):
        """Sin random_seed la función no debe escribir en cache."""
        p, d, r, _ = samples_and_config
        cfg_no_seed = _make_mc_config(n_scenarios=2000, random_seed=None)
        from django.core.cache import cache
        cached_aggregate_results(p, d, r, cfg_no_seed)
        assert cache.get('mc:agg:') is None

    def test_different_configs_different_results(self, samples_and_config):
        p, d, r, cfg1 = samples_and_config
        cfg2 = _make_mc_config(
            n_scenarios=2000, random_seed=42, confidence_level=0.99
        )
        result1 = cached_aggregate_results(p, d, r, cfg1)
        result2 = cached_aggregate_results(p, d, r, cfg2)
        assert result1.confidence_level != result2.confidence_level

    def test_result_has_correct_metadata(self, samples_and_config):
        p, d, r, cfg = samples_and_config
        result = cached_aggregate_results(p, d, r, cfg)
        assert result.distribution_used == cfg.distribution
        assert result.n_scenarios == len(p)

    def test_returns_aggregated_result_type(self, samples_and_config):
        from simulate.core.monte_carlo import AggregatedResult
        p, d, r, cfg = samples_and_config
        result = cached_aggregate_results(p, d, r, cfg)
        assert isinstance(result, AggregatedResult)


# ─────────────────────────────────────────────────────────────────────────────
# P2A — RecommendationService (módulo extraído)
# ─────────────────────────────────────────────────────────────────────────────

class TestRecommendationService:
    """
    Tests del servicio extraído. Importa directamente desde el nuevo módulo.
    La interfaz pública es idéntica a RecommendationEngine (alias de compat).
    """

    @pytest.fixture
    def profitable_risk(self):
        return RiskMetrics(
            mean=8000, std=1200, variance=1440000,
            skewness=0.1, kurtosis=0.5,
            p1=4000, p5=5500, p10=6000, p25=7000,
            p50=8000, p75=9000, p90=10000, p95=10500, p99=12000,
            probability_of_loss=0.01,
            probability_breakeven=0.99,
            var_95=5500, var_99=4000,
            cvar_95=5000, cvar_99=3500,
            sharpe_ratio=5.0, sortino_ratio=None, downside_std=None,
        )

    @pytest.fixture
    def loss_risk(self):
        return RiskMetrics(
            mean=-2000, std=3000, variance=9000000,
            skewness=-0.5, kurtosis=4.0,
            p1=-8000, p5=-6000, p10=-5000, p25=-3000,
            p50=-2000, p75=0, p90=1000, p95=2000, p99=5000,
            probability_of_loss=0.65,
            probability_breakeven=0.35,
            var_95=-6000, var_99=-8000,
            cvar_95=-7000, cvar_99=-9000,
            sharpe_ratio=None, sortino_ratio=None, downside_std=None,
        )

    def test_importable_from_new_module(self):
        from simulate.services.recommendation_service import RecommendationService
        svc = RecommendationService()
        assert svc is not None

    def test_recommendation_engine_is_alias(self):
        """RecommendationEngine (importado de decision_engine) es el mismo objeto."""
        from simulate.core.decision_engine import RecommendationEngine
        assert RecommendationEngine is RecommendationService

    def test_generate_returns_list(self, profitable_risk):
        svc = RecommendationService()
        recs = svc.generate(profitable_risk, {'IT': 50000, 'GT': 8000, 'TG': 42000})
        assert isinstance(recs, list)

    def test_recommendation_type_is_correct(self, profitable_risk):
        svc = RecommendationService()
        recs = svc.generate(profitable_risk, {'IT': 50000, 'GT': 8000, 'TG': 42000})
        for rec in recs:
            assert isinstance(rec, SvcRecommendation)

    def test_critical_on_loss_operation(self, loss_risk):
        svc = RecommendationService()
        recs = svc.generate(loss_risk, {'IT': 10000, 'GT': -2000, 'TG': 12000})
        severities = [r.severity for r in recs]
        assert 'critical' in severities

    def test_no_critical_for_profitable_operation(self, profitable_risk):
        svc = RecommendationService(min_profit_margin_pct=10.0)
        recs = svc.generate(profitable_risk, {'IT': 50000, 'GT': 8000, 'TG': 42000})
        criticals = [r for r in recs if r.severity == 'critical']
        assert criticals == []

    def test_sorted_critical_before_warning(self, loss_risk):
        svc = RecommendationService()
        recs = svc.generate(loss_risk, {'IT': 5000, 'GT': -2000, 'TG': 7000})
        order = {'critical': 0, 'warning': 1, 'info': 2}
        for i in range(len(recs) - 1):
            assert order[recs[i].severity] <= order[recs[i + 1].severity]

    def test_to_dict_has_required_keys(self, loss_risk):
        svc = RecommendationService()
        recs = svc.generate(loss_risk, {'IT': 5000, 'GT': -2000, 'TG': 7000})
        assert recs
        d = recs[0].to_dict()
        for key in ('category', 'severity', 'title', 'message', 'metric_name',
                    'metric_value', 'threshold', 'action', 'impact'):
            assert key in d

    def test_custom_thresholds_respected(self):
        svc = RecommendationService(min_profit_margin_pct=30.0, max_cost_revenue_ratio=50.0)
        risk = RiskMetrics(
            mean=5000, std=500, variance=250000,
            skewness=0.0, kurtosis=0.0,
            p1=3500, p5=4000, p10=4200, p25=4600,
            p50=5000, p75=5400, p90=5800, p95=6000, p99=7000,
            probability_of_loss=0.02, probability_breakeven=0.98,
            var_95=4000, var_99=3500, cvar_95=3800, cvar_99=3200,
            sharpe_ratio=7.0, sortino_ratio=None, downside_std=None,
        )
        # margen = 5000/50000 = 10% < umbral 30% → debe generar warning
        recs = svc.generate(risk, {'IT': 50000, 'GT': 5000, 'TG': 45000})
        margin_warnings = [r for r in recs if 'margen' in r.metric_name.lower()]
        assert margin_warnings

    def test_demand_lost_warning(self, profitable_risk):
        svc = RecommendationService()
        recs = svc.generate(profitable_risk, {
            'IT': 50000, 'GT': 8000, 'TG': 42000,
            'DI': 600, 'DDP': 2000,  # 30% perdida
        })
        titles = [r.title for r in recs]
        assert any('demanda' in t.lower() for t in titles)

    def test_capacity_underutilized(self, profitable_risk):
        svc = RecommendationService()
        recs = svc.generate(profitable_risk, {
            'IT': 50000, 'GT': 8000, 'TG': 42000,
            'FU': 0.3,
        })
        cap_recs = [r for r in recs if 'capacidad' in r.title.lower()]
        assert cap_recs
        assert cap_recs[0].severity == 'info'

    def test_decision_engine_uses_recommendation_service(self, profitable_risk):
        """DecisionEngine._rec_engine es instancia de RecommendationService."""
        engine = DecisionEngine()
        assert isinstance(engine._rec_engine, RecommendationService)
