import pytest

from modeling.engine import DiscreteEventEngine, compile_model, run_engine, run_monte_carlo, run_sensitivity, run_system_dynamics
from modeling.schema import empty_model_spec


def golden_retail_spec():
    spec = empty_model_spec(name="Tienda dorada", sector="retail")
    spec["metadata"]["horizon"] = 2
    spec["variables"] = [{"id": "price", "value": 10}, {"id": "sales", "value": 3}]
    spec["stocks"] = [{"id": "cash", "initial": 0, "unit": "Bs"}]
    spec["revenues"] = [{"id": "sales-revenue", "expression": "price * sales", "unit": "Bs"}]
    spec["costs"] = [{"id": "fixed-cost", "value": 4, "unit": "Bs"}]
    return spec


def test_golden_business_model_has_deterministic_financial_output():
    result = run_system_dynamics(compile_model(golden_retail_spec()), seed=7)

    assert [row["profit"] for row in result["periods"]] == [26.0, 26.0]


def test_engine_exposes_explicit_financial_breakdown_without_hidden_allocation():
    spec = golden_retail_spec()
    spec["costs"][0]["classification"] = "FIXED"

    row = run_system_dynamics(compile_model(spec), seed=7)["periods"][0]

    assert row["financial"]["status"] == "complete"
    assert row["financial"]["revenue"] == "30.00"
    assert row["financial"]["variable_cost"] == "0.00"
    assert row["financial"]["fixed_cost"] == "4.00"
    assert row["financial"]["operating_result"] == "26.00"


def test_engine_uses_declared_financial_inputs_for_roi_break_even_and_cash():
    spec = golden_retail_spec()
    spec["costs"][0]["classification"] = "FIXED"
    spec["financial"] = {
        "units_sold": "sales",
        "unit_price": "price",
        "unit_variable_cost": 0,
        "investment": 10,
        "cash_inflows": "revenue",
        "cash_outflows": "cost",
        "opening_cash": 100,
        "current_assets": 250,
        "current_liabilities": 90,
    }

    row = run_system_dynamics(compile_model(spec), seed=7)["periods"][0]

    assert row["financial"]["break_even_units"] == "0.4000"
    assert row["financial"]["break_even_revenue"] == "4.00"
    assert row["financial"]["roi"] == "260.0000"
    assert row["financial"]["cash_flow"] == "26.00"
    assert row["financial"]["ending_cash"] == "126.00"
    assert row["financial"]["working_capital"] == "160.00"


def test_monte_carlo_is_reproducible_for_same_model_and_seed():
    spec = golden_retail_spec()
    first = run_monte_carlo(spec, iterations=20, seed=42)
    second = run_monte_carlo(spec, iterations=20, seed=42)

    assert first == second


def test_scenario_delta_is_constant_across_periods():
    spec = golden_retail_spec()
    spec["metadata"]["horizon"] = 3
    result = run_system_dynamics(compile_model(spec), seed=7, scenario={"changes": {"price": 1}})

    assert [row["values"]["price"] for row in result["periods"]] == [11.0, 11.0, 11.0]
    assert [row["revenue"] for row in result["periods"]] == [33.0, 33.0, 33.0]


def test_scenario_delta_shifts_sampled_distribution_without_changing_random_draws():
    spec = golden_retail_spec()
    spec["distributions"] = [{"id": "sales-uncertainty", "target": "sales", "distribution": "normal", "params": {"mean": 3, "std": 1}}]

    baseline = run_system_dynamics(compile_model(spec), seed=17)
    shifted = run_system_dynamics(compile_model(spec), seed=17, scenario={"changes": {"sales": 2}})

    assert [shifted_row["values"]["sales"] - base_row["values"]["sales"] for base_row, shifted_row in zip(baseline["periods"], shifted["periods"])] == pytest.approx([2, 2])


def test_stock_scenario_delta_changes_initial_state_once_and_then_flows_carry_it():
    spec = empty_model_spec(name="Scenario cash stock")
    spec["metadata"]["horizon"] = 2
    spec["stocks"] = [{"id": "cash", "initial": 10, "unit": "Bs"}]
    spec["flows"] = [{"id": "expense", "source_id": "cash", "value": 1, "unit": "Bs"}]

    result = run_system_dynamics(compile_model(spec), seed=3, scenario={"changes": {"cash": 5}})

    assert [row["stocks"]["cash"] for row in result["periods"]] == [14.0, 13.0]


