import numpy as np
import pytest
import re
from pathlib import Path
from types import SimpleNamespace

from simulate.services.demand_model import DemandModelService
from simulate.services.context_manager import SimulationContextManager
from simulate.services.statistical_service import StatisticalService
from simulate.services.validation_service import SimulationValidationService
from simulate.utils.statistical_contracts import stable_distribution_shape
from simulate.utils.chart_utils import ChartGenerator
from simulate.views.simulate_init_view import SimulateShowView
from simulate.views.simulate_result_view import SimulateResultView


def test_forecast_metrics_do_not_truncate_non_comparable_series():
    service = StatisticalService()

    assert service._calculate_mape([1, 2, 3], [1, 2]) is None
    assert service._calculate_rmse([1, 2, 3], [1, 2]) is None
    assert service._calculate_mae([1, 2, 3], [1, 2]) is None


def test_mape_is_unavailable_when_all_actuals_are_zero():
    service = StatisticalService()

    assert service._calculate_mape([0, 0], [0, 0]) is None


def test_equal_length_forecast_metrics_remain_deterministic():
    service = StatisticalService()
    actual = np.asarray([10.0, 20.0, 30.0])
    predicted = np.asarray([11.0, 18.0, 33.0])

    assert service._calculate_rmse(actual, predicted) == np.sqrt(14 / 3)
    assert service._calculate_mae(actual, predicted) == 2.0


def test_distribution_shape_matches_standard_biased_moments():
    values = np.array([1.0, 2.0, 3.0, 8.0])
    centered = values - np.mean(values)
    second_moment = np.mean(centered ** 2)
    expected_skewness = np.mean(centered ** 3) / second_moment ** 1.5
    expected_kurtosis = np.mean(centered ** 4) / second_moment ** 2 - 3.0
    shape = stable_distribution_shape(values)

    assert shape.status == "AVAILABLE"
    assert shape.skewness == pytest.approx(expected_skewness)
    assert shape.kurtosis == pytest.approx(expected_kurtosis)


def test_basic_statistics_exposes_degenerate_shape_as_unavailable():
    stats_result = StatisticalService()._calculate_basic_statistics(np.array([7.0] * 5))

    assert stats_result["skewness"] is None
    assert stats_result["kurtosis"] is None
    assert stats_result["shape_statistics_status"] == "DEGENERATE_DISTRIBUTION"


def test_historical_init_view_uses_real_v2_fit_without_fabricated_pvalue():
    result = SimulateShowView()._basic_statistical_analysis(
        [8.0, 9.0, 10.0, 11.0, 12.0, 9.5, 10.5, 11.5]
    )

    diagnostic = result["distribution_fit_diagnostic"]
    assert diagnostic["method_version"] == "distribution_fit_v2"
    assert diagnostic["valid"] is True
    assert 0 <= diagnostic["statistic"] <= 1
    assert diagnostic["p_value"] is None
    assert diagnostic["p_value_unavailable_reason"] == "PARAMETERS_ESTIMATED_FROM_SAME_SAMPLE"
    assert result["best_ks_p_value_floor"] is None


@pytest.mark.parametrize(
    ("sample", "reason"),
    [
        ([1.0, 2.0, 3.0, 4.0], "INSUFFICIENT_SAMPLE"),
        ([5.0, 5.0, 5.0, 5.0, 5.0], "NO_COMPATIBLE_DISTRIBUTION"),
    ],
)
def test_historical_init_view_marks_unavailable_fit(sample, reason):
    result = SimulateShowView()._basic_statistical_analysis(sample)

    assert result["best_distribution"] is None
    assert result["best_ks_statistic_floor"] is None
    assert result["best_ks_p_value_floor"] is None
    assert result["distribution_fit_diagnostic"]["valid"] is False
    assert result["distribution_fit_diagnostic"]["unavailable_reason"] == reason


def test_historical_init_view_records_nonfinite_exclusions_without_zero_imputation():
    result = SimulateShowView()._basic_statistical_analysis(
        [1.0, 2.0, 3.0, 4.0, 5.0, float("nan"), float("inf")]
    )

    assert result["original_data_count"] == 7
    assert result["cleaned_data_count"] == 5
    assert result["distribution_fit_diagnostic"]["excluded_observations"] == 2
    assert result["demand_mean"] == 3.0


