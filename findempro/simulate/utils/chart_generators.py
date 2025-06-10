# utils/chart_generators.py - ENHANCED VERSION
import base64
from datetime import timedelta
import logging
from io import BytesIO
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.figure import Figure
from django.core.cache import cache
from django.db.models import Avg, Sum, Count

from dashboards.models import Chart
from variable.models import Variable

# Set matplotlib to non-interactive mode
matplotlib.use('Agg')

# Configure matplotlib for better performance
plt.rcParams['figure.max_open_warning'] = 0
plt.rcParams['figure.autolayout'] = True
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10

logger = logging.getLogger(__name__)


class ChartGenerator:
    """Enhanced chart generator with demand comparison capabilities"""
    
    def __init__(self):
        self.iniciales_a_buscar = [
            'CTR', 'CTAI', 'TPV', 'TPPRO', 'DI', 'VPC', 'IT', 'GT', 'TCA', 
            'NR', 'GO', 'GG', 'CTTL', 'CPP', 'CPV', 'CPI', 'CPMO', 
            'CUP', 'TG', 'IB', 'MB', 'RI', 'RTI', 'RTC', 'PE', 
            'HO', 'CHO', 'CA'
        ]
        self.cache_timeout = 3600  # 1 hour
        self._setup_plot_style()
    
    def _setup_plot_style(self):
        """Set up consistent plot styling"""
        sns.set_style("whitegrid")
        sns.set_palette("husl")
    
    def generate_all_charts(self, simulation_id: int, simulation_instance, 
                          results_simulation: List, historical_demand: List = None) -> Dict[str, Any]:
        """Generate all charts including demand comparison"""
        cache_key = f"charts_{simulation_id}_v2"
        cached_data = cache.get(cache_key)
        
        if cached_data and not historical_demand:
            return cached_data
        
        # Extract variables and calculate totals
        all_variables_extracted = self._extract_variables_from_results(results_simulation)
        totales_acumulativos = self._calculate_cumulative_totals(results_simulation)
        variables_to_graph = self._prepare_variables_for_graphing(results_simulation)
        
        # Create enhanced chart data with historical demand
        chart_data = self._create_demand_chart_data(results_simulation, historical_demand)
        
        # Generate charts in parallel
        chart_images = self._generate_charts_parallel(
            simulation_id, simulation_instance, results_simulation, 
            chart_data, variables_to_graph, historical_demand
        )
        
        result = {
            'all_variables_extracted': all_variables_extracted,
            'totales_acumulativos': totales_acumulativos,
            'chart_images': chart_images
        }
        
        # Cache the result
        cache.set(cache_key, result, self.cache_timeout)
        
        return result
    
    @lru_cache(maxsize=128)
    def _get_variable_mapping(self) -> Dict[str, Dict[str, str]]:
        """Get cached variable mapping"""
        variables_db = Variable.objects.filter(
            initials__in=self.iniciales_a_buscar
        ).values('initials', 'name', 'unit')
        
        return {
            variable['initials']: {
                'name': variable['name'], 
                'unit': variable['unit']
            } 
            for variable in variables_db
        }
    
    def _extract_variables_from_results(self, results_simulation: List) -> List[Dict]:
        """Extract and process variables from simulation results"""
        all_variables_extracted = []
        name_variables = self._get_variable_mapping()
        
        iniciales_a_nombres = {
            initial: info['name'] 
            for initial, info in name_variables.items()
        }
        
        for result_simulation in results_simulation:
            variables_extracted = result_simulation.get_variables()
            date_simulation = result_simulation.date
            
            totales_por_variable = {}
            for inicial, value in variables_extracted.items():
                if inicial in iniciales_a_nombres:
                    name_variable = iniciales_a_nombres[inicial]
                    totales_por_variable[name_variable] = {
                        'total': value,
                        'unit': name_variables.get(inicial, {}).get('unit', '')
                    }
            
            all_variables_extracted.append({
                'result_simulation': result_simulation,
                'totales_por_variable': totales_por_variable,
                'date_simulation': date_simulation
            })
        
        return all_variables_extracted
    
    def _calculate_cumulative_totals(self, results_simulation: List) -> Dict[str, Dict]:
        """Calculate cumulative totals with optimization"""
        name_variables = self._get_variable_mapping()
        totales_acumulativos = {}
        
        for result_simulation in results_simulation:
            variables_extracted = result_simulation.get_variables()
            
            for inicial, value in variables_extracted.items():
                if inicial in self.iniciales_a_buscar and inicial in name_variables:
                    name_variable = name_variables[inicial]['name']
                    
                    if name_variable not in totales_acumulativos:
                        totales_acumulativos[name_variable] = {
                            'total': 0, 
                            'unit': name_variables[inicial]['unit']
                        }
                    
                    totales_acumulativos[name_variable]['total'] += value
        
        return totales_acumulativos
    
    def _prepare_variables_for_graphing(self, results_simulation: List) -> List[Dict]:
        """Prepare variables data for chart generation"""
        name_variables = self._get_variable_mapping()
        variables_to_graph = []
        
        for result_simulation in results_simulation:
            variables_extracted = result_simulation.get_variables()
            filtered_variables = {}
            
            for inicial, value in variables_extracted.items():
                if inicial in self.iniciales_a_buscar and inicial in name_variables:
                    filtered_variables[name_variables[inicial]['name']] = {
                        'value': value, 
                        'unit': name_variables[inicial]['unit']
                    }
            
            variables_to_graph.append(filtered_variables)
        
        return variables_to_graph
    
    def _create_demand_chart_data(self, result_simulations: List, 
                                historical_demand: List = None) -> Dict:
        """Create enhanced chart data with historical demand"""
        labels = []
        values = []
        
        for i, result_simulation in enumerate(result_simulations):
            labels.append(i + 1)
            values.append(float(result_simulation.demand_mean))
        
        chart_data = {
            'labels': labels,
            'datasets': [
                {'label': 'Demanda Simulada', 'values': values},
            ],
            'x_label': 'Días',
            'y_label': 'Demanda (Litros)',
        }
        
        # Add historical demand if available
        if historical_demand:
            chart_data['historical_demand'] = historical_demand
        
        return chart_data
    
    def _generate_charts_parallel(self, simulation_id: int, simulation_instance, 
                                results_simulation: List, chart_data: Dict, 
                                variables_to_graph: List, 
                                historical_demand: List = None) -> Dict[str, str]:
        """Generate charts in parallel including demand comparison"""
        chart_images = {}
        
        # Define chart configurations
        chart_configs = self._get_chart_configurations(variables_to_graph)
        
        # Generate main charts with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            
            # Main demand comparison chart (PRIORITY)
            if historical_demand:
                futures['demand_comparison'] = executor.submit(
                    self.generate_demand_comparison_chart,
                    historical_demand, results_simulation
                )
            
            # Standard demand charts
            if self._validate_chart_data(chart_data):
                futures['image_data_line'] = executor.submit(
                    self._generate_single_chart,
                    chart_data, 'linedemand', simulation_id, simulation_instance,
                    results_simulation, 'Análisis de Demanda',
                    'Comportamiento de la demanda simulada con tendencias'
                )
                
                futures['image_data_bar'] = executor.submit(
                    self._generate_single_chart,
                    chart_data, 'bar', simulation_id, simulation_instance,
                    results_simulation, 'Distribución de Demanda',
                    'Análisis por período de la demanda simulada'
                )
            
            # Variable-specific charts
            for config in chart_configs:
                chart_data_vars = self._create_variable_chart_data(
                    chart_data['labels'], variables_to_graph, config['variables']
                )
                
                if self._validate_chart_data(chart_data_vars):
                    futures[config['key']] = executor.submit(
                        self._generate_single_chart,
                        chart_data_vars, config['type'], simulation_id, 
                        simulation_instance, results_simulation,
                        config['title'], config['description']
                    )
            
            # Collect results
            for key, future in futures.items():
                try:
                    chart_images[key] = future.result()
                except Exception as e:
                    logger.error(f"Error generating chart {key}: {str(e)}")
                    chart_images[key] = None
        
        return chart_images
    
    def generate_demand_comparison_chart(self, historical_demand: List[float], 
                                       results_simulation: List) -> str:
        """Generate comprehensive demand comparison chart"""
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), 
                                          gridspec_kw={'height_ratios': [3, 1]})
            
            # Main comparison plot
            if historical_demand:
                # Historical demand
                hist_periods = list(range(1, len(historical_demand) + 1))
                ax1.plot(hist_periods, historical_demand, 'b-', marker='s', 
                        markersize=5, linewidth=2, label='Demanda Histórica', 
                        alpha=0.8)
                
                # Historical statistics
                hist_mean = np.mean(historical_demand)
                hist_std = np.std(historical_demand)
                ax1.axhline(y=hist_mean, color='blue', linestyle=':', alpha=0.5,
                          label=f'Media Histórica: {hist_mean:.2f}')
                
                # Historical confidence interval
                ax1.fill_between(hist_periods, 
                               hist_mean - hist_std, 
                               hist_mean + hist_std,
                               alpha=0.1, color='blue')
            
            # Simulated demand
            simulated_values = [float(r.demand_mean) for r in results_simulation]
            sim_start = len(historical_demand) + 1 if historical_demand else 1
            sim_periods = list(range(sim_start, sim_start + len(simulated_values)))
            
            ax1.plot(sim_periods, simulated_values, 'r-', marker='o',
                    markersize=5, linewidth=2, label='Demanda Simulada',
                    alpha=0.8)
            
            # Simulated statistics
            sim_mean = np.mean(simulated_values)
            sim_std = np.std(simulated_values)
            ax1.axhline(y=sim_mean, color='red', linestyle=':', alpha=0.5,
                      label=f'Media Simulada: {sim_mean:.2f}')
            
            # Simulated confidence interval
            ax1.fill_between(sim_periods,
                           sim_mean - sim_std,
                           sim_mean + sim_std,
                           alpha=0.1, color='red')
            
            # Add transition line
            if historical_demand:
                ax1.axvline(x=len(historical_demand), color='gray', 
                          linestyle='--', alpha=0.5, label='Inicio Simulación')
            
            # Trend lines
            if historical_demand and len(historical_demand) > 1:
                z = np.polyfit(hist_periods, historical_demand, 1)
                p = np.poly1d(z)
                ax1.plot(hist_periods, p(hist_periods), 'b--', alpha=0.5,
                       label=f'Tendencia Histórica: {z[0]:.2f}')
            
            if len(simulated_values) > 1:
                z = np.polyfit(range(len(simulated_values)), simulated_values, 1)
                p = np.poly1d(z)
                ax1.plot(sim_periods, p(range(len(simulated_values))), 'r--', 
                       alpha=0.5, label=f'Tendencia Simulada: {z[0]:.2f}')
            
            # Configure main plot
            ax1.set_xlabel('Período de Tiempo', fontsize=12)
            ax1.set_ylabel('Demanda (Litros)', fontsize=12)
            ax1.set_title('Comparación Completa: Demanda Histórica vs Simulada', 
                         fontsize=16, fontweight='bold', pad=20)
            ax1.legend(loc='upper left', bbox_to_anchor=(1, 1))
            ax1.grid(True, alpha=0.3)
            ax1.set_xlim(0, max(len(historical_demand) + len(simulated_values) + 1, 10))
            
            # Difference plot (bottom subplot)
            if historical_demand:
                # Calculate percentage differences
                hist_last_values = historical_demand[-min(len(simulated_values), len(historical_demand)):]
                sim_first_values = simulated_values[:len(hist_last_values)]
                
                if hist_last_values and sim_first_values:
                    periods_diff = list(range(1, len(hist_last_values) + 1))
                    differences = [(s - h) / h * 100 if h != 0 else 0 
                                 for h, s in zip(hist_last_values, sim_first_values)]
                    
                    bars = ax2.bar(periods_diff, differences, alpha=0.7,
                                  color=['green' if d >= 0 else 'red' for d in differences])
                    
                    # Add value labels on bars
                    for bar, diff in zip(bars, differences):
                        height = bar.get_height()
                        ax2.text(bar.get_x() + bar.get_width()/2., height,
                               f'{diff:.1f}%', ha='center', 
                               va='bottom' if height >= 0 else 'top',
                               fontsize=8)
                    
                    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
                    ax2.set_xlabel('Período de Comparación')
                    ax2.set_ylabel('Diferencia (%)')
                    ax2.set_title('Diferencia Porcentual entre Demanda Histórica y Simulada')
                    ax2.grid(True, alpha=0.3, axis='y')
            
            plt.tight_layout()
            
            # Convert to base64
            image_data = self._save_plot_as_base64(fig)
            plt.close(fig)
            
            return image_data
            
        except Exception as e:
            logger.error(f"Error generating demand comparison chart: {str(e)}")
            if 'fig' in locals():
                plt.close(fig)
            return None
    
    def generate_statistical_validation_chart(self, demand_data: List[float], 
                                           distribution_type: str,
                                           distribution_params: Dict) -> str:
        """Generate Q-Q plot and distribution validation charts"""
        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
            
            # Q-Q Plot
            from scipy import stats
            
            if distribution_type == 'normal':
                stats.probplot(demand_data, dist="norm", plot=ax1)
            elif distribution_type == 'exponential':
                stats.probplot(demand_data, dist="expon", plot=ax1)
            elif distribution_type == 'lognorm':
                stats.probplot(demand_data, dist="lognorm", plot=ax1)
            else:
                stats.probplot(demand_data, dist="norm", plot=ax1)
            
            ax1.set_title('Q-Q Plot')
            ax1.grid(True, alpha=0.3)
            
            # Histogram with fitted distribution
            ax2.hist(demand_data, bins=20, density=True, alpha=0.7, 
                    color='skyblue', edgecolor='black')
            
            x_range = np.linspace(min(demand_data), max(demand_data), 100)
            
            if distribution_type == 'normal':
                mean = distribution_params.get('mean', np.mean(demand_data))
                std = distribution_params.get('std', np.std(demand_data))
                y_fit = stats.norm.pdf(x_range, mean, std)
                ax2.plot(x_range, y_fit, 'r-', linewidth=2, 
                        label=f'Normal(μ={mean:.2f}, σ={std:.2f})')
            elif distribution_type == 'exponential':
                lambda_param = distribution_params.get('lambda', 1/np.mean(demand_data))
                y_fit = stats.expon.pdf(x_range, scale=1/lambda_param)
                ax2.plot(x_range, y_fit, 'r-', linewidth=2,
                        label=f'Exponencial(λ={lambda_param:.4f})')
            
            ax2.set_xlabel('Demanda')
            ax2.set_ylabel('Densidad')
            ax2.set_title('Ajuste de Distribución')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # Box plot for outliers
            box_plot = ax3.boxplot(demand_data, patch_artist=True)
            box_plot['boxes'][0].set_facecolor('lightblue')
            ax3.set_ylabel('Demanda')
            ax3.set_title('Análisis de Outliers')
            ax3.grid(True, alpha=0.3, axis='y')
            
            # Statistical tests results
            # Shapiro-Wilk test for normality
            if len(demand_data) < 5000:
                statistic, p_value = stats.shapiro(demand_data)
                test_results = f"Shapiro-Wilk Test:\nEstadístico: {statistic:.4f}\np-valor: {p_value:.4f}\n"
                test_results += "Normalidad: " + ("Sí" if p_value > 0.05 else "No")
            else:
                # Kolmogorov-Smirnov test for large samples
                statistic, p_value = stats.kstest(demand_data, 'norm', 
                                                args=(np.mean(demand_data), np.std(demand_data)))
                test_results = f"Kolmogorov-Smirnov Test:\nEstadístico: {statistic:.4f}\np-valor: {p_value:.4f}\n"
                test_results += "Normalidad: " + ("Sí" if p_value > 0.05 else "No")
            
            # Add statistics summary
            stats_summary = f"\nEstadísticas:\n"
            stats_summary += f"Media: {np.mean(demand_data):.2f}\n"
            stats_summary += f"Mediana: {np.median(demand_data):.2f}\n"
            stats_summary += f"Desv. Est.: {np.std(demand_data):.2f}\n"
            stats_summary += f"Asimetría: {stats.skew(demand_data):.2f}\n"
            stats_summary += f"Curtosis: {stats.kurtosis(demand_data):.2f}"
            
            ax4.text(0.1, 0.5, test_results + stats_summary, 
                    transform=ax4.transAxes, fontsize=10,
                    verticalalignment='center',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            ax4.axis('off')
            ax4.set_title('Pruebas Estadísticas')
            
            fig.suptitle('Validación Estadística de la Demanda', fontsize=16, fontweight='bold')
            plt.tight_layout()
            
            # Convert to base64
            image_data = self._save_plot_as_base64(fig)
            plt.close(fig)
            
            return image_data
            
        except Exception as e:
            logger.error(f"Error generating statistical validation chart: {str(e)}")
            if 'fig' in locals():
                plt.close(fig)
            return None
    
    def generate_demand_analysis_charts(self, historical_demand: List[float], 
                                      simulated_demand: List[float]) -> Dict[str, str]:
        """Generate comprehensive demand analysis charts"""
        charts = {}
        
        try:
            # 1. Comparative Statistics Chart
            stats_chart = self._generate_comparative_stats_chart(
                historical_demand, simulated_demand
            )
            if stats_chart:
                charts['stats_comparison'] = stats_chart
            
            # 2. Distribution Comparison
            dist_chart = self._generate_distribution_comparison(
                historical_demand, simulated_demand
            )
            if dist_chart:
                charts['distribution_comparison'] = dist_chart
            
            # 3. Trend Analysis
            trend_chart = self._generate_trend_analysis_chart(
                historical_demand, simulated_demand
            )
            if trend_chart:
                charts['trend_analysis'] = trend_chart
            
            # 4. Forecast Accuracy Metrics
            accuracy_chart = self._generate_accuracy_metrics_chart(
                historical_demand, simulated_demand
            )
            if accuracy_chart:
                charts['accuracy_metrics'] = accuracy_chart
                
        except Exception as e:
            logger.error(f"Error generating demand analysis charts: {str(e)}")
        
        return charts
    
    def _generate_comparative_stats_chart(self, historical: List[float], 
                                        simulated: List[float]) -> str:
        """Generate comparative statistics visualization"""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Calculate statistics
            stats_names = ['Media', 'Mediana', 'Desv. Est.', 'Mínimo', 'Máximo', 'CV%']
            
            hist_stats = [
                np.mean(historical),
                np.median(historical),
                np.std(historical),
                np.min(historical),
                np.max(historical),
                (np.std(historical) / np.mean(historical) * 100) if np.mean(historical) > 0 else 0
            ]
            
            sim_stats = [
                np.mean(simulated),
                np.median(simulated),
                np.std(simulated),
                np.min(simulated),
                np.max(simulated),
                (np.std(simulated) / np.mean(simulated) * 100) if np.mean(simulated) > 0 else 0
            ]
            
            # Create grouped bar chart
            x = np.arange(len(stats_names))
            width = 0.35
            
            bars1 = ax.bar(x - width/2, hist_stats, width, label='Histórico', 
                          alpha=0.8, color='skyblue')
            bars2 = ax.bar(x + width/2, sim_stats, width, label='Simulado', 
                          alpha=0.8, color='lightcoral')
            
            # Add value labels
            for bars in [bars1, bars2]:
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.1f}', ha='center', va='bottom', fontsize=9)
            
            ax.set_xlabel('Estadística')
            ax.set_ylabel('Valor')
            ax.set_title('Comparación de Estadísticas: Histórico vs Simulado')
            ax.set_xticks(x)
            ax.set_xticklabels(stats_names)
            ax.legend()
            ax.grid(True, alpha=0.3, axis='y')
            
            plt.tight_layout()
            
            image_data = self._save_plot_as_base64(fig)
            plt.close(fig)
            
            return image_data
            
        except Exception as e:
            logger.error(f"Error generating stats comparison chart: {str(e)}")
            return None
    
    def _generate_distribution_comparison(self, historical: List[float],
                                        simulated: List[float]) -> str:
        """Generate distribution comparison visualization"""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            
            # Histogram comparison
            bins = np.linspace(
                min(min(historical), min(simulated)),
                max(max(historical), max(simulated)),
                20
            )
            
            ax1.hist(historical, bins=bins, alpha=0.5, label='Histórico', 
                    color='blue', density=True)
            ax1.hist(simulated, bins=bins, alpha=0.5, label='Simulado', 
                    color='red', density=True)
            
            # Add KDE curves
            from scipy.stats import gaussian_kde
            
            kde_hist = gaussian_kde(historical)
            kde_sim = gaussian_kde(simulated)
            x_range = np.linspace(bins[0], bins[-1], 100)
            
            ax1.plot(x_range, kde_hist(x_range), 'b-', linewidth=2, label='KDE Histórico')
            ax1.plot(x_range, kde_sim(x_range), 'r-', linewidth=2, label='KDE Simulado')
            
            ax1.set_xlabel('Demanda')
            ax1.set_ylabel('Densidad')
            ax1.set_title('Comparación de Distribuciones')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # CDF comparison
            hist_sorted = np.sort(historical)
            sim_sorted = np.sort(simulated)
            
            hist_cdf = np.arange(1, len(hist_sorted) + 1) / len(hist_sorted)
            sim_cdf = np.arange(1, len(sim_sorted) + 1) / len(sim_sorted)
            
            ax2.plot(hist_sorted, hist_cdf, 'b-', linewidth=2, label='CDF Histórico')
            ax2.plot(sim_sorted, sim_cdf, 'r-', linewidth=2, label='CDF Simulado')
            
            ax2.set_xlabel('Demanda')
            ax2.set_ylabel('Probabilidad Acumulada')
            ax2.set_title('Funciones de Distribución Acumulada')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            image_data = self._save_plot_as_base64(fig)
            plt.close(fig)
            
            return image_data
            
        except Exception as e:
            logger.error(f"Error generating distribution comparison: {str(e)}")
            return None
    
    def _generate_trend_analysis_chart(self, historical: List[float],
                                     simulated: List[float]) -> str:
        """Generate trend analysis visualization"""
        try:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Create time series
            hist_time = np.arange(len(historical))
            sim_time = np.arange(len(historical), len(historical) + len(simulated))
            
            # Plot data
            ax.plot(hist_time, historical, 'bo-', markersize=4, alpha=0.5, label='Histórico')
            ax.plot(sim_time, simulated, 'ro-', markersize=4, alpha=0.5, label='Simulado')
            
            # Add trend lines
            if len(historical) > 1:
                z_hist = np.polyfit(hist_time, historical, 1)
                p_hist = np.poly1d(z_hist)
                ax.plot(hist_time, p_hist(hist_time), 'b--', linewidth=2,
                       label=f'Tendencia Hist.: {z_hist[0]:.2f}x + {z_hist[1]:.2f}')
            
            if len(simulated) > 1:
                z_sim = np.polyfit(range(len(simulated)), simulated, 1)
                p_sim = np.poly1d(z_sim)
                ax.plot(sim_time, p_sim(range(len(simulated))), 'r--', linewidth=2,
                       label=f'Tendencia Sim.: {z_sim[0]:.2f}x + {z_sim[1]:.2f}')
            
            # Add moving averages
            window = min(7, len(historical) // 4)
            if window > 1:
                hist_ma = np.convolve(historical, np.ones(window)/window, mode='valid')
                ax.plot(hist_time[window-1:], hist_ma, 'b-', linewidth=3, alpha=0.7,
                       label=f'MA{window} Histórico')
            
            if len(simulated) >= window:
                sim_ma = np.convolve(simulated, np.ones(window)/window, mode='valid')
                ax.plot(sim_time[:len(sim_ma)], sim_ma, 'r-', linewidth=3, alpha=0.7,
                       label=f'MA{window} Simulado')
            
            # Separator line
            ax.axvline(x=len(historical)-0.5, color='gray', linestyle='--', 
                      alpha=0.5, label='Transición')
            
            ax.set_xlabel('Período')
            ax.set_ylabel('Demanda')
            ax.set_title('Análisis de Tendencias y Patrones')
            ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            image_data = self._save_plot_as_base64(fig)
            plt.close(fig)
            
            return image_data
            
        except Exception as e:
            logger.error(f"Error generating trend analysis chart: {str(e)}")
            return None
    
    def _generate_accuracy_metrics_chart(self, historical: List[float],
                                       simulated: List[float]) -> str:
        """Generate forecast accuracy metrics visualization"""
        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
            
            # Use last part of historical for comparison
            n_compare = min(len(historical), len(simulated), 30)
            hist_compare = historical[-n_compare:]
            sim_compare = simulated[:n_compare]
            
            # 1. Actual vs Predicted scatter
            ax1.scatter(hist_compare, sim_compare, alpha=0.6)
            
            # Add perfect prediction line
            min_val = min(min(hist_compare), min(sim_compare))
            max_val = max(max(hist_compare), max(sim_compare))
            ax1.plot([min_val, max_val], [min_val, max_val], 'r--', label='Predicción Perfecta')
            
            # Add regression line
            z = np.polyfit(hist_compare, sim_compare, 1)
            p = np.poly1d(z)
            ax1.plot(hist_compare, p(hist_compare), 'g-', 
                    label=f'Regresión: {z[0]:.2f}x + {z[1]:.2f}')
            
            ax1.set_xlabel('Demanda Histórica')
            ax1.set_ylabel('Demanda Simulada')
            ax1.set_title('Histórico vs Simulado')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 2. Residual plot
            residuals = np.array(sim_compare) - np.array(hist_compare)
            periods = range(1, len(residuals) + 1)
            
            ax2.bar(periods, residuals, alpha=0.7,
                   color=['green' if r >= 0 else 'red' for r in residuals])
            ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
            ax2.set_xlabel('Período')
            ax2.set_ylabel('Residual (Sim - Hist)')
            ax2.set_title('Gráfico de Residuales')
            ax2.grid(True, alpha=0.3, axis='y')
            
            # 3. Error metrics
            mape = np.mean(np.abs((hist_compare - sim_compare) / hist_compare)) * 100
            rmse = np.sqrt(np.mean((hist_compare - sim_compare) ** 2))
            mae = np.mean(np.abs(hist_compare - sim_compare))
            mse = np.mean((hist_compare - sim_compare) ** 2)
            
            metrics = ['MAPE (%)', 'RMSE', 'MAE', 'MSE']
            values = [mape, rmse, mae, mse]
            
            bars = ax3.bar(metrics, values, alpha=0.7, color=['blue', 'green', 'orange', 'red'])
            
            # Add value labels
            for bar, val in zip(bars, values):
                ax3.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                        f'{val:.2f}', ha='center', va='bottom')
            
            ax3.set_ylabel('Valor')
            ax3.set_title('Métricas de Error')
            ax3.grid(True, alpha=0.3, axis='y')
            
            # 4. Performance summary
            r_squared = np.corrcoef(hist_compare, sim_compare)[0, 1] ** 2
            
            summary_text = f"Resumen de Desempeño:\n\n"
            summary_text += f"R² = {r_squared:.4f}\n"
            summary_text += f"MAPE = {mape:.2f}%\n"
            summary_text += f"RMSE = {rmse:.2f}\n"
            summary_text += f"MAE = {mae:.2f}\n\n"
            
            if mape < 10:
                summary_text += "Precisión: Excelente"
            elif mape < 20:
                summary_text += "Precisión: Buena"
            elif mape < 30:
                summary_text += "Precisión: Aceptable"
            else:
                summary_text += "Precisión: Mejorable"
            
            ax4.text(0.1, 0.5, summary_text, transform=ax4.transAxes,
                    fontsize=12, verticalalignment='center',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            ax4.axis('off')
            
            fig.suptitle('Métricas de Precisión del Pronóstico', fontsize=16, fontweight='bold')
            plt.tight_layout()
            
            image_data = self._save_plot_as_base64(fig)
            plt.close(fig)
            
            return image_data
            
        except Exception as e:
            logger.error(f"Error generating accuracy metrics chart: {str(e)}")
            return None
        
        
    def _save_plot_as_base64(self, fig: Figure) -> str:
        """Convert matplotlib figure to base64 string"""
        try:
            buf = BytesIO()
            fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            buf.close()
            return image_base64
        except Exception as e:
            logger.error(f"Error saving plot as base64: {str(e)}")
            return None
    
    def _generate_single_chart(self, chart_data: Dict, chart_type: str, 
                              simulation_id: int, simulation_instance,
                              results_simulation: List, title: str,
                              description: str) -> str:
        """Generate a single chart based on type and data"""
        try:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            labels = chart_data.get('labels', [])
            datasets = chart_data.get('datasets', [])
            
            if chart_type == 'linedemand':
                # Enhanced line chart for demand
                for dataset in datasets:
                    ax.plot(labels, dataset['values'], marker='o', markersize=4, 
                           label=dataset.get('label', ''), alpha=0.8)
                    
                # Add trend line
                for dataset in datasets:
                    z = np.polyfit(labels, dataset['values'], 1)
                    p = np.poly1d(z)
                    ax.plot(labels, p(labels), '--', alpha=0.5,
                           label=f'Tendencia ({z[0]:.2f}x + {z[1]:.2f})')
                    
                # Add confidence interval
                for dataset in datasets:
                    mean = np.mean(dataset['values'])
                    std = np.std(dataset['values'])
                    ax.fill_between(labels,
                                  [mean - std] * len(labels),
                                  [mean + std] * len(labels),
                                  alpha=0.1)
                    
            elif chart_type == 'bar':
                # Enhanced bar chart
                width = 0.8 / len(datasets)
                for i, dataset in enumerate(datasets):
                    x = np.array(labels) + i * width - (len(datasets) - 1) * width / 2
                    bars = ax.bar(x, dataset['values'], width, 
                                label=dataset.get('label', ''), alpha=0.8)
                    
                    # Add value labels
                    for bar in bars:
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., height,
                               f'{height:.1f}', ha='center', va='bottom')
                        
            else:
                # Default line chart
                for dataset in datasets:
                    ax.plot(labels, dataset['values'], label=dataset.get('label', ''))
            
            # Configure axes and labels
            ax.set_xlabel(chart_data.get('x_label', ''), fontsize=12)
            ax.set_ylabel(chart_data.get('y_label', ''), fontsize=12)
            ax.set_title(f"{title}\n{description}", fontsize=14, pad=20)
            
            # Enhance grid
            ax.grid(True, alpha=0.3)
            
            # Optimize legend
            if datasets:
                ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
            
            # Rotate x-labels if many periods
            if len(labels) > 10:
                plt.xticks(rotation=45)
            
            plt.tight_layout()
            
            # Convert to base64
            image_data = self._save_plot_as_base64(fig)
            plt.close(fig)
            
            return image_data
            
        except Exception as e:
            logger.error(f"Error generating chart {chart_type}: {str(e)}")
            if 'fig' in locals():
                plt.close(fig)
            return None
    
    def _get_chart_configurations(self, variables_to_graph: List) -> List[Dict]:
        """Define chart configurations for different variable groups"""
        return [
            {
                'key': 'costs_chart',
                'variables': ['Costo Total Real', 'Costo Total Acumulado Inicial', 
                             'Costo Total de Logística'],
                'type': 'line',
                'title': 'Análisis de Costos',
                'description': 'Comparación de diferentes tipos de costos'
            },
            {
                'key': 'production_chart',
                'variables': ['Total Producción Vendida', 'Total Producción Programada',
                             'Total Producción Real'],
                'type': 'line',
                'title': 'Análisis de Producción',
                'description': 'Comparación de niveles de producción'
            },
            {
                'key': 'income_chart',
                'variables': ['Ingresos Totales', 'Ingresos Brutos', 'Margen Bruto'],
                'type': 'bar',
                'title': 'Análisis de Ingresos',
                'description': 'Comportamiento de ingresos y márgenes'
            },
            {
                'key': 'efficiency_chart',
                'variables': ['Nivel de Rendimiento', 'Rentabilidad Total',
                             'Rentabilidad Total Interna'],
                'type': 'line',
                'title': 'Métricas de Eficiencia',
                'description': 'Indicadores de rendimiento y rentabilidad'
            }
        ]
    
    def _validate_chart_data(self, chart_data: Dict) -> bool:
        """
        Validate chart data structure and content

        Args:
            chart_data: Dictionary containing chart data

        Returns:
            bool: True if data is valid, False otherwise
        """
        try:
            # Check if required keys exist
            if not all(key in chart_data for key in ['labels', 'datasets']):
                logger.warning("Missing required keys in chart data")
                return False

            # Check if labels exist and are not empty
            if not chart_data['labels']:
                logger.warning("Empty labels in chart data")
                return False

            # Check if datasets exist and are properly formatted
            if not chart_data['datasets']:
                logger.warning("No datasets found in chart data")
                return False

            for dataset in chart_data['datasets']:
                # Check if dataset has required keys
                if not all(key in dataset for key in ['label', 'values']):
                    logger.warning("Missing required keys in dataset")
                    return False

                # Check if values match labels length
                if len(dataset['values']) != len(chart_data['labels']):
                    logger.warning("Mismatch between values and labels length")
                    return False

                # Check if values are numeric
                if not all(isinstance(v, (int, float)) for v in dataset['values']):
                    logger.warning("Non-numeric values found in dataset")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating chart data: {str(e)}")
            return False
        
    def _create_variable_chart_data(self, labels: List[int], variables_to_graph: List[Dict], 
                                  variables_to_include: List[str]) -> Dict:
        """
        Create chart data for specific variables

        Args:
            labels: List of period labels
            variables_to_graph: List of dictionaries containing variable data
            variables_to_include: List of variable names to include in chart

        Returns:
            Dict: Formatted chart data structure
        """
        try:
            datasets = []
            
            for variable_name in variables_to_include:
                values = []
                
                for period_data in variables_to_graph:
                    if variable_name in period_data:
                        value = period_data[variable_name]['value']
                        # Convert to float and handle special cases
                        try:
                            values.append(float(value))
                        except (ValueError, TypeError):
                            values.append(0.0)
                    else:
                        values.append(0.0)
                
                if any(values):  # Only include if there are non-zero values
                    datasets.append({
                        'label': variable_name,
                        'values': values
                    })
            
            return {
                'labels': labels,
                'datasets': datasets,
                'x_label': 'Período',
                'y_label': 'Valor'
            }
            
        except Exception as e:
            logger.error(f"Error creating variable chart data: {str(e)}")
            return {'labels': [], 'datasets': [], 'x_label': '', 'y_label': ''}
        
    def generate_demand_scatter_plot(self, demands: List[float]) -> str:
        """
        Generate a detailed scatter plot analysis of demand values.
        
        Args:
            simulation_id: ID of the simulation
            demands: List of demand values to analyze
            
        Returns:
            str: Base64 encoded image of the scatter plot
        """
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Calculate statistics
            mean_demand = np.mean(demands)
            std_demand = np.std(demands)
            median_demand = np.median(demands)
            
            # Create scatter plot
            periods = range(1, len(demands) + 1)
            scatter = ax.scatter(periods, demands, alpha=0.6, c=demands, 
                               cmap='viridis', s=50)
            
            # Add trend line
            z = np.polyfit(periods, demands, 1)
            p = np.poly1d(z)
            ax.plot(periods, p(periods), 'r--', alpha=0.8, 
                    label=f'Tendencia: {z[0]:.2f}x + {z[1]:.2f}')
            
            # Add mean and confidence intervals
            ax.axhline(y=mean_demand, color='g', linestyle='-', alpha=0.5,
                       label=f'Media: {mean_demand:.2f}')
            ax.axhline(y=median_demand, color='b', linestyle=':', alpha=0.5,
                       label=f'Mediana: {median_demand:.2f}')
            ax.fill_between(periods, mean_demand - std_demand, mean_demand + std_demand,
                           alpha=0.2, color='gray', label=f'±1 Desv. Est.: {std_demand:.2f}')
            
            # Add colorbar
            plt.colorbar(scatter, label='Demanda')
            
            # Configure plot
            ax.set_xlabel('Período')
            ax.set_ylabel('Demanda')
            ax.set_title('Análisis de Dispersión de la Demanda')
            ax.grid(True, alpha=0.3)
            ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
            
            plt.tight_layout()
            
            # Convert to base64
            image_data = self._save_plot_as_base64(fig)
            plt.close(fig)
            
            return image_data
            
        except Exception as e:
            logger.error(f"Error generating demand scatter plot: {str(e)}")
            if 'fig' in locals():
                plt.close(fig)
            return None
        
    def generate_demand_histogram(self, demands: List[float]) -> str:
        """
        Generate a detailed histogram analysis of demand distribution.
        
        Args:
            simulation_id: ID of the simulation
            demands: List of demand values to analyze
            
        Returns:
            str: Base64 encoded image of the histogram
        """
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))
            
            # Calculate statistics
            mean_demand = np.mean(demands)
            std_demand = np.std(demands)
            median_demand = np.median(demands)
            skew = stats.skew(demands)
            kurtosis = stats.kurtosis(demands)
            
            # Create main histogram
            counts, bins, patches = ax1.hist(demands, bins='auto', density=True, 
                                           alpha=0.7, color='skyblue', 
                                           edgecolor='black')
            
            # Add KDE curve
            kde = stats.gaussian_kde(demands)
            x_range = np.linspace(min(demands), max(demands), 100)
            ax1.plot(x_range, kde(x_range), 'r-', linewidth=2, 
                     label='Densidad Estimada')
            
            # Add normal distribution curve for comparison
            norm_curve = stats.norm.pdf(x_range, mean_demand, std_demand)
            ax1.plot(x_range, norm_curve, 'g--', linewidth=2, 
                     label='Distribución Normal')
            
            # Add vertical lines for key statistics
            ax1.axvline(mean_demand, color='red', linestyle='-', alpha=0.5,
                        label=f'Media: {mean_demand:.2f}')
            ax1.axvline(median_demand, color='green', linestyle=':', alpha=0.5,
                        label=f'Mediana: {median_demand:.2f}')
            
            ax1.set_xlabel('Demanda')
            ax1.set_ylabel('Densidad')
            ax1.set_title('Distribución de la Demanda')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Create box plot in second subplot
            ax2.boxplot(demands, vert=False, widths=0.7, 
                       patch_artist=True, 
                       boxprops=dict(facecolor='lightblue', color='black'),
                       medianprops=dict(color='red'))
            
            # Add statistics text
            stats_text = (
                f'Estadísticas Descriptivas:\n'
                f'Media: {mean_demand:.2f}\n'
                f'Mediana: {median_demand:.2f}\n'
                f'Desv. Est.: {std_demand:.2f}\n'
                f'CV: {(std_demand/mean_demand*100):.2f}%\n'
                f'Asimetría: {skew:.2f}\n'
                f'Curtosis: {kurtosis:.2f}\n'
                f'Mín: {min(demands):.2f}\n'
                f'Máx: {max(demands):.2f}'
            )
            
            ax2.text(1.2, 0.5, stats_text, transform=ax2.transAxes,
                    bbox=dict(facecolor='white', alpha=0.8),
                    verticalalignment='center')
            
            ax2.set_xlabel('Demanda')
            ax2.set_title('Diagrama de Caja y Estadísticas')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Convert to base64
            image_data = self._save_plot_as_base64(fig)
            plt.close(fig)
            
            return image_data
            
        except Exception as e:
            logger.error(f"Error generating demand histogram: {str(e)}")
            if 'fig' in locals():
                plt.close(fig)
            return None