def test_stock_distribution_is_sampled_once_as_initial_state():
    spec = empty_model_spec(name="Uncertain initial stock")
    spec["metadata"]["horizon"] = 2
    spec["stocks"] = [{"id": "inventory", "initial": 0, "unit": "unit"}]
    spec["distributions"] = [{"id": "initial-inventory", "target": "inventory", "distribution": "uniform", "params": {"min": 7, "max": 7}}]
    spec["flows"] = [{"id": "sale", "source_id": "inventory", "value": 1, "unit": "unit"}]

    result = run_system_dynamics(compile_model(spec), seed=4)

    assert [row["stocks"]["inventory"] for row in result["periods"]] == [6.0, 5.0]


def test_monte_carlo_summary_keeps_explicit_financial_means():
    spec = golden_retail_spec()
    spec["costs"][0]["classification"] = "FIXED"

    result = run_monte_carlo(spec, iterations=2, seed=42)

    assert result["summary"]["financial"]["status"] == "complete"
    assert result["summary"]["financial"]["mean_revenue"] == "60.00"
    assert result["summary"]["financial"]["mean_operating_result"] == "52.00"


def test_one_at_a_time_sensitivity_is_seeded_and_sorted_by_effect():
    result = run_sensitivity(golden_retail_spec(), {"price": 1, "sales": 2}, iterations=20, seed=42)

    assert result["seed"] == 42
    assert result["factors"][0]["variable"] == "sales"
    assert result["factors"][0]["effect"] > result["factors"][1]["effect"]
    assert result == run_sensitivity(golden_retail_spec(), {"price": 1, "sales": 2}, iterations=20, seed=42)


def test_sensitivity_uses_the_selected_engine_and_metric():
    spec = empty_model_spec(name="Sensitivity workshop")
    spec["metadata"]["horizon"] = 2
    spec["resources"] = [{"id": "worker", "capacity": 4}]
    spec["processes"] = [{"id": "repair", "steps": [{"id": "task", "resource_id": "worker", "cycle_time": 1}]}]
    spec["demand"] = {"arrivals_per_period": 2}

    result = run_sensitivity(spec, {"arrivals_per_period": 1}, engine="discrete_event", metric="completed", seed=42)

    assert result["simulation_engine"] == "discrete_event"
    assert result["metric"] == "completed"
    assert result["factors"][0]["effect"] == 2.0


def test_discrete_event_engine_reports_queue_and_utilization():
    spec = empty_model_spec(name="Workshop")
    spec["metadata"]["horizon"] = 2
    spec["resources"] = [{"id": "worker", "capacity": 1}]
    spec["processes"] = [{"id": "repair", "steps": [{"id": "task", "resource_id": "worker", "cycle_time": 2}]}]
    spec["demand"] = {"arrivals_per_period": 3}

    result = DiscreteEventEngine().run(spec, seed=5)

    assert result["engine"] == "discrete_event"
    assert result["summary"]["arrivals"] == 6
    assert result["summary"]["completed"] == 1
    assert result["summary"]["queue_end"] == 5
    assert 0 < result["summary"]["utilization"] <= 1


def test_discrete_event_engine_does_not_turn_zero_capacity_into_capacity():
    spec = empty_model_spec(name="Closed workshop")
    spec["metadata"]["horizon"] = 1
    spec["resources"] = [{"id": "worker", "capacity": 0}]
    spec["processes"] = [{"id": "repair", "steps": [{"id": "task", "resource_id": "worker", "cycle_time": 1}]}]
    spec["demand"] = {"arrivals_per_period": 2}

    result = DiscreteEventEngine().run(spec, seed=5)

    assert result["summary"]["completed"] == 0
    assert result["summary"]["queue_end"] == 2


