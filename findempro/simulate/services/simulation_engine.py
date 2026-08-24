"""
simulation_engine.py  [LEGACY — standalone, sin persistencia en BD]
====================================================================
Motor Monte Carlo ligero para endpoints de API que NO disponen de una
instancia Simulation en BD (SimulateAPIView, RiskAnalysisAPIView,
ScenariosAPIView).  No requiere ORM.

Para el pipeline completo con persistencia (Celery, FullPipelineAPIView):
    → simulate.services.simulation_service.SimulationService.run_full_pipeline()

Soporta cualquier sector: producción, retail, servicios, agro, manufactura.
Usa distribuciones probabilísticas (Normal, Log-Normal, Gamma, Uniforme, Exponencial).
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy import stats
from scipy.stats import norm, lognorm, gamma, uniform, expon

from modeling.statistics import fit_distributions

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────

@dataclass
class SimulationConfig:
    """Configuración completa de una simulación Monte Carlo."""
    n_iterations: int = 10000
    confidence_level: float = 0.95
    time_periods: int = 30           # días / semanas / meses a simular
    random_seed: Optional[int] = None
    distribution_type: str = 'normal'  # normal | lognormal | gamma | uniform | exponential
    # Parámetros de demanda
    demand_mean: float = 1000.0
    demand_std: float = 150.0
    demand_min: Optional[float] = None
    demand_max: Optional[float] = None
    # Parámetros económicos
    unit_price: float = 10.0
    unit_cost: float = 6.0
    fixed_costs: float = 5000.0
    investment: Optional[float] = None
    # Estacionalidad (lista de 12 factores — se extrapola si time_periods != 12)
    seasonality_factors: List[float] = field(default_factory=lambda: [1.0] * 12)

    def __post_init__(self):
        if self.n_iterations < 1:
            raise ValueError("n_iterations debe ser al menos 1.")
        if self.time_periods < 1:
            raise ValueError("time_periods debe ser al menos 1.")
        if not 0 < self.confidence_level < 1:
            raise ValueError("confidence_level debe estar entre 0 y 1 (exclusivos).")
        numeric_nonnegative = {
            "demand_mean": self.demand_mean,
            "demand_std": self.demand_std,
            "unit_price": self.unit_price,
            "unit_cost": self.unit_cost,
            "fixed_costs": self.fixed_costs,
        }
        for name, value in numeric_nonnegative.items():
            if not math.isfinite(float(value)) or value < 0:
                raise ValueError(f"{name} debe ser un número finito no negativo.")
        if self.demand_min is not None and self.demand_max is not None and self.demand_min > self.demand_max:
            raise ValueError("demand_min no puede superar demand_max.")
        if any(not math.isfinite(float(factor)) or factor < 0 for factor in self.seasonality_factors):
            raise ValueError("seasonality_factors debe contener números finitos no negativos.")
        if self.investment is not None and (not math.isfinite(float(self.investment)) or self.investment < 0):
            raise ValueError("investment debe ser un número finito no negativo.")


@dataclass
class ScenarioResult:
    """Resultado de un escenario de simulación."""
    name: str
    demand_percentile: float        # Percentil de la distribución de demanda usado
    demand_value: float
    revenue: float
    variable_costs: float
    total_costs: float
    gross_profit: float
    profit_margin_pct: float
    roi: Optional[float]


@dataclass
class SimulationResult:
    """Resultado completo de una simulación Monte Carlo."""
    # Estadísticas de demanda
    demand_mean: float
    demand_std: float
    demand_median: float
    demand_p5: float                 # Percentil 5 — escenario pesimista
    demand_p25: float
    demand_p75: float
    demand_p95: float                # Percentil 95 — escenario optimista
    demand_samples: np.ndarray

    # Estadísticas financieras
    revenue_mean: float
    revenue_std: float
    revenue_p5: float
    revenue_p95: float

    profit_mean: float
    profit_std: float
    profit_p5: float
    profit_p95: float
    # La mediana faltaba: en una distribución de utilidad asimétrica la media no
    # es el "escenario típico", y es la mediana la que responde a "¿cómo me suele
    # ir?". Sin ella, quien consume el resultado acaba usando la media como si lo
    # fuera.
    profit_median: float

    # Métricas de riesgo
    probability_of_loss: float       # P(profit < 0)
    probability_breakeven: float     # P(profit >= 0)
    value_at_risk_95: float          # VaR al 95%: máxima pérdida esperada
    expected_shortfall: float        # CVaR/ES: pérdida promedio en el 5% peor

    # Intervalos de confianza
    demand_ci_lower: float
    demand_ci_upper: float
    profit_ci_lower: float
    profit_ci_upper: float

    # Escenarios
    scenarios: List[ScenarioResult] = field(default_factory=list)

    # Serie temporal (por período)
    time_series: List[Dict] = field(default_factory=list)

    # Metadatos
    n_iterations: int = 10000
    distribution_used: str = 'normal'
    distribution_fit_score: float = 0.0


# ─────────────────────────────────────────────
# Motor principal
# ─────────────────────────────────────────────

class MonteCarloEngine:
    """
    Motor de simulación Monte Carlo genérico para apoyo a decisiones financieras.

    Uso:
        config = SimulationConfig(demand_mean=5000, demand_std=800, unit_price=12.5, ...)
        engine = MonteCarloEngine(config)
        result = engine.run()
    """

    SUPPORTED_DISTRIBUTIONS = ('normal', 'lognormal', 'gamma', 'uniform', 'exponential')

    def __init__(self, config: SimulationConfig):
        self.config = config
        # RNG de instancia (thread-safe): evita el estado global de np.random.seed,
        # que correlaciona resultados entre requests concurrentes. default_rng(None)
        # produce una semilla aleatoria; con seed fija es reproducible.
        self.rng = np.random.default_rng(config.random_seed)

    # ── Distribuciones ─────────────────────────────────────────────────────────

    def _get_distribution(self) -> stats.rv_continuous:
        """Construye el objeto de distribución scipy según la configuración."""
        d = self.config.distribution_type.lower()
        mu = self.config.demand_mean
        sigma = self.config.demand_std

        if d == 'normal':
            return norm(loc=mu, scale=max(sigma, 1e-6))

        elif d == 'lognormal':
            # Convertir media/std real → parámetros log-normales
            if mu <= 0:
                mu = abs(mu) + 1
            cv2 = (sigma / mu) ** 2 if mu > 0 else 0.01
            log_sigma = np.sqrt(np.log(1 + cv2))
            log_mu = np.log(mu) - log_sigma ** 2 / 2
            return lognorm(s=log_sigma, scale=np.exp(log_mu))

        elif d == 'gamma':
            # k (shape) y θ (scale) desde media y varianza
            sigma = max(sigma, 1e-6)
            shape = (mu / sigma) ** 2
            scale = sigma ** 2 / mu
            return gamma(a=max(shape, 0.01), scale=max(scale, 0.01))

        elif d == 'uniform':
            low = self.config.demand_min if self.config.demand_min is not None else mu - 3 * sigma
            high = self.config.demand_max if self.config.demand_max is not None else mu + 3 * sigma
            low, high = min(low, high - 1), max(low + 1, high)
            return uniform(loc=low, scale=high - low)

        elif d == 'exponential':
            rate = 1.0 / max(mu, 1e-6)
            return expon(scale=1.0 / rate)

        else:
            raise ValueError(f"Distribución '{d}' no soportada. Use: {self.SUPPORTED_DISTRIBUTIONS}")

    def _sample_demand(self, size: int) -> np.ndarray:
        """Genera muestras de demanda asegurando no-negatividad."""
        dist = self._get_distribution()
        samples = dist.rvs(size=size, random_state=self.rng)
        # Asegurar no-negatividad (la demanda no puede ser negativa)
        return np.maximum(samples, 0.0)

    # ── Estacionalidad ──────────────────────────────────────────────────────────

    def _get_period_seasonality(self, period_idx: int) -> float:
        """Retorna el factor de estacionalidad para el período dado."""
        factors = self.config.seasonality_factors
        if not factors or len(factors) == 0:
            return 1.0
        return factors[period_idx % len(factors)]

    # ── Cálculos financieros ───────────────────────────────────────────────────

    def _compute_financials(self, demand_samples: np.ndarray) -> Dict[str, np.ndarray]:
        """Calcula métricas financieras para cada muestra de demanda."""
        price = self.config.unit_price
        cost = self.config.unit_cost
        fixed = self.config.fixed_costs

        revenue = demand_samples * price
        variable_costs = demand_samples * cost
        total_costs = variable_costs + fixed
        gross_profit = revenue - total_costs
        profit_margin = np.where(revenue > 0, (gross_profit / revenue) * 100, 0.0)
        # Total operating costs are not an investment basis. ROI is exposed
        # only when the caller explicitly declares invested capital.
        roi = None

        return {
            'revenue': revenue,
            'variable_costs': variable_costs,
            'total_costs': total_costs,
            'gross_profit': gross_profit,
            'profit_margin_pct': profit_margin,
            'roi': roi,
        }

    # ── Métricas de riesgo ──────────────────────────────────────────────────────

    @staticmethod
    def _compute_risk_metrics(profit_samples: np.ndarray, confidence_level: float) -> Dict:
        """Calcula métricas de riesgo financiero."""
        alpha = 1 - confidence_level  # ej: 0.05 para 95%

        prob_loss = float(np.mean(profit_samples < 0))
        var_threshold = np.percentile(profit_samples, alpha * 100)
        tail_losses = profit_samples[profit_samples <= var_threshold]
        expected_shortfall = float(np.mean(tail_losses)) if len(tail_losses) > 0 else float(var_threshold)

        return {
            'probability_of_loss': prob_loss,
            'probability_breakeven': 1.0 - prob_loss,
            'value_at_risk_95': float(var_threshold),
            'expected_shortfall': expected_shortfall,
            'confidence_level': confidence_level,
        }

    # ── Intervalos de confianza ─────────────────────────────────────────────────

    @staticmethod
    def _confidence_interval(samples: np.ndarray, confidence: float) -> Tuple[float, float]:
        """Calcula el intervalo de confianza bootstrap para las muestras."""
        alpha = (1 - confidence) / 2
        return (float(np.percentile(samples, alpha * 100)),
                float(np.percentile(samples, (1 - alpha) * 100)))

    # ── Escenarios ─────────────────────────────────────────────────────────────

    def _build_scenarios(self, demand_samples: np.ndarray) -> List[ScenarioResult]:
        """Construye escenarios pesimista / base / optimista / extremo."""
        scenarios_def = [
            ('Pesimista', 5),
            ('Conservador', 25),
            ('Base', 50),
            ('Optimista', 75),
            ('Muy Optimista', 95),
        ]
        results = []
        price = self.config.unit_price
        cost = self.config.unit_cost
        fixed = self.config.fixed_costs

        for name, pct in scenarios_def:
            d = float(np.percentile(demand_samples, pct))
            rev = d * price
            var_c = d * cost
            total_c = var_c + fixed
            gp = rev - total_c
            margin = (gp / rev * 100) if rev > 0 else 0.0
            roi = (gp / self.config.investment * 100) if self.config.investment and self.config.investment > 0 else None
            results.append(ScenarioResult(
                name=name,
                demand_percentile=pct,
                demand_value=d,
                revenue=rev,
                variable_costs=var_c,
                total_costs=total_c,
                gross_profit=gp,
                profit_margin_pct=margin,
                roi=roi,
            ))
        return results

    # ── Serie temporal ──────────────────────────────────────────────────────────

    def _build_time_series(self) -> List[Dict]:
        """
        Simula la evolución período a período aplicando estacionalidad.
        Para cada período: genera N muestras → calcula estadísticas.
        """
        series = []
        n_periods = self.config.time_periods
        n_iter = max(1000, self.config.n_iterations // n_periods)

        for t in range(n_periods):
            seasonal_factor = self._get_period_seasonality(t)
            # Ajustar media por estacionalidad
            adjusted_mean = self.config.demand_mean * seasonal_factor
            original_mean = self.config.demand_mean
            self.config.demand_mean = adjusted_mean

            samples = self._sample_demand(n_iter)
            fin = self._compute_financials(samples)

            self.config.demand_mean = original_mean  # restaurar

            series.append({
                'period': t + 1,
                'seasonality_factor': seasonal_factor,
                'demand_mean': float(np.mean(samples)),
                'demand_p5': float(np.percentile(samples, 5)),
                'demand_p95': float(np.percentile(samples, 95)),
                'revenue_mean': float(np.mean(fin['revenue'])),
                'profit_mean': float(np.mean(fin['gross_profit'])),
                'profit_p5': float(np.percentile(fin['gross_profit'], 5)),
                'profit_p95': float(np.percentile(fin['gross_profit'], 95)),
            })
        return series

    # ── Ajuste automático de distribución ──────────────────────────────────────

    @staticmethod
    def fit_best_distribution(data: np.ndarray) -> Tuple[str, float]:
        """
        Ajusta varias distribuciones a los datos históricos y retorna
        la que mejor se ajusta (menor KS statistic).

        Returns:
            (distribution_name, ks_statistic)
        """
        data = np.asarray(data, dtype=float)
        fitted = fit_distributions(data.tolist(), data_semantics='continuous')
        best_name = fitted['ranking']['selected_distribution']
        diagnostic = next(
            item for item in fitted['candidates']
            if item['distribution'] == best_name
        )
        return best_name, diagnostic['statistic']

    # ── Ejecución principal ─────────────────────────────────────────────────────

    def run(self) -> SimulationResult:
        """
        Ejecuta la simulación Monte Carlo completa.

        Returns:
            SimulationResult con todas las métricas, escenarios y serie temporal.
        """
        cfg = self.config
        n = max(1000, cfg.n_iterations)

        logger.info(f"[MC] Iniciando simulación: {n} iteraciones, dist={cfg.distribution_type}")

        # 1. Muestras de demanda
        demand_samples = self._sample_demand(n)

        # 2. Financiero
        fin = self._compute_financials(demand_samples)

        # 3. Riesgo
        risk = self._compute_risk_metrics(fin['gross_profit'], cfg.confidence_level)

        # 4. ICs
        d_ci = self._confidence_interval(demand_samples, cfg.confidence_level)
        p_ci = self._confidence_interval(fin['gross_profit'], cfg.confidence_level)

        # 5. Escenarios
        scenarios = self._build_scenarios(demand_samples)

        # 6. Serie temporal
        time_series = self._build_time_series()

        result = SimulationResult(
            # Demanda
            demand_mean=float(np.mean(demand_samples)),
            demand_std=float(np.std(demand_samples)),
            demand_median=float(np.median(demand_samples)),
            demand_p5=float(np.percentile(demand_samples, 5)),
            demand_p25=float(np.percentile(demand_samples, 25)),
            demand_p75=float(np.percentile(demand_samples, 75)),
            demand_p95=float(np.percentile(demand_samples, 95)),
            demand_samples=demand_samples,
            # Ingresos
            revenue_mean=float(np.mean(fin['revenue'])),
            revenue_std=float(np.std(fin['revenue'])),
            revenue_p5=float(np.percentile(fin['revenue'], 5)),
            revenue_p95=float(np.percentile(fin['revenue'], 95)),
            # Utilidades
            profit_mean=float(np.mean(fin['gross_profit'])),
            profit_std=float(np.std(fin['gross_profit'])),
            profit_p5=float(np.percentile(fin['gross_profit'], 5)),
            profit_p95=float(np.percentile(fin['gross_profit'], 95)),
            profit_median=float(np.median(fin['gross_profit'])),
            # Riesgo
            probability_of_loss=risk['probability_of_loss'],
            probability_breakeven=risk['probability_breakeven'],
            value_at_risk_95=risk['value_at_risk_95'],
            expected_shortfall=risk['expected_shortfall'],
            # ICs
            demand_ci_lower=d_ci[0],
            demand_ci_upper=d_ci[1],
            profit_ci_lower=p_ci[0],
            profit_ci_upper=p_ci[1],
            # Colecciones
            scenarios=scenarios,
            time_series=time_series,
            n_iterations=n,
            distribution_used=cfg.distribution_type,
        )

        logger.info(f"[MC] Simulación completada. P(pérdida)={risk['probability_of_loss']:.2%}")
        return result

    def to_dict(self) -> Dict:
        """Ejecuta y retorna el resultado como diccionario serializable."""
        result = self.run()
        return {
            'demand': {
                'mean': result.demand_mean,
                'std': result.demand_std,
                'median': result.demand_median,
                'p5': result.demand_p5,
                'p25': result.demand_p25,
                'p75': result.demand_p75,
                'p95': result.demand_p95,
                'ci_lower': result.demand_ci_lower,
                'ci_upper': result.demand_ci_upper,
            },
            'revenue': {
                'mean': result.revenue_mean,
                'std': result.revenue_std,
                'p5': result.revenue_p5,
                'p95': result.revenue_p95,
            },
            'profit': {
                'mean': result.profit_mean,
                'std': result.profit_std,
                'p5': result.profit_p5,
                'p95': result.profit_p95,
                # Monetary profit is not a periodized return series. Keep
                # these fields explicit so clients cannot present a fabricated
                # Sharpe/Sortino interpretation.
                'var_95': result.value_at_risk_95,
                'cvar_95': result.expected_shortfall,
                'sharpe_ratio': None,
                'ratio_basis': 'not_applicable_monetary_profit',
                'var_semantics': 'lower_profit_quantile',
                'cvar_semantics': 'lower_tail_mean_profit',
                'ci_lower': result.profit_ci_lower,
                'ci_upper': result.profit_ci_upper,
            },
            'risk': {
                'probability_of_loss': result.probability_of_loss,
                'probability_breakeven': result.probability_breakeven,
                # Legacy value_at_risk_95/expected_shortfall keys remain for
                # clients, but the configured confidence is authoritative.
                'confidence_level': self.config.confidence_level,
                'var_confidence_level': self.config.confidence_level,
                'cvar_confidence_level': self.config.confidence_level,
                'var_semantics': 'lower_profit_quantile',
                'cvar_semantics': 'lower_tail_mean_profit',
                'value_at_risk_95': result.value_at_risk_95,
                'expected_shortfall': result.expected_shortfall,
            },
            'scenarios': [
                {
                    'name': s.name,
                    'demand_percentile': s.demand_percentile,
                    'demand_value': s.demand_value,
                    'revenue': s.revenue,
                    'total_costs': s.total_costs,
                    'gross_profit': s.gross_profit,
                    'profit_margin_pct': s.profit_margin_pct,
                    'roi': s.roi,
                }
                for s in result.scenarios
            ],
            'time_series': result.time_series,
            'metadata': {
                'n_iterations': result.n_iterations,
                'distribution_used': result.distribution_used,
                'confidence_level': self.config.confidence_level,
            },
        }
