import pytest
from django.test import override_settings

from modeling.safe_expression import ExpressionError, evaluate_expression, validate_expression
from modeling.schema import empty_model_spec, model_hash, validate_model_spec


def test_empty_spec_is_safe_but_reports_missing_readiness_dimensions():
    result = validate_model_spec(empty_model_spec(name="Tienda demo"))

    assert result["valid"] is True
    assert result["readiness"]["score"] == 0
    assert "demand" in result["readiness"]["missing"]
    assert result["readiness"]["actions"]["demand"]


def test_readiness_recognizes_service_and_explicit_data_dimensions():
    spec = empty_model_spec(name="Ready service")
    spec["variables"] = [{"id": "demand", "value": 5, "role": "demand"}]
    spec["resources"] = [{"id": "staff", "capacity": 1}]
    spec["services"] = [{"id": "consulting", "tasks": [{"id": "task", "duration": 1, "role_id": "staff"}]}]
    spec["revenues"] = [{"id": "sales", "value": 10, "unit": "Bs"}]
    spec["costs"] = [{"id": "cost", "value": 2, "unit": "Bs"}]

    readiness = validate_model_spec(spec)["readiness"]

    assert readiness["dimensions"]["demand"] is True
    assert readiness["dimensions"]["process"] is True
    assert readiness["dimensions"]["data"] is True
    assert readiness["dimensions"]["finance"] is True


def test_costs_and_revenues_have_one_canonical_list_shape():
    spec = empty_model_spec(name="Shape")
    assert spec["costs"] == []
    assert spec["revenues"] == []
    spec["costs"] = {"value": 2}
    result = validate_model_spec(spec)
    assert any(error["path"] == "costs" and error["code"] == "wrong_type" for error in result["errors"])


def test_model_hash_is_deterministic_for_key_order():
    assert model_hash({"b": 2, "a": 1}) == model_hash({"a": 1, "b": 2})


@override_settings(MODELING_MAX_MODEL_NODES=2, MODELING_MAX_MODEL_EDGES=20)
def test_schema_rejects_models_above_configured_node_limit():
    spec = empty_model_spec(name="Too many nodes")
    spec["variables"] = [{"id": f"variable-{index}", "value": index} for index in range(3)]

    result = validate_model_spec(spec)

    assert result["complexity"] == {"nodes": 3, "edges": 0, "max_nodes": 2, "max_edges": 20}
    assert any(error["code"] == "model_node_limit" for error in result["errors"])


@override_settings(MODELING_MAX_MODEL_NODES=20, MODELING_MAX_MODEL_EDGES=1)
def test_schema_rejects_models_above_configured_edge_limit():
    spec = empty_model_spec(name="Too many edges")
    spec["stocks"] = [{"id": "inventory", "initial": 10, "unit": "unit"}]
    spec["flows"] = [{"id": "sales", "source_id": "inventory", "target_id": "inventory", "value": 1, "unit": "unit"}]

    result = validate_model_spec(spec)

    assert result["complexity"] == {"nodes": 2, "edges": 2, "max_nodes": 20, "max_edges": 1}
    assert any(error["code"] == "model_edge_limit" for error in result["errors"])


def test_safe_expression_allows_math_and_rejects_python_execution():
    assert evaluate_expression("price * quantity - discount", {"price": 10, "quantity": 3, "discount": 2}) == 28
    assert validate_expression("max(price, 0)", allowed_names={"price"}) == {"price"}
    with pytest.raises(ExpressionError):
        validate_expression("__import__('os').system('whoami')", allowed_names=set())


def test_safe_expression_rejects_unknown_names_and_non_finite_results():
    with pytest.raises(ExpressionError, match="no definidas"):
        evaluate_expression("price * elasticity", {"price": 4})
    with pytest.raises(ExpressionError, match="División por cero"):
        evaluate_expression("price / 0", {"price": 4})


def test_safe_expression_evaluates_registered_numeric_constants():
    assert evaluate_expression("pi * 2", {}) == pytest.approx(2 * 3.141592653589793)


def test_safe_expression_function_pow_cannot_bypass_exponent_limit():
    with pytest.raises(ExpressionError, match="Exponente fuera de rango"):
        evaluate_expression("pow(2, 21)", {})
    with pytest.raises(ExpressionError, match="límites numéricos"):
        evaluate_expression("log(-1)", {})


@override_settings(MODELING_MAX_EXPRESSION_LENGTH=8)
def test_safe_expression_rejects_configured_length_limit():
    with pytest.raises(ExpressionError, match="8 caracteres"):
        validate_expression("1 + 2 + 3", allowed_names=set())


