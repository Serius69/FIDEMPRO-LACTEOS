"""Small allow-listed expression language; never executes user Python."""

from __future__ import annotations

import ast
import math
from typing import Any, Mapping

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class ExpressionError(ValueError):
    pass


def _safe_pow(base: float, exponent: float) -> float:
    if abs(exponent) > 20:
        raise ExpressionError("Exponente fuera de rango.")
    return base ** exponent


FUNCTIONS = {name: getattr(math, name) for name in ("ceil", "floor", "sqrt", "exp", "log", "log10", "fabs")}
FUNCTIONS.update({"min": min, "max": max, "abs": abs, "round": round, "pow": _safe_pow, "pi": math.pi, "E": math.e})
ALLOWED_NODES = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.USub, ast.UAdd, ast.Constant, ast.Name, ast.Call, ast.Load, ast.Compare, ast.Gt, ast.GtE, ast.Lt, ast.LtE, ast.Eq, ast.NotEq, ast.IfExp)
DEFAULT_MAX_EXPRESSION_LENGTH = 500
DEFAULT_MAX_EXPRESSION_NODES = 200
DEFAULT_MAX_EXPRESSION_DEPTH = 40


def _configured_limit(name: str, default: int) -> int:
    try:
        value = int(getattr(settings, name, default))
    except (ImproperlyConfigured, TypeError, ValueError):
        return default
    return max(1, value)


def _depth(tree: ast.AST) -> int:
    maximum = 0
    stack = [(tree, 1)]
    while stack:
        node, depth = stack.pop()
        maximum = max(maximum, depth)
        stack.extend((child, depth + 1) for child in ast.iter_child_nodes(node))
    return maximum


def _tree(expression: str) -> ast.Expression:
    if not isinstance(expression, str) or not expression.strip():
        raise ExpressionError("La expresión no puede estar vacía.")
    max_length = _configured_limit("MODELING_MAX_EXPRESSION_LENGTH", DEFAULT_MAX_EXPRESSION_LENGTH)
    if len(expression) > max_length:
        raise ExpressionError(f"La expresión excede el límite de longitud ({max_length} caracteres).")
    try:
        tree = ast.parse(expression, mode="eval")
    except (SyntaxError, ValueError, RecursionError, MemoryError) as exc:
        if not isinstance(exc, SyntaxError):
            raise ExpressionError("La expresión no puede analizarse de forma segura.") from exc
        raise ExpressionError(f"Sintaxis inválida: {exc.msg}.") from exc
    nodes = list(ast.walk(tree))
    max_nodes = _configured_limit("MODELING_MAX_EXPRESSION_NODES", DEFAULT_MAX_EXPRESSION_NODES)
    if len(nodes) > max_nodes:
        raise ExpressionError(f"La expresión excede el límite estructural ({max_nodes} nodos).")
    max_depth = _configured_limit("MODELING_MAX_EXPRESSION_DEPTH", DEFAULT_MAX_EXPRESSION_DEPTH)
    if _depth(tree) > max_depth:
        raise ExpressionError(f"La expresión excede la profundidad permitida ({max_depth} niveles).")
    for node in nodes:
        if not isinstance(node, ALLOWED_NODES):
            raise ExpressionError(f"Operación no permitida: {type(node).__name__}.")
        if isinstance(node, ast.Constant) and not isinstance(node.value, (int, float)):
            raise ExpressionError("Solo se permiten constantes numéricas.")
        if isinstance(node, ast.Name) and node.id.startswith("__"):
            raise ExpressionError("Nombres privados no permitidos.")
    return tree


def _validate_names(tree: ast.Expression, allowed_names: set[str] | None) -> set[str]:
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    allowed = set(allowed_names or set()) | set(FUNCTIONS)
    unknown = names - allowed
    if unknown:
        raise ExpressionError("Variables no definidas: " + ", ".join(sorted(unknown)))
    return names - set(FUNCTIONS)


def validate_expression(expression: str, *, allowed_names: set[str] | None = None) -> set[str]:
    tree = _tree(expression)
    return _validate_names(tree, allowed_names)


def evaluate_expression(expression: str, values: Mapping[str, float]) -> float:
    tree = _tree(expression)
    _validate_names(tree, set(values))

    def evaluate(node: ast.AST) -> Any:
        if isinstance(node, ast.Expression): return evaluate(node.body)
        if isinstance(node, ast.Constant): return node.value
        if isinstance(node, ast.Name):
            if node.id in values:
                return values[node.id]
            value = FUNCTIONS.get(node.id)
            if isinstance(value, (int, float)):
                return value
            raise ExpressionError(f"Variable no evaluable: {node.id}.")
        if isinstance(node, ast.UnaryOp):
            value = evaluate(node.operand)
            return -value if isinstance(node.op, ast.USub) else value
        if isinstance(node, ast.BinOp):
            left, right = evaluate(node.left), evaluate(node.right)
            if isinstance(node.op, ast.Add): return left + right
            if isinstance(node.op, ast.Sub): return left - right
            if isinstance(node.op, ast.Mult): return left * right
            if isinstance(node.op, ast.Div):
                if right == 0: raise ExpressionError("División por cero.")
                return left / right
            if isinstance(node.op, ast.Pow):
                if abs(right) > 20: raise ExpressionError("Exponente fuera de rango.")
                return left ** right
            if isinstance(node.op, ast.Mod): return left % right
        if isinstance(node, ast.Compare):
            left = evaluate(node.left)
            for operator, comparator in zip(node.ops, node.comparators):
                right = evaluate(comparator)
                if isinstance(operator, ast.Gt): ok = left > right
                elif isinstance(operator, ast.GtE): ok = left >= right
                elif isinstance(operator, ast.Lt): ok = left < right
                elif isinstance(operator, ast.LtE): ok = left <= right
                elif isinstance(operator, ast.Eq): ok = left == right
                elif isinstance(operator, ast.NotEq): ok = left != right
                else: raise ExpressionError("Comparación no permitida.")
                if not ok: return False
                left = right
            return True
        if isinstance(node, ast.IfExp): return evaluate(node.body if evaluate(node.test) else node.orelse)
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in FUNCTIONS:
                raise ExpressionError("Función no permitida.")
            return FUNCTIONS[node.func.id](*(evaluate(arg) for arg in node.args))
        raise ExpressionError(f"Nodo no evaluable: {type(node).__name__}.")

    try:
        result = evaluate(tree)
    except ExpressionError:
        raise
    except (ArithmeticError, ValueError, RecursionError, MemoryError) as exc:
        raise ExpressionError("La expresión excede los límites numéricos permitidos.") from exc
    if not isinstance(result, (int, float)) or not math.isfinite(float(result)):
        raise ExpressionError("El resultado no es un número finito.")
    return float(result)
