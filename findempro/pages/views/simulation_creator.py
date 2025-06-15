"""
views/simulation_creator.py - Creación de simulaciones y resultados
"""
import logging
import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List

from django.contrib.auth.models import User

from business.models import Business
from questionary.models import Questionary, Question, QuestionaryResult, Answer
from simulate.models import (
    Simulation, ResultSimulation, Demand, DemandBehavior, 
    ProbabilisticDensityFunction
)
from variable.models import Variable

logger = logging.getLogger(__name__)


def register_elements_simulation(request, user: User = None) -> int:
    """
    Registrar elementos de simulación para el usuario actual o especificado.
    """
    if user is None:
        user = request.user

    try:
        questionaries = Questionary.objects.filter(
            is_active=True, 
            fk_product__fk_business__fk_user=user
        ).select_related('fk_product__fk_business')

        if not questionaries.exists():
            logger.warning(f"No active questionaries found for user {user.id}")
            return 0

        simulations_created = 0
        for questionary in questionaries:
            if create_and_save_questionary_result(questionary):
                simulations_created += 1

        logger.info(f"{simulations_created} simulations created for user {user.id}")
        return simulations_created

    except Exception as e:
        logger.error(f"Error in simulation registration for user {user.id}: {str(e)}")
        return 0


def create_and_save_questionary_result(questionary: Questionary) -> bool:
    """
    Crear resultado de cuestionario y simulación asociada usando datos realistas
    """
    try:
        questionary_result, created = QuestionaryResult.objects.get_or_create(
            fk_questionary=questionary,
            defaults={'is_active': questionary.is_active}
        )
        
        if created:
            # Crear respuestas realistas
            created_answers = create_realistic_answers_for_questionary(questionary_result)
            logger.info(f"{len(created_answers)} answers created for questionary result")
            
            # Crear simulación mejorada
            # create_enhanced_simulation(questionary_result)
            
            logger.info(f'Questionary result created for questionary {questionary.id}')
            return True
        else:
            logger.info(f'Questionary result already exists for questionary {questionary.id}')
            return False

    except Exception as e:
        logger.error(f"Error creating questionary result: {str(e)}")
        return False


def create_realistic_answers_for_questionary(questionary_result: QuestionaryResult) -> List[Answer]:
    """
    Crear respuestas realistas para un resultado de cuestionario
    """
    created_answers = []
    
    try:
        product_name = questionary_result.fk_questionary.fk_product.name.lower()
        
        # Importar datos de respuestas según el producto
        answer_data = get_answer_data_for_product(product_name)
        
        if not answer_data:
            logger.warning(f"No answer data found for product {product_name}")
            return []
        
        # Obtener preguntas del cuestionario
        questions = Question.objects.filter(
            fk_questionary=questionary_result.fk_questionary,
            is_active=True
        )
        
        for answer_data_item in answer_data:
            question = questions.filter(question=answer_data_item.get('question')).first()
            
            if question:
                answer_value = answer_data_item.get('answer')
                if isinstance(answer_value, list):
                    answer_value = str(answer_value)
                else:
                    answer_value = str(answer_value)
                
                answer = Answer.objects.create(
                    answer=answer_value,
                    fk_question=question,
                    fk_questionary_result=questionary_result,
                    is_active=True
                )
                created_answers.append(answer)
        
        return created_answers
        
    except Exception as e:
        logger.error(f"Error creating realistic answers: {str(e)}")
        return []


def get_answer_data_for_product(product_name: str) -> List[Dict[str, Any]]:
    """
    Obtener datos de respuesta para un producto específico
    """
    # Mapeo de nombres de productos a sus datos
    product_answer_mapping = {
        'leche': 'answer_data_leche',
        'leche entera': 'answer_data_leche',
        'queso': 'answer_data_queso',
        'queso fresco': 'answer_data_queso',
        'yogur': 'answer_data_yogur',
        'yogur natural': 'answer_data_yogur',
        'mantequilla': 'answer_data_mantequilla',
        'crema de leche': 'answer_data_crema',
        'leche deslactosada': 'answer_data_leche_deslactosada',
        'dulce de leche': 'answer_data_dulce_leche'
    }
    
    data_name = product_answer_mapping.get(product_name)
    
    if data_name:
        try:
            module = __import__('questionary.data.questionary_result_test_data', fromlist=[data_name])
            return getattr(module, data_name, [])
        except (ImportError, AttributeError) as e:
            logger.warning(f"Could not import {data_name}: {e}")
    
    return []


