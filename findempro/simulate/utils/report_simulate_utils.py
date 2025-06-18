import numpy as np
import scipy.stats
class EndogenousVariablesReporter:
    """Generate comprehensive reports for endogenous variables"""
    
    def __init__(self, simulation_instance, results_simulation, all_variables_extracted):
        self.simulation = simulation_instance
        self.results = results_simulation
        self.variables_data = all_variables_extracted
    
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        report = {
            'simulation_info': self._get_simulation_info(),
            'variables_overview': self._get_variables_overview(),
            'performance_metrics': self._get_performance_metrics(),
            'trends_analysis': self._get_trends_analysis(),
            'recommendations': self._get_recommendations()
        }
        return report
    
    def _get_simulation_info(self):
        """Get basic simulation information"""
        return {
            'simulation_id': self.simulation.id,
            'start_date': self.simulation.date_created,
            'duration_days': len(self.variables_data),
            'business_name': self.simulation.fk_questionary_result.fk_questionary.fk_product.fk_business.name,
            'product_name': self.simulation.fk_questionary_result.fk_questionary.fk_product.name
        }
    
    def _get_variables_overview(self):
        """Get overview of all variables"""
        overview = {
            'total_variables': 0,
            'financial_variables': 0,
            'operational_variables': 0,
            'quality_variables': 0,
            'variables_list': []
        }
        
        if not self.variables_data:
            return overview
        
        # Get all unique variables
        all_vars = set()
        for day_data in self.variables_data:
            all_vars.update(day_data.keys())
        
        # Remove non-variable keys
        exclude_keys = {'day', 'date', 'demand_mean', 'demand_std'}
        variables = all_vars - exclude_keys
        
        overview['total_variables'] = len(variables)
        
        # Categorize variables
        financial_vars = {'IT', 'GT', 'TG', 'NR', 'PVP', 'CFD', 'CVU'}
        quality_vars = {'NSC', 'EOG'}
        
        for var in variables:
            if var in financial_vars:
                overview['financial_variables'] += 1
                category = 'financial'
            elif var in quality_vars:
                overview['quality_variables'] += 1
                category = 'quality'
            else:
                overview['operational_variables'] += 1
                category = 'operational'
            
            overview['variables_list'].append({
                'name': var,
                'category': category,
                'description': self._get_variable_description(var)
            })
        
        return overview
    
    def _get_performance_metrics(self):
        """Calculate key performance metrics"""
        metrics = {
            'average_profitability': 0,
            'average_satisfaction': 0,
            'average_efficiency': 0,
            'total_revenue': 0,
            'total_profit': 0,
            'profit_margin': 0
        }
        
        if not self.variables_data:
            return metrics
        
        # Calculate averages
        profitability_values = []
        satisfaction_values = []
        efficiency_values = []
        revenue_values = []
        profit_values = []
        
        for day_data in self.variables_data:
            if 'NR' in day_data and day_data['NR'] is not None:
                profitability_values.append(float(day_data['NR']))
            
            if 'NSC' in day_data and day_data['NSC'] is not None:
                satisfaction_values.append(float(day_data['NSC']))
            
            if 'EOG' in day_data and day_data['EOG'] is not None:
                efficiency_values.append(float(day_data['EOG']))
            
            if 'IT' in day_data and day_data['IT'] is not None:
                revenue_values.append(float(day_data['IT']))
            
            if 'GT' in day_data and day_data['GT'] is not None:
                profit_values.append(float(day_data['GT']))
        
        # Calculate metrics
        if profitability_values:
            metrics['average_profitability'] = np.mean(profitability_values) * 100
        
        if satisfaction_values:
            metrics['average_satisfaction'] = np.mean(satisfaction_values) * 100
        
        if efficiency_values:
            metrics['average_efficiency'] = np.mean(efficiency_values) * 100
        
        if revenue_values:
            metrics['total_revenue'] = sum(revenue_values)
        
        if profit_values:
            metrics['total_profit'] = sum(profit_values)
        
        if metrics['total_revenue'] > 0:
            metrics['profit_margin'] = (metrics['total_profit'] / metrics['total_revenue']) * 100
        
        return metrics
    
    def _get_trends_analysis(self):
        """Analyze trends for key variables"""
        trends = {}
        
        key_variables = ['IT', 'GT', 'TG', 'TPV', 'NSC', 'EOG', 'NR']
        
        for var in key_variables:
            trend_data = self._analyze_variable_trend(var)
            if trend_data:
                trends[var] = trend_data
        
        return trends
    
    def _analyze_variable_trend(self, variable):
        """Analyze trend for a specific variable"""
        values = []
        
        for day_data in self.variables_data:
            if variable in day_data and day_data[variable] is not None:
                values.append(float(day_data[variable]))
        
        if len(values) < 3:
            return None
        
        # Calculate trend
        x = np.arange(len(values))
        slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(x, values)
        
        trend_direction = 'stable'
        if slope > 0.01:
            trend_direction = 'increasing'
        elif slope < -0.01:
            trend_direction = 'decreasing'
        
        return {
            'direction': trend_direction,
            'slope': slope,
            'correlation': r_value,
            'significance': p_value,
            'start_value': values[0],
            'end_value': values[-1],
            'change_percentage': ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0,
            'volatility': np.std(values),
            'mean': np.mean(values),
            'min': min(values),
            'max': max(values)
        }
    
    def _get_recommendations(self):
        """Generate recommendations based on analysis"""
        recommendations = []
        metrics = self._get_performance_metrics()
        
        # Profitability recommendations
        if metrics['average_profitability'] < 10:
            recommendations.append({
                'type': 'warning',
                'category': 'Rentabilidad',
                'message': 'La rentabilidad promedio está por debajo del 10%. Considere revisar la estructura de costos.',
                'priority': 'high'
            })
        elif metrics['average_profitability'] > 30:
            recommendations.append({
                'type': 'success',
                'category': 'Rentabilidad',
                'message': 'Excelente rentabilidad. Mantenga las estrategias actuales.',
                'priority': 'low'
            })
        
        # Satisfaction recommendations
        if metrics['average_satisfaction'] < 80:
            recommendations.append({
                'type': 'warning',
                'category': 'Satisfacción',
                'message': 'La satisfacción del cliente está por debajo del 80%. Implemente mejoras en el servicio.',
                'priority': 'high'
            })
        
        # Efficiency recommendations
        if metrics['average_efficiency'] < 70:
            recommendations.append({
                'type': 'info',
                'category': 'Eficiencia',
                'message': 'La eficiencia operativa puede mejorarse. Analice los procesos actuales.',
                'priority': 'medium'
            })
        
        return recommendations
    
    def _get_variable_description(self, variable):
        """Get description for a variable"""
        descriptions = {
            'IT': 'Ingresos Totales generados en el período',
            'GT': 'Ganancia Total obtenida después de gastos',
            'TG': 'Total de Gastos incurridos',
            'TPV': 'Total de Productos Vendidos',
            'NSC': 'Nivel de Satisfacción del Cliente',
            'EOG': 'Eficiencia Operativa General',
            'NR': 'Nivel de Rentabilidad',
            'PVP': 'Precio de Venta al Público',
            'CFD': 'Costo Fijo Diario',
            'CVU': 'Costo Variable Unitario',
            'DPH': 'Demanda Promedio Histórica',
            'CPROD': 'Capacidad de Producción',
            'NEPP': 'Número de Empleados en Producción'
        }
        return descriptions.get(variable, f'Variable {variable} del modelo')