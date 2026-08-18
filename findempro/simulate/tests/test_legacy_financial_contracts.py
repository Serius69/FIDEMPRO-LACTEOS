"""Regression tests for inherited simulation finance semantics.

These tests protect the boundary that derived financial metrics must be based
on explicit inputs, not on operating-cost or placeholder capital proxies.
"""

from simulate.utils.simulation_math_utils import SimulationMathEngine
from simulate.services.validation_service import SimulationValidationService
from simulate.utils.simulation_financial_utils import SimulationFinancialAnalyzer
from types import SimpleNamespace


def test_legacy_roi_is_absent_without_explicit_investment():
    engine = SimulationMathEngine()

    result = engine.equation_solver.solve_with_iterations(
        {'GT': 500.0, 'TG': 100.0}, {'RI'}
    )

    assert 'RI' not in result


def test_legacy_roi_uses_explicit_investment_only():
    engine = SimulationMathEngine()

    result = engine.equation_solver.solve_with_iterations(
        {'GT': 500.0, 'INV': 200.0}, {'RI'}
    )

    assert result['RI'] == 2.5


def test_legacy_equation_solver_does_not_fill_missing_dependencies_with_defaults():
    engine = SimulationMathEngine()

    result = engine.equation_solver.solve_with_iterations({'IT': 1000.0}, {'TG', 'GT'})

    assert 'TG' not in result
    assert 'GT' not in result


def test_capital_productivity_is_absent_without_investment():
    engine = SimulationMathEngine()

    assert 'CAPITAL_PRODUCTIVITY' not in engine._calculate_additional_metrics(
        {'GT': 500.0, 'IT': 1000.0, 'TG': 500.0}
    )


def test_basic_fallback_does_not_invent_financial_inputs():
    engine = SimulationMathEngine()

    variables = engine.calculate_basic_variables(100.0, 1)

    assert variables['_financial_status'] == 'incomplete'
    assert 'IT' not in variables
    assert 'MB' not in variables


def test_basic_calculation_accepts_only_explicit_financial_inputs():
    engine = SimulationMathEngine()

    variables = engine.calculate_basic_variables(
        100.0, 1, financial_inputs={"units_sold": 20, "unit_price": 10, "variable_cost": 4, "fixed_cost": 50}
    )

    assert variables["IT"] == 200
    assert variables["TG"] == 130
    assert variables["GT"] == 70


def test_legacy_validation_does_not_infer_total_cost_from_operating_cost():
    service = SimulationValidationService.__new__(SimulationValidationService)

    result = service._calculate_derived_real_values_improved({'IT': 1000.0, 'GO': 500.0})

    assert 'TG' not in result
    assert 'GT' not in result


def test_legacy_default_hook_preserves_missing_financial_inputs():
    service = SimulationValidationService.__new__(SimulationValidationService)

    result = service._add_reasonable_defaults({'QPL': 100.0, 'IT': 1000.0}, simulation=None)

    assert result == {'QPL': 100.0, 'IT': 1000.0}


def test_legacy_financial_report_does_not_label_missing_inputs_as_roi_or_ebitda():
    analyzer = SimulationFinancialAnalyzer()
    result = SimpleNamespace(
        variables={'IT': 100.0, 'GT': 20.0, 'GO': 10.0, 'TG': 30.0, 'TPV': 5.0},
        date='2026-01-01',
        demand_mean=5.0,
    )

    daily = analyzer._extract_daily_financials([result])
    profitability = analyzer._analyze_profitability(daily)
    kpis = analyzer._calculate_financial_kpis(daily)

    assert daily[0]['roi'] is None
    assert daily[0]['ebitda'] is None
    assert profitability['roi_average'] is None
    assert profitability['ebitda_total'] is None
    assert kpis['roi'] is None