def create_enhanced_simulation(questionary_result: QuestionaryResult) -> None:
    """
    Crear simulación mejorada para un resultado de cuestionario
    """
    try:
        product_name = questionary_result.fk_questionary.fk_product.name.lower()
        business = questionary_result.fk_questionary.fk_product.fk_business
        
        # Obtener o crear FDP
        fdp_instance = get_or_create_fdp_for_product(product_name, business)
        
        if not fdp_instance:
            logger.warning(f"No FDP instance available for business {business.id}")
            return
        
        # Obtener datos de simulación específicos del producto
        simulations_data = get_simulation_data_for_product(product_name)
        
        # Crear simulaciones para cada escenario
        if simulations_data:
            for idx, sim_data in enumerate(simulations_data[:3]):  # Máximo 3 escenarios
                simulation = Simulation.objects.create(
                    unit_time=sim_data.get('unit_time', 'days'),
                    quantity_time=sim_data.get('quantity_time', 30),
                    fk_fdp=fdp_instance,
                    demand_history=sim_data.get('demand_history', []),
                    fk_questionary_result=questionary_result,
                    confidence_level=sim_data.get('confidence_level', 0.95),
                    random_seed=sim_data.get('random_seed'),
                    is_active=True
                )
                
                # Ejecutar simulación completa
                execute_complete_simulation(simulation)
                
                logger.info(f"Enhanced simulation created and executed for scenario {idx + 1}")
        else:
            # Crear simulación por defecto
            create_default_simulation(questionary_result, fdp_instance)
        
    except Exception as e:
        logger.error(f"Error creating enhanced simulation: {str(e)}")
        raise


def get_or_create_fdp_for_product(product_name: str, business: Business) -> ProbabilisticDensityFunction:
    """
    Obtener o crear función de densidad probabilística para un producto
    """
    # Configuración por defecto para productos
    pdf_configs = {
        'leche': {'distribution_type': 1, 'mean_param': 2500, 'std_dev_param': 250},
        'queso': {'distribution_type': 1, 'mean_param': 185, 'std_dev_param': 20},
        'yogur': {'distribution_type': 1, 'mean_param': 330, 'std_dev_param': 35},
        'mantequilla': {'distribution_type': 1, 'mean_param': 280, 'std_dev_param': 30},
        'crema de leche': {'distribution_type': 1, 'mean_param': 850, 'std_dev_param': 90},
        'leche deslactosada': {'distribution_type': 1, 'mean_param': 1800, 'std_dev_param': 200},
        'dulce de leche': {'distribution_type': 1, 'mean_param': 420, 'std_dev_param': 45}
    }
    
    config = pdf_configs.get(product_name, pdf_configs['leche'])
    
    fdp_instance, _ = ProbabilisticDensityFunction.objects.get_or_create(
        distribution_type=config['distribution_type'],
        fk_business=business,
        defaults={
            'name': f'Distribución {product_name.title()}',
            'mean_param': config.get('mean_param'),
            'std_dev_param': config.get('std_dev_param'),
            'is_active': True
        }
    )
    
    return fdp_instance


