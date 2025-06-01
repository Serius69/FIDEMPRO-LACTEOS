# services/simulation_service.py
import json
import logging
import random
import statistics
from datetime import timedelta
from typing import Dict, List, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import sympy as sp
from sympy import symbols, Eq, solve
from scipy import stats

from django.core.cache import cache
from django.db import transaction
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404

from ..models import (
    Simulation, ResultSimulation, Demand, DemandBehavior,
    ProbabilisticDensityFunction
)
from ..validators.simulation_validators import SimulationValidator
# from ..utils.cache_utils import get_or_set_cache

from business.models import Business
from finance.models import FinanceRecommendation, FinanceRecommendationSimulation
from product.models import Product, Area
from questionary.models import QuestionaryResult, Answer, Question
from variable.models import Variable, Equation

logger = logging.getLogger(__name__)


class SimulationService:
    """Enhanced service class for handling simulation business logic"""
    
    def __init__(self):
        self.validator = SimulationValidator()
        self.cache_timeout = 3600  # 1 hour cache
        self.batch_size = 100  # For bulk operations
        
    @transaction.atomic
    def create_simulation(self, form_data: Dict[str, Any]) -> Simulation:
        """Create a new simulation instance with validation and optimization"""
        try:
            # Validate form data
            validated_data = self.validator.validate_simulation_data(form_data)
            
            # Get related instances with select_related for optimization
            fk_fdp_instance = get_object_or_404(
                ProbabilisticDensityFunction.objects.select_related('fk_business'),
                id=validated_data['fk_fdp_id']
            )
            fk_questionary_result_instance = get_object_or_404(
                QuestionaryResult.objects.select_related(
                    'fk_questionary__fk_product__fk_business'
                ),
                id=validated_data['fk_questionary_result']
            )
            
            # Create simulation
            simulation_instance = Simulation.objects.create(
                fk_questionary_result=fk_questionary_result_instance,
                quantity_time=validated_data['quantity_time'],
                unit_time=validated_data['unit_time'],
                demand_history=validated_data['demand_history'],
                fk_fdp=fk_fdp_instance,
                is_active=True
            )
            
            # Create initial demand record
            self._create_initial_demand(simulation_instance, validated_data['demand_history'])
            
            logger.info(f"Simulation {simulation_instance.id} created successfully")
            return simulation_instance
            
        except Exception as e:
            logger.error(f"Error creating simulation: {str(e)}")
            raise
    
    def _create_initial_demand(self, simulation_instance: Simulation, demand_history: str) -> Demand:
        """Create initial demand record from history"""
        # Parse demand history efficiently
        demand_history_list = self._parse_demand_history(demand_history)
        demand_mean = statistics.mean(demand_history_list)
        
        product_instance = simulation_instance.fk_questionary_result.fk_questionary.fk_product
        
        return Demand.objects.create(
            quantity=demand_mean,
            fk_simulation=simulation_instance,
            fk_product=product_instance,
            is_predicted=False
        )
    
    def _parse_demand_history(self, demand_history: str) -> List[float]:
        """Parse demand history string to list of floats"""
        cleaned_history = demand_history.replace('[', '').replace(']', '').replace('\r\n', '').split()
        return [float(item) for item in cleaned_history if item.replace('.', '').isdigit()]
    
    @transaction.atomic
    def execute_simulation(self, simulation_instance: Simulation) -> None:
        """Execute simulation with parallel processing and optimization"""
        try:
            nmd = int(simulation_instance.quantity_time)
            
            # Get all required data upfront with optimized queries
            simulation_data = self._prepare_simulation_data(simulation_instance)
            
            # Process days in parallel for better performance
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                
                for day_index in range(nmd):
                    future = executor.submit(
                        self._simulate_single_day_optimized,
                        simulation_instance, simulation_data, day_index
                    )
                    futures.append((day_index, future))
                
                # Collect results and save in order
                results_to_save = []
                for day_index, future in futures:
                    try:
                        day_results = future.result()
                        results_to_save.append((day_index, day_results))
                    except Exception as e:
                        logger.error(f"Error simulating day {day_index}: {str(e)}")
                        continue
                
                # Bulk save results
                self._bulk_save_results(simulation_instance, results_to_save)
            
            # Create predicted demand
            self._create_predicted_demand(simulation_instance)
            
            logger.info(f"Simulation {simulation_instance.id} executed successfully")
            
        except Exception as e:
            logger.error(f"Error executing simulation {simulation_instance.id}: {str(e)}")
            raise
    
    def _prepare_simulation_data(self, simulation_instance: Simulation) -> Dict[str, Any]:
        """Prepare all simulation data with optimized queries"""
        product = simulation_instance.fk_questionary_result.fk_questionary.fk_product
        
        # Use select_related and prefetch_related for optimization
        areas = Area.objects.filter(
            is_active=True,
            fk_product=product
        ).prefetch_related(
            Prefetch(
                'area_equation',
                queryset=Equation.objects.filter(is_active=True).select_related(
                    'fk_variable1', 'fk_variable2', 'fk_variable3',
                    'fk_variable4', 'fk_variable5'
                )
            )
        ).order_by('id')
        
        equations = Equation.objects.filter(
            is_active=True,
            fk_area__in=areas
        ).select_related(
            'fk_variable1', 'fk_variable2', 'fk_variable3',
            'fk_variable4', 'fk_variable5', 'fk_area'
        ).order_by('fk_area_id')
        
        variables = Variable.objects.filter(
            is_active=True,
            fk_product=product
        ).values('id', 'name', 'initials', 'unit')
        
        answers = Answer.objects.filter(
            fk_questionary_result=simulation_instance.fk_questionary_result
        ).select_related('fk_question__fk_variable').values(
            'fk_question_id', 'fk_question__fk_variable__initials', 'answer'
        )
        
        return {
            'areas': list(areas),
            'equations': list(equations),
            'variables': {v['initials']: v for v in variables},
            'answers': list(answers),
            'product': product
        }
    
    def _simulate_single_day_optimized(
        self, simulation_instance: Simulation, simulation_data: Dict[str, Any], 
        day_index: int
    ) -> Dict[str, Any]:
        """Simulate a single day with optimizations"""
        # Process answers into variable dictionary
        variable_initials_dict = self._process_answers_optimized(
            simulation_data['answers'], simulation_instance
        )
        
        # Solve equations with caching
        endogenous_results = self._solve_equations_optimized(
            simulation_data['equations'], variable_initials_dict
        )
        
        return {
            'endogenous_results': endogenous_results,
            'variable_initials_dict': variable_initials_dict
        }
    
    def _process_answers_optimized(
        self, answers: List[Dict], simulation_instance: Simulation
    ) -> Dict[str, float]:
        """Process questionary answers into variable dictionary with optimization"""
        variable_dict = {}
        nmd = int(simulation_instance.quantity_time)
        demand_values = []
        
        for answer_data in answers:
            variable_name = answer_data['fk_question__fk_variable__initials']
            answer_value = answer_data['answer']
            
            if variable_name == "DH":
                # Handle demand history
                try:
                    values = [float(val) for val in answer_value.strip('[]').split()]
                    demand_values.extend(values)
                except Exception as e:
                    logger.warning(f"Error processing demand history: {e}")
                    continue
            else:
                # Handle other variables
                if answer_value == "Sí":
                    variable_dict[variable_name] = 1.0
                elif answer_value == "No":
                    variable_dict[variable_name] = 0.5
                else:
                    try:
                        variable_dict[variable_name] = float(answer_value)
                    except ValueError:
                        logger.warning(f"Could not convert {answer_value} to float")
                        continue
        
        # Process demand history mean
        if demand_values:
            variable_dict["DH"] = round(np.mean(demand_values), 2)
        
        # Set number of simulation days
        variable_dict["NMD"] = nmd
        
        return variable_dict
    
    def _solve_equations_optimized(
        self, equations: List, variable_dict: Dict[str, float]
    ) -> Dict[str, float]:
        """Solve equations with caching and optimization"""
        endogenous_results = {}
        pending_equations = []
        
        # First pass: solve equations that can be solved immediately
        for equation in equations:
            cache_key = f"equation_{equation.id}_vars_{hash(frozenset(variable_dict.items()))}"
            cached_result = cache.get(cache_key)
            
            if cached_result is not None:
                variables = self._get_equation_variables(equation)
                if variables:
                    endogenous_results[variables[-1]] = cached_result
                continue
            
            result = self._try_solve_equation(equation, variable_dict)
            if result is not None:
                variables = self._get_equation_variables(equation)
                if variables:
                    endogenous_results[variables[-1]] = result
                    cache.set(cache_key, result, self.cache_timeout)
            else:
                pending_equations.append(equation)
        
        # Second pass: try to solve pending equations
        if pending_equations:
            self._solve_pending_equations_optimized(
                pending_equations, variable_dict, endogenous_results
            )
        
        return endogenous_results
    
    def _try_solve_equation(
        self, equation: Equation, variable_dict: Dict[str, float]
    ) -> Optional[float]:
        """Try to solve a single equation"""
        try:
            variables = self._get_equation_variables(equation)
            substituted_expression = equation.expression
            
            # Substitute known variables
            for var in variables:
                if var in variable_dict:
                    substituted_expression = substituted_expression.replace(
                        var, str(variable_dict[var])
                    )
            
            # Parse and solve
            if '=' in substituted_expression:
                lhs, rhs = substituted_expression.split('=')
                rhs = rhs.replace('∑', '')
                
                # Try to evaluate the expression
                try:
                    # If rhs is just a number, return it
                    result = float(eval(rhs.strip(), {"__builtins__": {}}, {}))
                    return result
                except:
                    # Try symbolic solving
                    symbol = symbols(lhs.strip())
                    result = solve(Eq(sp.sympify(rhs.strip()), 0), symbol)
                    if result:
                        return float(result[0])
            
        except Exception as e:
            logger.debug(f"Could not solve equation {equation.id}: {e}")
        
        return None
    
    def _get_equation_variables(self, equation: Equation) -> List[str]:
        """Get variables used in an equation"""
        variables = []
        for var_attr in ['fk_variable1', 'fk_variable2', 'fk_variable3', 
                        'fk_variable4', 'fk_variable5']:
            var = getattr(equation, var_attr)
            if var is not None:
                variables.append(var.initials)
        return variables
    
    def _solve_pending_equations_optimized(
        self, pending_equations: List, variable_dict: Dict[str, float],
        endogenous_results: Dict[str, float]
    ) -> None:
        """Solve pending equations with iteration"""
        max_iterations = 10
        iteration = 0
        
        while pending_equations and iteration < max_iterations:
            iteration += 1
            newly_solved = []
            
            # Update variable dict with newly solved values
            combined_dict = {**variable_dict, **endogenous_results}
            
            for equation in pending_equations:
                result = self._try_solve_equation(equation, combined_dict)
                if result is not None:
                    variables = self._get_equation_variables(equation)
                    if variables:
                        endogenous_results[variables[-1]] = result
                        newly_solved.append(equation)
            
            # Remove solved equations
            pending_equations = [eq for eq in pending_equations if eq not in newly_solved]
            
            # If no progress, stop
            if not newly_solved:
                break
    
    def _bulk_save_results(
        self, simulation_instance: Simulation, results: List[Tuple[int, Dict]]
    ) -> None:
        """Bulk save simulation results for better performance"""
        result_objects = []
        
        # Sort results by day index
        results.sort(key=lambda x: x[0])
        
        for day_index, day_data in results:
            endogenous_results = day_data['endogenous_results']
            variable_dict = day_data['variable_initials_dict']
            
            # Calculate demand statistics
            demand_total = endogenous_results.get('DH', variable_dict.get('DH', 0))
            demand_history_numeric = self._parse_demand_history(
                simulation_instance.demand_history
            )
            demand_std_dev = np.std(demand_history_numeric + [demand_total])
            
            # Serialize results
            serializable_results = {
                k: float(v) if isinstance(v, (int, float, np.number)) else str(v)
                for k, v in endogenous_results.items()
            }
            
            result_objects.append(
                ResultSimulation(
                    fk_simulation=simulation_instance,
                    demand_mean=demand_total,
                    demand_std_deviation=demand_std_dev,
                    date=simulation_instance.date_created + timedelta(days=day_index),
                    variables=serializable_results,
                )
            )
            
            # Bulk create in batches
            if len(result_objects) >= self.batch_size:
                ResultSimulation.objects.bulk_create(result_objects)
                result_objects = []
        
        # Save remaining results
        if result_objects:
            ResultSimulation.objects.bulk_create(result_objects)
    
    def _create_predicted_demand(self, simulation_instance: Simulation) -> None:
        """Create predicted demand based on simulation results"""
        # Get the last result
        last_result = ResultSimulation.objects.filter(
            fk_simulation=simulation_instance
        ).order_by('-date').first()
        
        if last_result:
            product = simulation_instance.fk_questionary_result.fk_questionary.fk_product
            
            # Create predicted demand
            predicted_demand = Demand.objects.create(
                quantity=last_result.demand_mean,
                is_predicted=True,
                fk_simulation=simulation_instance,
                fk_product=product,
                confidence_score=0.95 if last_result.demand_std_deviation < 10 else 0.85
            )
            
            # Create demand behavior analysis
            initial_demand = Demand.objects.get(
                fk_simulation=simulation_instance,
                is_predicted=False
            )
            
            DemandBehavior.objects.create(
                current_demand=initial_demand,
                predicted_demand=predicted_demand
            )
    
    def analyze_financial_results(
        self, simulation_id: int, totales_acumulativos: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """Analyze financial results with enhanced insights"""
        try:
            # Get demands with optimized query
            demands = Demand.objects.filter(
                fk_simulation_id=simulation_id
            ).select_related('fk_simulation__fk_questionary_result__fk_questionary__fk_product__fk_business')
            
            demand_initial = demands.get(is_predicted=False)
            demand_predicted = demands.get(is_predicted=True)
            
            # Calculate metrics
            growth_rate = self._calculate_growth_rate(
                demand_initial.quantity, demand_predicted.quantity
            )
            error_permisible = self._calculate_error(
                demand_initial.quantity, demand_predicted.quantity
            )
            
            # Get business instance
            business_instance = demand_initial.fk_simulation.fk_questionary_result.fk_questionary.fk_product.fk_business
            
            # Generate financial recommendations
            recommendations = self._generate_financial_recommendations_optimized(
                business_instance, totales_acumulativos, demand_initial.fk_simulation
            )
            
            # Calculate additional insights
            insights = self._calculate_additional_insights(
                totales_acumulativos, growth_rate, error_permisible
            )
            
            return {
                'demand_initial': demand_initial,
                'demand_predicted': demand_predicted,
                'growth_rate': growth_rate,
                'error_permisible': error_permisible,
                'financial_recommendations_to_show': recommendations,
                'insights': insights
            }
            
        except Exception as e:
            logger.error(f"Error analyzing financial results: {str(e)}")
            raise
    
    def _calculate_growth_rate(self, initial: float, predicted: float) -> float:
        """Calculate growth rate with safety checks"""
        if initial == 0:
            return 0.0
        growth = ((predicted / initial) - 1) * 100
        return round(abs(growth), 2)
    
    def _calculate_error(self, initial: float, predicted: float) -> float:
        """Calculate permissible error"""
        if initial == 0:
            return 0.0
        error = abs((initial - predicted) / initial) * 100
        return round(error, 2)
    
    def _generate_financial_recommendations_optimized(
        self, business_instance: Business, totales_acumulativos: Dict[str, Dict],
        simulation_instance: Simulation
    ) -> List[Dict[str, Any]]:
        """Generate financial recommendations with batch processing"""
        # Get all recommendations at once
        recommendations = FinanceRecommendation.objects.filter(
            is_active=True,
            fk_business=business_instance
        ).select_related('fk_business')
        
        recommendations_to_show = []
        recommendations_to_save = []
        
        for recommendation in recommendations:
            variable_name = recommendation.variable_name
            
            if variable_name in totales_acumulativos:
                variable_value = totales_acumulativos[variable_name]['total']
                threshold_value = recommendation.threshold_value
                
                if threshold_value and variable_value > threshold_value:
                    recommendations_to_show.append({
                        'name': recommendation.name,
                        'recommendation': recommendation.recommendation,
                        'variable_name': variable_name,
                        'severity': self._calculate_severity(variable_value, threshold_value)
                    })
                    
                    recommendations_to_save.append(
                        FinanceRecommendationSimulation(
                            data=variable_value,
                            fk_simulation=simulation_instance,
                            fk_finance_recommendation=recommendation,
                        )
                    )
        
        # Bulk create recommendations
        if recommendations_to_save:
            FinanceRecommendationSimulation.objects.bulk_create(recommendations_to_save)
        
        # Sort by severity
        recommendations_to_show.sort(key=lambda x: x['severity'], reverse=True)
        
        return recommendations_to_show
    
    def _calculate_severity(self, value: float, threshold: float) -> float:
        """Calculate severity score for recommendations"""
        if threshold == 0:
            return 0.0
        excess_percentage = ((value - threshold) / threshold) * 100
        return min(100, excess_percentage)
    
    def _calculate_additional_insights(
        self, totales_acumulativos: Dict[str, Dict], growth_rate: float, 
        error_permisible: float
    ) -> Dict[str, Any]:
        """Calculate additional business insights"""
        insights = {
            'efficiency_score': 0,
            'profitability_index': 0,
            'risk_level': 'low',
            'opportunities': []
        }
        
        # Calculate efficiency score
        if 'INGRESOS TOTALES' in totales_acumulativos and 'GASTOS TOTALES' in totales_acumulativos:
            income = totales_acumulativos['INGRESOS TOTALES']['total']
            expenses = totales_acumulativos['GASTOS TOTALES']['total']
            
            if income > 0:
                insights['efficiency_score'] = round((1 - expenses / income) * 100, 2)
                insights['profitability_index'] = round(income / expenses, 2)
        
        # Determine risk level
        if error_permisible > 15 or growth_rate < -10:
            insights['risk_level'] = 'high'
        elif error_permisible > 10 or growth_rate < 0:
            insights['risk_level'] = 'medium'
        
        # Identify opportunities
        if growth_rate > 20:
            insights['opportunities'].append('Expansión rápida detectada')
        if insights['efficiency_score'] > 30:
            insights['opportunities'].append('Alta eficiencia operativa')
        
        return insights
    
    def create_random_result_simulations(self, instance: Simulation) -> None:
        """Create random result simulations for testing (optimized version)"""
        current_date = instance.date_created
        initial_demand = json.loads(instance.demand_history)
        
        # Pre-calculate statistics
        demand_mean_historical = np.mean(initial_demand)
        demand_std_historical = np.std(initial_demand)
        
        # Generate all results at once
        result_objects = []
        
        for day in range(int(instance.quantity_time)):
            current_date += timedelta(days=1)
            
            # Generate variables efficiently
            variables_means = self._generate_random_variables_optimized(
                demand_mean_historical, demand_std_historical
            )
            
            # Create result
            result_objects.append(
                ResultSimulation(
                    demand_mean=variables_means['DH'],
                    demand_std_deviation=random.normalvariate(5, 20),
                    date=current_date,
                    variables=variables_means,
                    fk_simulation=instance,
                    is_active=True
                )
            )
        
        # Bulk create all results
        ResultSimulation.objects.bulk_create(result_objects, batch_size=self.batch_size)
        
        # Create demand instances
        self._create_demand_instances_bulk(instance, demand_mean_historical)
    
    def _generate_random_variables_optimized(
        self, demand_mean: float, demand_std: float
    ) -> Dict[str, float]:
        """Generate random variables efficiently"""
        # Pre-defined variable configurations
        var_configs = {
            "DH": (demand_mean, demand_std),
            "CTR": (1000, 5000),
            "CTAI": (5000, 20000),
            "TPV": (1000, 5000),
            "TPPRO": (800, 4000),
            "DI": (50, 200),
            "VPC": (500, 1500),
            "IT": (5000, 20000),
            "GT": (3000, 12000),
            "TCA": (500, 2000),
            "NR": (0.1, 0.5),
            "GO": (1000, 5000),
            "GG": (1000, 5000),
            "CTTL": (1000, 5000),
            "CPP": (500, 2000),
            "CPV": (500, 2000),
            "CPI": (500, 2000),
            "CPMO": (500, 2000),
            "CUP": (500, 2000),
            "FU": (0.1, 0.5),
            "TG": (2000, 8000),
            "IB": (3000, 12000),
            "MB": (2000, 8000),
            "RI": (1000, 5000),
            "RTI": (1000, 5000),
            "RTC": (0.1, 0.5),
            "PM": (500, 1500),
            "PE": (1000, 5000),
            "HO": (10, 50),
            "CHO": (1000, 5000),
            "CA": (1000, 5000),
        }
        
        # Generate means efficiently
        return {
            var: max(0, np.mean([
                random.normalvariate(mean, std) for _ in range(10)
            ]))
            for var, (mean, std) in var_configs.items()
        }
    
    def _create_demand_instances_bulk(
        self, simulation_instance: Simulation, demand_mean: float
    ) -> None:
        """Create demand instances efficiently"""
        product = simulation_instance.fk_questionary_result.fk_questionary.fk_product
        
        demands_to_create = []
        
        # Initial demand
        if not Demand.objects.filter(
            fk_simulation=simulation_instance, is_predicted=False
        ).exists():
            initial_demand = Demand(
                quantity=json.loads(simulation_instance.demand_history)[0],
                is_predicted=False,
                fk_simulation=simulation_instance,
                fk_product=product,
                is_active=True
            )
            demands_to_create.append(initial_demand)
        
        # Predicted demand
        if not Demand.objects.filter(
            fk_simulation=simulation_instance, is_predicted=True
        ).exists():
            predicted_demand = Demand(
                quantity=demand_mean,
                is_predicted=True,
                fk_simulation=simulation_instance,
                fk_product=product,
                is_active=True,
                confidence_score=0.85
            )
            demands_to_create.append(predicted_demand)
        
        # Bulk create demands
        if demands_to_create:
            created_demands = Demand.objects.bulk_create(demands_to_create)
            
            # Create demand behavior if both demands exist
            if len(created_demands) == 2:
                DemandBehavior.objects.create(
                    current_demand=created_demands[0],
                    predicted_demand=created_demands[1],
                    is_active=True
                )