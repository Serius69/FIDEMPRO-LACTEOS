from types import SimpleNamespace

from simulate.utils.variable_mapper import VariableMapper


def _seeded_mapper_values():
    from django.contrib.auth.models import User
    from business.data.bolivia_industries import get_spec
    from business.services.seed_service import IndustrySeeder
    from questionary.models import QuestionaryResult

    user = User.objects.create_user(username='mapper-sector-test', password='x')
    spec = get_spec(7)
    business = IndustrySeeder(user).seed_business(spec)
    result = QuestionaryResult.objects.filter(
        fk_questionary__fk_product__fk_business=business
    ).first()
    return spec.products[0], result, VariableMapper().extract_all_variables(result)


def test_runtime_mapper_does_not_load_global_test_fixture_values():
    mapper = VariableMapper()

    assert mapper._extract_from_variable_system_fixed(None) == {}
    assert mapper.enhanced_defaults == {}


def test_missing_business_values_remain_missing_and_explicit_zero_is_preserved():
    mapper = VariableMapper()

    result = mapper._apply_enhanced_defaults({'PVP': 0, 'ED': 1})

    assert result == {'PVP': 0, 'ED': 1}
    assert 'CUIP' not in result
    assert 'CPROD' not in result
    assert 'DH' not in result


def test_context_hook_does_not_invent_capacity_inventory_cost_or_price():
    mapper = VariableMapper()
    explicit = {'DE': 100, 'CPROD': 80, 'NEPP': 2, 'PC': 15}

    result = mapper._apply_contextual_adjustments(explicit)

    assert result == explicit
    assert 'PVP' not in result
    assert 'CFD' not in result
    assert 'IPF' not in result


def test_derived_metrics_require_complete_inputs():
    mapper = VariableMapper()

    assert mapper._calculate_derived_variables({'ES': 0.8, 'PE': 0.9}) == {}

    result = mapper._calculate_derived_variables(
        {'ES': 0.8, 'PE': 0.9, 'QC': 0.95, 'NEPP': 2, 'MLP': 480, 'TPE': 30}
    )

    assert result['EOG'] == 0.8 * 0.9 * 0.95
    assert result['CPROD'] == 32


def test_invalid_values_are_dropped_instead_of_replaced_by_sector_examples():
    mapper = VariableMapper()

    result = mapper._validate_and_clean_variables({'PVP': 'not-a-price', 'ED': 1})

    assert result == {'ED': 1.0}


def test_extraction_report_measures_explicit_critical_input_coverage():
    report = VariableMapper().generate_extraction_report({'PVP': 10, 'CUIP': 4})

    assert report['variables_with_defaults'] == []
    assert report['coverage_analysis']['coverage_percentage'] == 40
    assert report['coverage_analysis']['missing_critical_vars'] == ['NEPP', 'CPROD', 'CPD']


def test_seeded_sector_uses_its_questionnaire_values_not_global_dairy_examples(db):
    baseline, result, values = _seeded_mapper_values()

    assert values['PVP'] == baseline.price
    assert values['CUIP'] == baseline.unit_cost
    assert values['NEPP'] == baseline.employees
    assert values['CPROD'] == round(baseline.daily_demand * baseline.capacity_factor, 1)
    envelope = result.fk_questionary.fk_product.fk_business.company_profile.custom_kpis[
        'legacy_product_parameters'
    ][str(result.fk_questionary.fk_product_id)]
    assert envelope['provenance'] == 'SYNTHETIC_TEMPLATE'
    assert envelope['model_kind'] == 'SERVICE'
    assert envelope['values']['QPL'] == round(baseline.daily_demand, 1)
    assert envelope['values']['PI'] == 0.0
    assert envelope['equations'] == [
        'TPV = min(DE, CPROD)',
        'IT = TPV * PVP',
        'TG = TPV * CUIP + CFD + SE / 30 + GMM / 30 + TPV * CUTRANS',
        'GT = IT - TG',
    ]


def test_seeded_sector_declares_external_dependencies_for_financial_outputs(db):
    from simulate.core.discrete_engine import _extract_rhs_dependencies, _get_lhs

    _baseline, questionary_result, values = _seeded_mapper_values()
    mapper = VariableMapper()
    equations = [
        SimpleNamespace(expression=expression)
        for expression in mapper.get_template_equation_expressions(questionary_result)
    ]
    dependencies_by_lhs = {
        _get_lhs(equation.expression): _extract_rhs_dependencies(equation.expression)
        for equation in equations
        if _get_lhs(equation.expression)
    }
    runtime_symbols = {'DE', 'DPH', 'DSD', 'CVD', 'DIA', 'NMD'}
    required_external = set()
    pending = ['IT', 'GT']
    visited = set()
    while pending:
        symbol = pending.pop()
        if symbol in visited:
            continue
        visited.add(symbol)
        if symbol in values or symbol in runtime_symbols:
            continue
        if symbol not in dependencies_by_lhs:
            required_external.add(symbol)
            continue
        for dependency in dependencies_by_lhs[symbol]:
            if dependency == symbol:
                required_external.add(dependency)
            else:
                pending.append(dependency)

    missing = required_external - runtime_symbols - set(values)
    assert not missing, ','.join(sorted(missing))


def test_seeded_service_financial_equations_reconcile_from_explicit_inputs(db):
    from simulate.core.discrete_engine import CompanyConfig, DiscreteEventEngine, OperationScenario

    baseline, questionary_result, values = _seeded_mapper_values()
    mapper = VariableMapper()
    equations = [
        SimpleNamespace(expression=expression, fk_area=None)
        for expression in mapper.get_template_equation_expressions(questionary_result)
    ]
    exogenous = {
        key: value for key, value in values.items()
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    }
    result = DiscreteEventEngine(CompanyConfig(equations=equations)).run_period(
        OperationScenario(demand_value=baseline.daily_demand), exogenous
    )

    assert result.revenue > 0
    financial_trace = {
        key: result.variables.get(key)
        for key in ('IT', 'TG', 'GT', 'GO', 'GG', 'CTAI', 'QPL', 'TPV', 'CTTL', 'CA', 'CTM', 'SE')
    }
    assert result.profit > 0, financial_trace
    assert result.profit == result.revenue - result.costs