def get_simulation_data_for_product(product_name: str) -> List[Dict[str, Any]]:
    """
    Obtener datos de simulación para un producto específico
    """
    # Mapeo de nombres de productos a sus datos de simulación
    product_simulation_mapping = {
        'leche': 'simulation_data_leche',
        'leche entera': 'simulation_data_leche',
        'queso': 'simulation_data_queso',
        'queso fresco': 'simulation_data_queso',
        'yogur': 'simulation_data_yogur',
        'yogur natural': 'simulation_data_yogur',
        'mantequilla': 'simulation_data_mantequilla',
        'crema de leche': 'simulation_data_crema',
        'leche deslactosada': 'simulation_data_leche_deslactosada',
        'dulce de leche': 'simulation_data_dulce_leche'
    }
    
    data_name = product_simulation_mapping.get(product_name)
    
    if data_name:
        try:
            module = __import__('simulate.data.simulate_test_data', fromlist=[data_name])
            return getattr(module, data_name, [])
        except (ImportError, AttributeError) as e:
            logger.warning(f"Could not import {data_name}: {e}")
    
    return []


def execute_complete_simulation(simulation: Simulation) -> None:
    """
    Ejecutar simulación completa con todas las funciones
    """
    try:
        logger.info(f"Starting complete simulation for simulation {simulation.id}")
        
        # Verificar que existan respuestas
        questionary_result = simulation.fk_questionary_result
        answers_count = Answer.objects.filter(
            fk_questionary_result=questionary_result,
            is_active=True
        ).count()
        
        if answers_count == 0:
            logger.warning(f"No answers found for questionary result {questionary_result.id}")
            # Crear respuestas realistas si no existen
            create_realistic_answers_for_questionary(questionary_result)
        
        # Ejecutar simulaciones en orden
        simulate_demand(simulation)
        simulate_demandbehavior(simulation)
        simulate_resultsimulation(simulation)
        
        logger.info(f"Complete simulation finished for simulation {simulation.id}")
        
    except Exception as e:
        logger.error(f"Error in execute_complete_simulation: {str(e)}")
        raise


def simulate_demand(simulation: Simulation) -> None:
    """
    Simular demanda basada en respuestas del cuestionario
    """
    try:
        questionary_result = simulation.fk_questionary_result
        product = questionary_result.fk_questionary.fk_product
        
        # Obtener respuestas del cuestionario
        answers = Answer.objects.filter(
            fk_questionary_result=questionary_result,
            is_active=True
        ).select_related('fk_question__fk_variable')
        
        # Extraer valores de las respuestas
        demand_values = {}
        for answer in answers:
            if answer.fk_question.fk_variable:
                var_initials = answer.fk_question.fk_variable.initials
                
                # Procesar respuesta según el tipo
                if answer.fk_question.type == 3:  # Lista de valores
                    try:
                        import ast
                        demand_values[var_initials] = ast.literal_eval(answer.answer)
                    except:
                        demand_values[var_initials] = [float(answer.answer)]
                else:
                    try:
                        demand_values[var_initials] = float(answer.answer)
                    except:
                        demand_values[var_initials] = answer.answer
        
        # Obtener demanda histórica si existe
        historical_demand = demand_values.get('DH', simulation.demand_history)
        if isinstance(historical_demand, list) and len(historical_demand) > 0:
            current_demand = historical_demand[-1]
        else:
            current_demand = demand_values.get('DE', 2500)
        
        # Crear demanda actual
        demand_actual, _ = Demand.objects.update_or_create(
            fk_simulation=simulation,
            is_predicted=False,
            defaults={
                'quantity': current_demand,
                'fk_product': product,
                'is_active': True
            }
        )
        
        # Calcular demanda predicha
        growth_rate = demand_values.get('TC', 0.02)
        seasonality = demand_values.get('ED', 1.0)
        
        predicted_demand = current_demand * (1 + growth_rate) * seasonality
        
        # Crear demanda predicha
        demand_predicted, _ = Demand.objects.update_or_create(
            fk_simulation=simulation,
            is_predicted=True,
            defaults={
                'quantity': predicted_demand,
                'fk_product': product,
                'is_active': True
            }
        )
        
        logger.info(f"Demand simulated: current={current_demand}, predicted={predicted_demand}")
        
    except Exception as e:
        logger.error(f"Error in simulate_demand: {str(e)}")
        raise


