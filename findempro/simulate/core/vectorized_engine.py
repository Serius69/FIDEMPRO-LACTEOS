"""
vectorized_engine.py
====================
Motor Monte Carlo **vectorizado** (CPU NumPy / GPU CuPy) para el modelo de
ecuaciones de ``DiscreteEventEngine``.

Motivación
----------
El pipeline clásico (``simulation_service``) ejecuta un bucle Python
``for período: for escenario: engine.run_period(...)`` — es decir T×N
evaluaciones objeto-por-objeto (hasta millones de iteraciones del intérprete).
Como cada escenario se corre con ``reset_state()`` (ver comentario
"stateless-per-scenario" en ``simulation_service``), **cada celda (período,
escenario) es independiente**: no hay carryover de estado entre ellas.

Eso permite reemplazar el bucle por operaciones de array sobre toda la grilla
T×N a la vez, evaluando las MISMAS ecuaciones con variables array-valuadas.
En CPU esto ya elimina el overhead del intérprete; en GPU (CuPy) además paraleliza
el muestreo y la aritmética (~70× a N=100k en una RTX 5070 Ti).

Seguridad / correctitud
-----------------------
· ``can_vectorize()`` valida numéricamente la ruta vectorizada contra el motor
  escalar sobre una micro-grilla antes de usarla. Si diverge o alguna ecuación
  no es vectorizable (construcciones no aritméticas, división por cero, etc.),
  el llamador debe caer al motor escalar.
· La semántica de la tabla de variables replica ``DiscreteEventEngine.
  _build_variable_table`` en estado reseteado (``_demand_history`` vacío).
"""

from __future__ import annotations

import ast
import logging
import warnings
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from modeling.safe_expression import ExpressionError

from simulate.core.discrete_engine import (
    CompanyConfig,
    DiscreteEventEngine,
    OperationScenario,
    _extract_rhs_dependencies,
    _get_lhs,
    _preprocess_rhs,
    _topological_sort,
)
from simulate.core.gbm import simular_gbm_grid
from simulate.core.gpu_backend import (
    asnumpy,
    backend_name,
    build_safe_namespace,
    get_array_module,
    make_generator,
)
from simulate.core.monte_carlo import MonteCarloConfig

logger = logging.getLogger(__name__)


def _evaluate_vector_expression(expression: str, values: Dict[str, Any], namespace: Dict[str, Any]) -> Any:
    """Evaluate an array expression and reject every invalid numeric domain."""
    tree = ast.parse(expression, mode="eval")
    allowed = set(values) | set(namespace)

    def finite(value: Any) -> Any:
        try:
            host = asnumpy(value)
        except (TypeError, ValueError) as exc:
            raise ExpressionError("El resultado vectorizado no es numérico.") from exc
        if not np.all(np.isfinite(host)) or np.any(np.abs(host) > 1e100):
            raise ExpressionError(
                "El resultado vectorizado no es finito o excede el límite operativo."
            )
        return value

    def contains_zero(value: Any) -> bool:
        return bool(np.any(asnumpy(value) == 0))

    def visit(node: ast.AST) -> Any:
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return finite(node.value)
        if isinstance(node, ast.Name) and node.id in allowed:
            value = values[node.id] if node.id in values else namespace[node.id]
            return value if callable(value) or isinstance(value, dict) else finite(value)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            value = visit(node.operand)
            return finite(-value if isinstance(node.op, ast.USub) else value)
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod)):
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Add): return finite(left + right)
            if isinstance(node.op, ast.Sub): return finite(left - right)
            if isinstance(node.op, ast.Mult): return finite(left * right)
            if isinstance(node.op, ast.Div):
                if contains_zero(right):
                    raise ExpressionError("División por cero en expresión vectorizada.")
                return finite(left / right)
            if isinstance(node.op, ast.Pow):
                if bool(np.any(np.abs(asnumpy(right)) > 20)):
                    raise ExpressionError("Exponente fuera de rango.")
                return finite(left ** right)
            if contains_zero(right):
                raise ExpressionError("Módulo por cero en expresión vectorizada.")
            return finite(left % right)
        if isinstance(node, ast.Compare) and len(node.ops) == 1:
            left, right = visit(node.left), visit(node.comparators[0])
            op = node.ops[0]
            if isinstance(op, ast.Gt): return left > right
            if isinstance(op, ast.GtE): return left >= right
            if isinstance(op, ast.Lt): return left < right
            if isinstance(op, ast.LtE): return left <= right
            if isinstance(op, ast.Eq): return left == right
            if isinstance(op, ast.NotEq): return left != right
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in namespace:
            return finite(namespace[node.func.id](*(visit(arg) for arg in node.args)))
        raise ValueError(f"Vector expression node not allowed: {type(node).__name__}")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            return finite(visit(tree))
    except RuntimeWarning as exc:
        raise ExpressionError("La expresión vectorizada produjo un error numérico.") from exc
    except (ArithmeticError, OverflowError) as exc:
        raise ExpressionError("La expresión vectorizada produjo un error numérico.") from exc


