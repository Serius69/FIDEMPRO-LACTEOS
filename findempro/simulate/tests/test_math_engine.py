"""
test_math_engine.py
===================
Tests de validación matemática para los motores de simulación,
modelado de demanda y análisis financiero.

Valida:
  - Correctitud estadística (distribuciones, percentiles, CIs)
  - Consistencia financiera (break-even, márgenes, escenarios)
  - Comportamiento de riesgo (VaR, CVaR, P(pérdida))
  - Análisis de demanda (tendencias, estacionalidad, proyección)
  - Robustez ante entradas extremas o datos escasos
"""

import math
import numpy as np
import pytest

from simulate.services.simulation_engine import (
    MonteCarloEngine,
    SimulationConfig,
    SimulationResult,
)
from simulate.services.demand_model import DemandModelService
from simulate.services.financial_analysis import FinancialAnalysisEngine


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def base_config():
    return SimulationConfig(
        n_iterations=5000,
        confidence_level=0.95,
        time_periods=12,
        random_seed=42,
        distribution_type='normal',
        demand_mean=1000.0,
        demand_std=150.0,
        unit_price=10.0,
        unit_cost=6.0,
        fixed_costs=2000.0,
    )


@pytest.fixture
def historical_stable():
    """Serie de demanda estable con ruido pequeño."""
    rng = np.random.default_rng(42)
    return (1000 + rng.normal(0, 50, 60)).tolist()


@pytest.fixture
def historical_trending():
    """Serie de demanda con tendencia creciente."""
    rng = np.random.default_rng(42)
    return (np.linspace(800, 1200, 60) + rng.normal(0, 40, 60)).tolist()


@pytest.fixture
def historical_seasonal():
    """Serie de demanda con estacionalidad mensual."""
    rng = np.random.default_rng(42)
    t = np.arange(60)
    seasonal = 200 * np.sin(2 * np.pi * t / 12)
    return (1000 + seasonal + rng.normal(0, 30, 60)).tolist()


@pytest.fixture
def base_financials():
    return dict(
        revenue=100_000.0,
        variable_costs=60_000.0,
        fixed_costs=20_000.0,
        demand_mean=5_000.0,
        demand_std=500.0,
        unit_price=20.0,
        industry_sector='production',
    )


# ═════════════════════════════════════════════
# 1. TESTS DEL MOTOR MONTE CARLO
# ═════════════════════════════════════════════

