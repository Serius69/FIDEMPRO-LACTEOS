from modeling.schema import validate_model_spec
from modeling.templates import SECTOR_TEMPLATES, starter_spec
from modeling.engine import compile_model, run_system_dynamics


def test_every_builtin_sector_has_a_valid_editable_synthetic_starter():
    for slug, label in SECTOR_TEMPLATES:
        result = validate_model_spec(starter_spec(slug, label))
        assert result["valid"] is True, (slug, result["errors"])
        assert result["warnings"] or result["readiness"]["score"] >= 0


def test_starters_are_structurally_different_by_business_archetype():
    retail = starter_spec("retail", "Tienda")
    bakery = starter_spec("bakery", "Panadería")
    service = starter_spec("professional-services", "Consultoría")

    assert retail["stocks"] and retail["flows"]
    assert retail["flows"][1]["role"] == "demand"
    assert "sales" in retail["revenues"][0]["expression"]
    assert bakery["products"] and bakery["boms"] and bakery["processes"]
    assert service["services"] and service["resources"]
    assert retail != bakery != service


def test_starter_demand_is_explicit_and_ready_for_simulation():
    spec = starter_spec("retail", "Tienda")
    validation = validate_model_spec(spec)

    assert validation["valid"] is True
    assert spec["demand"] == {"target": "period_demand"}
    assert validation["readiness"]["dimensions"]["demand"] is True


def test_schema_rejects_unknown_demand_target():
    spec = starter_spec("retail", "Tienda")
    spec["demand"]["target"] = "not_declared"

    result = validate_model_spec(spec)

    assert any(error["path"] == "demand.target" and error["code"] == "unresolved_reference" for error in result["errors"])


def test_retail_starter_reconciles_realized_sales_revenue_and_cogs():
    spec = starter_spec("retail", "Tienda")
    spec["metadata"]["horizon"] = 1
    next(item for item in spec["variables"] if item["id"] == "period_demand")["value"] = 5
    next(item for item in spec["variables"] if item["id"] == "unit_price")["value"] = 10
    next(item for item in spec["variables"] if item["id"] == "purchase_unit_cost")["value"] = 6
    spec["stocks"][0]["initial"] = 2

    row = run_system_dynamics(compile_model(spec), seed=1)["periods"][0]

    assert row["flows"]["sales"] == 2.0
    assert row["revenue"] == 20.0
    assert row["cost"] == 12.0
    assert row["profit"] == 8.0
    assert row["financial"]["cogs"] == "12.00"
    assert row["financial"]["operating_result"] == "8.00"


def test_manufacturing_and_service_starters_reconcile_capacity_with_finance():
    manufacturing = starter_spec("manufacturing", "Fábrica")
    manufacturing["metadata"]["horizon"] = 1
    next(item for item in manufacturing["variables"] if item["id"] == "period_demand")["value"] = 10
    next(item for item in manufacturing["variables"] if item["id"] == "unit_price")["value"] = 10
    manufacturing["materials"][0]["unit_cost"] = 4
    manufacturing["costs"][0]["value"] = 2

    production_row = run_system_dynamics(compile_model(manufacturing), seed=1)["periods"][0]

    assert production_row["processes"]["production"]["served"] == 8.0
    assert production_row["unmet_demand"] == 2.0
    assert production_row["revenue"] == 80.0
    assert production_row["bom_cost"] == 32.0
    assert production_row["cost"] == 34.0
    assert production_row["profit"] == 46.0

    service = starter_spec("professional-services", "Consultoría")
    service["metadata"]["horizon"] = 1
    next(item for item in service["variables"] if item["id"] == "period_demand")["value"] = 10
    next(item for item in service["variables"] if item["id"] == "unit_price")["value"] = 10
    service["costs"][0]["value"] = 2

    service_row = run_system_dynamics(compile_model(service), seed=1)["periods"][0]

    assert service_row["services"]["core_service"]["served"] == 8.0
    assert service_row["unmet_demand"] == 2.0
    assert service_row["revenue"] == 80.0
    assert service_row["cost"] == 2.0
    assert service_row["profit"] == 78.0
