"""Minimal dimensional unit registry for model validation and conversion."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import ast


class UnitError(ValueError):
    pass


@dataclass(frozen=True)
class Unit:
    symbol: str
    dimension: str
    factor: Decimal = Decimal("1")


UNITS = {
    "1": Unit("1", "dimensionless"),
    "%": Unit("%", "dimensionless", Decimal("0.01")),
    "Bs": Unit("Bs", "currency"),
    "USD": Unit("USD", "currency"),
    "unit": Unit("unit", "count"),
    "person": Unit("person", "count"),
    "machine": Unit("machine", "count"),
    "kg": Unit("kg", "mass"),
    "g": Unit("g", "mass", Decimal("0.001")),
    "liter": Unit("liter", "volume"),
    "ml": Unit("ml", "volume", Decimal("0.001")),
    "minute": Unit("minute", "time"),
    "hour": Unit("hour", "time", Decimal("60")),
    "day": Unit("day", "time", Decimal("1440")),
}


def unit(symbol: str | None) -> Unit:
    if not symbol:
        return UNITS["1"]
    try:
        return UNITS[symbol]
    except KeyError as exc:
        raise UnitError(f"Unidad no soportada: {symbol}.") from exc


def compatible(left: str | None, right: str | None) -> bool:
    return unit(left).dimension == unit(right).dimension


def convert(value: int | float | Decimal, source: str, target: str) -> Decimal:
    source_unit, target_unit = unit(source), unit(target)
    if source_unit.dimension != target_unit.dimension:
        raise UnitError(f"No se puede convertir {source} a {target}.")
    return Decimal(str(value)) * source_unit.factor / target_unit.factor


def infer_expression_dimension(expression: str, symbols: dict[str, str | None]) -> str:
    """Infer the coarse dimension of a safe model expression.

    Counts are treated as neutral for business arithmetic (e.g. Bs/unit * unit
    produces Bs). Addition and subtraction still require compatible dimensions.
    Composite dimensions are intentionally rejected when a declared output unit
    cannot represent them; this keeps the DSL conservative without pretending
    to be a full scientific unit algebra system.
    """
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise UnitError(f"Expresión inválida para unidades: {exc.msg}.") from exc

    def dimension(node: ast.AST) -> str:
        if isinstance(node, ast.Constant):
            return "dimensionless"
        if isinstance(node, ast.Name):
            if node.id not in symbols:
                raise UnitError(f"Unidad no definida para {node.id}.")
            result = unit(symbols[node.id]).dimension
            return "dimensionless" if result == "count" else result
        if isinstance(node, ast.UnaryOp):
            return dimension(node.operand)
        if isinstance(node, ast.BinOp):
            left, right = dimension(node.left), dimension(node.right)
            if isinstance(node.op, (ast.Add, ast.Sub, ast.Mod)):
                if left != right and left != "dimensionless" and right != "dimensionless":
                    raise UnitError(f"No se pueden combinar unidades {left} y {right}.")
                return right if left == "dimensionless" else left
            if isinstance(node.op, ast.Div):
                if right == "dimensionless":
                    return left
                if left == right:
                    return "dimensionless"
                return "composite"
            if isinstance(node.op, ast.Mult):
                if left == "dimensionless": return right
                if right == "dimensionless": return left
                if left == right: return "composite"
                return "composite"
            if isinstance(node.op, ast.Pow):
                return left if right == "dimensionless" else "composite"
        if isinstance(node, ast.Compare):
            dimension(node.left)
            for comparator in node.comparators:
                dimension(comparator)
            return "dimensionless"
        if isinstance(node, ast.IfExp):
            left, right = dimension(node.body), dimension(node.orelse)
            if left != right and left != "dimensionless" and right != "dimensionless":
                raise UnitError(f"Las ramas condicionales usan unidades {left} y {right}.")
            return right if left == "dimensionless" else left
        if isinstance(node, ast.Call):
            args = [dimension(arg) for arg in node.args]
            if node.func.id in {"min", "max", "abs", "round", "fabs"}:
                concrete = {item for item in args if item != "dimensionless"}
                if len(concrete) > 1:
                    raise UnitError("Una función combina dimensiones incompatibles.")
                return next(iter(concrete), "dimensionless")
            if node.func.id in {"sqrt", "exp", "log", "log10", "ceil", "floor"}:
                return args[0] if node.func.id in {"sqrt", "ceil", "floor"} and args else "dimensionless"
        raise UnitError("No se pudo inferir la unidad de la expresión.")

    return dimension(tree.body)
