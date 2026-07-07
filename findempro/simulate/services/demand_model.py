"""
demand_model.py
===============
Modelo de demanda genérico para PyMEs multi-industria.

Funcionalidades:
- Análisis de datos históricos de demanda
- Ajuste de distribuciones estadísticas
- Detección de tendencias y estacionalidad
- Proyección de demanda futura
- Validación matemática de los datos
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import norm, lognorm, gamma, expon, uniform

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────

@dataclass
class DemandAnalysis:
    """Resultado completo del análisis de demanda histórica."""
    # Estadísticas descriptivas
    mean: float
    std: float
    median: float
    min: float
    max: float
    cv: float                    # Coeficiente de variación (std/mean)
    skewness: float
    kurtosis: float

    # Distribución ajustada
    best_distribution: str
    distribution_params: Dict
    goodness_of_fit_ks: float    # KS statistic (menor = mejor ajuste)
    goodness_of_fit_pvalue: float

    # Tendencia
    trend_slope: float           # Pendiente de la tendencia lineal
    trend_intercept: float
    trend_r2: float              # R² de la tendencia
    trend_direction: str         # 'increasing' | 'decreasing' | 'stable'

    # Estacionalidad
    has_seasonality: bool
    seasonality_period: Optional[int]
    seasonality_strength: float

    # Proyección
    forecast_next: List[float] = field(default_factory=list)  # próximos N períodos
    forecast_ci_lower: List[float] = field(default_factory=list)
    forecast_ci_upper: List[float] = field(default_factory=list)

    # Alertas
    volatility_alert: bool = False
    outliers_count: int = 0


@dataclass
class DemandForecast:
    """Proyección de demanda para períodos futuros."""
    periods: int
    forecasted_values: List[float]
    ci_lower: List[float]
    ci_upper: List[float]
    method_used: str
    confidence_level: float
    mape: Optional[float] = None      # Mean Absolute Percentage Error
    rmse: Optional[float] = None


# ─────────────────────────────────────────────
# Servicio de demanda
# ─────────────────────────────────────────────

class DemandModelService:
    """
    Servicio de modelado de demanda genérico para cualquier tipo de PyME.

    Analiza datos históricos, ajusta distribuciones, detecta patrones
    y genera proyecciones con intervalos de confianza.

    Uso:
        service = DemandModelService(historical_data=[1200, 1350, 980, ...])
        analysis = service.analyze()
        forecast = service.forecast(periods=30)
    """

    # Distribuciones candidatas para el ajuste
    DISTRIBUTIONS = {
        'normal': norm,
        'lognormal': lognorm,
        'gamma': gamma,
        'exponential': expon,
        'uniform': uniform,
    }

    def __init__(
        self,
        historical_data: List[float],
        confidence_level: float = 0.95,
        seasonality_period: Optional[int] = None,  # None = auto-detectar
    ):
        data = np.array(historical_data, dtype=float)
        if len(data) < 5:
            raise ValueError("Se requieren al menos 5 puntos de datos históricos.")

        self.data = data
        self.confidence_level = confidence_level
        self._seasonality_period = seasonality_period
        self._n = len(data)

    # ── Estadísticas descriptivas ──────────────────────────────────────────────

    def descriptive_stats(self) -> Dict:
        """Calcula estadísticas descriptivas completas."""
        d = self.data
        mean = float(np.mean(d))
        std = float(np.std(d, ddof=1)) if self._n > 1 else 0.0
        cv = (std / mean) if mean != 0 else 0.0

        return {
            'mean': mean,
            'std': std,
            'median': float(np.median(d)),
            'min': float(np.min(d)),
            'max': float(np.max(d)),
            'cv': cv,
            'skewness': float(stats.skew(d)),
            'kurtosis': float(stats.kurtosis(d)),
            'q1': float(np.percentile(d, 25)),
            'q3': float(np.percentile(d, 75)),
            'iqr': float(np.percentile(d, 75) - np.percentile(d, 25)),
            'count': self._n,
        }

    # ── Detección de outliers (IQR) ────────────────────────────────────────────

    def detect_outliers(self) -> Tuple[np.ndarray, int]:
        """Detecta outliers usando el método IQR."""
        q1 = np.percentile(self.data, 25)
        q3 = np.percentile(self.data, 75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        mask = (self.data < lower) | (self.data > upper)
        return self.data[mask], int(np.sum(mask))

    # ── Ajuste de distribución ─────────────────────────────────────────────────

    def fit_distribution(self) -> Tuple[str, Dict, float, float]:
        """
        Ajusta las distribuciones candidatas y retorna la mejor.

        Returns:
            (nombre, parámetros, ks_statistic, p_value)
        """
        # Usar solo datos positivos para distribuciones con soporte (0, ∞)
        data_pos = self.data[self.data > 0]
        if len(data_pos) < 5:
            data_pos = self.data

        best_name = 'normal'
        best_ks = float('inf')
        best_pval = 0.0
        best_params = {}

        for name, dist in self.DISTRIBUTIONS.items():
            try:
                params = dist.fit(data_pos)
                ks_stat, p_val = stats.kstest(data_pos, dist.cdf, args=params)
                if ks_stat < best_ks:
                    best_ks = ks_stat
                    best_pval = p_val
                    best_name = name
                    # Guardar params como dict legible
                    if name == 'normal':
                        best_params = {'loc': params[0], 'scale': params[1]}
                    elif name == 'lognormal':
                        best_params = {'s': params[0], 'loc': params[1], 'scale': params[2]}
                    elif name == 'gamma':
                        best_params = {'a': params[0], 'loc': params[1], 'scale': params[2]}
                    elif name == 'exponential':
                        best_params = {'loc': params[0], 'scale': params[1]}
                    elif name == 'uniform':
                        best_params = {'loc': params[0], 'scale': params[1]}
            except Exception:
                continue

        return best_name, best_params, best_ks, best_pval

    # ── Análisis de tendencia ──────────────────────────────────────────────────

    def analyze_trend(self) -> Dict:
        """Regresión lineal sobre los datos históricos para detectar tendencia."""
        x = np.arange(self._n, dtype=float)
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, self.data)

        if r_value ** 2 < 0.1 or p_value > 0.05:
            direction = 'stable'
        elif slope > 0:
            direction = 'increasing'
        else:
            direction = 'decreasing'

        return {
            'slope': float(slope),
            'intercept': float(intercept),
            'r2': float(r_value ** 2),
            'p_value': float(p_value),
            'direction': direction,
            'growth_rate_pct': float((slope / np.mean(self.data)) * 100) if np.mean(self.data) != 0 else 0.0,
        }

    # ── Análisis de estacionalidad ─────────────────────────────────────────────

    def analyze_seasonality(self) -> Dict:
        """
        Detecta estacionalidad usando autocorrelación.
        Retorna si hay estacionalidad, el período y la fuerza.
        """
        if self._n < 10:
            return {'has_seasonality': False, 'period': None, 'strength': 0.0}

        try:
            # Autocorrelación manual para períodos de 2..n//2
            max_lag = min(self._n // 2, 52)  # máximo un año de semanas
            acf_values = []
            mean = np.mean(self.data)
            var = np.var(self.data)

            if var == 0:
                return {'has_seasonality': False, 'period': None, 'strength': 0.0}

            for lag in range(1, max_lag + 1):
                cov = np.mean((self.data[:-lag] - mean) * (self.data[lag:] - mean))
                acf_values.append(cov / var)

            acf_array = np.array(acf_values)
            # Umbral estadístico: 2/sqrt(n)
            threshold = 2.0 / np.sqrt(self._n)

            # Buscar picos significativos de autocorrelación (excluyendo lag=1)
            significant = np.where(np.abs(acf_array[1:]) > threshold)[0] + 2  # +2 por el offset
            if len(significant) > 0:
                period = int(significant[0])
                strength = float(np.abs(acf_array[period - 1]))
                has_seasonality = strength > threshold * 1.5
            else:
                period = None
                strength = 0.0
                has_seasonality = False

            # Si el usuario especificó período, priorizar
            if self._seasonality_period is not None:
                period = self._seasonality_period
                has_seasonality = True
                if period - 1 < len(acf_array):
                    strength = float(np.abs(acf_array[period - 1]))

            return {
                'has_seasonality': has_seasonality,
                'period': period,
                'strength': strength,
                'acf_values': acf_array[:12].tolist(),
            }
        except Exception as e:
            logger.warning(f"Error en análisis de estacionalidad: {e}")
            return {'has_seasonality': False, 'period': None, 'strength': 0.0}

    # ── Proyección de demanda ──────────────────────────────────────────────────

    def forecast(
        self,
        periods: int = 30,
        method: str = 'auto',
    ) -> DemandForecast:
        """
        Proyecta la demanda para los próximos N períodos.

        Métodos disponibles:
        - 'linear': regresión lineal + tendencia
        - 'moving_average': media móvil
        - 'exponential_smoothing': suavizamiento exponencial
        - 'auto': selecciona el mejor según R²
        """
        trend = self.analyze_trend()
        alpha = (1 - self.confidence_level) / 2

        if method == 'auto':
            method = 'linear' if trend['r2'] > 0.5 else 'exponential_smoothing'

        forecasted = []
        if method == 'linear':
            last_x = self._n - 1
            for i in range(1, periods + 1):
                forecasted.append(trend['intercept'] + trend['slope'] * (last_x + i))

        elif method == 'moving_average':
            window = min(7, self._n)
            last_ma = float(np.mean(self.data[-window:]))
            forecasted = [last_ma] * periods

        elif method == 'exponential_smoothing':
            alpha_es = 0.3
            s = float(self.data[0])
            for val in self.data[1:]:
                s = alpha_es * val + (1 - alpha_es) * s
            # Proyección: nivel suavizado + tendencia acumulada
            forecasted = [max(0.0, s + trend['slope'] * (i + 1)) for i in range(periods)]

        else:
            raise ValueError(f"Método '{method}' no soportado.")

        # Intervalo de confianza: basado en el error estándar de los datos
        std_err = float(np.std(self.data, ddof=1)) if self._n > 1 else 0.0
        z = stats.norm.ppf(1 - alpha)
        ci_lower = [max(0.0, v - z * std_err) for v in forecasted]
        ci_upper = [v + z * std_err for v in forecasted]

        # MAPE sobre datos históricos (validación interna)
        mape = self._calculate_mape(method, trend)

        return DemandForecast(
            periods=periods,
            forecasted_values=forecasted,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            method_used=method,
            confidence_level=self.confidence_level,
            mape=mape,
        )

    def _calculate_mape(self, method: str, trend: Dict) -> Optional[float]:
        """
        Calcula MAPE (Mean Absolute Percentage Error) por validación cruzada simple.
        Usa el último 20% de los datos como conjunto de test.

        Returns:
            MAPE en porcentaje, o None si no hay suficientes datos.
        """
        n_test = max(1, self._n // 5)
        train  = self.data[:-n_test]
        test   = self.data[-n_test:]

        if len(train) < 3:
            return None

        try:
            if method == 'linear':
                x_train = np.arange(len(train), dtype=float)
                slope, intercept, _, _, _ = stats.linregress(x_train, train)
                preds = intercept + slope * np.arange(len(train), len(train) + n_test, dtype=float)
            else:
                preds = np.full(n_test, float(np.mean(train)))

            mask = test != 0
            if np.any(mask):
                return round(
                    float(np.mean(np.abs((test[mask] - preds[mask]) / test[mask])) * 100),
                    2,
                )
        except Exception:
            pass
        return None

    # ── Análisis completo ──────────────────────────────────────────────────────

    def analyze(self, forecast_periods: int = 30) -> DemandAnalysis:
        """
        Ejecuta el análisis completo de demanda.

        Returns:
            DemandAnalysis con todas las métricas, distribución ajustada,
            tendencia, estacionalidad y proyección.
        """
        desc = self.descriptive_stats()
        best_dist, dist_params, ks_stat, ks_pval = self.fit_distribution()
        trend = self.analyze_trend()
        seasonality = self.analyze_seasonality()
        _, outlier_count = self.detect_outliers()

        # Proyección
        forecast = self.forecast(periods=forecast_periods)

        volatility_alert = desc['cv'] > 0.5  # CV > 50% = alta volatilidad

        return DemandAnalysis(
            mean=desc['mean'],
            std=desc['std'],
            median=desc['median'],
            min=desc['min'],
            max=desc['max'],
            cv=desc['cv'],
            skewness=desc['skewness'],
            kurtosis=desc['kurtosis'],
            best_distribution=best_dist,
            distribution_params=dist_params,
            goodness_of_fit_ks=ks_stat,
            goodness_of_fit_pvalue=ks_pval,
            trend_slope=trend['slope'],
            trend_intercept=trend['intercept'],
            trend_r2=trend['r2'],
            trend_direction=trend['direction'],
            has_seasonality=seasonality['has_seasonality'],
            seasonality_period=seasonality.get('period'),
            seasonality_strength=seasonality.get('strength', 0.0),
            forecast_next=forecast.forecasted_values,
            forecast_ci_lower=forecast.ci_lower,
            forecast_ci_upper=forecast.ci_upper,
            volatility_alert=volatility_alert,
            outliers_count=outlier_count,
        )

    def to_simulation_params(self, analysis: Optional['DemandAnalysis'] = None) -> Dict:
        """
        Convierte el análisis en parámetros listos para MonteCarloConfig.

        Args:
            analysis: resultado de analyze() previamente calculado.
                      Si se omite, se llama analyze() internamente.
                      Pasar el resultado cached evita recalcular todo.

        Returns:
            Dict compatible con MonteCarloConfig(**params).
        """
        if analysis is None:
            analysis = self.analyze()

        return {
            # 'distribution_type' es la clave que consume SimulationConfig; se
            # mantiene 'distribution' como alias por compatibilidad con MonteCarloConfig.
            'distribution_type': analysis.best_distribution,
            'distribution':      analysis.best_distribution,
            'demand_mean':  analysis.mean,
            'demand_std':   analysis.std,
            'demand_min':   analysis.min,
            'demand_max':   analysis.max,
            'trend_slope':  analysis.trend_slope,
            'trend_r2':     analysis.trend_r2,
        }
