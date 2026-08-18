# services/statistical_service.py
"""
Refactored statistical service for demand analysis and distribution fitting.
Focuses on proper historical data analysis for simulation parameters.
"""
import base64
import logging
import math
import re
import statistics
from io import BytesIO
from typing import Dict, List, Tuple, Optional, Any
from functools import lru_cache

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import warnings
from scipy import stats
from scipy.stats import (
    kstest, norm, expon, lognorm, gaussian_kde,
    anderson, shapiro, jarque_bera, gamma, uniform
)
from scipy.optimize import minimize
from django.core.cache import cache
from django.shortcuts import get_object_or_404

from modeling.statistics import DistributionFitError, METHOD_VERSION, fit_distributions

from questionary.models import Answer
from ..models import ProbabilisticDensityFunction
from ..validators.simulation_validators import SimulationValidator
from ..utils.data_parsers_utils import DataParser
from ..utils.statistical_contracts import stable_distribution_shape

# Set matplotlib to non-interactive mode
matplotlib.use('Agg')

logger = logging.getLogger(__name__)


# Configurar matplotlib para evitar errores de fuentes y caracteres
matplotlib.use('Agg')  # Backend sin GUI
matplotlib.rcParams['font.family'] = ['DejaVu Sans', 'Liberation Sans', 'sans-serif']
matplotlib.rcParams['font.size'] = 10
matplotlib.rcParams['axes.unicode_minus'] = False

# Suprimir warnings específicos de matplotlib
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')
warnings.filterwarnings('ignore', message='Glyph.*missing from current font')

def safe_text(text):
    """Convertir caracteres unicode problemáticos a ASCII seguros"""
    replacements = {
        '✓': 'OK',
        '❌': 'ERROR', 
        '⚠️': 'WARNING',
        '📊': 'Chart',
        '📈': 'Trend',
        '📉': 'Down',
        '🔴': 'RED',
        '🟢': 'GREEN',
        '🟡': 'YELLOW'
    }
    
    for unicode_char, ascii_replacement in replacements.items():
        text = text.replace(unicode_char, ascii_replacement)
    
    return text


