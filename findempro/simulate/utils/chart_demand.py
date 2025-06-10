import logging
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from .chart_base import ChartBase

logger = logging.getLogger(__name__)

class ChartDemand(ChartBase):
    def generate_demand_comparison_chart(self, historical_demand, results_simulation):
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

    def generate_statistical_validation_chart(self, demand_data, distribution_type, distribution_params):
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

    def generate_demand_histogram(self, demands):
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