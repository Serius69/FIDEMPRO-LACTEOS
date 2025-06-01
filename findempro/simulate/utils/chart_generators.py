# utils/chart_generators.py
import base64
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

logger = logging.getLogger(__name__)


class ChartGenerator:
    """Optimized utility class for generating charts and visualizations"""
    
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
                          results_simulation: List) -> Dict[str, Any]:
        """Generate all charts with parallel processing"""
        cache_key = f"charts_{simulation_id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        # Extract variables and calculate totals
        all_variables_extracted = self._extract_variables_from_results(results_simulation)
        totales_acumulativos = self._calculate_cumulative_totals(results_simulation)
        variables_to_graph = self._prepare_variables_for_graphing(results_simulation)
        
        # Generate chart data
        chart_data = self._create_demand_chart_data(results_simulation)
        
        # Generate charts in parallel
        chart_images = self._generate_charts_parallel(
            simulation_id, simulation_instance, results_simulation, 
            chart_data, variables_to_graph
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
        
        # Create initials to names mapping
        iniciales_a_nombres = {
            initial: info['name'] 
            for initial, info in name_variables.items()
        }
        
        for result_simulation in results_simulation:
            variables_extracted = result_simulation.get_variables()
            date_simulation = result_simulation.date
            
            # Calculate totals per variable efficiently
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
    
    def _create_demand_chart_data(self, result_simulations: List) -> Dict:
        """Create chart data for demand visualization"""
        labels = []
        values = []
        
        for i, result_simulation in enumerate(result_simulations):
            labels.append(i + 1)
            values.append(float(result_simulation.demand_mean))
        
        return {
            'labels': labels,
            'datasets': [
                {'label': 'Demanda Simulada', 'values': values},
            ],
            'x_label': 'Días',
            'y_label': 'Demanda (Litros)',
        }
    
    def _generate_charts_parallel(self, simulation_id: int, simulation_instance, 
                                results_simulation: List, chart_data: Dict, 
                                variables_to_graph: List) -> Dict[str, str]:
        """Generate charts in parallel for better performance"""
        chart_images = {}
        
        # Define chart configurations
        chart_configs = self._get_chart_configurations(variables_to_graph)
        
        # Generate main charts
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            
            # Submit main demand charts
            if self._validate_chart_data(chart_data):
                futures['image_data_line'] = executor.submit(
                    self._generate_single_chart,
                    chart_data, 'linedemand', simulation_id, simulation_instance,
                    results_simulation, 'Gráfico Lineal de Demanda',
                    'Comportamiento de la demanda en los días de simulación'
                )
                
                futures['image_data_bar'] = executor.submit(
                    self._generate_single_chart,
                    chart_data, 'bar', simulation_id, simulation_instance,
                    results_simulation, 'Gráfico de Barras',
                    'Distribución de demanda por día'
                )
            
            # Submit variable charts
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
    
    def _get_chart_configurations(self, variables_to_graph: List) -> List[Dict]:
        """Get chart configurations"""
        return [
            {
                'key': 'image_data_0',
                'type': 'barApilate',
                'variables': ['INGRESOS TOTALES', 'GANANCIAS TOTALES'],
                'title': 'Ingresos vs Ganancias',
                'description': 'Comparación entre ingresos totales y ganancias totales'
            },
            {
                'key': 'image_data_1',
                'type': 'bar',
                'variables': ['VENTAS POR CLIENTE', 'DEMANDA INSATISFECHA'],
                'title': 'Ventas vs Demanda Insatisfecha',
                'description': 'Análisis de satisfacción de demanda'
            },
            {
                'key': 'image_data_2',
                'type': 'line',
                'variables': ['GASTOS GENERALES', 'GASTOS OPERATIVOS', 'Total Gastos'],
                'title': 'Análisis de Gastos',
                'description': 'Evolución de gastos generales y operativos'
            },
            {
                'key': 'image_data_3',
                'type': 'bar',
                'variables': ['Costo Unitario Producción', 'Ingreso Bruto'],
                'title': 'Costos vs Ingresos',
                'description': 'Relación entre costos de producción e ingresos'
            },
            {
                'key': 'image_data_4',
                'type': 'line',
                'variables': ['Ingreso Bruto', 'INGRESOS TOTALES'],
                'title': 'Evolución de Ingresos',
                'description': 'Tendencia de ingresos brutos y totales'
            },
            {
                'key': 'image_data_5',
                'type': 'line',
                'variables': ['COSTO TOTAL TRANSPORTE', 'Costo Promedio Mano Obra', 
                            'Costo Almacenamiento', 'COSTO TOTAL ADQUISICIÓN INSUMOS'],
                'title': 'Análisis de Costos Operativos',
                'description': 'Desglose de costos operativos principales'
            },
            {
                'key': 'image_data_6',
                'type': 'line',
                'variables': ['TOTAL PRODUCTOS PRODUCIDOS', 'TOTAL PRODUCTOS VENDIDOS'],
                'title': 'Producción vs Ventas',
                'description': 'Comparación entre producción y ventas'
            },
            {
                'key': 'image_data_7',
                'type': 'line',
                'variables': ['COSTO PROMEDIO PRODUCCION', 'COSTO PROMEDIO VENTA'],
                'title': 'Costos Promedio',
                'description': 'Evolución de costos promedio de producción y venta'
            },
            {
                'key': 'image_data_8',
                'type': 'line',
                'variables': ['Retorno Inversión', 'GANANCIAS TOTALES'],
                'title': 'ROI y Ganancias',
                'description': 'Análisis de retorno de inversión y ganancias'
            }
        ]
    
    def _validate_chart_data(self, chart_data: Dict) -> bool:
        """Validate chart data before plotting"""
        if not chart_data or 'labels' not in chart_data or 'datasets' not in chart_data:
            return False
        
        if not chart_data['labels'] or not chart_data['datasets']:
            return False
        
        # Check all datasets have same length as labels
        labels_len = len(chart_data['labels'])
        for dataset in chart_data['datasets']:
            if len(dataset.get('values', [])) != labels_len:
                return False
        
        return True
    
    def _create_variable_chart_data(self, labels: List, variables_to_graph: List,
                                  variable_names: List[str]) -> Dict:
        """Create chart data for specific variables"""
        datasets = []
        
        for variable_name in variable_names:
            values = self.get_variable_values(variable_name, variables_to_graph)
            if values:  # Only add if we have data
                datasets.append({'label': variable_name, 'values': values})
        
        return {
            'labels': labels[:len(values)] if datasets else [],
            'datasets': datasets,
            'x_label': 'Días',
            'y_label': 'Valor',
        }
    
    def get_variable_values(self, variable_to_search: str, 
                          data_list: List[Dict]) -> List[float]:
        """Extract values for a specific variable from data list"""
        values_for_variable = []
        
        for data in data_list:
            if variable_to_search in data:
                if isinstance(data[variable_to_search], dict):
                    value = data[variable_to_search].get('value', 0)
                    values_for_variable.append(float(value))
                else:
                    logger.warning(f"{variable_to_search} is not a dictionary")
        
        return values_for_variable
    
    def _generate_single_chart(self, chart_data: Dict, chart_type: str, 
                             simulation_id: int, product_instance,
                             result_simulations: List, title: str, 
                             description: str) -> Optional[str]:
        """Generate a single chart and return base64 encoded image"""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Plot based on type
            plot_methods = {
                'linedemand': self._plot_line_demand_chart,
                'line': self._plot_line_chart,
                'bar': self._plot_bar_chart,
                'scatter': self._plot_scatter_chart,
                'histogram': self._plot_histogram_chart,
                'barApilate': self._plot_stacked_bar_chart,
            }
            
            plot_method = plot_methods.get(chart_type)
            if plot_method:
                plot_method(ax, chart_data)
            else:
                plt.close(fig)
                return None
            
            # Configure plot
            self._configure_plot(ax, chart_data, title, description)
            
            # Save as base64
            image_data = self._save_plot_as_base64(fig)
            
            # Save to database (optional)
            # self._save_chart_to_database(...)
            
            plt.close(fig)
            
            return image_data
            
        except Exception as e:
            logger.error(f"Error generating {chart_type} chart: {str(e)}")
            return None
    
    def _plot_histogram_chart(self, ax, chart_data: Dict):
        """Plot histogram with statistics"""
        for dataset in chart_data['datasets']:
            values = dataset['values']
            
            # Plot histogram with KDE
            n, bins, patches = ax.hist(values, bins=20, alpha=0.7, 
                                      density=True, label=dataset['label'])
            
            # Add KDE curve
            from scipy import stats
            kde = stats.gaussian_kde(values)
            x_range = np.linspace(min(values), max(values), 100)
            ax.plot(x_range, kde(x_range), linewidth=2)
            
            # Add statistics
            mean_val = np.mean(values)
            std_val = np.std(values)
            ax.axvline(mean_val, color='red', linestyle='--', 
                      label=f'Media: {mean_val:.2f}')
            
            # Add text box with stats
            textstr = f'μ={mean_val:.2f}\nσ={std_val:.2f}'
            props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            ax.text(0.05, 0.95, textstr, transform=ax.transAxes, 
                   verticalalignment='top', bbox=props)
        
        ax.legend()
        ax.grid(True, axis='y', alpha=0.3)
    
    def _plot_stacked_bar_chart(self, ax, chart_data: Dict):
        """Plot stacked bar chart"""
        labels = chart_data['labels']
        x = np.arange(len(labels))
        bottom = np.zeros(len(labels))
        
        for dataset in chart_data['datasets']:
            values = np.array(dataset['values'])
            ax.bar(x, values, label=dataset['label'], bottom=bottom, alpha=0.8)
            bottom += values
        
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend()
        ax.grid(True, axis='y', alpha=0.3)
    
    def _configure_plot(self, ax, chart_data: Dict, title: str, description: str):
        """Configure plot appearance and labels"""
        # Set labels
        ax.set_xlabel(chart_data.get('x_label', 'X'), fontsize=12)
        ax.set_ylabel(chart_data.get('y_label', 'Y'), fontsize=12)
        
        # Set title
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        # Rotate x labels if many
        if len(chart_data['labels']) > 20:
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Add description as subtitle
        ax.text(0.5, -0.15, description, transform=ax.transAxes, 
               ha='center', fontsize=10, style='italic', wrap=True)
        
        # Improve layout
        plt.tight_layout()
    
    def _save_plot_as_base64(self, fig: Figure) -> str:
        """Save matplotlib figure as base64 encoded string"""
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        buffer.close()
        return image_data
    
    def _save_chart_to_database(self, title: str, chart_type: str, 
                              chart_data: Dict, product_instance, 
                              result_simulations: List, image_data: str):
        """Save chart information to database (optional)"""
        try:
            chart, created = Chart.objects.update_or_create(
                fk_product=product_instance,
                chart_type=chart_type,
                defaults={
                    'title': title,
                    'chart_data': chart_data,
                }
            )
            
            # Save image
            chart.save_chart_image(image_data)
            
        except Exception as e:
            logger.error(f"Error saving chart to database: {str(e)}")
    
    # Additional utility methods for specific chart types
    
    def generate_demand_forecast_chart(self, results: List, periods: int = 30) -> str:
        """Generate demand forecast chart with predictions"""
        try:
            # Extract historical data
            dates = [r.date for r in results]
            demands = [float(r.demand_mean) for r in results]
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Plot historical data
            ax.plot(dates, demands, 'b-', label='Histórico', linewidth=2)
            
            # Generate forecast
            if len(demands) > 7:
                from statsmodels.tsa.holtwinters import ExponentialSmoothing
                
                model = ExponentialSmoothing(demands, seasonal_periods=7, 
                                           trend='add', seasonal='add')
                fitted_model = model.fit()
                
                # Predict
                forecast = fitted_model.forecast(periods)
                forecast_dates = [dates[-1] + timedelta(days=i+1) 
                                for i in range(periods)]
                
                ax.plot(forecast_dates, forecast, 'r--', 
                       label=f'Pronóstico ({periods} días)', linewidth=2)
                
                # Add confidence intervals
                std_error = np.std(fitted_model.resid)
                lower_bound = forecast - 1.96 * std_error
                upper_bound = forecast + 1.96 * std_error
                
                ax.fill_between(forecast_dates, lower_bound, upper_bound, 
                              alpha=0.2, color='red', label='IC 95%')
            
            ax.set_xlabel('Fecha')
            ax.set_ylabel('Demanda (L)')
            ax.set_title('Pronóstico de Demanda')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Format dates
            fig.autofmt_xdate()
            
            return self._save_plot_as_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating forecast chart: {str(e)}")
            return None
        finally:
            plt.close(fig)
    
    def generate_correlation_heatmap(self, variables_data: Dict[str, List[float]]) -> str:
        """Generate correlation heatmap for variables"""
        try:
            # Create correlation matrix
            import pandas as pd
            
            df = pd.DataFrame(variables_data)
            corr_matrix = df.corr()
            
            # Create heatmap
            fig, ax = plt.subplots(figsize=(12, 10))
            
            sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', 
                       center=0, square=True, linewidths=0.5,
                       cbar_kws={"shrink": 0.8}, ax=ax)
            
            ax.set_title('Matriz de Correlación de Variables', fontsize=16, pad=20)
            
            plt.tight_layout()
            
            return self._save_plot_as_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating correlation heatmap: {str(e)}")
            return None
        finally:
            plt.close(fig)
    
    def generate_dashboard_summary(self, simulation_data: Dict) -> Dict[str, str]:
        """Generate a complete dashboard summary with multiple charts"""
        summary_charts = {}
        
        try:
            # Create figure with subplots
            fig = plt.figure(figsize=(16, 10))
            
            # Create grid
            gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
            
            # Add different chart types
            ax1 = fig.add_subplot(gs[0, :2])  # Top left - wide
            ax2 = fig.add_subplot(gs[0, 2])   # Top right
            ax3 = fig.add_subplot(gs[1, :])   # Middle - full width
            ax4 = fig.add_subplot(gs[2, 0])   # Bottom left
            ax5 = fig.add_subplot(gs[2, 1])   # Bottom middle
            ax6 = fig.add_subplot(gs[2, 2])   # Bottom right
            
            # Plot different visualizations
            # ... (add specific plots based on simulation_data)
            
            fig.suptitle('Resumen de Simulación', fontsize=16, fontweight='bold')
            
            summary_charts['dashboard'] = self._save_plot_as_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating dashboard summary: {str(e)}")
        finally:
            plt.close('all')
        
        return summary_charts
    
    # Performance monitoring methods
    
    def get_chart_generation_stats(self) -> Dict[str, Any]:
        """Get statistics about chart generation performance"""
        stats = cache.get('chart_generation_stats', {})
        return {
            'total_generated': stats.get('total', 0),
            'average_time': stats.get('avg_time', 0),
            'cache_hits': stats.get('cache_hits', 0),
            'errors': stats.get('errors', 0),
        }
    
    def _update_generation_stats(self, generation_time: float, success: bool = True):
        """Update chart generation statistics"""
        stats = cache.get('chart_generation_stats', {
            'total': 0,
            'total_time': 0,
            'cache_hits': 0,
            'errors': 0
        })
        
        stats['total'] += 1
        stats['total_time'] += generation_time
        stats['avg_time'] = stats['total_time'] / stats['total']
        
        if not success:
            stats['errors'] += 1
        
        cache.set('chart_generation_stats', stats, 86400)  # 24 hours_line_demand_chart(self, ax, chart_data: Dict):
        """Plot enhanced line chart with regression and trend analysis"""
        labels = np.array(chart_data['labels'])
        values = np.array(chart_data['datasets'][0]['values'])
        
        # Plot main line
        ax.plot(labels, values, marker='o', label='Demanda Simulada', 
               linewidth=2, markersize=6)
        
        # Add regression line
        if len(labels) > 1:
            z = np.polyfit(labels, values, 1)
            p = np.poly1d(z)
            ax.plot(labels, p(labels), "--", alpha=0.8, 
                   label=f'Tendencia: {z[0]:.2f}x + {z[1]:.2f}')
        
        # Add confidence interval
        if len(values) > 3:
            from scipy import stats
            confidence = 0.95
            mean = np.mean(values)
            sem = stats.sem(values)
            h = sem * stats.t.ppf((1 + confidence) / 2., len(values)-1)
            
            ax.fill_between(labels, mean - h, mean + h, alpha=0.2, 
                          label=f'IC {confidence*100:.0f}%')
        
        ax.grid(True, alpha=0.3)
        ax.legend()
    
    def _plot_line_chart(self, ax, chart_data: Dict):
        """Plot standard line chart"""
        labels = chart_data['labels']
        
        for i, dataset in enumerate(chart_data['datasets']):
            ax.plot(labels, dataset['values'], label=dataset['label'], 
                   linewidth=2, marker='o', markersize=4)
        
        ax.grid(True, alpha=0.3)
        ax.legend()
    
    def _plot_bar_chart(self, ax, chart_data: Dict):
        """Plot bar chart"""
        labels = chart_data['labels']
        x = np.arange(len(labels))
        width = 0.8 / len(chart_data['datasets'])
        
        for i, dataset in enumerate(chart_data['datasets']):
            offset = (i - len(chart_data['datasets'])/2) * width + width/2
            ax.bar(x + offset, dataset['values'], width, 
                  label=dataset['label'], alpha=0.8)
        
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend()
        ax.grid(True, axis='y', alpha=0.3)
    
    def _plot_scatter_chart(self, ax, chart_data: Dict):
        """Plot scatter chart with regression lines"""
        labels = chart_data['labels']
        
        for i, dataset in enumerate(chart_data['datasets']):
            ax.scatter(labels, dataset['values'], label=dataset['label'], 
                      s=50, alpha=0.7)
            
            # Add regression line
            if len(labels) > 1:
                z = np.polyfit(labels, dataset['values'], 1)
                p = np.poly1d(z)
                ax.plot(labels, p(labels), '--', alpha=0.8)
        
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_line_demand_chart(self, ax, chart_data: Dict):
        """Plot enhanced line chart with regression and trend analysis"""
        labels = np.array(chart_data['labels'])
        values = np.array(chart_data['datasets'][0]['values'])
        
        # Plot main line
        ax.plot(labels, values, marker='o', label='Demanda Simulada', 
               linewidth=2, markersize=6)
        
        # Add regression line
        if len(labels) > 1:
            z = np.polyfit(labels, values, 1)
            p = np.poly1d(z)
            ax.plot(labels, p(labels), "--", alpha=0.8, 
                   label=f'Tendencia: {z[0]:.2f}x + {z[1]:.2f}')
        
        # Add confidence interval
        if len(values) > 3:
            from scipy import stats
            confidence = 0.95
            mean = np.mean(values)
            sem = stats.sem(values)
            h = sem * stats.t.ppf((1 + confidence) / 2., len(values)-1)
            
            ax.fill_between(labels, mean - h, mean + h, alpha=0.2, 
                          label=f'IC {confidence*100:.0f}%')
        
        ax.grid(True, alpha=0.3)
        ax.legend()