"""Synthetic starter templates; users can edit them and add sectors without code changes."""

from .schema import empty_model_spec

SECTOR_TEMPLATES = (
    ("retail", "Retail / comercio"),
    ("grocery", "Tienda de barrio / minimarket"),
    ("restaurant", "Restaurante / food service"),
    ("bakery", "Panadería"),
    ("dairy", "Microempresa láctea"),
    ("food-production", "Producción alimentaria"),
    ("textiles", "Textiles / confecciones"),
    ("manufacturing", "Manufactura"),
    ("handicrafts", "Artesanía"),
    ("agriculture", "Agricultura"),
    ("livestock", "Ganadería"),
    ("transport", "Transporte"),
    ("logistics", "Logística"),
    ("construction", "Construcción"),
    ("repair", "Reparación / taller"),
    ("beauty", "Belleza y cuidado personal"),
    ("health", "Servicios de salud"),
    ("education", "Educación"),
    ("professional-services", "Servicios profesionales"),
    ("technology-services", "Servicios tecnológicos"),
    ("tourism", "Turismo / hospitalidad"),
    ("wholesale", "Mayorista / distribución"),
    ("ecommerce", "Comercio electrónico"),
)


def starter_spec(slug: str, name: str) -> dict:
    spec = empty_model_spec(name=name, sector=slug)
    spec["metadata"]["description"] = "Plantilla inicial con datos sintéticos; requiere confirmación del usuario."
    spec["metadata"]["provenance"] = "SIMULATED"
    spec["variables"] = [
        {"id": "unit_price", "name": "Precio unitario", "value": 1, "unit": "Bs", "provenance": "USER_ENTERED"},
        {"id": "period_demand", "name": "Demanda por período", "value": 1, "unit": "unit", "provenance": "USER_ENTERED"},
    ]
    spec["demand"] = {"target": "period_demand"}
    spec["revenues"] = [{"id": "sales_revenue", "name": "Ingresos por ventas", "expression": "unit_price * period_demand", "unit": "Bs"}]
    spec["costs"] = [{"id": "operating_cost", "name": "Costo operativo", "value": 0, "unit": "Bs", "classification": "FIXED", "provenance": "USER_ENTERED"}]

    # These are synthetic, editable structures—not sector claims or defaults
    # about a real company. The common DSL stays the source of truth, while
    # the archetypes make the first modeling session useful across SME types.
    if slug in {"retail", "grocery", "wholesale", "ecommerce"}:
        spec["variables"].append({"id": "purchase_unit_cost", "name": "Costo unitario de compra", "value": 0.6, "unit": "Bs", "provenance": "USER_ENTERED"})
        spec["stocks"] = [{"id": "inventory", "name": "Inventario", "initial": 100, "unit": "unit", "provenance": "SIMULATED"}]
        spec["resources"] = [{"id": "seller", "name": "Atención y ventas", "capacity": 1, "hours_per_period": 8, "provenance": "SIMULATED"}]
        spec["flows"] = [
            {"id": "purchases", "name": "Compras", "target_id": "inventory", "value": 20, "unit": "unit"},
            {"id": "sales", "name": "Ventas", "source_id": "inventory", "expression": "period_demand", "unit": "unit", "role": "demand"},
        ]
        spec["revenues"] = [{"id": "sales_revenue", "name": "Ingresos por ventas realizadas", "expression": "unit_price * sales", "unit": "Bs"}]
        spec["costs"] = [{"id": "purchase_cost", "name": "Costo de mercadería vendida", "expression": "purchase_unit_cost * sales", "unit": "Bs", "classification": "COGS", "provenance": "USER_ENTERED"}]
        spec["financial"] = {"units_sold": "sales", "unit_price": "unit_price", "unit_variable_cost": "purchase_unit_cost"}
    elif slug in {"bakery", "dairy", "food-production", "manufacturing", "textiles", "handicrafts", "agriculture", "livestock", "construction"}:
        spec["resources"] = [{"id": "operator", "name": "Operación", "capacity": 1, "hours_per_period": 8, "provenance": "SIMULATED"}]
        spec["products"] = [{"id": "finished_product", "name": "Producto terminado", "provenance": "USER_ENTERED"}]
        spec["materials"] = [{"id": "primary_material", "name": "Material principal", "unit": "unit", "unit_cost": 0.4, "provenance": "SIMULATED"}]
        spec["boms"] = [{"id": "finished-product-bom", "product_id": "finished_product", "output_variable": "production", "include_in_costs": True, "cost_classification": "COGS", "items": [{"component_id": "primary_material", "quantity": 1, "unit": "unit", "waste_pct": 0, "yield_pct": 100}]}]
        spec["processes"] = [{"id": "production", "name": "Producción realizada", "unit": "unit", "demand_variable": "period_demand", "steps": [{"id": "operation", "name": "Transformación", "resource_id": "operator", "cycle_time": 1}]}]
        spec["revenues"] = [{"id": "sales_revenue", "name": "Ingresos por producción realizada", "expression": "unit_price * production", "unit": "Bs"}]
        spec["costs"] = [{"id": "fixed_overhead", "name": "Overhead fijo", "value": 0, "unit": "Bs", "classification": "FIXED", "provenance": "USER_ENTERED"}]
    elif slug in {"restaurant", "tourism", "health", "education", "professional-services", "technology-services", "beauty", "repair", "transport", "logistics"}:
        spec["resources"] = [{"id": "staff", "name": "Personal", "capacity": 1, "hours_per_period": 8, "provenance": "SIMULATED"}]
        spec["services"] = [{"id": "core_service", "name": "Servicios realizados", "unit": "unit", "demand_variable": "period_demand", "tasks": [{"id": "service_task", "name": "Atención", "role_id": "staff", "duration": 1}]}]
        spec["revenues"] = [{"id": "service_revenue", "name": "Ingresos por servicios realizados", "expression": "unit_price * core_service", "unit": "Bs"}]
        spec["costs"] = [{"id": "service_overhead", "name": "Overhead del servicio", "value": 0, "unit": "Bs", "classification": "FIXED", "provenance": "USER_ENTERED"}]
    return spec
