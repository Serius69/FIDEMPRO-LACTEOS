"""
monte_carlo.py
==============
Módulo Monte Carlo SEPARADO del motor de eventos discretos.

Responsabilidad única: generar escenarios probabilísticos.
NO ejecuta simulaciones de negocio ni calcula ecuaciones.

Flujo de integración:
  1. generate_scenarios()  →  Lista[OperationScenario]
  2. Cada OperationScenario entra al DiscreteEventEngine
  3. Los resultados se agregan en aggregate_results()
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Union

if TYPE_CHECKING:
    from business.models import CompanyProfile
    from simulate.models import Simulation

import numpy as np
from scipy import stats
from scipy.stats import norm, lognorm, gamma, uniform, expon

from simulate.core.discrete_engine import OperationScenario

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Configuración de generación de escenarios
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class MonteCarloConfig:
    """
    Parámetros para la generación de escenarios Monte Carlo.
    Independiente de la estructura interna de la empresa.
    """
    n_scenarios: int = 10_000
    confidence_level: float = 0.95
    n_periods: int = 30
    random_seed: Optional[int] = None

    # Distribución de demanda
    distribution: str = 'normal'        # normal | lognormal | gamma | uniform | exponential
    demand_mean: float = 1_000.0
    demand_std: float = 150.0
    demand_min: Optional[float] = None  # para distribución uniforme
    demand_max: Optional[float] = None  # para distribución uniforme

    # Estacionalidad (12 factores mensuales)
    seasonality_factors: List[float] = field(default_factory=lambda: [1.0] * 12)

    # Variaciones de precio y costo (distribución normal centrada en 0)
    price_volatility: float = 0.0       # desviación estándar del % de variación de precio
    cost_volatility: float = 0.0        # desviación estándar del % de variación de costo

    @classmethod
    def from_simulation(
        cls,
        simulation: 'Simulation',
        company_profile: Optional['CompanyProfile'] = None,
        n_scenarios: int = 1_000,
    ) -> 'MonteCarloConfig':
        """
        Factory: construye un MonteCarloConfig desde una instancia Simulation + CompanyProfile.

        Centraliza:
          · mapeo distribution_type (int PDP) → nombre de distribución (str)
          · resolución de preferencia 'auto' vía DistributionFactory.fit_best()
          · estacionalidad desde CompanyProfile (12 factores)

        Args:
            simulation:      instancia de simulate.models.Simulation (necesita fk_fdp)
            company_profile: instancia de business.models.CompanyProfile (opcional)
            n_scenarios:     escenarios MC a generar por período

        Returns:
            MonteCarloConfig lista para ScenarioGenerator.
        """
        demand_stats   = simulation.get_demand_statistics()
        demand_history = simulation.get_demand_history_array()

        distribution = cls._resolve_distribution(
            dist_type=getattr(simulation.fk_fdp, 'distribution_type', 1),
            demand_history=demand_history,
            company_profile=company_profile,
        )

        seasonality = (
            company_profile.get_seasonality_factors()
            if company_profile is not None
            else [1.0] * 12
        )

        return cls(
            n_scenarios=n_scenarios,
            confidence_level=getattr(simulation, 'confidence_level', 0.95),
            n_periods=simulation.duration_in_days,
            random_seed=getattr(simulation, 'random_seed', None),
            distribution=distribution,
            demand_mean=demand_stats['mean'],
            demand_std=max(demand_stats['std'], 1e-6),
            seasonality_factors=seasonality,
        )

    @staticmethod
    def _resolve_distribution(
        dist_type: int,
        demand_history: np.ndarray,
        company_profile: Optional['CompanyProfile'] = None,
    ) -> str:
        """
        Traduce distribution_type (int) a nombre de distribución (str).

        Si company_profile.distribution_preference == 'auto', usa
        DistributionFactory.fit_best() para seleccionar el mejor ajuste KS
        sobre los datos históricos de demanda.
        """
        if (
            company_profile is not None
            and getattr(company_profile, 'distribution_preference', None) == 'auto'
        ):
            best_dist, ks = DistributionFactory.fit_best(demand_history)
            logger.info(
                "distribution_preference='auto': mejor ajuste = %s (KS=%.4f)",
                best_dist, ks,
            )
            return best_dist

        _MAP = {1: 'normal', 2: 'exponential', 3: 'lognormal',
                4: 'gamma',  5: 'uniform',      6: 'poisson'}
        return _MAP.get(dist_type, 'normal')


# ─────────────────────────────────────────────────────────────────────────────
# Resultados agregados
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AggregatedResult:
    """Estadísticas agregadas sobre N escenarios simulados."""
    # Demanda
    demand_mean: float
    demand_std: float
    demand_p5: float
    demand_p25: float
    demand_p75: float
    demand_p95: float

    # Ingresos
    revenue_mean: float
    revenue_std: float
    revenue_p5: float
    revenue_p95: float

    # Utilidades
    profit_mean: float
    profit_std: float
    profit_p5: float
    profit_p95: float

    # Métricas de riesgo
    probability_of_loss: float
    probability_breakeven: float
    value_at_risk: float         # VaR al nivel de confianza configurado
    expected_shortfall: float    # CVaR / ES

    # Intervalos de confianza
    demand_ci_lower: float
    demand_ci_upper: float
    profit_ci_lower: float
    profit_ci_upper: float

    # Escenarios descriptivos
    scenario_pessimistic: Dict
    scenario_base: Dict
    scenario_optimistic: Dict

    # Metadatos
    n_scenarios: int
    distribution_used: str
    confidence_level: float


# ─────────────────────────────────────────────────────────────────────────────
# Generador de distribuciones
# ─────────────────────────────────────────────────────────────────────────────

class DistributionFactory:
    """
    Construye objetos scipy a partir de los parámetros de MonteCarloConfig.

    Distribuciones soportadas:
      normal      – demanda simétrica alrededor de la media
      lognormal   – demanda asimétrica positiva (típica en consumo)
      gamma       – similar a lognormal pero más flexible
      uniform     – demanda en rango fijo (requiere demand_min/max)
      exponential – demanda memoryless (tiempo entre eventos)
      poisson     – demanda discreta de eventos por período
    """

    SUPPORTED = ('normal', 'lognormal', 'gamma', 'uniform', 'exponential', 'poisson')

    @classmethod
    def build(cls, config: 'MonteCarloConfig') -> Union[stats.rv_continuous, stats.rv_discrete]:
        """
        Retorna un objeto scipy frozen-distribution listo para .rvs().
        Para Poisson retorna scipy.stats.poisson (rv_discrete).
        """
        d = config.distribution.lower()
        mu = config.demand_mean
        sigma = max(config.demand_std, 1e-6)

        if d == 'normal':
            return norm(loc=mu, scale=sigma)

        elif d == 'lognormal':
            # Parametrización vía media y desv. estándar de la variable original
            mu_pos = abs(mu) + 1 if mu <= 0 else mu
            cv2 = (sigma / mu_pos) ** 2
            s = np.sqrt(np.log(1 + cv2))
            scale = np.exp(np.log(mu_pos) - s ** 2 / 2)
            return lognorm(s=max(s, 1e-6), scale=max(scale, 1e-6))

        elif d == 'gamma':
            # shape k = (μ/σ)², scale θ = σ²/μ
            shape = max((mu / sigma) ** 2, 0.01)
            scale = max(sigma ** 2 / max(mu, 1e-6), 0.01)
            return gamma(a=shape, scale=scale)

        elif d == 'uniform':
            low  = config.demand_min if config.demand_min is not None else mu - 3 * sigma
            high = config.demand_max if config.demand_max is not None else mu + 3 * sigma
            # Garantizar low < high con al menos 1 unidad de separación
            low, high = min(low, high - 1), max(low + 1, high)
            return uniform(loc=low, scale=high - low)

        elif d == 'exponential':
            # Para exponencial, la media es el parámetro de escala (1/λ)
            return expon(scale=max(mu, 1e-6))

        elif d == 'poisson':
            # Poisson: λ = media. Devuelve rv_discrete; .rvs() genera enteros ≥ 0.
            from scipy.stats import poisson
            lambda_param = max(abs(mu), 0.1)
            return poisson(mu=lambda_param)

        else:
            raise ValueError(
                f"Distribución '{d}' no soportada. Opciones: {cls.SUPPORTED}"
            )

    @classmethod
    def fit_best(cls, data: np.ndarray) -> Tuple[str, float]:
        """
        Ajusta Normal, Log-Normal, Gamma y Exponencial a los datos históricos.
        Selecciona la distribución con menor estadístico KS.

        Args:
            data: array de datos históricos de demanda (valores positivos)

        Returns:
            (nombre_distribución, estadístico_KS)
        """
        data = np.asarray(data, dtype=float)
        data_pos = data[data > 0]
        if len(data_pos) < 10:
            return 'normal', 1.0

        candidates = [
            ('normal',      norm),
            ('lognormal',   lognorm),
            ('gamma',       gamma),
            ('exponential', expon),
        ]
        best_name, best_ks = 'normal', float('inf')

        for name, dist_cls in candidates:
            try:
                params = dist_cls.fit(data_pos)
                ks, _ = stats.kstest(data_pos, dist_cls.cdf, args=params)
                if ks < best_ks:
                    best_ks, best_name = ks, name
            except Exception:
                continue

        logger.info(
            "Mejor distribución ajustada: %s (KS=%.4f, n=%d)",
            best_name, best_ks, len(data_pos),
        )
        return best_name, best_ks


# ─────────────────────────────────────────────────────────────────────────────
# Generador de escenarios
# ─────────────────────────────────────────────────────────────────────────────

class ScenarioGenerator:
    """
    Genera escenarios probabilísticos para alimentar el DiscreteEventEngine.

    Usa numpy.random.Generator (API moderna, thread-safe) en lugar del
    estado global np.random.seed(). Cada instancia tiene su propio RNG
    inicializado con random_seed del config → reproducibilidad garantizada.
    """

    def __init__(self, config: 'MonteCarloConfig'):
        self.config = config
        # RNG encapsulado por instancia — no afecta el estado global de numpy
        self._rng = np.random.default_rng(config.random_seed)
        # Distribución scipy frozen (construida una sola vez)
        self._distribution = DistributionFactory.build(config)

    def _get_seasonality(self, period_idx: int) -> float:
        factors = self.config.seasonality_factors
        if not factors:
            return 1.0
        return factors[period_idx % len(factors)]

    def _sample_demand(self, n: int) -> np.ndarray:
        """
        Genera n muestras de demanda no-negativas usando el RNG encapsulado.

        scipy's .rvs() acepta random_state para inyectar el RNG moderno.
        """
        try:
            samples = self._distribution.rvs(size=n, random_state=self._rng)
        except TypeError:
            # Fallback por si la distribución no acepta random_state
            samples = self._distribution.rvs(size=n)
        return np.maximum(np.asarray(samples, dtype=float), 0.0)

    def generate_for_period(
        self,
        period_idx: int,
        n_scenarios: Optional[int] = None,
    ) -> List[OperationScenario]:
        """
        Genera N escenarios independientes para un único período.

        Args:
            period_idx:  índice del período (0-based)
            n_scenarios: cantidad de escenarios; usa config.n_scenarios por defecto

        Returns:
            Lista de OperationScenario listos para DiscreteEventEngine.run_period().
        """
        n = n_scenarios or self.config.n_scenarios
        demands  = self._sample_demand(n)
        seasonal = self._get_seasonality(period_idx)

        price_vars = (
            self._rng.normal(0.0, self.config.price_volatility, n)
            if self.config.price_volatility > 0
            else np.zeros(n)
        )
        cost_vars = (
            self._rng.normal(0.0, self.config.cost_volatility, n)
            if self.config.cost_volatility > 0
            else np.zeros(n)
        )

        return [
            OperationScenario(
                period_index=period_idx,
                demand_value=float(d),
                seasonality_factor=seasonal,
                price_variation=float(pv),
                cost_variation=float(cv),
            )
            for d, pv, cv in zip(demands, price_vars, cost_vars)
        ]

    def generate_time_series(self) -> List[List[OperationScenario]]:
        """
        Genera escenarios para todos los períodos configurados.

        Implementación vectorizada: muestrea T×N valores en 1-3 llamadas numpy
        en vez de T llamadas scipy separadas. El orden de la secuencia RNG difiere
        de llamar generate_for_period() T veces, pero las propiedades estadísticas
        son idénticas. Misma semilla → mismo resultado para este método.

        Returns:
            Lista[T] de Lista[N] — T períodos, N escenarios por período.
        """
        T = self.config.n_periods
        N = self.config.n_scenarios

        # ── 1 llamada scipy para todos los períodos ──────────────────────────
        all_demands = self._sample_demand(T * N).reshape(T, N)

        # ── 1 llamada numpy por variable estocástica ─────────────────────────
        if self.config.price_volatility > 0:
            all_price_vars = self._rng.normal(0.0, self.config.price_volatility, (T, N))
        else:
            all_price_vars = np.zeros((T, N))

        if self.config.cost_volatility > 0:
            all_cost_vars = self._rng.normal(0.0, self.config.cost_volatility, (T, N))
        else:
            all_cost_vars = np.zeros((T, N))

        seasonality = [self._get_seasonality(t) for t in range(T)]

        return [
            [
                OperationScenario(
                    period_index=t,
                    demand_value=float(d),
                    seasonality_factor=seasonality[t],
                    price_variation=float(pv),
                    cost_variation=float(cv),
                )
                for d, pv, cv in zip(all_demands[t], all_price_vars[t], all_cost_vars[t])
            ]
            for t in range(T)
        ]


# ─────────────────────────────────────────────────────────────────────────────
# Agregación de resultados
# ─────────────────────────────────────────────────────────────────────────────

def aggregate_results(
    profit_samples: np.ndarray,
    demand_samples: np.ndarray,
    revenue_samples: np.ndarray,
    config: MonteCarloConfig,
) -> AggregatedResult:
    """
    Agrega N resultados de simulación en estadísticas descriptivas y de riesgo.

    Args:
        profit_samples:  array de ganancia por escenario
        demand_samples:  array de demanda por escenario
        revenue_samples: array de ingresos por escenario
        config:          configuración Monte Carlo (para metadatos)

    Returns:
        AggregatedResult con todas las métricas.
    """
    cl = config.confidence_level
    alpha = 1 - cl
    half_alpha = alpha / 2

    def pct(arr: np.ndarray, p: float) -> float:
        return float(np.percentile(arr, p * 100))

    # Riesgo
    prob_loss = float(np.mean(profit_samples < 0))
    var_threshold = pct(profit_samples, alpha)
    tail = profit_samples[profit_samples <= var_threshold]
    es = float(np.mean(tail)) if len(tail) > 0 else float(var_threshold)

    # Escenarios descriptivos (percentiles clave)
    def _build_scenario(pct_val: float) -> Dict:
        idx = int(np.argmin(np.abs(demand_samples - np.percentile(demand_samples, pct_val))))
        return {
            'demand': float(demand_samples[idx]),
            'revenue': float(revenue_samples[idx]),
            'profit': float(profit_samples[idx]),
            'percentile': pct_val,
        }

    return AggregatedResult(
        # Demanda
        demand_mean=float(np.mean(demand_samples)),
        demand_std=float(np.std(demand_samples)),
        demand_p5=pct(demand_samples, 0.05),
        demand_p25=pct(demand_samples, 0.25),
        demand_p75=pct(demand_samples, 0.75),
        demand_p95=pct(demand_samples, 0.95),
        # Ingresos
        revenue_mean=float(np.mean(revenue_samples)),
        revenue_std=float(np.std(revenue_samples)),
        revenue_p5=pct(revenue_samples, 0.05),
        revenue_p95=pct(revenue_samples, 0.95),
        # Utilidades
        profit_mean=float(np.mean(profit_samples)),
        profit_std=float(np.std(profit_samples)),
        profit_p5=pct(profit_samples, 0.05),
        profit_p95=pct(profit_samples, 0.95),
        # Riesgo
        probability_of_loss=prob_loss,
        probability_breakeven=1.0 - prob_loss,
        value_at_risk=float(var_threshold),
        expected_shortfall=es,
        # Intervalos de confianza (bootstrap percentile)
        demand_ci_lower=pct(demand_samples, half_alpha),
        demand_ci_upper=pct(demand_samples, 1 - half_alpha),
        profit_ci_lower=pct(profit_samples, half_alpha),
        profit_ci_upper=pct(profit_samples, 1 - half_alpha),
        # Escenarios
        scenario_pessimistic=_build_scenario(5),
        scenario_base=_build_scenario(50),
        scenario_optimistic=_build_scenario(95),
        # Metadatos
        n_scenarios=len(profit_samples),
        distribution_used=config.distribution,
        confidence_level=cl,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Cache de resultados agregados
# ─────────────────────────────────────────────────────────────────────────────

_CACHE_TTL = 3600  # 1 hora


def _make_aggregate_cache_key(config: MonteCarloConfig) -> str:
    """
    Genera una cache key determinista a partir de los parámetros de MonteCarloConfig.
    Solo debe llamarse cuando config.random_seed is not None.
    """
    key_data = {
        'n_scenarios': config.n_scenarios,
        'confidence_level': config.confidence_level,
        'n_periods': config.n_periods,
        'random_seed': config.random_seed,
        'distribution': config.distribution,
        'demand_mean': round(config.demand_mean, 6),
        'demand_std': round(config.demand_std, 6),
        'demand_min': config.demand_min,
        'demand_max': config.demand_max,
        'seasonality_factors': list(config.seasonality_factors),
        'price_volatility': config.price_volatility,
        'cost_volatility': config.cost_volatility,
    }
    digest = hashlib.sha256(
        json.dumps(key_data, sort_keys=True).encode()
    ).hexdigest()[:20]
    return f'mc:agg:{digest}'


def cached_aggregate_results(
    profit_samples: np.ndarray,
    demand_samples: np.ndarray,
    revenue_samples: np.ndarray,
    config: MonteCarloConfig,
    force_recompute: bool = False,
) -> 'AggregatedResult':
    """
    Versión con cache de aggregate_results().

    Cachea en Redis (vía django.core.cache) usando hash(config+seed) como key.
    Solo cachea cuando config.random_seed is not None (resultados deterministas).
    TTL = 1 hora. Si Django no está disponible, delega directamente.

    Args:
        profit_samples:   array de ganancia por escenario
        demand_samples:   array de demanda por escenario
        revenue_samples:  array de ingresos por escenario
        config:           configuración Monte Carlo
        force_recompute:  si True, ignora el cache y recomputa siempre

    Returns:
        AggregatedResult (desde cache o recomputado).
    """
    try:
        from django.core.cache import cache as django_cache
    except ImportError:
        django_cache = None

    cacheable = (
        django_cache is not None
        and config.random_seed is not None
        and not force_recompute
    )

    if cacheable:
        key = _make_aggregate_cache_key(config)
        cached = django_cache.get(key)
        if cached is not None:
            logger.debug('[MC cache] hit key=%s', key)
            return cached

    result = aggregate_results(profit_samples, demand_samples, revenue_samples, config)

    if cacheable:
        django_cache.set(key, result, timeout=_CACHE_TTL)
        logger.debug('[MC cache] set key=%s ttl=%ds', key, _CACHE_TTL)

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Función pública de alto nivel
# ─────────────────────────────────────────────────────────────────────────────

def generate_scenarios(
    config: MonteCarloConfig,
    period_idx: int = 0,
) -> List[OperationScenario]:
    """
    Genera N escenarios probabilísticos para un período dado.

    Punto de entrada principal para integrar Monte Carlo con el motor de eventos.

    Example::

        config = MonteCarloConfig(
            n_scenarios=10000,
            distribution='normal',
            demand_mean=5000,
            demand_std=800,
            seasonality_factors=[1.0, 1.1, 0.9, ...],
        )
        scenarios = generate_scenarios(config, period_idx=0)
        # Luego pasar cada scenario al DiscreteEventEngine.run_period()
    """
    generator = ScenarioGenerator(config)
    scenarios = generator.generate_for_period(period_idx)
    logger.info(
        f"[MC] Generados {len(scenarios)} escenarios "
        f"para período {period_idx} (dist={config.distribution}, "
        f"μ={config.demand_mean:.0f}, σ={config.demand_std:.0f})"
    )
    return scenarios