def test_legacy_statistical_service_ranks_by_aic_and_withholds_fitted_ks_pvalue():
    distribution = SimpleNamespace(distribution_type=1, name="Normal", id=1)
    result = StatisticalService()._test_distribution_fit(
        np.array([8.0, 9.0, 10.0, 11.0, 12.0]),
        distribution,
        {},
    )

    assert result["valid"] is True
    assert result["aic"] is not None
    assert result["ks_statistic"] is not None
    assert result["ks_p_value"] is None
    assert result["diagnostic"]["method_version"] == "distribution_fit_v2"


@pytest.mark.parametrize(
    "consumer",
    [
        SimulationContextManager.__new__(SimulationContextManager),
        SimulateResultView.__new__(SimulateResultView),
    ],
)
def test_result_distribution_consumers_expose_real_statistic_and_unavailable_pvalue(consumer):
    result = consumer._analyze_distribution([8.0, 9.0, 10.0, 11.0, 12.0, 9.5])
    diagnostic = result["distribution_fit"]

    assert diagnostic["method_version"] == "distribution_fit_v2"
    assert diagnostic["valid"] is True
    assert 0 <= diagnostic["statistic"] <= 1
    assert diagnostic["p_value"] is None
    assert diagnostic["p_value_unavailable_reason"] == "PARAMETERS_ESTIMATED_FROM_SAME_SAMPLE"


def test_validation_distribution_diagnostic_does_not_create_confidence_from_missing_pvalue():
    service = SimulationValidationService()
    validation_results = {
        "summary": {"total_tests": 0, "passed_tests": 0, "critical_failures": 0},
        "alerts": [],
    }
    demand = service._perform_ks_test_demand(
        [8.0, 9.0, 10.0, 11.0, 12.0, 9.5],
        None,
        validation_results,
    )

    assert demand["best_p_value"] is None
    assert demand["overall_passes"] is None
    assert validation_results["summary"]["total_tests"] == 0

    report = service._generate_reliability_report(
        {"summary": validation_results["summary"], "ks_tests": {"demand": demand}}
    )
    component = report["component_analysis"]["demand"]
    assert component["confidence"] is None
    assert component["reliability"] is None
    assert component["status"] == "diagnostic_only"


def test_variable_distribution_diagnostic_never_passes_from_uncalibrated_pvalue():
    result = SimulationValidationService()._perform_ks_test_variable(
        [8.0, 9.0, 10.0, 11.0, 12.0],
        "IT",
        {"summary": {"total_tests": 0, "passed_tests": 0}, "alerts": []},
    )

    assert result["method_version"] == "distribution_fit_v2"
    assert result["statistic"] is not None
    assert result["p_value"] is None
    assert result["passes_test"] is None


def test_legacy_distribution_ui_contains_no_random_or_threshold_fabricated_pvalues():
    project_root = Path(__file__).resolve().parents[2]
    sources = [
        project_root / "static/js/simulate/tabs/statistical-analysis.js",
        project_root / "templates/simulate/result/tabs/analysis-tab.html",
        project_root / "templates/simulate/result/tabs/ksvalidation-tab.html",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in sources)

    assert not re.search(r"pValue\s*=.*Math\.random", combined)
    assert "const pValue = isNormal ? 0.15 : 0.02" not in combined
    assert "const pValue = tStatistic < 1.96 ? 0.1 : 0.01" not in combined
    assert "const pValue = fStatistic < 2.5 ? 0.1 : 0.01" not in combined
    assert "const pValue = maxDiff < 0.3 ? 0.1 : 0.01" not in combined


def test_active_result_views_do_not_generate_placeholder_observations():
    project_root = Path(__file__).resolve().parents[2]
    sources = [
        project_root / "templates/simulate/result/tabs/analysis-tab.html",
        project_root / "templates/simulate/result/tabs/endogenous-tab.html",
        project_root / "simulate/utils/chart_utils.py",
        project_root / "simulate/utils/chart_demand_utils.py",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in sources)

    assert "Math.random" not in combined
    assert "generateMockChartData" not in combined
    assert "projection_adjusted" not in combined
    assert "rng.normal" not in combined


def test_financial_charts_are_unavailable_without_observed_values():
    charts = ChartGenerator()

    assert charts.generate_rentabilidad_diaria_chart([{}]) is None
    assert charts.generate_tendencia_promedio_movil_chart([{}]) is None


def test_explicit_zero_profit_is_not_treated_as_missing_data():
    chart = ChartGenerator().generate_rentabilidad_diaria_chart([
        {'IT': 100.0, 'TG': 100.0, 'GT': 0.0},
        {'IT': 100.0, 'TG': 100.0, 'GT': 0.0},
    ])

    assert isinstance(chart, str)
    assert chart


