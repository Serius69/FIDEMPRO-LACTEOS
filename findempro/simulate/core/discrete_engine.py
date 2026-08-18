"""
discrete_engine.py
==================
Motor de eventos discretos GENÉRICO para PyMEs multi-sector.

Diseño:
  - CompanyConfig   : estructura de la empresa (capacidad, costos, ecuaciones, estado inicial)
  - OperationScenario : condiciones externas para un período (demanda, precios, estacionalidad)
  - DiscreteEventEngine : resuelve ecuaciones en orden topológico, lleva estado entre períodos
  - simular_operacion() : función pública de alto nivel

No tiene lógica hardcodeada para ningún sector específico.
Toda la lógica de negocio vive en las ecuaciones almacenadas en BD o pasadas en config.
"""

from __future__ import annotations

import logging
import math
import re
from collections import deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Deque, Dict, List, Optional, Set, Tuple

if TYPE_CHECKING:
    from business.models import CompanyProfile

import numpy as np

from modeling.safe_expression import ExpressionError, evaluate_expression

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Estructuras de datos
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CompanyConfig:
    """
    Configuración genérica de empresa para el motor de eventos discretos.

    Sector-agnóstica: sirve para lácteos, retail, servicios, manufactura, etc.
    Los defaults de sector deben cargarse desde CompanyProfile antes de instanciar.
    """
    # Identificación del sector (para logging y defaults mínimos)
    sector: str = 'other'
    business_name: str = 'Empresa'

    # Nombres de variables clave en el modelo (configurables por sector)
    demand_variable: str = 'DE'         # Variable de demanda del día
    revenue_variable: str = 'IT'        # Variable de ingresos
    cost_variable: str = 'TG'           # Variable de gastos totales
    profit_variable: str = 'GT'         # Variable de ganancia

    # Estado inicial de variables de estado (inventarios, stocks, etc.)
    # Cargado desde el cuestionario o CompanyProfile — NO hardcodeado aquí.
    initial_state: Dict[str, float] = field(default_factory=dict)

    # Ecuaciones a resolver cada período (objetos Equation del ORM o mock compatibles)
    # Cada ecuación debe tener atributo .expression (str "LHS=RHS") y .fk_area.name (str)
    equations: List[Any] = field(default_factory=list)

    # Orden de áreas para resolver ecuaciones (influye en qué se calcula primero)
    # Si está vacío, se usa orden topológico puro.
    area_priority: List[str] = field(default_factory=list)

    # Umbrales de alerta financiera (del CompanyProfile)
    min_profit_margin_pct: float = 10.0
    max_cost_revenue_ratio: float = 70.0

    # Constantes del sistema disponibles siempre (nombre → valor)
    system_constants: Dict[str, float] = field(default_factory=dict)

    # Número total de períodos de la simulación
    total_periods: int = 30


@dataclass
class OperationScenario:
    """
    Condiciones externas para UN período de la simulación.

    Generado por el motor Monte Carlo o definido manualmente.
    """
    period_index: int = 0

    # Demanda del período (generada por Monte Carlo)
    demand_value: float = 1000.0

    # Factores externos
    seasonality_factor: float = 1.0   # Multiplicador estacional
    price_variation: float = 0.0      # Variación de precio respecto al base (%)
    cost_variation: float = 0.0       # Variación de costos respecto al base (%)

    # Dispersión explícita de demanda. None significa no disponible; nunca se
    # sustituye por un porcentaje arbitrario del nivel de demanda.
    demand_std: Optional[float] = None
    demand_std_source: Optional[str] = None

    # Variables externas adicionales (pasan a la tabla de variables directamente)
    external_variables: Dict[str, float] = field(default_factory=dict)


@dataclass
class PeriodResult:
    """Resultado de simular un período con el motor de eventos discretos."""
    period_index: int
    variables: Dict[str, float]   # Todas las variables resueltas
    demand: float
    revenue: float
    costs: float
    profit: float
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# Resolución de expresiones
# ─────────────────────────────────────────────────────────────────────────────

# Retained as a compatibility description for dependency extraction. Equation
# evaluation itself uses the shared AST allowlist below; it never executes
# Python source.
_SAFE_MATH = frozenset({'max', 'min', 'abs', 'round', 'pow', 'sqrt', 'log', 'exp', 'ceil', 'floor'})

