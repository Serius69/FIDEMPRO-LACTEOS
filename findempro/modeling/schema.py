"""Versioned, deterministic BusinessModelDefinition contract.

The schema is deliberately JSON-compatible so it can be edited by the UI,
imported from files, or proposed by an AI assistant. Validation is stricter
than JSON shape validation: references, equations, units and graph cycles are
checked before a model can be simulated.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from typing import Any

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .safe_expression import ExpressionError, validate_expression
from .units import UnitError, compatible, infer_expression_dimension, unit

SCHEMA_VERSION = "1.0"
SECTION_NAMES = (
    "metadata", "variables", "parameters", "entities", "resources", "employee_roles", "suppliers",
    "sales_channels", "inventory_nodes", "stocks", "flows", "products", "materials", "boms",
    "services", "processes", "demand", "costs", "revenues",
    "constraints", "equations", "distributions", "causal_links", "scenarios", "outputs",
)
TOP_LEVEL_NAMES = {"schema_version", *SECTION_NAMES, "financial"}
LIST_SECTIONS = set(SECTION_NAMES) - {"metadata", "demand"}
OPTIONAL_LIST_SECTIONS = {"causal_links", "employee_roles", "suppliers", "sales_channels", "inventory_nodes"}
SUPPORTED_DISTRIBUTIONS = {"empirical", "normal", "lognormal", "poisson", "negative_binomial", "gamma", "uniform", "gbm"}
SUPPORTED_PROVENANCE = {"USER_ENTERED", "IMPORTED", "HISTORICAL_BUSINESS_DATA", "PUBLIC_SOURCE", "ESTIMATED", "SIMULATED", "AI_SUGGESTED"}
FINANCIAL_CLASSIFICATIONS = {"VARIABLE", "COGS", "FIXED"}
DEFAULT_MAX_MODEL_NODES = 1_000
DEFAULT_MAX_MODEL_EDGES = 5_000


def empty_model_spec(*, name: str = "Modelo sin nombre", sector: str = "generic") -> dict[str, Any]:
    spec: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "metadata": {"name": name, "sector": sector, "description": "", "provenance": "USER_ENTERED"},
    }
    for section in LIST_SECTIONS:
        spec[section] = []
    for section in ("demand",):
        spec[section] = {}
    spec["financial"] = {}
    for section in ("costs", "revenues"):
        spec[section] = []
    return spec


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def model_hash(spec: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(spec).encode("utf-8")).hexdigest()


def _configured_limit(name: str, default: int) -> int:
    """Read a positive resource limit while keeping the DSL usable standalone."""
    try:
        value = int(getattr(settings, name, default))
    except (ImproperlyConfigured, TypeError, ValueError):
        return default
    return max(1, value)


def _model_complexity(spec: dict[str, Any]) -> dict[str, int]:
    """Count executable/visual components and their declared connections.

    Nested BOM items, process steps and service tasks are independently
    editable components, so they count as nodes. Their membership/dependency
    links, stock-flow endpoints, causal links and explicit formula inputs count
    as edges. Invalid shapes are ignored here and reported by normal schema
    validation below.
    """
    node_count = 0
    edge_count = 0
    for section in LIST_SECTIONS - {"causal_links"}:
        items = spec.get(section, [])
        if isinstance(items, list):
            node_count += len(items)

    causal_links = spec.get("causal_links", [])
    if isinstance(causal_links, list):
        edge_count += len(causal_links)

    flows = spec.get("flows", [])
    if isinstance(flows, list):
        edge_count += sum(
            int(isinstance(flow, dict) and isinstance(flow.get(endpoint), str))
            for flow in flows
            for endpoint in ("source_id", "target_id")
        )

    for collection, nested_key in (("boms", "items"), ("processes", "steps"), ("services", "tasks")):
        parents = spec.get(collection, [])
        if not isinstance(parents, list):
            continue
        for parent in parents:
            nested = parent.get(nested_key, []) if isinstance(parent, dict) else []
            if not isinstance(nested, list):
                continue
            node_count += len(nested)
            edge_count += len(nested)
            for item in nested:
                dependencies = item.get("dependencies", []) if isinstance(item, dict) else []
                if isinstance(dependencies, list):
                    edge_count += len(dependencies)

    for section in ("equations", "outputs", "constraints"):
        items = spec.get(section, [])
        if not isinstance(items, list):
            continue
        for item in items:
            inputs = item.get("inputs", []) if isinstance(item, dict) else []
            if isinstance(inputs, list):
                edge_count += len(inputs)

    return {"nodes": node_count, "edges": edge_count}


def _ids(items: list[dict[str, Any]], section: str, errors: list[dict[str, str]]) -> set[str]:
    seen: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append({"path": f"{section}[{index}]", "code": "not_object", "message": "Debe ser un objeto."})
            continue
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id.strip():
            errors.append({"path": f"{section}[{index}].id", "code": "missing_id", "message": "Cada elemento necesita un id estable."})
        elif item_id in seen:
            errors.append({"path": f"{section}[{index}].id", "code": "duplicate_id", "message": f"Id duplicado: {item_id}."})
        else:
            seen.add(item_id)
    return seen


def _ref(item: dict[str, Any], key: str, known: set[str], path: str, errors: list[dict[str, str]], *, required: bool = True):
    value = item.get(key)
    if value is None and not required:
        return
    if not isinstance(value, str) or value not in known:
        errors.append({"path": f"{path}.{key}", "code": "unresolved_reference", "message": f"Referencia no resuelta: {value!r}."})


def _number(item: dict[str, Any], key: str, path: str, errors: list[dict[str, str]], *, minimum: float | None = None, maximum: float | None = None, strict_minimum: bool = False) -> float | None:
    """Read a finite numeric field without allowing runtime conversion errors."""
    if key not in item or item[key] is None:
        return None
    raw = item[key]
    try:
        value = float(raw)
    except (TypeError, ValueError):
        errors.append({"path": f"{path}.{key}", "code": "invalid_number", "message": "Debe ser un número finito."})
        return None
    if isinstance(raw, bool) or not math.isfinite(value):
        errors.append({"path": f"{path}.{key}", "code": "invalid_number", "message": "Debe ser un número finito."})
        return None
    below = value <= minimum if strict_minimum and minimum is not None else minimum is not None and value < minimum
    above = maximum is not None and value > maximum
    if below or above:
        errors.append({"path": f"{path}.{key}", "code": "out_of_range", "message": "Está fuera del dominio permitido."})
    return value


def _position(item: dict[str, Any], path: str, errors: list[dict[str, str]]) -> None:
    """Validate optional editor layout without making layout business logic."""
    position = item.get("position")
    if position is None:
        return
    if not isinstance(position, dict):
        errors.append({"path": f"{path}.position", "code": "invalid_position", "message": "position debe ser un objeto con x e y."})
        return
    for axis in ("x", "y"):
        value = position.get(axis)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            errors.append({"path": f"{path}.position.{axis}", "code": "invalid_position", "message": "Cada coordenada debe ser un número finito."})


def _check_cycles(
    calculations: list[dict[str, Any]],
    errors: list[dict[str, str]],
    allowed_names: set[str] | None = None,
    *,
    section: str = "equations",
) -> None:
    names = {item.get("id") for item in calculations if isinstance(item, dict)}
    graph: dict[str, set[str]] = defaultdict(set)
    for item in calculations:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            continue
        try:
            names_used = validate_expression(item.get("expression", ""), allowed_names=names | set(allowed_names or set()) | set(item.get("inputs", [])))
            graph[item["id"]].update(name for name in names_used if name in names)
        except ExpressionError as exc:
            errors.append({"path": f"{section}[{item['id']}].expression", "code": "unsafe_expression", "message": str(exc)})
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str, trail: list[str]):
        if node in visiting:
            errors.append({"path": section, "code": "cycle", "message": "Dependencia circular: " + " → ".join(trail + [node])})
            return
        if node in visited:
            return
        visiting.add(node)
        for child in graph[node]:
            visit(child, trail + [node])
        visiting.remove(node)
        visited.add(node)

    for node in list(graph):
        visit(node, [])


def _check_bom_cycles(boms: list[dict[str, Any]], products: set[str], errors: list[dict[str, str]]) -> None:
    """Reject recursive product composition before it reaches a compiler."""
    graph: dict[str, set[str]] = defaultdict(set)
    for bom in boms:
        if not isinstance(bom, dict) or not isinstance(bom.get("product_id"), str):
            continue
        for component in bom.get("items", []):
            if isinstance(component, dict) and component.get("component_id") in products:
                graph[bom["product_id"]].add(component["component_id"])
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str, trail: list[str]) -> None:
        if node in visiting:
            errors.append({"path": "boms", "code": "cycle", "message": "BOM circular: " + " → ".join(trail + [node])})
            return
        if node in visited:
            return
        visiting.add(node)
        for child in graph[node]:
            visit(child, trail + [node])
        visiting.remove(node)
        visited.add(node)

    for node in list(graph):
        visit(node, [])


def _causal_loops(links: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Describe explanatory causal loops without turning them into equations."""
    graph: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for link in links:
        if isinstance(link, dict) and isinstance(link.get("source_id"), str) and isinstance(link.get("target_id"), str):
            graph[link["source_id"]].append((link["target_id"], link.get("polarity", "positive")))
    loops: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()

    def visit(start: str, node: str, trail: list[str], signs: list[str]) -> None:
        for target, polarity in graph[node]:
            if target == start:
                cycle = trail + [start]
                key = tuple(sorted(cycle[:-1]))
                if key in seen:
                    continue
                seen.add(key)
                negative_edges = sum(sign == "negative" for sign in signs + [polarity])
                loops.append({
                    "nodes": cycle,
                    "type": "BALANCING" if negative_edges % 2 else "REINFORCING",
                    "negative_edges": negative_edges,
                })
            elif target not in trail and len(trail) < len(graph):
                visit(start, target, trail + [target], signs + [polarity])

    for node in list(graph):
        visit(node, node, [node], [])
    return loops