# ── Muestreo de demanda vectorizado ──────────────────────────────────────────

def _sample_demand_grid(mc: MonteCarloConfig, T: int, N: int, xp: Any, rng: Any) -> Any:
    """
    Muestrea una grilla (T, N) de demanda no-negativa según ``mc.distribution``.

    Usa el RNG del backend activo (CuPy o NumPy). Para distribuciones que un
    backend no soporte nativamente, muestrea en NumPy y transfiere.
    """
    shape = (T, N)
    dist = mc.distribution.lower()
    mu = float(mc.demand_mean)
    sigma = max(float(mc.demand_std), 1e-6)

    try:
        if dist == "normal":
            out = rng.normal(mu, sigma, size=shape)
        elif dist == "lognormal":
            mu_pos = abs(mu) + 1 if mu <= 0 else mu
            cv2 = (sigma / mu_pos) ** 2
            s = float(np.sqrt(np.log(1 + cv2)))
            scale = float(np.exp(np.log(mu_pos) - s ** 2 / 2))
            out = rng.lognormal(mean=float(np.log(max(scale, 1e-6))), sigma=max(s, 1e-6), size=shape)
        elif dist == "gamma":
            shape_k = max((mu / sigma) ** 2, 0.01)
            scale = max(sigma ** 2 / max(mu, 1e-6), 0.01)
            out = rng.gamma(shape_k, scale, size=shape)
        elif dist == "uniform":
            low = mc.demand_min if mc.demand_min is not None else mu - 3 * sigma
            high = mc.demand_max if mc.demand_max is not None else mu + 3 * sigma
            low, high = min(low, high - 1), max(low + 1, high)
            out = rng.uniform(low, high, size=shape)
        elif dist == "exponential":
            out = rng.exponential(max(mu, 1e-6), size=shape)
        elif dist == "poisson":
            out = rng.poisson(max(abs(mu), 0.1), size=shape).astype(xp.float64)
        elif dist == "gbm":
            # GBM: trayectorias con memoria (cumsum sobre el eje de períodos),
            # no draws i.i.d. Cada columna n es un path coherente sobre los T
            # períodos. Usa el mismo xp/rng del backend activo (CPU o GPU).
            s0, media_d, sigma_d = mc.resolve_gbm_params()
            out = simular_gbm_grid(s0, media_d, sigma_d, T, N, xp=xp, rng=rng)
        else:
            raise ValueError(f"distribución no soportada: {dist}")
    except (AttributeError, TypeError, NotImplementedError):
        # El backend GPU no implementa esta distribución → muestreo en CPU y transferencia.
        cpu_rng = np.random.default_rng(mc.random_seed)
        out = xp.asarray(_sample_demand_grid(mc, T, N, np, cpu_rng))

    return xp.maximum(xp.asarray(out, dtype=xp.float64), 0.0)


# ── Construcción de la tabla de variables vectorizada ────────────────────────