def test_demand_distribution_fit_does_not_drop_negative_observations_for_symmetric_candidates():
    service = DemandModelService([-100, -90, -80, -70, -60, 1, 2, 3, 4, 5])

    _, params, _, _ = service.fit_distribution()

    assert any(isinstance(value, (int, float)) and value < 0 for value in params.values())


def test_demand_distribution_fit_fails_explicitly_when_all_candidates_fail(monkeypatch):
    service = DemandModelService([1, 2, 3, 4, 5])

    class BrokenDistribution:
        @staticmethod
        def fit(_data):
            raise ValueError("broken candidate")

    monkeypatch.setattr(service, "DISTRIBUTIONS", {"broken": BrokenDistribution})

    with pytest.raises(ValueError, match="compatible"):
        service.fit_distribution()


def test_demand_distribution_fit_rejects_degenerate_zero_scale_candidates():
    service = DemandModelService([5, 5, 5, 5, 5])

    with pytest.raises(ValueError, match="compatible"):
        service.fit_distribution()


def test_legacy_distribution_parameter_fit_rejects_invalid_support_and_degenerate_data():
    service = StatisticalService()

    with pytest.raises(ValueError, match="positivos"):
        service.calculate_distribution_parameters(3, (-1, 2, 3, 4))
    with pytest.raises(ValueError, match="variación"):
        service.calculate_distribution_parameters(1, (5, 5, 5, 5))


def test_prediction_validation_does_not_turn_invalid_values_into_perfect_zeros():
    result = SimulationValidationService()._validate_model_predictions(None, ["bad"], ["also-bad"])

    assert result["validation_status"] == "FAILED"
    assert result["predictions_validated"] == 0
    assert result["invalid_pairs_dropped"] == 1
    assert result["accuracy_metrics"] == {}


def test_prediction_validation_drops_invalid_values_pairwise_without_time_shift():
    result = SimulationValidationService()._validate_model_predictions(
        None,
        [10, "bad", 30],
        [10, 20, 30],
    )

    assert result["validation_status"] == "PASSED"
    assert result["predictions_validated"] == 2
    assert result["invalid_pairs_dropped"] == 1
    assert result["accuracy_metrics"]["accuracy_rate"] == 1.0
    assert result["accuracy_metrics"]["mean_absolute_error"] == 0.0


def test_prediction_validation_reports_unpaired_and_non_finite_values():
    result = SimulationValidationService()._validate_model_predictions(
        None,
        [10, float("nan"), 30, 40],
        [10, 20, 30],
    )

    assert result["predictions_validated"] == 2
    assert result["invalid_pairs_dropped"] == 1
    assert result["unpaired_values_dropped"] == 1
    assert len(result["warnings"]) == 2


def test_prediction_validation_keeps_zero_actual_mape_unavailable():
    result = SimulationValidationService()._validate_model_predictions(None, [0, 0.5], [0, 0])

    assert result["validation_status"] == "PASSED"
    assert result["accuracy_metrics"]["mean_absolute_percentage_error"] is None
    assert result["accuracy_metrics"]["mean_absolute_error"] == 0.25


# ── Gráfico de ajuste de distribuciones: ni muestra inventada ni veredicto falso ──
#
# El gráfico quedó desincronizado del cierre de `distribution_fit_v2`. Aquel cierre
# dejó `p_value=None` y `passes_test=None` a propósito — un p-value post-ajuste no
# es válido y no se publica. El gráfico seguía asumiendo que existían: fabricaba la
# muestra con una onda seno rotulada "Datos Observados", ordenaba los candidatos por
# p-value y pintaba "✗ Falla" para lo que en realidad es "no disponible".

def _diagnostic_without_p_values():
    """Contrato real que hoy devuelve `_perform_ks_test_demand`."""
    return {
        'test_type': 'distribution_fit_diagnostic',
        'sample_size': 40,
        'distributions_tested': {
            'normal': {
                'statistic': 0.0812, 'p_value': None, 'params': (100.0, 12.0),
                'passes_test': None, 'test_name': 'kolmogorov_smirnov_distance',
                'p_value_unavailable_reason': 'ESTIMATED_PARAMETERS',
            },
            'lognormal': {
                'statistic': 0.1310, 'p_value': None, 'params': (0.1, 0.0, 100.0),
                'passes_test': None, 'test_name': 'kolmogorov_smirnov_distance',
                'p_value_unavailable_reason': 'ESTIMATED_PARAMETERS',
            },
        },
        'best_fit_distribution': 'normal',
        'best_p_value': None,
        'overall_passes': None,
        'ranking_method': 'aic',
    }