@override_settings(MODELING_MAX_EXPRESSION_NODES=6)
def test_safe_expression_rejects_configured_ast_node_limit():
    with pytest.raises(ExpressionError, match="6 nodos"):
        validate_expression("price + cost", allowed_names={"price", "cost"})


@override_settings(MODELING_MAX_EXPRESSION_DEPTH=3)
def test_safe_expression_rejects_configured_ast_depth_limit():
    with pytest.raises(ExpressionError, match="3 niveles"):
        validate_expression("-(-1)", allowed_names=set())


def test_schema_rejects_unresolved_bom_reference_and_invalid_distribution():
    spec = empty_model_spec()
    spec["products"] = [{"id": "bread", "name": "Pan"}]
    spec["boms"] = [{"id": "bread-bom", "product_id": "bread", "items": [{"component_id": "flour", "quantity": 1}]}]
    spec["distributions"] = [{"id": "demand", "distribution": "made_up"}]

    result = validate_model_spec(spec)

    assert result["valid"] is False
    assert {error["code"] for error in result["errors"]} >= {"unresolved_reference", "unsupported_distribution"}


def test_schema_rejects_invalid_distribution_parameters_and_unknown_sections():
    spec = empty_model_spec()
    spec["private_notes"] = "no DSL data"
    spec["distributions"] = [
        {"id": "demand", "distribution": "normal", "params": {"std": -1}},
        {"id": "arrivals", "distribution": "negative_binomial", "params": {"n": 0, "p": 1.2}},
        {"id": "price", "distribution": "uniform", "params": {"min": 10, "max": 2}},
    ]

    result = validate_model_spec(spec)

    assert result["valid"] is False
    assert {error["code"] for error in result["errors"]} >= {"unknown_section", "invalid_distribution_params"}


def test_schema_rejects_non_finite_operational_values_but_allows_explicit_signed_cash():
    spec = empty_model_spec()
    spec["resources"] = [{"id": "worker", "capacity": "NaN", "hours_per_period": -2}]
    spec["processes"] = [{"id": "repair", "steps": [{"id": "step", "cycle_time": "fast"}]}]
    spec["stocks"] = [{"id": "cash", "initial": -100, "allow_negative": True}]

    result = validate_model_spec(spec)

    assert result["valid"] is False
    assert any(error["code"] == "invalid_number" for error in result["errors"])
    assert result["errors"]


def test_schema_requires_boolean_opt_in_for_negative_stocks():
    spec = empty_model_spec()
    spec["stocks"] = [
        {"id": "inventory", "initial": -1},
        {"id": "cash", "initial": 0, "allow_negative": "yes"},
    ]

    result = validate_model_spec(spec)

    assert {error["code"] for error in result["errors"]} >= {"negative_stock", "invalid_boolean"}


def test_schema_validates_flow_roles_and_financial_formula_symbols():
    spec = empty_model_spec()
    spec["stocks"] = [{"id": "inventory", "initial": 1, "unit": "unit"}]
    spec["flows"] = [{"id": "sales", "source_id": "inventory", "value": 1, "unit": "unit", "role": "wishful"}]
    spec["revenues"] = [{"id": "revenue", "expression": "unknown_sales * 10", "unit": "Bs"}]

    result = validate_model_spec(spec)

    assert {error["code"] for error in result["errors"]} >= {"invalid_flow_role", "unsafe_expression"}


def test_schema_rejects_ambiguous_and_reserved_runtime_ids():
    spec = empty_model_spec()
    spec["variables"] = [{"id": "demand", "value": 1}, {"id": "profit", "value": 2}]
    spec["flows"] = [{"id": "demand", "value": 1}]
    # Cost/revenue line labels are not executable symbols and may retain
    # familiar business-facing names.
    spec["costs"] = [{"id": "cost", "value": 0, "classification": "FIXED"}]
    spec["revenues"] = [{"id": "revenue", "value": 0}]

    result = validate_model_spec(spec)

    codes = {error["code"] for error in result["errors"]}
    assert {"duplicate_runtime_id", "reserved_runtime_id"} <= codes
    assert not any(error["path"] in {"costs[cost].id", "revenues[revenue].id"} for error in result["errors"])


def test_schema_rejects_runtime_coercion_traps():
    spec = empty_model_spec()
    spec["metadata"]["horizon"] = 2.5
    spec["demand"] = {"arrivals_per_period": "many"}
    spec["distributions"] = [{"id": "demand", "distribution": "empirical", "params": {"observations": [1, "bad"]}}]
    spec["products"] = [{"id": "product"}]
    spec["materials"] = [{"id": "material", "unit_cost": 1}]
    spec["boms"] = [{"id": "bom", "product_id": "product", "items": [{"component_id": "material", "quantity": 1, "yield_pct": 120}]}]

    result = validate_model_spec(spec)

    assert result["valid"] is False
    paths = {error["path"] for error in result["errors"]}
    assert "metadata.horizon" in paths
    assert "demand.arrivals_per_period" in paths
    assert "distributions[demand].params.observations[1]" in paths
    assert "boms[bom].items[0].yield_pct" in paths