_VAR_PATTERN = re.compile(r'\b([A-Z][A-Z0-9_]*)\b')
_KNOWN_FUNCTIONS = _SAFE_MATH | {'True', 'False', 'None'}


def _extract_rhs_dependencies(expression: str) -> Set[str]:
    """Extrae las variables que el lado derecho de una ecuación necesita."""
    if '=' not in expression:
        return set()
    _, rhs = expression.split('=', 1)
    return {v for v in _VAR_PATTERN.findall(rhs) if v not in _KNOWN_FUNCTIONS}


def _get_lhs(expression: str) -> Optional[str]:
    """Retorna la variable del lado izquierdo (LHS) de la expresión."""
    if '=' not in expression:
        return None
    lhs = expression.split('=', 1)[0].strip()
    return lhs if lhs else None


def _preprocess_rhs(rhs: str) -> str:
    """Normaliza la expresión RHS antes de evaluar."""
    rhs = rhs.replace('∑', '').strip()
    rhs = re.sub(r'mean\(DH\)', 'DPH', rhs)
    return rhs


def _eval_expression(rhs: str, var_table: Dict[str, float]) -> Optional[float]:
    """
    Evalúa el RHS de una ecuación en el contexto de var_table.

    Las expresiones no evaluables por referencias/sintaxis retornan ``None``
    para conservar el contrato legacy de resolución por pasadas. Los errores
    matemáticos de una expresión ya resoluble se propagan: convertirlos en cero
    fabricaría resultados financieros plausibles pero falsos.
    """
    rhs = _preprocess_rhs(rhs)

    # Sustituir variables (de más largo a más corto para evitar sustituciones parciales)
    expr = rhs
    for name, value in sorted(var_table.items(), key=lambda x: -len(x[0])):
        expr = re.sub(r'\b' + re.escape(name) + r'\b', repr(float(value)), expr)

    try:
        result = evaluate_expression(expr, values={name: float(value) for name, value in var_table.items()})
        return float(result)
    except ExpressionError as exc:
        numeric_errors = (
            'División por cero.',
            'Exponente fuera de rango.',
            'La expresión excede los límites numéricos permitidos.',
            'El resultado no es un número finito.',
        )
        if str(exc) in numeric_errors:
            raise
        return None
    except (ArithmeticError, OverflowError, ValueError) as exc:
        raise ExpressionError("La ecuación produjo un error numérico.") from exc
    except Exception as e:
        logger.debug("eval error en '%s': %s", rhs, e)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Ordenamiento topológico
# ─────────────────────────────────────────────────────────────────────────────

def _topological_sort(equations: List[Any]) -> List[Any]:
    """
    Ordena las ecuaciones según sus dependencias (Kahn's algorithm).
    Las ecuaciones con dependencias circulares van al final.
    """
    lhs_to_eq: Dict[str, Any] = {}
    for eq in equations:
        lhs = _get_lhs(eq.expression)
        if lhs:
            lhs_to_eq[lhs] = eq

    in_degree: Dict[str, int] = {lhs: 0 for lhs in lhs_to_eq}
    graph: Dict[str, List[str]] = {lhs: [] for lhs in lhs_to_eq}

    for lhs, eq in lhs_to_eq.items():
        deps = _extract_rhs_dependencies(eq.expression)
        for dep in deps:
            if dep in lhs_to_eq:
                graph[dep].append(lhs)
                in_degree[lhs] = in_degree.get(lhs, 0) + 1

    queue: Deque[str] = deque(lhs for lhs, deg in in_degree.items() if deg == 0)
    sorted_lhs: List[str] = []

    while queue:
        node = queue.popleft()
        sorted_lhs.append(node)
        for neighbor in graph.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # Ecuaciones con ciclos van al final
    remaining = [lhs for lhs in lhs_to_eq if lhs not in sorted_lhs]
    sorted_lhs.extend(remaining)

    return [lhs_to_eq[lhs] for lhs in sorted_lhs if lhs in lhs_to_eq]


# ─────────────────────────────────────────────────────────────────────────────
# Motor principal
# ─────────────────────────────────────────────────────────────────────────────

