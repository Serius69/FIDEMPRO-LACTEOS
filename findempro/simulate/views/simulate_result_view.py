# views/simulate_result_view.py
"""
Refactored simulation results view.
Focuses on daily comparisons and proper data visualization.
"""
import json
import logging
from typing import Dict, List, Any, Optional

import numpy as np
from django.views.generic import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from ..models import Simulation, ResultSimulation
from ..services.simulation_math import SimulationMathEngine
from ..services.validation_service import SimulationValidationService
from ..services.simulation_financial import SimulationFinancialAnalyzer
from ..utils.chart_utils import ChartGenerator
from ..utils.data_parsers import DataParser
from questionary.models import Answer
from variable.models import Variable, Equation
from finance.models import FinanceRecommendation, FinanceRecommendationSimulation

logger = logging.getLogger(__name__)


class SimulateResultView(LoginRequiredMixin, View):
    """Enhanced view for displaying simulation results with daily analysis"""
    
    def __init__(self):
        super().__init__()
        self.validation_service = SimulationValidationService()
        self.financial_analyzer = SimulationFinancialAnalyzer()
        self.chart_generator = ChartGenerator()
        self.data_parser = DataParser()
        self.math_engine = SimulationMathEngine()
    
    def get(self, request, simulation_id, *args, **kwargs):
        """Display results with proper service delegation"""
        # Check permissions
        if not self.result_service.user_can_view_simulation(request.user, simulation_id):
            messages.error(request, "No tiene permisos para ver esta simulación.")
            return redirect('simulate:simulate.show')
        
        # Get complete analysis from service
        analysis_data = self.result_service.get_complete_simulation_analysis(
            simulation_id=simulation_id,
            page=request.GET.get('page', 1)
        )
        
        if analysis_data.get('error'):
            messages.error(request, analysis_data['error'])
            return redirect('simulate:simulate.show')
        
        return render(request, 'simulate/simulate-result.html', analysis_data)
    
    def _get_simulation_with_relations(self, simulation_id: int) -> Simulation:
        """Get simulation with all necessary relations"""
        return get_object_or_404(
            Simulation.objects.select_related(
                'fk_questionary_result__fk_questionary__fk_product__fk_business',
                'fk_fdp'
            ).prefetch_related(
                'results',
                'fk_questionary_result__fk_question_result_answer__fk_question__fk_variable'
            ),
            pk=simulation_id
        )
    
    def _user_can_view_simulation(self, user, simulation: Simulation) -> bool:
        """Check if user has permission to view simulation"""
        business = simulation.fk_questionary_result.fk_questionary.fk_product.fk_business
        return business.fk_user == user
    
    def _get_paginated_results(self, simulation_id: int, page: int):
        """Get paginated simulation results"""
        results = ResultSimulation.objects.filter(
            is_active=True,
            fk_simulation_id=simulation_id
        ).order_by('date')
        
        paginator = Paginator(results, 50)  # 50 results per page
        
        try:
            return paginator.page(page)
        except PageNotAnInteger:
            return paginator.page(1)
        except EmptyPage:
            return paginator.page(paginator.num_pages)
    
    def _extract_historical_demand(self, simulation: Simulation) -> List[float]:
        """Extract historical demand data"""
        try:
            # Try from simulation first
            if simulation.demand_history:
                return self.data_parser.parse_demand_history(simulation.demand_history)
            
            # Try from questionnaire
            answers = simulation.fk_questionary_result.fk_question_result_answer.all()
            for answer in answers:
                if 'históric' in answer.fk_question.question.lower() and 'demanda' in answer.fk_question.question.lower():
                    if answer.answer:
                        return self.data_parser.parse_demand_history(answer.answer)
            
            return []
        except Exception as e:
            logger.error(f"Error extracting historical demand: {str(e)}")
            return []
    
    def _extract_real_values_from_questionnaire(self, simulation: Simulation) -> Dict[str, float]:
        """Extract real values from questionnaire for validation"""
        real_values = {}
        
        try:
            answers = simulation.fk_questionary_result.fk_question_result_answer.select_related(
                'fk_question__fk_variable'
            ).all()
            
            for answer in answers:
                if answer.fk_question.fk_variable and answer.answer:
                    var_initials = answer.fk_question.fk_variable.initials
                    value = self.data_parser.parse_numeric_answer(answer.answer)
                    
                    if value is not None:
                        real_values[var_initials] = value
            
            # Calculate derived values
            real_values = self._calculate_derived_real_values(real_values)
            
            logger.info(f"Extracted {len(real_values)} real values from questionnaire")
            
        except Exception as e:
            logger.error(f"Error extracting real values: {str(e)}")
        
        return real_values
    
    def _calculate_derived_real_values(self, real_values: Dict[str, float]) -> Dict[str, float]:
        """Calculate derived values that aren't directly in questionnaire"""
        # Total income
        if 'IT' not in real_values and all(k in real_values for k in ['TPV', 'PVP']):
            real_values['IT'] = real_values['TPV'] * real_values['PVP']
        
        # Total expenses
        if 'TG' not in real_values and 'GO' in real_values:
            real_values['TG'] = real_values['GO'] * 1.2  # Estimate
        
        # Total profit
        if 'GT' not in real_values and all(k in real_values for k in ['IT', 'TG']):
            real_values['GT'] = real_values['IT'] - real_values['TG']
        
        # Production capacity
        if 'CPROD' not in real_values and 'QPL' in real_values:
            real_values['CPROD'] = real_values['QPL'] * 1.2  # 20% headroom
        
        # Average demand
        if 'DPH' not in real_values and 'DH' in real_values:
            if isinstance(real_values['DH'], list):
                real_values['DPH'] = np.mean(real_values['DH'])
            else:
                real_values['DPH'] = real_values['DH']
        
        return real_values
    
    def _generate_daily_comparisons(self, results: List[ResultSimulation],
                                  real_values: Dict[str, float],
                                  historical_demand: List[float]) -> List[Dict[str, Any]]:
        """Generate daily comparison data for analysis"""
        comparisons = []
        
        for idx, result in enumerate(results):
            day_comparison = {
                'day': idx + 1,
                'date': result.date,
                'simulated_demand': float(result.demand_mean),
                'variables': {}
            }
            
            # Add historical demand if available
            if historical_demand and idx < len(historical_demand):
                day_comparison['historical_demand'] = historical_demand[idx]
                day_comparison['demand_deviation'] = (
                    (day_comparison['simulated_demand'] - historical_demand[idx]) / 
                    historical_demand[idx] * 100 if historical_demand[idx] > 0 else 0
                )
            
            # Compare key variables
            if hasattr(result, 'variables') and result.variables:
                for var_name, sim_value in result.variables.items():
                    if var_name in real_values and not var_name.startswith('_'):
                        real_value = real_values[var_name]
                        day_comparison['variables'][var_name] = {
                            'simulated': float(sim_value) if isinstance(sim_value, (int, float)) else 0,
                            'real': real_value,
                            'deviation': self._calculate_deviation(sim_value, real_value),
                            'status': self._determine_status(sim_value, real_value, var_name)
                        }
            
            comparisons.append(day_comparison)
        
        return comparisons
    
    def _calculate_deviation(self, simulated: Any, real: float) -> float:
        """Calculate percentage deviation"""
        try:
            sim_value = float(simulated) if isinstance(simulated, (int, float)) else 0
            if real == 0:
                return 100.0 if sim_value != 0 else 0.0
            return ((sim_value - real) / abs(real)) * 100
        except:
            return 0.0
    
    def _determine_status(self, simulated: Any, real: float, var_name: str) -> str:
        """Determine comparison status"""
        deviation = abs(self._calculate_deviation(simulated, real))
        
        # Variable-specific thresholds
        strict_vars = ['PVP', 'CPROD', 'NEPP', 'CFD']
        flexible_vars = ['DPH', 'TPV', 'GT', 'IPF']
        
        if var_name in strict_vars:
            threshold = 5  # 5% tolerance
        elif var_name in flexible_vars:
            threshold = 20  # 20% tolerance
        else:
            threshold = 10  # 10% default
        
        if deviation <= threshold:
            return 'success'
        elif deviation <= threshold * 2:
            return 'warning'
        else:
            return 'danger'
    
    def _calculate_summary_statistics(self, results: List[ResultSimulation],
                                    historical_demand: List[float],
                                    validation_results: Dict) -> Dict[str, Any]:
        """Calculate comprehensive summary statistics"""
        summary = {
            'simulation_metrics': {},
            'demand_analysis': {},
            'performance_indicators': {},
            'validation_metrics': {}
        }
        
        # Extract demand values
        simulated_demands = [float(r.demand_mean) for r in results]
        
        # Simulation metrics
        summary['simulation_metrics'] = {
            'total_days': len(results),
            'start_date': results[0].date if results else None,
            'end_date': results[-1].date if results else None,
        }
        
        # Demand analysis
        if simulated_demands:
            summary['demand_analysis'] = {
                'simulated': {
                    'mean': np.mean(simulated_demands),
                    'std': np.std(simulated_demands),
                    'min': np.min(simulated_demands),
                    'max': np.max(simulated_demands),
                    'cv': np.std(simulated_demands) / np.mean(simulated_demands) if np.mean(simulated_demands) > 0 else 0
                }
            }
            
            if historical_demand:
                summary['demand_analysis']['historical'] = {
                    'mean': np.mean(historical_demand),
                    'std': np.std(historical_demand),
                    'min': np.min(historical_demand),
                    'max': np.max(historical_demand),
                    'cv': np.std(historical_demand) / np.mean(historical_demand) if np.mean(historical_demand) > 0 else 0
                }
                
                # Comparison
                summary['demand_analysis']['comparison'] = {
                    'mean_deviation': ((summary['demand_analysis']['simulated']['mean'] - 
                                      summary['demand_analysis']['historical']['mean']) / 
                                     summary['demand_analysis']['historical']['mean'] * 100),
                    'cv_change': (summary['demand_analysis']['simulated']['cv'] - 
                                 summary['demand_analysis']['historical']['cv'])
                }
        
        # Performance indicators
        if results:
            # Extract key metrics from last result
            last_result = results[-1]
            if hasattr(last_result, 'variables') and last_result.variables:
                vars = last_result.variables
                summary['performance_indicators'] = {
                    'final_profit': float(vars.get('GT', 0)),
                    'final_margin': float(vars.get('NR', 0)) * 100,
                    'service_level': float(vars.get('NSC', 0)) * 100,
                    'efficiency': float(vars.get('EOG', 0)) * 100,
                    'roi': float(vars.get('RI', 0)) * 100
                }
        
        # Validation metrics
        if validation_results.get('summary'):
            summary['validation_metrics'] = {
                'overall_accuracy': validation_results['summary'].get('overall_accuracy', 0),
                'success_rate': validation_results['summary'].get('success_rate', 0),
                'variables_validated': validation_results['summary'].get('total_days', 0)
            }
        
        return summary
    
    def _extract_all_variables(self, results: List[ResultSimulation]) -> List[Dict[str, Any]]:
        """Extract all variables from results for analysis"""
        all_variables = []
        
        for idx, result in enumerate(results):
            day_data = {
                'day': idx + 1,
                'date': result.date.isoformat() if result.date else None,
                'demand_mean': float(result.demand_mean),
                'demand_std': float(result.demand_std_deviation)
            }
            
            if hasattr(result, 'variables') and result.variables:
                for key, value in result.variables.items():
                    if not key.startswith('_'):
                        try:
                            day_data[key] = float(value) if isinstance(value, (int, float)) else value
                        except:
                            day_data[key] = 0.0
            
            all_variables.append(day_data)
        
        return all_variables
    
    def _generate_demand_comparison_chart(self, historical_demand: List[float],
                                        results: List[ResultSimulation]) -> Optional[str]:
        """Generate demand comparison chart"""
        try:
            if not historical_demand or not results:
                return None
            
            return self.chart_generator.generate_demand_comparison_chart(
                list(range(1, len(results) + 1)),
                self._extract_all_variables(results),
                historical_demand
            )
        except Exception as e:
            logger.error(f"Error generating comparison chart: {str(e)}")
            return None
    
    def _group_alerts_by_type(self, alerts: List[Dict]) -> Dict[str, List[Dict]]:
        """Group alerts by type for display"""
        grouped = {}
        
        for alert in alerts:
            alert_type = alert.get('type', 'OTHER')
            if alert_type not in grouped:
                grouped[alert_type] = []
            grouped[alert_type].append(alert)
        
        # Sort alerts within each group by severity
        severity_order = {'ERROR': 0, 'WARNING': 1, 'INFO': 2}
        for alert_type in grouped:
            grouped[alert_type].sort(
                key=lambda x: severity_order.get(x.get('severity', 'INFO'), 3)
            )
        
        return grouped
    
    def _calculate_model_performance(self, results: List[ResultSimulation],
                                   real_values: Dict[str, float],
                                   historical_demand: List[float]) -> Dict[str, Any]:
        """Calculate overall model performance metrics"""
        performance = {
            'demand_forecast_accuracy': 0,
            'variable_accuracy': {},
            'overall_score': 0,
            'strengths': [],
            'weaknesses': []
        }
        
        # Demand forecast accuracy
        if historical_demand and results:
            simulated_demands = [float(r.demand_mean) for r in results[:len(historical_demand)]]
            if simulated_demands:
                mape = self._calculate_mape(historical_demand[:len(simulated_demands)], simulated_demands)
                performance['demand_forecast_accuracy'] = max(0, 100 - mape)
        
        # Variable accuracy
        variable_scores = []
        for var_name, real_value in real_values.items():
            if var_name.startswith('_'):
                continue
            
            # Get average simulated value
            sim_values = []
            for result in results:
                if hasattr(result, 'variables') and result.variables:
                    if var_name in result.variables:
                        try:
                            sim_values.append(float(result.variables[var_name]))
                        except:
                            pass
            
            if sim_values:
                avg_sim = np.mean(sim_values)
                accuracy = max(0, 100 - abs(self._calculate_deviation(avg_sim, real_value)))
                performance['variable_accuracy'][var_name] = accuracy
                variable_scores.append(accuracy)
                
                # Identify strengths and weaknesses
                if accuracy >= 90:
                    performance['strengths'].append(f"{var_name}: {accuracy:.1f}% accuracy")
                elif accuracy < 70:
                    performance['weaknesses'].append(f"{var_name}: {accuracy:.1f}% accuracy")
        
        # Overall score
        all_scores = []
        if performance['demand_forecast_accuracy'] > 0:
            all_scores.append(performance['demand_forecast_accuracy'])
        all_scores.extend(variable_scores)
        
        if all_scores:
            performance['overall_score'] = np.mean(all_scores)
        
        return performance
    
    def _calculate_mape(self, actual: List[float], predicted: List[float]) -> float:
        """Calculate Mean Absolute Percentage Error"""
        if len(actual) != len(predicted) or not actual:
            return 100.0
        
        errors = []
        for a, p in zip(actual, predicted):
            if a != 0:
                errors.append(abs((a - p) / a) * 100)
        
        return np.mean(errors) if errors else 100.0
    
    def _get_comparable_simulations(self, current_simulation: Simulation) -> List[Simulation]:
        """Get other simulations for the same product for comparison"""
        try:
            return Simulation.objects.filter(
                fk_questionary_result__fk_questionary__fk_product=current_simulation.fk_questionary_result.fk_questionary.fk_product,
                is_active=True
            ).exclude(
                id=current_simulation.id
            ).order_by('-date_created')[:5]  # Last 5 simulations
        except:
            return []
    
    def _rank_simulation_performance(self, current_id: int,
                                   other_simulations: List[Simulation]) -> Dict[str, Any]:
        """Rank current simulation against others"""
        all_simulations = list(other_simulations) + [
            Simulation.objects.get(id=current_id)
        ]
        
        rankings = []
        for sim in all_simulations:
            # Get summary metrics
            try:
                results = ResultSimulation.objects.filter(
                    fk_simulation=sim,
                    is_active=True
                ).order_by('-date').first()
                
                if results and hasattr(results, 'variables') and results.variables:
                    vars = results.variables
                    score = (
                        float(vars.get('NR', 0)) * 100 +  # Net margin weight
                        float(vars.get('NSC', 0)) * 50 +  # Service level weight
                        float(vars.get('EOG', 0)) * 30    # Efficiency weight
                    )
                    rankings.append({
                        'id': sim.id,
                        'date': sim.date_created,
                        'score': score,
                        'metrics': {
                            'profit_margin': float(vars.get('NR', 0)) * 100,
                            'service_level': float(vars.get('NSC', 0)) * 100,
                            'efficiency': float(vars.get('EOG', 0)) * 100
                        }
                    })
            except:
                continue
        
        # Sort by score
        rankings.sort(key=lambda x: x['score'], reverse=True)
        
        # Find current simulation rank
        current_rank = None
        for idx, rank in enumerate(rankings):
            if rank['id'] == current_id:
                current_rank = idx + 1
                break
        
        return {
            'current_rank': current_rank,
            'total_simulations': len(rankings),
            'rankings': rankings[:5],  # Top 5
            'is_best': current_rank == 1 if current_rank else False
        }


def simulate_result_simulation_view(request, simulation_id):
    """Function-based view wrapper for compatibility"""
    view = SimulateResultView.as_view()
    return view(request, simulation_id=simulation_id)