"""
decision_engine.py
==================
Motor de apoyo a la toma de decisiones financieras para PyMEs.

Responsabilidad:
  - Calcular utilidad esperada con función de utilidad CARA (Constant Absolute Risk Aversion)
  - Calcular métricas de riesgo: varianza, percentiles, VaR, CVaR
  - Generar recomendaciones automáticas basadas en los resultados de simulación
  - Comparar escenarios y recomendar la estrategia óptima

No contiene lógica de simulación ni de generación de datos.
Opera sobre los resultados ya calculados por DiscreteEventEngine y Monte Carlo.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from simulate.services.recommendation_service import (
    Recommendation,
    RecommendationService,
)

logger = logging.getLogger(__name__)

# Alias de retrocompatibilidad — importable desde la ubicación original
RecommendationEngine = RecommendationService


# ─────────────────────────────────────────────────────────────────────────────
# Estructuras de salida
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RiskMetrics:
    """Métricas de riesgo calculadas sobre distribución de utilidades/ganancias."""
    mean: float
    std: float
    variance: float
    skewness: float
    kurtosis: float

    # Percentiles clave
    p1: float
    p5: float
    p10: float
    p25: float
    p50: float
    p75: float
    p90: float
    p95: float
    p99: float

    # Riesgo de pérdida
    probability_of_loss: float
    probability_breakeven: float

    # VaR y CVaR
    var_95: float     # Percentil 5 de ganancias = pérdida máxima al 95% de confianza
    var_99: float
    cvar_95: float    # Media de la cola inferior al 5% (Expected Shortfall / CVaR)
    cvar_99: float

    # Ratios de rendimiento ajustados por riesgo
    sharpe_ratio: Optional[float] = None   # (mean - rf) / std
    sortino_ratio: Optional[float] = None  # (mean - rf) / downside_std
    downside_std: Optional[float] = None   # std sólo de retornos negativos


@dataclass
class DecisionReport:
    """Reporte completo del motor de decisión."""
    # Métricas de riesgo
    risk_metrics: RiskMetrics

    # Utilidad esperada (función CARA)
    expected_utility: float
    risk_aversion: float

    # Recomendaciones ordenadas por severidad
    recommendations: List[Recommendation]

    # Comparación de escenarios
    scenario_comparison: Dict

    # Decisión recomendada
    overall_assessment: str    # viable | riesgoso | no_viable
    overall_score: float       # 0.0 – 1.0 (mayor = mejor)
    summary: str

    def to_dict(self) -> Dict:
        return {
            'risk_metrics': {
                'mean':                 self.risk_metrics.mean,
                'std':                  self.risk_metrics.std,
                'p5':                   self.risk_metrics.p5,
                'p25':                  self.risk_metrics.p25,
                'p50':                  self.risk_metrics.p50,
                'p75':                  self.risk_metrics.p75,
                'p95':                  self.risk_metrics.p95,
                'probability_of_loss':  self.risk_metrics.probability_of_loss,
                'var_95':               self.risk_metrics.var_95,
                'var_99':               self.risk_metrics.var_99,
                'cvar_95':              self.risk_metrics.cvar_95,
                'cvar_99':              self.risk_metrics.cvar_99,
                'sharpe_ratio':         self.risk_metrics.sharpe_ratio,
                'sortino_ratio':        self.risk_metrics.sortino_ratio,
                'downside_std':         self.risk_metrics.downside_std,
                'skewness':             self.risk_metrics.skewness,
                'kurtosis':             self.risk_metrics.kurtosis,
            },
            'expected_utility': self.expected_utility,
            'risk_aversion': self.risk_aversion,
            'recommendations': [r.to_dict() for r in self.recommendations],
            'scenario_comparison': self.scenario_comparison,
            'overall_assessment': self.overall_assessment,
            'overall_score': self.overall_score,
            'summary': self.summary,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Cálculos de utilidad y riesgo
# ─────────────────────────────────────────────────────────────────────────────

def _compute_risk_metrics(
    profit_samples: np.ndarray,
    risk_free_rate: float = 0.0,
) -> RiskMetrics:
    """
    Calcula el conjunto completo de métricas de riesgo sobre la distribución
    de ganancias simuladas.

    Incluye VaR, CVaR, Sharpe y Sortino. Todas las operaciones son vectorizadas.
    """
    if len(profit_samples) == 0:
        raise ValueError("profit_samples no puede estar vacío")

    from scipy import stats as scipy_stats

    mean = float(np.mean(profit_samples))
    std  = float(np.std(profit_samples, ddof=1)) if len(profit_samples) > 1 else 0.0

    def pct(p: float) -> float:
        return float(np.percentile(profit_samples, p))

    # ── VaR y CVaR ───────────────────────────────────────────────────────────
    var_95_threshold = pct(5)
    var_99_threshold = pct(1)

    tail_95 = profit_samples[profit_samples <= var_95_threshold]
    tail_99 = profit_samples[profit_samples <= var_99_threshold]
    cvar_95 = float(np.mean(tail_95)) if len(tail_95) > 0 else var_95_threshold
    cvar_99 = float(np.mean(tail_99)) if len(tail_99) > 0 else var_99_threshold

    # ── Ratios de rendimiento ─────────────────────────────────────────────────
    excess_return = mean - risk_free_rate
    sharpe  = excess_return / std if std > 0 else None

    # Sortino: penaliza solo la volatilidad a la baja (retornos < risk_free_rate)
    downside_returns = profit_samples[profit_samples < risk_free_rate]
    if len(downside_returns) > 1:
        downside_std_val = float(np.std(downside_returns, ddof=1))
        sortino = excess_return / downside_std_val if downside_std_val > 0 else None
    else:
        downside_std_val = None
        sortino = None

    # ── Momentos estadísticos ─────────────────────────────────────────────────
    skewness = float(scipy_stats.skew(profit_samples))
    kurt     = float(scipy_stats.kurtosis(profit_samples))

    return RiskMetrics(
        mean=mean,
        std=std,
        variance=std ** 2,
        skewness=skewness,
        kurtosis=kurt,
        p1=pct(1),  p5=pct(5),  p10=pct(10),
        p25=pct(25), p50=pct(50), p75=pct(75),
        p90=pct(90), p95=pct(95), p99=pct(99),
        probability_of_loss=float(np.mean(profit_samples < 0)),
        probability_breakeven=float(np.mean(profit_samples >= 0)),
        var_95=var_95_threshold,
        var_99=var_99_threshold,
        cvar_95=cvar_95,
        cvar_99=cvar_99,
        sharpe_ratio=sharpe,
        sortino_ratio=sortino,
        downside_std=downside_std_val,
    )


def _compute_cara_utility(
    profit_samples: np.ndarray,
    risk_aversion: float,
) -> float:
    """
    Calcula la utilidad esperada con función CARA (Constant Absolute Risk Aversion).

        U(π) = -exp(-λ·π) / λ    (λ ≠ 0)
        U(π) = π                  (λ = 0, neutro al riesgo)

    Protección ante overflow numérico:
    · Los exponentes -λπ se recortan al rango [-500, 500] antes de exp().
    · float64 puede representar exp de hasta ≈ 709; el clip en 500 deja margen.

    Args:
        profit_samples: array de ganancias por escenario
        risk_aversion:  λ — positivo = averso, negativo = amante del riesgo
                        Rango típico para PyMEs: 1e-5 a 1e-2

    Returns:
        Utilidad esperada (escalar float)
    """
    if abs(risk_aversion) < 1e-10:
        return float(np.mean(profit_samples))

    lam = risk_aversion
    # Clamp exponentes para evitar overflow (exp > 500 → inf en float64)
    exponents = np.clip(-lam * profit_samples, -500.0, 500.0)
    utilities = -np.exp(exponents) / lam
    return float(np.mean(utilities))



# ─────────────────────────────────────────────────────────────────────────────
# Motor de decisión principal
# ─────────────────────────────────────────────────────────────────────────────

class DecisionEngine:
    """
    Motor de apoyo a la toma de decisiones financieras.

    Opera sobre los resultados ya calculados por el motor de simulación.
    No hace supuestos sobre el sector de la empresa.

    Uso::

        engine = DecisionEngine(risk_aversion=0.001)
        report = engine.analyze(
            profit_samples=np.array([...]),
            demand_samples=np.array([...]),
            revenue_samples=np.array([...]),
            aggregated_vars={'IT': 50000, 'TG': 35000, ...},
            company_profile=profile,  # opcional
        )
    """

    def __init__(
        self,
        risk_aversion: float = 0.001,
        risk_free_rate: float = 0.0,
        min_profit_margin_pct: float = 10.0,
        max_cost_revenue_ratio: float = 70.0,
        max_probability_of_loss: float = 0.20,
    ):
        self.risk_aversion = risk_aversion
        self.risk_free_rate = risk_free_rate
        self._rec_engine = RecommendationService(
            min_profit_margin_pct=min_profit_margin_pct,
            max_cost_revenue_ratio=max_cost_revenue_ratio,
            max_probability_of_loss=max_probability_of_loss,
        )

    @classmethod
    def from_company_profile(cls, profile) -> 'DecisionEngine':
        """Construye el motor con parámetros del CompanyProfile de Django."""
        return cls(
            min_profit_margin_pct=profile.min_profit_margin_pct,
            max_cost_revenue_ratio=profile.max_cost_revenue_ratio,
        )

    def analyze(
        self,
        profit_samples: np.ndarray,
        demand_samples: np.ndarray,
        revenue_samples: np.ndarray,
        aggregated_vars: Optional[Dict[str, float]] = None,
    ) -> DecisionReport:
        """
        Analiza los resultados de N escenarios y genera un reporte de decisión.

        Args:
            profit_samples:  array de ganancia por escenario (shape: [N])
            demand_samples:  array de demanda por escenario (shape: [N])
            revenue_samples: array de ingresos por escenario (shape: [N])
            aggregated_vars: media de variables de negocio (dict nombre→valor)

        Returns:
            DecisionReport completo.
        """
        if aggregated_vars is None:
            aggregated_vars = {}

        profit_samples = np.asarray(profit_samples, dtype=float)
        demand_samples = np.asarray(demand_samples, dtype=float)
        revenue_samples = np.asarray(revenue_samples, dtype=float)

        # 1. Métricas de riesgo
        risk = _compute_risk_metrics(profit_samples, self.risk_free_rate)

        # 2. Utilidad esperada
        eu = _compute_cara_utility(profit_samples, self.risk_aversion)

        # 3. Recomendaciones
        # Combinar vars con estadísticas de demanda/ingreso para reglas
        vars_extended = {
            'IT': float(np.mean(revenue_samples)),
            'DE': float(np.mean(demand_samples)),
            **aggregated_vars,
        }
        recommendations = self._rec_engine.generate(risk, vars_extended)

        # 4. Comparación de escenarios
        scenario_comparison = self._build_scenario_comparison(
            profit_samples, demand_samples, revenue_samples
        )

        # 5. Evaluación global
        assessment, score, summary = self._assess_overall(risk, recommendations)

        return DecisionReport(
            risk_metrics=risk,
            expected_utility=eu,
            risk_aversion=self.risk_aversion,
            recommendations=recommendations,
            scenario_comparison=scenario_comparison,
            overall_assessment=assessment,
            overall_score=score,
            summary=summary,
        )

    # ── Comparación de escenarios ─────────────────────────────────────────────

    def _build_scenario_comparison(
        self,
        profit_samples: np.ndarray,
        demand_samples: np.ndarray,
        revenue_samples: np.ndarray,
    ) -> Dict:
        """Construye tabla comparativa de escenarios pesimista / base / optimista."""
        def _scenario(pct: float) -> Dict:
            idx = int(np.argmin(np.abs(profit_samples - np.percentile(profit_samples, pct))))
            return {
                'percentile': pct,
                'demand': float(demand_samples[idx]),
                'revenue': float(revenue_samples[idx]),
                'profit': float(profit_samples[idx]),
                'profit_margin_pct': (
                    float(profit_samples[idx] / revenue_samples[idx] * 100)
                    if revenue_samples[idx] > 0 else 0.0
                ),
            }

        return {
            'pessimistic_p5':  _scenario(5),
            'conservative_p25': _scenario(25),
            'base_p50':        _scenario(50),
            'optimistic_p75':  _scenario(75),
            'very_optimistic_p95': _scenario(95),
        }

    # ── Evaluación global ─────────────────────────────────────────────────────

    def _assess_overall(
        self,
        risk: RiskMetrics,
        recommendations: List[Recommendation],
    ) -> Tuple[str, float, str]:
        """
        Calcula:
        - assessment: 'viable' | 'riesgoso' | 'no_viable'
        - score: 0.0–1.0
        - summary: texto descriptivo en español
        """
        n_critical = sum(1 for r in recommendations if r.severity == 'critical')
        n_warning = sum(1 for r in recommendations if r.severity == 'warning')

        # Score base desde métricas de riesgo
        # Mayor P(ganancia) → mejor; menor variabilidad → mejor
        p_gain_score = min(1.0, risk.probability_breakeven)         # 0–1
        var_score = 1.0 / (1.0 + abs(risk.var_95) / max(risk.mean, 1))  # 0–1
        margin_score = min(1.0, max(0.0, risk.mean / max(abs(risk.std), 1) * 0.3))

        raw_score = 0.5 * p_gain_score + 0.3 * var_score + 0.2 * margin_score

        # Penalizar por alertas críticas y advertencias
        score = max(0.0, raw_score - 0.15 * n_critical - 0.05 * n_warning)

        # Clasificación
        if n_critical > 0 or risk.probability_of_loss > 0.40:
            assessment = 'no_viable'
        elif n_warning > 2 or risk.probability_of_loss > 0.20:
            assessment = 'riesgoso'
        else:
            assessment = 'viable'

        # Resumen
        summaries = {
            'viable': (
                f"La operación es financieramente viable con P(ganancia)={risk.probability_breakeven:.1%}. "
                f"Ganancia esperada: {risk.mean:,.0f}, VaR 95%: {risk.var_95:,.0f}."
            ),
            'riesgoso': (
                f"La operación presenta riesgos moderados. "
                f"P(pérdida)={risk.probability_of_loss:.1%}. "
                f"Se identificaron {n_warning} alertas que requieren atención."
            ),
            'no_viable': (
                f"La operación presenta riesgos críticos. "
                f"P(pérdida)={risk.probability_of_loss:.1%}. "
                f"{n_critical} alerta(s) crítica(s) requieren acción inmediata."
            ),
        }

        return assessment, round(score, 4), summaries[assessment]


# ─────────────────────────────────────────────────────────────────────────────
# Función pública de alto nivel
# ─────────────────────────────────────────────────────────────────────────────

def analizar_decision(
    profit_samples: np.ndarray,
    demand_samples: np.ndarray,
    revenue_samples: np.ndarray,
    aggregated_vars: Optional[Dict[str, float]] = None,
    risk_aversion: float = 0.001,
    min_profit_margin_pct: float = 10.0,
    max_cost_revenue_ratio: float = 70.0,
) -> DecisionReport:
    """
    Función de alto nivel para obtener un reporte de decisión.

    Example::

        report = analizar_decision(
            profit_samples=profits,
            demand_samples=demands,
            revenue_samples=revenues,
            aggregated_vars={'IT': 50000, 'TG': 35000, 'FU': 0.82},
            risk_aversion=0.001,
        )
        print(report.overall_assessment)   # 'viable'
        for rec in report.recommendations:
            print(rec.severity, rec.title)
    """
    engine = DecisionEngine(
        risk_aversion=risk_aversion,
        min_profit_margin_pct=min_profit_margin_pct,
        max_cost_revenue_ratio=max_cost_revenue_ratio,
    )
    return engine.analyze(profit_samples, demand_samples, revenue_samples, aggregated_vars)