class DiscreteEventEngine:
    """
    Motor de simulación de eventos discretos genérico para PyMEs.

    No tiene hardcoding de ningún sector. Toda la lógica de negocio
    vive en las ecuaciones almacenadas en BD (config.equations).

    Flujo por período:
      1. Construir tabla de variables (estado_previo + constantes + escenario)
      2. Resolver ecuaciones en orden topológico
      3. Actualizar estado persistente
      4. Retornar PeriodResult
    """

    def __init__(self, config: CompanyConfig):
        self.config = config
        # Estado persistente entre períodos (variables de estado = inventarios, acumulados, etc.)
        self._state: Dict[str, float] = dict(config.initial_state)
        # Historial de demandas para cálculos de media móvil
        self._demand_history: List[float] = []
        self._last_demand_std_source: Optional[str] = None
        # Ecuaciones ordenadas topológicamente (se calcula una sola vez)
        self._sorted_equations = self._prepare_equations()

    def _prepare_equations(self) -> List[Any]:
        """Ordena las ecuaciones respetando area_priority si se definió."""
        eqs = self.config.equations
        if not eqs:
            return []

        if self.config.area_priority:
            # Agrupar por área y concatenar según prioridad
            by_area: Dict[str, List[Any]] = {}
            no_area: List[Any] = []
            for eq in eqs:
                area = eq.fk_area.name if getattr(eq, 'fk_area', None) else None
                if area:
                    by_area.setdefault(area, []).append(eq)
                else:
                    no_area.append(eq)

            ordered: List[Any] = []
            for area_name in self.config.area_priority:
                ordered.extend(by_area.pop(area_name, []))
            # Áreas restantes no especificadas
            for remaining in by_area.values():
                ordered.extend(remaining)
            ordered.extend(no_area)
            return _topological_sort(ordered)

        return _topological_sort(eqs)

    # ── Tabla de variables ───────────────────────────────────────────────────

    def _build_variable_table(
        self,
        scenario: OperationScenario,
        exogenous: Dict[str, float],
    ) -> Dict[str, float]:
        """
        Construye la tabla completa de variables para el período actual.
        Prioridad (mayor a menor): escenario > exógenas > estado_previo > constantes.
        """
        table: Dict[str, float] = {}

        # 1. Constantes del sistema
        table.update(self.config.system_constants)

        # 2. Estado previo (inventarios, acumulados del período anterior)
        table.update(self._state)

        # 3. Variables exógenas del cuestionario
        table.update(exogenous)

        # 4. Variables externas del escenario (pasan directamente)
        table.update(scenario.external_variables)

        # 5. Variables universales del sistema (siempre presentes)
        table['DIA'] = float(scenario.period_index + 1)
        table['NMD'] = float(self.config.total_periods)

        # 6. Demanda del escenario con estacionalidad aplicada
        demand = scenario.demand_value * scenario.seasonality_factor
        table[self.config.demand_variable] = max(0.0, demand)

        # 7. Media y dispersión de demanda. La dispersión procede de una
        # ventana simulada suficiente, del escenario/configuración o de una
        # entrada exógena explícita; nunca de un 10% hardcodeado.
        if self._demand_history:
            window = self._demand_history[-7:]  # últimos 7 períodos
            table['DPH'] = float(np.mean(window))
        else:
            table['DPH'] = table.get(self.config.demand_variable, demand)

        demand_std = None
        self._last_demand_std_source = None
        if len(self._demand_history) > 1:
            demand_std = float(np.std(self._demand_history[-7:]))
            self._last_demand_std_source = 'SIMULATED_WINDOW'
        elif scenario.demand_std is not None:
            demand_std = scenario.demand_std
            self._last_demand_std_source = (
                scenario.demand_std_source or 'CONFIGURED_SCENARIO'
            )
        elif 'DSD' in table:
            demand_std = table['DSD']
            self._last_demand_std_source = 'EXPLICIT_EXOGENOUS'

        if demand_std is not None:
            if isinstance(demand_std, bool):
                raise ValueError("La desviación de demanda debe ser numérica y no negativa.")
            demand_std = float(demand_std)
            if not math.isfinite(demand_std) or demand_std < 0:
                raise ValueError("La desviación de demanda debe ser finita y no negativa.")
            table['DSD'] = demand_std
            table['CVD'] = demand_std / max(abs(table['DPH']), 1.0)
        else:
            table.pop('DSD', None)
            table.pop('CVD', None)

        return table

    # ── Resolver ecuaciones ──────────────────────────────────────────────────

    def _solve_equations(self, var_table: Dict[str, float]) -> Dict[str, float]:
        """
        Resuelve todas las ecuaciones configuradas en orden topológico.
        Realiza hasta 3 pasadas para resolver dependencias que requieran resultados previos.
        """
        results: Dict[str, float] = {}

        def _attempt_solve(equations: List[Any]) -> int:
            solved = 0
            for eq in equations:
                lhs = _get_lhs(eq.expression)
                if not lhs or lhs in results:
                    continue
                _, rhs = eq.expression.split('=', 1)
                combined = {**var_table, **results}
                deps = _extract_rhs_dependencies(eq.expression)
                if not all(d in combined for d in deps):
                    continue
                value = _eval_expression(rhs, combined)
                if value is not None:
                    results[lhs] = value
                    solved += 1
            return solved

        # Pasada 1: resolver todo lo que sea posible
        _attempt_solve(self._sorted_equations)

        # Pasadas 2-3: resolver ecuaciones que dependían de resultados de la pasada anterior
        for _ in range(2):
            if _attempt_solve(self._sorted_equations) == 0:
                break

        return results

    # ── Actualizar estado ────────────────────────────────────────────────────

    def _update_state(
        self, var_table: Dict[str, float], results: Dict[str, float]
    ) -> None:
        """
        Actualiza el estado persistente con las variables de estado del período.
        Solo persisten las variables que ya estaban en el estado inicial
        (definidas en CompanyConfig.initial_state) o que cambian de período en período.
        """
        combined = {**var_table, **results}

        # Persistir solo las variables de estado definidas en la configuración
        for key in self.config.initial_state:
            if key in combined:
                self._state[key] = combined[key]

        # También persistir el demand_variable como referencia del período anterior
        demand_var = self.config.demand_variable
        if demand_var in combined:
            self._demand_history.append(combined[demand_var])
            self._state[f'{demand_var}_prev'] = combined[demand_var]

    # ── Extraer métricas financieras ─────────────────────────────────────────

    @staticmethod
    def _finite(x: float) -> float:
        """Rechaza valores financieros no finitos o fuera del límite operativo."""
        v = float(x)
        if math.isnan(v) or math.isinf(v) or abs(v) > 1e100:
            raise ExpressionError(
                "El resultado financiero no es finito o excede el límite operativo."
            )
        return v

    def _extract_financials(
        self, combined: Dict[str, float]
    ) -> Tuple[float, float, float, float]:
        """Extrae métricas y rechaza resultados numéricos que no pueden reportarse."""
        demand = combined.get(self.config.demand_variable, 0.0)
        revenue = combined.get(self.config.revenue_variable, 0.0)
        costs = combined.get(self.config.cost_variable, 0.0)
        profit = combined.get(self.config.profit_variable, revenue - costs)
        return (
            self._finite(demand),
            self._finite(revenue),
            self._finite(costs),
            self._finite(profit),
        )

    # ── API pública ──────────────────────────────────────────────────────────

    def run_period(
        self,
        scenario: OperationScenario,
        exogenous: Optional[Dict[str, float]] = None,
    ) -> PeriodResult:
        """
        Simula un único período con las condiciones externas dadas.

        Args:
            scenario: condiciones del período (demanda, estacionalidad, etc.)
            exogenous: variables exógenas del cuestionario (precio, costos base, etc.)

        Returns:
            PeriodResult con todas las variables calculadas y métricas financieras.
        """
        if exogenous is None:
            exogenous = {}

        warnings: List[str] = []

        # Construir tabla de variables
        var_table = self._build_variable_table(scenario, exogenous)

        # Resolver ecuaciones
        results = self._solve_equations(var_table)

        # Combinar todo
        combined = {**var_table, **results}

        # Actualizar estado persistente
        self._update_state(var_table, results)

        # Extraer métricas financieras
        demand, revenue, costs, profit = self._extract_financials(combined)

        # Advertencias de negocio configurables
        if revenue > 0:
            margin = profit / revenue
            if margin < -(self.config.min_profit_margin_pct / 100):
                warnings.append(
                    f"Margen negativo: {margin:.1%} (umbral: -{self.config.min_profit_margin_pct}%)"
                )
            cost_ratio = costs / revenue * 100
            if cost_ratio > self.config.max_cost_revenue_ratio:
                warnings.append(
                    f"Ratio costo/ingreso alto: {cost_ratio:.1f}% (máx: {self.config.max_cost_revenue_ratio}%)"
                )

        return PeriodResult(
            period_index=scenario.period_index,
            variables=combined,
            demand=demand,
            revenue=revenue,
            costs=costs,
            profit=profit,
            warnings=warnings,
            metadata={
                'demand_std': combined.get('DSD'),
                'demand_std_source': self._last_demand_std_source,
            },
        )

    def run_all_periods(
        self,
        scenarios: List[OperationScenario],
        exogenous: Optional[Dict[str, float]] = None,
    ) -> List[PeriodResult]:
        """
        Simula todos los períodos secuencialmente, manteniendo estado entre ellos.

        Args:
            scenarios: lista de escenarios, uno por período
            exogenous: variables exógenas compartidas por todos los períodos

        Returns:
            Lista de PeriodResult, uno por período.
        """
        return [self.run_period(s, exogenous) for s in scenarios]

    def reset_state(self) -> None:
        """Reinicia el estado al valor inicial (útil para múltiples corridas)."""
        self._state = dict(self.config.initial_state)
        self._demand_history = []
        self._last_demand_std_source = None


