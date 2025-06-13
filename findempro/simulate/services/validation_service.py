import json
import numpy as np
from typing import Counter
from simulate.models import ResultSimulation, Simulation

class SimulationValidationService:
    """Service for validating simulation results"""
    
    def __init__(self):
        self.thresholds = {
            'demand_deviation': 0.5,  # 50% max deviation from historical
            'profit_margin_min': -0.3,  # -30% minimum margin
            'profit_margin_max': 0.6,   # 60% maximum margin
            'production_utilization_min': 0.3,  # 30% minimum utilization
            'inventory_turnover_min': 2,  # Minimum 2x turnover per month
        }
    
    def validate_simulation(self, simulation_id):
        """Validate complete simulation results"""
        simulation = Simulation.objects.get(id=simulation_id)
        results = ResultSimulation.objects.filter(fk_simulation=simulation)
        
        # Get historical data
        demand_history = [float(x) for x in json.loads(simulation.demand_history)]
        hist_mean = float(np.mean(demand_history))
        hist_std = float(np.std(demand_history))
        
        alerts = []
        
        for result in results:
            day_alerts = self._validate_day_result(result, hist_mean, hist_std)
            alerts.extend(day_alerts)
        
        # Aggregate validation
        summary = self._generate_validation_summary(results, alerts)
        
        return {
            'alerts': alerts,
            'summary': summary,
            'is_valid': len([a for a in alerts if a['severity'] == 'ERROR']) == 0
        }
    
    def _validate_day_result(self, result, hist_mean, hist_std):
        """Validate single day result"""
        alerts = []
        variables = result.variables
        
        # Check demand prediction
        demand = float(result.demand_mean)
        deviation = abs(demand - hist_mean) / hist_mean if hist_mean > 0 else 0
        
        if deviation > self.thresholds['demand_deviation']:
            alerts.append({
                'day': result.date,
                'type': 'DEMAND_DEVIATION',
                'severity': 'ERROR',
                'message': f'Demand {demand:.2f} deviates {deviation:.2%} from historical mean',
                'value': demand,
                'expected_range': (hist_mean - 2*hist_std, hist_mean + 2*hist_std)
            })
        
        # Check profit margins
        it = float(variables.get('IT', 0))
        gt = float(variables.get('GT', 0))
        if it > 0:
            margin = gt / it
            if margin < self.thresholds['profit_margin_min']:
                alerts.append({
                    'day': result.date,
                    'type': 'LOW_PROFIT_MARGIN',
                    'severity': 'WARNING',
                    'message': f'Profit margin {margin:.2%} below threshold',
                    'value': margin,
                    'threshold': self.thresholds['profit_margin_min']
                })
        
        # Check production utilization
        tpv = float(variables.get('TPV', 0))
        cprod = float(variables.get('CPROD', 1))
        utilization = tpv / cprod if cprod > 0 else 0
        
        if utilization < self.thresholds['production_utilization_min']:
            alerts.append({
                'day': result.date,
                'type': 'LOW_UTILIZATION',
                'severity': 'WARNING',
                'message': f'Production utilization {utilization:.2%} below threshold',
                'value': utilization,
                'threshold': self.thresholds['production_utilization_min']
            })
        
        return alerts
    
    def _generate_validation_summary(self, results, alerts):
        """Generate validation summary"""
        total_days = results.count()
        error_days = len(set(a['day'] for a in alerts if a['severity'] == 'ERROR'))
        warning_days = len(set(a['day'] for a in alerts if a['severity'] == 'WARNING'))
        
        # Calculate average metrics
        avg_demand = np.mean([r.demand_mean for r in results])
        avg_profit_margin = np.mean([
            r.variables.get('GT', 0) / r.variables.get('IT', 1) 
            for r in results if r.variables.get('IT', 0) > 0
        ])
        
        return {
            'total_days': total_days,
            'error_days': error_days,
            'warning_days': warning_days,
            'success_rate': (total_days - error_days) / total_days if total_days > 0 else 0,
            'average_demand': avg_demand,
            'average_profit_margin': avg_profit_margin,
            'alert_types': dict(Counter(a['type'] for a in alerts))
        }