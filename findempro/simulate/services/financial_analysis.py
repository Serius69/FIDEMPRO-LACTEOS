"""
financial_analysis.py
=====================
Motor de análisis financiero genérico para PyMEs multi-industria.

Calcula:
- Métricas de rentabilidad (margen, ROI, ROE, EBITDA proxy)
- Métricas de riesgo (VaR, CVaR, probabilidad de pérdida)
- Análisis de punto de equilibrio (break-even)
- Escenarios financieros (pesimista / base / optimista)
- Recomendaciones automáticas basadas en umbrales configurables
- Alertas inteligentes por sector
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────

@dataclass
class FinancialMetrics:
    """Métricas financieras calculadas a partir de los datos del negocio."""
    # Ingresos y costos
    total_revenue: float
    total_costs: float
    variable_costs: float
    fixed_costs: float

    # Rentabilidad
    gross_profit: float
    net_profit: float
    gross_margin_pct: float
    net_margin_pct: float
    ebitda_proxy: float          # Utilidad operativa simplificada
    roi_pct: float

    # Eficiencia
    cost_revenue_ratio_pct: float
    variable_cost_ratio_pct: float

    # Break-even
    breakeven_units: float       # Unidades necesarias para cubrir costos
    breakeven_revenue: float
    margin_of_safety_pct: float  # Qué tan lejos está del break-even

    # Flujo de caja proxy
    operating_cash_flow: float

    # Indicadores de salud
    financial_health_score: float  # 0-100
    profitability_rating: str      # 'excelente' | 'bueno' | 'regular' | 'crítico'


@dataclass
class RiskMetrics:
    """Métricas de riesgo financiero."""
    probability_of_loss: float
    value_at_risk_95: float      # Máxima pérdida esperada con 95% de confianza
    expected_shortfall: float    # Pérdida promedio en el 5% peor (CVaR)
    demand_volatility: float     # Coeficiente de variación de la demanda
    revenue_at_risk: float       # Ingresos en riesgo (VaR aplicado a ingresos)
    risk_rating: str             # 'bajo' | 'moderado' | 'alto' | 'crítico'
    risk_score: float            # 0-100


@dataclass
class Recommendation:
    """Recomendación financiera automática."""
    category: str               # 'rentabilidad' | 'costos' | 'demanda' | 'riesgo' | 'eficiencia'
    severity: str               # 'info' | 'warning' | 'critical'
    title: str
    description: str
    actions: List[str] = field(default_factory=list)
    metric_name: str = ''
    metric_value: float = 0.0
    threshold: float = 0.0
    impact: str = 'medium'      # 'low' | 'medium' | 'high'


@dataclass
class FinancialReport:
    """Reporte financiero completo integrado."""
    metrics: FinancialMetrics
    risk: RiskMetrics
    recommendations: List[Recommendation]
    scenarios: Dict[str, Dict]   # pesimista | base | optimista
    summary: str                 # Resumen ejecutivo en texto
    score_overall: float         # Puntaje global 0-100


# ─────────────────────────────────────────────
# Motor de análisis
# ─────────────────────────────────────────────

class FinancialAnalysisEngine:
    """
    Motor de análisis financiero genérico para cualquier PyME.

    Recibe los datos financieros del negocio y genera métricas,
    análisis de riesgo y recomendaciones accionables automáticamente.

    Uso:
        engine = FinancialAnalysisEngine(
            revenue=150000,
            variable_costs=90000,
            fixed_costs=30000,
            demand_mean=5000,
            demand_std=800,
            unit_price=30.0,
            industry_sector='retail',
            profit_margin_threshold=15.0,
        )
        report = engine.generate_report()
    """

    # Umbrales por sector (personalizables vía CompanyProfile)
    SECTOR_THRESHOLDS = {
        'agro': {
            'min_profit_margin': 15.0,
            'max_cost_ratio': 75.0,
            'target_roi': 12.0,
        },
        'production': {
            'min_profit_margin': 20.0,
            'max_cost_ratio': 70.0,
            'target_roi': 15.0,
        },
        'retail': {
            'min_profit_margin': 12.0,
            'max_cost_ratio': 80.0,
            'target_roi': 10.0,
        },
        'services': {
            'min_profit_margin': 25.0,
            'max_cost_ratio': 65.0,
            'target_roi': 20.0,
        },
        'manufacturing': {
            'min_profit_margin': 18.0,
            'max_cost_ratio': 72.0,
            'target_roi': 14.0,
        },
        'other': {
            'min_profit_margin': 15.0,
            'max_cost_ratio': 75.0,
            'target_roi': 12.0,
        },
    }

    def __init__(
        self,
        revenue: float,
        variable_costs: float,
        fixed_costs: float,
        demand_mean: float,
        demand_std: float = 0.0,
        unit_price: float = 0.0,
        industry_sector: str = 'other',
        # Parámetros de riesgo de la simulación Monte Carlo (opcionales)
        profit_samples: Optional[np.ndarray] = None,
        # Umbrales personalizados (sobreescriben los de sector)
        min_profit_margin: Optional[float] = None,
        max_cost_ratio: Optional[float] = None,
        target_roi: Optional[float] = None,
    ):
        self.revenue = float(revenue)
        self.variable_costs = float(variable_costs)
        self.fixed_costs = float(fixed_costs)
        self.total_costs = self.variable_costs + self.fixed_costs
        self.demand_mean = float(demand_mean)
        self.demand_std = float(demand_std)
        self.unit_price = float(unit_price)
        self.industry_sector = industry_sector
        self.profit_samples = profit_samples

        # Umbrales: personalizados > sector > default
        sector_th = self.SECTOR_THRESHOLDS.get(industry_sector, self.SECTOR_THRESHOLDS['other'])
        self.min_profit_margin = min_profit_margin if min_profit_margin is not None else sector_th['min_profit_margin']
        self.max_cost_ratio = max_cost_ratio if max_cost_ratio is not None else sector_th['max_cost_ratio']
        self.target_roi = target_roi if target_roi is not None else sector_th['target_roi']

    # ── Métricas financieras ───────────────────────────────────────────────────

    def compute_metrics(self) -> FinancialMetrics:
        """Calcula todas las métricas financieras."""
        gross_profit = self.revenue - self.variable_costs
        net_profit = self.revenue - self.total_costs
        gross_margin = (gross_profit / self.revenue * 100) if self.revenue > 0 else 0.0
        net_margin = (net_profit / self.revenue * 100) if self.revenue > 0 else 0.0
        roi = (net_profit / self.total_costs * 100) if self.total_costs > 0 else 0.0
        ebitda = net_profit  # Proxy simplificado (sin D&A por ahora)
        cost_ratio = (self.total_costs / self.revenue * 100) if self.revenue > 0 else 100.0
        var_ratio = (self.variable_costs / self.revenue * 100) if self.revenue > 0 else 100.0

        # Break-even
        unit_price = self.unit_price if self.unit_price > 0 else (self.revenue / max(self.demand_mean, 1))
        unit_var_cost = self.variable_costs / max(self.demand_mean, 1)
        contribution_margin = unit_price - unit_var_cost
        if contribution_margin > 0:
            breakeven_units = self.fixed_costs / contribution_margin
            breakeven_revenue = breakeven_units * unit_price
        else:
            breakeven_units = float('inf')
            breakeven_revenue = float('inf')

        # Margen de seguridad
        if breakeven_revenue < self.revenue and self.revenue > 0:
            margin_of_safety = ((self.revenue - breakeven_revenue) / self.revenue) * 100
        else:
            margin_of_safety = 0.0

        # Flujo de caja operativo proxy
        operating_cf = net_profit  # Simplificado

        # Puntaje de salud financiera (0-100)
        health_score = self._compute_health_score(net_margin, roi, cost_ratio, margin_of_safety)

        if health_score >= 75:
            rating = 'excelente'
        elif health_score >= 55:
            rating = 'bueno'
        elif health_score >= 35:
            rating = 'regular'
        else:
            rating = 'crítico'

        return FinancialMetrics(
            total_revenue=self.revenue,
            total_costs=self.total_costs,
            variable_costs=self.variable_costs,
            fixed_costs=self.fixed_costs,
            gross_profit=gross_profit,
            net_profit=net_profit,
            gross_margin_pct=gross_margin,
            net_margin_pct=net_margin,
            ebitda_proxy=ebitda,
            roi_pct=roi,
            cost_revenue_ratio_pct=cost_ratio,
            variable_cost_ratio_pct=var_ratio,
            breakeven_units=breakeven_units if not np.isinf(breakeven_units) else -1,
            breakeven_revenue=breakeven_revenue if not np.isinf(breakeven_revenue) else -1,
            margin_of_safety_pct=margin_of_safety,
            operating_cash_flow=operating_cf,
            financial_health_score=health_score,
            profitability_rating=rating,
        )

    def _compute_health_score(self, net_margin: float, roi: float, cost_ratio: float, mos: float) -> float:
        """Calcula puntaje de salud financiera 0-100."""
        score = 0.0
        # Margen neto (0-30 puntos)
        if net_margin >= self.min_profit_margin:
            score += 30
        elif net_margin > 0:
            score += (net_margin / self.min_profit_margin) * 30
        # ROI (0-25 puntos)
        if roi >= self.target_roi:
            score += 25
        elif roi > 0:
            score += (roi / self.target_roi) * 25
        # Ratio costo/ingreso (0-25 puntos)
        if cost_ratio <= self.max_cost_ratio:
            score += 25
        else:
            excess = cost_ratio - self.max_cost_ratio
            score += max(0, 25 - excess)
        # Margen de seguridad (0-20 puntos)
        score += min(20, (mos / 100) * 20)
        return round(min(100, max(0, score)), 1)

    # ── Métricas de riesgo ─────────────────────────────────────────────────────

    def compute_risk(self) -> RiskMetrics:
        """Calcula métricas de riesgo financiero."""
        cv = (self.demand_std / self.demand_mean) if self.demand_mean > 0 else 0.0

        if self.profit_samples is not None and len(self.profit_samples) > 10:
            prob_loss = float(np.mean(self.profit_samples < 0))
            var_95 = float(np.percentile(self.profit_samples, 5))
            tail = self.profit_samples[self.profit_samples <= var_95]
            es = float(np.mean(tail)) if len(tail) > 0 else var_95
            revenue_at_risk = abs(var_95) if var_95 < 0 else 0.0
        else:
            # Estimación analítica cuando no hay muestras
            prob_loss = 0.0
            var_95 = 0.0
            es = 0.0
            revenue_at_risk = 0.0

        # Risk score (0-100, menor es mejor)
        risk_score = self._compute_risk_score(prob_loss, cv, var_95)

        if risk_score <= 25:
            risk_rating = 'bajo'
        elif risk_score <= 50:
            risk_rating = 'moderado'
        elif risk_score <= 75:
            risk_rating = 'alto'
        else:
            risk_rating = 'crítico'

        return RiskMetrics(
            probability_of_loss=prob_loss,
            value_at_risk_95=var_95,
            expected_shortfall=es,
            demand_volatility=cv,
            revenue_at_risk=revenue_at_risk,
            risk_rating=risk_rating,
            risk_score=risk_score,
        )

    def _compute_risk_score(self, prob_loss: float, cv: float, var_95: float) -> float:
        """Calcula puntaje de riesgo 0-100 (mayor = más riesgo)."""
        score = 0.0
        # Probabilidad de pérdida (0-40 puntos)
        score += min(40, prob_loss * 100)
        # Volatilidad de demanda (0-30 puntos)
        score += min(30, cv * 60)
        # VaR relativo a ingresos (0-30 puntos)
        if self.revenue > 0 and var_95 < 0:
            rel_loss = abs(var_95) / self.revenue
            score += min(30, rel_loss * 100)
        return round(min(100, max(0, score)), 1)

    # ── Escenarios ─────────────────────────────────────────────────────────────

    def compute_scenarios(self) -> Dict[str, Dict]:
        """
        Calcula escenarios financieros usando factores sobre la demanda media.
        """
        base_demand = self.demand_mean
        scenarios = {
            'pesimista': 0.70,
            'conservador': 0.85,
            'base': 1.00,
            'optimista': 1.15,
            'muy_optimista': 1.30,
        }

        unit_price = self.unit_price if self.unit_price > 0 else (self.revenue / max(base_demand, 1))
        unit_var_cost = self.variable_costs / max(base_demand, 1)

        results = {}
        for name, factor in scenarios.items():
            demand = base_demand * factor
            rev = demand * unit_price
            var_c = demand * unit_var_cost
            total_c = var_c + self.fixed_costs
            gp = rev - total_c
            margin = (gp / rev * 100) if rev > 0 else 0.0
            roi = (gp / total_c * 100) if total_c > 0 else 0.0

            results[name] = {
                'demand_factor': factor,
                'demand_units': round(demand, 2),
                'revenue': round(rev, 2),
                'variable_costs': round(var_c, 2),
                'total_costs': round(total_c, 2),
                'gross_profit': round(gp, 2),
                'profit_margin_pct': round(margin, 2),
                'roi_pct': round(roi, 2),
                'is_profitable': gp > 0,
            }
        return results

    # ── Recomendaciones automáticas ────────────────────────────────────────────

    def generate_recommendations(
        self,
        metrics: FinancialMetrics,
        risk: RiskMetrics,
    ) -> List[Recommendation]:
        """
        Genera recomendaciones financieras accionables automáticamente.
        Basadas en umbrales configurables por empresa/sector.
        """
        recs: List[Recommendation] = []

        # 1. Margen de ganancia
        if metrics.net_margin_pct < 0:
            recs.append(Recommendation(
                category='rentabilidad',
                severity='critical',
                title='Operación con Pérdidas',
                description=f'El margen neto es {metrics.net_margin_pct:.1f}%. '
                            f'La empresa está perdiendo dinero en cada unidad vendida.',
                actions=[
                    'Revisar y reducir costos variables inmediatamente',
                    f'Aumentar precio de venta para superar el punto de equilibrio',
                    'Analizar qué productos/servicios generan pérdidas',
                    'Considerar suspender líneas no rentables',
                ],
                metric_name='margen_neto_pct',
                metric_value=metrics.net_margin_pct,
                threshold=0.0,
                impact='high',
            ))
        elif metrics.net_margin_pct < self.min_profit_margin:
            recs.append(Recommendation(
                category='rentabilidad',
                severity='warning',
                title='Margen de Ganancia Bajo',
                description=f'El margen neto ({metrics.net_margin_pct:.1f}%) está por debajo '
                            f'del mínimo recomendado para el sector ({self.min_profit_margin:.0f}%).',
                actions=[
                    f'Objetivo: aumentar margen a {self.min_profit_margin:.0f}%',
                    'Revisar estructura de costos y eliminar gastos innecesarios',
                    'Evaluar ajuste de precios con análisis de elasticidad',
                    'Mejorar mezcla de productos hacia los más rentables',
                ],
                metric_name='margen_neto_pct',
                metric_value=metrics.net_margin_pct,
                threshold=self.min_profit_margin,
                impact='high',
            ))

        # 2. Ratio costos/ingresos
        if metrics.cost_revenue_ratio_pct > self.max_cost_ratio:
            excess = metrics.cost_revenue_ratio_pct - self.max_cost_ratio
            recs.append(Recommendation(
                category='costos',
                severity='warning' if excess < 15 else 'critical',
                title='Costos Elevados',
                description=f'Los costos representan el {metrics.cost_revenue_ratio_pct:.1f}% '
                            f'de los ingresos (máximo recomendado: {self.max_cost_ratio:.0f}%).',
                actions=[
                    'Auditar costos fijos y reducir los no esenciales',
                    f'Reducir costos en {excess:.1f}% para alcanzar el umbral objetivo',
                    'Negociar mejores condiciones con proveedores',
                    'Implementar eficiencias operativas',
                    'Revisar contratos y gastos recurrentes',
                ],
                metric_name='cost_revenue_ratio_pct',
                metric_value=metrics.cost_revenue_ratio_pct,
                threshold=self.max_cost_ratio,
                impact='high',
            ))

        # 3. Break-even
        if metrics.margin_of_safety_pct < 10 and metrics.margin_of_safety_pct >= 0:
            recs.append(Recommendation(
                category='riesgo',
                severity='warning',
                title='Margen de Seguridad Bajo',
                description=f'Opera al {metrics.margin_of_safety_pct:.1f}% sobre el punto de equilibrio. '
                            f'Una caída pequeña en ventas generaría pérdidas.',
                actions=[
                    'Aumentar ventas para ampliar el margen de seguridad',
                    'Reducir costos fijos para bajar el punto de equilibrio',
                    f'Punto de equilibrio actual: ${metrics.breakeven_revenue:,.0f}',
                ],
                metric_name='margin_of_safety_pct',
                metric_value=metrics.margin_of_safety_pct,
                threshold=20.0,
                impact='medium',
            ))
        elif metrics.margin_of_safety_pct < 0:
            recs.append(Recommendation(
                category='riesgo',
                severity='critical',
                title='Por Debajo del Punto de Equilibrio',
                description=f'Los ingresos actuales no cubren los costos fijos. '
                            f'Punto de equilibrio: ${metrics.breakeven_revenue:,.0f}.',
                actions=[
                    f'Incrementar ingresos en ${abs(metrics.gross_profit):,.0f} para cubrir costos',
                    'Plan de emergencia: reducir costos fijos inmediatamente',
                    'Revisar viabilidad del negocio actual',
                ],
                metric_name='below_breakeven',
                metric_value=self.revenue,
                threshold=metrics.breakeven_revenue,
                impact='high',
            ))

        # 4. Riesgo de pérdida
        if risk.probability_of_loss > 0.3:
            recs.append(Recommendation(
                category='riesgo',
                severity='critical' if risk.probability_of_loss > 0.5 else 'warning',
                title=f'Alta Probabilidad de Pérdidas ({risk.probability_of_loss:.0%})',
                description=f'La simulación indica que en {risk.probability_of_loss:.0%} '
                            f'de los escenarios la empresa operaría con pérdidas.',
                actions=[
                    'Construir reserva de liquidez para cubrir escenarios adversos',
                    f'VaR al 95%: ${abs(risk.value_at_risk_95):,.0f} en riesgo',
                    'Diversificar fuentes de ingreso para reducir dependencia de demanda',
                    'Establecer coberturas o contratos de largo plazo',
                ],
                metric_name='probability_of_loss',
                metric_value=risk.probability_of_loss * 100,
                threshold=20.0,
                impact='high',
            ))

        # 5. Volatilidad de demanda
        if risk.demand_volatility > 0.4:
            recs.append(Recommendation(
                category='demanda',
                severity='warning',
                title='Alta Volatilidad de Demanda',
                description=f'El coeficiente de variación de la demanda es {risk.demand_volatility:.0%}, '
                            f'indicando alta incertidumbre en ventas.',
                actions=[
                    'Implementar estrategias de suavizamiento de demanda (contratos, suscripciones)',
                    'Mantener inventario de seguridad adecuado',
                    'Revisar estrategia de marketing para estabilizar clientes',
                    'Analizar causas de la variabilidad (estacionalidad, competencia)',
                ],
                metric_name='demand_volatility_cv',
                metric_value=risk.demand_volatility * 100,
                threshold=30.0,
                impact='medium',
            ))

        # 6. ROI
        if metrics.roi_pct < self.target_roi and metrics.roi_pct >= 0:
            recs.append(Recommendation(
                category='rentabilidad',
                severity='info',
                title='ROI por Debajo del Objetivo',
                description=f'El retorno sobre inversión ({metrics.roi_pct:.1f}%) '
                            f'está por debajo del objetivo sectorial ({self.target_roi:.0f}%).',
                actions=[
                    f'Objetivo ROI: {self.target_roi:.0f}% — brecha: {self.target_roi - metrics.roi_pct:.1f}%',
                    'Revisar eficiencia del capital invertido',
                    'Identificar activos o inversiones de bajo rendimiento',
                    'Evaluar reinversión en áreas de mayor retorno',
                ],
                metric_name='roi_pct',
                metric_value=metrics.roi_pct,
                threshold=self.target_roi,
                impact='medium',
            ))

        # 7. Situación positiva
        if not recs:
            recs.append(Recommendation(
                category='rentabilidad',
                severity='info',
                title='Situación Financiera Saludable',
                description='Los indicadores financieros están dentro de los parámetros óptimos para el sector.',
                actions=[
                    'Mantener disciplina en control de costos',
                    'Evaluar oportunidades de expansión o reinversión',
                    'Actualizar el análisis periódicamente',
                ],
                metric_name='financial_health_score',
                metric_value=metrics.financial_health_score,
                threshold=75.0,
                impact='low',
            ))

        # Ordenar por severidad
        severity_order = {'critical': 0, 'warning': 1, 'info': 2}
        recs.sort(key=lambda r: severity_order.get(r.severity, 99))
        return recs

    # ── Resumen ejecutivo ──────────────────────────────────────────────────────

    def _generate_summary(self, metrics: FinancialMetrics, risk: RiskMetrics) -> str:
        """Genera un resumen ejecutivo en texto."""
        status = metrics.profitability_rating.upper()
        lines = [
            f"Estado financiero: {status}",
            f"Ingresos: ${metrics.total_revenue:,.0f} | Costos: ${metrics.total_costs:,.0f}",
            f"Utilidad neta: ${metrics.net_profit:,.0f} ({metrics.net_margin_pct:.1f}%)",
            f"ROI: {metrics.roi_pct:.1f}% | Riesgo: {risk.risk_rating.upper()} ({risk.risk_score:.0f}/100)",
            f"P(pérdida): {risk.probability_of_loss:.1%} | Salud financiera: {metrics.financial_health_score:.0f}/100",
        ]
        if metrics.breakeven_revenue > 0:
            lines.append(f"Break-even: ${metrics.breakeven_revenue:,.0f} | "
                         f"Margen seguridad: {metrics.margin_of_safety_pct:.1f}%")
        return " | ".join(lines)

    # ── Reporte completo ───────────────────────────────────────────────────────

    def generate_report(self) -> FinancialReport:
        """
        Genera el reporte financiero completo.

        Returns:
            FinancialReport con métricas, riesgo, escenarios y recomendaciones.
        """
        logger.info("[FA] Generando reporte financiero")

        metrics = self.compute_metrics()
        risk = self.compute_risk()
        scenarios = self.compute_scenarios()
        recommendations = self.generate_recommendations(metrics, risk)
        summary = self._generate_summary(metrics, risk)

        # Puntaje global: promedio ponderado de salud y riesgo (invertido)
        overall_score = (metrics.financial_health_score * 0.6 + (100 - risk.risk_score) * 0.4)

        return FinancialReport(
            metrics=metrics,
            risk=risk,
            recommendations=recommendations,
            scenarios=scenarios,
            summary=summary,
            score_overall=round(overall_score, 1),
        )

    def to_dict(self) -> Dict:
        """Genera el reporte y lo retorna como diccionario serializable."""
        report = self.generate_report()
        m = report.metrics
        r = report.risk
        return {
            'metrics': {
                'revenue': m.total_revenue,
                'costs': m.total_costs,
                'variable_costs': m.variable_costs,
                'fixed_costs': m.fixed_costs,
                'gross_profit': m.gross_profit,
                'net_profit': m.net_profit,
                'gross_margin_pct': m.gross_margin_pct,
                'net_margin_pct': m.net_margin_pct,
                'roi_pct': m.roi_pct,
                'cost_revenue_ratio_pct': m.cost_revenue_ratio_pct,
                'breakeven_units': m.breakeven_units,
                'breakeven_revenue': m.breakeven_revenue,
                'margin_of_safety_pct': m.margin_of_safety_pct,
                'financial_health_score': m.financial_health_score,
                'profitability_rating': m.profitability_rating,
            },
            'risk': {
                'probability_of_loss': r.probability_of_loss,
                'value_at_risk_95': r.value_at_risk_95,
                'expected_shortfall': r.expected_shortfall,
                'demand_volatility': r.demand_volatility,
                'revenue_at_risk': r.revenue_at_risk,
                'risk_rating': r.risk_rating,
                'risk_score': r.risk_score,
            },
            'scenarios': report.scenarios,
            'recommendations': [
                {
                    'category': rec.category,
                    'severity': rec.severity,
                    'title': rec.title,
                    'description': rec.description,
                    'actions': rec.actions,
                    'metric_name': rec.metric_name,
                    'metric_value': rec.metric_value,
                    'threshold': rec.threshold,
                    'impact': rec.impact,
                }
                for rec in report.recommendations
            ],
            'summary': report.summary,
            'score_overall': report.score_overall,
        }
