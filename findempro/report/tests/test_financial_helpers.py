from decimal import Decimal
from types import SimpleNamespace

import pytest

from report.views import (
    calculate_flujo_caja,
    calculate_payback_period,
    calculate_punto_equilibrio,
    calculate_roi,
    calculate_tir,
    calculate_utilidad_neta,
    calculate_van,
    generate_sensitivity_analysis,
)
from report.tasks import _extract_persisted_profit_summary


def test_simulation_report_uses_only_valid_persisted_profit_summaries():
    rows = [
        SimpleNamespace(variables={'profit_mean': 10, 'profit_p5': 5, 'profit_p95': 15}),
        SimpleNamespace(variables={'profit_mean': -2, 'profit_p5': -8, 'profit_p95': 4}),
        SimpleNamespace(variables={'profit_mean': 20, 'profit_p5': 30, 'profit_p95': 40}),
        SimpleNamespace(variables={'profit_mean': 'nan', 'profit_p5': 0, 'profit_p95': 1}),
        SimpleNamespace(variables={}),
    ]

    summary = _extract_persisted_profit_summary(rows)

    assert [period['mean'] for period in summary['periods']] == [10.0, -2.0]
    assert summary['excluded_periods'] == 3
    assert summary['mean_of_period_means'] == 4.0
    assert summary['std_of_period_means'] == 6.0
    assert summary['negative_mean_periods'] == 1
    assert summary['risk_metrics_available'] is False
    assert summary['risk_unavailable_reason'] == 'ORIGINAL_MONTE_CARLO_SAMPLES_NOT_PERSISTED'
    assert summary['method_version'] == 'simulation_report_summary_v2'


def test_simulation_report_task_does_not_reconstruct_random_samples():
    source = __import__('inspect').getsource(__import__('report.tasks', fromlist=['tasks']))
    assert 'np.random' not in source
    assert 'rng.normal' not in source


def test_legacy_report_financial_helpers_use_decimal_safe_golden_values():
    params = {
        "demanda_inicial": "3",
        "precio_unitario": "10.005",
        "costo_unitario": "2.005",
        "gastos_fijos": "5.00",
        "inversion_inicial": "20.00",
        "horizonte": 1,
    }

    assert calculate_utilidad_neta(params) == float(Decimal("24.00"))
    assert calculate_flujo_caja(params) == float(Decimal("19.00"))
    assert calculate_roi(params) == -5.0
    assert calculate_punto_equilibrio(params) == 0.625
    assert calculate_van(params, tasa_descuento=0) == -1.0


def test_legacy_report_rejects_negative_monetary_inputs():
    with pytest.raises(ValueError, match="gastos_fijos"):
        calculate_flujo_caja({"demanda_inicial": 1, "precio_unitario": 2, "costo_unitario": 1, "gastos_fijos": -1})


def test_legacy_report_does_not_invent_invested_capital():
    params = {
        "demanda_inicial": 3,
        "precio_unitario": 10,
        "costo_unitario": 2,
        "gastos_fijos": 5,
    }

    with pytest.raises(ValueError, match="inversion_inicial es obligatorio"):
        calculate_roi(params)


def test_report_investment_metrics_reconcile_for_break_even_annuity():
    params = {
        "demanda_inicial": 10,
        "precio_unitario": 3,
        "costo_unitario": 1,
        "gastos_fijos": 10,
        "inversion_inicial": 100,
        "horizonte": 10,
    }

    assert calculate_flujo_caja(params) == 10.0
    assert calculate_roi(params) == 0.0
    assert calculate_payback_period(params) == 10.0
    assert calculate_van(params, tasa_descuento=0) == 0.0
    assert calculate_tir(params) == pytest.approx(0.0, abs=0.0001)


def test_report_irr_solves_npv_root_and_is_annual_effective():
    params = {
        "demanda_inicial": 11,
        "precio_unitario": 12,
        "costo_unitario": 2,
        "gastos_fijos": 0,
        "inversion_inicial": 100,
        "horizonte": 1,
    }

    expected_annual_effective = ((1.10 ** 12) - 1) * 100
    assert calculate_roi(params) == 10.0
    assert calculate_tir(params) == pytest.approx(expected_annual_effective, abs=0.0001)


def test_report_undefined_investment_metrics_remain_unavailable():
    zero_investment = {
        "demanda_inicial": 1,
        "precio_unitario": 2,
        "costo_unitario": 1,
        "gastos_fijos": 0,
        "inversion_inicial": 0,
        "horizonte": 12,
    }
    non_positive_cash = {**zero_investment, "inversion_inicial": 10, "gastos_fijos": 2}

    assert calculate_roi(zero_investment) is None
    assert calculate_payback_period(zero_investment) == 0.0
    assert calculate_tir(zero_investment) is None
    assert calculate_payback_period(non_positive_cash) is None
    assert calculate_tir(non_positive_cash) is None
    sensitivity = generate_sensitivity_analysis(zero_investment)
    assert all(
        row["roi"] is None and row["roi_change"] is None
        for rows in sensitivity.values()
        for row in rows
    )


@pytest.mark.parametrize("horizon", [None, 0, 1.5, 121, True])
def test_report_financial_metrics_reject_invalid_horizon(horizon):
    params = {
        "demanda_inicial": 1,
        "precio_unitario": 2,
        "costo_unitario": 1,
        "gastos_fijos": 0,
        "inversion_inicial": 10,
        "horizonte": horizon,
    }

    with pytest.raises(ValueError, match="horizonte"):
        calculate_roi(params)


def test_report_npv_requires_explicit_discount_rate():
    params = {
        "demanda_inicial": 1,
        "precio_unitario": 2,
        "costo_unitario": 1,
        "gastos_fijos": 0,
        "inversion_inicial": 10,
        "horizonte": 12,
    }

    with pytest.raises(ValueError, match="tasa_descuento_anual es obligatoria"):
        calculate_van(params)
    with pytest.raises(ValueError, match="finita y no negativa"):
        calculate_van(params, tasa_descuento=float("nan"))