def test_discrete_event_engine_uses_the_sequential_bottleneck_capacity():
    spec = empty_model_spec(name="Bottleneck workshop")
    spec["metadata"]["horizon"] = 1
    spec["resources"] = [
        {"id": "fast", "capacity": 4},
        {"id": "slow", "capacity": 1},
    ]
    spec["processes"] = [{"id": "line", "steps": [
        {"id": "cut", "resource_id": "fast", "cycle_time": 1},
        {"id": "finish", "resource_id": "slow", "cycle_time": 1},
    ]}]
    spec["demand"] = {"arrivals_per_period": 3}

    result = DiscreteEventEngine().run(spec, seed=5)

    assert result["periods"][0]["attempted"] == 1
    assert result["summary"]["completed"] == 1
    assert result["summary"]["queue_end"] == 2


def test_discrete_event_engine_accepts_validated_arrival_scenario_changes():
    spec = empty_model_spec(name="Scenario workshop")
    spec["metadata"]["horizon"] = 2
    spec["resources"] = [{"id": "worker", "capacity": 2}]
    spec["processes"] = [{"id": "repair", "steps": [{"id": "task", "resource_id": "worker", "cycle_time": 1}]}]
    spec["demand"] = {"arrivals_per_period": 2}

    result = DiscreteEventEngine().run(spec, seed=5, scenario={"changes": {"arrivals_per_period": 1}})

    assert result["summary"]["arrivals"] == 6


def test_discrete_event_engine_rejects_unknown_scenario_changes():
    spec = empty_model_spec(name="Invalid scenario workshop")
    spec["metadata"]["horizon"] = 1
    spec["demand"] = {"arrivals_per_period": 1}

    with pytest.raises(ValueError, match="no configurables"):
        DiscreteEventEngine().run(spec, seed=5, scenario={"changes": {"unknown": 1}})


def test_discrete_event_engine_reports_failure_rework_and_scrap_with_seeded_downtime():
    spec = empty_model_spec(name="Risky workshop")
    spec["metadata"]["horizon"] = 1
    spec["resources"] = [{"id": "worker", "capacity": 4, "downtime_probability": 0}]
    spec["processes"] = [{"id": "repair", "steps": [{
        "id": "task", "resource_id": "worker", "cycle_time": 1,
        "failure_probability": 0.25, "rework_probability": 0.25, "scrap_probability": 0.25,
    }]}]
    spec["demand"] = {"arrivals_per_period": 4}

    result = DiscreteEventEngine().run(spec, seed=11)
    summary = result["summary"]

    assert summary["arrivals"] == 4
    assert summary["failed"] == pytest.approx(1)
    assert summary["scrap"] == pytest.approx(0.75)
    assert summary["rework"] == pytest.approx(0.5625)
    assert summary["completed"] == pytest.approx(1.6875)
    assert result["periods"][0]["queue_end"] == pytest.approx(0.5625)


def test_schema_rejects_process_probabilities_above_one():
    spec = empty_model_spec(name="Invalid process risk")
    spec["processes"] = [{"id": "process", "steps": [{
        "id": "step", "failure_probability": 0.8, "rework_probability": 0.4,
    }]}]

    with pytest.raises(ValueError, match="probabilidades"):
        compile_model(spec)


def test_system_dynamics_enforces_declared_stock_constraint():
    spec = empty_model_spec(name="Inventory constraint")
    spec["metadata"]["horizon"] = 1
    spec["stocks"] = [{"id": "inventory", "initial": 1, "allow_negative": True}]
    spec["flows"] = [{"id": "sales", "source_id": "inventory", "value": 2}]
    spec["constraints"] = [{"id": "nonnegative-inventory", "expression": "inventory >= 0"}]

    with pytest.raises(ValueError, match="Restricción incumplida"):
        run_system_dynamics(compile_model(spec), seed=1)


def test_bounded_stock_scales_competing_outflows_without_list_order_bias():
    spec = empty_model_spec(name="Shared inventory")
    spec["metadata"]["horizon"] = 1
    spec["stocks"] = [{"id": "inventory", "initial": 5, "unit": "unit"}]
    spec["flows"] = [
        {"id": "store-sales", "source_id": "inventory", "value": 4, "unit": "unit"},
        {"id": "online-sales", "source_id": "inventory", "value": 4, "unit": "unit"},
    ]

    row = run_system_dynamics(compile_model(spec), seed=1)["periods"][0]

    assert row["stocks"]["inventory"] == 0.0
    assert row["flows"] == {"store-sales": 2.5, "online-sales": 2.5}