def test_schema_validates_explicit_financial_inputs_and_safe_references():
    spec = empty_model_spec()
    spec["variables"] = [{"id": "price", "value": 10}]
    spec["financial"] = {"unit_price": "price", "investment": 100}
    assert validate_model_spec(spec)["valid"] is True

    spec["financial"]["opening_cash"] = "__import__('os')"
    invalid = validate_model_spec(spec)
    assert any(error["path"] == "financial.opening_cash" and error["code"] == "unsafe_expression" for error in invalid["errors"])

    spec["financial"] = {"not_a_metric": 1}
    invalid = validate_model_spec(spec)
    assert any(error["code"] == "unknown_field" for error in invalid["errors"])


def test_schema_requires_discrete_event_arrivals_to_be_integral():
    spec = empty_model_spec()
    spec["demand"] = {"arrivals_per_period": 1.5}
    result = validate_model_spec(spec)
    assert any(error["code"] == "invalid_integer" for error in result["errors"])


def test_schema_rejects_unsafe_constraint_expressions():
    spec = empty_model_spec()
    spec["constraints"] = [{"id": "safe-stock", "expression": "__import__('os')"}]
    result = validate_model_spec(spec)
    assert any(error["path"] == "constraints[safe-stock].expression" for error in result["errors"])


def test_schema_validates_provenance_on_operational_and_financial_records():
    spec = empty_model_spec(name="Provenance")
    spec["stocks"] = [{"id": "inventory", "initial": 1, "provenance": "UNKNOWN"}]
    spec["costs"] = [{"id": "rent", "value": 10, "provenance": "UNKNOWN"}]
    result = validate_model_spec(spec)
    invalid = [error for error in result["errors"] if error["code"] == "invalid_provenance"]
    assert {error["path"] for error in invalid} == {"stocks[inventory].provenance", "costs[rent].provenance"}


def test_schema_rejects_non_finite_visual_layout_coordinates():
    spec = empty_model_spec(name="Layout")
    spec["variables"] = [{"id": "demand", "value": 1, "position": {"x": "left", "y": float("nan")}}]
    result = validate_model_spec(spec)
    assert {error["path"] for error in result["errors"] if error["code"] == "invalid_position"} == {
        "variables[demand].position.x", "variables[demand].position.y"
    }


def test_schema_rejects_flow_between_incompatible_stock_units():
    spec = empty_model_spec()
    spec["stocks"] = [{"id": "inventory", "unit": "kg"}, {"id": "cash", "unit": "Bs"}]
    spec["flows"] = [{"id": "invalid-transfer", "source_id": "inventory", "target_id": "cash", "unit": "kg", "value": 1}]
    result = validate_model_spec(spec)
    assert any(error["code"] == "incompatible_units" for error in result["errors"])


def test_schema_rejects_equation_cycles():
    spec = empty_model_spec()
    spec["equations"] = [
        {"id": "a", "expression": "b + 1"},
        {"id": "b", "expression": "a + 1"},
    ]

    result = validate_model_spec(spec)

    assert result["valid"] is False
    assert any(error["code"] == "cycle" for error in result["errors"])


def test_schema_rejects_incompatible_equation_units():
    spec = empty_model_spec(name="Units")
    spec["variables"] = [
        {"id": "material", "value": 1, "unit": "kg"},
        {"id": "price", "value": 2, "unit": "Bs"},
    ]
    spec["equations"] = [{"id": "invalid_total", "expression": "material + price", "unit": "Bs"}]

    result = validate_model_spec(spec)

    assert any(error["code"] == "incompatible_units" for error in result["errors"])


def test_schema_accepts_count_as_neutral_in_business_multiplication():
    spec = empty_model_spec(name="Units")
    spec["variables"] = [
        {"id": "price", "value": 2, "unit": "Bs"},
        {"id": "quantity", "value": 3, "unit": "unit"},
    ]
    spec["equations"] = [{"id": "total", "expression": "price * quantity", "unit": "Bs"}]

    result = validate_model_spec(spec)

    assert result["valid"] is True