class TestMonteCarloEngine:

    def test_simulation_config_rejects_invalid_financial_and_confidence_inputs(self):
        with pytest.raises(ValueError, match='confidence_level'):
            SimulationConfig(confidence_level=1.0)
        with pytest.raises(ValueError, match='unit_cost'):
            SimulationConfig(unit_cost=-1)
        with pytest.raises(ValueError, match='demand_min'):
            SimulationConfig(demand_min=10, demand_max=5)

    def test_result_returns_correct_type(self, base_config):
        engine = MonteCarloEngine(base_config)
        result = engine.run()
        assert isinstance(result, SimulationResult)

    def test_demand_mean_close_to_config(self, base_config):
        engine = MonteCarloEngine(base_config)
        result = engine.run()
        # Con 5000 iteraciones, la media simulada debe estar cerca de la configurada
        assert abs(result.demand_mean - base_config.demand_mean) < base_config.demand_mean * 0.05

    def test_demand_std_close_to_config(self, base_config):
        engine = MonteCarloEngine(base_config)
        result = engine.run()
        assert abs(result.demand_std - base_config.demand_std) < base_config.demand_std * 0.10

    def test_percentile_ordering(self, base_config):
        engine = MonteCarloEngine(base_config)
        result = engine.run()
        assert result.demand_p5 <= result.demand_p25
        assert result.demand_p25 <= result.demand_median
        assert result.demand_median <= result.demand_p75
        assert result.demand_p75 <= result.demand_p95

    def test_confidence_interval_contains_mean(self, base_config):
        engine = MonteCarloEngine(base_config)
        result = engine.run()
        assert result.demand_ci_lower <= result.demand_mean <= result.demand_ci_upper

    def test_probability_of_loss_range(self, base_config):
        engine = MonteCarloEngine(base_config)
        result = engine.run()
        assert 0.0 <= result.probability_of_loss <= 1.0
        assert abs(result.probability_of_loss + result.probability_breakeven - 1.0) < 1e-6

    def test_profitable_config_low_loss_probability(self, base_config):
        """Con precio >> costo, P(pérdida) debe ser muy baja."""
        cfg = SimulationConfig(
            n_iterations=5000, random_seed=0,
            demand_mean=1000, demand_std=50,
            unit_price=20.0, unit_cost=5.0, fixed_costs=1000.0,
        )
        engine = MonteCarloEngine(cfg)
        result = engine.run()
        assert result.probability_of_loss < 0.05

    def test_unprofitable_config_high_loss_probability(self):
        """Con costo >> precio, P(pérdida) debe ser muy alta."""
        cfg = SimulationConfig(
            n_iterations=5000, random_seed=0,
            demand_mean=1000, demand_std=50,
            unit_price=5.0, unit_cost=15.0, fixed_costs=5000.0,
        )
        engine = MonteCarloEngine(cfg)
        result = engine.run()
        assert result.probability_of_loss > 0.90

    def test_var_is_less_than_mean_profit(self, base_config):
        engine = MonteCarloEngine(base_config)
        result = engine.run()
        # VaR al 95% debe ser menor que la utilidad media (es el peor caso)
        assert result.value_at_risk_95 <= result.profit_mean

    def test_expected_shortfall_worse_than_var(self, base_config):
        engine = MonteCarloEngine(base_config)
        result = engine.run()
        # CVaR (ES) siempre debe ser <= VaR (pérdida promedio en la cola peor)
        assert result.expected_shortfall <= result.value_at_risk_95

    def test_risk_payload_exposes_configured_var_confidence(self):
        config = SimulationConfig(n_iterations=1200, confidence_level=0.90, random_seed=4)
        payload = MonteCarloEngine(config).to_dict()

        assert payload['risk']['confidence_level'] == 0.90
        assert payload['risk']['var_confidence_level'] == 0.90
        assert payload['risk']['cvar_confidence_level'] == 0.90

    def test_scenarios_count_and_names(self, base_config):
        engine = MonteCarloEngine(base_config)
        result = engine.run()
        assert len(result.scenarios) == 5
        names = [s.name for s in result.scenarios]
        assert 'Pesimista' in names
        assert 'Base' in names
        assert 'Muy Optimista' in names

    def test_scenarios_demand_ordering(self, base_config):
        """La demanda de los escenarios debe ser creciente."""
        engine = MonteCarloEngine(base_config)
        result = engine.run()
        demands = [s.demand_value for s in result.scenarios]
        assert all(demands[i] <= demands[i+1] for i in range(len(demands)-1))

    def test_time_series_length(self, base_config):
        engine = MonteCarloEngine(base_config)
        result = engine.run()
        assert len(result.time_series) == base_config.time_periods

    def test_time_series_has_required_keys(self, base_config):
        engine = MonteCarloEngine(base_config)
        result = engine.run()
        for period in result.time_series:
            assert 'period' in period
            assert 'demand_mean' in period
            assert 'profit_mean' in period
            assert 'profit_p5' in period
            assert 'profit_p95' in period

    def test_reproducibility_with_seed(self, base_config):
        """La misma semilla debe producir los mismos resultados."""
        e1 = MonteCarloEngine(base_config)
        r1 = e1.run()
        e2 = MonteCarloEngine(base_config)
        r2 = e2.run()
        assert abs(r1.demand_mean - r2.demand_mean) < 1e-6

    def test_lognormal_distribution(self):
        cfg = SimulationConfig(
            n_iterations=5000, random_seed=42,
            distribution_type='lognormal',
            demand_mean=1000, demand_std=200,
            unit_price=10, unit_cost=6, fixed_costs=2000,
        )
        engine = MonteCarloEngine(cfg)
        result = engine.run()
        # Log-normal produce solo valores positivos
        assert result.demand_p5 >= 0
        assert isinstance(result.demand_mean, float)

    def test_gamma_distribution(self):
        cfg = SimulationConfig(
            n_iterations=5000, random_seed=42,
            distribution_type='gamma',
            demand_mean=1000, demand_std=300,
            unit_price=10, unit_cost=6, fixed_costs=2000,
        )
        engine = MonteCarloEngine(cfg)
        result = engine.run()
        assert result.demand_p5 >= 0

    def test_uniform_distribution(self):
        cfg = SimulationConfig(
            n_iterations=5000, random_seed=42,
            distribution_type='uniform',
            demand_mean=1000, demand_std=200,
            demand_min=600, demand_max=1400,
            unit_price=10, unit_cost=6, fixed_costs=2000,
        )
        engine = MonteCarloEngine(cfg)
        result = engine.run()
        assert result.demand_p5 >= 600 - 50   # Tolerancia numérica
        assert result.demand_p95 <= 1400 + 50

    def test_invalid_distribution_raises(self, base_config):
        base_config.distribution_type = 'quantum_physics'
        engine = MonteCarloEngine(base_config)
        with pytest.raises(ValueError):
            engine.run()

    def test_to_dict_has_all_sections(self, base_config):
        engine = MonteCarloEngine(base_config)
        d = engine.to_dict()
        assert 'demand' in d
        assert 'revenue' in d
        assert 'profit' in d
        assert 'risk' in d
        assert 'scenarios' in d
        assert 'time_series' in d
        assert 'metadata' in d

    def test_seasonality_affects_time_series(self):
        """Estacionalidad debe producir variación en la serie temporal."""
        cfg_flat = SimulationConfig(
            n_iterations=2000, random_seed=42,
            demand_mean=1000, demand_std=10,
            unit_price=10, unit_cost=6, fixed_costs=1000,
            seasonality_factors=[1.0] * 12,
            time_periods=12,
        )
        cfg_season = SimulationConfig(
            n_iterations=2000, random_seed=42,
            demand_mean=1000, demand_std=10,
            unit_price=10, unit_cost=6, fixed_costs=1000,
            seasonality_factors=[0.7, 0.8, 0.9, 1.0, 1.1, 1.3,
                                  1.3, 1.1, 1.0, 0.9, 0.8, 1.4],
            time_periods=12,
        )
        r_flat = MonteCarloEngine(cfg_flat).run()
        r_season = MonteCarloEngine(cfg_season).run()
        # Con estacionalidad, la variación entre períodos debe ser mayor
        flat_means = [p['demand_mean'] for p in r_flat.time_series]
        season_means = [p['demand_mean'] for p in r_season.time_series]
        assert np.std(season_means) > np.std(flat_means)

    def test_fit_best_distribution_returns_valid(self, historical_stable):
        dist, ks = MonteCarloEngine.fit_best_distribution(np.array(historical_stable))
        assert dist in ('normal', 'lognormal', 'gamma', 'exponential', 'uniform')
        assert 0.0 <= ks <= 1.0


