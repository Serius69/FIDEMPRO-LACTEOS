# utils/chart_utils.py
import logging
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import matplotlib.pyplot as plt
from django.core.cache import cache

from .chart_base import ChartBase
from .chart_demand import ChartDemand

logger = logging.getLogger(__name__)

class ChartGenerator(ChartBase, ChartDemand):
    """Main chart generator class that combines all chart functionality"""
    
    def __init__(self):
        super().__init__()
        self.chart_demand = ChartDemand()
    
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
                    totales = self._calculate_cumulative_totals(results_simulation)
                    futures[config['key']] = executor.submit(
                            self._generate_single_chart,
                            chart_data_vars, config['type'], simulation_id, 
                            simulation_instance, results_simulation,
                            config['title'], config['description'],
                            totales
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
        """Get enhanced chart configurations"""
        return [
            {
                'key': 'image_data_0',
                'type': 'barApilate',
                'variables': ['INGRESOS TOTALES', 'GANANCIAS TOTALES'],
                'title': 'Análisis Financiero: Ingresos vs Ganancias',
                'description': 'Comparación entre ingresos totales y ganancias totales por período'
            },
            {
                'key': 'image_data_1',
                'type': 'bar',
                'variables': ['VENTAS POR CLIENTE', 'DEMANDA INSATISFECHA'],
                'title': 'Eficiencia de Ventas',
                'description': 'Relación entre ventas realizadas y demanda no cubierta'
            },
            {
                'key': 'image_data_2',
                'type': 'line',
                'variables': ['GASTOS GENERALES', 'GASTOS OPERATIVOS', 'Total Gastos'],
                'title': 'Estructura de Costos',
                'description': 'Evolución y composición de los gastos empresariales'
            },
            {
                'key': 'image_data_3',
                'type': 'bar',
                'variables': ['Costo Unitario Producción', 'Ingreso Bruto'],
                'title': 'Análisis de Márgenes',
                'description': 'Comparación entre costos unitarios e ingresos brutos'
            },
            {
                'key': 'image_data_4',
                'type': 'line',
                'variables': ['Ingreso Bruto', 'INGRESOS TOTALES'],
                'title': 'Tendencia de Ingresos',
                'description': 'Evolución de ingresos brutos y totales en el período'
            },
            {
                'key': 'image_data_5',
                'type': 'line',
                'variables': ['COSTO TOTAL TRANSPORTE', 'Costo Promedio Mano Obra', 
                            'Costo Almacenamiento', 'COSTO TOTAL ADQUISICIÓN INSUMOS'],
                'title': 'Desglose de Costos Operativos',
                'description': 'Análisis detallado de los principales componentes de costo'
            },
            {
                'key': 'image_data_6',
                'type': 'line',
                'variables': ['TOTAL PRODUCTOS PRODUCIDOS', 'TOTAL PRODUCTOS VENDIDOS'],
                'title': 'Eficiencia Productiva',
                'description': 'Relación entre producción y ventas efectivas'
            },
            {
                'key': 'image_data_7',
                'type': 'line',
                'variables': ['COSTO PROMEDIO PRODUCCION', 'COSTO PROMEDIO VENTA'],
                'title': 'Análisis de Costos Promedio',
                'description': 'Evolución de costos promedio de producción y venta'
            },
            {
                'key': 'image_data_8',
                'type': 'line',
                'variables': ['Retorno Inversión', 'GANANCIAS TOTALES'],
                'title': 'Rentabilidad y ROI',
                'description': 'Análisis de retorno de inversión y ganancias acumuladas'
            }
        ]
    
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
        
    def _generate_single_chart(self, chart_data: Dict, chart_type: str, 
                             simulation_id: int, product_instance,
                             result_simulations: List, title: str, 
                             description: str, totales_acumulativos: Dict = None) -> Optional[str]:
        """Generate a single chart with enhanced styling"""
        try:
            fig = plt.figure(figsize=(15, 10))
            
            # Create subplots
            gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
            ax1 = fig.add_subplot(gs[0, :2])  # Income vs Expenses
            ax2 = fig.add_subplot(gs[0, 2])   # Profit Margin
            ax3 = fig.add_subplot(gs[1, :])   # Cost Breakdown
            ax4 = fig.add_subplot(gs[2, 0])   # Efficiency
            ax5 = fig.add_subplot(gs[2, 1])   # ROI
            ax6 = fig.add_subplot(gs[2, 2])   # Key Metrics
            
            # 1. Income vs Expenses
            income = totales_acumulativos.get('INGRESOS TOTALES', {}).get('total', 0)
            expenses = totales_acumulativos.get('GASTOS TOTALES', {}).get('total', 0)
            profit = income - expenses
            
            categories = ['Ingresos', 'Gastos', 'Ganancia']
            values = [income, expenses, profit]
            colors = ['green', 'red', 'blue' if profit > 0 else 'orange']
            
            bars = ax1.bar(categories, values, color=colors, alpha=0.7)
            for bar, val in zip(bars, values):
                ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                        f'${val:,.0f}', ha='center', va='bottom')
            
            ax1.set_title('Resumen Financiero')
            ax1.set_ylabel('Monto ($)')
            ax1.grid(True, axis='y', alpha=0.3)
            
            # 2. Profit Margin Gauge
            profit_margin = (profit / income * 100) if income > 0 else 0
            
            # Create gauge chart
            wedges, texts = ax2.pie([profit_margin, 100-profit_margin], 
                                   startangle=90, counterclock=False,
                                   colors=['green' if profit_margin > 0 else 'red', 'lightgray'])
            ax2.add_artist(plt.Circle((0, 0), 0.7, color='white'))
            ax2.text(0, 0, f'{profit_margin:.1f}%', ha='center', va='center', 
                    fontsize=20, fontweight='bold')
            ax2.set_title('Margen de Ganancia')
            
            # 3. Cost Breakdown
            cost_categories = []
            cost_values = []
            
            for var_name, data in totales_acumulativos.items():
                if 'COSTO' in var_name or 'GASTO' in var_name:
                    cost_categories.append(var_name[:20])  # Truncate long names
                    cost_values.append(data['total'])
            
            if cost_categories:
                ax3.barh(cost_categories, cost_values, alpha=0.7)
                ax3.set_xlabel('Monto ($)')
                ax3.set_title('Desglose de Costos')
                ax3.grid(True, axis='x', alpha=0.3)
            
            # 4. Efficiency Metrics
            production = totales_acumulativos.get('TOTAL PRODUCTOS PRODUCIDOS', {}).get('total', 0)
            sales = totales_acumulativos.get('TOTAL PRODUCTOS VENDIDOS', {}).get('total', 0)
            efficiency = (sales / production * 100) if production > 0 else 0
            
            ax4.bar(['Producción', 'Ventas'], [production, sales], alpha=0.7)
            ax4.text(0.5, 0.9, f'Eficiencia: {efficiency:.1f}%', 
                    transform=ax4.transAxes, ha='center', fontsize=12,
                    bbox=dict(boxstyle='round', facecolor='wheat'))
            ax4.set_title('Eficiencia Productiva')
            ax4.set_ylabel('Unidades')
            
            # 5. ROI
            roi = totales_acumulativos.get('Retorno Inversión', {}).get('total', 0)
            ax5.bar(['ROI'], [roi], alpha=0.7, color='purple')
            ax5.set_title('Retorno de Inversión')
            ax5.set_ylabel('Valor')
            ax5.set_ylim(0, max(roi * 1.2, 1))
            
            # 6. Key Metrics Summary
            metrics_text = "Métricas Clave:\n\n"
            metrics_text += f"Ingresos: ${income:,.0f}\n"
            metrics_text += f"Gastos: ${expenses:,.0f}\n"
            metrics_text += f"Ganancia: ${profit:,.0f}\n"
            metrics_text += f"Margen: {profit_margin:.1f}%\n"
            metrics_text += f"Eficiencia: {efficiency:.1f}%\n"
            metrics_text += f"ROI: {roi:.2f}"
            
            ax6.text(0.1, 0.5, metrics_text, transform=ax6.transAxes,
                    fontsize=11, verticalalignment='center',
                    bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
            ax6.axis('off')
            
            fig.suptitle('Dashboard Financiero Integral', fontsize=18, fontweight='bold')
            plt.tight_layout()
            
            image_data = self._save_plot_as_base64(fig)
            plt.close(fig)
            
            return image_data
            
        except Exception as e:
            logger.error(f"Error generating financial summary chart: {str(e)}")
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

# Función de utilidad para importar fácilmente el generador principal
    def get_chart_generator():
        """Get an instance of the main chart generator"""
        return ChartGenerator()

    def generate_chart(self, chart_type, chart_data, title="", description=""):
        """Generate chart based on type and data"""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Plot based on type
            plot_methods = {
                'linedemand': self.plot_line_demand_chart,
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
            
            plt.close(fig)
            
            return image_data
            
        except Exception as e:
            logger.error(f"Error generating {chart_type} chart: {str(e)}")
            if 'fig' in locals():
                plt.close(fig)
            return None
        
    def generate_financial_summary_chart(self, totales_acumulativos: Dict[str, Dict]) -> Optional[str]:
        """Generate comprehensive financial summary dashboard with multiple charts"""
        try:
            fig = plt.figure(figsize=(15, 10))
            
            # Create subplots
            gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
            ax1 = fig.add_subplot(gs[0, :2])  # Income vs Expenses
            ax2 = fig.add_subplot(gs[0, 2])   # Profit Margin
            ax3 = fig.add_subplot(gs[1, :])   # Cost Breakdown
            ax4 = fig.add_subplot(gs[2, 0])   # Efficiency
            ax5 = fig.add_subplot(gs[2, 1])   # ROI
            ax6 = fig.add_subplot(gs[2, 2])   # Key Metrics
            
            # 1. Income vs Expenses
            income = totales_acumulativos.get('INGRESOS TOTALES', {}).get('total', 0)
            expenses = totales_acumulativos.get('GASTOS TOTALES', {}).get('total', 0)
            profit = income - expenses
            
            categories = ['Ingresos', 'Gastos', 'Ganancia']
            values = [income, expenses, profit]
            colors = ['green', 'red', 'blue' if profit > 0 else 'orange']
            
            bars = ax1.bar(categories, values, color=colors, alpha=0.7)
            for bar, val in zip(bars, values):
                ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                        f'${val:,.0f}', ha='center', va='bottom')
            
            ax1.set_title('Resumen Financiero')
            ax1.set_ylabel('Monto ($)')
            ax1.grid(True, axis='y', alpha=0.3)
            
            # 2. Profit Margin Gauge
            profit_margin = (profit / income * 100) if income > 0 else 0
            wedges, texts = ax2.pie([profit_margin, 100-profit_margin], 
                                   startangle=90, counterclock=False,
                                   colors=['green' if profit_margin > 0 else 'red', 'lightgray'])
            ax2.add_artist(plt.Circle((0, 0), 0.7, color='white'))
            ax2.text(0, 0, f'{profit_margin:.1f}%', ha='center', va='center', 
                    fontsize=20, fontweight='bold')
            ax2.set_title('Margen de Ganancia')
            
            # 3. Cost Breakdown
            cost_categories = []
            cost_values = []
            for var_name, data in totales_acumulativos.items():
                if 'COSTO' in var_name or 'GASTO' in var_name:
                    cost_categories.append(var_name[:20])
                    cost_values.append(data['total'])
            
            if cost_categories:
                ax3.barh(cost_categories, cost_values, alpha=0.7)
                ax3.set_xlabel('Monto ($)')
                ax3.set_title('Desglose de Costos')
                ax3.grid(True, axis='x', alpha=0.3)
            
            # 4. Efficiency Metrics
            production = totales_acumulativos.get('TOTAL PRODUCTOS PRODUCIDOS', {}).get('total', 0)
            sales = totales_acumulativos.get('TOTAL PRODUCTOS VENDIDOS', {}).get('total', 0)
            efficiency = (sales / production * 100) if production > 0 else 0
            
            ax4.bar(['Producción', 'Ventas'], [production, sales], alpha=0.7)
            ax4.text(0.5, 0.9, f'Eficiencia: {efficiency:.1f}%', 
                    transform=ax4.transAxes, ha='center', fontsize=12,
                    bbox=dict(boxstyle='round', facecolor='wheat'))
            ax4.set_title('Eficiencia Productiva')
            ax4.set_ylabel('Unidades')
            
            # 5. ROI
            roi = totales_acumulativos.get('Retorno Inversión', {}).get('total', 0)
            ax5.bar(['ROI'], [roi], alpha=0.7, color='purple')
            ax5.set_title('Retorno de Inversión')
            ax5.set_ylabel('Valor')
            ax5.set_ylim(0, max(roi * 1.2, 1))
            
            # 6. Key Metrics Summary
            metrics_text = f"Métricas Clave:\n\n"
            metrics_text += f"Ingresos: ${income:,.0f}\n"
            metrics_text += f"Gastos: ${expenses:,.0f}\n"
            metrics_text += f"Ganancia: ${profit:,.0f}\n"
            metrics_text += f"Margen: {profit_margin:.1f}%\n"
            metrics_text += f"Eficiencia: {efficiency:.1f}%\n"
            metrics_text += f"ROI: {roi:.2f}"
            
            ax6.text(0.1, 0.5, metrics_text, transform=ax6.transAxes,
                    fontsize=11, verticalalignment='center',
                    bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
            ax6.axis('off')
            
            fig.suptitle('Dashboard Financiero Integral', fontsize=18, fontweight='bold')
            plt.tight_layout()
            
            image_data = self._save_plot_as_base64(fig)
            plt.close(fig)
            
            return image_data
            
        except Exception as e:
            logger.error(f"Error generating financial summary chart: {str(e)}")
            if 'fig' in locals():
                plt.close(fig)
            return None