class StatisticalService:
    """Enhanced service for statistical analysis of demand data"""
    
    def __init__(self):
        self.validator = SimulationValidator()
        self.parser = DataParser()
        self.cache_timeout = 3600  # 1 hour
        self._setup_plot_style()
    
    def _setup_plot_style(self):
        """Setup consistent plotting style"""
        plt.style.use('seaborn-v0_8-darkgrid')
        plt.rcParams['figure.figsize'] = (10, 6)
        plt.rcParams['figure.dpi'] = 100
        plt.rcParams['savefig.dpi'] = 100
        plt.rcParams['font.size'] = 10
    
    
    def _calculate_comprehensive_statistics(self, historical_demand, results_simulation):
        """Calculate comprehensive statistics for analysis"""
        stats = {
            'historical': {},
            'simulated': {},
            'comparison': {},
            'forecast_accuracy': {}
        }
        
        # Historical statistics
        if historical_demand:
            historical_array = np.array(historical_demand)
            stats['historical'] = {
                'mean': np.mean(historical_array),
                'std': np.std(historical_array),
                'min': np.min(historical_array),
                'max': np.max(historical_array),
                'median': np.median(historical_array),
                'cv': np.std(historical_array) / np.mean(historical_array) if np.mean(historical_array) > 0 else 0,
                'trend': self._calculate_trend(historical_array)
            }
        
        # Simulated statistics
        try:
            simulated_values = [float(r.demand_mean) for r in results_simulation]
        except (AttributeError, ValueError, TypeError) as e:
            logger.error(f"Error extracting simulated values: {str(e)}")
            simulated_values = []
        
        if simulated_values:
            simulated_array = np.array(simulated_values)
            stats['simulated'] = {
                'mean': np.mean(simulated_array),
                'std': np.std(simulated_array),
                'min': np.min(simulated_array),
                'max': np.max(simulated_array),
                'median': np.median(simulated_array),
                'cv': np.std(simulated_array) / np.mean(simulated_array) if np.mean(simulated_array) > 0 else 0,
                'trend': self._calculate_trend(simulated_array)
            }
            
            # Comparison metrics
            if historical_demand and stats['historical']:
                stats['comparison'] = {
                    'mean_diff': stats['simulated']['mean'] - stats['historical']['mean'],
                    'mean_diff_pct': ((stats['simulated']['mean'] - stats['historical']['mean']) / 
                                    stats['historical']['mean'] * 100) if stats['historical']['mean'] > 0 else 0,
                    'std_diff': stats['simulated']['std'] - stats['historical']['std'],
                    'cv_diff': stats['simulated']['cv'] - stats['historical']['cv'],
                    'trend_change': stats['simulated']['trend'] - stats['historical']['trend']
                }
                
                # Forecast accuracy metrics
                try:
                    if len(historical_demand) != len(simulated_values):
                        stats['forecast_accuracy'] = {
                            'mape': None, 'rmse': None, 'mae': None,
                            'status': 'unavailable',
                            'reason': 'series_not_comparable',
                        }
                    else:
                        stats['forecast_accuracy'] = {
                            'mape': self._calculate_mape(historical_demand, simulated_values),
                            'rmse': self._calculate_rmse(historical_demand, simulated_values),
                            'mae': self._calculate_mae(historical_demand, simulated_values),
                            'status': 'complete',
                        }
                except Exception as e:
                    logger.error(f"Error calculating forecast accuracy: {str(e)}")
                    stats['forecast_accuracy'] = {
                        'mape': None,
                        'rmse': None,
                        'mae': None,
                        'status': 'unavailable',
                        'reason': 'series_not_comparable',
                    }
        
        return stats
    
    def _calculate_realistic_comparison(self, historical_demand, results_simulation):
        """Calculate realistic comparison metrics"""
        hist_mean = np.mean(historical_demand)
        hist_std = np.std(historical_demand)
        
        sim_demands = [float(r.demand_mean) for r in results_simulation]
        sim_mean = np.mean(sim_demands)
        sim_std = np.std(sim_demands)
        
        # Calculate realistic growth
        growth_rate = ((sim_mean - hist_mean) / hist_mean * 100) if hist_mean > 0 else 0
        
        # Flag if growth seems unrealistic
        is_realistic = abs(growth_rate) < 50  # Less than 50% change
        
        return {
            'historical_mean': hist_mean,
            'simulated_mean': sim_mean,
            'growth_rate': growth_rate,
            'is_realistic': is_realistic,
            'deviation_percentage': abs(growth_rate),
            'recommendation': self._get_growth_recommendation(growth_rate, is_realistic)
        }
    
    def _get_growth_recommendation(self, growth_rate, is_realistic):
        """Get recommendation based on growth rate"""
        if not is_realistic:
            if growth_rate > 50:
                return "La predicción parece sobreestimar la demanda. Revise los parámetros del modelo."
            else:
                return "La predicción muestra una caída drástica. Verifique los datos de entrada."
        else:
            if growth_rate > 20:
                return "Crecimiento optimista pero realista. Prepare capacidad adicional."
            elif growth_rate > 0:
                return "Crecimiento moderado esperado. Mantenga niveles actuales."
            elif growth_rate > -10:
                return "Ligera contracción esperada. Optimice costos operativos."
            else:
                return "Contracción significativa. Implemente estrategias de retención."
    
    def _calculate_mape(self, actual, predicted):
        """Calculate Mean Absolute Percentage Error"""
        if len(actual) == 0 or len(predicted) == 0 or len(actual) != len(predicted):
            return None
        
        # Convert to numpy arrays
        actual = np.array(actual)
        predicted = np.array(predicted)
        
        # Ensure same length
        n = min(len(actual), len(predicted))
        actual = actual[:n]
        predicted = predicted[:n]
        
        # Avoid division by zero
        mask = actual != 0
        if not np.any(mask):
            return None
        
        return np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100
    
    def _calculate_rmse(self, actual, predicted):
        """Calculate Root Mean Square Error"""
        if len(actual) == 0 or len(predicted) == 0 or len(actual) != len(predicted):
            return None
        
        # Convert to numpy arrays
        actual = np.array(actual)
        predicted = np.array(predicted)
        
        return np.sqrt(np.mean((actual - predicted) ** 2))
    
    def _calculate_mae(self, actual, predicted):
        """Calculate Mean Absolute Error"""
        if len(actual) == 0 or len(predicted) == 0 or len(actual) != len(predicted):
            return None
        
        # Convert to numpy arrays
        actual = np.array(actual)
        predicted = np.array(predicted)
        
        return np.mean(np.abs(actual - predicted))
    def _calculate_trend(self, data):
        """Calculate trend slope"""
        try:
            data_array = np.array(data)
            if len(data_array) < 2:
                return 0
            x = np.arange(len(data_array))
            z = np.polyfit(x, data_array, 1)
            return float(z[0])
        except (ValueError, TypeError) as e:
            logger.error(f"Error calculating trend: {str(e)}")
            return 0
        
    def analyze_demand_history(self, questionary_result_id: int, user, 
                         demand_data: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        🔧 MÉTODO CORREGIDO: Ahora acepta demand_data como parámetro opcional
        para evitar doble parsing y asegurar consistencia en demand_std
        """
        try:
            # Check cache first
            cache_key = f"demand_analysis_{questionary_result_id}"
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.info("Returning cached demand analysis")
                return cached_result
            
            # 🔧 NUEVO: Usar demand_data si se proporciona, sino extraer
            if demand_data is not None and len(demand_data) > 0:
                logger.info(f"Using provided demand data: {len(demand_data)} values")
                parsed_demand_data = demand_data
                # Validar datos proporcionados
                validation_result = self._validate_provided_demand_data(parsed_demand_data)
            else:
                # Fallback: extraer como antes
                logger.info("No demand data provided, extracting from questionnaire...")
                demand_answer = self._get_demand_history_answer(questionary_result_id)
                if not demand_answer:
                    raise ValueError("No se encontró historial de demanda en el cuestionario")
                
                # Parse demand data
                parsed_demand_data = self.parser.parse_demand_history(demand_answer.answer)
                if not parsed_demand_data:
                    raise ValueError("No se pudieron extraer datos válidos del historial")
                
                validation_result = self.parser.validate_parsed_data(parsed_demand_data, 'demand')
            
            logger.info(f"Final demand data count: {len(parsed_demand_data)}")
            
            # 🔧 VALIDACIÓN CRÍTICA: Asegurar que tenemos datos numéricos válidos
            if not self._validate_demand_data_for_stats(parsed_demand_data):
                raise ValueError("Los datos de demanda no son válidos para cálculos estadísticos")
            
            # Convert to numpy array for analysis
            demand_array = np.array(parsed_demand_data, dtype=float)
            
            # 🔧 LOG CRÍTICO: Verificar datos antes del análisis
            logger.info(f"Demand array stats - Min: {np.min(demand_array)}, Max: {np.max(demand_array)}, Mean: {np.mean(demand_array)}")
            
            # Perform comprehensive statistical analysis
            analysis_results = self._perform_demand_analysis(
                demand_array, user, validation_result
            )
            
            # 🔧 VERIFICACIÓN FINAL: Asegurar que demand_std está presente
            if 'demand_std' not in analysis_results:
                logger.error("demand_std missing from analysis results!")
                analysis_results['demand_std'] = float(np.std(demand_array, ddof=1))
            
            logger.info(f"Final analysis - demand_mean: {analysis_results.get('demand_mean')}, demand_std: {analysis_results.get('demand_std')}")
            
            # Cache results
            cache.set(cache_key, analysis_results, self.cache_timeout)
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error analyzing demand history: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
    
    def _validate_demand_data_for_stats(self, demand_data: List[float]) -> bool:
        """🔧 NUEVO: Validación crítica para asegurar que los datos son aptos para estadísticas"""
        try:
            if not demand_data or len(demand_data) < 2:
                logger.error("Insufficient data for statistical calculations")
                return False
            
            # Convertir a numpy
            data_array = np.array(demand_data, dtype=float)
            
            # Verificar que no hay NaN o infinitos
            if np.any(np.isnan(data_array)) or np.any(np.isinf(data_array)):
                logger.error("Data contains NaN or infinite values")
                return False
            
            # Verificar que hay variabilidad
            if np.std(data_array) == 0:
                logger.warning("Data has zero variance - all values are identical")
                # Permitir, pero advertir
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating data for statistics: {e}")
            return False
    
    
    def _validate_provided_demand_data(self, demand_data: List[float]) -> Dict[str, Any]:
        """🔧 NUEVO: Validar datos de demanda proporcionados externamente"""
        try:
            # Convertir a numpy para validación
            data_array = np.array(demand_data, dtype=float)
            
            warnings = []
            
            # Validaciones básicas
            if len(data_array) < 10:
                warnings.append(f"Pocos datos: {len(data_array)} (recomendado: ≥30)")
            
            # Verificar valores negativos
            negative_count = np.sum(data_array < 0)
            if negative_count > 0:
                warnings.append(f"Valores negativos encontrados: {negative_count}")
            
            # Verificar outliers extremos
            q75, q25 = np.percentile(data_array, [75, 25])
            iqr = q75 - q25
            outlier_threshold = q75 + 3 * iqr
            extreme_outliers = np.sum(data_array > outlier_threshold)
            if extreme_outliers > 0:
                warnings.append(f"Outliers extremos: {extreme_outliers}")
            
            # Calcular estadísticas básicas
            stats = {
                'count': len(data_array),
                'mean': float(np.mean(data_array)),
                'std': float(np.std(data_array, ddof=1)),
                'cv': float(np.std(data_array, ddof=1) / np.mean(data_array)) if np.mean(data_array) > 0 else 0,
                'min': float(np.min(data_array)),
                'max': float(np.max(data_array))
            }
            
            return {
                'is_valid': len(warnings) == 0,
                'warnings': warnings,
                'stats': stats
            }
            
        except Exception as e:
            logger.error(f"Error validating provided demand data: {e}")
            return {
                'is_valid': False,
                'warnings': [f"Error en validación: {str(e)}"],
                'stats': {}
            }
    
    
    def _get_demand_history_answer(self, questionary_result_id: int) -> Optional[Answer]:
        """Get demand history answer from questionnaire"""
        return Answer.objects.filter(
            fk_question__question__icontains='datos históricos de la demanda',
            fk_questionary_result_id=questionary_result_id
        ).select_related('fk_question').first()
    
    def _perform_demand_analysis(self, demand_data: np.ndarray, 
                            user, validation_result: Dict) -> Dict[str, Any]:
        """Perform comprehensive analysis of demand data - VERSIÓN CORREGIDA"""
        # Basic statistics
        basic_stats = self._calculate_basic_statistics(demand_data)
        
        # Time series analysis
        time_series_stats = self._analyze_time_series_properties(demand_data)
        
        # CORRECCIÓN: Cambiar el orden de parámetros
        best_distribution = self._find_best_distribution(
            user, demand_data, basic_stats  # ✅ CORRECTO: user primero, luego demand_data
        )
        
        # Generate visualizations
        visualizations = self._generate_analysis_visualizations(
            demand_data, basic_stats, time_series_stats, 
            best_distribution, validation_result
        )
        
        # Prepare simulation parameters
        simulation_params = self._prepare_simulation_parameters(
            basic_stats, time_series_stats, best_distribution
        )
        
        return {
            'basic_stats': basic_stats,
            'time_series': time_series_stats,
            'best_distribution': best_distribution['distribution'],
            'distribution_fit': best_distribution,
            'visualizations': visualizations,
            'simulation_params': simulation_params,
            'validation_result': validation_result,
            'demand_data': demand_data.tolist(),
            # Legacy fields for compatibility
            'scatter_image': visualizations.get('time_series_plot'),
            'histogram_image': visualizations.get('distribution_plot'),
            'demand_mean': basic_stats['mean'],
            'data_list': demand_data.tolist(),
            'best_ks_p_value_floor': best_distribution['ks_p_value'],
            'best_ks_statistic_floor': best_distribution['ks_statistic'],
            'distribution_fit_diagnostic': best_distribution.get('diagnostic'),
            'selected_fdp': best_distribution['distribution'].id if best_distribution['distribution'] else None,
        }
    
    def _calculate_basic_statistics(self, data: np.ndarray) -> Dict[str, Any]:
        """🔧 MEJORADO: Calculate comprehensive basic statistics with detailed logging"""
        try:
            logger.debug(f"Calculating basic statistics for {len(data)} data points")
            
            # Cálculos estadísticos con logging
            mean_val = float(np.mean(data))
            std_val = float(np.std(data, ddof=1))  # 🔧 Usar ddof=1 para muestra
            shape = stable_distribution_shape(data)
            
            logger.debug(f"Calculated - Mean: {mean_val}, Std: {std_val}")
            
            stats_result = {
                'mean': mean_val,
                'median': float(np.median(data)),
                'std': std_val,  # 🔧 CRÍTICO: Asegurar que se incluye
                'variance': float(np.var(data, ddof=1)),
                'min': float(np.min(data)),
                'max': float(np.max(data)),
                'range': float(np.max(data) - np.min(data)),
                'cv': float(std_val / mean_val) if mean_val > 0 else 0,
                'count': len(data),
                'q1': float(np.percentile(data, 25)),
                'q3': float(np.percentile(data, 75)),
                'iqr': float(np.percentile(data, 75) - np.percentile(data, 25)),
                'skewness': shape.skewness,
                'kurtosis': shape.kurtosis,
                'shape_statistics_status': shape.status,
            }
            
            # 🔧 VERIFICACIÓN FINAL
            if 'std' not in stats_result or stats_result['std'] is None:
                logger.error("STD calculation failed!")
                stats_result['std'] = std_val
            
            logger.info(f"Basic statistics completed - std: {stats_result['std']}")
            return stats_result
            
        except Exception as e:
            logger.error(f"Error calculating basic statistics: {e}")
            # 🔧 FALLBACK con cálculo mínimo
            return {
                'mean': float(np.mean(data)) if len(data) > 0 else 0,
                'std': float(np.std(data, ddof=1)) if len(data) > 1 else 0,
                'count': len(data),
                'min': float(np.min(data)) if len(data) > 0 else 0,
                'max': float(np.max(data)) if len(data) > 0 else 0,
            }
    
    def _analyze_time_series_properties(self, data: np.ndarray) -> Dict[str, Any]:
        """Analyze time series properties of demand data"""
        results = {
            'has_trend': False,
            'trend_slope': 0.0,
            'is_stationary': False,
            'seasonality_detected': False,
            'autocorrelation': {},
            'volatility': 0.0
        }
        
        try:
            # Trend analysis
            x = np.arange(len(data))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, data)
            
            results['trend_slope'] = float(slope)
            results['trend_intercept'] = float(intercept)
            results['trend_r_squared'] = float(r_value ** 2)
            results['trend_p_value'] = float(p_value)
            results['has_trend'] = p_value < 0.05
            
            # Stationarity test (simplified)
            if len(data) >= 20:
                from statsmodels.tsa.stattools import adfuller
                adf_result = adfuller(data, autolag='AIC')
                results['adf_statistic'] = float(adf_result[0])
                results['adf_p_value'] = float(adf_result[1])
                results['is_stationary'] = adf_result[1] < 0.05
            
            # Volatility (using rolling window)
            if len(data) >= 7:
                rolling_std = pd.Series(data).rolling(window=7).std()
                results['volatility'] = float(rolling_std.mean() / np.mean(data))
            
            # Simple autocorrelation at lag 1
            if len(data) > 1:
                results['autocorrelation']['lag_1'] = float(
                    np.corrcoef(data[:-1], data[1:])[0, 1]
                )
            
        except Exception as e:
            logger.warning(f"Error in time series analysis: {str(e)}")
        
        return results
    
    def _find_best_distribution(self, user, data: np.ndarray, 
                           basic_stats: Dict) -> Dict[str, Any]:
        """Find best fitting probability distribution - VERSIÓN CORREGIDA"""
        # CORRECCIÓN: Usar user para filtrar, no data
        distributions = ProbabilisticDensityFunction.objects.filter(
            is_active=True,
            fk_business__fk_user=user  # ✅ CORRECTO: user en lugar de data
        ).order_by('-id')
        
        best_result: Dict[str, Any] = {
            'distribution': None,
            'ks_statistic': None,
            'ks_p_value': None,
            'aic': None,
            'bic': None,
            'parameters': {},
            'diagnostic': {
                'method_version': METHOD_VERSION,
                'valid': False,
                'statistic': None,
                'p_value': None,
                'unavailable_reason': 'NO_COMPATIBLE_DISTRIBUTION',
            },
        }

        valid_results = []
        for dist in distributions:
            fit_result = self._test_distribution_fit(data, dist, basic_stats)
            if fit_result['valid']:
                fit_result['distribution'] = dist
                valid_results.append(fit_result)

        if valid_results:
            best_result = min(
                valid_results,
                key=lambda item: (item['aic'], item['ks_statistic'], item['distribution'].id),
            )
        return best_result
    
    def _test_distribution_fit(self, data: np.ndarray,
                              distribution: ProbabilisticDensityFunction,
                              basic_stats: Dict) -> Dict[str, Any]:
        """Fit one continuous candidate and expose a truthful v2 diagnostic."""
        names = {
            1: 'normal',
            2: 'exponential',
            3: 'lognormal',
            4: 'gamma',
            5: 'uniform',
        }
        try:
            name = names.get(distribution.distribution_type)
            if name is None:
                raise DistributionFitError("Tipo de distribución no soportado.")
            result = fit_distributions(data.tolist(), candidates=[name])
            diagnostic = result['candidates'][0]
            raw = diagnostic['parameters']
            if name == 'normal':
                params = {'mean': raw['loc'], 'std': raw['scale']}
            elif name == 'exponential':
                params = {'lambda': raw['rate'], 'scale': raw['scale']}
            elif name in {'lognormal', 'gamma'}:
                params = {'shape': raw['shape'], 'scale': raw['scale']}
            else:
                params = {'min': raw['minimum'], 'max': raw['maximum']}
            return {
                'valid': True,
                'ks_statistic': diagnostic['ks_statistic'],
                'ks_p_value': diagnostic['p_value'],
                'aic': diagnostic['aic'],
                'bic': diagnostic['bic'],
                'log_likelihood': diagnostic['log_likelihood'],
                'parameters': params,
                'diagnostic': diagnostic,
            }
        except (DistributionFitError, ValueError, FloatingPointError) as e:
            logger.error(f"Error testing distribution {distribution.name}: {str(e)}")
            return {
                'valid': False,
                'ks_statistic': None,
                'ks_p_value': None,
                'aic': None,
                'bic': None,
                'parameters': {},
                'diagnostic': {
                    'method_version': METHOD_VERSION,
                    'valid': False,
                    'statistic': None,
                    'p_value': None,
                    'unavailable_reason': 'INVALID_FIT',
                    'warnings': [str(e)],
                },
            }
    
    def _generate_analysis_visualizations(self, data: np.ndarray,
                                        basic_stats: Dict,
                                        time_series_stats: Dict,
                                        best_distribution: Dict,
                                        validation_result: Dict) -> Dict[str, str]:
        """Generate comprehensive visualization plots"""
        visualizations = {}
        
        try:
            # 1. Time series plot with analysis
            visualizations['time_series_plot'] = self._plot_time_series_analysis(
                data, basic_stats, time_series_stats
            )
            
            # 2. Distribution plot with fitted curve
            visualizations['distribution_plot'] = self._plot_distribution_analysis(
                data, basic_stats, best_distribution
            )
            
            # 3. Diagnostic plots
            visualizations['diagnostic_plot'] = self._plot_diagnostics(
                data, validation_result
            )
            
            # 4. Autocorrelation plot
            if len(data) >= 20:
                visualizations['acf_plot'] = self._plot_autocorrelation(data)
            
        except Exception as e:
            logger.error(f"Error generating visualizations: {str(e)}")
        
        return visualizations
    
    def _plot_time_series_analysis(self, data: np.ndarray,
                                  basic_stats: Dict,
                                  time_series_stats: Dict) -> str:
        """Create time series analysis plot"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), 
                                       gridspec_kw={'height_ratios': [3, 1]})
        
        x = np.arange(1, len(data) + 1)
        
        # Main time series
        ax1.plot(x, data, 'b-', linewidth=2, alpha=0.8, label='Demanda Histórica')
        ax1.scatter(x, data, alpha=0.6, s=30, c='blue')
        
        # Add mean line
        ax1.axhline(y=basic_stats['mean'], color='green', linestyle='--',
                   linewidth=2, label=f'Media: {basic_stats["mean"]:.2f}')
        
        # Add trend line if significant
        if time_series_stats['has_trend']:
            trend_line = time_series_stats['trend_slope'] * x + time_series_stats['trend_intercept']
            ax1.plot(x, trend_line, 'r--', linewidth=2, 
                    label=f'Tendencia (R²={time_series_stats["trend_r_squared"]:.3f})')
        
        # Add confidence bands
        std = basic_stats['std']
        ax1.fill_between(x, basic_stats['mean'] - 2*std, basic_stats['mean'] + 2*std,
                        alpha=0.2, color='green', label='±2σ')
        
        # Moving average
        if len(data) >= 7:
            ma7 = pd.Series(data).rolling(window=7, center=True).mean()
            ax1.plot(x, ma7, 'orange', linewidth=2, alpha=0.8, label='MA(7)')
        
        ax1.set_xlabel('Período')
        ax1.set_ylabel('Demanda (Litros)')
        ax1.set_title('Análisis de Serie Temporal - Demanda Histórica')
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)
        
        # Residuals or detrended data
        if time_series_stats['has_trend']:
            residuals = data - (time_series_stats['trend_slope'] * x + time_series_stats['trend_intercept'])
            ax2.bar(x, residuals, alpha=0.7, color=['green' if r > 0 else 'red' for r in residuals])
            ax2.set_title('Residuales (Datos sin Tendencia)')
        else:
            deviations = data - basic_stats['mean']
            ax2.bar(x, deviations, alpha=0.7, color=['green' if d > 0 else 'red' for d in deviations])
            ax2.set_title('Desviaciones de la Media')
        
        ax2.axhline(y=0, color='black', linewidth=1)
        ax2.set_xlabel('Período')
        ax2.set_ylabel('Valor')
        ax2.grid(True, alpha=0.3)
        
        # Add statistics text
        stats_text = (
            f'CV: {basic_stats["cv"]:.2%}\n'
            f'Volatilidad: {time_series_stats["volatility"]:.2%}\n'
            f'Estacionaria: {"Sí" if time_series_stats["is_stationary"] else "No"}'
        )
        ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes, 
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        return self._save_plot_as_base64(fig)
    
    def _plot_distribution_analysis(self, data: np.ndarray,
                                  basic_stats: Dict,
                                  best_distribution: Dict) -> str:
        """Create distribution analysis plot"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Histogram with fitted distribution
        n_bins = int(np.ceil(np.log2(len(data)) + 1))  # Sturges' rule
        
        n, bins, _ = ax1.hist(data, bins=n_bins, density=True, alpha=0.7,
                             color='skyblue', edgecolor='darkblue',
                             label='Datos Históricos')
        
        # Plot fitted distribution if available
        if best_distribution['distribution']:
            x_range = np.linspace(data.min(), data.max(), 1000)
            
            dist_type = best_distribution['distribution'].distribution_type
            params = best_distribution['parameters']
            
            if dist_type == 1:  # Normal
                y_fitted = norm.pdf(x_range, loc=params['mean'], scale=params['std'])
                label = f'Normal(μ={params["mean"]:.1f}, σ={params["std"]:.1f})'
            elif dist_type == 2:  # Exponential
                y_fitted = expon.pdf(x_range, scale=1/params.get('lambda', 1))
                label = f'Exponencial(λ={params.get("lambda", 0):.3f})'
            elif dist_type == 3:  # Log-Normal
                y_fitted = lognorm.pdf(x_range, s=params['shape'], scale=params['scale'])
                label = f'Log-Normal'
            elif dist_type == 4:  # Gamma
                y_fitted = gamma.pdf(x_range, a=params['shape'], scale=params['scale'])
                label = f'Gamma(α={params["shape"]:.2f}, β={params["scale"]:.1f})'
            elif dist_type == 5:  # Uniform
                y_fitted = uniform.pdf(x_range, loc=params['min'], 
                                      scale=params['max']-params['min'])
                label = f'Uniforme({params["min"]:.1f}, {params["max"]:.1f})'
            else:
                y_fitted = None
                label = 'Unknown'
            
            if y_fitted is not None:
                ax1.plot(x_range, y_fitted, 'r-', linewidth=3, label=label)
        
        # Add KDE
        kde = gaussian_kde(data)
        x_kde = np.linspace(data.min(), data.max(), 1000)
        ax1.plot(x_kde, kde(x_kde), 'g--', linewidth=2, label='KDE Empírico')
        
        ax1.set_xlabel('Demanda (Litros)')
        ax1.set_ylabel('Densidad de Probabilidad')
        ax1.set_title('Distribución de Demanda Histórica')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Q-Q plot
        stats.probplot(data, dist="norm", plot=ax2)
        ax2.set_title('Gráfico Q-Q Normal')
        ax2.grid(True, alpha=0.3)
        
        # Add fit statistics
        if best_distribution['distribution']:
            fit_text = (
                f'Distribución: {best_distribution["distribution"].get_distribution_type_display()}\n'
                f'Distancia KS: {best_distribution["ks_statistic"]:.4f}\n'
                'p-value: no calculado (parámetros ajustados)\n'
                f'AIC: {best_distribution["aic"]:.1f}'
            )
            ax1.text(0.98, 0.98, fit_text, transform=ax1.transAxes,
                    verticalalignment='top', horizontalalignment='right',
                    bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
        plt.tight_layout()
        return self._save_plot_as_base64(fig)
    
    def _plot_diagnostics(self, data: np.ndarray, 
                         validation_result: Dict) -> str:
        """Create diagnostic plots"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        
        # 1. Boxplot with outliers
        bp = ax1.boxplot(data, vert=True, patch_artist=True)
        bp['boxes'][0].set_facecolor('lightblue')
        bp['boxes'][0].set_alpha(0.7)
        
        # Annotate outliers
        outliers = bp['fliers'][0].get_data()[1]
        if len(outliers) > 0:
            ax1.text(1.1, np.median(outliers), f'{len(outliers)} outliers',
                    ha='left', va='center',
                    bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
        
        ax1.set_ylabel('Demanda (Litros)')
        ax1.set_title('Diagrama de Caja')
        ax1.grid(True, alpha=0.3, axis='y')
        
        # 2. Monthly aggregation (if enough data)
        if len(data) >= 30:
            # Assume daily data, aggregate by 30-day periods
            n_months = len(data) // 30
            monthly_data = [data[i*30:(i+1)*30].mean() for i in range(n_months)]
            months = list(range(1, n_months + 1))
            
            ax2.bar(months, monthly_data, alpha=0.7, color='steelblue')
            ax2.set_xlabel('Mes')
            ax2.set_ylabel('Demanda Promedio')
            ax2.set_title('Demanda Promedio Mensual')
            ax2.grid(True, alpha=0.3, axis='y')
        else:
            ax2.text(0.5, 0.5, 'Datos insuficientes\npara análisis mensual',
                    ha='center', va='center', transform=ax2.transAxes,
                    fontsize=12, color='gray')
            ax2.set_title('Análisis Mensual')
        
        # 3. Cumulative distribution
        sorted_data = np.sort(data)
        cumulative = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
        
        ax3.plot(sorted_data, cumulative, 'b-', linewidth=2)
        ax3.fill_between(sorted_data, 0, cumulative, alpha=0.3)
        ax3.set_xlabel('Demanda (Litros)')
        ax3.set_ylabel('Probabilidad Acumulada')
        ax3.set_title('Función de Distribución Acumulada Empírica')
        ax3.grid(True, alpha=0.3)
        
        # Add percentiles
        for p in [25, 50, 75, 95]:
            val = np.percentile(data, p)
            ax3.axvline(x=val, color='red', linestyle='--', alpha=0.5)
            ax3.text(val, 0.05, f'P{p}', ha='center', fontsize=8)
        
        # 4. Validation warnings
        ax4.axis('off')
        warnings_text = "Validación de Datos:\n\n"
        
        if validation_result['warnings']:
            for i, warning in enumerate(validation_result['warnings'][:5]):
                warnings_text += f"• {warning}\n"
        else:
            warnings_text += "✓ Todos los controles pasaron exitosamente\n"
        
        warnings_text += f"\n📊 Estadísticas:\n"
        warnings_text += f"• Datos: {validation_result['stats']['count']}\n"
        warnings_text += f"• Media: {validation_result['stats']['mean']:.2f}\n"
        warnings_text += f"• CV: {validation_result['stats']['cv']:.2%}"
        
        ax4.text(0.1, 0.9, warnings_text, transform=ax4.transAxes,
                verticalalignment='top', fontsize=11,
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
        
        plt.tight_layout()
        return self._save_plot_as_base64(fig)
    
    def _plot_autocorrelation(self, data: np.ndarray) -> str:
        """Create autocorrelation plot"""
        from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # ACF
        plot_acf(data, ax=ax1, lags=min(20, len(data)//4), alpha=0.05)
        ax1.set_title('Función de Autocorrelación (ACF)')
        ax1.set_xlabel('Lag')
        ax1.set_ylabel('ACF')
        
        # PACF
        plot_pacf(data, ax=ax2, lags=min(20, len(data)//4), alpha=0.05)
        ax2.set_title('Función de Autocorrelación Parcial (PACF)')
        ax2.set_xlabel('Lag')
        ax2.set_ylabel('PACF')
        
        plt.tight_layout()
        return self._save_plot_as_base64(fig)
    
    def _prepare_simulation_parameters(self, basic_stats: Dict,
                                     time_series_stats: Dict,
                                     best_distribution: Dict) -> Dict[str, Any]:
        """Prepare parameters for simulation based on analysis"""
        params = {
            'demand_mean': basic_stats['mean'],
            'demand_std': basic_stats['std'],
            'demand_cv': basic_stats['cv'],
            'has_trend': time_series_stats['has_trend'],
            'trend_slope': time_series_stats['trend_slope'],
            'volatility': time_series_stats['volatility'],
            'distribution_type': best_distribution['distribution'].distribution_type if best_distribution['distribution'] else None,
            'distribution_params': best_distribution['parameters'],
            'seasonality_factor': 1.0  # Default, can be enhanced
        }
        
        # Add safety limits for simulation
        params['min_demand'] = max(0, basic_stats['mean'] - 3 * basic_stats['std'])
        params['max_demand'] = basic_stats['mean'] + 3 * basic_stats['std']
        
        return params
    
    def _save_plot_as_base64(self, fig) -> str:
        """Save matplotlib figure as base64 encoded string"""
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)
        
        buffer.seek(0)
        image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return image_data
    
    def calculate_distribution_parameters(self, distribution_type: int,
                                        data_tuple: tuple) -> Dict[str, float]:
        """Calculate optimal parameters for a specific distribution type"""
        data = np.array(data_tuple)
        if data.size == 0 or not np.all(np.isfinite(data)):
            raise ValueError("Los datos deben ser finitos y no estar vacíos.")
        if distribution_type == 1:  # Normal
            mean, std = norm.fit(data)
            if std <= 0:
                raise ValueError("La distribución normal requiere variación en los datos.")
            return {'mean': float(mean), 'std': float(std)}
        elif distribution_type == 2:  # Exponential
            if np.any(data < 0):
                raise ValueError("La distribución exponencial requiere datos no negativos.")
            loc, scale = expon.fit(data)
            if scale <= 0:
                raise ValueError("La distribución exponencial requiere variación en los datos.")
            return {'lambda': float(1/scale)}
        elif distribution_type == 3:  # Log-Normal
            if np.any(data <= 0):
                raise ValueError("La distribución log-normal requiere datos positivos.")
            shape, loc, scale = lognorm.fit(data, floc=0)
            if shape <= 0 or scale <= 0:
                raise ValueError("Parámetros log-normales inválidos.")
            return {'shape': float(shape), 'scale': float(scale)}
        elif distribution_type == 4:  # Gamma
            if np.any(data <= 0):
                raise ValueError("La distribución gamma requiere datos positivos.")
            shape, loc, scale = gamma.fit(data, floc=0)
            if shape <= 0 or scale <= 0:
                raise ValueError("Parámetros gamma inválidos.")
            return {'shape': float(shape), 'scale': float(scale)}
        elif distribution_type == 5:  # Uniform
            if data.max() <= data.min():
                raise ValueError("La distribución uniforme requiere un rango positivo.")
            return {'min': float(data.min()), 'max': float(data.max())}
        
        return {}
    
    def perform_forecast_accuracy_metrics(self, actual: np.ndarray, 
                                        predicted: np.ndarray) -> Dict[str, float]:
        """Calculate various forecast accuracy metrics"""
        if len(actual) != len(predicted):
            raise ValueError("Arrays must have the same length")
        
        errors = actual - predicted

        # El error porcentual no existe cuando la observación es cero. Antes se
        # sustituía por 0 —un acierto perfecto— y se promediaba junto al resto:
        # el MAPE bajaba justamente en los puntos donde no se podía medir.
        measurable = actual != 0
        if np.any(measurable):
            mape = float(np.mean(np.abs(errors[measurable] / actual[measurable] * 100)))
        else:
            mape = None

        mean_absolute_error = float(np.mean(np.abs(errors)))
        return {
            'mae': mean_absolute_error,
            'mse': float(np.mean(errors ** 2)),
            'rmse': float(np.sqrt(np.mean(errors ** 2))),
            'mape': mape,
            'mape_excluded_observations': int(np.count_nonzero(~measurable)),
            'bias': float(np.mean(errors)),
            'tracking_signal': (
                float(np.sum(errors) / mean_absolute_error) if mean_absolute_error > 0 else None
            ),
        }
