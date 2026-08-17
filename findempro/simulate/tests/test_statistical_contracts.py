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