def simulate_demandbehavior(simulation: Simulation) -> None:
    """
    Simular comportamiento de demanda
    """
    try:
        # Obtener demandas actual y predicha
        demand_actual = Demand.objects.filter(
            fk_simulation=simulation,
            is_predicted=False
        ).first()
        
        demand_predicted = Demand.objects.filter(
            fk_simulation=simulation,
            is_predicted=True
        ).first()
        
        if demand_actual and demand_predicted:
            # Crear o actualizar comportamiento de demanda
            demand_behavior, created = DemandBehavior.objects.update_or_create(
                current_demand=demand_actual,
                predicted_demand=demand_predicted,
                defaults={'is_active': True}
            )
            
            logger.info(f"DemandBehavior {'created' if created else 'updated'}")
        else:
            logger.warning(f"Missing demand instances for simulation {simulation.id}")
            
    except Exception as e:
        logger.error(f"Error in simulate_demandbehavior: {str(e)}")
        raise


def simulate_resultsimulation(simulation: Simulation) -> None:
    """
    Simular resultados basados en respuestas del cuestionario
    """
    try:
        questionary_result = simulation.fk_questionary_result
        product = questionary_result.fk_questionary.fk_product
        
        # Obtener todas las respuestas
        answers = Answer.objects.filter(
            fk_questionary_result=questionary_result,
            is_active=True
        ).select_related('fk_question__fk_variable')
        
        # Crear diccionario de respuestas por variable
        answer_values = {}
        for answer in answers:
            if answer.fk_question.fk_variable:
                var_initials = answer.fk_question.fk_variable.initials
                
                # Procesar valor según tipo
                try:
                    if answer.fk_question.type == 3:  # Lista
                        import ast
                        value = ast.literal_eval(answer.answer)
                        if isinstance(value, list):
                            answer_values[var_initials] = value
                        else:
                            answer_values[var_initials] = float(answer.answer)
                    else:
                        answer_values[var_initials] = float(answer.answer)
                except:
                    answer_values[var_initials] = answer.answer
        
        # Valores base desde respuestas o defaults
        base_demand = answer_values.get('DE', 2500)
        price = answer_values.get('PVP', 15.50)
        production_cost = answer_values.get('CUIP', 8.0)
        employees = answer_values.get('NEPP', 15)
        
        # Crear resultados para cada día
        current_date = simulation.date_created
        result_simulations = []
        
        for day in range(int(simulation.quantity_time)):
            # Variación diaria
            daily_variation = random.uniform(0.95, 1.05)
            daily_demand = base_demand * daily_variation
            
            # Calcular variables
            variables = calculate_variables_from_answers(
                answer_values,
                daily_demand,
                price,
                production_cost,
                employees,
                product.name
            )
            
            current_date += timedelta(days=1)
            
            result_simulation = ResultSimulation(
                demand_mean=daily_demand,
                demand_std_deviation=base_demand * 0.1,
                date=current_date,
                variables=variables,
                fk_simulation=simulation,
                is_active=True
            )
            result_simulations.append(result_simulation)
        
        # Bulk create
        ResultSimulation.objects.bulk_create(result_simulations)
        
        logger.info(f"Created {len(result_simulations)} result simulations")
        
    except Exception as e:
        logger.error(f"Error in simulate_resultsimulation: {str(e)}")
        raise


