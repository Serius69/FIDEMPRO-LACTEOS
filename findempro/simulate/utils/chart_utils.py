import logging
from functools import lru_cache
from variable.models import Variable

logger = logging.getLogger(__name__)

class ChartUtils:
    iniciales_a_buscar = [
        'CTR', 'CTAI', 'TPV', 'TPPRO', 'DI', 'VPC', 'IT', 'GT', 'TCA', 
        'NR', 'GO', 'GG', 'CTTL', 'CPP', 'CPV', 'CPI', 'CPMO', 
        'CUP', 'TG', 'IB', 'MB', 'RI', 'RTI', 'RTC', 'PE', 
        'HO', 'CHO', 'CA'
    ]

    @lru_cache(maxsize=128)
    def _get_variable_mapping(self):
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

    def _extract_variables_from_results(self, results_simulation):
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

    def _calculate_cumulative_totals(self, results_simulation):
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

    def _prepare_variables_for_graphing(self, results_simulation):
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

    def _create_demand_chart_data(self, result_simulations, historical_demand=None):
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

    def _get_chart_configurations(self, variables_to_graph):
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