def test_negative_stock_requires_explicit_opt_in_and_then_remains_unbounded():
    spec = empty_model_spec(name="Credit line")
    spec["metadata"]["horizon"] = 1
    spec["stocks"] = [{"id": "cash", "initial": 1, "unit": "Bs", "allow_negative": True}]
    spec["flows"] = [{"id": "payment", "source_id": "cash", "value": 4, "unit": "Bs"}]

    row = run_system_dynamics(compile_model(spec), seed=1)["periods"][0]

    assert row["stocks"]["cash"] == -3.0
    assert row["flows"]["payment"] == 4.0


def test_bounded_stock_uses_opening_balance_without_cross_flow_ordering():
    spec = empty_model_spec(name="Inventory settlement")
    spec["metadata"]["horizon"] = 2
    spec["stocks"] = [{"id": "inventory", "initial": 0, "unit": "unit"}]
    spec["flows"] = [
        {"id": "purchase", "target_id": "inventory", "value": 5, "unit": "unit"},
        {"id": "sale", "source_id": "inventory", "value": 5, "unit": "unit"},
    ]

    rows = run_system_dynamics(compile_model(spec), seed=1)["periods"]

    assert [row["flows"]["sale"] for row in rows] == [0.0, 5.0]
    assert [row["stocks"]["inventory"] for row in rows] == [5.0, 5.0]


def test_demand_flow_stockout_reconciles_revenue_shortfall_and_service_level():
    spec = empty_model_spec(name="Stockout retailer")
    spec["metadata"]["horizon"] = 1
    spec["variables"] = [{"id": "demand", "value": 5, "unit": "unit"}, {"id": "price", "value": 10, "unit": "Bs"}]
    spec["stocks"] = [{"id": "inventory", "initial": 2, "unit": "unit"}]
    spec["flows"] = [{"id": "sales", "source_id": "inventory", "expression": "demand", "unit": "unit", "role": "demand"}]
    spec["revenues"] = [{"id": "sales-revenue", "expression": "price * sales", "unit": "Bs"}]

    row = run_system_dynamics(compile_model(spec), seed=1)["periods"][0]

    assert row["requested_flows"]["sales"] == 5.0
    assert row["flows"]["sales"] == 2.0
    assert row["flow_shortfalls"]["sales"] == 3.0
    assert row["stock_service_level"] == pytest.approx(0.4)
    assert row["unmet_demand"] == 3.0
    assert row["revenue"] == 20.0

    monte_carlo = run_monte_carlo(spec, iterations=2, seed=1)
    dynamics = run_engine(spec, "system_dynamics", seed=1)
    assert monte_carlo["summary"]["mean_unmet_demand"] == 3.0
    assert monte_carlo["summary"]["mean_stock_service_level"] == pytest.approx(0.4)
    assert dynamics["summary"]["mean_unmet_demand"] == 3.0
    assert dynamics["summary"]["mean_stock_service_level"] == pytest.approx(0.4)


def test_engine_dispatch_exposes_composable_runtime_contracts():
    spec = empty_model_spec(name="Dispatch")
    spec["metadata"]["horizon"] = 1
    spec["variables"] = [{"id": "price", "value": 4}, {"id": "sales", "value": 2}]
    spec["revenues"] = [{"id": "revenue", "expression": "price * sales"}]

    dynamics = run_engine(spec, "system_dynamics", seed=4)
    monte_carlo = run_engine(spec, "monte_carlo", iterations=2, seed=4)

    assert dynamics["engine"] == "system_dynamics"
    assert dynamics["summary"]["mean"] == 8.0
    assert monte_carlo["engine"] == "monte_carlo"