def test_distribution_chart_does_not_invent_a_sample_when_there_is_none():
    """Sin muestra real no hay gráfico. Antes dibujaba una onda seno."""
    view = SimulateResultView()
    diagnostic = _diagnostic_without_p_values()

    assert view._create_distribution_comparison_chart(diagnostic) is None
    assert view._create_distribution_comparison_chart({**diagnostic, 'sample': []}) is None


def test_distribution_chart_renders_with_the_real_sample_and_no_p_values():
    """Con muestra real debe producir imagen sin reventar por los p-value None."""
    rng = np.random.default_rng(20260817)
    diagnostic = {**_diagnostic_without_p_values(),
                  'sample': rng.normal(100.0, 12.0, 200).tolist()}

    chart = SimulateResultView()._create_distribution_comparison_chart(diagnostic)

    assert isinstance(chart, str) and len(chart) > 0


def test_distribution_chart_source_never_hardcodes_a_synthetic_series():
    """Guardia de regresión sobre el archivo: la onda seno no puede volver."""
    source = Path(__file__).resolve().parents[1] / 'views' / 'simulate_result_view.py'
    text = source.read_text(encoding='utf-8')

    assert 'np.sin(np.linspace' not in text
    assert 'Distribuciones Ajustadas vs Datos Observados' not in text


def test_distribution_chart_does_not_call_an_unavailable_verdict_a_failure():
    """`passes_test=None` es 'no disponible', no 'falla'."""
    view = SimulateResultView()

    assert view._fit_verdict_label(None) == 'No disponible'
    assert view._fit_verdict_label(True) != view._fit_verdict_label(None)
    assert view._fit_verdict_label(False) != view._fit_verdict_label(None)


# ── Métricas de comparación: un fallo no es un acierto ──────────────────────
#
# `_calculate_comparison_metrics` alimenta las estadísticas de demanda que ve el
# usuario. Convertía cada caso imposible en un número con significado propio:
# RMSE/MAE 0.0 (predicción perfecta), correlación 0, R² 0 (el modelo no explica
# nada) y MAPE 100. Ninguno de esos se midió; todos se inventaron. Lo no medible
# es `None`, igual que ya hace `StatisticalService`.

def test_error_metrics_are_unavailable_instead_of_perfect_on_bad_input():
    view = SimulateResultView()

    for bad in ([], [np.nan, np.nan]):
        assert view._calculate_rmse(np.asarray(bad, dtype=float),
                                    np.asarray(bad, dtype=float)) is None
        assert view._calculate_mae(np.asarray(bad, dtype=float),
                                   np.asarray(bad, dtype=float)) is None
        assert view._calculate_mape(np.asarray(bad, dtype=float),
                                    np.asarray(bad, dtype=float)) is None


def test_error_metrics_still_measure_when_the_data_is_usable():
    view = SimulateResultView()
    actual = np.asarray([10.0, 20.0, 30.0])
    predicted = np.asarray([11.0, 18.0, 33.0])

    assert view._calculate_rmse(actual, predicted) == pytest.approx(np.sqrt(14 / 3))
    assert view._calculate_mae(actual, predicted) == pytest.approx(2.0)
    assert view._calculate_mape(actual, predicted) == pytest.approx(
        np.mean([10.0, 10.0, 10.0])
    )


def test_comparison_metrics_do_not_fabricate_zero_correlation_or_r_squared():
    """Una sola observación no permite correlación ni R². Cero sería una afirmación."""
    comparison = SimulateResultView()._calculate_comparison_metrics([100.0], [110.0])

    assert comparison['correlation'] is None
    assert comparison['r_squared'] is None


def test_comparison_metrics_do_not_fabricate_zero_when_the_baseline_is_zero():
    """Con media histórica 0 no hay porcentaje ni coeficiente de variación."""
    comparison = SimulateResultView()._calculate_comparison_metrics(
        [0.0, 0.0, 0.0], [5.0, 6.0, 7.0]
    )

    assert comparison['mean_diff_pct'] is None
    assert comparison['cv_diff'] is None
    # La diferencia de medias sí es medible y debe seguir estando.
    assert comparison['mean_diff'] == pytest.approx(6.0)


