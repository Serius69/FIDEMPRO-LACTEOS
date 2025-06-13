# utils/chart_demand.py
import logging
from typing import Dict, List, Optional
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from scipy import stats

from .chart_base import ChartBase

matplotlib.use('Agg')
logger = logging.getLogger(__name__)

class ChartDemand(ChartBase):
    """Specialized class for demand-related charts"""
    
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
    
    def generate_demand_scatter_plot(self, demand_data: List[float]) -> str:
        """Generate scatter plot for demand data analysis"""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Create x-axis (time periods)
            x_values = list(range(1, len(demand_data) + 1))
            
            # Create scatter plot
            ax.scatter(x_values, demand_data, alpha=0.7, s=50, c='blue', 
                    label='Demanda Observada')
            
            # Add regression line
            if len(demand_data) > 1:
                z = np.polyfit(x_values, demand_data, 1)
                p = np.poly1d(z)
                ax.plot(x_values, p(x_values), "r--", alpha=0.8, 
                    label=f'Tendencia: {z[0]:.2f}x + {z[1]:.2f}')
            
            # Add mean line
            mean_demand = np.mean(demand_data)
            ax.axhline(y=mean_demand, color='green', linestyle=':', 
                    label=f'Media: {mean_demand:.2f}')
            
            # Configure plot
            ax.set_xlabel('Período de Tiempo', fontsize=12)
            ax.set_ylabel('Demanda (Litros)', fontsize=12)
            ax.set_title('Análisis de Dispersión de Demanda', fontsize=14, fontweight='bold')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Convert to base64
            image_data = self._save_plot_as_base64(fig)
            plt.close(fig)
            
            return image_data
            
        except Exception as e:
            logger.error(f"Error generating demand scatter plot: {str(e)}")
            return None
    
    def generate_demand_histogram(self, demand_data: List[float]) -> str:
        """Generate histogram for demand data distribution analysis"""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Create histogram
            n, bins, patches = ax.hist(demand_data, bins=15, alpha=0.7, 
                                    color='skyblue', edgecolor='black', 
                                    density=True, label='Distribución de Demanda')
            
            # Add statistical information
            mean_val = np.mean(demand_data)
            std_val = np.std(demand_data)
            median_val = np.median(demand_data)
            
            # Add vertical lines for statistics
            ax.axvline(mean_val, color='red', linestyle='--', linewidth=2,
                    label=f'Media: {mean_val:.2f}')
            ax.axvline(median_val, color='orange', linestyle='--', linewidth=2,
                    label=f'Mediana: {median_val:.2f}')
            
            # Add normal distribution curve if we have enough data
            if len(demand_data) > 5:
                try:
                    # Fit normal distribution
                    x_range = np.linspace(min(demand_data), max(demand_data), 100)
                    normal_dist = stats.norm.pdf(x_range, mean_val, std_val)
                    ax.plot(x_range, normal_dist, 'g-', linewidth=2, 
                        label='Distribución Normal')
                    
                    # Try to fit other distributions
                    # Lognormal
                    if all(x > 0 for x in demand_data):
                        shape, loc, scale = stats.lognorm.fit(demand_data, floc=0)
                        lognorm_dist = stats.lognorm.pdf(x_range, shape, loc, scale)
                        ax.plot(x_range, lognorm_dist, 'm--', linewidth=2,
                            label='Distribución Log-Normal')
                    
                except Exception as dist_error:
                    logger.warning(f"Could not fit distributions: {str(dist_error)}")
            
            # Add statistics text box
            textstr = f'μ = {mean_val:.2f}\nσ = {std_val:.2f}\nMediana = {median_val:.2f}\nRango = {max(demand_data) - min(demand_data):.2f}'
            props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
            ax.text(0.75, 0.75, textstr, transform=ax.transAxes, 
                verticalalignment='top', bbox=props, fontsize=10)
            
            # Configure plot
            ax.set_xlabel('Demanda (Litros)', fontsize=12)
            ax.set_ylabel('Densidad de Probabilidad', fontsize=12)
            ax.set_title('Distribución de Demanda', fontsize=14, fontweight='bold')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Convert to base64
            image_data = self._save_plot_as_base64(fig)
            plt.close(fig)
            
            return image_data
            
        except Exception as e:
            logger.error(f"Error generating demand histogram: {str(e)}")
            return None
    
    def generate_demand_box_plot(self, demand_data: List[float]) -> str:
        """Generate box plot for demand data outlier analysis"""
        try:
            fig, ax = plt.subplots(figsize=(8, 6))
            
            # Create box plot
            box_plot = ax.boxplot(demand_data, patch_artist=True, 
                                boxprops=dict(facecolor='lightblue', alpha=0.7),
                                medianprops=dict(color='red', linewidth=2))
            
            # Add scatter of actual data points
            ax.scatter([1] * len(demand_data), demand_data, alpha=0.6, s=30)
            
            # Calculate and display statistics
            q1 = np.percentile(demand_data, 25)
            q3 = np.percentile(demand_data, 75)
            iqr = q3 - q1
            lower_fence = q1 - 1.5 * iqr
            upper_fence = q3 + 1.5 * iqr
            
            # Identify outliers
            outliers = [x for x in demand_data if x < lower_fence or x > upper_fence]
            
            # Add statistics text
            stats_text = f'Q1: {q1:.2f}\nMediana: {np.median(demand_data):.2f}\nQ3: {q3:.2f}\nIQR: {iqr:.2f}\nOutliers: {len(outliers)}'
            ax.text(1.15, np.median(demand_data), stats_text, 
                verticalalignment='center', fontsize=10,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            # Configure plot
            ax.set_ylabel('Demanda (Litros)', fontsize=12)
            ax.set_title('Análisis de Outliers - Demanda', fontsize=14, fontweight='bold')
            ax.set_xticklabels(['Demanda'])
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Convert to base64
            image_data = self._save_plot_as_base64(fig)
            plt.close(fig)
            
            return image_data
            
        except Exception as e:
            logger.error(f"Error generating demand box plot: {str(e)}")
            return None
    
    def generate_demand_time_series(self, demand_data: List[float]) -> str:
        """Generate time series plot for demand data"""
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            
            # Time periods
            time_periods = list(range(1, len(demand_data) + 1))
            
            # Main time series plot
            ax1.plot(time_periods, demand_data, 'b-', marker='o', 
                    linewidth=2, markersize=4, label='Demanda')
            
            # Add moving average if we have enough data
            if len(demand_data) >= 7:
                window_size = min(7, len(demand_data) // 3)
                moving_avg = []
                for i in range(len(demand_data)):
                    start_idx = max(0, i - window_size // 2)
                    end_idx = min(len(demand_data), i + window_size // 2 + 1)
                    moving_avg.append(np.mean(demand_data[start_idx:end_idx]))
                
                ax1.plot(time_periods, moving_avg, 'r--', linewidth=2,
                        label=f'Media Móvil ({window_size})')
            
            ax1.set_xlabel('Período de Tiempo')
            ax1.set_ylabel('Demanda (Litros)')
            ax1.set_title('Serie Temporal de Demanda')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Autocorrelation plot (if we have enough data)
            if len(demand_data) > 10:
                try:
                    from statsmodels.tsa.stattools import acf
                    
                    # Calculate autocorrelation
                    autocorr = acf(demand_data, nlags=min(20, len(demand_data)//2))
                    lags = range(len(autocorr))
                    
                    ax2.bar(lags, autocorr, alpha=0.7)
                    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
                    ax2.axhline(y=0.05, color='red', linestyle='--', alpha=0.5, label='Umbral 5%')
                    ax2.axhline(y=-0.05, color='red', linestyle='--', alpha=0.5)
                    
                    ax2.set_xlabel('Rezago')
                    ax2.set_ylabel('Autocorrelación')
                    ax2.set_title('Función de Autocorrelación')
                    ax2.legend()
                    ax2.grid(True, alpha=0.3)
                    
                except ImportError:
                    # Fallback: simple lag plot
                    if len(demand_data) > 1:
                        ax2.scatter(demand_data[:-1], demand_data[1:], alpha=0.7)
                        ax2.set_xlabel('Demanda (t)')
                        ax2.set_ylabel('Demanda (t+1)')
                        ax2.set_title('Gráfico de Rezago')
                        ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Convert to base64
            image_data = self._save_plot_as_base64(fig)
            plt.close(fig)
            
            return image_data
            
        except Exception as e:
            logger.error(f"Error generating demand time series: {str(e)}")
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
    
    def plot_line_demand_chart(self, ax, chart_data: Dict):
        """Plot demand chart showing historical and simulated demand"""
        labels = np.array(chart_data['labels'])
        values = np.array(chart_data['datasets'][0]['values'])
        
        # Check if historical demand is available
        if 'historical_demand' in chart_data and chart_data['historical_demand']:
            historical_demand = chart_data['historical_demand']
            
            # Plot historical demand
            hist_labels = np.arange(1, len(historical_demand) + 1)
            ax.plot(hist_labels, historical_demand, 'b-', marker='s', 
                   label='Demanda Histórica', linewidth=2, markersize=6)
            
            # Plot simulated demand with offset
            sim_labels = labels + len(historical_demand)
            ax.plot(sim_labels, values, 'r-', marker='o',
                   label='Demanda Simulada', linewidth=2, markersize=6)
            
            # Add vertical separator
            ax.axvline(x=len(historical_demand), color='gray', linestyle='--', 
                      alpha=0.5, label='Inicio Simulación')
            
            # Add mean lines
            hist_mean = np.mean(historical_demand)
            sim_mean = np.mean(values)
            
            ax.axhline(y=hist_mean, color='blue', linestyle=':', alpha=0.5,
                      label=f'Media Hist.: {hist_mean:.2f}')
            ax.axhline(y=sim_mean, color='red', linestyle=':', alpha=0.5,
                      label=f'Media Sim.: {sim_mean:.2f}')
        else:
            # Standard demand plot without historical data
            ax.plot(labels, values, marker='o', label='Demanda Simulada',
                   linewidth=2, markersize=6)
            
            # Add regression line
            if len(labels) > 1:
                z = np.polyfit(labels, values, 1)
                p = np.poly1d(z)
                ax.plot(labels, p(labels), "--", alpha=0.8,
                       label=f'Tendencia: {z[0]:.2f}x + {z[1]:.2f}')
            
            # Add mean line
            mean_val = np.mean(values)
            ax.axhline(y=mean_val, color='green', linestyle=':', alpha=0.5,
                      label=f'Media: {mean_val:.2f}')
        
        ax.grid(True, alpha=0.3)
        ax.legend()