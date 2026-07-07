"""
recommendation_service.py
=========================
Lógica de generación de recomendaciones de negocio.

Extraído de simulate/core/decision_engine.py para separación de responsabilidades.
DecisionEngine delega en RecommendationService manteniendo retrocompatibilidad.

Uso directo::

    from simulate.services.recommendation_service import RecommendationService
    from simulate.core.decision_engine import _compute_risk_metrics

    risk = _compute_risk_metrics(profit_samples)
    svc  = RecommendationService(min_profit_margin_pct=15.0)
    recs = svc.generate(risk, {'IT': 50_000, 'TG': 35_000})
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List

if TYPE_CHECKING:
    from simulate.core.decision_engine import RiskMetrics

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Dataclass compartido
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Recommendation:
    """Recomendación de acción generada por RecommendationService."""
    category: str       # financiero | operativo | riesgo | demanda | eficiencia
    severity: str       # info | warning | critical
    title: str
    message: str
    metric_name: str
    metric_value: float
    threshold: float
    action: str
    impact: str         # Bajo | Medio | Alto | Crítico

    def to_dict(self) -> Dict:
        return {
            'category':     self.category,
            'severity':     self.severity,
            'title':        self.title,
            'message':      self.message,
            'metric_name':  self.metric_name,
            'metric_value': self.metric_value,
            'threshold':    self.threshold,
            'action':       self.action,
            'impact':       self.impact,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Servicio de recomendaciones
# ─────────────────────────────────────────────────────────────────────────────

class RecommendationService:
    """
    Genera recomendaciones de negocio a partir de métricas de simulación.

    Recibe RiskMetrics como input (producidas por DecisionEngine o directamente
    por _compute_risk_metrics). Sector-agnóstico.

    Extraído de RecommendationEngine para separación de responsabilidades.
    DecisionEngine delega en esta clase; RecommendationEngine es un alias
    de retrocompatibilidad en simulate.core.decision_engine.
    """

    def __init__(
        self,
        min_profit_margin_pct: float = 10.0,
        max_cost_revenue_ratio: float = 70.0,
        max_probability_of_loss: float = 0.20,
        min_service_level: float = 0.85,
    ):
        self.min_profit_margin_pct = min_profit_margin_pct
        self.max_cost_revenue_ratio = max_cost_revenue_ratio
        self.max_probability_of_loss = max_probability_of_loss
        self.min_service_level = min_service_level

    def generate(
        self,
        risk_metrics: 'RiskMetrics',
        aggregated_vars: Dict[str, float],
    ) -> List[Recommendation]:
        """
        Genera recomendaciones basadas en métricas de riesgo y variables agregadas.

        Args:
            risk_metrics:    calculadas por _compute_risk_metrics()
            aggregated_vars: media de variables de negocio (nombre→valor)

        Returns:
            Lista de Recommendation ordenada por severidad (crítico → info).
        """
        recs: List[Recommendation] = []

        recs.extend(self._check_profitability(risk_metrics, aggregated_vars))
        recs.extend(self._check_risk_exposure(risk_metrics))
        recs.extend(self._check_cost_structure(aggregated_vars))
        recs.extend(self._check_demand(aggregated_vars))
        recs.extend(self._check_efficiency(aggregated_vars))

        order = {'critical': 0, 'warning': 1, 'info': 2}
        recs.sort(key=lambda r: order.get(r.severity, 3))
        return recs

    # ── Verificaciones individuales ──────────────────────────────────────────

    def _check_profitability(
        self, risk: 'RiskMetrics', agg_vars: Dict[str, float]
    ) -> List[Recommendation]:
        recs = []

        revenue = agg_vars.get('IT', agg_vars.get('INGRESOS', 0.0))
        profit = agg_vars.get('GT', agg_vars.get('GANANCIA', risk.mean))
        margin_pct = (profit / revenue * 100) if revenue > 0 else 0.0

        if margin_pct < 0:
            recs.append(Recommendation(
                category='financiero', severity='critical',
                title='Operación con pérdidas',
                message=(
                    f"El margen de ganancia promedio es {margin_pct:.1f}%. "
                    "La empresa opera en pérdida en el escenario base."
                ),
                metric_name='margen_ganancia_pct',
                metric_value=margin_pct,
                threshold=0.0,
                action=(
                    "Revisar inmediatamente la estructura de costos y precio de venta. "
                    "Considerar reducir costos fijos o incrementar precios."
                ),
                impact='Crítico',
            ))
        elif margin_pct < self.min_profit_margin_pct:
            recs.append(Recommendation(
                category='financiero', severity='warning',
                title='Margen de ganancia por debajo del umbral',
                message=(
                    f"Margen actual: {margin_pct:.1f}% "
                    f"(umbral mínimo: {self.min_profit_margin_pct:.1f}%)."
                ),
                metric_name='margen_ganancia_pct',
                metric_value=margin_pct,
                threshold=self.min_profit_margin_pct,
                action=(
                    "Analizar qué costos pueden reducirse sin afectar calidad, "
                    "o evaluar un ajuste de precios."
                ),
                impact='Alto',
            ))

        if risk.probability_of_loss > self.max_probability_of_loss:
            recs.append(Recommendation(
                category='riesgo', severity='warning',
                title='Alta probabilidad de pérdida',
                message=(
                    f"P(pérdida) = {risk.probability_of_loss:.1%} "
                    f"(máximo aceptable: {self.max_probability_of_loss:.1%})."
                ),
                metric_name='probability_of_loss',
                metric_value=risk.probability_of_loss,
                threshold=self.max_probability_of_loss,
                action=(
                    "Crear un fondo de contingencia o revisar el punto de equilibrio. "
                    "Considerar cobertura de riesgo para demanda baja."
                ),
                impact='Alto',
            ))

        return recs

    def _check_risk_exposure(self, risk: 'RiskMetrics') -> List[Recommendation]:
        recs = []

        if risk.var_95 < 0:
            var_magnitude = abs(risk.var_95)
            if var_magnitude > abs(risk.mean) * 0.5:
                recs.append(Recommendation(
                    category='riesgo', severity='warning',
                    title='Exposición a pérdidas extremas alta (VaR)',
                    message=(
                        f"El VaR al 95% es {risk.var_95:,.0f}. "
                        "En el peor 5% de escenarios, las pérdidas son significativas."
                    ),
                    metric_name='var_95',
                    metric_value=risk.var_95,
                    threshold=0.0,
                    action=(
                        "Diversificar fuentes de ingreso o establecer precios con "
                        "mayor margen de seguridad para absorber escenarios desfavorables."
                    ),
                    impact='Alto',
                ))

        if abs(risk.kurtosis) > 3:
            recs.append(Recommendation(
                category='riesgo', severity='info',
                title='Distribución de ganancias con colas pesadas',
                message=(
                    f"La kurtosis de {risk.kurtosis:.2f} indica que son posibles "
                    "eventos extremos (tanto pérdidas como ganancias inusuales)."
                ),
                metric_name='kurtosis',
                metric_value=risk.kurtosis,
                threshold=3.0,
                action="Evaluar escenarios de estrés y preparar planes de contingencia.",
                impact='Medio',
            ))

        return recs

    def _check_cost_structure(self, agg_vars: Dict[str, float]) -> List[Recommendation]:
        recs = []
        revenue = agg_vars.get('IT', agg_vars.get('INGRESOS', 0.0))
        costs = agg_vars.get('TG', agg_vars.get('GASTOS_TOTALES', 0.0))

        if revenue > 0 and costs > 0:
            cost_ratio = costs / revenue * 100
            if cost_ratio > self.max_cost_revenue_ratio:
                recs.append(Recommendation(
                    category='financiero', severity='warning',
                    title='Ratio costo/ingreso elevado',
                    message=(
                        f"Los costos representan {cost_ratio:.1f}% de los ingresos "
                        f"(máximo recomendado: {self.max_cost_revenue_ratio:.1f}%)."
                    ),
                    metric_name='cost_revenue_ratio_pct',
                    metric_value=cost_ratio,
                    threshold=self.max_cost_revenue_ratio,
                    action=(
                        "Identificar los costos de mayor impacto (Pareto) y establecer "
                        "metas de reducción por área."
                    ),
                    impact='Alto',
                ))

        return recs

    def _check_demand(self, agg_vars: Dict[str, float]) -> List[Recommendation]:
        recs = []

        di = agg_vars.get('DI', 0.0)
        ddp = agg_vars.get('DDP', agg_vars.get('DE', 0.0))
        if ddp > 0 and di / ddp > 0.15:
            recs.append(Recommendation(
                category='demanda', severity='warning',
                title='Demanda insatisfecha significativa',
                message=(
                    f"Se pierde aproximadamente {di / ddp:.1%} de la demanda potencial "
                    f"({di:,.0f} unidades de {ddp:,.0f})."
                ),
                metric_name='demand_lost_pct',
                metric_value=di / ddp,
                threshold=0.15,
                action=(
                    "Incrementar capacidad de producción o de servicio. "
                    "Evaluar si la restricción es inventario, producción o distribución."
                ),
                impact='Medio',
            ))

        nsc = agg_vars.get('NSC', None)
        if nsc is not None and nsc < self.min_service_level:
            recs.append(Recommendation(
                category='eficiencia', severity='warning',
                title='Nivel de servicio al cliente bajo',
                message=(
                    f"Nivel de servicio: {nsc:.1%} "
                    f"(mínimo aceptable: {self.min_service_level:.1%})."
                ),
                metric_name='service_level',
                metric_value=nsc,
                threshold=self.min_service_level,
                action=(
                    "Revisar disponibilidad de inventario, tiempos de entrega "
                    "y capacidad operativa."
                ),
                impact='Alto',
            ))

        return recs

    def _check_efficiency(self, agg_vars: Dict[str, float]) -> List[Recommendation]:
        recs = []

        fu = agg_vars.get('FU', None)
        if fu is not None:
            if fu < 0.5:
                recs.append(Recommendation(
                    category='eficiencia', severity='info',
                    title='Capacidad productiva subutilizada',
                    message=f"Factor de utilización: {fu:.1%}. La capacidad instalada no se aprovecha.",
                    metric_name='capacity_utilization',
                    metric_value=fu,
                    threshold=0.5,
                    action=(
                        "Evaluar si existe demanda adicional que pueda captarse, "
                        "o reducir capacidad ociosa para bajar costos fijos."
                    ),
                    impact='Medio',
                ))
            elif fu > 0.95:
                recs.append(Recommendation(
                    category='eficiencia', severity='info',
                    title='Capacidad productiva al límite',
                    message=f"Factor de utilización: {fu:.1%}. Riesgo de cuellos de botella.",
                    metric_name='capacity_utilization',
                    metric_value=fu,
                    threshold=0.95,
                    action=(
                        "Planificar expansión de capacidad antes de perder demanda "
                        "por incapacidad de respuesta."
                    ),
                    impact='Medio',
                ))

        ri = agg_vars.get('RI', None)
        if ri is not None and ri < 0.05:
            recs.append(Recommendation(
                category='financiero', severity='info',
                title='Retorno sobre inversión bajo',
                message=f"ROI estimado: {ri:.1%}. Por debajo de una tasa de retorno razonable.",
                metric_name='roi',
                metric_value=ri,
                threshold=0.05,
                action=(
                    "Evaluar si la inversión actual genera el retorno esperado. "
                    "Identificar activos subutilizados o capital inmovilizado."
                ),
                impact='Medio',
            ))

        return recs
