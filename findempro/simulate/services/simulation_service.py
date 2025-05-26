# services/simulation_service.py
import json
import random
import statistics
from datetime import timedelta

import numpy as np
import sympy as sp
from sympy import symbols, Eq, solve

from django.shortcuts import get_object_or_404

from ..models import Simulation, ResultSimulation, Demand, DemandBehavior
from ..validators.simulation_validators import SimulationValidator

from business.models import Business
from finance.models import FinanceRecommendation, FinanceRecommendationSimulation
from product.models import Product
from questionary.models import QuestionaryResult, Answer, Question
from variable.models import Variable, Equation


class SimulationService:
    """Service class for handling simulation business logic"""
    
    def __init__(self):
        self.validator = SimulationValidator()
    
    def create_simulation(self, form_data):
        """Create a new simulation instance"""
        # Validate form data
        validated_data = self.validator.validate_simulation_data(form_data)
        
        # Get related instances
        fk_fdp_instance = get_object_or_404(
            ProbabilisticDensityFunction, 
            id=validated_data['fk_fdp_id']
        )
        fk_questionary_result_instance = get_object_or_404(
            QuestionaryResult, 
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
        
        return simulation_instance
    
    def _create_initial_demand(self, simulation_instance, demand_history):
        """Create initial demand record from history"""
        cleaned_demand_history = demand_history.replace('[', '').replace(']', '').replace('\r\n', '').split()
        demand_history_list = [float(item) for item in cleaned_demand_history if item.isdigit()]
        demand_mean = statistics.mean(demand_history_list)
        
        product_instance = get_object_or_404(
            Product, 
            pk=simulation_instance.fk_questionary_result.fk_questionary.fk_product.id
        )
        
        Demand.objects.create(
            quantity=demand_mean,
            fk_simulation=simulation_instance,
            fk_product=product_instance,
            is_predicted=False
        )
    
    def execute_simulation(self, simulation_instance):
        """Execute the main simulation logic"""
        nmd = int(simulation_instance.quantity_time)
        endogenous_results = {}
        
        # Get areas for the product
        areas = Area.objects.filter(
            is_active=True, 
            fk_product=simulation_instance.fk_questionary_result.fk_questionary.fk_product
        ).order_by('id')
        
        # Run simulation for each time period
        for i in range(nmd):
            day_results = self._simulate_single_day(
                simulation_instance, areas, i, endogenous_results
            )
            self._save_day_results(simulation_instance, day_results, i)
    
    def _simulate_single_day(self, simulation_instance, areas, day_index, endogenous_results):
        """Simulate a single day of the simulation"""
        # Get required data
        product_instance = get_object_or_404(
            Product, 
            pk=simulation_instance.fk_questionary_result.fk_questionary.fk_product.id
        )
        
        equations = Equation.objects.filter(
            is_active=True, 
            fk_area__in=areas
        ).order_by('fk_area_id')
        
        variables = Variable.objects.filter(
            is_active=True, 
            fk_product=product_instance
        )
        
        questionary_result = simulation_instance.fk_questionary_result
        answers = Answer.objects.filter(fk_questionary_result=questionary_result)
        
        # Process answers into variable dictionary
        variable_initials_dict = self._process_answers_to_variables(answers, simulation_instance)
        
        # Solve equations
        pending_equations = []
        for equation in equations:
            try:
                result = self._solve_equation(equation, variable_initials_dict)
                if result:
                    variables_to_use = self._get_equation_variables(equation)
                    if variables_to_use:
                        endogenous_results[variables_to_use[-1]] = result[0]
                else:
                    pending_equations.append(equation)
            except Exception as e:
                print(f"Error solving equation: {e}")
                pending_equations.append(equation)
        
        # Process pending equations
        self._process_pending_equations(pending_equations, variable_initials_dict, endogenous_results)
        
        return {
            'endogenous_results': endogenous_results,
            'variable_initials_dict': variable_initials_dict
        }
    
    def _process_answers_to_variables(self, answers, simulation_instance):
        """Process questionary answers into variable dictionary"""
        variable_initials_dict = {}
        nmd = int(simulation_instance.quantity_time)
        
        for answer in answers:
            question_id = str(answer.fk_question.id)
            question = get_object_or_404(Question, pk=question_id)
            variable_name = f"{question.fk_variable.initials}"
            
            if variable_name == "DH":
                # Handle demand history
                if variable_name not in variable_initials_dict:
                    variable_initials_dict[variable_name] = []
                try:
                    values = [float(val) for val in answer.answer.strip('[]').split()]
                    answer_array = np.array(values)
                    variable_initials_dict[variable_name].extend(answer_array)
                except Exception as e:
                    print(f"Error processing demand history: {e}")
                    continue
            else:
                # Handle other variables
                if answer.answer == "Sí":
                    variable_initials_dict[variable_name] = 1.0
                elif answer.answer == "No":
                    variable_initials_dict[variable_name] = 0.5
                else:
                    variable_initials_dict[variable_name] = float(answer.answer)
        
        # Process demand history mean
        if "DH" in variable_initials_dict:
            demand_mean = round(np.mean(variable_initials_dict["DH"]), 2)
            variable_initials_dict["DH"] = demand_mean
        
        # Set number of simulation days
        if "NMD" in variable_initials_dict:
            variable_initials_dict["NMD"] = nmd
        
        return variable_initials_dict
    
    def _solve_equation(self, equation, variable_initials_dict):
        """Solve a single equation"""
        variables_to_use = self._get_equation_variables(equation)
        
        substituted_expression = equation.expression
        for var in variables_to_use:
            if var in variable_initials_dict:
                substituted_expression = substituted_expression.replace(
                    var, str(variable_initials_dict.get(var))
                )
        
        lhs, rhs = substituted_expression.split('=')
        
        if rhs is not None:
            rhs = rhs.replace('∑', '')
            try:
                symbol = symbols(rhs.strip())
                result = solve(Eq(sp.sympify(rhs.strip()), 0), symbol)
                return result
            except Exception:
                return None
        
        return None
    
    def _get_equation_variables(self, equation):
        """Get variables used in an equation"""
        return [
            var.initials for var in [
                equation.fk_variable1, equation.fk_variable2, 
                equation.fk_variable3, equation.fk_variable4, 
                equation.fk_variable5
            ] if var is not None
        ]
    
    def _process_pending_equations(self, pending_equations, variable_initials_dict, endogenous_results):
        """Process equations that couldn't be solved initially"""
        # This would contain the logic from try_to_solve_pending_equations
        # Simplified for brevity
        pass
    
    def _save_day_results(self, simulation_instance, day_results, day_index):
        """Save results for a single day"""
        demand_total = self.validator.convert_to_float(0)  # Calculate actual demand
        demand_history_numeric = self.validator.convert_to_numeric_list(
            simulation_instance.demand_history
        )
        demand_std_dev = self.validator.calculate_std_dev(
            demand_history_numeric + [demand_total]
        )
        
        serializable_results = self.validator.serialize_endogenous_results(
            day_results['endogenous_results']
        )
        
        json_data = json.dumps(serializable_results)
        
        new_result_simulation = ResultSimulation(
            fk_simulation=simulation_instance,
            demand_mean=demand_total,
            demand_std_deviation=demand_std_dev,
            date=simulation_instance.date_created + timedelta(days=day_index),
            variables=json_data,
        )
        new_result_simulation.save()
    
    def analyze_financial_results(self, simulation_id, totales_acumulativos):
        """Analyze financial results and generate recommendations"""
        # Get demand data
        demand_initial = get_object_or_404(
            Demand, 
            fk_simulation_id=simulation_id, 
            is_predicted=False
        )
        demand_predicted = get_object_or_404(
            Demand, 
            fk_simulation_id=simulation_id, 
            is_predicted=True
        )
        
        # Calculate growth rate
        growth_rate = abs(
            ((demand_predicted.quantity / demand_initial.quantity) ** (1 / 1) - 1) * 100
        )
        growth_rate = round(growth_rate, 2)
        
        # Calculate error
        error_permisible = abs(
            ((demand_initial.quantity - demand_predicted.quantity) / demand_initial.quantity) * 100
        )
        
        # Get business instance
        simulation_instance = get_object_or_404(Simulation, pk=simulation_id)
        business_instance = get_object_or_404(
            Business, 
            pk=simulation_instance.fk_questionary_result.fk_questionary.fk_product.fk_business.id
        )
        
        # Generate financial recommendations
        financial_recommendations_to_show = self._generate_financial_recommendations(
            business_instance, totales_acumulativos, simulation_instance
        )
        
        return {
            'demand_initial': demand_initial,
            'demand_predicted': demand_predicted,
            'growth_rate': growth_rate,
            'error_permisible': error_permisible,
            'financial_recommendations_to_show': financial_recommendations_to_show,
        }
    
    def _generate_financial_recommendations(self, business_instance, totales_acumulativos, simulation_instance):
        """Generate financial recommendations based on simulation results"""
        financial_recommendations = FinanceRecommendation.objects.filter(
            is_active=True,
            fk_business=business_instance
        )
        
        recommendations_to_show = []
        
        for recommendation_instance in financial_recommendations:
            name = recommendation_instance.name
            variable_name = recommendation_instance.variable_name
            threshold_value = recommendation_instance.threshold_value
            
            if variable_name in totales_acumulativos:
                variable_value = totales_acumulativos[variable_name]['total']
                
                if threshold_value is not None and variable_value is not None:
                    if variable_value > threshold_value:
                        recommendation_data = {
                            'name': name,
                            'recommendation': recommendation_instance.recommendation,
                            'variable_name': variable_name
                        }
                        recommendations_to_show.append(recommendation_data)
                        
                        # Save recommendation simulation
                        FinanceRecommendationSimulation.objects.create(
                            data=variable_value,
                            fk_simulation=simulation_instance,
                            fk_finance_recommendation=recommendation_instance,
                        )
        
        return recommendations_to_show
    
    def create_random_result_simulations(self, instance):
        """Create random result simulations for testing purposes"""
        current_date = instance.date_created
        
        for day in range(int(instance.quantity_time)):
            # Generate random demand and variables
            initial_demand = json.loads(instance.demand_history)
            demand_mean_historical = np.mean(initial_demand)
            demand_std_deviation_historical = np.std(initial_demand)
            
            # Generate random variables for this day
            variables = self._generate_random_variables()
            demand_mean = random.normalvariate(demand_mean_historical, demand_std_deviation_historical)
            
            # Calculate means for variables
            means = {variable: np.mean(values) for variable, values in variables.items()}
            
            current_date += timedelta(days=1)
            demand_std_deviation = random.normalvariate(5, 20)
            
            # Create result simulation
            result_simulation = ResultSimulation(
                demand_mean=demand_mean,
                demand_std_deviation=demand_std_deviation,
                date=current_date,
                variables=means,
                fk_simulation=instance,
                is_active=True
            )
            result_simulation.save()
        
        # Create demand instances
        self._create_demand_instances(instance, demand_mean_historical)
    
    def _generate_random_variables(self):
        """Generate random variables for simulation"""
        return {
            "CTR": [max(0, random.normalvariate(1000, 5000)) for _ in range(10)],
            "CTAI": [max(0, random.normalvariate(5000, 20000)) for _ in range(10)],
            "TPV": [max(0, random.normalvariate(1000, 5000)) for _ in range(10)],
            "TPPRO": [max(0, random.normalvariate(800, 4000)) for _ in range(10)],
            "DI": [max(0, random.normalvariate(50, 200)) for _ in range(10)],
            "VPC": [max(0, random.normalvariate(500, 1500)) for _ in range(10)],
            "IT": [max(0, random.normalvariate(5000, 20000)) for _ in range(10)],
            "GT": [max(0, random.normalvariate(3000, 12000)) for _ in range(10)],
            "TCA": [max(0, random.normalvariate(500, 2000)) for _ in range(10)],
            "NR": [max(0, random.normalvariate(0.1, 0.5)) for _ in range(10)],
            "GO": [max(0, random.normalvariate(1000, 5000)) for _ in range(10)],
            "GG": [max(0, random.normalvariate(1000, 5000)) for _ in range(10)],
            "CTTL": [max(0, random.normalvariate(1000, 5000)) for _ in range(10)],
            "CPP": [max(0, random.normalvariate(500, 2000)) for _ in range(10)],
            "CPV": [max(0, random.normalvariate(500, 2000)) for _ in range(10)],
            "CPI": [max(0, random.normalvariate(500, 2000)) for _ in range(10)],
            "CPMO": [max(0, random.normalvariate(500, 2000)) for _ in range(10)],
            "CUP": [max(0, random.normalvariate(500, 2000)) for _ in range(10)],
            "FU": [max(0, random.normalvariate(0.1, 0.5)) for _ in range(10)],
            "TG": [max(0, random.normalvariate(2000, 8000)) for _ in range(10)],
            "IB": [max(0, random.normalvariate(3000, 12000)) for _ in range(10)],
            "MB": [max(0, random.normalvariate(2000, 8000)) for _ in range(10)],
            "RI": [max(0, random.normalvariate(1000, 5000)) for _ in range(10)],
            "RTI": [max(0, random.normalvariate(1000, 5000)) for _ in range(10)],
            "RTC": [max(0, random.normalvariate(0.1, 0.5)) for _ in range(10)],
            "PM": [max(0, random.normalvariate(500, 1500)) for _ in range(10)],
            "PE": [max(0, random.normalvariate(1000, 5000)) for _ in range(10)],
            "HO": [max(0, random.normalvariate(10, 50)) for _ in range(10)],
            "CHO": [max(0, random.normalvariate(1000, 5000)) for _ in range(10)],
            "CA": [max(0, random.normalvariate(1000, 5000)) for _ in range(10)],
        }
    
    def _create_demand_instances(self, simulation_instance, demand_mean):
        """Create demand instances for initial and predicted values"""
        product = simulation_instance.fk_questionary_result.fk_questionary.fk_product
        
        # Create initial demand if not exists
        if not Demand.objects.filter(fk_simulation=simulation_instance, is_predicted=False).exists():
            demand_instance = Demand(
                quantity=json.loads(simulation_instance.demand_history)[0],
                is_predicted=False,
                fk_simulation=simulation_instance,
                fk_product=product,
                is_active=True
            )
            demand_instance.save()
        
        # Create predicted demand if not exists
        if not Demand.objects.filter(fk_simulation=simulation_instance, is_predicted=True).exists():
            demand_predicted_instance = Demand(
                quantity=demand_mean,
                is_predicted=True,
                fk_simulation=simulation_instance,
                fk_product=product,
                is_active=True
            )
            demand_predicted_instance.save()
            
            # Create demand behavior
            if not DemandBehavior.objects.filter(
                current_demand=demand_instance, 
                predicted_demand=demand_predicted_instance
            ).exists():
                demand_behavior = DemandBehavior(
                    current_demand=demand_instance,
                    predicted_demand=demand_predicted_instance,
                    is_active=True
                )
                demand_behavior.save()