def validate_model_spec(spec: Any) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    if not isinstance(spec, dict):
        return {"valid": False, "errors": [{"path": "$", "code": "not_object", "message": "La especificación debe ser un objeto JSON."}], "warnings": [], "readiness": {"score": 0, "missing": ["model"]}}
    if spec.get("schema_version") != SCHEMA_VERSION:
        errors.append({"path": "schema_version", "code": "unsupported_schema", "message": f"Se esperaba {SCHEMA_VERSION}."})
    for key in set(spec) - TOP_LEVEL_NAMES:
        errors.append({"path": key, "code": "unknown_section", "message": "Sección DSL no reconocida; no se acepta contenido fuera del contrato."})
    for section in SECTION_NAMES:
        if section in OPTIONAL_LIST_SECTIONS and section not in spec:
            continue
        if section not in spec:
            errors.append({"path": section, "code": "missing_section", "message": "Sección requerida ausente."})
    for section in LIST_SECTIONS:
        if section in spec and not isinstance(spec[section], list):
            errors.append({"path": section, "code": "wrong_type", "message": "Debe ser una lista."})
    complexity = _model_complexity(spec)
    max_nodes = _configured_limit("MODELING_MAX_MODEL_NODES", DEFAULT_MAX_MODEL_NODES)
    max_edges = _configured_limit("MODELING_MAX_MODEL_EDGES", DEFAULT_MAX_MODEL_EDGES)
    if complexity["nodes"] > max_nodes:
        errors.append({
            "path": "model",
            "code": "model_node_limit",
            "message": f"El modelo contiene {complexity['nodes']} componentes; el límite es {max_nodes}. Divídelo o elimina componentes innecesarios.",
        })
    if complexity["edges"] > max_edges:
        errors.append({
            "path": "model",
            "code": "model_edge_limit",
            "message": f"El modelo contiene {complexity['edges']} conexiones; el límite es {max_edges}. Simplifica sus dependencias o relaciones.",
        })
    if any(error["code"] in {"model_node_limit", "model_edge_limit"} for error in errors):
        return {
            "valid": False,
            "errors": errors,
            "warnings": [],
            "complexity": {**complexity, "max_nodes": max_nodes, "max_edges": max_edges},
            "causal_loops": [],
            "readiness": {"score": 0, "missing": ["model"], "dimensions": {}, "actions": {"model": "Reduce la complejidad del modelo antes de validarlo."}},
        }
    if not isinstance(spec.get("metadata"), dict):
        errors.append({"path": "metadata", "code": "wrong_type", "message": "Debe ser un objeto."})
    elif "horizon" in spec["metadata"]:
        horizon = _number(spec["metadata"], "horizon", "metadata", errors, minimum=1)
        if horizon is not None and (horizon != int(horizon) or horizon > 10_000):
            errors.append({"path": "metadata.horizon", "code": "invalid_horizon", "message": "El horizonte debe ser un entero entre 1 y 10.000."})

    financial = spec.get("financial", {})
    if not isinstance(financial, dict):
        errors.append({"path": "financial", "code": "wrong_type", "message": "Debe ser un objeto de entradas financieras explícitas."})
    else:
        financial_fields = {
            "units_sold", "unit_price", "unit_variable_cost", "investment",
            "cash_inflows", "cash_outflows", "opening_cash", "current_assets",
            "current_liabilities",
        }
        for key in set(financial) - financial_fields:
            errors.append({"path": f"financial.{key}", "code": "unknown_field", "message": "Entrada financiera no reconocida."})

    ids: dict[str, set[str]] = {section: _ids(spec.get(section, []), section, errors) for section in LIST_SECTIONS if isinstance(spec.get(section), list)}
    all_ids: set[str] = set().union(*ids.values()) if ids else set()
    executable_sections = ("variables", "parameters", "stocks", "flows", "equations", "processes", "services", "outputs")
    reserved_runtime_names = {"revenue", "cost", "profit", "unmet_demand"}
    executable_owner: dict[str, str] = {}
    for section in executable_sections:
        for item in spec.get(section, []) if isinstance(spec.get(section), list) else []:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                continue
            identifier = item["id"]
            if identifier in reserved_runtime_names:
                errors.append({"path": f"{section}[{identifier}].id", "code": "reserved_runtime_id", "message": f"{identifier} está reservado para una métrica agregada."})
            previous = executable_owner.get(identifier)
            if previous and previous != section:
                errors.append({"path": f"{section}[{identifier}].id", "code": "duplicate_runtime_id", "message": f"{identifier} ya está definido en {previous}."})
            else:
                executable_owner[identifier] = section
    symbol_units = {
        item.get("id"): item.get("unit")
        for section in ("variables", "parameters", "stocks", "flows", "equations", "costs", "revenues", "outputs")
        for item in spec.get(section, []) if isinstance(item, dict) and item.get("id")
    }
    for section in ("processes", "services"):
        for item in spec.get(section, []):
            if isinstance(item, dict) and item.get("id"):
                symbol_units[item["id"]] = item.get("unit", "unit")
    declared_revenue_unit = next((item.get("unit") for item in spec.get("revenues", []) if isinstance(item, dict) and item.get("unit")), None)
    declared_cost_unit = next((item.get("unit") for item in spec.get("costs", []) if isinstance(item, dict) and item.get("unit")), None)
    if declared_revenue_unit:
        symbol_units["revenue"] = declared_revenue_unit
    if declared_cost_unit:
        symbol_units["cost"] = declared_cost_unit
    if declared_revenue_unit and declared_cost_unit and compatible(declared_revenue_unit, declared_cost_unit):
        symbol_units["profit"] = declared_revenue_unit
    symbol_units["unmet_demand"] = "unit"
    # Expressions execute against the runtime value map, not against every
    # structural record in the DSL.  A resource, product or supplier id is a
    # valid relationship reference in its own section but is not automatically
    # a numeric expression variable.
    model_symbols = (
        ids.get("variables", set())
        | ids.get("parameters", set())
        | ids.get("stocks", set())
        | ids.get("equations", set())
    )
    post_flow_symbols = model_symbols | ids.get("flows", set())
    operational_symbols = post_flow_symbols | ids.get("processes", set()) | ids.get("services", set())
    runtime_symbols = operational_symbols | {"revenue", "cost", "profit", "unmet_demand"}
    financial_symbols = runtime_symbols
    if isinstance(financial, dict):
        for key, value in financial.items():
            if key not in {"units_sold", "unit_price", "unit_variable_cost", "investment", "cash_inflows", "cash_outflows", "opening_cash", "current_assets", "current_liabilities"}:
                continue
            if isinstance(value, str):
                try:
                    validate_expression(value, allowed_names=financial_symbols)
                except ExpressionError as exc:
                    errors.append({"path": f"financial.{key}", "code": "unsafe_expression", "message": str(exc)})
            elif isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                errors.append({"path": f"financial.{key}", "code": "invalid_number", "message": "Debe ser un número finito o una expresión segura."})
    # Provenance is a first-class property of every configurable record, not
    # only scalar variables.  This prevents imported/estimated costs,
    # processes, BOMs or outputs from silently becoming business truth.
    for section in (section for section in SECTION_NAMES if section not in {"metadata", "demand"}):
        for item in spec.get(section, []) if isinstance(spec.get(section), list) else []:
            if isinstance(item, dict):
                item_path = f"{section}[{item.get('id', '?')}]"
                _position(item, item_path, errors)
                if item.get("provenance") and item["provenance"] not in SUPPORTED_PROVENANCE:
                    errors.append({"path": f"{item_path}.provenance", "code": "invalid_provenance", "message": "Origen de dato no reconocido."})
                for numeric_key in ("value", "initial", "capacity", "hours_per_period", "unit_cost", "lead_time"):
                    minimum = 0 if numeric_key in {"capacity", "hours_per_period", "unit_cost", "lead_time"} else None
                    _number(item, numeric_key, item_path, errors, minimum=minimum)
                for probability_key in ("failure_probability", "rework_probability", "scrap_probability"):
                    _number(item, probability_key, item_path, errors, minimum=0, maximum=1)

    demand = spec.get("demand")
    if isinstance(demand, dict):
        if "target" in demand:
            demand_targets = ids.get("variables", set()) | ids.get("parameters", set()) | ids.get("stocks", set())
            demand_targets |= {
                item.get("target", item.get("id")) for item in spec.get("distributions", [])
                if isinstance(item, dict) and isinstance(item.get("target", item.get("id")), str)
            }
            _ref(demand, "target", demand_targets, "demand", errors)
        arrivals = _number(demand, "arrivals_per_period", "demand", errors, minimum=0)
        if arrivals is not None and arrivals != int(arrivals):
            errors.append({"path": "demand.arrivals_per_period", "code": "invalid_integer", "message": "Las llegadas por período deben ser un entero no negativo."})
        _number(demand, "value", "demand", errors, minimum=0)

    for resource in spec.get("resources", []) if isinstance(spec.get("resources"), list) else []:
        if isinstance(resource, dict):
            resource_path = f"resources[{resource.get('id', '?')}]"
            _number(resource, "availability", resource_path, errors, minimum=0, maximum=1)
            _number(resource, "downtime_probability", resource_path, errors, minimum=0, maximum=1)

    for stock in spec.get("stocks", []) if isinstance(spec.get("stocks"), list) else []:
        if not isinstance(stock, dict):
            continue
        stock_path = f"stocks[{stock.get('id', '?')}]"
        allow_negative = stock.get("allow_negative", False)
        if not isinstance(allow_negative, bool):
            errors.append({"path": f"{stock_path}.allow_negative", "code": "invalid_boolean", "message": "allow_negative debe ser booleano."})
        initial = stock.get("initial", stock.get("value", 0))
        if isinstance(initial, (int, float)) and not isinstance(initial, bool) and math.isfinite(float(initial)) and initial < 0 and allow_negative is not True:
            errors.append({"path": f"{stock_path}.initial", "code": "negative_stock", "message": "Un stock negativo requiere allow_negative=true explícito."})

    product_material_ids = ids.get("products", set()) | ids.get("materials", set())
    for section in ("materials", "products"):
        for item in spec.get(section, []) if isinstance(spec.get(section), list) else []:
            if isinstance(item, dict):
                _ref(item, "supplier_id", ids.get("suppliers", set()), f"{section}[{item.get('id', '?')}].supplier_id", errors, required=False)
    for item in spec.get("boms", []) if isinstance(spec.get("boms"), list) else []:
        if isinstance(item, dict):
            _ref(item, "product_id", ids.get("products", set()), f"boms[{item.get('id', '?')}].product_id", errors)
            if item.get("cost_classification") and str(item["cost_classification"]).upper() not in FINANCIAL_CLASSIFICATIONS:
                errors.append({"path": f"boms[{item.get('id', '?')}].cost_classification", "code": "invalid_classification", "message": "La clasificación debe ser VARIABLE, COGS o FIXED."})
            for index, component in enumerate(item.get("items", [])):
                if not isinstance(component, dict):
                    errors.append({"path": f"boms[{item.get('id', '?')}].items[{index}]", "code": "not_object", "message": "Componente inválido."})
                    continue
                _ref(component, "component_id", product_material_ids, f"boms[{item.get('id', '?')}].items[{index}]", errors)
                _ref(component, "supplier_id", ids.get("suppliers", set()), f"boms[{item.get('id', '?')}].items[{index}]", errors, required=False)
                component_definition = next((candidate for candidate in spec.get("materials", []) + spec.get("products", []) if isinstance(candidate, dict) and candidate.get("id") == component.get("component_id")), None)
                component_unit = component_definition.get("unit") if component_definition else None
                if component.get("unit") and component_unit and not compatible(component["unit"], component_unit):
                    errors.append({"path": f"boms[{item.get('id', '?')}].items[{index}].unit", "code": "incompatible_units", "message": "La unidad del componente no coincide con la del material o producto."})
                quantity = _number(component, "quantity", f"boms[{item.get('id', '?')}].items[{index}]", errors, minimum=0, strict_minimum=True)
                if quantity is not None and quantity <= 0:
                    errors.append({"path": f"boms[{item.get('id', '?')}].items[{index}].quantity", "code": "invalid_quantity", "message": "La cantidad debe ser positiva."})
                waste = _number(component, "waste_pct", f"boms[{item.get('id', '?')}].items[{index}]", errors, minimum=0, maximum=100)
                if waste is not None and not 0 <= waste < 100:
                    errors.append({"path": f"boms[{item.get('id', '?')}].items[{index}].waste_pct", "code": "invalid_percentage", "message": "El desperdicio debe estar entre 0 y 100%."})
                yield_pct = _number(component, "yield_pct", f"boms[{item.get('id', '?')}].items[{index}]", errors, minimum=0, maximum=100, strict_minimum=True)
                if yield_pct is not None and yield_pct > 100:
                    errors.append({"path": f"boms[{item.get('id', '?')}].items[{index}].yield_pct", "code": "invalid_percentage", "message": "El rendimiento debe estar entre 0 y 100%."})
    _check_bom_cycles(spec.get("boms", []) if isinstance(spec.get("boms"), list) else [], ids.get("products", set()), errors)

    for item in spec.get("services", []) if isinstance(spec.get("services"), list) else []:
        if isinstance(item, dict):
            tasks = item.get("tasks", [])
            if not isinstance(tasks, list) or not tasks:
                errors.append({"path": f"services[{item.get('id', '?')}].tasks", "code": "missing_tasks", "message": "Un servicio necesita al menos una tarea."})
            for index, task in enumerate(tasks if isinstance(tasks, list) else []):
                if not isinstance(task, dict):
                    errors.append({"path": f"services[{item.get('id', '?')}].tasks[{index}]", "code": "not_object", "message": "Tarea inválida."})
                    continue
                duration = _number(task, "duration", f"services[{item.get('id', '?')}].tasks[{index}]", errors, minimum=0, strict_minimum=True)
                if duration is None or duration <= 0:
                    errors.append({"path": f"services[{item.get('id', '?')}].tasks[{index}].duration", "code": "invalid_duration", "message": "La duración debe ser positiva."})
                _ref(task, "role_id", ids.get("resources", set()), f"services[{item.get('id', '?')}].tasks[{index}]", errors, required=False)

    for item in spec.get("processes", []) if isinstance(spec.get("processes"), list) else []:
        if isinstance(item, dict):
            for index, step in enumerate(item.get("steps", [])):
                if not isinstance(step, dict):
                    errors.append({"path": f"processes[{item.get('id', '?')}].steps[{index}]", "code": "not_object", "message": "Paso inválido."})
                    continue
                _ref(step, "resource_id", ids.get("resources", set()), f"processes[{item.get('id', '?')}].steps[{index}]", errors, required=False)
                cycle_time = _number(step, "cycle_time", f"processes[{item.get('id', '?')}].steps[{index}]", errors, minimum=0)
                if cycle_time is not None and cycle_time < 0:
                    errors.append({"path": f"processes[{item.get('id', '?')}].steps[{index}].cycle_time", "code": "negative_cycle_time", "message": "El tiempo de ciclo no puede ser negativo."})
                step_path = f"processes[{item.get('id', '?')}].steps[{index}]"
                probabilities = []
                for probability_key in ("failure_probability", "rework_probability", "scrap_probability"):
                    probability = _number(step, probability_key, step_path, errors, minimum=0, maximum=1)
                    if probability is not None:
                        probabilities.append(probability)
                if sum(probabilities) > 1:
                    errors.append({"path": step_path, "code": "invalid_probabilities", "message": "Las probabilidades de fallo, retrabajo y scrap no pueden sumar más de 1."})

    for item in spec.get("flows", []) if isinstance(spec.get("flows"), list) else []:
        if isinstance(item, dict):
            flow_path = f"flows[{item.get('id', '?')}]"
            _ref(item, "source_id", ids.get("stocks", set()), f"{flow_path}.source_id", errors, required=False)
            _ref(item, "target_id", ids.get("stocks", set()), f"{flow_path}.target_id", errors, required=False)
            if item.get("role") not in {None, "demand", "supply", "transfer"}:
                errors.append({"path": f"{flow_path}.role", "code": "invalid_flow_role", "message": "role debe ser demand, supply o transfer."})
            if item.get("unit"):
                try:
                    unit(item["unit"])
                except UnitError as exc:
                    errors.append({"path": f"{flow_path}.unit", "code": "invalid_unit", "message": str(exc)})
            source = next((stock for stock in spec.get("stocks", []) if isinstance(stock, dict) and stock.get("id") == item.get("source_id")), None)
            target = next((stock for stock in spec.get("stocks", []) if isinstance(stock, dict) and stock.get("id") == item.get("target_id")), None)
            source_unit = source.get("unit") if source else None
            target_unit = target.get("unit") if target else None
            if source_unit and target_unit and not compatible(source_unit, target_unit):
                errors.append({"path": flow_path, "code": "incompatible_units", "message": "El flujo conecta stocks con unidades incompatibles."})
            if item.get("unit") and source_unit and not compatible(item["unit"], source_unit):
                errors.append({"path": f"{flow_path}.unit", "code": "incompatible_units", "message": "La unidad del flujo no coincide con el stock de origen."})
            if item.get("unit") and target_unit and not compatible(item["unit"], target_unit):
                errors.append({"path": f"{flow_path}.unit", "code": "incompatible_units", "message": "La unidad del flujo no coincide con el stock destino."})

    for section in ("costs", "revenues"):
        for item in spec.get(section, []) if isinstance(spec.get(section), list) else []:
            if isinstance(item, dict) and section == "costs" and item.get("classification") and str(item["classification"]).upper() not in FINANCIAL_CLASSIFICATIONS:
                errors.append({"path": f"costs[{item.get('id', '?')}].classification", "code": "invalid_classification", "message": "La clasificación debe ser VARIABLE, COGS o FIXED."})
            if isinstance(item, dict) and item.get("expression"):
                item_path = f"{section}[{item.get('id', '?')}]"
                try:
                    validate_expression(item["expression"], allowed_names=operational_symbols)
                except ExpressionError as exc:
                    errors.append({"path": f"{item_path}.expression", "code": "unsafe_expression", "message": str(exc)})
                if item.get("unit"):
                    try:
                        inferred = infer_expression_dimension(item["expression"], symbol_units)
                        expected = unit(item["unit"]).dimension
                        if inferred not in {expected, "dimensionless"} and expected != "dimensionless":
                            raise UnitError(f"La expresión produce {inferred}, pero declara {expected}.")
                    except UnitError as exc:
                        errors.append({"path": f"{item_path}.unit", "code": "incompatible_units", "message": str(exc)})

    for item in spec.get("distributions", []) if isinstance(spec.get("distributions"), list) else []:
        if isinstance(item, dict):
            distribution = item.get("distribution")
            path = f"distributions[{item.get('id', '?')}]"
            if distribution not in SUPPORTED_DISTRIBUTIONS:
                errors.append({"path": f"{path}.distribution", "code": "unsupported_distribution", "message": "Distribución no soportada para este modelo."})
                continue
            params = item.get("params", {})
            if not isinstance(params, dict):
                errors.append({"path": f"{path}.params", "code": "invalid_distribution_params", "message": "Los parámetros deben ser un objeto."})
                continue

            if distribution == "empirical":
                observations = params.get("observations")
                if not isinstance(observations, list) or not observations:
                    errors.append({"path": f"{path}.params.observations", "code": "invalid_distribution_params", "message": "La distribución empírica necesita observaciones."})
                else:
                    for index, observation in enumerate(observations):
                        if isinstance(observation, bool) or not isinstance(observation, (int, float)) or not math.isfinite(float(observation)):
                            errors.append({"path": f"{path}.params.observations[{index}]", "code": "invalid_distribution_params", "message": "Cada observación debe ser un número finito."})
            for key in ("mean", "drift"):
                if key in params:
                    finite_raw = params.get(key)
                    try:
                        finite_value = float(finite_raw)
                    except (TypeError, ValueError):
                        finite_value = math.nan
                    if isinstance(finite_raw, bool) or not math.isfinite(finite_value):
                        errors.append({"path": f"{path}.params.{key}", "code": "invalid_distribution_params", "message": "El parámetro debe ser numérico y finito."})

            def finite_number(name: str, *, minimum: float | None = None, strictly_positive: bool = False) -> float | None:
                raw = params.get(name)
                if raw is None or isinstance(raw, bool):
                    return None
                try:
                    value = float(raw)
                except (TypeError, ValueError):
                    errors.append({"path": f"{path}.params.{name}", "code": "invalid_distribution_params", "message": "El parámetro debe ser numérico."})
                    return None
                if not math.isfinite(value) or (strictly_positive and value <= 0) or (minimum is not None and value < minimum):
                    errors.append({"path": f"{path}.params.{name}", "code": "invalid_distribution_params", "message": "El parámetro está fuera de su dominio válido."})
                return value

            if distribution == "normal":
                finite_number("std", minimum=0)
            elif distribution == "lognormal":
                finite_number("sigma", minimum=0)
            elif distribution == "poisson":
                finite_number("lam", minimum=0)
            elif distribution == "negative_binomial":
                finite_number("n", strictly_positive=True)
                probability = finite_number("p")
                if probability is not None and not 0 < probability <= 1:
                    errors.append({"path": f"{path}.params.p", "code": "invalid_distribution_params", "message": "p debe estar entre 0 y 1."})
            elif distribution == "gamma":
                finite_number("shape", strictly_positive=True)
                finite_number("scale", strictly_positive=True)
            elif distribution == "uniform":
                lower = finite_number("min")
                upper = finite_number("max")
                if lower is not None and upper is not None and upper < lower:
                    errors.append({"path": f"{path}.params", "code": "invalid_distribution_params", "message": "max no puede ser menor que min."})
            elif distribution == "gbm":
                finite_number("s0", minimum=0)
                finite_number("volatility", minimum=0)
    for item in spec.get("equations", []) if isinstance(spec.get("equations"), list) else []:
        if isinstance(item, dict):
            for input_index, input_name in enumerate(item.get("inputs", [])):
                if input_name not in model_symbols:
                    errors.append({"path": f"equations[{item.get('id', '?')}].inputs[{input_index}]", "code": "unresolved_reference", "message": f"Referencia no resuelta: {input_name!r}."})
            try:
                validate_expression(item.get("expression", ""), allowed_names=model_symbols)
            except ExpressionError as exc:
                errors.append({"path": f"equations[{item.get('id', '?')}].expression", "code": "unsafe_expression", "message": str(exc)})
            if item.get("unit") and item.get("expression"):
                try:
                    inferred = infer_expression_dimension(item["expression"], symbol_units)
                    expected = unit(item["unit"]).dimension
                    if inferred not in {expected, "dimensionless"} and expected != "dimensionless":
                        raise UnitError(f"La expresión produce {inferred}, pero declara {expected}.")
                except UnitError as exc:
                    errors.append({"path": f"equations[{item.get('id', '?')}].unit", "code": "incompatible_units", "message": str(exc)})
            if item.get("unit"):
                try:
                    unit(item["unit"])
                except UnitError as exc:
                    errors.append({"path": f"equations[{item.get('id', '?')}].unit", "code": "invalid_unit", "message": str(exc)})
    for item in spec.get("constraints", []) if isinstance(spec.get("constraints"), list) else []:
        if isinstance(item, dict):
            try:
                validate_expression(item.get("expression", ""), allowed_names=runtime_symbols)
            except ExpressionError as exc:
                errors.append({"path": f"constraints[{item.get('id', '?')}].expression", "code": "unsafe_expression", "message": str(exc)})
    for item in spec.get("outputs", []) if isinstance(spec.get("outputs"), list) else []:
        if isinstance(item, dict):
            output_runtime_symbols = runtime_symbols | ids.get("outputs", set())
            try:
                validate_expression(item.get("expression", ""), allowed_names=output_runtime_symbols)
            except ExpressionError as exc:
                errors.append({"path": f"outputs[{item.get('id', '?')}].expression", "code": "unsafe_expression", "message": str(exc)})
            if item.get("unit") and item.get("expression"):
                try:
                    inferred = infer_expression_dimension(item["expression"], symbol_units)
                    expected = unit(item["unit"]).dimension
                    if inferred not in {expected, "dimensionless"} and expected != "dimensionless":
                        raise UnitError(f"La expresión produce {inferred}, pero declara {expected}.")
                except UnitError as exc:
                    errors.append({"path": f"outputs[{item.get('id', '?')}].unit", "code": "incompatible_units", "message": str(exc)})
    _check_cycles(spec.get("equations", []) if isinstance(spec.get("equations"), list) else [], errors, model_symbols)
    _check_cycles(
        spec.get("outputs", []) if isinstance(spec.get("outputs"), list) else [],
        errors,
        runtime_symbols,
        section="outputs",
    )

    causal_links = spec.get("causal_links", [])
    if isinstance(causal_links, list):
        causal_nodes = all_ids - ids.get("causal_links", set())
        for item in causal_links:
            if isinstance(item, dict):
                _ref(item, "source_id", causal_nodes, f"causal_links[{item.get('id', '?')}]", errors)
                _ref(item, "target_id", causal_nodes, f"causal_links[{item.get('id', '?')}]", errors)
                if item.get("polarity") not in {"positive", "negative"}:
                    errors.append({"path": f"causal_links[{item.get('id', '?')}].polarity", "code": "invalid_polarity", "message": "La polaridad debe ser positive o negative."})
    causal_loops = _causal_loops(causal_links if isinstance(causal_links, list) else [])

    dimensions = {
        "demand": bool(spec.get("demand")) or any(
            isinstance(item, dict) and (item.get("role") == "demand" or item.get("is_demand") is True)
            for section in ("variables", "parameters") for item in spec.get(section, [])
        ),
        "cost": bool(spec.get("costs") or any(
            isinstance(item, dict) and item.get("unit_cost") is not None
            for section in ("materials", "products") for item in spec.get(section, [])
        )),
        "revenue": bool(spec.get("revenues")),
        "capacity": bool(spec.get("resources")),
        "inventory": bool(spec.get("boms") or spec.get("materials") or spec.get("stocks")),
        "process": bool(spec.get("processes") or spec.get("services")),
        "finance": bool(spec.get("costs") and spec.get("revenues")),
        "uncertainty": bool(spec.get("distributions")),
        "data": any(
            isinstance(item, dict) and ("value" in item or "initial" in item)
            for section in ("variables", "parameters", "stocks") for item in spec.get(section, [])
        ),
    }
    missing = [name for name, present in dimensions.items() if not present]
    score = round(100 * (len(dimensions) - len(missing)) / len(dimensions))
    actions = {
        "demand": "Define una demanda base, un objetivo de demanda o una distribución de llegadas.",
        "cost": "Añade costos explícitos o costos unitarios de materiales/productos.",
        "revenue": "Define al menos un driver de ingresos con unidad y fórmula o valor.",
        "capacity": "Declara recursos y capacidad disponible para limitar el servicio/proceso.",
        "inventory": "Añade stocks, materiales o una estructura BOM si el negocio maneja inventario.",
        "process": "Define procesos o un blueprint de servicio para modelar operaciones.",
        "finance": "Conecta ingresos y costos para habilitar resultados financieros.",
        "uncertainty": "Selecciona distribuciones o datos históricos si necesitas incertidumbre.",
        "data": "Confirma valores iniciales o parámetros observados/importados.",
    }
    if missing:
        warnings.append({"path": "model", "code": "incomplete", "message": "Faltan dimensiones: " + ", ".join(missing)})
    return {"valid": not errors, "errors": errors, "warnings": warnings, "complexity": {**complexity, "max_nodes": max_nodes, "max_edges": max_edges}, "causal_loops": causal_loops, "readiness": {"score": score, "missing": missing, "dimensions": dimensions, "actions": {name: actions[name] for name in missing}}}
