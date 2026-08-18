"""Deterministic diagram projections derived from a canonical model spec.

Diagrams are read-only projections. They are never persisted as a second model
source, so a version hash always identifies the structure that produced them.
"""

from __future__ import annotations

from typing import Any


def _label(item: dict[str, Any], fallback: str) -> str:
    return str(item.get("name") or item.get("label") or item.get("id") or fallback)


def _node(item_id: str, label: str, kind: str, **data: Any) -> dict[str, Any]:
    return {"id": item_id, "label": label, "kind": kind, **data}


def _edge(source: str, target: str, relation: str, **data: Any) -> dict[str, Any]:
    return {"source": source, "target": target, "relation": relation, **data}


def _items(spec: dict[str, Any], section: str) -> list[dict[str, Any]]:
    return [item for item in spec.get(section, []) if isinstance(item, dict) and item.get("id")]


def build_diagrams(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return all supported diagram projections in stable input order."""
    products = {item["id"]: item for item in _items(spec, "products")}
    materials = {item["id"]: item for item in _items(spec, "materials")}
    resources = {item["id"]: item for item in _items(spec, "resources")}
    diagrams: dict[str, dict[str, Any]] = {}

    bom_nodes: dict[str, dict[str, Any]] = {}
    bom_edges: list[dict[str, Any]] = []
    for product_id, product in products.items():
        bom_nodes[product_id] = _node(product_id, _label(product, product_id), "PRODUCT", position=product.get("position"))
    for material_id, material in materials.items():
        bom_nodes[material_id] = _node(material_id, _label(material, material_id), "MATERIAL", position=material.get("position"))
    for bom in _items(spec, "boms"):
        product_id = bom.get("product_id")
        if product_id not in bom_nodes:
            continue
        for item in bom.get("items", []):
            if not isinstance(item, dict) or item.get("component_id") not in bom_nodes:
                continue
            bom_edges.append(_edge(product_id, item["component_id"], "CONTAINS", quantity=item.get("quantity"), unit=item.get("unit"), waste_pct=item.get("waste_pct", 0)))
    diagrams["bom"] = {"title": "BOM / estructura de componentes", "nodes": list(bom_nodes.values()), "edges": bom_edges}

    process_nodes: list[dict[str, Any]] = []
    process_edges: list[dict[str, Any]] = []
    for process in _items(spec, "processes"):
        previous: str | None = None
        for index, step in enumerate(process.get("steps", [])):
            if not isinstance(step, dict):
                continue
            step_id = f"{process['id']}:{step.get('id') or index}"
            process_nodes.append(_node(step_id, _label(step, step_id), "PROCESS_STEP", process_id=process["id"], cycle_time=step.get("cycle_time"), position=step.get("position")))
            if previous:
                process_edges.append(_edge(previous, step_id, "SEQUENCE"))
            resource_id = step.get("resource_id")
            if resource_id in resources:
                process_edges.append(_edge(step_id, resource_id, "USES_RESOURCE"))
            previous = step_id
    process_nodes.extend(_node(item_id, _label(item, item_id), "RESOURCE", position=item.get("position")) for item_id, item in resources.items())
    diagrams["process"] = {"title": "Flujo de procesos y recursos", "nodes": process_nodes, "edges": process_edges}

    causal_nodes: dict[str, dict[str, Any]] = {}
    causal_edges: list[dict[str, Any]] = []
    known = {item["id"]: item for section in ("variables", "parameters", "stocks", "flows", "products", "resources") for item in _items(spec, section)}
    for link in _items(spec, "causal_links"):
        for key in ("source_id", "target_id"):
            node_id = link.get(key)
            if node_id in known and node_id not in causal_nodes:
                causal_nodes[node_id] = _node(node_id, _label(known[node_id], node_id), "CAUSAL_VARIABLE", position=known[node_id].get("position"))
        if link.get("source_id") in causal_nodes and link.get("target_id") in causal_nodes:
            causal_edges.append(_edge(link["source_id"], link["target_id"], "CAUSAL", polarity=link.get("polarity")))
    diagrams["causal"] = {"title": "Relaciones causales", "nodes": list(causal_nodes.values()), "edges": causal_edges}

    stock_nodes = [_node(item["id"], _label(item, item["id"]), "STOCK", unit=item.get("unit"), position=item.get("position")) for item in _items(spec, "stocks")]
    stock_ids = {node["id"] for node in stock_nodes}
    flow_nodes = [_node(item["id"], _label(item, item["id"]), "FLOW", unit=item.get("unit"), position=item.get("position")) for item in _items(spec, "flows")]
    stock_edges: list[dict[str, Any]] = []
    for flow in _items(spec, "flows"):
        if flow.get("source_id") in stock_ids:
            stock_edges.append(_edge(flow["source_id"], flow["id"], "OUTFLOW"))
        if flow.get("target_id") in stock_ids:
            stock_edges.append(_edge(flow["id"], flow["target_id"], "INFLOW"))
    diagrams["stock_flow"] = {"title": "Stocks y flujos", "nodes": stock_nodes + flow_nodes, "edges": stock_edges}

    resource_nodes = [_node(item["id"], _label(item, item["id"]), "RESOURCE", capacity=item.get("capacity"), position=item.get("position")) for item in _items(spec, "resources")]
    resource_edges = [_edge(f"{process['id']}:{step.get('id') or index}", step["resource_id"], "ALLOCATED_TO") for process in _items(spec, "processes") for index, step in enumerate(process.get("steps", [])) if isinstance(step, dict) and step.get("resource_id") in resources]
    resource_edges.extend(_edge(task.get("role_id"), service["id"], "SERVES") for service in _items(spec, "services") for task in service.get("tasks", []) if isinstance(task, dict) and task.get("role_id") in resources)
    diagrams["resources"] = {"title": "Mapa de recursos", "nodes": resource_nodes, "edges": resource_edges}

    financial_nodes: list[dict[str, Any]] = []
    financial_edges: list[dict[str, Any]] = []
    for section, kind in (("costs", "COST"), ("revenues", "REVENUE")):
        for item in _items(spec, section):
            financial_nodes.append(_node(item["id"], _label(item, item["id"]), kind, expression=item.get("expression"), position=item.get("position")))
            for token in item.get("inputs", []):
                if isinstance(token, str):
                    financial_edges.append(_edge(token, item["id"], "DRIVES"))
    diagrams["finance"] = {"title": "Estructura de costos e ingresos", "nodes": financial_nodes, "edges": financial_edges}
    return diagrams
