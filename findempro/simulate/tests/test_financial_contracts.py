import numpy as np

from simulate.core.decision_engine import _compute_risk_metrics


def test_confidence_level_is_preserved_and_changes_dynamic_var():
    samples = np.arange(-100.0, 101.0)
    lower = _compute_risk_metrics(samples, confidence_level=0.90)
    higher = _compute_risk_metrics(samples, confidence_level=0.99)

    assert lower.confidence_level == 0.90
    assert higher.confidence_level == 0.99
    assert higher.var_at_confidence <= lower.var_at_confidence
    assert higher.cvar_at_confidence <= lower.cvar_at_confidence
    assert lower.var_semantics == "lower_profit_quantile"
    assert lower.cvar_semantics == "lower_tail_mean_profit"


def test_return_ratios_are_unavailable_for_monetary_profit_samples():
    metrics = _compute_risk_metrics(np.array([-10.0, 5.0, 20.0]))

    assert metrics.ratio_basis == "not_applicable_monetary_profit"
    assert metrics.sharpe_ratio is None
    assert metrics.sortino_ratio is None
    assert metrics.downside_std is None


def test_shape_moments_are_explicitly_unavailable_for_constant_profit():
    metrics = _compute_risk_metrics(np.array([1250.0] * 20))

    assert metrics.skewness is None
    assert metrics.kurtosis is None
    assert metrics.shape_statistics_status == "DEGENERATE_DISTRIBUTION"


def test_nearly_constant_large_profit_does_not_emit_unstable_shape():
    metrics = _compute_risk_metrics(np.array([1e12, 1e12 + 0.001, 1e12 - 0.001]))

    assert metrics.skewness is None
    assert metrics.kurtosis is None
    assert metrics.shape_statistics_status == "DEGENERATE_DISTRIBUTION"