def test_comparison_metrics_measure_a_healthy_series():
    comparison = SimulateResultView()._calculate_comparison_metrics(
        [10.0, 20.0, 30.0, 40.0], [11.0, 21.0, 29.0, 41.0]
    )

    assert comparison['correlation'] == pytest.approx(1.0, abs=0.01)
    assert comparison['r_squared'] is not None
    assert comparison['rmse'] is not None


def test_the_dead_accuracy_helpers_that_reported_100_percent_are_gone():
    """`_calculate_deviation` devolvía 0.0 en except y el llamador lo leía como
    `100 - 0 = 100% de precisión`, publicándolo además como 'fortaleza'. El
    bloque completo no lo llamaba nadie; se elimina en vez de dejar la trampa."""
    for dead in ('_calculate_deviation', '_determine_status',
                 '_calculate_model_performance', '_generate_daily_comparisons'):
        assert not hasattr(SimulateResultView, dead), dead


def test_no_runtime_chart_asset_fabricates_its_own_series():
    """U1 — ningún gráfico del runtime puede inventarse los datos que grafica.

    `statistical-analysis.js` construía la distribución de frecuencias, la nube de
    correlación "Histórico vs Simulado" y los residuos con `Math.random()`, y
    `validation-charts.js` generaba así las series rotuladas "Valor Real" y
    "Valor Simulado". Eran afirmaciones estadísticas fabricadas: un residuo o una
    correlación inventados son indistinguibles de los medidos para quien mira.

    La guardia anterior sólo cubría `pValue = … Math.random`, así que estos
    quedaban fuera.
    """
    project_root = Path(__file__).resolve().parents[2]
    sources = [
        project_root / "static/js/simulate/tabs/statistical-analysis.js",
        project_root / "static/js/components/validation-charts.js",
    ]

    def strip_comments(text: str) -> str:
        """Los comentarios explican el defecto ya cerrado; se mira el código."""
        without_block = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
        return "\n".join(
            line for line in without_block.split("\n")
            if not line.lstrip().startswith("//")
        )

    for path in sources:
        code = strip_comments(path.read_text(encoding="utf-8"))
        assert "Math.random" not in code, path.name


# ── F2 — la "confianza" de cada método de comparación no puede ser un literal ──

def _comparison_methods(values, real_value=100.0):
    return SimulationValidationService()._calculate_multiple_comparisons(
        list(values), real_value, 'IT'
    )


def test_method_confidence_is_derived_from_the_sample_not_hardcoded():
    """`trimmed_mean` declaraba 0.9, `weighted` 0.8 y `final_period` 0.85/0.6.

    Eran literales: no salían de los datos, y sin embargo pesaban un 20% en la
    elección del método "mejor". Dos muestras con dispersión muy distinta
    producían exactamente la misma confianza.
    """
    tight = _comparison_methods([100.0, 100.5, 99.5, 100.2, 99.8, 100.1])
    loose = _comparison_methods([100.0, 300.0, 10.0, 250.0, 5.0, 180.0])

    for method in ('trimmed_mean', 'weighted', 'final_period'):
        assert method in tight and method in loose, method
        assert tight[method]['confidence'] is not None
        assert loose[method]['confidence'] is not None
        # Una muestra concentrada no puede tener la misma confianza que una dispersa.
        assert tight[method]['confidence'] > loose[method]['confidence'], method


def test_method_confidence_is_bounded_and_unavailable_when_undefined():
    methods = _comparison_methods([100.0, 101.0, 99.0, 100.5, 99.5])
    measured = [m['confidence'] for m in methods.values() if m['confidence'] is not None]

    assert measured, 'ningún método logró medir la dispersión'
    assert all(0.0 <= value <= 1.0 for value in measured)
    # `final_period` toma un solo valor con esta muestra: una observación no tiene
    # dispersión, así que su confianza debe faltar en vez de inventarse.
    assert methods['final_period']['confidence'] is None

    # Con estimador cero la dispersión relativa no está definida.
    zeroed = _comparison_methods([0.0, 0.0, 0.0, 0.0, 0.0], real_value=10.0)
    assert all(method['confidence'] is None for method in zeroed.values())


def test_unavailable_confidence_does_not_become_a_default_score():
    """`.get('confidence', 0.5)` inventaba media confianza para lo no medido."""
    service = SimulationValidationService()
    methods = {
        'average': {'method': 'a', 'status': 'PRECISE', 'error_pct': 1.0,
                    'confidence': None, 'simulated_value': 100.0},
        'median': {'method': 'm', 'status': 'PRECISE', 'error_pct': 1.0,
                   'confidence': 0.9, 'simulated_value': 100.0},
    }
    best = service._select_best_comparison_method(methods, 'IT')

    # El que sí tiene confianza medida no puede perder contra uno sin medir.
    assert best['method'] == 'median'