def calculate_variables_from_answers(answers: dict, demand: float, price: float, 
                                    production_cost: float, employees: int, 
                                    product_name: str) -> dict:
    """
    Calcular variables basadas en respuestas del cuestionario
    """
    # Usar respuestas del cuestionario para calcular variables
    capacity = answers.get('CPROD', demand * 1.2)
    inventory = answers.get('CIP', demand * 1.5)
    marketing = answers.get('GMM', 3500)
    transport_cost = answers.get('CUTRANS', 0.35)
    
    # Calcular ingresos y costos
    revenue = demand * price
    total_costs = demand * production_cost
    gross_profit = revenue - total_costs
    profit_margin = gross_profit / revenue if revenue > 0 else 0
    
    return {
        # Variables de producción
        "TPV": demand * (1 - answers.get('waste_percentage', 0.03)),
        "TPPRO": capacity,
        "DI": max(0, answers.get('DE', demand) - demand),
        "VPC": demand / answers.get('CPD', 85),
        
        # Variables financieras
        "IT": revenue,
        "GT": gross_profit,
        "NR": profit_margin,
        "MB": profit_margin * 1.1,
        "RI": gross_profit / total_costs if total_costs > 0 else 0,
        
        # Variables de eficiencia
        "FU": demand / capacity if capacity > 0 else 0,
        "PE": demand / employees if employees > 0 else 0,
        "PM": answers.get('PM', 0.15),
        
        # Variables de costos
        "CTAI": total_costs * 0.6,
        "GO": answers.get('CFD', 1800) + answers.get('SE', 48000)/30,
        "GG": marketing / 30,
        "TG": total_costs * 0.95,
        "CTTL": demand * transport_cost,
        
        # Variables de inventario
        "CPROD": capacity,
        "IPF": inventory,
        "II": answers.get('CMIPF', inventory * 2),
        "RTI": 30 / answers.get('TR', 3),
        "CA": inventory * 0.02,
        
        # Otras variables
        "CPL": answers.get('CPL', 500),
        "SI": answers.get('SI', 3000),
        "TPC": answers.get('TPC', 2),
        "FC": 1 / answers.get('TPC', 2),
    }


def create_default_simulation(questionary_result: QuestionaryResult, 
                             fdp_instance: ProbabilisticDensityFunction) -> None:
    """
    Crear simulación por defecto
    """
    try:
        # Generar datos de demanda realistas
        base_demand = random.randint(2000, 4000)
        variation = 0.15
        demand_history = [
            int(base_demand * (1 + random.uniform(-variation, variation)))
            for _ in range(30)
        ]
        
        simulation = Simulation.objects.create(
            unit_time='days',
            fk_fdp=fdp_instance,
            demand_history=demand_history,
            quantity_time=30,
            fk_questionary_result=questionary_result,
            confidence_level=0.95,
            is_active=True
        )
        
        # Ejecutar simulación
        execute_complete_simulation(simulation)
        
        logger.info(f"Default simulation created for questionary result {questionary_result.id}")
        
    except Exception as e:
        logger.error(f"Error creating default simulation: {str(e)}")
        raise


def create_probability_density_functions(business: Business) -> None:
    """
    Crear funciones de densidad probabilística para el negocio
    """
    try:
        # Importar datos de PDF
        try:
            from simulate.data.simulate_data import pdf_data
        except ImportError:
            pdf_data = []
        
        if pdf_data:
            for pdf_config in pdf_data:
                ProbabilisticDensityFunction.objects.get_or_create(
                    distribution_type=pdf_config['distribution_type'],
                    fk_business=business,
                    defaults={
                        'name': pdf_config['name'],
                        'mean_param': pdf_config.get('mean_param'),
                        'std_dev_param': pdf_config.get('std_dev_param'),
                        'lambda_param': pdf_config.get('lambda_param'),
                        'shape_param': pdf_config.get('shape_param'),
                        'scale_param': pdf_config.get('scale_param'),
                        'min_param': pdf_config.get('min_param'),
                        'max_param': pdf_config.get('max_param'),
                        'cumulative_distribution_function': pdf_config.get('cumulative_distribution_function', 0.5),
                        'is_active': True
                    }
                )
            logger.info(f"Created {len(pdf_data)} PDF instances for business {business.id}")
        else:
            # Crear PDF por defecto
            ProbabilisticDensityFunction.objects.get_or_create(
                distribution_type=1,  # Normal
                fk_business=business,
                defaults={
                    'name': 'Distribución Normal Estándar',
                    'mean_param': 2500,
                    'std_dev_param': 250,
                    'cumulative_distribution_function': 0.5,
                    'is_active': True
                }
            )
            logger.info("Created default PDF instance")
            
    except Exception as e:
        logger.error(f"Error creating PDF instances: {str(e)}")