"""Explicit monetary contract for configurable business models.

All monetary inputs are converted through str and calculated with Decimal. The
caller must provide a cost classification; this module never silently
allocates fixed costs or invents an elasticity/return basis.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

MONEY = Decimal("0.01")
RATIO = Decimal("0.0001")
FINANCIAL_CLASSIFICATIONS = {"VARIABLE", "COGS", "FIXED"}


def money(value: Any) -> Decimal:
    try:
        return Decimal(str(value)).quantize(MONEY, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Valor monetario inválido: {value!r}") from exc


def non_negative(value: Any, field: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Valor inválido para {field}: {value!r}") from exc
    if result < 0:
        raise ValueError(f"{field} no puede ser negativo.")
    return result


@dataclass(frozen=True)
class FinancialSnapshot:
    units_sold: Decimal
    revenue: Decimal
    variable_cost: Decimal
    cogs: Decimal
    fixed_cost: Decimal
    gross_profit: Decimal
    operating_result: Decimal
    contribution_per_unit: Decimal
    contribution_margin: Decimal
    gross_margin_pct: Decimal
    contribution_margin_pct: Decimal
    break_even_units: Decimal | None
    break_even_revenue: Decimal | None
    roi: Decimal | None
    cash_flow: Decimal | None
    ending_cash: Decimal | None
    working_capital: Decimal | None

    def as_dict(self) -> dict[str, str | None]:
        return {key: (format(value, "f") if value is not None else None) for key, value in self.__dict__.items()}


def calculate_financials(
    *,
    units_sold: Any,
    unit_price: Any,
    unit_variable_cost: Any,
    fixed_cost: Any,
    investment: Any = 0,
    cash_inflows: Any | None = None,
    cash_outflows: Any | None = None,
    opening_cash: Any | None = None,
    current_assets: Any | None = None,
    current_liabilities: Any | None = None,
) -> FinancialSnapshot:
    units = non_negative(units_sold, "units_sold")
    price = non_negative(unit_price, "unit_price")
    variable_unit = non_negative(unit_variable_cost, "unit_variable_cost")
    fixed = money(non_negative(fixed_cost, "fixed_cost"))
    invested = money(non_negative(investment, "investment"))

    def optional_money(value: Any | None, field: str) -> Decimal | None:
        return None if value is None else money(non_negative(value, field))

    inflows = optional_money(cash_inflows, "cash_inflows")
    outflows = optional_money(cash_outflows, "cash_outflows")
    opening = optional_money(opening_cash, "opening_cash")
    assets = optional_money(current_assets, "current_assets")
    liabilities = optional_money(current_liabilities, "current_liabilities")

    revenue = (units * price).quantize(MONEY, rounding=ROUND_HALF_UP)
    variable_cost = (units * variable_unit).quantize(MONEY, rounding=ROUND_HALF_UP)
    gross_profit = revenue - variable_cost
    operating_result = gross_profit - fixed
    contribution = price - variable_unit
    gross_margin = ((gross_profit / revenue) * 100).quantize(RATIO, rounding=ROUND_HALF_UP) if revenue else Decimal("0")
    if contribution > 0:
        break_even_units = (fixed / contribution).quantize(RATIO, rounding=ROUND_HALF_UP)
        break_even_revenue = (break_even_units * price).quantize(MONEY, rounding=ROUND_HALF_UP)
    else:
        break_even_units = None
        break_even_revenue = None
    roi = ((operating_result / invested) * 100).quantize(RATIO, rounding=ROUND_HALF_UP) if invested else None
    cash_flow = (inflows - outflows) if inflows is not None and outflows is not None else None
    ending_cash = (opening + cash_flow) if opening is not None and cash_flow is not None else None
    working_capital = (assets - liabilities) if assets is not None and liabilities is not None else None
    return FinancialSnapshot(
        units_sold=units, revenue=revenue, variable_cost=variable_cost, cogs=variable_cost,
        fixed_cost=fixed, gross_profit=gross_profit, operating_result=operating_result,
        contribution_per_unit=contribution, contribution_margin=gross_profit,
        gross_margin_pct=gross_margin, contribution_margin_pct=gross_margin,
        break_even_units=break_even_units, break_even_revenue=break_even_revenue, roi=roi,
        cash_flow=cash_flow, ending_cash=ending_cash, working_capital=working_capital,
    )


def summarize_explicit_financials(
    *,
    revenue: Any,
    cost_lines: list[dict[str, Any]],
    units_sold: Any | None = None,
    unit_price: Any | None = None,
    unit_variable_cost: Any | None = None,
    investment: Any | None = None,
    cash_inflows: Any | None = None,
    cash_outflows: Any | None = None,
    opening_cash: Any | None = None,
    current_assets: Any | None = None,
    current_liabilities: Any | None = None,
) -> dict[str, Any]:
    """Summarize simulated money only when every cost has an explicit class.

    ``VARIABLE``, ``COGS`` and ``FIXED`` are the only accepted classes.
    An unclassified line keeps total revenue/cost visible but prevents gross
    margin and operating-result claims.
    """
    revenue_amount = money(non_negative(revenue, "revenue"))
    total_cost = Decimal("0.00")
    variable_cost = Decimal("0.00")
    cogs = Decimal("0.00")
    fixed_cost = Decimal("0.00")
    missing: list[str] = []
    for line in cost_lines:
        line_id = str(line.get("id", "cost"))
        amount = money(non_negative(line.get("amount", 0), line_id))
        total_cost += amount
        classification = str(line.get("classification", "")).upper()
        if classification in {"VARIABLE", "COGS"}:
            variable_cost += amount
            if classification == "COGS":
                cogs += amount
        elif classification == "FIXED":
            fixed_cost += amount
        else:
            missing.append(line_id)
    summary: dict[str, Any] = {
        "status": "complete" if not missing else "incomplete",
        "revenue": format(revenue_amount, "f"),
        "total_cost": format(total_cost, "f"),
        "currency": "declared_by_model",
    }
    if missing:
        summary["missing"] = [f"costs[{line_id}].classification" for line_id in missing]
        return summary
    gross_profit = revenue_amount - (cogs if cogs else variable_cost)
    contribution_amount = revenue_amount - variable_cost
    operating_result = contribution_amount - fixed_cost
    gross_margin = ((gross_profit / revenue_amount) * 100).quantize(RATIO, rounding=ROUND_HALF_UP) if revenue_amount else Decimal("0")
    contribution_margin = ((contribution_amount / revenue_amount) * 100).quantize(RATIO, rounding=ROUND_HALF_UP) if revenue_amount else Decimal("0")
    summary.update({
        "variable_cost": format(variable_cost, "f"),
        "cogs": format(cogs if cogs else variable_cost, "f"),
        "fixed_cost": format(fixed_cost, "f"),
        "gross_profit": format(gross_profit, "f"),
        "operating_result": format(operating_result, "f"),
        "contribution_margin": format(contribution_amount, "f"),
        "gross_margin_pct": format(gross_margin, "f"),
        "contribution_margin_pct": format(contribution_margin, "f"),
    })

    unit_inputs = (units_sold, unit_price, unit_variable_cost)
    if any(value is not None for value in unit_inputs):
        if any(value is None for value in unit_inputs):
            summary["missing"] = [
                f"financial.{field}"
                for field, value in zip(("units_sold", "unit_price", "unit_variable_cost"), unit_inputs)
                if value is None
            ]
            summary["status"] = "incomplete"
            return summary
        units = non_negative(units_sold, "units_sold")
        price = non_negative(unit_price, "unit_price")
        variable_unit = non_negative(unit_variable_cost, "unit_variable_cost")
        expected_revenue = (units * price).quantize(MONEY, rounding=ROUND_HALF_UP)
        expected_variable = (units * variable_unit).quantize(MONEY, rounding=ROUND_HALF_UP)
        if expected_revenue != revenue_amount or expected_variable != variable_cost:
            raise ValueError("financial.unit_* no coincide con ingresos o costos variables declarados.")
        contribution_per_unit = price - variable_unit
        summary["contribution_per_unit"] = format(contribution_per_unit, "f")
        if contribution_per_unit > 0:
            break_even_units = (fixed_cost / contribution_per_unit).quantize(RATIO, rounding=ROUND_HALF_UP)
            summary["break_even_units"] = format(break_even_units, "f")
            summary["break_even_revenue"] = format((break_even_units * price).quantize(MONEY, rounding=ROUND_HALF_UP), "f")
        else:
            summary["break_even_units"] = None
            summary["break_even_revenue"] = None

    if investment is not None:
        invested = money(non_negative(investment, "investment"))
        summary["roi"] = format(((operating_result / invested) * 100).quantize(RATIO, rounding=ROUND_HALF_UP), "f") if invested else None
    if cash_inflows is not None or cash_outflows is not None:
        if cash_inflows is None or cash_outflows is None:
            summary["missing"] = [
                f"financial.{field}"
                for field, value in (("cash_inflows", cash_inflows), ("cash_outflows", cash_outflows))
                if value is None
            ]
            summary["status"] = "incomplete"
            return summary
        inflows = money(non_negative(cash_inflows, "cash_inflows"))
        outflows = money(non_negative(cash_outflows, "cash_outflows"))
        cash_flow = inflows - outflows
        summary["cash_flow"] = format(cash_flow, "f")
        if opening_cash is not None:
            summary["ending_cash"] = format(money(opening_cash) + cash_flow, "f")
    elif opening_cash is not None:
        summary["missing"] = ["financial.cash_inflows", "financial.cash_outflows"]
        summary["status"] = "incomplete"
        return summary
    if current_assets is not None or current_liabilities is not None:
        if current_assets is None or current_liabilities is None:
            summary["missing"] = [
                f"financial.{field}"
                for field, value in (("current_assets", current_assets), ("current_liabilities", current_liabilities))
                if value is None
            ]
            summary["status"] = "incomplete"
            return summary
        summary["working_capital"] = format(
            money(non_negative(current_assets, "current_assets")) - money(non_negative(current_liabilities, "current_liabilities")), "f"
        )
    return summary