def test_recursive_bom_is_rejected():
    spec = empty_model_spec(name="Recursive")
    spec["products"] = [{"id": "a"}, {"id": "b"}]
    spec["boms"] = [
        {"id": "a-bom", "product_id": "a", "items": [{"component_id": "b", "quantity": 1}]},
        {"id": "b-bom", "product_id": "b", "items": [{"component_id": "a", "quantity": 1}]},
    ]
    result = validate_model_spec(spec)
    assert any(error["code"] == "cycle" for error in result["errors"])


def test_service_blueprint_requires_positive_task_duration():
    spec = empty_model_spec(name="Service")
    spec["resources"] = [{"id": "role", "name": "Consultor"}]
    spec["services"] = [{"id": "service", "tasks": [{"id": "task", "duration": 0, "role_id": "role"}]}]
    result = validate_model_spec(spec)
    assert any(error["code"] == "invalid_duration" for error in result["errors"])


def test_causal_loop_is_explanatory_and_classified_by_polarity():
    spec = empty_model_spec(name="Feedback")
    spec["variables"] = [{"id": "demand"}, {"id": "capacity"}]
    spec["causal_links"] = [
        {"id": "a", "source_id": "demand", "target_id": "capacity", "polarity": "positive"},
        {"id": "b", "source_id": "capacity", "target_id": "demand", "polarity": "negative"},
    ]

    result = validate_model_spec(spec)

    assert result["valid"] is True
    assert result["causal_loops"][0]["type"] == "BALANCING"


def test_causal_link_rejects_unknown_polarity_and_reference():
    spec = empty_model_spec()
    spec["causal_links"] = [{"id": "link", "source_id": "missing", "target_id": "also-missing", "polarity": "sideways"}]
    result = validate_model_spec(spec)
    assert {error["code"] for error in result["errors"]} >= {"unresolved_reference", "invalid_polarity"}


def test_schema_rejects_bom_component_with_incompatible_unit():
    spec = empty_model_spec()
    spec["products"] = [{"id": "bread"}]
    spec["materials"] = [{"id": "milk", "unit": "liter"}]
    spec["boms"] = [{"id": "bread-bom", "product_id": "bread", "items": [{"component_id": "milk", "quantity": 1, "unit": "kg"}]}]
    result = validate_model_spec(spec)
    assert any(error["code"] == "incompatible_units" for error in result["errors"])


def test_schema_rejects_unsafe_output_formula():
    spec = empty_model_spec()
    spec["outputs"] = [{"id": "kpi", "expression": "__import__('os')"}]
    result = validate_model_spec(spec)
    assert any(error["path"] == "outputs[kpi].expression" for error in result["errors"])


def test_schema_rejects_circular_dynamic_kpis():
    spec = empty_model_spec()
    spec["outputs"] = [
        {"id": "first", "expression": "second + 1"},
        {"id": "second", "expression": "first + 1"},
    ]

    result = validate_model_spec(spec)

    assert result["valid"] is False
    assert any(error["path"] == "outputs" and error["code"] == "cycle" for error in result["errors"])


def test_schema_rejects_equation_dependency_on_later_financial_phase():
    spec = empty_model_spec()
    spec["equations"] = [{"id": "invalid_margin", "expression": "profit / revenue"}]

    result = validate_model_spec(spec)

    assert result["valid"] is False
    assert any(error["path"] == "equations[invalid_margin].expression" for error in result["errors"])


def test_schema_rejects_structural_ids_and_undeclared_inputs_as_runtime_symbols():
    spec = empty_model_spec()
    spec["resources"] = [{"id": "worker", "capacity": 1}]
    spec["equations"] = [
        {"id": "capacity_copy", "expression": "worker", "inputs": ["worker"]},
        {"id": "missing_input", "expression": "1", "inputs": ["not_declared"]},
    ]

    result = validate_model_spec(spec)

    assert result["valid"] is False
    assert any(error["code"] == "unresolved_reference" for error in result["errors"])


def test_schema_supports_supplier_channel_role_and_inventory_structures():
    spec = empty_model_spec(name="Supply model")
    spec["suppliers"] = [{"id": "flour-supplier", "name": "Proveedor de harina"}]
    spec["employee_roles"] = [{"id": "baker", "name": "Panadero"}]
    spec["sales_channels"] = [{"id": "counter", "name": "Mostrador"}]
    spec["inventory_nodes"] = [{"id": "warehouse", "name": "Almacén"}]
    spec["materials"] = [{"id": "flour", "supplier_id": "flour-supplier", "unit_cost": 1}]

    assert validate_model_spec(spec)["valid"] is True

    spec["materials"][0]["supplier_id"] = "missing-supplier"
    result = validate_model_spec(spec)
    assert any(error["code"] == "unresolved_reference" for error in result["errors"])