def test_golden_manufacturer_reports_capacity_and_opt_in_bom_cost():
    spec = empty_model_spec(name="Manufactura dorada", sector="manufacturing")
    spec["metadata"]["horizon"] = 1
    spec["variables"] = [{"id": "production", "value": 4}, {"id": "price", "value": 10}]
    spec["resources"] = [{"id": "machine", "capacity": 2, "hours_per_period": 1}]
    spec["processes"] = [{"id": "assembly", "demand_variable": "production", "steps": [{"id": "step", "resource_id": "machine", "cycle_time": 1}]}]
    spec["products"] = [{"id": "widget"}]
    spec["materials"] = [{"id": "steel", "unit_cost": 3}]
    spec["boms"] = [{"id": "widget-bom", "product_id": "widget", "output_variable": "assembly", "include_in_costs": True, "items": [{"component_id": "steel", "quantity": 2, "waste_pct": 10}]}]
    spec["revenues"] = [{"id": "revenue", "expression": "price * assembly"}]

    row = run_system_dynamics(compile_model(spec), seed=1)["periods"][0]

    assert row["processes"]["assembly"] == {"requested": 4.0, "capacity": 2.0, "served": 2.0, "unmet": 2.0, "utilization": 1.0}
    assert row["values"]["assembly"] == 2.0
    assert row["revenue"] == pytest.approx(20.0)
    assert row["bom_cost"] == pytest.approx(13.2)
    assert row["cost"] == pytest.approx(13.2)
    assert row["profit"] == pytest.approx(6.8)


def test_nested_bom_includes_subassembly_material_cost():
    spec = empty_model_spec(name="Nested manufacturer", sector="manufacturing")
    spec["metadata"]["horizon"] = 1
    spec["variables"] = [{"id": "production", "value": 4}, {"id": "price", "value": 20}]
    spec["products"] = [{"id": "finished"}, {"id": "subassembly"}]
    spec["materials"] = [{"id": "steel", "unit_cost": 3}]
    spec["boms"] = [
        {"id": "subassembly-bom", "product_id": "subassembly", "output_variable": "production", "items": [{"component_id": "steel", "quantity": 2}]},
        {"id": "finished-bom", "product_id": "finished", "output_variable": "production", "include_in_costs": True, "items": [{"component_id": "subassembly", "quantity": 1}]},
    ]
    spec["revenues"] = [{"id": "revenue", "expression": "price * production"}]

    row = run_system_dynamics(compile_model(spec), seed=1)["periods"][0]

    assert row["bom_cost"] == pytest.approx(24.0)
    assert row["profit"] == pytest.approx(56.0)


def test_outputs_are_safe_dynamic_kpis_over_period_metrics():
    spec = golden_retail_spec()
    spec["outputs"] = [{"id": "profit_margin", "expression": "profit / revenue * 100", "unit": "%"}, {"id": "margin_copy", "expression": "profit_margin", "unit": "%"}]

    row = run_system_dynamics(compile_model(spec), seed=7)["periods"][0]

    assert row["outputs"] == {"profit_margin": pytest.approx(86.6666666667), "margin_copy": pytest.approx(86.6666666667)}


def test_equations_and_outputs_are_evaluated_by_dependency_not_list_order():
    spec = golden_retail_spec()
    spec["equations"] = [
        {"id": "doubled_margin", "expression": "base_margin * 2"},
        {"id": "base_margin", "expression": "price - 1"},
    ]
    spec["outputs"] = [
        {"id": "display_copy", "expression": "display_margin"},
        {"id": "display_margin", "expression": "profit / revenue * 100"},
    ]

    row = run_system_dynamics(compile_model(spec), seed=7)["periods"][0]

    assert row["values"]["doubled_margin"] == 18.0
    assert row["outputs"]["display_copy"] == pytest.approx(86.6666666667)


def test_golden_service_blueprint_and_stock_flow_are_explicitly_reported():
    spec = empty_model_spec(name="Servicio dorado", sector="professional-services")
    spec["metadata"]["horizon"] = 2
    spec["variables"] = [{"id": "demand", "value": 3}]
    spec["resources"] = [{"id": "consultant", "capacity": 1, "hours_per_period": 2}]
    spec["services"] = [{"id": "consulting", "demand_variable": "demand", "tasks": [{"id": "session", "role_id": "consultant", "duration": 1}]}]
    spec["stocks"] = [{"id": "cash", "initial": 10, "unit": "Bs"}]
    spec["flows"] = [{"id": "cash-in", "target_id": "cash", "value": 5, "unit": "Bs"}]

    result = run_system_dynamics(compile_model(spec), seed=3)

    assert result["periods"][0]["services"]["consulting"] == {"requested": 3.0, "capacity": 2.0, "served": 2.0, "unmet": 1.0, "utilization": 1.0}
    assert result["periods"][0]["unmet_demand"] == 1.0
    assert result["periods"][0]["stocks"]["cash"] == 15.0
    assert result["periods"][1]["stocks"]["cash"] == 20.0