def _build_vectorized_table(
    company: CompanyConfig,
    exogenous: Dict[str, float],
    demand_grid: Any,          # (T, N) — demanda ya con estacionalidad aplicada
    period_index_col: Any,     # (T, 1) — DIA por período
    xp: Any,
    demand_std: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Replica ``DiscreteEventEngine._build_variable_table`` en estado reseteado,
    pero con la variable de demanda como array (T, N) y el resto broadcast.
    """
    table: Dict[str, Any] = {}
    table.update({k: float(v) for k, v in company.system_constants.items()})
    table.update({k: float(v) for k, v in company.initial_state.items()})
    table.update({k: float(v) for k, v in exogenous.items()})

    table["DIA"] = period_index_col               # (T,1) broadcast sobre N
    table["NMD"] = float(company.total_periods)

    demand = xp.maximum(demand_grid, 0.0)
    table[company.demand_variable] = demand
    # Estado reseteado ⇒ _demand_history vacío ⇒ DPH = demanda del período.
    table["DPH"] = demand
    configured_std = demand_std if demand_std is not None else exogenous.get('DSD')
    if configured_std is not None:
        if isinstance(configured_std, bool):
            raise ValueError("La desviación de demanda debe ser numérica y no negativa.")
        configured_std = float(configured_std)
        if not np.isfinite(configured_std) or configured_std < 0:
            raise ValueError("La desviación de demanda debe ser finita y no negativa.")
        table["DSD"] = configured_std
        table["CVD"] = configured_std / xp.maximum(xp.abs(demand), 1.0)
    else:
        table.pop("DSD", None)
        table.pop("CVD", None)
    return table


class _TernaryToWhere(ast.NodeTransformer):
    """Reescribe cada ``A if C else B`` (ast.IfExp) como ``where(C, A, B)``."""

    def visit_IfExp(self, node: ast.IfExp) -> ast.AST:  # noqa: N802
        self.generic_visit(node)
        return ast.Call(
            func=ast.Name(id="where", ctx=ast.Load()),
            args=[node.test, node.body, node.orelse],
            keywords=[],
        )


def _rewrite_ternaries_to_where(expr: str) -> str:
    """Convierte ternarios Python en llamadas ``where`` para evaluación array-wise.

    El motor escalar evalúa ``A if C else B`` con el ternario nativo (C es un
    bool). En modo vectorizado C es un array booleano y el ternario nativo lanza
    "truth value of an array is ambiguous", lo que hacía que ``can_vectorize``
    descartara cualquier ecuación con ``if/else`` y cayera al motor escalar
    (lentísimo). ``where(C, A, B)`` (element-wise, en ``build_safe_namespace``) es
    numéricamente equivalente por celda — ``can_vectorize`` lo valida contra el
    escalar antes de usarse. Ante cualquier fallo de parseo se devuelve la
    expresión intacta (el guard hará el fallback seguro).
    """
    if " if " not in expr or " else " not in expr:
        return expr
    try:
        tree = ast.parse(expr, mode="eval")
        _TernaryToWhere().visit(tree)
        ast.fix_missing_locations(tree)
        return ast.unparse(tree)
    except (SyntaxError, ValueError):
        return expr


def _solve_vectorized(
    company: CompanyConfig,
    table: Dict[str, Any],
    xp: Any,
) -> Dict[str, Any]:
    """
    Resuelve las ecuaciones en orden topológico con variables array-valuadas.

    Evalúa cada RHS con ``eval`` usando el namespace vectorizado seguro. Hasta
    3 pasadas (idéntico al motor escalar) para dependencias encadenadas.
    """
    safe_ns = build_safe_namespace(xp)
    sorted_eqs = _topological_sort([e for e in company.equations if _get_lhs(e.expression)])
    results: Dict[str, Any] = {}

    def _attempt() -> int:
        solved = 0
        for eq in sorted_eqs:
            lhs = _get_lhs(eq.expression)
            if not lhs or lhs in results:
                continue
            _, rhs = eq.expression.split("=", 1)
            combined = {**table, **results}
            deps = _extract_rhs_dependencies(eq.expression)
            if not all(d in combined for d in deps):
                continue
            expr = _rewrite_ternaries_to_where(_preprocess_rhs(rhs))
            value = _evaluate_vector_expression(expr, combined, safe_ns)
            results[lhs] = value
            solved += 1
        return solved

    _attempt()
    for _ in range(2):
        if _attempt() == 0:
            break
    return results


class VectorizedMonteCarlo:
    """
    Ejecuta la grilla T×N de la simulación con operaciones de array.

    Devuelve arrays planos (host / NumPy) de demanda, ingresos, costos y ganancia
    — compatibles con ``monte_carlo.aggregate_results`` y ``DecisionEngine``.
    """

    def __init__(
        self,
        mc_config: MonteCarloConfig,
        company_config: CompanyConfig,
        exogenous: Optional[Dict[str, float]] = None,
    ):
        self.mc = mc_config
        self.company = company_config
        self.exogenous = exogenous or {}

    def run(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Devuelve (demanda, ingreso, costo, ganancia) como vectores planos T·N (host)."""
        d, r, c, p = self.run_grid()
        return d.reshape(-1), r.reshape(-1), c.reshape(-1), p.reshape(-1)

    def run_grid(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Igual que ``run()`` pero devuelve arrays con forma (T, N) — útil para
        calcular estadísticos por período sin re-simular.
        """
        xp = get_array_module()
        T = int(self.company.total_periods or self.mc.n_periods)
        N = int(self.mc.n_scenarios)
        rng = make_generator(self.mc.random_seed)

        # 1. Demanda (T,N) + estacionalidad por período
        raw = _sample_demand_grid(self.mc, T, N, xp, rng)
        factors = self.mc.seasonality_factors or [1.0] * 12
        # Mapeo día → mes idéntico al motor escalar (ScenarioGenerator._get_seasonality):
        # el período t es un DÍA; los factores son mensuales (×30 días/mes), se envuelve
        # por año. Antes ``t % len(factors)`` comprimía el año a un ciclo de 12 días.
        seasonal_col = xp.asarray(
            [factors[(t // 30) % len(factors)] for t in range(T)], dtype=xp.float64
        ).reshape(T, 1)
        demand_grid = raw * seasonal_col

        # 2. Tabla de variables + solve vectorizado
        dia_col = xp.asarray([float(t + 1) for t in range(T)], dtype=xp.float64).reshape(T, 1)
        table = _build_vectorized_table(
            self.company,
            self.exogenous,
            demand_grid,
            dia_col,
            xp,
            demand_std=self.mc.demand_std,
        )
        results = _solve_vectorized(self.company, table, xp)

        combined = {**table, **results}

        # 3. Extraer métricas financieras (mismo criterio que _extract_financials)
        def _grid(name: str, default: Any) -> Any:
            v = combined.get(name, default)
            arr = xp.asarray(v, dtype=xp.float64)
            if arr.ndim == 0:
                return xp.full((T, N), float(arr))
            return xp.broadcast_to(arr, (T, N))

        demand = _grid(self.company.demand_variable, 0.0)
        revenue = _grid(self.company.revenue_variable, 0.0)
        costs = _grid(self.company.cost_variable, 0.0)
        profit_var = combined.get(self.company.profit_variable)
        if profit_var is None:
            profit = revenue - costs
        else:
            profit = _grid(self.company.profit_variable, 0.0)

        # 4. Devolver en host con forma (T,N), rechazando resultados inválidos.
        def _grid_host(a: Any) -> np.ndarray:
            out = asnumpy(xp.broadcast_to(a, (T, N)))
            if not np.all(np.isfinite(out)) or np.any(np.abs(out) > 1e100):
                raise ExpressionError(
                    "La simulación vectorizada produjo un resultado financiero inválido."
                )
            return out

        logger.info(
            "[MC vectorizado] backend=%s T=%d N=%d (%d celdas)",
            backend_name(), T, N, T * N,
        )
        return _grid_host(demand), _grid_host(revenue), _grid_host(costs), _grid_host(profit)


# ── Guard de compatibilidad numérica ─────────────────────────────────────────

def can_vectorize(
    company: CompanyConfig,
    exogenous: Optional[Dict[str, float]] = None,
    demand_std: Optional[float] = None,
    rtol: float = 1e-6,
    atol: float = 1e-3,
) -> bool:
    """
    Verifica que el motor vectorizado reproduce al escalar en una micro-grilla.

    Ejecuta ambos motores sobre los mismos escenarios deterministas (demandas
    fijas) y compara demanda/ingreso/costo/ganancia. Devuelve ``False`` ante
    cualquier error o divergencia → el llamador usa el motor escalar.
    """
    exo = exogenous or {}
    try:
        xp = get_array_module()
        # Demandas de prueba deterministas (evita depender del muestreo del backend).
        test_demands = [500.0, 1000.0, 1500.0, 2000.0]
        T, N = 1, len(test_demands)

        demand_grid = xp.asarray(test_demands, dtype=xp.float64).reshape(T, N)
        dia_col = xp.asarray([1.0]).reshape(T, 1)
        reference_std = demand_std if demand_std is not None else exo.get('DSD')
        table = _build_vectorized_table(
            company, exo, demand_grid, dia_col, xp, demand_std=reference_std
        )
        vres = _solve_vectorized(company, table, xp)
        vcomb = {**table, **vres}

        def _vec_scalar(name: str, default: float, idx: int) -> float:
            v = vcomb.get(name, default)
            arr = asnumpy(xp.asarray(v, dtype=xp.float64))
            return float(arr.reshape(-1)[idx]) if arr.ndim else float(arr)

        # Motor escalar de referencia
        engine = DiscreteEventEngine(company)
        for i, d in enumerate(test_demands):
            engine.reset_state()
            res = engine.run_period(
                OperationScenario(
                    period_index=0,
                    demand_value=d,
                    seasonality_factor=1.0,
                    demand_std=reference_std,
                    demand_std_source=(
                        'EXPLICIT_EXOGENOUS' if reference_std is not None else None
                    ),
                ),
                exo,
            )
            for name, sval in (
                (company.demand_variable, res.demand),
                (company.revenue_variable, res.revenue),
                (company.cost_variable, res.costs),
                (company.profit_variable, res.profit),
            ):
                vv = _vec_scalar(name, 0.0, i)
                if not np.isclose(vv, float(sval), rtol=rtol, atol=atol):
                    logger.info(
                        "[MC vectorizado] descartado: %s difiere (vec=%.4f vs escalar=%.4f). "
                        "Se usará el motor escalar.", name, vv, float(sval),
                    )
                    return False
        return True
    except Exception as exc:
        logger.info("[MC vectorizado] no aplicable (%s). Se usará el motor escalar.", exc)
        return False