def test_the_error_fallback_does_not_invent_a_value_or_a_perfect_error():
    """El `except` devolvía `simulated_value: 0` y `error_pct: 100.0` medidos."""
    fallback = SimulationValidationService()._calculate_multiple_comparisons(
        [], 100.0, 'IT'
    )

    assert fallback['average']['simulated_value'] is None
    assert fallback['average']['error_pct'] is None
    assert fallback['average']['confidence'] is None
    assert fallback['average']['status'] == 'UNAVAILABLE'


def test_forecast_accuracy_metrics_do_not_score_a_zero_actual_as_a_perfect_hit():
    """`np.where(actual != 0, err/actual*100, 0)` metía un 0% de error por cada
    observación nula: el MAPE bajaba justamente donde no se podía medir."""
    service = StatisticalService()
    actual = np.asarray([100.0, 0.0, 200.0])
    predicted = np.asarray([110.0, 50.0, 180.0])

    metrics = service.perform_forecast_accuracy_metrics(actual, predicted)

    # Sólo las dos observaciones no nulas entran en el MAPE: (10% + 10%) / 2.
    assert metrics['mape'] == pytest.approx(10.0)
    assert metrics['mape_excluded_observations'] == 1
    # MAE/RMSE/bias sí usan todas las observaciones: no dependen de dividir.
    assert metrics['mae'] == pytest.approx(np.mean([10.0, 50.0, 20.0]))


def test_forecast_accuracy_metrics_report_unavailable_when_every_actual_is_zero():
    metrics = StatisticalService().perform_forecast_accuracy_metrics(
        np.asarray([0.0, 0.0]), np.asarray([1.0, 2.0])
    )

    assert metrics['mape'] is None
    assert metrics['tracking_signal'] is not None


# ── Fuga temporal: el holdout no puede haber visto el futuro ────────────────

def _demand_service(values):
    return DemandModelService(list(values), confidence_level=0.95)


def test_holdout_mape_only_uses_information_available_at_the_origin():
    """La predicción evaluada debe salir del tramo de entrenamiento, no de la serie
    completa. Si el holdout viera el futuro, cambiar sólo el tramo de test movería
    la predicción — y el MAPE dejaría de ser una validación."""
    base = [100.0 + 2.0 * i for i in range(40)]
    n_test = max(1, len(base) // 5)
    train = base[:-n_test]

    # Predicción honesta: entrenar con el prefijo y proyectar n_test períodos.
    expected = _demand_service(train)._forecast_values(
        np.asarray(train, dtype=float), n_test, 'linear'
    )

    # El servicio completo, con la serie entera, debe evaluar contra esa misma
    # predicción: su MAPE tiene que coincidir con el calculado a mano.
    service = _demand_service(base)
    test = np.asarray(base[-n_test:], dtype=float)
    manual = float(np.mean(np.abs((test - np.asarray(expected)) / test)) * 100)

    assert service._calculate_mape('linear') == pytest.approx(round(manual, 2))


def test_method_selection_for_validation_ignores_the_test_window():
    """Elegir el método mirando toda la serie ya es fuga: la decisión usaría
    observaciones que en el origen histórico no existían."""
    # Prefijo perfectamente lineal (R² = 1.0) y ventana de test caótica que
    # hunde el R² de la serie completa a ~0.23.
    values = [100.0 + 5.0 * i for i in range(32)] + [
        10.0, 900.0, 12.0, 880.0, 15.0, 860.0, 18.0, 840.0]
    service = _demand_service(values)
    n_test = max(1, len(values) // 5)

    chosen_on_train = service._select_method(np.asarray(values[:-n_test], dtype=float))
    chosen_on_all = service._select_method(np.asarray(values, dtype=float))

    # La serie está construida para que ambas elecciones difieran; si no
    # difirieran el test no probaría nada.
    assert chosen_on_train != chosen_on_all

    expected = service._forecast_values(
        np.asarray(values[:-n_test], dtype=float), n_test, chosen_on_train
    )
    test = np.asarray(values[-n_test:], dtype=float)
    mask = test != 0
    manual = round(float(np.mean(np.abs((test[mask] - np.asarray(expected)[mask]) / test[mask])) * 100), 2)

    assert service._calculate_mape('auto') == pytest.approx(manual)
