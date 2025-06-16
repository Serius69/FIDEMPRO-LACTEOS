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
from scipy import stats
from scipy.stats import (
    kstest, norm, expon, lognorm, gaussian_kde,
    anderson, shapiro, jarque_bera, gamma, uniform
)
from scipy.optimize import minimize
from django.core.cache import cache
from django.shortcuts import get_object_or_404

from questionary.models import Answer
from ..models import ProbabilisticDensityFunction
from ..validators.simulation_validators import SimulationValidator
from ..utils.data_parsers import DataParser

# Set matplotlib to non-interactive mode
matplotlib.use('Agg')

logger = logging.getLogger(__name__)


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
    
    def analyze_demand_history(self, questionary_result_id: int, user) -> Dict[str, Any]:
        """
        Analyze historical demand data for distribution fitting.
        This analysis is used to parameterize the simulation model.
        """
        try:
            # Check cache first
            cache_key = f"demand_analysis_{questionary_result_id}"
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.info("Returning cached demand analysis")
                return cached_result
            
            # Get demand history from questionnaire
            demand_answer = self._get_demand_history_answer(questionary_result_id)
            if not demand_answer:
                raise ValueError("No se encontró historial de demanda en el cuestionario")
            
            # Parse demand data
            logger.info("Parsing demand data...")
            demand_data = self.parser.parse_demand_history(demand_answer.answer)
            
            if not demand_data:
                raise ValueError("No se pudieron extraer datos válidos del historial")
            
            logger.info(f"Parsed {len(demand_data)} demand values")
            
            # Validate demand data
            validation_result = self.parser.validate_parsed_data(demand_data, 'demand')
            if not validation_result['is_valid']:
                logger.warning(f"Demand data validation warnings: {validation_result['warnings']}")
            
            # Convert to numpy array for analysis
            demand_array = np.array(demand_data)
            
            # Perform comprehensive statistical analysis
            analysis_results = self._perform_demand_analysis(
                demand_array, user, validation_result
            )
            
            # Cache results
            cache.set(cache_key, analysis_results, self.cache_timeout)
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error analyzing demand history: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
    
    def _get_demand_history_answer(self, questionary_result_id: int) -> Optional[Answer]:
        """Get demand history answer from questionnaire"""
        return Answer.objects.filter(
            fk_question__question__icontains='datos históricos de la demanda',
            fk_questionary_result_id=questionary_result_id
        ).select_related('fk_question').first()
    
    def _perform_demand_analysis(self, demand_data: np.ndarray, 
                                user, validation_result: Dict) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of demand data.
        Focus on understanding patterns for simulation.
        """
        # Basic statistics
        basic_stats = self._calculate_basic_statistics(demand_data)
        
        # Time series analysis
        time_series_stats = self._analyze_time_series_properties(demand_data)
        
        # Distribution fitting
        best_distribution = self._find_best_distribution(
            demand_data, user, basic_stats
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
            'best_ks_p_value_floor': math.floor(best_distribution['ks_p_value'] * 100) / 100,
            'best_ks_statistic_floor': math.floor(best_distribution['ks_statistic'] * 100) / 100,
            'selected_fdp': best_distribution['distribution'].id if best_distribution['distribution'] else None,
        }
    
    def _calculate_basic_statistics(self, data: np.ndarray) -> Dict[str, float]:
        """Calculate comprehensive basic statistics"""
        return {
            'mean': float(np.mean(data)),
            'median': float(np.median(data)),
            'std': float(np.std(data, ddof=1)),
            'variance': float(np.var(data, ddof=1)),
            'min': float(np.min(data)),
            'max': float(np.max(data)),
            'range': float(np.max(data) - np.min(data)),
            'cv': float(np.std(data, ddof=1) / np.mean(data)) if np.mean(data) > 0 else 0,
            'count': len(data),
            'q1': float(np.percentile(data, 25)),
            'q3': float(np.percentile(data, 75)),
            'iqr': float(np.percentile(data, 75) - np.percentile(data, 25)),
            'skewness': float(stats.skew(data)),
            'kurtosis': float(stats.kurtosis(data)),
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
    
    def _find_best_distribution(self, data: np.ndarray, 
                               user, basic_stats: Dict) -> Dict[str, Any]:
        """Find best fitting probability distribution"""
        distributions = ProbabilisticDensityFunction.objects.filter(
            is_active=True,
            fk_business__fk_user=user
        ).order_by('-id')
        
        best_result = {
            'distribution': None,
            'ks_statistic': float('inf'),
            'ks_p_value': 0.0,
            'aic': float('inf'),
            'parameters': {}
        }
        
        for dist in distributions:
            fit_result = self._test_distribution_fit(data, dist, basic_stats)
            
            # Select best based on p-value and AIC
            if (fit_result['ks_p_value'] > best_result['ks_p_value'] or
                (fit_result['ks_p_value'] == best_result['ks_p_value'] and
                 fit_result['aic'] < best_result['aic'])):
                best_result = fit_result
                best_result['distribution'] = dist
        
        return best_result
    
    def _test_distribution_fit(self, data: np.ndarray,
                              distribution: ProbabilisticDensityFunction,
                              basic_stats: Dict) -> Dict[str, Any]:
        """Test how well a distribution fits the data"""
        try:
            # Fit parameters based on distribution type
            if distribution.distribution_type == 1:  # Normal
                loc, scale = norm.fit(data)
                fitted_dist = norm(loc=loc, scale=scale)
                params = {'mean': loc, 'std': scale}
                
            elif distribution.distribution_type == 2:  # Exponential
                loc, scale = expon.fit(data)
                fitted_dist = expon(loc=loc, scale=scale)
                params = {'lambda': 1/scale if scale > 0 else 0}
                
            elif distribution.distribution_type == 3:  # Log-Normal
                shape, loc, scale = lognorm.fit(data, floc=0)
                fitted_dist = lognorm(s=shape, loc=loc, scale=scale)
                params = {'shape': shape, 'scale': scale}
                
            elif distribution.distribution_type == 4:  # Gamma
                shape, loc, scale = gamma.fit(data, floc=0)
                fitted_dist = gamma(a=shape, loc=loc, scale=scale)
                params = {'shape': shape, 'scale': scale}
                
            elif distribution.distribution_type == 5:  # Uniform
                loc = data.min()
                scale = data.max() - data.min()
                fitted_dist = uniform(loc=loc, scale=scale)
                params = {'min': loc, 'max': loc + scale}
                
            else:
                return {
                    'ks_statistic': float('inf'),
                    'ks_p_value': 0.0,
                    'aic': float('inf'),
                    'parameters': {}
                }
            
            # Kolmogorov-Smirnov test
            ks_statistic, ks_p_value = kstest(data, fitted_dist.cdf)
            
            # Calculate log-likelihood and AIC
            log_likelihood = np.sum(fitted_dist.logpdf(data))
            n_params = len(params)
            aic = 2 * n_params - 2 * log_likelihood
            
            return {
                'ks_statistic': float(ks_statistic),
                'ks_p_value': float(ks_p_value),
                'aic': float(aic),
                'log_likelihood': float(log_likelihood),
                'parameters': params
            }
            
        except Exception as e:
            logger.error(f"Error testing distribution {distribution.name}: {str(e)}")
            return {
                'ks_statistic': float('inf'),
                'ks_p_value': 0.0,
                'aic': float('inf'),
                'parameters': {}
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
                f'KS Statistic: {best_distribution["ks_statistic"]:.4f}\n'
                f'KS p-value: {best_distribution["ks_p_value"]:.4f}\n'
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
            'distribution_type': best_distribution['distribution'].distribution_type if best_distribution['distribution'] else 1,
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
        
        if distribution_type == 1:  # Normal
            mean, std = norm.fit(data)
            return {'mean': float(mean), 'std': float(std)}
            
        elif distribution_type == 2:  # Exponential
            loc, scale = expon.fit(data)
            return {'lambda': float(1/scale) if scale > 0 else 0}
            
        elif distribution_type == 3:  # Log-Normal
            shape, loc, scale = lognorm.fit(data, floc=0)
            return {'shape': float(shape), 'scale': float(scale)}
            
        elif distribution_type == 4:  # Gamma
            shape, loc, scale = gamma.fit(data, floc=0)
            return {'shape': float(shape), 'scale': float(scale)}
            
        elif distribution_type == 5:  # Uniform
            return {'min': float(data.min()), 'max': float(data.max())}
        
        return {}
    
    def perform_forecast_accuracy_metrics(self, actual: np.ndarray, 
                                        predicted: np.ndarray) -> Dict[str, float]:
        """Calculate various forecast accuracy metrics"""
        if len(actual) != len(predicted):
            raise ValueError("Arrays must have the same length")
        
        errors = actual - predicted
        percentage_errors = np.where(actual != 0, errors / actual * 100, 0)
        
        return {
            'mae': float(np.mean(np.abs(errors))),
            'mse': float(np.mean(errors ** 2)),
            'rmse': float(np.sqrt(np.mean(errors ** 2))),
            'mape': float(np.mean(np.abs(percentage_errors))),
            'bias': float(np.mean(errors)),
            'tracking_signal': float(np.sum(errors) / np.mean(np.abs(errors))) if np.mean(np.abs(errors)) > 0 else 0,
        }