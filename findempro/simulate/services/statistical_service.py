# services/statistical_service.py
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
    anderson, shapiro, jarque_bera
)
from scipy.optimize import minimize
from django.core.cache import cache
from django.shortcuts import get_object_or_404

from questionary.models import Answer
from ..models import ProbabilisticDensityFunction
from ..validators.simulation_validators import SimulationValidator

# Set matplotlib to non-interactive mode
matplotlib.use('Agg')

logger = logging.getLogger(__name__)


class StatisticalService:
    """Enhanced service for statistical analysis with optimizations"""
    
    def __init__(self):
        self.validator = SimulationValidator()
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
        """Analyze demand history with enhanced statistical methods"""
        try:
            # Check cache first
            cache_key = f"demand_analysis_{questionary_result_id}"
            cached_result = cache.get(cache_key)
            if cached_result:
                return cached_result
            
            # Get demand history
            demand_history = self._get_demand_history(questionary_result_id)
            if not demand_history:
                raise ValueError("No se encontró historial de demanda")
            
            # Parse and validate demand data
            numbers = self._parse_demand_data(demand_history.answer)
            validated_numbers = self.validator.validate_demand_data(numbers)
            
            # Perform comprehensive analysis
            analysis_results = self._perform_comprehensive_analysis(
                validated_numbers, user
            )
            
            # Cache results
            cache.set(cache_key, analysis_results, self.cache_timeout)
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error analyzing demand history: {str(e)}")
            raise
    
    def _get_demand_history(self, questionary_result_id: int) -> Optional[Answer]:
        """Get demand history answer with optimization"""
        return Answer.objects.filter(
            fk_question__question__icontains='datos históricos de la demanda',
            fk_questionary_result_id=questionary_result_id
        ).select_related('fk_question').first()
    
    def _parse_demand_data(self, demand_answer: str) -> np.ndarray:
        """Parse demand data with improved error handling"""
        try:
            # Clean the string
            cleaned = demand_answer.strip('[]').replace('<br>', ' ')
            cleaned = re.sub(r'[^\d\s.-]', ' ', cleaned)
            
            # Extract numbers
            numbers = []
            for token in cleaned.split():
                try:
                    num = float(token)
                    if num > 0:  # Only positive values for demand
                        numbers.append(num)
                except ValueError:
                    continue
            
            if not numbers:
                raise ValueError("No se pudieron extraer números válidos")
            
            return np.array(numbers)
            
        except Exception as e:
            logger.error(f"Error parsing demand data: {str(e)}")
            raise
    
    def _perform_comprehensive_analysis(self, numbers: np.ndarray, user) -> Dict[str, Any]:
        """Perform comprehensive statistical analysis"""
        # Basic statistics
        basic_stats = self._calculate_basic_statistics(numbers)
        
        # Advanced statistics
        advanced_stats = self._calculate_advanced_statistics(numbers)
        
        # Smooth data with KDE
        kde, smoothed_data = self._apply_kde_smoothing(numbers)
        
        # Optimize distribution parameters
        optimized_params = self._optimize_distribution_parameters(
            numbers, smoothed_data, basic_stats['mean'], basic_stats['std']
        )
        
        # Find best distribution
        best_dist_results = self._find_best_distribution_enhanced(
            numbers, optimized_params['mean'], optimized_params['std'], user
        )
        
        # Generate visualizations
        visualizations = self._generate_enhanced_visualizations(
            numbers, best_dist_results['distribution'], 
            best_dist_results['pdf'], basic_stats, advanced_stats
        )
        
        # Prepare results
        return {
            'scatter_image': visualizations['scatter'],
            'histogram_image': visualizations['histogram'],
            'best_distribution': best_dist_results['distribution'],
            'demand_mean': basic_stats['mean'],
            'data_list': numbers.tolist(),
            'best_ks_p_value_floor': math.floor(best_dist_results['ks_p_value'] * 100) / 100,
            'best_ks_statistic_floor': math.floor(best_dist_results['ks_statistic'] * 100) / 100,
            'basic_stats': basic_stats,
            'advanced_stats': advanced_stats,
            'selected_fdp': best_dist_results['distribution'].id if best_dist_results['distribution'] else None,
        }
    
    def _calculate_basic_statistics(self, data: np.ndarray) -> Dict[str, float]:
        """Calculate basic statistical measures"""
        return {
            'mean': float(np.mean(data)),
            'median': float(np.median(data)),
            'std': float(np.std(data, ddof=1)),
            'variance': float(np.var(data, ddof=1)),
            'min': float(np.min(data)),
            'max': float(np.max(data)),
            'range': float(np.max(data) - np.min(data)),
            'cv': float(np.std(data, ddof=1) / np.mean(data)),  # Coefficient of variation
            'count': len(data),
        }
    
    def _calculate_advanced_statistics(self, data: np.ndarray) -> Dict[str, Any]:
        """Calculate advanced statistical measures"""
        return {
            'skewness': float(stats.skew(data)),
            'kurtosis': float(stats.kurtosis(data)),
            'q1': float(np.percentile(data, 25)),
            'q3': float(np.percentile(data, 75)),
            'iqr': float(np.percentile(data, 75) - np.percentile(data, 25)),
            'outliers': self._detect_outliers(data),
            'normality_tests': self._perform_normality_tests(data),
            'trend': self._detect_trend(data),
        }
    
    def _detect_outliers(self, data: np.ndarray) -> Dict[str, Any]:
        """Detect outliers using multiple methods"""
        # IQR method
        q1, q3 = np.percentile(data, [25, 75])
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        iqr_outliers = data[(data < lower_bound) | (data > upper_bound)]
        
        # Z-score method
        z_scores = np.abs(stats.zscore(data))
        z_outliers = data[z_scores > 3]
        
        return {
            'iqr_method': {
                'count': len(iqr_outliers),
                'values': iqr_outliers.tolist(),
                'bounds': (lower_bound, upper_bound)
            },
            'zscore_method': {
                'count': len(z_outliers),
                'values': z_outliers.tolist(),
                'threshold': 3
            }
        }
    
    def _perform_normality_tests(self, data: np.ndarray) -> Dict[str, Tuple[float, float]]:
        """Perform multiple normality tests"""
        tests = {}
        
        # Shapiro-Wilk test
        if len(data) <= 5000:
            stat, p_value = shapiro(data)
            tests['shapiro_wilk'] = (float(stat), float(p_value))
        
        # Jarque-Bera test
        stat, p_value = jarque_bera(data)
        tests['jarque_bera'] = (float(stat), float(p_value))
        
        # Anderson-Darling test
        result = anderson(data, dist='norm')
        tests['anderson_darling'] = {
            'statistic': float(result.statistic),
            'critical_values': result.critical_values.tolist(),
            'significance_levels': result.significance_level.tolist()
        }
        
        return tests
    
    def _detect_trend(self, data: np.ndarray) -> Dict[str, Any]:
        """Detect trend in time series data"""
        x = np.arange(len(data))
        
        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, data)
        
        # Mann-Kendall test (simplified version)
        from itertools import combinations
        s = 0
        for (i, xi), (j, xj) in combinations(enumerate(data), 2):
            s += np.sign(xj - xi) if j > i else 0
        
        n = len(data)
        var_s = n * (n - 1) * (2 * n + 5) / 18
        
        if s > 0:
            z = (s - 1) / np.sqrt(var_s)
        elif s < 0:
            z = (s + 1) / np.sqrt(var_s)
        else:
            z = 0
        
        mk_p_value = 2 * (1 - stats.norm.cdf(abs(z)))
        
        return {
            'linear_regression': {
                'slope': float(slope),
                'intercept': float(intercept),
                'r_squared': float(r_value ** 2),
                'p_value': float(p_value),
                'trend_direction': 'increasing' if slope > 0 else 'decreasing',
            },
            'mann_kendall': {
                's_statistic': float(s),
                'z_statistic': float(z),
                'p_value': float(mk_p_value),
                'trend_exists': mk_p_value < 0.05,
            }
        }
    
    def _apply_kde_smoothing(self, data: np.ndarray) -> Tuple[gaussian_kde, np.ndarray]:
        """Apply Kernel Density Estimation for smoothing"""
        # Use Scott's rule for bandwidth selection
        kde = gaussian_kde(data, bw_method='scott')
        
        # Generate smooth data points
        x_range = np.linspace(data.min(), data.max(), 1000)
        smoothed_data = kde(x_range)
        
        return kde, smoothed_data
    
    def _optimize_distribution_parameters(self, data: np.ndarray, smoothed_data: np.ndarray,
                                        initial_mean: float, initial_std: float) -> Dict[str, float]:
        """Optimize distribution parameters using multiple methods"""
        # Method 1: Maximum Likelihood Estimation (MLE)
        mle_mean, mle_std = norm.fit(data)
        
        # Method 2: Method of Moments
        mom_mean = np.mean(data)
        mom_std = np.std(data, ddof=1)
        
        # Method 3: Optimization with smoothed data
        def loss_function(params):
            theoretical_pdf = norm.pdf(smoothed_data, loc=params[0], scale=params[1])
            return np.sum((smoothed_data - theoretical_pdf) ** 2)
        
        initial_params = [initial_mean, initial_std]
        bounds = [(data.min(), data.max()), (0.01, data.std() * 3)]
        
        result = minimize(loss_function, initial_params, method='L-BFGS-B', bounds=bounds)
        opt_mean, opt_std = result.x
        
        # Choose best parameters based on AIC
        params_options = [
            (mle_mean, mle_std, 'MLE'),
            (mom_mean, mom_std, 'MoM'),
            (opt_mean, opt_std, 'Optimized')
        ]
        
        best_params = self._select_best_parameters(data, params_options)
        
        return {
            'mean': best_params[0],
            'std': best_params[1],
            'method': best_params[2]
        }
    
    def _select_best_parameters(self, data: np.ndarray, 
                               params_options: List[Tuple[float, float, str]]) -> Tuple[float, float, str]:
        """Select best parameters using AIC criterion"""
        best_aic = float('inf')
        best_params = params_options[0]
        
        for mean, std, method in params_options:
            # Calculate log-likelihood
            log_likelihood = np.sum(norm.logpdf(data, loc=mean, scale=std))
            
            # Calculate AIC (Akaike Information Criterion)
            aic = 2 * 2 - 2 * log_likelihood  # 2 parameters for normal distribution
            
            if aic < best_aic:
                best_aic = aic
                best_params = (mean, std, method)
        
        return best_params
    
    def _find_best_distribution_enhanced(self, data: np.ndarray, optimized_mean: float,
                                       optimized_std: float, user) -> Dict[str, Any]:
        """Find best fitting distribution with enhanced methods"""
        # Get available distributions
        distributions = ProbabilisticDensityFunction.objects.filter(
            is_active=True,
            fk_business__fk_user=user
        ).order_by('-id')
        
        best_results = {
            'distribution': None,
            'ks_statistic': float('inf'),
            'ks_p_value': 0.0,
            'pdf': None,
            'aic': float('inf'),
            'bic': float('inf'),
        }
        
        # Test each distribution
        for distribution in distributions:
            results = self._test_distribution_fit(
                data, distribution, optimized_mean, optimized_std
            )
            
            # Update best if this is better (prioritize p-value, then AIC)
            if (results['ks_p_value'] > best_results['ks_p_value'] or 
                (results['ks_p_value'] == best_results['ks_p_value'] and 
                 results['aic'] < best_results['aic'])):
                best_results.update(results)
                best_results['distribution'] = distribution
        
        # Generate PDF for best distribution
        if best_results['distribution']:
            best_results['pdf'] = self._generate_pdf(
                data, best_results['distribution'], optimized_mean, optimized_std
            )
        
        return best_results
    
    def _test_distribution_fit(self, data: np.ndarray, distribution: ProbabilisticDensityFunction,
                              optimized_mean: float, optimized_std: float) -> Dict[str, Any]:
        """Test how well a distribution fits the data"""
        try:
            # Create theoretical distribution
            theoretical_dist = self._create_theoretical_distribution(
                distribution, optimized_mean, optimized_std
            )
            
            if theoretical_dist is None:
                return {
                    'ks_statistic': float('inf'),
                    'ks_p_value': 0.0,
                    'aic': float('inf'),
                    'bic': float('inf'),
                }
            
            # Kolmogorov-Smirnov test
            ks_statistic, ks_p_value = kstest(data, theoretical_dist.cdf)
            
            # Calculate log-likelihood
            log_likelihood = np.sum(theoretical_dist.logpdf(data))
            
            # Calculate information criteria
            n_params = self._get_distribution_params_count(distribution)
            n_data = len(data)
            
            aic = 2 * n_params - 2 * log_likelihood
            bic = n_params * np.log(n_data) - 2 * log_likelihood
            
            return {
                'ks_statistic': float(ks_statistic),
                'ks_p_value': float(ks_p_value),
                'aic': float(aic),
                'bic': float(bic),
                'log_likelihood': float(log_likelihood),
            }
            
        except Exception as e:
            logger.error(f"Error testing distribution {distribution.name}: {str(e)}")
            return {
                'ks_statistic': float('inf'),
                'ks_p_value': 0.0,
                'aic': float('inf'),
                'bic': float('inf'),
            }
    
    def _create_theoretical_distribution(self, distribution: ProbabilisticDensityFunction,
                                       optimized_mean: float, optimized_std: float):
        """Create theoretical distribution object"""
        try:
            if distribution.distribution_type == 1:  # Normal
                return norm(loc=optimized_mean, scale=optimized_std)
            elif distribution.distribution_type == 2:  # Exponential
                if distribution.lambda_param and distribution.lambda_param > 0:
                    return expon(scale=1/distribution.lambda_param)
            elif distribution.distribution_type == 3:  # Log-Normal
                if optimized_std > 0:
                    return lognorm(s=optimized_std, scale=np.exp(optimized_mean))
        except Exception as e:
            logger.error(f"Error creating distribution: {str(e)}")
        
        return None
    
    def _get_distribution_params_count(self, distribution: ProbabilisticDensityFunction) -> int:
        """Get number of parameters for a distribution"""
        if distribution.distribution_type == 1:  # Normal
            return 2  # mean, std
        elif distribution.distribution_type == 2:  # Exponential
            return 1  # lambda
        elif distribution.distribution_type == 3:  # Log-Normal
            return 2  # mean, std
        return 2  # default
    
    def _generate_pdf(self, data: np.ndarray, distribution: ProbabilisticDensityFunction,
                     optimized_mean: float, optimized_std: float) -> Optional[np.ndarray]:
        """Generate PDF values for visualization"""
        try:
            theoretical_dist = self._create_theoretical_distribution(
                distribution, optimized_mean, optimized_std
            )
            
            if theoretical_dist:
                return theoretical_dist.pdf(data)
            
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
        
        return None
    
    def _generate_enhanced_visualizations(self, data: np.ndarray, 
                                        best_distribution: Optional[ProbabilisticDensityFunction],
                                        pdf: Optional[np.ndarray], 
                                        basic_stats: Dict[str, float],
                                        advanced_stats: Dict[str, Any]) -> Dict[str, str]:
        """Generate enhanced visualizations"""
        visualizations = {}
        
        try:
            # Scatter plot with trend
            visualizations['scatter'] = self._plot_enhanced_scatter(
                data, basic_stats, advanced_stats
            )
            
            # Histogram with PDF and statistics
            visualizations['histogram'] = self._plot_enhanced_histogram(
                data, pdf, best_distribution, basic_stats, advanced_stats
            )
            
            # Additional visualizations
            visualizations['boxplot'] = self._plot_boxplot(data, advanced_stats)
            visualizations['qq_plot'] = self._plot_qq_plot(data)
            visualizations['acf_plot'] = self._plot_autocorrelation(data)
            
        except Exception as e:
            logger.error(f"Error generating visualizations: {str(e)}")
        
        return visualizations
    
    def _plot_enhanced_scatter(self, data: np.ndarray, basic_stats: Dict[str, float],
                              advanced_stats: Dict[str, Any]) -> str:
        """Create enhanced scatter plot with trend and statistics"""
        fig, ax = plt.subplots(figsize=(12, 7))
        
        # Create index for x-axis
        x = np.arange(1, len(data) + 1)
        
        # Scatter plot
        ax.scatter(x, data, alpha=0.6, s=50, c='blue', edgecolor='darkblue', 
                  label='Demanda Histórica')
        
        # Add trend line
        trend = advanced_stats['trend']['linear_regression']
        trend_line = trend['slope'] * x + trend['intercept']
        ax.plot(x, trend_line, 'r--', linewidth=2, 
               label=f'Tendencia (R²={trend["r_squared"]:.3f})')
        
        # Add moving average
        window_size = min(7, len(data) // 4)
        if window_size > 1:
            moving_avg = pd.Series(data).rolling(window=window_size, center=True).mean()
            ax.plot(x, moving_avg, 'g-', linewidth=2, alpha=0.7, 
                   label=f'Media Móvil ({window_size} períodos)')
        
        # Add mean line
        ax.axhline(y=basic_stats['mean'], color='orange', linestyle=':', 
                  linewidth=2, label=f'Media: {basic_stats["mean"]:.2f}')
        
        # Add confidence bands
        std = basic_stats['std']
        ax.fill_between(x, basic_stats['mean'] - 2*std, basic_stats['mean'] + 2*std,
                       alpha=0.2, color='orange', label='±2σ')
        
        # Highlight outliers
        outliers = advanced_stats['outliers']['iqr_method']
        if outliers['count'] > 0:
            outlier_indices = [i for i, val in enumerate(data) 
                             if val in outliers['values']]
            if outlier_indices:
                ax.scatter([i+1 for i in outlier_indices], 
                          [data[i] for i in outlier_indices],
                          color='red', s=100, marker='x', linewidth=3,
                          label=f'Outliers ({outliers["count"]})')
        
        # Configure plot
        ax.set_xlabel('Número de Observación', fontsize=12)
        ax.set_ylabel('Demanda (Litros)', fontsize=12)
        ax.set_title('Análisis de Demanda Histórica', fontsize=14, fontweight='bold')
        ax.legend(loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        
        # Add statistics text box
        stats_text = (f'Media: {basic_stats["mean"]:.2f}\n'
                     f'Mediana: {basic_stats["median"]:.2f}\n'
                     f'Desv. Est.: {basic_stats["std"]:.2f}\n'
                     f'CV: {basic_stats["cv"]:.2%}\n'
                     f'Tendencia: {trend["trend_direction"]}')
        
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
               verticalalignment='top', bbox=props)
        
        plt.tight_layout()
        return self._save_plot_as_base64(fig)
    
    def _plot_enhanced_histogram(self, data: np.ndarray, pdf: Optional[np.ndarray],
                                distribution: Optional[ProbabilisticDensityFunction],
                                basic_stats: Dict[str, float],
                                advanced_stats: Dict[str, Any]) -> str:
        """Create enhanced histogram with PDF overlay and statistics"""
        fig, ax = plt.subplots(figsize=(12, 7))
        
        # Calculate optimal number of bins using Sturges' rule
        n_bins = int(np.ceil(np.log2(len(data)) + 1))
        
        # Create histogram
        n, bins, patches = ax.hist(data, bins=n_bins, density=True, alpha=0.7,
                                  color='skyblue', edgecolor='darkblue',
                                  label='Demanda Histórica')
        
        # Color code bars by value
        cm = plt.cm.get_cmap('viridis')
        bin_centers = 0.5 * (bins[:-1] + bins[1:])
        col = bin_centers - min(bin_centers)
        col /= max(col)
        for c, p in zip(col, patches):
            plt.setp(p, 'facecolor', cm(c))
        
        # Plot PDF if available
        if pdf is not None and distribution is not None:
            x_range = np.linspace(data.min(), data.max(), 1000)
            theoretical_dist = self._create_theoretical_distribution(
                distribution, basic_stats['mean'], basic_stats['std']
            )
            if theoretical_dist:
                pdf_values = theoretical_dist.pdf(x_range)
                ax.plot(x_range, pdf_values, 'r-', linewidth=3,
                       label=f'FDP {distribution.get_distribution_type_display()}')
        
        # Add KDE
        from scipy.stats import gaussian_kde
        kde = gaussian_kde(data)
        x_kde = np.linspace(data.min(), data.max(), 1000)
        ax.plot(x_kde, kde(x_kde), 'g--', linewidth=2, label='KDE Empírico')
        
        # Add vertical lines for statistics
        ax.axvline(basic_stats['mean'], color='red', linestyle='--', linewidth=2,
                  label=f'Media: {basic_stats["mean"]:.2f}')
        ax.axvline(basic_stats['median'], color='orange', linestyle=':', linewidth=2,
                  label=f'Mediana: {basic_stats["median"]:.2f}')
        
        # Add percentiles
        for p in [25, 75]:
            percentile_val = np.percentile(data, p)
            ax.axvline(percentile_val, color='gray', linestyle=':', alpha=0.7,
                      label=f'P{p}: {percentile_val:.2f}')
        
        # Configure plot
        ax.set_xlabel('Demanda (Litros)', fontsize=12)
        ax.set_ylabel('Densidad de Probabilidad', fontsize=12)
        ax.set_title('Distribución de Demanda Histórica', fontsize=14, fontweight='bold')
        ax.legend(loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add normality test results
        normality_tests = advanced_stats['normality_tests']
        test_text = 'Pruebas de Normalidad:\n'
        
        if 'shapiro_wilk' in normality_tests:
            sw_stat, sw_p = normality_tests['shapiro_wilk']
            test_text += f'Shapiro-Wilk: p={sw_p:.4f}\n'
        
        if 'jarque_bera' in normality_tests:
            jb_stat, jb_p = normality_tests['jarque_bera']
            test_text += f'Jarque-Bera: p={jb_p:.4f}\n'
        
        test_text += f'\nAsimetría: {advanced_stats["skewness"]:.3f}\n'
        test_text += f'Curtosis: {advanced_stats["kurtosis"]:.3f}'
        
        props = dict(boxstyle='round', facecolor='lightblue', alpha=0.8)
        ax.text(0.98, 0.98, test_text, transform=ax.transAxes, fontsize=9,
               verticalalignment='top', horizontalalignment='right', bbox=props)
        
        plt.tight_layout()
        return self._save_plot_as_base64(fig)
    
    def _plot_boxplot(self, data: np.ndarray, advanced_stats: Dict[str, Any]) -> str:
        """Create enhanced boxplot with outliers"""
        fig, ax = plt.subplots(figsize=(8, 10))
        
        # Create boxplot
        bp = ax.boxplot(data, vert=True, patch_artist=True, showmeans=True,
                       meanprops=dict(marker='D', markerfacecolor='red', markersize=8))
        
        # Customize colors
        bp['boxes'][0].set_facecolor('lightblue')
        bp['boxes'][0].set_alpha(0.7)
        bp['medians'][0].set_color('darkblue')
        bp['medians'][0].set_linewidth(2)
        
        # Add outlier information
        outliers = advanced_stats['outliers']['iqr_method']
        if outliers['count'] > 0:
            ax.text(1.1, np.median(data), f'{outliers["count"]} outliers\ndetectados',
                   ha='center', va='center', fontsize=10,
                   bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
        
        # Add quartile labels
        q1, q3 = advanced_stats['q1'], advanced_stats['q3']
        ax.text(0.7, q1, f'Q1: {q1:.2f}', ha='right', va='center')
        ax.text(0.7, q3, f'Q3: {q3:.2f}', ha='right', va='center')
        ax.text(0.7, np.median(data), f'Mediana: {np.median(data):.2f}', 
               ha='right', va='center')
        
        # Configure plot
        ax.set_ylabel('Demanda (Litros)', fontsize=12)
        ax.set_title('Diagrama de Caja - Demanda Histórica', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        return self._save_plot_as_base64(fig)
    
    def _plot_qq_plot(self, data: np.ndarray) -> str:
        """Create Q-Q plot for normality assessment"""
        fig, ax = plt.subplots(figsize=(8, 8))
        
        # Create Q-Q plot
        stats.probplot(data, dist="norm", plot=ax)
        
        # Customize
        ax.get_lines()[0].set_markerfacecolor('blue')
        ax.get_lines()[0].set_markeredgecolor('darkblue')
        ax.get_lines()[0].set_markersize(8)
        ax.get_lines()[1].set_color('red')
        ax.get_lines()[1].set_linewidth(2)
        
        ax.set_title('Gráfico Q-Q Normal', fontsize=14, fontweight='bold')
        ax.set_xlabel('Cuantiles Teóricos', fontsize=12)
        ax.set_ylabel('Cuantiles Observados', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return self._save_plot_as_base64(fig)
    
    def _plot_autocorrelation(self, data: np.ndarray) -> str:
        """Create autocorrelation plot"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # ACF plot
        from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
        
        plot_acf(data, ax=ax1, lags=min(20, len(data)//4), alpha=0.05)
        ax1.set_title('Función de Autocorrelación (ACF)', fontsize=12)
        ax1.set_xlabel('Lag')
        ax1.set_ylabel('ACF')
        
        # PACF plot
        plot_pacf(data, ax=ax2, lags=min(20, len(data)//4), alpha=0.05)
        ax2.set_title('Función de Autocorrelación Parcial (PACF)', fontsize=12)
        ax2.set_xlabel('Lag')
        ax2.set_ylabel('PACF')
        
        plt.tight_layout()
        return self._save_plot_as_base64(fig)
    
    def _save_plot_as_base64(self, fig) -> str:
        """Save matplotlib figure as base64 encoded string"""
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)
        
        buffer.seek(0)
        image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return image_data
    
    # Additional statistical methods
    
    @lru_cache(maxsize=32)
    def calculate_distribution_parameters(self, distribution_type: int, 
                                        data_tuple: tuple) -> Dict[str, float]:
        """Calculate optimal parameters for a specific distribution type"""
        data = np.array(data_tuple)
        
        if distribution_type == 1:  # Normal
            return {
                'mean': float(np.mean(data)),
                'std': float(np.std(data, ddof=1))
            }
        elif distribution_type == 2:  # Exponential
            return {
                'lambda': float(1 / np.mean(data))
            }
        elif distribution_type == 3:  # Log-Normal
            log_data = np.log(data[data > 0])  # Ensure positive values
            return {
                'log_mean': float(np.mean(log_data)),
                'log_std': float(np.std(log_data, ddof=1))
            }
        
        return {}
    
    def perform_time_series_analysis(self, data: np.ndarray) -> Dict[str, Any]:
        """Perform comprehensive time series analysis"""
        try:
            from statsmodels.tsa.seasonal import seasonal_decompose
            from statsmodels.tsa.stattools import adfuller
            
            # Create time series
            ts = pd.Series(data, index=pd.date_range('2024-01-01', periods=len(data), freq='D'))
            
            # Decomposition
            if len(data) >= 14:  # Need at least 2 weeks for weekly seasonality
                decomposition = seasonal_decompose(ts, model='additive', period=7)
                
                # Stationarity test
                adf_result = adfuller(data)
                
                return {
                    'trend': decomposition.trend.dropna().values.tolist(),
                    'seasonal': decomposition.seasonal.dropna().values.tolist(),
                    'residual': decomposition.resid.dropna().values.tolist(),
                    'adf_statistic': float(adf_result[0]),
                    'adf_p_value': float(adf_result[1]),
                    'is_stationary': adf_result[1] < 0.05,
                }
            
        except Exception as e:
            logger.error(f"Error in time series analysis: {str(e)}")
        
        return {}
    
    def calculate_forecast_accuracy_metrics(self, actual: np.ndarray, 
                                          predicted: np.ndarray) -> Dict[str, float]:
        """Calculate various forecast accuracy metrics"""
        if len(actual) != len(predicted):
            raise ValueError("Arrays must have the same length")
        
        errors = actual - predicted
        percentage_errors = errors / actual * 100
        
        return {
            'mae': float(np.mean(np.abs(errors))),  # Mean Absolute Error
            'mse': float(np.mean(errors ** 2)),     # Mean Squared Error
            'rmse': float(np.sqrt(np.mean(errors ** 2))),  # Root Mean Squared Error
            'mape': float(np.mean(np.abs(percentage_errors))),  # Mean Absolute Percentage Error
            'bias': float(np.mean(errors)),          # Bias
            'tracking_signal': float(np.sum(errors) / np.mean(np.abs(errors))) if np.mean(np.abs(errors)) > 0 else 0,
        }