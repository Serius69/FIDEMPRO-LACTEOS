"""Deterministic runtime for the canonical model specification.

This is intentionally small and composable: it handles the common stock/flow
path directly and leaves advanced DES/ABM adapters behind explicit contracts.
It never evaluates Python source; formulas go through ``safe_expression``.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import math
from typing import Any, Protocol

import numpy as np

from .safe_expression import evaluate_expression, validate_expression
from .financial import summarize_explicit_financials
from .schema import validate_model_spec


class ModelCompileError(ValueError):
    pass


SUPPORTED_ENGINES = {"monte_carlo", "system_dynamics", "discrete_event"}


@dataclass(frozen=True)
class CompiledModel:
    spec: dict[str, Any]
    horizon: int


def validate_scenario_changes(spec: dict[str, Any], changes: dict[str, Any]) -> None:
    """Validate explicit scenario inputs before they can alter a run."""
    if not isinstance(changes, dict) or not changes:
        raise ModelCompileError("changes debe contener al menos una variable.")
    allowed = {
        item["id"]
        for section in ("variables", "parameters", "stocks")
        for item in spec.get(section, [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    allowed.update(
        item.get("target", item.get("id"))
        for item in spec.get("distributions", [])
        if isinstance(item, dict) and isinstance(item.get("target", item.get("id")), str)
    )
    demand = spec.get("demand") if isinstance(spec.get("demand"), dict) else {}
    if "arrivals_per_period" in demand:
        allowed.add("arrivals_per_period")
    unknown = sorted(set(changes) - allowed)
    if unknown:
        raise ModelCompileError("Variables de escenario no configurables: " + ", ".join(unknown))
    if len(changes) > 20 or any(not isinstance(key, str) or not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)) for key, value in changes.items()):
        raise ModelCompileError("changes debe contener hasta 20 variables con valores numéricos finitos.")


class SimulationEngine(Protocol):
    """Common contract; each engine keeps its own time and randomness semantics."""

    engine_name: str

    def validate(self, spec: dict[str, Any]) -> dict[str, Any]: ...
    def compile(self, spec: dict[str, Any]) -> CompiledModel: ...
    def run(self, spec: dict[str, Any], *, seed: int | None = None, scenario: dict[str, Any] | None = None) -> dict[str, Any]: ...
    def summarize(self, result: dict[str, Any]) -> dict[str, Any]: ...


def compile_model(spec: dict[str, Any]) -> CompiledModel:
    validation = validate_model_spec(spec)
    if not validation["valid"]:
        raise ModelCompileError(validation)
    horizon = int(spec.get("metadata", {}).get("horizon", 12) or 12)
    if horizon < 1 or horizon > 10_000:
        raise ModelCompileError("El horizonte debe estar entre 1 y 10.000 períodos.")
    return CompiledModel(spec=spec, horizon=horizon)


def _value(item: dict[str, Any], values: dict[str, float], *, default: float = 0.0) -> float:
    expression = item.get("expression")
    if expression:
        return evaluate_expression(expression, values)
    raw = item.get("value", item.get("initial", default))
    return float(raw or 0.0)


def _dependency_order(
    calculations: list[dict[str, Any]],
    *,
    section: str,
    allowed_names: set[str],
) -> list[dict[str, Any]]:
    """Return a stable topological order for safe formula records."""
    records = [item for item in calculations if isinstance(item, dict) and isinstance(item.get("id"), str)]
    by_id = {item["id"]: item for item in records}
    names = set(by_id)
    dependencies = {
        item["id"]: validate_expression(item.get("expression", ""), allowed_names=names | allowed_names) & names
        for item in records
    }
    ordered: list[dict[str, Any]] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(identifier: str, trail: list[str]) -> None:
        if identifier in visiting:
            raise ModelCompileError(f"Dependencia circular en {section}: " + " → ".join(trail + [identifier]))
        if identifier in visited:
            return
        visiting.add(identifier)
        for dependency in dependencies[identifier]:
            visit(dependency, trail + [identifier])
        visiting.remove(identifier)
        visited.add(identifier)
        ordered.append(by_id[identifier])

    for item in records:
        visit(item["id"], [])
    return ordered


def _financial_input(value: Any, values: dict[str, float]) -> float:
    """Resolve one explicit financial input without permitting code execution."""
    if isinstance(value, str):
        return float(evaluate_expression(value, values))
    return float(value)


def _distribution_sample(config: dict[str, Any], rng: np.random.Generator, values: dict[str, float]) -> float:
    name = config.get("distribution", "normal")
    params = config.get("params", {})
    if name == "empirical":
        observations = params.get("observations", [])
        if not observations:
            raise ModelCompileError("La distribución empírica necesita observations.")
        return float(rng.choice(observations))
    if name == "normal": return float(rng.normal(params.get("mean", 0), params.get("std", 1)))
    if name == "lognormal": return float(rng.lognormal(params.get("mean", 0), params.get("sigma", 1)))
    if name == "poisson": return float(rng.poisson(params.get("lam", 1)))
    if name == "negative_binomial": return float(rng.negative_binomial(params.get("n", 1), params.get("p", 0.5)))
    if name == "gamma": return float(rng.gamma(params.get("shape", 1), params.get("scale", 1)))
    if name == "uniform": return float(rng.uniform(params.get("min", 0), params.get("max", 1)))
    if name == "gbm":
        previous = values.get(config.get("target", "demand"), params.get("s0", 1))
        drift, volatility = params.get("drift", 0), params.get("volatility", 0)
        return float(previous * np.exp((drift - volatility**2 / 2) + volatility * rng.normal()))
    raise ModelCompileError(f"Distribución no soportada: {name}.")


def _process_metrics(spec: dict[str, Any], values: dict[str, float]) -> tuple[dict[str, dict[str, float]], float]:
    """Calculate explicit per-period capacity without changing finance implicitly."""
    resources = {item.get("id"): item for item in spec.get("resources", []) if isinstance(item, dict) and item.get("id")}
    demand_cfg = spec.get("demand", {}) if isinstance(spec.get("demand"), dict) else {}
    target_demand = demand_cfg.get("target", "demand")
    metrics: dict[str, dict[str, float]] = {}
    total_unmet = 0.0
    for process in spec.get("processes", []):
        if not isinstance(process, dict) or not process.get("id"):
            continue
        capacities: list[float] = []
        for step in process.get("steps", []):
            if not isinstance(step, dict):
                continue
            cycle = float(step.get("cycle_time", 0) or 0)
            resource = resources.get(step.get("resource_id"), {})
            available = float(resource.get("capacity", 0) or 0) * float(resource.get("hours_per_period", 1) or 1)
            if cycle > 0 and available > 0:
                capacities.append(available / cycle)
        capacity = min(capacities) if capacities else 0.0
        requested = max(0.0, float(values.get(process.get("demand_variable", target_demand), process.get("demand", 0)) or 0))
        served = min(requested, capacity) if capacity else 0.0
        unmet = max(0.0, requested - served)
        total_unmet += unmet
        metrics[process["id"]] = {"requested": requested, "capacity": capacity, "served": served, "unmet": unmet, "utilization": served / capacity if capacity else 0.0}
    return metrics, total_unmet


def _service_metrics(spec: dict[str, Any], values: dict[str, float]) -> tuple[dict[str, dict[str, float]], float]:
    """Calculate service-blueprint capacity from task duration and role capacity."""
    resources = {item.get("id"): item for item in spec.get("resources", []) if isinstance(item, dict) and item.get("id")}
    demand_cfg = spec.get("demand", {}) if isinstance(spec.get("demand"), dict) else {}
    target_demand = demand_cfg.get("target", "demand")
    metrics: dict[str, dict[str, float]] = {}
    total_unmet = 0.0
    for service in spec.get("services", []):
        if not isinstance(service, dict) or not service.get("id"):
            continue
        capacities: list[float] = []
        for task in service.get("tasks", []):
            if not isinstance(task, dict):
                continue
            duration = float(task.get("duration", 0) or 0)
            role = resources.get(task.get("role_id"), {})
            available = float(role.get("capacity", 0) or 0) * float(role.get("hours_per_period", 1) or 1)
            if duration > 0 and available > 0:
                capacities.append(available / duration)
        capacity = min(capacities) if capacities else 0.0
        requested = max(0.0, float(values.get(service.get("demand_variable", target_demand), service.get("demand", 0)) or 0))
        served = min(requested, capacity) if capacity else 0.0
        unmet = max(0.0, requested - served)
        total_unmet += unmet
        metrics[service["id"]] = {"requested": requested, "capacity": capacity, "served": served, "unmet": unmet, "utilization": served / capacity if capacity else 0.0}
    return metrics, total_unmet


def _bom_metrics(spec: dict[str, Any], values: dict[str, float]) -> tuple[dict[str, float], float, list[dict[str, Any]]]:
    """Calculate material requirements; financial inclusion is explicit per BOM."""
    materials = {item.get("id"): item for item in spec.get("materials", []) if isinstance(item, dict) and item.get("id")}
    boms_by_product = {item.get("product_id"): item for item in spec.get("boms", []) if isinstance(item, dict) and item.get("product_id")}
    outputs: dict[str, float] = {}
    total_cost = 0.0
    cost_lines: list[dict[str, Any]] = []

    def bom_cost(bom: dict[str, Any], output: float, trail: tuple[str, ...]) -> float:
        bom_id = str(bom.get("id", bom.get("product_id", "bom")))
        if bom_id in trail:
            raise ModelCompileError("BOM circular durante la compilación: " + " → ".join(trail + (bom_id,)))
        subtotal = 0.0
        next_trail = trail + (bom_id,)
        for component in bom.get("items", []):
            if not isinstance(component, dict):
                continue
            quantity = max(0.0, float(component.get("quantity", 0) or 0))
            waste = max(0.0, float(component.get("waste_pct", 0) or 0))
            yield_pct = float(component.get("yield_pct", 100) or 100)
            if yield_pct <= 0:
                raise ModelCompileError(f"yield_pct inválido en BOM {bom_id}.")
            required = output * quantity * (1 + waste / 100) / (yield_pct / 100)
            component_id = component.get("component_id")
            nested = boms_by_product.get(component_id)
            if nested:
                subtotal += bom_cost(nested, required, next_trail)
                continue
            material = materials.get(component_id, {})
            unit_cost = float(component.get("unit_cost", material.get("unit_cost", material.get("cost", 0))) or 0)
            subtotal += required * unit_cost
        return subtotal

    for bom in spec.get("boms", []):
        if not isinstance(bom, dict) or not bom.get("id"):
            continue
        output = max(0.0, float(values.get(bom.get("output_variable", bom.get("product_id")), 0) or 0))
        bom_total = bom_cost(bom, output, ())
        outputs[bom["id"]] = output
        if bom.get("include_in_costs"):
            total_cost += bom_total
            cost_lines.append({"id": f"bom:{bom['id']}", "amount": bom_total, "classification": bom.get("cost_classification")})
    return outputs, total_cost, cost_lines


def run_system_dynamics(compiled: CompiledModel, *, seed: int | None = None, scenario: dict[str, Any] | None = None) -> dict[str, Any]:
    spec = compiled.spec
    scenario = scenario or {}
    changes = scenario.get("changes", {})
    if changes:
        validate_scenario_changes(spec, changes)
    rng = np.random.default_rng(seed)
    base_values = {item["id"]: float(item.get("value", item.get("initial", 0)) or 0) for section in ("variables", "parameters", "stocks") for item in spec.get(section, [])}
    states = {item["id"]: float(item.get("initial", item.get("value", 0)) or 0) for item in spec.get("stocks", [])}
    stock_specs = {item["id"]: item for item in spec.get("stocks", []) if isinstance(item, dict) and isinstance(item.get("id"), str)}
    distributions = {item.get("target", item.get("id")): item for item in spec.get("distributions", [])}
    demand_cfg = spec.get("demand", {}) if isinstance(spec.get("demand"), dict) else {}
    target_demand = demand_cfg.get("target", "demand")
    if demand_cfg.get("distribution") and target_demand not in distributions:
        distributions[target_demand] = demand_cfg
    # A stock distribution describes uncertain initial state, not a fresh
    # random reset every period. Sample it once, then let flows carry state.
    initial_values = dict(base_values)
    initial_values.update(states)
    for target in set(distributions) & set(states):
        states[target] = _distribution_sample(distributions.pop(target), rng, initial_values)
        initial_values[target] = states[target]
    stock_changes = {key: float(change) for key, change in changes.items() if key in states}
    period_changes = {key: float(change) for key, change in changes.items() if key not in states}
    for key, change in stock_changes.items():
        states[key] += change
    base_symbol_names = set(base_values) | set(states)
    equations = _dependency_order(spec.get("equations", []), section="equations", allowed_names=base_symbol_names)
    outputs = _dependency_order(
        spec.get("outputs", []),
        section="outputs",
        allowed_names=(
            base_symbol_names
            | {item["id"] for item in equations}
            | {item["id"] for item in spec.get("flows", []) if isinstance(item, dict) and isinstance(item.get("id"), str)}
            | {item["id"] for section in ("processes", "services") for item in spec.get(section, []) if isinstance(item, dict) and isinstance(item.get("id"), str)}
            | {"revenue", "cost", "profit", "unmet_demand"}
        ),
    )
    rows: list[dict[str, Any]] = []
    for period in range(compiled.horizon):
        # Scenario changes are deltas from the immutable model baseline.  They
        # must not compound merely because the simulation advances a period;
        # only stock state is carried forward through time.
        values = dict(base_values)
        values.update(states)
        for target, config in distributions.items():
            values[target] = _distribution_sample(config, rng, values)
        # Scenario deltas shift the realized stochastic input. Applying them
        # before sampling would silently discard the scenario for a target
        # that also declares a distribution.
        for key, change in period_changes.items():
            values[key] = values.get(key, 0) + change
        for equation in equations:
            values[equation["id"]] = _value(equation, values)
        flow_values: dict[str, float] = {}
        for flow in spec.get("flows", []):
            flow_values[flow["id"]] = max(0.0, _value(flow, values))
        requested_flow_values = dict(flow_values)
        # Stock updates are simultaneous. Outflows are bounded by opening
        # stock for the period; inflows settle into closing stock and become
        # available next period. This avoids hidden ordering across connected
        # stocks. Competing outflows are scaled proportionally.
        for stock_id, stock in stock_specs.items():
            if stock.get("allow_negative", False):
                continue
            outgoing = [flow for flow in spec.get("flows", []) if flow.get("source_id") == stock_id]
            requested_outbound = sum(flow_values[flow["id"]] for flow in outgoing)
            available = max(0.0, states[stock_id])
            if requested_outbound > available and requested_outbound > 0:
                scale = available / requested_outbound
                for flow in outgoing:
                    flow_values[flow["id"]] *= scale
        flow_shortfalls = {
            flow_id: max(0.0, requested - flow_values[flow_id])
            for flow_id, requested in requested_flow_values.items()
        }
        demand_flow_ids = {
            flow["id"] for flow in spec.get("flows", [])
            if isinstance(flow, dict) and flow.get("role") == "demand"
        }
        requested_demand_flow = sum(requested_flow_values[flow_id] for flow_id in demand_flow_ids)
        realized_demand_flow = sum(flow_values[flow_id] for flow_id in demand_flow_ids)
        stock_service_level = realized_demand_flow / requested_demand_flow if requested_demand_flow > 0 else None
        for flow in spec.get("flows", []):
            amount = flow_values[flow["id"]]
            source, target = flow.get("source_id"), flow.get("target_id")
            if source in states: states[source] -= amount
            if target in states: states[target] += amount
        for stock_id, stock in stock_specs.items():
            if not stock.get("allow_negative", False) and states[stock_id] < 0 and abs(states[stock_id]) < 1e-9:
                states[stock_id] = 0.0
        values.update(states)
        values.update(flow_values)
        process_metrics, process_unmet = _process_metrics(spec, values)
        service_metrics, service_unmet = _service_metrics(spec, values)
        values.update({process_id: metrics["served"] for process_id, metrics in process_metrics.items()})
        values.update({service_id: metrics["served"] for service_id, metrics in service_metrics.items()})
        stock_unmet = sum(flow_shortfalls[flow_id] for flow_id in demand_flow_ids)
        total_unmet = process_unmet + service_unmet + stock_unmet
        values["unmet_demand"] = total_unmet
        for constraint in spec.get("constraints", []):
            if not isinstance(constraint, dict):
                continue
            expression = constraint.get("expression")
            if expression and not bool(evaluate_expression(expression, values)):
                raise ModelCompileError(f"Restricción incumplida: {constraint.get('id', 'constraint')}")
        revenue = sum(_value(item, values) for item in spec.get("revenues", []))
        costs = sum(_value(item, values) for item in spec.get("costs", []))
        bom_outputs, bom_cost, bom_cost_lines = _bom_metrics(spec, values)
        costs += bom_cost
        values.update({"revenue": revenue, "cost": costs, "profit": revenue - costs, "unmet_demand": total_unmet})
        output_values: dict[str, float] = {}
        for output in outputs:
            if isinstance(output, dict) and output.get("id") and output.get("expression"):
                output_values[output["id"]] = evaluate_expression(output["expression"], values)
                values[output["id"]] = output_values[output["id"]]
        cost_lines = [{"id": item.get("id", "cost"), "amount": _value(item, values), "classification": item.get("classification")} for item in spec.get("costs", [])]
        cost_lines.extend(bom_cost_lines)
        try:
            financial_config = spec.get("financial", {}) if isinstance(spec.get("financial"), dict) else {}
            financial_inputs = {
                key: _financial_input(value, values)
                for key, value in financial_config.items()
            }
            financial = summarize_explicit_financials(
                revenue=revenue,
                cost_lines=cost_lines,
                **financial_inputs,
            )
        except ValueError as exc:
            raise ModelCompileError(f"Finanzas inválidas en el período {period + 1}: {exc}") from exc
        rows.append({"period": period + 1, "values": dict(values), "stocks": dict(states), "requested_flows": requested_flow_values, "flows": dict(flow_values), "flow_shortfalls": flow_shortfalls, "stock_service_level": stock_service_level, "demand": values.get(target_demand, 0.0), "revenue": revenue, "cost": costs, "profit": revenue - costs, "financial": financial, "outputs": output_values, "processes": process_metrics, "services": service_metrics, "unmet_demand": total_unmet, "bom_outputs": bom_outputs, "bom_cost": bom_cost})
    return {"engine": "system_dynamics", "seed": seed, "periods": rows}


def run_monte_carlo(spec: dict[str, Any], *, iterations: int = 100, seed: int | None = None, scenario: dict[str, Any] | None = None) -> dict[str, Any]:
    if iterations < 1 or iterations > 100_000:
        raise ModelCompileError("iterations debe estar entre 1 y 100.000.")
    compiled = compile_model(spec)
    master = np.random.default_rng(seed)
    profits: list[float] = []
    unmet_demand_samples: list[float] = []
    stock_service_level_samples: list[float] = []
    runs: list[dict[str, Any]] = []
    financial_samples: list[dict[str, Any]] = []
    for _ in range(iterations):
        child_seed = int(master.integers(0, 2**63 - 1))
        result = run_system_dynamics(compiled, seed=child_seed, scenario=scenario)
        profit = sum(row["profit"] for row in result["periods"])
        profits.append(profit)
        unmet_demand_samples.append(sum(float(row.get("unmet_demand", 0)) for row in result["periods"]))
        service_levels = [float(row["stock_service_level"]) for row in result["periods"] if row.get("stock_service_level") is not None]
        if service_levels:
            stock_service_level_samples.append(sum(service_levels) / len(service_levels))
        financial = _financial_summary_from_periods(result["periods"])
        if financial and financial.get("status") == "complete":
            financial_samples.append(financial)
        if len(runs) < 10:
            runs.append({"seed": child_seed, "profit": profit, "financial": financial})
    values = np.asarray(profits, dtype=float)
    summary: dict[str, Any] = {"mean": float(values.mean()), "median": float(np.median(values)), "std": float(values.std(ddof=1)) if len(values) > 1 else 0.0, "p5": float(np.percentile(values, 5)), "p95": float(np.percentile(values, 95)), "probability_loss": float(np.mean(values < 0))}
    if any(value > 0 for value in unmet_demand_samples):
        summary["mean_unmet_demand"] = float(np.mean(unmet_demand_samples))
        summary["p95_unmet_demand"] = float(np.percentile(unmet_demand_samples, 95))
    if stock_service_level_samples:
        summary["mean_stock_service_level"] = float(np.mean(stock_service_level_samples))
    if financial_samples:
        summary["financial"] = {
            "status": "complete",
            "currency": "declared_by_model",
            "mean_revenue": _decimal_mean(financial_samples, "revenue"),
            "mean_total_cost": _decimal_mean(financial_samples, "total_cost"),
            "mean_cogs": _decimal_mean(financial_samples, "cogs"),
            "mean_operating_result": _decimal_mean(financial_samples, "operating_result"),
            "mean_contribution_margin": _decimal_mean(financial_samples, "contribution_margin"),
        }
        for source_key, output_key in (
            ("roi", "mean_roi"), ("cash_flow", "mean_cash_flow"),
            ("ending_cash", "mean_ending_cash"), ("working_capital", "mean_working_capital"),
        ):
            if any(sample.get(source_key) is not None for sample in financial_samples):
                summary["financial"][output_key] = _decimal_mean(financial_samples, source_key)
    return {
        "engine": "monte_carlo",
        "iterations": iterations,
        "seed": seed,
        "summary": summary,
        "sample_runs": runs,
    }


def _decimal_mean(rows: list[dict[str, Any]], key: str) -> str:
    values = [Decimal(str(row[key])) for row in rows if row.get(key) is not None]
    return format((sum(values, Decimal("0")) / len(values)).quantize(Decimal("0.01")), "f") if values else "0.00"


def _financial_summary_from_periods(periods: list[dict[str, Any]]) -> dict[str, Any] | None:
    financials = [row.get("financial") for row in periods if isinstance(row, dict) and row.get("financial")]
    if not financials:
        return None
    missing = sorted({missing for item in financials for missing in item.get("missing", [])})
    if missing or any(item.get("status") != "complete" for item in financials):
        return {"status": "incomplete", "missing": missing}
    result = {"status": "complete", "currency": financials[0].get("currency", "declared_by_model")}
    for key in ("revenue", "total_cost", "variable_cost", "cogs", "fixed_cost", "gross_profit", "contribution_margin", "operating_result", "cash_flow"):
        values = []
        for item in financials:
            try:
                values.append(Decimal(str(item[key])))
            except (KeyError, InvalidOperation, TypeError):
                values = []
                break
        if values:
            result[key] = format(sum(values, Decimal("0.00")), "f")
    for key in ("gross_margin_pct", "contribution_margin_pct", "break_even_units", "break_even_revenue", "roi", "ending_cash", "working_capital"):
        values = []
        for item in financials:
            try:
                if item.get(key) is not None:
                    values.append(Decimal(str(item[key])))
            except (KeyError, InvalidOperation, TypeError):
                values = []
                break
        if values:
            result[key] = format((sum(values, Decimal("0.00")) / len(values)).quantize(Decimal("0.01")), "f")
    return result


def _summarize_periods(result: dict[str, Any]) -> dict[str, Any]:
    profits = [float(row.get("profit", 0)) for row in result.get("periods", []) if isinstance(row, dict)]
    if not profits:
        return {"mean": 0.0, "median": 0.0, "std": 0.0, "p5": 0.0, "p95": 0.0, "probability_loss": 0.0}
    values = np.asarray(profits, dtype=float)
    summary = {"mean": float(values.mean()), "median": float(np.median(values)), "std": float(values.std(ddof=1)) if len(values) > 1 else 0.0, "p5": float(np.percentile(values, 5)), "p95": float(np.percentile(values, 95)), "probability_loss": float(np.mean(values < 0))}
    unmet_demand = sum(float(row.get("unmet_demand", 0)) for row in result.get("periods", []))
    if unmet_demand > 0:
        summary["mean_unmet_demand"] = unmet_demand
    service_levels = [float(row["stock_service_level"]) for row in result.get("periods", []) if row.get("stock_service_level") is not None]
    if service_levels:
        summary["mean_stock_service_level"] = sum(service_levels) / len(service_levels)
    financial = _financial_summary_from_periods(result.get("periods", []))
    if financial:
        summary["financial"] = financial
    return summary


def run_engine(spec: dict[str, Any], engine: str, *, iterations: int = 100, seed: int | None = None, scenario: dict[str, Any] | None = None) -> dict[str, Any]:
    """Dispatch a validated model to one explicit engine adapter."""
    if engine not in SUPPORTED_ENGINES:
        raise ModelCompileError("Engine no soportado: " + str(engine))
    if engine == "monte_carlo":
        return run_monte_carlo(spec, iterations=iterations, seed=seed, scenario=scenario)
    if engine == "system_dynamics":
        result = run_system_dynamics(compile_model(spec), seed=seed, scenario=scenario)
        result["summary"] = _summarize_periods(result)
        return result
    result = DiscreteEventEngine().run(spec, seed=seed, scenario=scenario)
    return result


def run_sensitivity(
    spec: dict[str, Any],
    changes: dict[str, float],
    *,
    engine: str = "monte_carlo",
    metric: str = "profit",
    iterations: int = 100,
    seed: int | None = None,
) -> dict[str, Any]:
    """Run deterministic one-at-a-time additive sensitivity scenarios.

    ``changes`` is deliberately explicit: each value is an additive change in
    the variable's declared unit, not an invented percentage elasticity. Every
    perturbation uses the same seed as the baseline so effects are comparable.
    """
    validate_scenario_changes(spec, changes)
    if engine not in SUPPORTED_ENGINES:
        raise ModelCompileError("Engine no soportado: " + str(engine))
    if metric not in {"profit", "completed", "queue_end", "utilization"}:
        raise ModelCompileError("Métrica de sensibilidad no soportada: " + str(metric))

    def execute(scenario: dict[str, Any] | None = None) -> dict[str, Any]:
        return run_engine(spec, engine, iterations=iterations, seed=seed, scenario=scenario)

    baseline = execute()
    baseline_summary = baseline.get("summary") or _summarize_periods(baseline)

    def metric_value(summary: dict[str, Any]) -> float:
        if metric == "profit":
            value = summary.get("mean", summary.get("profit_mean"))
        else:
            value = summary.get(metric)
        if value is None:
            raise ModelCompileError(f"La métrica {metric} no está disponible para el engine {engine}.")
        return float(value)

    baseline_mean = metric_value(baseline_summary)
    rows = []
    for variable, delta in changes.items():
        perturbed = execute({"changes": {variable: float(delta)}})
        perturbed_summary = perturbed.get("summary") or _summarize_periods(perturbed)
        mean = metric_value(perturbed_summary)
        rows.append({
            "variable": variable,
            "change": float(delta),
            "baseline_mean": baseline_mean,
            "perturbed_mean": mean,
            "effect": mean - baseline_mean,
        })
    rows.sort(key=lambda item: abs(item["effect"]), reverse=True)
    return {
        "engine": "one_at_a_time_sensitivity",
        "simulation_engine": engine,
        "metric": metric,
        "seed": seed,
        "iterations": iterations,
        "baseline": baseline_summary,
        "factors": rows,
    }


class SystemDynamicsEngine:
    engine_name = "system_dynamics"

    def validate(self, spec: dict[str, Any]) -> dict[str, Any]:
        return validate_model_spec(spec)

    def compile(self, spec: dict[str, Any]) -> CompiledModel:
        return compile_model(spec)

    def run(self, spec: dict[str, Any], *, seed: int | None = None, scenario: dict[str, Any] | None = None) -> dict[str, Any]:
        return run_system_dynamics(self.compile(spec), seed=seed, scenario=scenario)

    def summarize(self, result: dict[str, Any]) -> dict[str, Any]:
        periods = result.get("periods", [])
        profits = [float(row.get("profit", 0)) for row in periods]
        return {"periods": len(periods), "profit_total": sum(profits), "profit_mean": sum(profits) / len(profits) if profits else 0.0}


class MonteCarloEngine:
    engine_name = "monte_carlo"

    def validate(self, spec: dict[str, Any]) -> dict[str, Any]:
        return validate_model_spec(spec)

    def compile(self, spec: dict[str, Any]) -> CompiledModel:
        return compile_model(spec)

    def run(self, spec: dict[str, Any], *, seed: int | None = None, scenario: dict[str, Any] | None = None, iterations: int = 100) -> dict[str, Any]:
        return run_monte_carlo(spec, iterations=iterations, seed=seed, scenario=scenario)

    def summarize(self, result: dict[str, Any]) -> dict[str, Any]:
        return result.get("summary", {})

    def sensitivity(self, spec: dict[str, Any], changes: dict[str, float], *, iterations: int = 100, seed: int | None = None) -> dict[str, Any]:
        return run_sensitivity(spec, changes, iterations=iterations, seed=seed)


class DiscreteEventEngine:
    """Queue/capacity adapter with explicit discrete-period semantics."""

    engine_name = "discrete_event"

    def validate(self, spec: dict[str, Any]) -> dict[str, Any]:
        return validate_model_spec(spec)

    def compile(self, spec: dict[str, Any]) -> CompiledModel:
        return compile_model(spec)

    def run(self, spec: dict[str, Any], *, seed: int | None = None, scenario: dict[str, Any] | None = None) -> dict[str, Any]:
        compiled = self.compile(spec)
        rng = np.random.default_rng(seed)
        demand = spec.get("demand", {}) if isinstance(spec.get("demand"), dict) else {}
        raw_arrivals = demand.get("arrivals_per_period", demand.get("value", 0)) or 0
        if isinstance(raw_arrivals, bool) or not isinstance(raw_arrivals, (int, float)) or not math.isfinite(float(raw_arrivals)) or float(raw_arrivals) < 0 or float(raw_arrivals) != int(float(raw_arrivals)):
            raise ModelCompileError("arrivals_per_period debe ser un entero no negativo para el engine discreto.")
        arrivals = int(raw_arrivals)
        scenario = scenario or {}
        changes = scenario.get("changes", {})
        if changes:
            validate_scenario_changes(spec, changes)
        arrival_change = changes.get("arrivals_per_period", 0) or 0
        if isinstance(arrival_change, bool) or not isinstance(arrival_change, (int, float)) or not math.isfinite(float(arrival_change)) or float(arrival_change) != int(float(arrival_change)):
            raise ModelCompileError("El cambio de arrivals_per_period debe ser un entero.")
        arrivals = max(0, arrivals + int(arrival_change))
        resource_specs = {
            item.get("id"): item for item in spec.get("resources", [])
            if isinstance(item, dict) and item.get("id")
        }
        resources = {resource_id: max(0.0, float(item.get("capacity", 1) or 0)) for resource_id, item in resource_specs.items()}
        steps = [step for process in spec.get("processes", []) for step in process.get("steps", []) if isinstance(step, dict)]
        if not steps:
            return {"engine": self.engine_name, "seed": seed, "time_semantics": "discrete_periods", "periods": [], "summary": {"arrivals": 0, "completed": 0, "failed": 0.0, "rework": 0.0, "scrap": 0.0, "queue_end": 0, "utilization": 0.0}}
        # Sequential process stages are constrained by their bottleneck, not
        # by an average of all resources.  Summing resource capacity and
        # dividing by total cycle time overstates throughput when one stage is
        # slower or has fewer workers.
        step_cycle_times = [float(step.get("cycle_time", 1) or 1) for step in steps]
        service_time = sum(step_cycle_times)
        failure_probability = 1.0
        rework_probability = 1.0
        scrap_probability = 1.0
        for step in steps:
            failure_probability *= 1 - float(step.get("failure_probability", 0) or 0)
            rework_probability *= 1 - float(step.get("rework_probability", 0) or 0)
            scrap_probability *= 1 - float(step.get("scrap_probability", 0) or 0)
        failure_probability = 1 - failure_probability
        rework_probability = 1 - rework_probability
        scrap_probability = 1 - scrap_probability
        queue = 0.0
        completed = 0.0
        failed_total = 0.0
        rework_total = 0.0
        scrap_total = 0.0
        rows = []
        for period in range(compiled.horizon):
            queue += max(0, arrivals)
            step_capacities: list[float] = []
            for step in steps:
                resource_id = step.get("resource_id")
                cycle_time = float(step.get("cycle_time", 1) or 1)
                if resource_id in resource_specs:
                    resource = resource_specs[resource_id]
                    availability = float(resource.get("availability", 1) or 0)
                    downtime_probability = float(resource.get("downtime_probability", 0) or 0)
                    downtime_factor = 0.0 if downtime_probability >= 1 else (1.0 if downtime_probability <= 0 else float(rng.random() >= downtime_probability))
                    active_capacity = resources[resource_id] * availability * downtime_factor
                else:
                    # Explicit resources are optional for small models; an
                    # unassigned stage has one implicit worker.
                    active_capacity = 1.0
                step_capacities.append(active_capacity / max(cycle_time, 1.0))
            # A period is an aggregate queue calculation; fractional capacity
            # remains meaningful when cycle time exceeds one period.
            available = min(step_capacities) if step_capacities else 0.0
            processed = min(queue, available)
            queue -= processed
            failed = processed * failure_probability
            remaining = processed - failed
            scrap = remaining * scrap_probability
            rework = (remaining - scrap) * rework_probability
            period_completed = max(0.0, remaining - scrap - rework)
            queue += rework
            failed_total += failed
            rework_total += rework
            scrap_total += scrap
            completed += period_completed
            rows.append({"period": period + 1, "arrivals": arrivals, "attempted": processed, "completed": period_completed, "failed": failed, "rework": rework, "scrap": scrap, "queue_end": queue})
        bottleneck_capacity = min(
            resources.get(step.get("resource_id"), 1.0) / max(float(step.get("cycle_time", 1) or 1), 1.0)
            for step in steps
        )
        utilization = min(1.0, completed / max(bottleneck_capacity * compiled.horizon, 1.0))
        return {"engine": self.engine_name, "seed": seed, "time_semantics": "discrete_periods", "periods": rows, "summary": {"arrivals": arrivals * compiled.horizon, "completed": completed, "failed": failed_total, "rework": rework_total, "scrap": scrap_total, "queue_end": queue, "utilization": utilization}}

    def summarize(self, result: dict[str, Any]) -> dict[str, Any]:
        return result.get("summary", {})
