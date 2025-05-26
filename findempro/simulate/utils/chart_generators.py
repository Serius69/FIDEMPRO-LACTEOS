# utils/chart_generators.py
import base64
from io import BytesIO

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

from django.shortcuts import get_object_or_404

from dashboards.models import Chart
from variable.models import Variable

# Set matplotlib to non-interactive mode
matplotlib.use('Agg')


class ChartGenerator:
    """Utility class for generating various types of charts and visualizations"""
    
    def __init__(self):
        self.iniciales_a_buscar = [
            'CTR', 'CTAI', 'TPV', 'TPPRO', 'DI', 'VPC', 'IT', 'GT', 'TCA', 
            'NR', 'GO', 'GG', 'GT', 'CTTL', 'CPP', 'CPV', 'CPI', 'CPMO', 
            'CUP', 'PVR', 'TG', 'IB', 'MB', 'RI', 'RTI', 'RTC', 'PE', 
            'HO', 'CHO', 'CA'
        ]
    
    def generate_all_charts(self, simulation_id, simulation_instance, results_simulation):
        """Generate all charts and analysis data for simulation results"""
        # Extract variables and calculate totals
        all_variables_extracted = self._extract_variables_from_results(results_simulation)
        totales_acumulativos = self._calculate_cumulative_totals(results_simulation)
        variables_to_graph = self._prepare_variables_for_graphing(results_simulation)
        
        # Generate chart data
        chart_data = self._create_demand_chart_data(results_simulation)
        
        # Generate various chart images
        chart_images = self._generate_chart_images(
            simulation_id, simulation_instance, results_simulation, 
            chart_data, variables_to_graph
        )
        
        return {
            'all_variables_extracted': all_variables_extracted,
            'totales_acumulativos': totales_acumulativos,
            'chart_images': chart_images
        }
    
    def _extract_variables_from_results(self, results_simulation):
        """Extract and process variables from simulation results"""
        all_variables_extracted = []
        variables_db = Variable.objects.all()
        name_variables = {
            variable.initials: {'name': variable.name, 'unit': variable.unit} 
            for variable in variables_db
        }
        
        for result_simulation in results_simulation:
            variables_extracted = result_simulation.get_variables()
            date_simulation = result_simulation.date
            
            # Filter variables that match our criteria
            filtered_variables = Variable.objects.filter(
                initials__in=self.iniciales_a_buscar
            ).values('name', 'initials')
            
            iniciales_a_nombres = {
                variable['initials']: variable['name'] 
                for variable in filtered_variables
            }
            
            # Calculate totals per variable
            totales_por_variable = {}
            for inicial, value in variables_extracted.items():
                if inicial in iniciales_a_nombres:
                    name_variable = iniciales_a_nombres[inicial]
                    if name_variable not in totales_por_variable:
                        totales_por_variable[name_variable] = {
                            'total': 0,
                            'unit': name_variables.get(inicial, {}).get('unit', None)
                        }
                    totales_por_variable[name_variable]['total'] += value
                    totales_por_variable[name_variable]['unit'] = name_variables.get(
                        inicial, {}
                    ).get('unit', totales_por_variable[name_variable]['unit'])
            
            all_variables_extracted.append({
                'result_simulation': result_simulation,
                'totales_por_variable': totales_por_variable,
                'date_simulation': date_simulation
            })
        
        return all_variables_extracted
    
    def _calculate_cumulative_totals(self, results_simulation):
        """Calculate cumulative totals for all variables"""
        variables_db = Variable.objects.all()
        name_variables = {
            variable.initials: {'name': variable.name, 'unit': variable.unit} 
            for variable in variables_db
        }
        
        totales_acumulativos = {}
        
        for result_simulation in results_simulation:
            variables_extracted = result_simulation.get_variables()
            filtered_variables = {
                name_variables[inicial]['name']: {
                    'value': value, 
                    'unit': name_variables[inicial]['unit']
                }
                for inicial, value in variables_extracted.items() 
                if inicial in self.iniciales_a_buscar
            }
            
            # Calculate cumulative totals
            for name_variable, info_variable in filtered_variables.items():
                if name_variable not in totales_acumulativos:
                    totales_acumulativos[name_variable] = {
                        'total': 0, 
                        'unit': info_variable['unit']
                    }
                totales_acumulativos[name_variable]['total'] += info_variable['value']
        
        return totales_acumulativos
    
    def _prepare_variables_for_graphing(self, results_simulation):
        """Prepare variables data for chart generation"""
        variables_db = Variable.objects.all()
        name_variables = {
            variable.initials: {'name': variable.name, 'unit': variable.unit} 
            for variable in variables_db
        }
        
        variables_to_graph = []
        
        for result_simulation in results_simulation:
            variables_extracted = result_simulation.get_variables()
            filtered_variables = {
                name_variables[inicial]['name']: {
                    'value': value, 
                    'unit': name_variables[inicial]['unit']
                }
                for inicial, value in variables_extracted.items() 
                if inicial in self.iniciales_a_buscar
            }
            variables_to_graph.append(filtered_variables)
        
        return variables_to_graph
    
    def _create_demand_chart_data(self, result_simulations):
        """Create chart data for demand visualization"""
        all_labels = []
        all_values = []
        
        for i, result_simulation in enumerate(result_simulations):
            data = result_simulation.get_average_demand_by_date()
            if data:
                for entry in data:
                    all_labels.append(i + 1)
                    all_values.append(entry['average_demand'])
        
        # Sort data
        sorted_data = sorted(zip(all_labels, all_values), key=lambda x: x[0])
        if sorted_data:
            all_labels, all_values = zip(*sorted_data)
        else:
            all_labels = []
            all_values = []
        
        return {
            'labels': all_labels,
            'datasets': [
                {'label': 'Demanda Simulada', 'values': all_values},
            ],
            'x_label': 'Dias',
            'y_label': 'Demanda (Litros)',
        }
    
    def _generate_chart_images(self, simulation_id, simulation_instance, results_simulation, 
                             chart_data, variables_to_graph):
        """Generate all chart images"""
        product_instance = get_object_or_404(
            Product, 
            pk=simulation_instance.fk_questionary_result.fk_questionary.fk_product.id
        )
        
        chart_images = {}
        
        # Generate main demand charts
        if len(chart_data['labels']) == len(chart_data['datasets'][0]['values']):
            try:
                chart_images['image_data_line'] = self.plot_and_save_chart(
                    chart_data, 'linedemand', simulation_id, product_instance, 
                    results_simulation, 'Grafico Lineal', 
                    'Este grafico muestra como es el comportamiento de la demanda en los dias de simulacion.'
                )
                
                chart_images['image_data_bar'] = self.plot_and_save_chart(
                    chart_data, 'bar', simulation_id, product_instance, 
                    results_simulation, 'Gráfico de Barras',
                    'Este gráfico de dispersión muestra la relación entre diferentes variables para el producto.'
                )
                
                chart_images['image_data_candlestick'] = self.plot_and_save_chart(
                    chart_data, 'scatter', simulation_id, product_instance, 
                    results_simulation, 'Gráfico Lineal',
                    'Este gráfico de dispersión muestra la relación entre diferentes variables para el producto.'
                )
                
                chart_images['image_data_histogram'] = self.plot_and_save_chart(
                    chart_data, 'histogram', simulation_id, product_instance, 
                    results_simulation, 'Gráfico Lineal',
                    'Este gráfico de dispersión muestra la relación entre diferentes variables para el producto.'
                )
            except Exception as e:
                print(f"Error generating chart: {e}")
        
        # Generate variable-specific charts
        chart_images.update(self._generate_variable_charts(
            simulation_id, product_instance, results_simulation, variables_to_graph
        ))
        
        return chart_images
    
    def _generate_variable_charts(self, simulation_id, product_instance, results_simulation, variables_to_graph):
        """Generate charts for specific variable combinations"""
        all_labels = list(range(1, len(variables_to_graph) + 1))
        chart_images = {}
        
        # Define chart configurations
        chart_configs = [
            {
                'key': 'image_data_0',
                'type': 'barApilate',
                'variables': ['INGRESOS TOTALES', 'GANANCIAS TOTALES'],
                'title': 'Grafico de Barras',
                'description': 'Este gráfico de barras muestra la relación entre diferentes variables para el producto.'
            },
            {
                'key': 'image_data_1',
                'type': 'bar',
                'variables': ['VENTAS POR CLIENTE', 'DEMANDA INSATISFECHA'],
                'title': 'Gráfico de Barras',
                'description': 'Este gráfico de dispersión muestra la relación entre diferentes variables para el producto.'
            },
            {
                'key': 'image_data_2',
                'type': 'line',
                'variables': ['GASTOS GENERALES', 'GASTOS OPERATIVOS', 'Total Gastos'],
                'title': 'Gráfico Lineal',
                'description': 'Este gráfico de dispersión muestra la relación entre diferentes variables para el producto.'
            },
            {
                'key': 'image_data_3',
                'type': 'bar',
                'variables': ['Costo Unitario Producción', 'Ingreso Bruto'],
                'title': 'Gráfico de Barras',
                'description': 'Este gráfico de dispersión muestra la relación entre diferentes variables para el producto.'
            },
            {
                'key': 'image_data_4',
                'type': 'line',
                'variables': ['Ingreso Bruto', 'INGRESOS TOTALES'],
                'title': 'Gráfico Lineal',
                'description': 'Este gráfico de dispersión muestra la relación entre diferentes variables para el producto.'
            },
            {
                'key': 'image_data_5',
                'type': 'line',
                'variables': ['COSTO TOTAL TRANSPORTE', 'Costo Promedio Mano Obra', 'Costo Almacenamiento', 'COSTO TOTAL ADQUISICIÓN INSUMOS'],
                'title': 'Gráfico de Barras',
                'description': 'Este gráfico de dispersión muestra la relación entre diferentes variables para el producto.'
            },
            {
                'key': 'image_data_6',
                'type': 'line',
                'variables': ['TOTAL PRODUCTOS PRODUCIDOS', 'TOTAL PRODUCTOS VENDIDOS'],
                'title': 'Gráfico Lineal',
                'description': 'Este gráfico de dispersión muestra la relación entre diferentes variables para el producto.'
            },
            {
                'key': 'image_data_7',
                'type': 'line',
                'variables': ['COSTO PROMEDIO PRODUCCION', 'COSTO PROMEDIO VENTA'],
                'title': 'Gráfico Lineal',
                'description': 'Este gráfico de dispersión muestra la relación entre diferentes variables para el producto.'
            },
            {
                'key': 'image_data_8',
                'type': 'line',
                'variables': ['Retorno Inversión', 'GANANCIAS TOTALES'],
                'title': 'Gráfico Lineal',
                'description': 'Este gráfico de dispersión muestra la relación entre diferentes variables para el producto.'
            }
        ]
        
        # Generate each chart
        for config in chart_configs:
            chart_data = self._create_variable_chart_data(
                all_labels, variables_to_graph, config['variables']
            )
            
            chart_images[config['key']] = self.plot_and_save_chart(
                chart_data, config['type'], simulation_id, product_instance,
                results_simulation, config['title'], config['description']
            )
        
        return chart_images
    
    def _create_variable_chart_data(self, labels, variables_to_graph, variable_names):
        """Create chart data for specific variables"""
        datasets = []
        for variable_name in variable_names:
            values = self.get_variable_values(variable_name, variables_to_graph)
            datasets.append({'label': variable_name, 'values': values})
        
        return {
            'labels': labels,
            'datasets': datasets,
            'x_label': 'Dias',
            'y_label': 'Pesos Bolivianos',
        }
    
    def get_variable_values(self, variable_to_search, data_list):
        """Extract values for a specific variable from data list"""
        values_for_variable = []
        
        for data in data_list:
            if variable_to_search in data:
                if isinstance(data[variable_to_search], dict):
                    value_for_variable = data[variable_to_search]['value']
                    values_for_variable.append(value_for_variable)
                else:
                    print(f"Error: {variable_to_search} is not a dictionary.")
        
        return values_for_variable
    
    def plot_and_save_chart(self, chart_data, chart_type, simulation_id, product_instance, 
                          result_simulations, title, description):
        """Plot and save chart, returning base64 encoded image"""
        plt.figure(figsize=(10, 6))
        
        # Generate chart based on type
        if chart_type == 'linedemand':
            self._plot_line_demand_chart(chart_data)
        elif chart_type == 'line':
            self._plot_line_chart(chart_data)
        elif chart_type == 'bar':
            self._plot_bar_chart(chart_data)
        elif chart_type == 'scatter':
            self._plot_scatter_chart(chart_data)
        elif chart_type == 'histogram':
            self._plot_histogram_chart(chart_data)
        elif chart_type == 'barApilate':
            self._plot_stacked_bar_chart(chart_data)
        else:
            plt.close()
            return None
        
        # Configure plot appearance
        self._configure_plot(chart_data, title, description, product_instance)
        
        # Save as base64
        image_data = self._save_plot_as_base64()
        
        # Save to database
        self._save_chart_to_database(
            title, chart_type, chart_data, product_instance, 
            result_simulations, image_data
        )
        
        plt.tight_layout()
        plt.close()
        
        return image_data
    
    def _plot_line_demand_chart(self, chart_data):
        """Plot line chart with regression and trend analysis"""
        labels = chart_data['labels']
        values = chart_data['datasets'][0]['values']
        label = chart_data['datasets'][0]['label']
        
        # Calculate regression line
        reg_line = np.polyfit(labels, values, 1)
        regression_values = np.polyval(reg_line, labels)
        
        # Plot regression line
        plt.plot(labels, regression_values, 
                label=f'{label} Regression Line', linestyle='--')
        
        # Plot demand line
        sns.lineplot(x=labels, y=values, marker='o', 
                    label='Demanda Simulada', palette='viridis')
        
        plt.grid(True)
        
        # Calculate and plot trend line
        coefficients = np.polyfit(labels, values, 1)
        polynomial = np.poly1d(coefficients)
        trendline_values = polynomial(labels)
        plt.plot(labels, trendline_values, 
                label=f'Línea de tendencia: {coefficients[0]:.2f}x + {coefficients[1]:.2f}', 
                linestyle='--')
        
        # Fill area between demand and trend lines
        plt.fill_between(labels, values, trendline_values, 
                        color='skyblue', alpha=0.3)
    
    def _plot_line_chart(self, chart_data):
        """Plot standard line chart"""
        labels = chart_data['labels']
        datasets = chart_data['datasets']
        custom_palette = sns.color_palette("husl", len(datasets))
        
        for i, dataset in enumerate(datasets):
            plt.plot(labels, dataset['values'], label=dataset['label'], 
                    color=custom_palette[i], linewidth=2)
            plt.fill_between(labels, dataset['values'], 
                           alpha=0.3, color=custom_palette[i])
        
        plt.grid(True)
    
    def _plot_bar_chart(self, chart_data):
        """Plot bar chart"""
        num_colors = len(chart_data['datasets'])
        color_palette = self._generate_random_color_palette(num_colors)
        
        for i, variable_data in enumerate(chart_data['datasets']):
            label = variable_data.get('label', f'Default Label {i+1}')
            values = variable_data['values']
            color = color_palette[i]
            sns.barplot(x=chart_data['labels'], y=values, 
                       label=label, color=color, alpha=0.7)
        
        plt.grid(True)
        plt.legend(loc='upper right')
    
    def _plot_scatter_chart(self, chart_data):
        """Plot scatter chart with regression lines"""
        for i, variable_data in enumerate(chart_data['datasets']):
            label = variable_data['label']
            values = variable_data['values']
            color = sns.color_palette('Set3', len(chart_data['labels']))[i]
            
            sns.scatterplot(x=chart_data['labels'], y=values, 
                          label=label, color=color, marker='o')
            
            # Add regression line
            reg_line = np.polyfit(chart_data['labels'], values, 1)
            plt.plot(chart_data['labels'], 
                    np.polyval(reg_line, chart_data['labels']), 
                    label=f'{label} Regression Line', linestyle='--')
    
    def _plot_histogram_chart(self, chart_data):
        """Plot histogram with statistics"""
        for i, variable_data in enumerate(chart_data['datasets']):
            values = variable_data['values']
            color = sns.color_palette('Set3', len(chart_data['labels']))[i]
            
            sns.histplot(values, bins=20, color=color, alpha=0.7, kde=True)
            
            mean_value = np.mean(values)
            plt.axvline(x=mean_value, color='red', linestyle='--', 
                       label=f'Mean: {mean_value:.2f}')
            
            stats_text = f'Mean: {mean_value:.2f}\nStd Dev: {np.std(values):.2f}'
            plt.text(0.05, 0.95, stats_text, transform=plt.gca().transAxes, 
                    fontsize=8, verticalalignment='top', 
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    def _plot_stacked_bar_chart(self, chart_data):
        """Plot stacked bar chart"""
        num_groups = len(chart_data['labels'])
        x = np.arange(num_groups)
        bottom = np.zeros(num_groups)
        
        for i, dataset in enumerate(chart_data['datasets']):
            values = dataset['values']
            label = dataset['label']
            color = sns.color_palette('Set1')[i]
            
            plt.bar(x, values, label=label, color=color, 
                   alpha=0.7, bottom=bottom)
            bottom += values
    
    def _configure_plot(self, chart_data, title, description, product_instance):
        """Configure plot appearance and labels"""
        plt.subplots_adjust(bottom=0.2)
        plt.xticks(chart_data['labels'], rotation=90, ha='center')
        plt.xlabel(chart_data['x_label'])
        plt.ylabel(chart_data['y_label'])
        plt.legend()
        
        # Add variable names to title
        variable_names = [dataset['label'] for dataset in chart_data['datasets']]
        title += f' ({", ".join(variable_names)})'
        plt.title(title)
        
        # Add description at bottom
        plt.figtext(0.5, 0.01, description, ha='center', va='center')
    
    def _save_plot_as_base64(self):
        """Save current plot as base64 encoded string"""
        with BytesIO() as buffer:
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def _save_chart_to_database(self, title, chart_type, chart_data, product_instance, 
                              result_simulations, image_data):
        """Save chart information to database"""
        chart = Chart.objects.filter(
            fk_product_id=product_instance, 
            chart_type=chart_type
        ).first()
        
        if chart:
            chart.title = title
            chart.chart_data = chart_data
        else:
            chart = Chart.objects.create(
                title=title,
                chart_type=chart_type,
                chart_data=chart_data,
                fk_product=result_simulations[0].fk_simulation.fk_questionary_result.fk_questionary.fk_product,
            )
        
        chart.save_chart_image(image_data)
        chart.save()
    
    def _generate_random_color_palette(self, num_colors):
        """Generate random color palette"""
        return sns.color_palette("husl", num_colors)