# ═════════════════════════════════════════════
# 2. TESTS DEL MODELO DE DEMANDA
# ═════════════════════════════════════════════

class TestDemandModelService:

    def test_demand_model_rejects_nonfinite_data_and_invalid_confidence(self):
        with pytest.raises(ValueError, match='finitos'):
            DemandModelService([1, 2, 3, 4, np.nan])
        with pytest.raises(ValueError, match='confidence_level'):
            DemandModelService([1, 2, 3, 4, 5], confidence_level=0)

    def test_raises_with_too_few_points(self):
        with pytest.raises(ValueError):
            DemandModelService([100, 200, 300])

    def test_descriptive_stats_correctness(self, historical_stable):
        service = DemandModelService(historical_stable)
        stats = service.descriptive_stats()
        assert abs(stats['mean'] - np.mean(historical_stable)) < 1e-6
        assert abs(stats['median'] - np.median(historical_stable)) < 1e-6
        assert stats['min'] == min(historical_stable)
        assert stats['max'] == max(historical_stable)
        assert stats['count'] == len(historical_stable)

    def test_cv_positive(self, historical_stable):
        service = DemandModelService(historical_stable)
        stats = service.descriptive_stats()
        assert stats['cv'] >= 0

    def test_fit_distribution_returns_known_type(self, historical_stable):
        service = DemandModelService(historical_stable)
        name, params, ks, pval = service.fit_distribution()
        assert name in ('normal', 'lognormal', 'gamma', 'exponential', 'uniform')
        assert 0 <= ks <= 1
        assert isinstance(params, dict)

    def test_trend_stable_data_near_zero_slope(self, historical_stable):
        service = DemandModelService(historical_stable)
        trend = service.analyze_trend()
        # Datos estables: pendiente pequeña relativa a la media
        assert abs(trend['slope']) < np.mean(historical_stable) * 0.05

    def test_trend_increasing_data(self, historical_trending):
        service = DemandModelService(historical_trending)
        trend = service.analyze_trend()
        assert trend['direction'] == 'increasing'
        assert trend['slope'] > 0
        assert trend['r2'] > 0.5

    def test_seasonality_detected(self, historical_seasonal):
        service = DemandModelService(historical_seasonal, seasonality_period=12)
        result = service.analyze_seasonality()
        assert result['has_seasonality'] is True

    def test_forecast_length(self, historical_stable):
        service = DemandModelService(historical_stable)
        forecast = service.forecast(periods=30)
        assert len(forecast.forecasted_values) == 30
        assert len(forecast.ci_lower) == 30
        assert len(forecast.ci_upper) == 30

    def test_forecast_ci_ordering(self, historical_stable):
        """CI inferior siempre <= valor proyectado <= CI superior."""
        service = DemandModelService(historical_stable)
        forecast = service.forecast(periods=20)
        for lo, mid, hi in zip(forecast.ci_lower, forecast.forecasted_values, forecast.ci_upper):
            assert lo <= mid + 1e-6
            assert mid <= hi + 1e-6

    def test_forecast_non_negative(self, historical_stable):
        service = DemandModelService(historical_stable)
        forecast = service.forecast(periods=20)
        assert all(v >= 0 for v in forecast.ci_lower)

    def test_moving_average_forecast(self, historical_stable):
        service = DemandModelService(historical_stable)
        forecast = service.forecast(periods=10, method='moving_average')
        # Todos los valores iguales a la última media móvil
        assert len(set(round(v, 4) for v in forecast.forecasted_values)) == 1

    def test_holdout_mape_uses_selected_moving_average_method(self):
        service = DemandModelService([1, 1, 1, 1, 1, 1, 1, 10, 20, 30])

        forecast = service.forecast(periods=2, method='moving_average')
        train = np.asarray([1, 1, 1, 1, 1, 1, 1, 10], dtype=float)
        expected_prediction = np.mean(train[-7:])
        expected = np.mean(np.abs((np.asarray([20, 30]) - expected_prediction) / np.asarray([20, 30]))) * 100

        assert forecast.mape == round(float(expected), 2)

    def test_auto_holdout_selection_uses_training_prefix(self, historical_trending, monkeypatch):
        service = DemandModelService(historical_trending)
        observed_lengths = []
        original = service._select_method

        def observe(data):
            observed_lengths.append(len(data))
            return original(data)

        monkeypatch.setattr(service, '_select_method', observe)
        service.forecast(periods=4, method='auto')

        assert len(service.data) in observed_lengths
        assert len(service.data) - max(1, len(service.data) // 5) in observed_lengths

    def test_exponential_smoothing_forecast(self, historical_stable):
        service = DemandModelService(historical_stable)
        forecast = service.forecast(periods=10, method='exponential_smoothing')
        assert len(forecast.forecasted_values) == 10

    def test_invalid_method_raises(self, historical_stable):
        service = DemandModelService(historical_stable)
        with pytest.raises(ValueError):
            service.forecast(method='black_magic')

    def test_outlier_detection(self):
        data = [1000.0] * 50 + [9999.0, -500.0]  # 2 outliers
        service = DemandModelService(data)
        outliers, count = service.detect_outliers()
        assert count >= 1

    def test_analyze_returns_complete_object(self, historical_stable):
        service = DemandModelService(historical_stable)
        analysis = service.analyze(forecast_periods=10)
        assert analysis.mean > 0
        assert analysis.best_distribution in ('normal', 'lognormal', 'gamma', 'exponential', 'uniform')
        assert analysis.trend_direction in ('increasing', 'decreasing', 'stable')
        assert len(analysis.forecast_next) == 10

    def test_to_simulation_params(self, historical_stable):
        service = DemandModelService(historical_stable)
        params = service.to_simulation_params()
        assert 'distribution_type' in params
        assert 'demand_mean' in params
        assert 'demand_std' in params
        assert params['demand_mean'] > 0

    def test_high_cv_triggers_volatility_alert(self):
        """Datos muy volátiles deben activar la alerta."""
        rng = np.random.default_rng(1)
        volatile = (500 + rng.normal(0, 400, 60)).clip(0).tolist()
        service = DemandModelService(volatile)
        analysis = service.analyze(forecast_periods=5)
        assert analysis.volatility_alert is True


# ═════════════════════════════════════════════
# 3. TESTS DEL MOTOR FINANCIERO
# ═════════════════════════════════════════════

class TestFinancialAnalysisEngine:

    def test_metrics_basic_correctness(self, base_financials):
        engine = FinancialAnalysisEngine(**base_financials)
        m = engine.compute_metrics()
        expected_gross = base_financials['revenue'] - base_financials['variable_costs']
        expected_net = expected_gross - base_financials['fixed_costs']
        assert abs(m.gross_profit - expected_gross) < 1e-4
        assert abs(m.net_profit - expected_net) < 1e-4
        assert m.ebitda_proxy is None
        assert m.operating_cash_flow is None

    def test_financial_engine_rejects_negative_monetary_inputs(self, base_financials):
        invalid = dict(base_financials, fixed_costs=-1)
        with pytest.raises(ValueError, match='fixed_costs'):
            FinancialAnalysisEngine(**invalid)

    def test_profit_margin_formula(self, base_financials):
        engine = FinancialAnalysisEngine(**base_financials)
        m = engine.compute_metrics()
        expected = (m.net_profit / base_financials['revenue']) * 100
        assert abs(m.net_margin_pct - expected) < 1e-4

    def test_roi_formula(self, base_financials):
        engine = FinancialAnalysisEngine(**base_financials)
        m = engine.compute_metrics()
        assert m.roi_pct is None

        invested = 200_000.0
        invested_engine = FinancialAnalysisEngine(**base_financials, investment=invested)
        invested_metrics = invested_engine.compute_metrics()
        expected = (invested_metrics.net_profit / invested) * 100
        assert abs(invested_metrics.roi_pct - expected) < 1e-4

    def test_cost_ratio_formula(self, base_financials):
        engine = FinancialAnalysisEngine(**base_financials)
        m = engine.compute_metrics()
        expected = (m.total_costs / base_financials['revenue']) * 100
        assert abs(m.cost_revenue_ratio_pct - expected) < 1e-4

    def test_breakeven_positive(self, base_financials):
        engine = FinancialAnalysisEngine(**base_financials)
        m = engine.compute_metrics()
        assert m.breakeven_units >= 0
        assert m.breakeven_revenue >= 0

    def test_breakeven_verification(self, base_financials):
        """Verificar que el break-even cumple la ecuación fundamental."""
        engine = FinancialAnalysisEngine(**base_financials)
        m = engine.compute_metrics()
        if m.breakeven_units > 0 and m.breakeven_units != -1:
            unit_price = base_financials['revenue'] / base_financials['demand_mean']
            unit_var_cost = base_financials['variable_costs'] / base_financials['demand_mean']
            # En el break-even: revenue = total_costs
            be_rev = m.breakeven_units * unit_price
            be_costs = m.breakeven_units * unit_var_cost + base_financials['fixed_costs']
            assert abs(be_rev - be_costs) / max(be_rev, 1) < 0.01  # <1% error

    def test_margin_of_safety_when_above_breakeven(self, base_financials):
        engine = FinancialAnalysisEngine(**base_financials)
        m = engine.compute_metrics()
        if m.net_profit > 0:
            assert m.margin_of_safety_pct > 0

    def test_health_score_range(self, base_financials):
        engine = FinancialAnalysisEngine(**base_financials)
        m = engine.compute_metrics()
        assert 0.0 <= m.financial_health_score <= 100.0

    def test_health_score_profitable_business_high(self, base_financials):
        """Negocio rentable debe tener puntaje alto."""
        engine = FinancialAnalysisEngine(**base_financials)
        m = engine.compute_metrics()
        assert m.financial_health_score > 50

    def test_health_score_unprofitable_business_low(self):
        engine = FinancialAnalysisEngine(
            revenue=50_000, variable_costs=80_000, fixed_costs=20_000,
            demand_mean=5000, unit_price=10,
        )
        m = engine.compute_metrics()
        assert m.financial_health_score < 40

    def test_profitability_rating_valid_values(self, base_financials):
        engine = FinancialAnalysisEngine(**base_financials)
        m = engine.compute_metrics()
        assert m.profitability_rating in ('excelente', 'bueno', 'regular', 'crítico')

    def test_scenarios_five_scenarios(self, base_financials):
        engine = FinancialAnalysisEngine(**base_financials)
        scenarios = engine.compute_scenarios()
        assert len(scenarios) == 5
        assert 'pesimista' in scenarios
        assert 'base' in scenarios
        assert 'muy_optimista' in scenarios

    def test_scenarios_profit_ordering(self, base_financials):
        """La utilidad en los escenarios debe ser creciente (más demanda → más ganancia)."""
        engine = FinancialAnalysisEngine(**base_financials)
        scenarios = engine.compute_scenarios()
        profits = [scenarios[k]['gross_profit'] for k in
                   ['pesimista', 'conservador', 'base', 'optimista', 'muy_optimista']]
        assert all(profits[i] <= profits[i+1] for i in range(len(profits)-1))

    def test_base_scenario_matches_metrics(self, base_financials):
        """El escenario base debe ser coherente con las métricas actuales."""
        engine = FinancialAnalysisEngine(**base_financials)
        m = engine.compute_metrics()
        scenarios = engine.compute_scenarios()
        base = scenarios['base']
        # El escenario base (factor=1.0) debe tener el mismo ingreso que el actual
        assert abs(base['revenue'] - base_financials['revenue']) < 1.0

    def test_risk_metrics_range(self, base_financials):
        engine = FinancialAnalysisEngine(**base_financials)
        r = engine.compute_risk()
        assert r.available is False
        assert r.unavailable_reason == 'INSUFFICIENT_PROFIT_SAMPLES'
        assert r.probability_of_loss is None
        assert r.value_at_risk_95 is None
        assert r.expected_shortfall is None
        assert r.risk_score is None
        assert r.risk_rating is None

    def test_risk_with_monte_carlo_samples(self, base_financials):
        """Con muestras reales, las métricas deben ser más precisas."""
        rng = np.random.default_rng(42)
        samples = rng.normal(20000, 5000, 10000)  # Ganancias simuladas
        engine = FinancialAnalysisEngine(**base_financials, profit_samples=samples)
        r = engine.compute_risk()
        expected_prob_loss = float(np.mean(samples < 0))
        assert r.available is True
        assert r.unavailable_reason is None
        assert abs(r.probability_of_loss - expected_prob_loss) < 0.01

    def test_risk_rejects_nonfinite_samples(self, base_financials):
        engine = FinancialAnalysisEngine(
            **base_financials,
            profit_samples=np.array([1.0] * 11 + [np.nan]),
        )
        with pytest.raises(ValueError, match='valores finitos'):
            engine.compute_risk()

    def test_recommendations_not_empty(self, base_financials):
        engine = FinancialAnalysisEngine(**base_financials)
        m = engine.compute_metrics()
        r = engine.compute_risk()
        recs = engine.generate_recommendations(m, r)
        assert len(recs) > 0

    def test_recommendations_critical_for_loss(self):
        """Negocio con pérdidas debe generar recomendaciones críticas."""
        engine = FinancialAnalysisEngine(
            revenue=30_000, variable_costs=40_000, fixed_costs=15_000,
            demand_mean=3000, unit_price=10,
        )
        m = engine.compute_metrics()
        r = engine.compute_risk()
        recs = engine.generate_recommendations(m, r)
        severities = [rec.severity for rec in recs]
        assert 'critical' in severities

    def test_recommendations_sorted_by_severity(self, base_financials):
        """Las recomendaciones deben estar ordenadas: critical > warning > info."""
        engine = FinancialAnalysisEngine(
            revenue=30_000, variable_costs=40_000, fixed_costs=15_000,
            demand_mean=3000, unit_price=10,
        )
        m = engine.compute_metrics()
        r = engine.compute_risk()
        recs = engine.generate_recommendations(m, r)
        severity_order = {'critical': 0, 'warning': 1, 'info': 2}
        for i in range(len(recs) - 1):
            assert severity_order[recs[i].severity] <= severity_order[recs[i+1].severity]

    def test_generate_report_complete(self, base_financials):
        engine = FinancialAnalysisEngine(**base_financials)
        report = engine.generate_report()
        assert report.metrics is not None
        assert report.risk is not None
        assert len(report.scenarios) == 5
        assert isinstance(report.recommendations, list)
        assert isinstance(report.summary, str)
        assert 0 <= report.score_overall <= 100

    def test_to_dict_serializable(self, base_financials):
        """El resultado en dict no debe contener tipos no serializables."""
        import json
        engine = FinancialAnalysisEngine(**base_financials)
        d = engine.to_dict()
        # No debe lanzar excepción
        json_str = json.dumps(d)
        assert len(json_str) > 100

    def test_sector_thresholds_applied(self):
        """Distintos sectores deben aplicar distintos umbrales."""
        e_retail = FinancialAnalysisEngine(
            revenue=100000, variable_costs=60000, fixed_costs=20000,
            demand_mean=5000, industry_sector='retail',
        )
        e_services = FinancialAnalysisEngine(
            revenue=100000, variable_costs=60000, fixed_costs=20000,
            demand_mean=5000, industry_sector='services',
        )
        assert e_retail.min_profit_margin < e_services.min_profit_margin

    def test_zero_revenue_edge_case(self):
        """Revenue=0 no debe causar ZeroDivisionError."""
        engine = FinancialAnalysisEngine(
            revenue=0.01, variable_costs=1000, fixed_costs=500,
            demand_mean=1, unit_price=0.01,
        )
        m = engine.compute_metrics()
        assert isinstance(m.net_margin_pct, float)
        assert isinstance(m.financial_health_score, float)


# ═════════════════════════════════════════════
# 4. TESTS DE INTEGRACIÓN
# ═════════════════════════════════════════════

class TestIntegration:

    def test_demand_model_feeds_monte_carlo(self, historical_stable):
        """El DemandModelService debe proveer parámetros válidos al MonteCarloEngine."""
        demand_service = DemandModelService(historical_stable)
        params = demand_service.to_simulation_params()

        config = SimulationConfig(
            n_iterations=2000,
            random_seed=42,
            distribution_type=params['distribution_type'],
            demand_mean=params['demand_mean'],
            demand_std=params['demand_std'],
            unit_price=12.0,
            unit_cost=7.0,
            fixed_costs=3000.0,
        )
        engine = MonteCarloEngine(config)
        result = engine.run()

        assert result.demand_mean > 0
        assert result.probability_of_loss >= 0

    def test_monte_carlo_feeds_financial_analysis(self, base_config):
        """Las muestras del MC deben alimentar el análisis financiero correctamente."""
        mc_engine = MonteCarloEngine(base_config)
        mc_result = mc_engine.run()

        profit_samples = (
            mc_result.demand_samples * base_config.unit_price
            - mc_result.demand_samples * base_config.unit_cost
            - base_config.fixed_costs
        )

        fa_engine = FinancialAnalysisEngine(
            revenue=mc_result.revenue_mean,
            variable_costs=mc_result.demand_mean * base_config.unit_cost,
            fixed_costs=base_config.fixed_costs,
            demand_mean=mc_result.demand_mean,
            demand_std=mc_result.demand_std,
            unit_price=base_config.unit_price,
            profit_samples=profit_samples,
        )
        report = fa_engine.generate_report()

        # La P(pérdida) del FA debe ser coherente con la del MC
        assert abs(report.risk.probability_of_loss - mc_result.probability_of_loss) < 0.05

    def test_full_pipeline_retail_sector(self):
        """Pipeline completo para empresa retail."""
        rng = np.random.default_rng(99)
        historical = (500 + rng.normal(0, 80, 48)).clip(0).tolist()

        demand_service = DemandModelService(historical, confidence_level=0.90)
        params = demand_service.to_simulation_params()
        forecast = demand_service.forecast(periods=30)

        config = SimulationConfig(
            n_iterations=3000, random_seed=99,
            distribution_type=params['distribution_type'],
            demand_mean=params['demand_mean'],
            demand_std=params['demand_std'],
            unit_price=25.0, unit_cost=15.0, fixed_costs=4000.0,
            time_periods=30,
        )
        mc_engine = MonteCarloEngine(config)
        mc_dict = mc_engine.to_dict()

        fa_engine = FinancialAnalysisEngine(
            revenue=params['demand_mean'] * 25,
            variable_costs=params['demand_mean'] * 15,
            fixed_costs=4000.0,
            demand_mean=params['demand_mean'],
            demand_std=params['demand_std'],
            unit_price=25.0,
            industry_sector='retail',
        )
        report = fa_engine.generate_report()

        assert len(forecast.forecasted_values) == 30
        assert 'demand' in mc_dict
        assert report.score_overall >= 0
        assert len(report.recommendations) > 0


# ═════════════════════════════════════════════
# RNG de instancia (item 29): reproducibilidad y thread-safety
# ═════════════════════════════════════════════

class TestMonteCarloEngineRNG:
    """
    Verifica que MonteCarloEngine use un RNG de instancia (np.random.default_rng)
    en vez del estado global np.random.seed. Misma semilla → resultados idénticos;
    semillas distintas → resultados distintos.
    """

    def _make(self, seed):
        return MonteCarloEngine(SimulationConfig(
            n_iterations=5000,
            confidence_level=0.95,
            time_periods=12,
            random_seed=seed,
            distribution_type='normal',
            demand_mean=1000.0,
            demand_std=150.0,
            unit_price=10.0,
            unit_cost=6.0,
            fixed_costs=2000.0,
        ))

    def test_uses_instance_generator_not_global_seed(self):
        engine = self._make(42)
        assert isinstance(engine.rng, np.random.Generator)

    def test_same_seed_identical_samples(self):
        s1 = self._make(42)._sample_demand(4000)
        s2 = self._make(42)._sample_demand(4000)
        assert np.array_equal(s1, s2)

    def test_same_seed_identical_results(self):
        r1 = self._make(7).run()
        r2 = self._make(7).run()
        assert r1.demand_mean == r2.demand_mean
        assert r1.profit_mean == r2.profit_mean
        assert r1.value_at_risk_95 == r2.value_at_risk_95
        assert r1.profit_ci_lower == r2.profit_ci_lower
        assert r1.profit_ci_upper == r2.profit_ci_upper

    def test_different_seed_different_results(self):
        r1 = self._make(1).run()
        r2 = self._make(2).run()
        assert r1.profit_mean != r2.profit_mean

    def test_global_seed_not_mutated(self):
        """El engine NO debe tocar el estado global de np.random."""
        np.random.seed(12345)
        before = np.random.get_state()[1].copy()
        self._make(999).run()
        after = np.random.get_state()[1].copy()
        assert np.array_equal(before, after)
