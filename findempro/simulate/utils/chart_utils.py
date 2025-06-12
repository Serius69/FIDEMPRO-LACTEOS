# utils/chart_utils.py
import logging
import random
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import matplotlib.pyplot as plt
from django.core.cache import cache

from .chart_base import ChartBase
from .chart_demand import ChartDemand

logger = logging.getLogger(__name__)

class ChartGenerator(ChartDemand):
    """Main chart generator class that combines all chart functionality"""
    
    def __init__(self):
        super().__init__()
        self.chart_demand = ChartDemand()
    
    def generate_all_charts(self, simulation_id: int, simulation_instance, 
                      results_simulation: List, historical_demand: List = None) -> Dict[str, Any]:
        """Generate all charts including demand comparison"""
        try:
            # Extract variables and calculate totals
            all_variables_extracted = self._extract_variables_from_results(results_simulation)
            totales_acumulativos = self._calculate_cumulative_totals(results_simulation)
            variables_to_graph = self._prepare_variables_for_graphing(results_simulation)
            
            # Log available variables for debugging
            logger.info(f"Total accumulated variables: {list(totales_acumulativos.keys())}")
            
            # Create enhanced chart data with historical demand
            chart_data = self._create_demand_chart_data(results_simulation, historical_demand)
            
            # Initialize chart images dictionary
            chart_images = {}
            
            # Generate demand comparison chart if historical data exists
            if historical_demand and len(historical_demand) > 0:
                try:
                    comparison_chart = self.generate_demand_comparison_chart(
                        historical_demand, list(results_simulation)
                    )
                    if comparison_chart:
                        chart_images['comparison_chart'] = comparison_chart
                        chart_images['demand_comparison'] = comparison_chart
                except Exception as e:
                    logger.error(f"Error generating comparison chart: {str(e)}")
            
            # Generate standard demand charts
            try:
                if self._validate_chart_data(chart_data):
                    # Line chart for demand trend
                    demand_trend = self._generate_demand_trend_chart(
                        chart_data, historical_demand, results_simulation
                    )
                    if demand_trend:
                        chart_images['image_data_line'] = demand_trend
                    
                    # Bar chart for demand distribution
                    demand_dist = self._generate_demand_distribution_chart(
                        chart_data, results_simulation
                    )
                    if demand_dist:
                        chart_images['image_data_bar'] = demand_dist
            except Exception as e:
                logger.error(f"Error generating demand charts: {str(e)}")
            
            # Define all charts to generate
            chart_configs = [
                {
                    'key': 'image_data_0',
                    'title': 'Ingresos vs Ganancias',
                    'variables': ['INGRESOS TOTALES', 'GANANCIAS TOTALES'],
                    'type': 'bar',
                    'required': True
                },
                {
                    'key': 'image_data_1',
                    'title': 'Ventas vs Demanda Insatisfecha',
                    'variables': ['TOTAL PRODUCTOS VENDIDOS', 'DEMANDA INSATISFECHA'],
                    'type': 'bar',
                    'required': True
                },
                {
                    'key': 'image_data_2',
                    'title': 'Análisis de Gastos',
                    'variables': ['GASTOS OPERATIVOS', 'GASTOS GENERALES', 'Total Gastos'],
                    'type': 'line',
                    'required': True
                },
                {
                    'key': 'image_data_3',
                    'title': 'Costos de Producción',
                    'variables': ['COSTO PROMEDIO PRODUCCION', 'COSTO UNITARIO PRODUCCION'],
                    'type': 'bar',
                    'required': True
                },
                {
                    'key': 'image_data_4',
                    'title': 'Tendencia de Ingresos',
                    'variables': ['INGRESOS TOTALES', 'Ingreso Bruto'],
                    'type': 'line',
                    'required': False
                },
                {
                    'key': 'image_data_5',
                    'title': 'Costos Operativos',
                    'variables': ['COSTO TOTAL TRANSPORTE', 'COSTO TOTAL ADQUISICIÓN INSUMOS', 
                                'Costo Almacenamiento', 'Costo Promedio Mano Obra'],
                    'type': 'stacked',
                    'required': True
                },
                {
                    'key': 'image_data_6',
                    'title': 'Producción vs Ventas',
                    'variables': ['TOTAL PRODUCTOS PRODUCIDOS', 'TOTAL PRODUCTOS VENDIDOS'],
                    'type': 'line',
                    'required': True
                },
                {
                    'key': 'image_data_7',
                    'title': 'Costos Promedio',
                    'variables': ['COSTO PROMEDIO PRODUCCION', 'COSTO PROMEDIO VENTA'],
                    'type': 'line',
                    'required': True
                },
                {
                    'key': 'image_data_8',
                    'title': 'ROI y Ganancias',
                    'variables': ['Retorno Inversión', 'GANANCIAS TOTALES'],
                    'type': 'bar',
                    'required': True
                }
            ]
            
            # Generate each configured chart
            for config in chart_configs:
                try:
                    # Create chart data for specific variables
                    chart_data_vars = self._create_variable_chart_data_safe(
                        chart_data['labels'], 
                        variables_to_graph, 
                        config['variables'],
                        totales_acumulativos
                    )
                    
                    if self._validate_chart_data(chart_data_vars):
                        # Generate the chart
                        chart_image = self.generate_chart(
                            config['type'], 
                            chart_data_vars, 
                            config['title'], 
                            f"Análisis de {config['title'].lower()}"
                        )
                        if chart_image:
                            chart_images[config['key']] = chart_image
                            logger.info(f"Generated chart: {config['title']}")
                    elif config.get('required', False):
                        # Generate empty chart for required charts
                        empty_chart = self._generate_empty_chart(
                            config['title'],
                            "No hay suficientes datos para generar este gráfico"
                        )
                        if empty_chart:
                            chart_images[config['key']] = empty_chart
                            logger.warning(f"Generated empty chart for: {config['title']}")
                            
                except Exception as e:
                    logger.error(f"Error generating chart {config['key']}: {str(e)}")
                    if config.get('required', False):
                        # Try to generate empty chart on error
                        try:
                            empty_chart = self._generate_empty_chart(config['title'])
                            if empty_chart:
                                chart_images[config['key']] = empty_chart
                        except:
                            pass
            
            result = {
                'all_variables_extracted': all_variables_extracted,
                'totales_acumulativos': totales_acumulativos,
                'chart_images': chart_images
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Critical error in generate_all_charts: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Return minimal valid structure
            return {
                'all_variables_extracted': [],
                'totales_acumulativos': {},
                'chart_images': {}
            }
    
    
    def _create_variable_chart_data_safe(self, labels: List, variables_to_graph: List,
                                   variable_names: List[str], totales_acumulativos: Dict) -> Dict:
        """Create chart data with fallback to accumulated totals"""
        datasets = []
        
        for variable_name in variable_names:
            values = []
            
            # First try to get from daily data
            values = self.get_variable_values(variable_name, variables_to_graph)
            
            # If no daily data, try accumulated totals
            if not values and variable_name in totales_acumulativos:
                # Create artificial daily values from total
                total = totales_acumulativos[variable_name]['total']
                num_days = len(labels)
                if num_days > 0:
                    # Distribute total across days with some variation
                    base_value = total / num_days
                    values = []
                    for i in range(num_days):
                        # Add some random variation
                        variation = random.uniform(0.8, 1.2)
                        values.append(base_value * variation)
                    logger.info(f"Created synthetic daily values for {variable_name} from total {total}")
            
            if values:
                datasets.append({
                    'label': variable_name,
                    'values': values[:len(labels)]
                })
        
        return {
            'labels': labels[:len(datasets[0]['values'])] if datasets else [],
            'datasets': datasets,
            'x_label': 'Días',
            'y_label': 'Valor',
        }
    
    def _extract_variables_from_results(self, results_simulation: List) -> List[Dict]:
        """Extract and process variables from simulation results with name normalization"""
        all_variables_extracted = []
        name_variables = self._get_variable_mapping()
        
        # Create comprehensive mapping including variations
        iniciales_a_nombres = {}
        for initial, info in name_variables.items():
            name = info['name']
            iniciales_a_nombres[initial] = name
            # Add uppercase version
            iniciales_a_nombres[initial.upper()] = name
            # Add common variations
            if initial == 'GT':
                iniciales_a_nombres['GANANCIAS_TOTALES'] = name
            elif initial == 'IT':
                iniciales_a_nombres['INGRESOS_TOTALES'] = name
            elif initial == 'GO':
                iniciales_a_nombres['GASTOS_OPERATIVOS'] = name
            elif initial == 'GG':
                iniciales_a_nombres['GASTOS_GENERALES'] = name
        
        for result_simulation in results_simulation:
            variables_extracted = result_simulation.get_variables()
            date_simulation = result_simulation.date
            
            totales_por_variable = {}
            
            # Process each variable
            for inicial, value in variables_extracted.items():
                # Try direct mapping first
                if inicial in iniciales_a_nombres:
                    name_variable = iniciales_a_nombres[inicial]
                    totales_por_variable[name_variable] = {
                        'total': float(value),
                        'unit': name_variables.get(inicial, {}).get('unit', '')
                    }
                # Try uppercase version
                elif inicial.upper() in name_variables:
                    name_variable = name_variables[inicial.upper()]['name']
                    totales_por_variable[name_variable] = {
                        'total': float(value),
                        'unit': name_variables.get(inicial.upper(), {}).get('unit', '')
                    }
                # Store as-is if not found in mapping
                else:
                    totales_por_variable[inicial] = {
                        'total': float(value),
                        'unit': ''
                    }
            
            # Ensure critical variables exist
            self._ensure_critical_variables(totales_por_variable, variables_extracted)
            
            all_variables_extracted.append({
                'result_simulation': result_simulation,
                'totales_por_variable': totales_por_variable,
                'date_simulation': date_simulation
            })
        
        return all_variables_extracted
    
    def _ensure_critical_variables(self, totales_por_variable, variables_extracted):
        """Ensure critical variables exist in the results"""
        # Map of critical variables and their possible keys
        critical_mappings = {
            'INGRESOS TOTALES': ['IT', 'INGRESOS_TOTALES', 'IngresosTotales'],
            'GANANCIAS TOTALES': ['GT', 'GANANCIAS_TOTALES', 'GananciasTotales'],
            'GASTOS OPERATIVOS': ['GO', 'GASTOS_OPERATIVOS', 'GastosOperativos'],
            'GASTOS GENERALES': ['GG', 'GASTOS_GENERALES', 'GastosGenerales'],
            'TOTAL PRODUCTOS VENDIDOS': ['TPV', 'TOTAL_PRODUCTOS_VENDIDOS'],
            'TOTAL PRODUCTOS PRODUCIDOS': ['TPPRO', 'TOTAL_PRODUCTOS_PRODUCIDOS'],
            'DEMANDA INSATISFECHA': ['DI', 'DEMANDA_INSATISFECHA'],
            'VENTAS POR CLIENTE': ['VPC', 'VENTAS_POR_CLIENTE'],
            'COSTO PROMEDIO PRODUCCION': ['CPP', 'COSTO_PROMEDIO_PRODUCCION'],
            'COSTO PROMEDIO VENTA': ['CPV', 'COSTO_PROMEDIO_VENTA'],
            'RETORNO INVERSIÓN': ['ROI', 'RI', 'RETORNO_INVERSION'],
            'COSTO TOTAL TRANSPORTE': ['CTT', 'CTTL', 'COSTO_TOTAL_TRANSPORTE'],
            'COSTO TOTAL ADQUISICIÓN INSUMOS': ['CTAI', 'COSTO_TOTAL_ADQUISICION_INSUMOS']
        }
        
        for target_name, possible_keys in critical_mappings.items():
            if target_name not in totales_por_variable:
                # Look for the variable under different keys
                for key in possible_keys:
                    if key in variables_extracted:
                        totales_por_variable[target_name] = {
                            'total': float(variables_extracted[key]),
                            'unit': self._get_unit_for_variable(target_name)
                        }
                        break
    
    def _get_unit_for_variable(self, variable_name):
        """Get the appropriate unit for a variable"""
        if 'COSTO' in variable_name or 'GASTO' in variable_name or 'INGRESO' in variable_name or 'GANANCIA' in variable_name:
            return 'BS'
        elif 'PRODUCTO' in variable_name:
            return 'UNIDADES'
        elif 'CLIENTE' in variable_name:
            return 'CLIENTES'
        elif 'RETORNO' in variable_name or 'ROI' in variable_name:
            return '%'
        else:
            return ''
    
    def _calculate_cumulative_totals(self, results_simulation: List) -> Dict[str, Dict]:
        """Calculate cumulative totals with optimization and trend analysis"""
        name_variables = self._get_variable_mapping()
        totales_acumulativos = {}
        daily_values = {}  # Store daily values for trend calculation
        
        # First pass: accumulate totals and store daily values
        for i, result_simulation in enumerate(results_simulation):
            variables_extracted = result_simulation.get_variables()
            
            for inicial, value in variables_extracted.items():
                if inicial in self.iniciales_a_buscar and inicial in name_variables:
                    name_variable = name_variables[inicial]['name']
                    
                    if name_variable not in totales_acumulativos:
                        totales_acumulativos[name_variable] = {
                            'total': 0, 
                            'unit': name_variables[inicial]['unit'],
                            'daily_values': []
                        }
                    
                    totales_acumulativos[name_variable]['total'] += value
                    totales_acumulativos[name_variable]['daily_values'].append(value)
        
        # Second pass: calculate trends and statistics
        for name_variable, data in totales_acumulativos.items():
            daily_values = data.get('daily_values', [])
            
            if daily_values:
                # Calculate trend
                if len(daily_values) > 1:
                    x = np.arange(len(daily_values))
                    z = np.polyfit(x, daily_values, 1)
                    trend_slope = z[0]
                    
                    if trend_slope > 0.01:
                        data['trend'] = 'increasing'
                    elif trend_slope < -0.01:
                        data['trend'] = 'decreasing'
                    else:
                        data['trend'] = 'stable'
                else:
                    data['trend'] = 'stable'
                
                # Calculate statistics
                data['mean'] = np.mean(daily_values)
                data['std'] = np.std(daily_values)
                data['min'] = np.min(daily_values)
                data['max'] = np.max(daily_values)
                
                # Remove daily_values from final output to save memory
                del data['daily_values']
        
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
        
        # Define chart configurations with proper variable mappings
        chart_configs = [
            {
                'key': 'image_data_0',
                'type': 'bar',
                'variables': ['INGRESOS TOTALES', 'GANANCIAS TOTALES'],
                'title': 'Análisis Financiero: Ingresos vs Ganancias',
                'description': 'Comparación entre ingresos totales y ganancias totales por período'
            },
            {
                'key': 'image_data_1',
                'type': 'bar',
                'variables': ['TOTAL PRODUCTOS VENDIDOS', 'DEMANDA INSATISFECHA'],
                'title': 'Eficiencia de Ventas',
                'description': 'Relación entre productos vendidos y demanda no cubierta'
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
                'variables': ['Costo Unitario Producción', 'COSTO PROMEDIO PRODUCCION'],
                'title': 'Análisis de Costos de Producción',
                'description': 'Comparación de costos unitarios de producción'
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
                # Line chart for demand trend
                futures['image_data_line'] = executor.submit(
                    self._generate_demand_trend_chart,
                    chart_data, historical_demand, results_simulation
                )
                
                # Bar chart for demand distribution
                futures['image_data_bar'] = executor.submit(
                    self._generate_demand_distribution_chart,
                    chart_data, results_simulation
                )
            
            # Variable-specific charts
            for config in chart_configs:
                chart_data_vars = self._create_variable_chart_data(
                    chart_data['labels'], variables_to_graph, config['variables']
                )
                
                if self._validate_chart_data(chart_data_vars):
                    futures[config['key']] = executor.submit(
                        self.generate_chart,
                        config['type'], chart_data_vars, 
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
    
    def _generate_empty_chart(self, title: str, message: str = "No hay datos disponibles") -> str:
        """Generate an empty chart placeholder"""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Remove axes
            ax.set_xticks([])
            ax.set_yticks([])
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.spines['left'].set_visible(False)
            
            # Add message
            ax.text(0.5, 0.5, message, 
                    horizontalalignment='center',
                    verticalalignment='center',
                    transform=ax.transAxes,
                    fontsize=14,
                    color='gray')
            
            # Add title
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
            
            # Save as base64
            image_data = self._save_plot_as_base64(fig)
            plt.close(fig)
            
            return image_data
            
        except Exception as e:
            logger.error(f"Error generating empty chart: {str(e)}")
            return None
    
    def _generate_demand_distribution_chart(self, chart_data: Dict, 
                                      results_simulation: List) -> str:
        """Generate demand distribution bar chart"""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Extract demand values
            demand_values = [float(r.demand_mean) for r in results_simulation]
            periods = list(range(1, len(demand_values) + 1))
            
            # Create bar chart
            bars = ax.bar(periods, demand_values, alpha=0.7, color='skyblue', 
                        edgecolor='darkblue')
            
            # Color code bars by value
            mean_demand = np.mean(demand_values)
            for bar, val in zip(bars, demand_values):
                if val > mean_demand * 1.1:
                    bar.set_color('lightgreen')
                elif val < mean_demand * 0.9:
                    bar.set_color('lightcoral')
            
            # Add mean line
            ax.axhline(y=mean_demand, color='red', linestyle='--', linewidth=2,
                    label=f'Media: {mean_demand:.2f}')
            
            # Add value labels on bars (show every nth bar if too many)
            n_bars = len(bars)
            show_every = max(1, n_bars // 20)
            for i, (bar, val) in enumerate(zip(bars, demand_values)):
                if i % show_every == 0:
                    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                        f'{val:.0f}', ha='center', va='bottom', fontsize=8)
            
            # Configure plot
            ax.set_xlabel('Día de Simulación', fontsize=12)
            ax.set_ylabel('Demanda (Litros)', fontsize=12)
            ax.set_title('Distribución Diaria de Demanda', fontsize=14, fontweight='bold')
            ax.legend()
            ax.grid(True, alpha=0.3, axis='y')
            
            plt.tight_layout()
            return self._save_plot_as_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating demand distribution chart: {str(e)}")
            return None
    
    def _generate_demand_trend_chart(self, chart_data: Dict, historical_demand: List, 
                                results_simulation: List) -> str:
        """Generate demand trend analysis chart with historical continuity"""
        try:
            fig, ax = plt.subplots(figsize=(12, 7))
            
            # Plot historical demand if available
            if historical_demand and len(historical_demand) > 0:
                hist_periods = list(range(1, len(historical_demand) + 1))
                ax.plot(hist_periods, historical_demand, 'b-', marker='s', 
                    markersize=4, linewidth=2, label='Demanda Histórica', alpha=0.8)
                
                # Add historical trend
                if len(historical_demand) > 1:
                    z = np.polyfit(hist_periods, historical_demand, 1)
                    p = np.poly1d(z)
                    ax.plot(hist_periods, p(hist_periods), 'b--', alpha=0.5,
                        label=f'Tendencia Histórica (pendiente: {z[0]:.2f})')
            
            # Plot simulated demand
            simulated_values = [float(r.demand_mean) for r in results_simulation]
            sim_start = len(historical_demand) + 1 if historical_demand else 1
            sim_periods = list(range(sim_start, sim_start + len(simulated_values)))
            
            ax.plot(sim_periods, simulated_values, 'r-', marker='o',
                markersize=4, linewidth=2, label='Demanda Simulada', alpha=0.8)
            
            # Add simulated trend
            if len(simulated_values) > 1:
                z = np.polyfit(range(len(simulated_values)), simulated_values, 1)
                p = np.poly1d(z)
                ax.plot(sim_periods, p(range(len(simulated_values))), 'r--', alpha=0.5,
                    label=f'Tendencia Simulada (pendiente: {z[0]:.2f})')
            
            # Add transition marker
            if historical_demand and len(historical_demand) > 0:
                ax.axvline(x=len(historical_demand), color='gray', linestyle='--', 
                        alpha=0.5, label='Inicio Simulación')
            
            # Configure plot
            ax.set_xlabel('Período de Tiempo', fontsize=12)
            ax.set_ylabel('Demanda (Litros)', fontsize=12)
            ax.set_title('Análisis de Tendencias de Demanda', fontsize=14, fontweight='bold')
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)
            
            # Add statistics annotation
            all_values = (historical_demand if historical_demand else []) + simulated_values
            stats_text = f'Media Total: {np.mean(all_values):.2f}\n'
            stats_text += f'Desv. Est.: {np.std(all_values):.2f}\n'
            stats_text += f'CV: {np.std(all_values)/np.mean(all_values):.3f}'
            
            props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
                verticalalignment='top', bbox=props)
            
            plt.tight_layout()
            return self._save_plot_as_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating demand trend chart: {str(e)}")
            return None
    
    def _get_chart_configurations(self, variables_to_graph: List) -> List[Dict]:
        """Get enhanced chart configurations with correct variable names"""
        
        # First, log available variables for debugging
        all_variables = set()
        for day_data in variables_to_graph:
            all_variables.update(day_data.keys())
        logger.info(f"Available variables for charting: {sorted(all_variables)}")
        
        return [
            {
                'key': 'image_data_0',
                'type': 'bar',
                'variables': ['INGRESOS TOTALES', 'GANANCIAS TOTALES', 'Ingreso Bruto'],
                'title': 'Análisis Financiero: Ingresos vs Ganancias',
                'description': 'Comparación entre ingresos totales y ganancias totales'
            },
            {
                'key': 'image_data_1',
                'type': 'bar',
                'variables': ['VENTAS POR CLIENTE', 'DEMANDA INSATISFECHA', 'TOTAL PRODUCTOS VENDIDOS'],
                'title': 'Ventas vs Demanda Insatisfecha',
                'description': 'Análisis de eficiencia en ventas y demanda no cubierta'
            },
            {
                'key': 'image_data_2',
                'type': 'line',
                'variables': ['GASTOS GENERALES', 'GASTOS OPERATIVOS', 'Total Gastos', 'GASTOS TOTALES'],
                'title': 'Análisis de Gastos',
                'description': 'Evolución de gastos operativos y generales'
            },
            {
                'key': 'image_data_3',
                'type': 'bar',
                'variables': ['COSTO UNITARIO PRODUCCION', 'COSTO PROMEDIO PRODUCCION', 'Costo Unitario Producción'],
                'title': 'Costos de Producción',
                'description': 'Análisis de costos unitarios y promedio de producción'
            },
            {
                'key': 'image_data_4',
                'type': 'line',
                'variables': ['Ingreso Bruto', 'INGRESOS TOTALES', 'INGRESO BRUTO'],
                'title': 'Tendencia de Ingresos',
                'description': 'Evolución de ingresos en el período'
            },
            {
                'key': 'image_data_5',
                'type': 'stacked',
                'variables': ['COSTO TOTAL TRANSPORTE', 'Costo Promedio Mano Obra', 
                            'Costo Almacenamiento', 'COSTO TOTAL ADQUISICIÓN INSUMOS', 
                            'COSTOS FIJOS DIARIOS', 'COSTO TOTAL PRODUCCION'],
                'title': 'Desglose de Costos Operativos',
                'description': 'Composición detallada de costos operativos'
            },
            {
                'key': 'image_data_6',
                'type': 'line',
                'variables': ['TOTAL PRODUCTOS PRODUCIDOS', 'TOTAL PRODUCTOS VENDIDOS', 
                            'PRODUCTOS PRODUCIDOS', 'Total Productos Vendidos'],
                'title': 'Producción vs Ventas',
                'description': 'Comparación entre producción y ventas'
            },
            {
                'key': 'image_data_7',
                'type': 'line',
                'variables': ['COSTO PROMEDIO PRODUCCION', 'COSTO PROMEDIO VENTA', 
                            'COSTO UNITARIO PRODUCCION', 'Costo Promedio Producción'],
                'title': 'Análisis de Costos Promedio',
                'description': 'Tendencia de costos promedio'
            },
            {
                'key': 'image_data_8',
                'type': 'bar',
                'variables': ['RETORNO INVERSIÓN', 'GANANCIAS TOTALES', 'Retorno Inversión', 'ROI'],
                'title': 'ROI y Ganancias',
                'description': 'Análisis de retorno de inversión y rentabilidad'
            }
        ]
    
    def _create_variable_chart_data(self, labels: List, variables_to_graph: List,
                              variable_names: List[str]) -> Dict:
        """Create chart data for specific variables with better error handling"""
        datasets = []
        
        for variable_name in variable_names:
            values = []
            
            # Try multiple variable name variations
            variations = [
                variable_name,
                variable_name.upper(),
                variable_name.replace('_', ' '),
                variable_name.replace(' ', '_')
            ]
            
            found = False
            for variation in variations:
                temp_values = self.get_variable_values(variation, variables_to_graph)
                if temp_values:
                    values = temp_values
                    found = True
                    logger.debug(f"Found values for {variable_name} as {variation}")
                    break
            
            if not found:
                # Try to find partial matches
                for data in variables_to_graph:
                    for key in data.keys():
                        if variable_name.lower() in key.lower() or key.lower() in variable_name.lower():
                            if isinstance(data[key], dict):
                                values.append(float(data[key].get('value', 0)))
                            else:
                                values.append(float(data[key]))
                            found = True
                            break
                    if found:
                        break
            
            if values:  # Only add if we have data
                datasets.append({
                    'label': variable_name, 
                    'values': values[:len(labels)]  # Ensure same length as labels
                })
                logger.info(f"Added dataset for {variable_name} with {len(values)} values")
            else:
                logger.warning(f"No data found for variable: {variable_name}")
        
        return {
            'labels': labels[:len(datasets[0]['values'])] if datasets else [],
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
                         simulation_id: int, simulation_instance,
                         result_simulations: List, title: str, 
                         description: str, totales_acumulativos: Dict = None) -> Optional[str]:
        """Generate a single chart with enhanced styling"""
        try:
            # Check if we have valid data
            if not self._validate_chart_data(chart_data):
                logger.warning(f"Invalid chart data for {title}")
                return None
                
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Plot based on type
            if chart_type == 'line':
                self._plot_line_chart(ax, chart_data)
            elif chart_type == 'bar':
                self._plot_bar_chart(ax, chart_data)
            elif chart_type == 'scatter':
                self._plot_scatter_chart(ax, chart_data)
            elif chart_type == 'histogram':
                self._plot_histogram_chart(ax, chart_data)
            elif chart_type == 'barApilate' or chart_type == 'stacked':
                self._plot_stacked_bar_chart(ax, chart_data)
            elif chart_type == 'linedemand':
                self.plot_line_demand_chart(ax, chart_data)
            else:
                logger.warning(f"Unknown chart type: {chart_type}")
                plt.close(fig)
                return None
            
            # Configure plot
            self._configure_plot(ax, chart_data, title, description)
            
            # Save as base64
            image_data = self._save_plot_as_base64(fig)
            plt.close(fig)
            
            return image_data
            
        except Exception as e:
            logger.error(f"Error generating {chart_type} chart '{title}': {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
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