# ─────────────────────────────────────────────────────────────────────────────
# Función pública de alto nivel
# ─────────────────────────────────────────────────────────────────────────────

def simular_operacion(
    config_empresa: CompanyConfig,
    escenario: OperationScenario,
    exogenous: Optional[Dict[str, float]] = None,
) -> PeriodResult:
    """
    Función base del motor de eventos discretos.

    Simula la operación de UNA empresa durante UN período bajo las
    condiciones externas especificadas en escenario.

    Args:
        config_empresa: estructura de la empresa (ecuaciones, estado, umbrales)
        escenario: condiciones externas del período (demanda, estacionalidad, etc.)
        exogenous: variables exógenas del cuestionario

    Returns:
        PeriodResult con todas las variables calculadas.

    Example::

        config = CompanyConfig(
            sector='production',
            demand_variable='DE',
            initial_state={'IPF': 500, 'II': 2000},
            equations=list(Equation.objects.filter(is_active=True)),
        )
        escenario = OperationScenario(period_index=0, demand_value=2500.0)
        result = simular_operacion(config, escenario, exogenous={'PVP': 15.5})
    """
    engine = DiscreteEventEngine(config_empresa)
    return engine.run_period(escenario, exogenous)


# ─────────────────────────────────────────────────────────────────────────────
# Factory: construir CompanyConfig desde un objeto Django CompanyProfile
# ─────────────────────────────────────────────────────────────────────────────

def build_config_from_profile(profile: 'CompanyProfile', equations: List[Any]) -> CompanyConfig:
    """
    Construye un CompanyConfig a partir de un CompanyProfile de Django.

    Args:
        profile: instancia de business.models.CompanyProfile
        equations: lista de Equation del ORM para la simulación

    Returns:
        CompanyConfig listo para usar con DiscreteEventEngine.
    """
    business = profile.fk_business
    return CompanyConfig(
        sector=business.industry_sector,
        business_name=business.name,
        demand_variable=profile.demand_variable_name,
        revenue_variable='IT',
        cost_variable='TG',
        profit_variable='GT',
        initial_state={},          # Se llena desde el cuestionario en simulation_service
        equations=equations,
        min_profit_margin_pct=profile.min_profit_margin_pct,
        max_cost_revenue_ratio=profile.max_cost_revenue_ratio,
        system_constants={},       # Se puede agregar π, tasas fiscales, etc.
        total_periods=30,          # Se sobreescribe antes de correr
    )
