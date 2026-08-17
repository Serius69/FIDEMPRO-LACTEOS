from decimal import Decimal

import pytest

from modeling.financial import calculate_financials, summarize_explicit_financials


def test_financial_snapshot_uses_decimal_and_expected_golden_values():
    result = calculate_financials(
        units_sold="3", unit_price="10.005", unit_variable_cost="2.005",
        fixed_cost="5.00", investment="20.00",
    )

    assert result.revenue == Decimal("30.02")
    assert result.variable_cost == Decimal("6.02")
    assert result.gross_profit == Decimal("24.00")
    assert result.operating_result == Decimal("19.00")
    assert result.cogs == Decimal("6.02")
    assert result.contribution_margin == Decimal("24.00")
    assert result.contribution_margin_pct == Decimal("79.9467")
    assert result.break_even_units == Decimal("0.6250")
    assert result.roi == Decimal("95.0000")
    assert result.cash_flow is None
    assert result.working_capital is None


def test_cash_and_working_capital_require_explicit_inputs():
    result = calculate_financials(
        units_sold=10, unit_price="10", unit_variable_cost="2", fixed_cost="20",
        cash_inflows="80", cash_outflows="35", opening_cash="100",
        current_assets="250", current_liabilities="90",
    )

    assert result.cash_flow == Decimal("45.00")
    assert result.ending_cash == Decimal("145.00")
    assert result.working_capital == Decimal("160.00")


def test_break_even_is_not_claimed_when_contribution_is_non_positive():
    result = calculate_financials(
        units_sold=10, unit_price=5, unit_variable_cost=5, fixed_cost=100,
    )

    assert result.break_even_units is None
    assert result.break_even_revenue is None


def test_negative_monetary_inputs_are_rejected():
    with pytest.raises(ValueError, match="fixed_cost"):
        calculate_financials(units_sold=1, unit_price=2, unit_variable_cost=1, fixed_cost=-1)


def test_explicit_financial_summary_requires_cost_classification():
    incomplete = summarize_explicit_financials(revenue="100.005", cost_lines=[{"id": "unknown", "amount": "20"}])
    complete = summarize_explicit_financials(revenue="100.005", cost_lines=[
        {"id": "materials", "amount": "20", "classification": "VARIABLE"},
        {"id": "rent", "amount": "10", "classification": "FIXED"},
    ])

    assert incomplete["status"] == "incomplete"
    assert incomplete["missing"] == ["costs[unknown].classification"]
    assert complete["gross_profit"] == "80.01"
    assert complete["operating_result"] == "70.01"
    assert complete["cogs"] == "20.00"
    assert complete["contribution_margin"] == "80.01"


def test_cogs_and_variable_costs_remain_distinct_and_explicit():
    summary = summarize_explicit_financials(revenue="100", cost_lines=[
        {"id": "materials", "amount": "40", "classification": "COGS"},
        {"id": "commission", "amount": "10", "classification": "VARIABLE"},
        {"id": "rent", "amount": "20", "classification": "FIXED"},
    ])

    assert summary["gross_profit"] == "60.00"
    assert summary["contribution_margin"] == "50.00"
    assert summary["operating_result"] == "30.00"
