# services/validation_service.py
"""
Enhanced validation service for simulation results.
Compares simulated values with real data on a daily basis.
"""
import logging
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta

from django.db.models import Avg, StdDev, Min, Max, Count
from simulate.models import ResultSimulation, Simulation
from questionary.models import Answer

logger = logging.getLogger(__name__)


class SimulationValidationService:
    """Service for validating simulation results against real data"""
    
    def __init__(self):
        self.tolerance_thresholds = {
            'strict': 0.05,      # 5% tolerance
            'normal': 0.10,      # 10% tolerance
            'flexible': 0.20,    # 20% tolerance
            'loose': 0.30        # 30% tolerance
        }
        
        # Variable-specific tolerances
        self.variable_tolerances = {
            # Financial variables need strict validation
            'IT': 'normal',      # Total income
            'GT': 'flexible',    # Total profit (more variable)
            'GO': 'normal',      # Operating expenses
            'TG': 'normal',      # Total expenses
            
            # Production variables
            'QPL': 'normal',     # Production quantity
            'CPROD': 'strict',   # Production capacity (should be stable)
            'TPPRO': 'normal',   # Total production
            'FU': 'flexible',    # Utilization factor
            
            # Sales variables
            'TPV': 'normal',     # Total products sold
            'TCAE': 'normal',    # Total customers served
            'VPC': 'flexible',   # Sales per customer
            'NSC': 'normal',     # Service level
            
            # Inventory variables
            'IPF': 'flexible',   # Final product inventory
            'II': 'flexible',    # Input inventory
            'RTI': 'loose',      # Inventory turnover
            
            # HR and efficiency
            'PE': 'flexible',    # Employee productivity
            'HO': 'loose',       # Idle hours
            
            # Demand variables (special handling)
            'DPH': 'special',    # Daily demand - compared differently
            'DE': 'flexible',    # Expected demand
            'DI': 'loose',       # Unmet demand
        }
    
    def validate_simulation(self, simulation_id: int) -> Dict[str, Any]:
        """
        Validate complete simulation results against real data.
        
        Returns:
            Dictionary with validation results, alerts, and summary
        """
        try:
            simulation = Simulation.objects.get(id=simulation_id)
            results = ResultSimulation.objects.filter(
                fk_simulation=simulation
            ).order_by('date')
            
            if not results.exists():
                return self._create_empty_validation_result()
            
            # Get real values from questionnaire
            real_values = self._extract_real_values(simulation)
            
            # Get historical demand for baseline
            demand_history = self._parse_demand_history(simulation.demand_history)
            hist_mean = float(np.mean(demand_history)) if demand_history else 0
            hist_std = float(np.std(demand_history)) if demand_history else 0
            
            # Validate each day
            daily_validations = []
            alerts = []
            
            for day_idx, result in enumerate(results):
                day_validation = self._validate_single_day(
                    result, real_values, hist_mean, hist_std, day_idx
                )
                daily_validations.append(day_validation)
                alerts.extend(day_validation['alerts'])
            
            # Aggregate validation results
            summary = self._generate_validation_summary(daily_validations, alerts)
            
            # Generate recommendations
            recommendations = self._generate_validation_recommendations(summary, alerts)
            
            return {
                'daily_validations': daily_validations,
                'alerts': alerts,
                'summary': summary,
                'recommendations': recommendations,
                'is_valid': summary['overall_accuracy'] >= 0.7,  # 70% threshold
                'real_values': real_values
            }
            
        except Exception as e:
            logger.error(f"Error validating simulation {simulation_id}: {str(e)}")
            return self._create_empty_validation_result()
    
    def validate_daily_results(self, 
                             simulated_values: Dict[str, float],
                             real_values: Dict[str, float],
                             day_index: int = 0) -> Dict[str, Any]:
        """
        Validate a single day's results against real values.
        
        Args:
            simulated_values: Dictionary of simulated variable values
            real_values: Dictionary of real/expected values
            day_index: Day number in simulation
            
        Returns:
            Validation results for the day
        """
        validations = {}
        total_variables = 0
        accurate_count = 0
        
        for var_name, sim_value in simulated_values.items():
            # Skip metadata and internal variables
            if var_name.startswith('_') or var_name not in self.variable_tolerances:
                continue
            
            # Check if we have a real value to compare
            if var_name not in real_values:
                continue
            
            real_value = real_values[var_name]
            tolerance_type = self.variable_tolerances.get(var_name, 'normal')
            
            # Special handling for demand variables
            if tolerance_type == 'special':
                validation = self._validate_demand_variable(
                    var_name, sim_value, real_value, day_index
                )
            else:
                validation = self._validate_single_variable(
                    var_name, sim_value, real_value, tolerance_type
                )
            
            validations[var_name] = validation
            total_variables += 1
            
            if validation['is_accurate']:
                accurate_count += 1
        
        accuracy_rate = accurate_count / total_variables if total_variables > 0 else 0
        
        return {
            'day': day_index + 1,
            'validations': validations,
            'total_variables': total_variables,
            'accurate_count': accurate_count,
            'accuracy_rate': accuracy_rate,
            'status': self._get_day_status(accuracy_rate)
        }
    
    def _validate_single_day(self, result: ResultSimulation,
                           real_values: Dict[str, float],
                           hist_mean: float,
                           hist_std: float,
                           day_idx: int) -> Dict[str, Any]:
        """Validate a single day's simulation results"""
        variables = result.variables
        alerts = []
        validations = {}
        
        # Validate demand first (special case)
        demand = float(result.demand_mean)
        demand_validation = self._validate_demand_prediction(
            demand, hist_mean, hist_std, day_idx
        )
        validations['DPH'] = demand_validation
        
        if demand_validation['severity'] == 'ERROR':
            alerts.append({
                'day': result.date,
                'type': 'DEMAND_DEVIATION',
                'severity': 'ERROR',
                'message': f'Demand {demand:.2f} deviates significantly from expected range',
                'value': demand,
                'expected_range': demand_validation['expected_range']
            })
        
        # Validate other variables
        for var_name, var_value in variables.items():
            if var_name.startswith('_') or var_name == 'DPH':
                continue
            
            if var_name in real_values and var_name in self.variable_tolerances:
                validation = self._validate_single_variable(
                    var_name, var_value, real_values[var_name],
                    self.variable_tolerances[var_name]
                )
                validations[var_name] = validation
                
                if not validation['is_accurate'] and validation['error_rate'] > 0.3:
                    alerts.append({
                        'day': result.date,
                        'type': f'{var_name}_DEVIATION',
                        'severity': 'WARNING',
                        'message': f'{var_name} value {var_value:.2f} differs from expected {real_values[var_name]:.2f}',
                        'error_rate': validation['error_rate']
                    })
        
        # Calculate day accuracy
        accurate_count = sum(1 for v in validations.values() if v.get('is_accurate', False))
        total_count = len(validations)
        accuracy_rate = accurate_count / total_count if total_count > 0 else 0
        
        return {
            'date': result.date,
            'day_number': day_idx + 1,
            'validations': validations,
            'alerts': alerts,
            'accuracy_rate': accuracy_rate,
            'status': self._get_day_status(accuracy_rate)
        }
    
    def _validate_single_variable(self, var_name: str,
                                simulated: float,
                                real: float,
                                tolerance_type: str) -> Dict[str, Any]:
        """Validate a single variable value"""
        if real == 0:
            error_rate = 1.0 if simulated != 0 else 0.0
        else:
            error_rate = abs(simulated - real) / abs(real)
        
        tolerance = self.tolerance_thresholds.get(tolerance_type, 0.1)
        is_accurate = error_rate <= tolerance
        
        return {
            'simulated': simulated,
            'real': real,
            'error_rate': error_rate,
            'tolerance': tolerance,
            'is_accurate': is_accurate,
            'deviation': simulated - real,
            'status': 'PASS' if is_accurate else 'FAIL'
        }
    
    def _validate_demand_variable(self, var_name: str,
                                simulated: float,
                                real: float,
                                day_index: int) -> Dict[str, Any]:
        """Special validation for demand variables"""
        # For DPH (daily demand), we expect variation but within reasonable bounds
        if var_name == 'DPH':
            # Allow more variation in early days, stabilizing over time
            base_tolerance = 0.3  # 30% base
            time_factor = max(0.1, 1 - (day_index / 30))  # Decreases over time
            tolerance = base_tolerance * (1 + time_factor)
        else:
            tolerance = self.tolerance_thresholds['flexible']
        
        error_rate = abs(simulated - real) / abs(real) if real != 0 else 0
        is_accurate = error_rate <= tolerance
        
        return {
            'simulated': simulated,
            'real': real,
            'error_rate': error_rate,
            'tolerance': tolerance,
            'is_accurate': is_accurate,
            'deviation': simulated - real,
            'status': 'PASS' if is_accurate else 'FAIL',
            'note': f'Day {day_index + 1} demand validation'
        }
    
    def _validate_demand_prediction(self, demand: float,
                                  hist_mean: float,
                                  hist_std: float,
                                  day_idx: int) -> Dict[str, Any]:
        """Validate demand prediction against historical patterns"""
        # Expected range based on historical data
        lower_bound = hist_mean - 2 * hist_std
        upper_bound = hist_mean + 2 * hist_std
        
        # Allow wider range in early days
        if day_idx < 7:
            expansion_factor = 1.5 - (day_idx * 0.07)  # 1.5x to 1x over first week
            range_expansion = hist_std * (expansion_factor - 1)
            lower_bound -= range_expansion
            upper_bound += range_expansion
        
        is_within_range = lower_bound <= demand <= upper_bound
        
        if is_within_range:
            severity = 'OK'
        elif hist_mean * 0.5 <= demand <= hist_mean * 1.5:
            severity = 'WARNING'
        else:
            severity = 'ERROR'
        
        deviation_from_mean = abs(demand - hist_mean) / hist_mean if hist_mean > 0 else 0
        
        return {
            'value': demand,
            'historical_mean': hist_mean,
            'historical_std': hist_std,
            'expected_range': (lower_bound, upper_bound),
            'is_within_range': is_within_range,
            'severity': severity,
            'deviation_rate': deviation_from_mean,
            'is_accurate': severity != 'ERROR'
        }
    
    def _extract_real_values(self, simulation: Simulation) -> Dict[str, float]:
        """Extract real values from questionnaire and business data"""
        real_values = {}
        
        try:
            # Get answers from questionnaire
            answers = Answer.objects.filter(
                fk_questionary_result=simulation.fk_questionary_result
            ).select_related('fk_question__fk_variable')
            
            for answer in answers:
                if answer.fk_question.fk_variable:
                    var_initials = answer.fk_question.fk_variable.initials
                    if var_initials and answer.answer:
                        try:
                            # Parse numeric value
                            value = self._parse_numeric_value(answer.answer)
                            if value is not None:
                                real_values[var_initials] = value
                        except:
                            continue
            
            # Calculate derived values
            real_values = self._calculate_derived_real_values(real_values)
            
            logger.info(f"Extracted {len(real_values)} real values for validation")
            
        except Exception as e:
            logger.error(f"Error extracting real values: {str(e)}")
        
        return real_values
    
    def _parse_numeric_value(self, value: Any) -> Optional[float]:
        """Parse a value to float, handling various formats"""
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Remove common formatting
            import re
            cleaned = re.sub(r'[^\d.-]', '', value)
            if cleaned:
                try:
                    return float(cleaned)
                except:
                    pass
        
        if isinstance(value, list) and len(value) > 0:
            # For lists, return average
            try:
                return float(np.mean([float(x) for x in value if x is not None]))
            except:
                pass
        
        return None
    
    def _calculate_derived_real_values(self, real_values: Dict[str, float]) -> Dict[str, float]:
        """Calculate derived values that aren't directly in questionnaire"""
        # Total income
        if 'IT' not in real_values and all(k in real_values for k in ['TPV', 'PVP']):
            real_values['IT'] = real_values['TPV'] * real_values['PVP']
        
        # Total expenses
        if 'TG' not in real_values and 'GO' in real_values:
            # Estimate general expenses as 20% of operating
            real_values['TG'] = real_values['GO'] * 1.2
        
        # Total profit
        if 'GT' not in real_values and all(k in real_values for k in ['IT', 'TG']):
            real_values['GT'] = real_values['IT'] - real_values['TG']
        
        # Production capacity
        if 'CPROD' not in real_values and 'QPL' in real_values:
            real_values['CPROD'] = real_values['QPL'] * 1.2  # 20% headroom
        
        # Customers served
        if 'TCAE' not in real_values and 'CPD' in real_values:
            real_values['TCAE'] = real_values['CPD'] * 0.95  # 95% efficiency
        
        return real_values
    
    def _parse_demand_history(self, demand_history) -> List[float]:
        """Parse demand history data"""
        try:
            import json
            if isinstance(demand_history, str):
                data = json.loads(demand_history)
            else:
                data = demand_history
            
            if isinstance(data, list):
                return [float(x) for x in data if x is not None]
            
        except Exception as e:
            logger.error(f"Error parsing demand history: {str(e)}")
        
        return []
    
    def _generate_validation_summary(self, 
                                   daily_validations: List[Dict],
                                   alerts: List[Dict]) -> Dict[str, Any]:
        """Generate summary of validation results"""
        total_days = len(daily_validations)
        
        # Calculate overall metrics
        accuracy_rates = [d['accuracy_rate'] for d in daily_validations]
        overall_accuracy = np.mean(accuracy_rates) if accuracy_rates else 0
        
        # Count days by status
        status_counts = {
            'EXCELLENT': sum(1 for d in daily_validations if d['status'] == 'EXCELLENT'),
            'GOOD': sum(1 for d in daily_validations if d['status'] == 'GOOD'),
            'FAIR': sum(1 for d in daily_validations if d['status'] == 'FAIR'),
            'POOR': sum(1 for d in daily_validations if d['status'] == 'POOR')
        }
        
        # Analyze alerts
        alert_counts = {}
        for alert in alerts:
            alert_type = alert['type']
            alert_counts[alert_type] = alert_counts.get(alert_type, 0) + 1
        
        # Variable-specific accuracy
        variable_accuracy = {}
        for day in daily_validations:
            for var_name, validation in day['validations'].items():
                if var_name not in variable_accuracy:
                    variable_accuracy[var_name] = []
                variable_accuracy[var_name].append(validation.get('is_accurate', False))
        
        variable_summary = {}
        for var_name, accuracies in variable_accuracy.items():
            variable_summary[var_name] = {
                'accuracy_rate': sum(accuracies) / len(accuracies) if accuracies else 0,
                'total_validations': len(accuracies),
                'accurate_count': sum(accuracies)
            }
        
        return {
            'total_days': total_days,
            'overall_accuracy': overall_accuracy,
            'accuracy_std': np.std(accuracy_rates) if len(accuracy_rates) > 1 else 0,
            'status_distribution': status_counts,
            'alert_summary': alert_counts,
            'variable_performance': variable_summary,
            'success_rate': (status_counts['EXCELLENT'] + status_counts['GOOD']) / total_days if total_days > 0 else 0
        }
    
    def _get_day_status(self, accuracy_rate: float) -> str:
        """Determine day status based on accuracy rate"""
        if accuracy_rate >= 0.9:
            return 'EXCELLENT'
        elif accuracy_rate >= 0.75:
            return 'GOOD'
        elif accuracy_rate >= 0.6:
            return 'FAIR'
        else:
            return 'POOR'
    
    def _generate_validation_recommendations(self, 
                                           summary: Dict[str, Any],
                                           alerts: List[Dict]) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        # Overall accuracy recommendations
        if summary['overall_accuracy'] < 0.7:
            recommendations.append(
                "La precisión general del modelo es baja. Considere revisar los parámetros "
                "de distribución de probabilidad o los datos de entrada."
            )
        elif summary['overall_accuracy'] > 0.9:
            recommendations.append(
                "El modelo muestra excelente precisión. Los resultados son altamente confiables."
            )
        
        # Variable-specific recommendations
        poor_variables = []
        for var_name, perf in summary['variable_performance'].items():
            if perf['accuracy_rate'] < 0.6:
                poor_variables.append(var_name)
        
        if poor_variables:
            recommendations.append(
                f"Las siguientes variables muestran baja precisión y requieren revisión: "
                f"{', '.join(poor_variables[:5])}"
            )
        
        # Alert-based recommendations
        demand_alerts = sum(1 for a in alerts if 'DEMAND' in a['type'])
        if demand_alerts > len(alerts) * 0.3:
            recommendations.append(
                "Se detectaron múltiples desviaciones en la demanda. "
                "Verifique la distribución de probabilidad seleccionada."
            )
        
        # Stability recommendations
        if summary['accuracy_std'] > 0.2:
            recommendations.append(
                "La precisión varía significativamente entre días. "
                "El modelo podría beneficiarse de ajustes en los factores de estabilización."
            )
        
        return recommendations
    
    def _create_empty_validation_result(self) -> Dict[str, Any]:
        """Create empty validation result structure"""
        return {
            'daily_validations': [],
            'alerts': [],
            'summary': {
                'total_days': 0,
                'overall_accuracy': 0,
                'accuracy_std': 0,
                'status_distribution': {},
                'alert_summary': {},
                'variable_performance': {},
                'success_rate': 0
            },
            'recommendations': ["No se encontraron resultados para validar"],
            'is_valid': False,
            'real_values': {}
        }
    
    def compare_simulations(self, 
                          simulation_ids: List[int],
                          variables: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Compare multiple simulations to identify best performing parameters.
        
        Args:
            simulation_ids: List of simulation IDs to compare
            variables: Optional list of variables to focus on
            
        Returns:
            Comparison results and recommendations
        """
        if not simulation_ids:
            return {'error': 'No simulations to compare'}
        
        comparison_data = []
        
        for sim_id in simulation_ids:
            validation = self.validate_simulation(sim_id)
            
            if validation['is_valid']:
                comparison_data.append({
                    'simulation_id': sim_id,
                    'overall_accuracy': validation['summary']['overall_accuracy'],
                    'success_rate': validation['summary']['success_rate'],
                    'variable_performance': validation['summary']['variable_performance']
                })
        
        if not comparison_data:
            return {'error': 'No valid simulations found'}
        
        # Find best performing simulation
        best_sim = max(comparison_data, key=lambda x: x['overall_accuracy'])
        
        # Identify best practices
        best_practices = self._identify_best_practices(comparison_data, variables)
        
        return {
            'best_simulation': best_sim,
            'all_comparisons': comparison_data,
            'best_practices': best_practices,
            'recommendation': f"Simulation {best_sim['simulation_id']} shows best overall performance"
        }
    
    def _identify_best_practices(self, 
                               comparison_data: List[Dict],
                               focus_variables: Optional[List[str]] = None) -> Dict[str, Any]:
        """Identify best practices from multiple simulations"""
        best_practices = {}
        
        # Get all variables
        all_variables = set()
        for comp in comparison_data:
            all_variables.update(comp['variable_performance'].keys())
        
        # Filter if specific variables requested
        if focus_variables:
            all_variables = all_variables.intersection(set(focus_variables))
        
        # Find best performer for each variable
        for var in all_variables:
            best_accuracy = 0
            best_sim_id = None
            
            for comp in comparison_data:
                var_perf = comp['variable_performance'].get(var, {})
                accuracy = var_perf.get('accuracy_rate', 0)
                
                if accuracy > best_accuracy:
                    best_accuracy = accuracy
                    best_sim_id = comp['simulation_id']
            
            if best_sim_id:
                best_practices[var] = {
                    'best_simulation': best_sim_id,
                    'accuracy': best_accuracy
                }
        
        return best_practices