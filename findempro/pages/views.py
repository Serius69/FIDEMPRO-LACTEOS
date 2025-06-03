from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.core.exceptions import MultipleObjectsReturned
from django.http import Http404, JsonResponse
from django.contrib.auth.models import User
from django.db import transaction
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from .forms import RegisterElementsForm
from user.models import UserProfile
from business.models import Business
from product.models import Product, Area
from variable.models import Variable, Equation
from questionary.models import Questionary, Question, QuestionaryResult, Answer
from simulate.models import Simulation, ResultSimulation, Demand, DemandBehavior

from product.products_data import products_data
from product.areas_data import areas_data
from questionary.questionary_data import questionary_data, question_data
from questionary.questionary_result_data import questionary_result_data, answer_data
from variable.variables_data import variables_data
from variable.equations_data import equations_data

import random
import numpy as np
from datetime import datetime, timedelta
import logging
from django.conf import settings
import os
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class PagesView(TemplateView):
    """Vista base para páginas estáticas"""
    pass


@login_required
@transaction.atomic
def register_elements(request):
    """
    Registra elementos del negocio para el usuario actual.
    Usa transacción atómica para asegurar consistencia de datos.
    """
    if request.method == 'POST':
        form = RegisterElementsForm(request.POST)
        if form.is_valid():
            try:
                create_and_save_business(request.user)
                messages.success(request, _('Elementos registrados correctamente.'))
                return redirect("dashboard:index")  # Redirige a la url 'dashboard:index'
            except Exception as e:
                logger.error(f"Error creating business for user {request.user.id}: {str(e)}")
                messages.error(request, _('Error al crear el negocio. Por favor, intente nuevamente.'))
                form.add_error(None, str(e))
    else:
        form = RegisterElementsForm()
        logger.error(f"Error creating elements {request.user.id}: {str(e)}")
    return redirect("dashboard:index")


def create_and_save_business(user: User) -> Business:
    """
    Crear y guardar business para un usuario, permitiendo múltiples negocios con nombres únicos.
    
    Args:
        user: Usuario Django
        
    Returns:
        Business: Instancia del negocio creado
        
    Raises:
        Exception: Si hay error en la creación
    """
    try:
        # Generar nombre único
        base_name = "Pyme Láctea"
        name = base_name
        counter = 1

        while Business.objects.filter(fk_user=user, name=name).exists():
            counter += 1
            name = f"{base_name} #{counter}"

        # Construir la ruta de la imagen
        image_filename = f"pyme_lactea_default.jpg"
        image_src = os.path.join(settings.MEDIA_URL, "business", image_filename)

        business = Business.objects.create(
            name=name,
            type=1,
            location="La Paz",
            image_src=image_src,
            fk_user=user,
            is_active=user.is_active
        )

        # Crear productos asociados
        create_and_save_products(business)
        
        logger.info(f'Business "{name}" created successfully for user {user.id}')
        return business

    except Exception as e:
        logger.error(f"Error creating business: {str(e)}")
        raise


def create_and_save_products(business: Business) -> None:
    """
    Crear y guardar productos para un business
    
    Args:
        business: Instancia del negocio
    """
    try:
        created_products = []
        
        for data in products_data:
            # Validar datos requeridos
            if not data.get('name') or not data.get('type'):
                logger.warning(f"Skipping product with incomplete data: {data}")
                continue
                
            image_filename = f"{data.get('name', 'default')}.jpg"
            image_src = os.path.join(settings.MEDIA_URL, "product", image_filename)

            product = Product.objects.create(
                name=data['name'],
                description=data.get('description', ''),
                image_src=image_src,
                type=data['type'],
                is_active=True,
                fk_business=business,
            )
            created_products.append(product)

            # Crear componentes relacionados
            create_and_save_areas(product)
            create_variables_and_equations(product)
            create_and_save_questionary(product)

        logger.info(f'{len(created_products)} products created successfully for business {business.id}')

    except Exception as e:
        logger.error(f"Error creating products for business {business.id}: {str(e)}")
        raise


def create_and_save_areas(product: Product) -> None:
    """
    Crear y guardar áreas para un producto
    
    Args:
        product: Instancia del producto
    """
    try:
        created_areas = []
        
        for data in areas_data:
            if not data.get('name'):
                continue
                
            image_filename = f"{data.get('name', 'default')}.jpg"
            image_src = os.path.join(settings.MEDIA_URL, "area", image_filename)

            area = Area.objects.create(
                name=data['name'],
                description=data.get('description', ''),
                params=data.get('params', {}),
                image_src=image_src,
                is_active=True,
                fk_product=product,
            )
            created_areas.append(area)

        logger.info(f'{len(created_areas)} areas created successfully for product {product.id}')

    except Exception as e:
        logger.error(f"Error creating areas for product {product.id}: {str(e)}")
        raise


def create_variables_and_equations(product: Product) -> None:
    """
    Crear variables y ecuaciones para un producto
    
    Args:
        product: Instancia del producto
    """
    try:
        # Crear variables
        created_variables = []
        for data in variables_data:
            if not all([data.get('name'), data.get('initials'), data.get('type')]):
                logger.warning(f"Skipping variable with incomplete data: {data}")
                continue
                
            image_filename = f"{data.get('initials', 'default')}.jpg"
            image_src = os.path.join(settings.MEDIA_URL, "variable", image_filename)
            
            variable = Variable.objects.create(
                name=data.get('name'),
                initials=data.get('initials'),
                type=data.get('type'),
                unit=data.get('unit', ''),
                image_src=image_src,
                description=data.get('description', ''),
                fk_product=product,
                is_active=True
            )
            created_variables.append(variable)
        
        # Verificar que se crearon todas las variables esperadas
        if len(created_variables) == len(variables_data):
            create_equations(product)
            logger.info(f"Variables and equations created successfully for product {product.id}")
        else:
            logger.warning(
                f"Created {len(created_variables)} of {len(variables_data)} expected variables "
                f"for product {product.id}"
            )
            
    except Exception as e:
        logger.error(f"Error creating variables and equations for product {product.id}: {str(e)}")
        raise


def create_equations(product: Product) -> None:
    """
    Crear ecuaciones para un producto
    
    Args:
        product: Instancia del producto
    """
    try:
        created_equations = []
        
        for data in equations_data:
            # Validar datos requeridos
            if not all([data.get('name'), data.get('expression'), 
                       data.get('variable1'), data.get('variable2'), data.get('area')]):
                logger.warning(f"Skipping equation with incomplete data: {data}")
                continue
                
            try:
                variable1 = get_variable_by_initials(data['variable1'], product.id)
                variable2 = get_variable_by_initials(data['variable2'], product.id)
                variable3 = get_variable_by_initials(data.get('variable3'), product.id)
                variable4 = get_variable_by_initials(data.get('variable4'), product.id)
                variable5 = get_variable_by_initials(data.get('variable5'), product.id)
                area = get_area_by_name(data['area'], product.id)
                
                equation = Equation.objects.create(
                    name=data['name'],
                    description=data.get('description', ''),
                    expression=data['expression'],
                    fk_variable1=variable1,
                    fk_variable2=variable2,
                    fk_variable3=variable3,
                    fk_variable4=variable4,
                    fk_variable5=variable5,
                    fk_area=area,
                    is_active=True
                )
                created_equations.append(equation)
                
            except Http404 as e:
                logger.error(f"Error creating equation '{data.get('name')}': {str(e)}")
                continue
                
        logger.info(f"{len(created_equations)} equations created for product {product.id}")
            
    except Exception as e:
        logger.error(f"Error creating equations for product {product.id}: {str(e)}")
        raise


def get_variable_by_initials(variable_initials: Optional[str], product_id: int) -> Optional[Variable]:
    """
    Obtener variable por iniciales y producto
    
    Args:
        variable_initials: Iniciales de la variable
        product_id: ID del producto
        
    Returns:
        Variable o None
        
    Raises:
        Http404: Si la variable requerida no existe
    """
    if variable_initials is None:
        return None
    
    try:
        return Variable.objects.get(initials=variable_initials, fk_product_id=product_id)
    except Variable.DoesNotExist:
        raise Http404(
            f"Variable with initials '{variable_initials}' "
            f"for product id '{product_id}' does not exist."
        )
    except Variable.MultipleObjectsReturned:
        logger.warning(
            f"Multiple variables found with initials '{variable_initials}' "
            f"for product {product_id}. Using first one."
        )
        return Variable.objects.filter(
            initials=variable_initials, 
            fk_product_id=product_id
        ).first()


def get_area_by_name(area_name: str, product_id: int) -> Area:
    """
    Obtener área por nombre y producto
    
    Args:
        area_name: Nombre del área
        product_id: ID del producto
        
    Returns:
        Area
        
    Raises:
        Http404: Si el área no existe
    """
    try:
        return Area.objects.get(name=area_name, fk_product_id=product_id)
    except Area.DoesNotExist:
        raise Http404(
            f"Area with name '{area_name}' for product id '{product_id}' does not exist."
        )
    except Area.MultipleObjectsReturned:
        logger.warning(
            f"Multiple areas found with name '{area_name}' for product {product_id}. "
            f"Using first one."
        )
        return Area.objects.filter(name=area_name, fk_product_id=product_id).first()


def create_and_save_questionary(product: Product) -> None:
    """
    Crear cuestionario para un producto
    
    Args:
        product: Instancia del producto
    """
    try:
        for data in questionary_data:
            if not data.get('questionary'):
                continue
                
            questionary = Questionary.objects.create(
                questionary=f"{data['questionary']} - {product.name}",
                fk_product=product,
                is_active=True
            )
            
            create_and_save_questions(questionary)
            
        logger.info(f'Questionary created successfully for product {product.id}')
        
    except Exception as e:
        logger.error(f"Error creating questionary for product {product.id}: {str(e)}")
        raise


def create_and_save_questions(questionary: Questionary) -> None:
    """
    Crear preguntas para un cuestionario
    
    Args:
        questionary: Instancia del cuestionario
    """
    try:
        created_questions = []
        
        for data in question_data:
            if not all([data.get('question'), data.get('type'), data.get('initials_variable')]):
                logger.warning(f"Skipping question with incomplete data: {data}")
                continue
                
            try:
                variable = Variable.objects.get(
                    initials=data['initials_variable'],
                    fk_product=questionary.fk_product
                )
            except Variable.DoesNotExist:
                logger.error(
                    f"Variable with initials '{data['initials_variable']}' not found "
                    f"for product {questionary.fk_product.id}"
                )
                continue
            except Variable.MultipleObjectsReturned:
                variable = Variable.objects.filter(
                    initials=data['initials_variable'],
                    fk_product=questionary.fk_product
                ).first()

            # Solo agregar possible_answers si el tipo no es 1 (respuesta abierta)
            possible_answers = data.get('possible_answers') if data['type'] != 1 else None
                
            question = Question.objects.create(
                question=data['question'],
                type=data['type'],
                fk_questionary=questionary,
                fk_variable=variable,
                possible_answers=possible_answers,
                is_active=True
            )
            created_questions.append(question)
            
        logger.info(f"{len(created_questions)} questions created for questionary {questionary.id}")
            
    except Exception as e:
        logger.error(f"Error creating questions for questionary {questionary.id}: {str(e)}")
        raise


@login_required
@transaction.atomic
def register_elements_simulation(request):
    """
    Registrar elementos de simulación para el usuario actual
    """
    if request.method == 'POST':
        form = RegisterElementsForm(request.POST)
        if form.is_valid():
            try:
                questionaries = Questionary.objects.filter(
                    is_active=True, 
                    fk_product__fk_business__fk_user=request.user
                ).select_related('fk_product__fk_business')

                if not questionaries.exists():
                    messages.warning(request, _('No se encontraron cuestionarios activos.'))
                    return redirect("dashboard:index")

                simulations_created = 0
                for questionary in questionaries:
                    if create_and_save_questionary_result(questionary):
                        simulations_created += 1

                messages.success(
                    request, 
                    _(f'{simulations_created} simulaciones creadas exitosamente.')
                )
                return redirect("dashboard:index")
                    
            except Exception as e:
                logger.error(f"Error in simulation registration: {str(e)}")
                messages.error(request, _('Error al procesar la simulación.'))
                form.add_error(None, str(e))

    else:
        form = RegisterElementsForm()

    return render(request, 'pages/register_elements.html', {
        'form': form,
        'title': 'Registrar Simulación'
    })


def create_and_save_questionary_result(questionary: Questionary) -> bool:
    """
    Crear resultado de cuestionario y simulación asociada
    
    Args:
        questionary: Instancia del cuestionario
        
    Returns:
        bool: True si se creó exitosamente
    """
    try:
        questionary_result, created = QuestionaryResult.objects.get_or_create(
            fk_questionary=questionary,
            defaults={'is_active': questionary.is_active}
        )

        if created:
            create_and_save_answers(questionary_result)
            create_and_save_simulation(questionary_result)
            logger.info(f'Questionary result created for questionary {questionary.id}')
            return True
        else:
            logger.info(f'Questionary result already exists for questionary {questionary.id}')
            return False

    except Exception as e:
        logger.error(f"Error creating questionary result: {str(e)}")
        return False


def create_and_save_answers(questionary_result: QuestionaryResult) -> None:
    """
    Crear respuestas para un resultado de cuestionario
    
    Args:
        questionary_result: Instancia del resultado del cuestionario
    """
    try:
        created_answers = []
        questions = Question.objects.filter(
            fk_questionary=questionary_result.fk_questionary,
            is_active=True
        )
        
        for data in answer_data:
            question = get_question_by_text(data.get('question'), questions)
            if question and data.get('answer'):
                answer, created = Answer.objects.get_or_create(
                    fk_question=question,
                    fk_questionary_result=questionary_result,
                    defaults={
                        'answer': data['answer'],
                        'is_active': True
                    }
                )
                if created:
                    created_answers.append(answer)
                    
        logger.info(f"{len(created_answers)} answers created for questionary result {questionary_result.id}")
                
    except Exception as e:
        logger.error(f"Error creating answers: {str(e)}")
        raise


def get_question_by_text(question_text: Optional[str], questions_queryset=None) -> Optional[Question]:
    """
    Obtener pregunta por texto
    
    Args:
        question_text: Texto de la pregunta
        questions_queryset: QuerySet opcional para buscar
        
    Returns:
        Question o None
    """
    if question_text is None:
        return None
    
    try:
        if questions_queryset is not None:
            return questions_queryset.filter(question=question_text).first()
        else:
            return Question.objects.get(question=question_text)
    except Question.DoesNotExist:
        logger.warning(f"Question '{question_text}' does not exist")
        return None
    except Question.MultipleObjectsReturned:
        logger.warning(f"Multiple questions found with text '{question_text}'")
        return Question.objects.filter(question=question_text).first()


def create_and_save_simulation(questionary_result: QuestionaryResult) -> None:
    """
    Crear simulación para un resultado de cuestionario
    
    Args:
        questionary_result: Instancia del resultado del cuestionario
    """
    try:
        # Obtener FDP instance
        fdp_instance = questionary_result.fk_questionary.fk_product.fk_business.fk_business_fdp.first()
        if fdp_instance is None:
            logger.warning(
                f"No FDP instance found for questionary result {questionary_result.id}"
            )
            return
        
        # Generar datos de demanda más realistas
        base_demand = random.randint(2000, 4000)
        variation = 0.15  # 15% de variación
        demand_history = [
            int(base_demand * (1 + random.uniform(-variation, variation)))
            for _ in range(30)
        ]
        
        simulation, created = Simulation.objects.get_or_create(
            fk_questionary_result=questionary_result,
            defaults={
                'unit_time': 'day',
                'fk_fdp': fdp_instance,
                'demand_history': demand_history,
                'quantity_time': 30,
                'is_active': True
            }
        )
        
        if created:
            create_random_result_simulations(simulation)
            logger.info(f"Simulation created for questionary result {questionary_result.id}")
        else:
            logger.info(f"Simulation already exists for questionary result {questionary_result.id}")
            
    except Exception as e:
        logger.error(f"Error creating simulation: {str(e)}")
        raise


def create_random_result_simulations(simulation: Simulation) -> None:
    """
    Crear resultados de simulación con datos más realistas
    
    Args:
        simulation: Instancia de la simulación
    """
    try:
        current_date = simulation.date_created
        result_simulations = []
        
        logger.info(f'Creating {simulation.quantity_time} ResultSimulation instances')
        
        # Generar datos base para mantener consistencia
        base_values = generate_base_values()
        
        for day in range(int(simulation.quantity_time)):
            # Generar variaciones diarias
            daily_variation = 0.05  # 5% de variación diaria
            demand = generate_daily_demand(base_values['demand'], daily_variation)
            demand_mean = np.mean(demand)
            demand_std = np.std(demand)
            
            # Generar variables con correlaciones realistas
            variables = generate_correlated_variables(base_values, demand_mean, daily_variation)
            
            # Calcular medias
            means = {var: np.mean(values) for var, values in variables.items()}
            
            current_date += timedelta(days=1)
            
            result_simulation = ResultSimulation(
                demand_mean=demand_mean,
                demand_std_deviation=demand_std,
                date=current_date,
                variables=means,
                fk_simulation=simulation,
                is_active=True
            )
            result_simulations.append(result_simulation)
        
        # Bulk create para mejor rendimiento
        ResultSimulation.objects.bulk_create(result_simulations)
        
        # Crear instancias de demanda
        create_demand_instances(simulation, demand_mean)
        
        logger.info(f"Created {len(result_simulations)} result simulations")
        
    except Exception as e:
        logger.error(f"Error creating result simulations: {str(e)}")
        raise


def generate_base_values() -> Dict[str, float]:
    """Generar valores base para las variables"""
    return {
        'demand': 3000,
        'price': 15,
        'production_cost': 8,
        'inventory': 500,
        'capacity': 5000,
        'efficiency': 0.85
    }


def generate_daily_demand(base_demand: float, variation: float) -> List[float]:
    """Generar demanda diaria con variación realista"""
    return [
        base_demand * (1 + random.gauss(0, variation))
        for _ in range(10)
    ]


def generate_correlated_variables(base_values: Dict[str, float], 
                                 demand_mean: float, 
                                 variation: float) -> Dict[str, List[float]]:
    """
    Generar variables con correlaciones realistas basadas en la demanda
    """
    demand_factor = demand_mean / base_values['demand']
    
    return {
        # Costos variables (correlacionados con demanda)
        "CTR": [base_values['production_cost'] * 100 * demand_factor * 
                (1 + random.gauss(0, variation)) for _ in range(10)],
        "CTAI": [5000 + (demand_mean * 2) * (1 + random.gauss(0, variation * 0.5)) 
                 for _ in range(10)],
        
        # Tiempos de proceso (inversamente correlacionados con eficiencia)
        "TPV": [120 / base_values['efficiency'] * (1 + random.gauss(0, variation)) 
                for _ in range(10)],
        "TPPRO": [90 / base_values['efficiency'] * (1 + random.gauss(0, variation)) 
                  for _ in range(10)],
        
        # Inventarios (correlacionados con demanda)
        "DI": [demand_mean * 0.1 * (1 + random.gauss(0, variation * 2)) 
               for _ in range(10)],
        "VPC": [base_values['inventory'] * (1 + random.gauss(0, variation)) 
                for _ in range(10)],
        
        # Ingresos y gastos
        "IT": [demand_mean * base_values['price'] * (1 + random.gauss(0, variation * 0.3)) 
               for _ in range(10)],
        "GT": [demand_mean * base_values['production_cost'] * (1 + random.gauss(0, variation * 0.2)) 
               for _ in range(10)],
        
        # Capacidad y eficiencia
        "TCA": [base_values['capacity'] * 0.3 * (1 + random.gauss(0, variation * 0.1)) 
                for _ in range(10)],
        "NR": [base_values['efficiency'] * (1 + random.gauss(0, variation * 0.05)) 
               for _ in range(10)],
        
        # Gastos operativos
        "GO": [1500 + demand_mean * 0.5 * (1 + random.gauss(0, variation)) 
               for _ in range(10)],
        "GG": [2000 + demand_mean * 0.3 * (1 + random.gauss(0, variation * 0.5)) 
               for _ in range(10)],
        
        # Costos unitarios
        "CTTL": [demand_mean * base_values['production_cost'] * 0.8 * 
                 (1 + random.gauss(0, variation)) for _ in range(10)],
        "CPP": [base_values['production_cost'] * 0.6 * (1 + random.gauss(0, variation * 0.1)) 
                for _ in range(10)],
        "CPV": [base_values['production_cost'] * 0.2 * (1 + random.gauss(0, variation * 0.1)) 
                for _ in range(10)],
        "CPI": [base_values['production_cost'] * 0.1 * (1 + random.gauss(0, variation * 0.1)) 
                for _ in range(10)],
        "CPMO": [base_values['production_cost'] * 0.15 * (1 + random.gauss(0, variation * 0.1)) 
                 for _ in range(10)],
        "CUP": [base_values['production_cost'] * (1 + random.gauss(0, variation * 0.05)) 
                for _ in range(10)],
        
        # Factores y márgenes
        "FU": [base_values['efficiency'] * (1 + random.gauss(0, variation * 0.02)) 
               for _ in range(10)],
        "TG": [demand_mean * base_values['production_cost'] * 0.9 * 
               (1 + random.gauss(0, variation)) for _ in range(10)],
        "IB": [demand_mean * base_values['price'] * 0.95 * 
               (1 + random.gauss(0, variation * 0.2)) for _ in range(10)],
        "MB": [(base_values['price'] - base_values['production_cost']) * demand_mean * 0.8 * 
               (1 + random.gauss(0, variation * 0.3)) for _ in range(10)],
        
        # Indicadores de rendimiento
        "RI": [demand_mean * 0.3 * (1 + random.gauss(0, variation)) for _ in range(10)],
        "RTI": [demand_mean * 0.25 * (1 + random.gauss(0, variation * 1.2)) for _ in range(10)],
        "RTC": [0.15 * (1 + random.gauss(0, variation * 0.5)) for _ in range(10)],
        
        # Recursos humanos
        "PM": [800 + demand_mean * 0.1 * (1 + random.gauss(0, variation * 0.3)) 
               for _ in range(10)],
        "PE": [1200 + demand_mean * 0.15 * (1 + random.gauss(0, variation * 0.2)) 
               for _ in range(10)],
        "HO": [8 + random.gauss(0, 0.5) for _ in range(10)],
        "CHO": [25 * (1 + random.gauss(0, variation * 0.1)) for _ in range(10)],
        
        # Capital
        "CA": [10000 + demand_mean * 2 * (1 + random.gauss(0, variation * 0.4)) 
               for _ in range(10)],
    }


def create_demand_instances(simulation: Simulation, last_demand_mean: float) -> None:
    """
    Crear instancias de demanda actual y predicha
    
    Args:
        simulation: Instancia de la simulación
        last_demand_mean: Última media de demanda calculada
    """
    try:
        product = simulation.fk_questionary_result.fk_questionary.fk_product
        
        # Usar el primer valor del historial o un valor por defecto
        current_demand_value = (
            simulation.demand_history[0] 
            if simulation.demand_history 
            else last_demand_mean
        )
        
        # Crear demanda actual
        demand_instance, _ = Demand.objects.get_or_create(
            fk_simulation=simulation,
            is_predicted=False,
            defaults={
                'quantity': current_demand_value,
                'fk_product': product,
                'is_active': True
            }
        )

        # Crear demanda predicha (con un margen de predicción)
        prediction_factor = 1.05  # Predicción 5% mayor
        predicted_demand_value = last_demand_mean * prediction_factor
        
        demand_predicted_instance, _ = Demand.objects.get_or_create(
            fk_simulation=simulation,
            is_predicted=True,
            defaults={
                'quantity': predicted_demand_value,
                'fk_product': product,
                'is_active': True
            }
        )

        # Crear comportamiento de demanda
        DemandBehavior.objects.get_or_create(
            current_demand=demand_instance,
            predicted_demand=demand_predicted_instance,
            defaults={'is_active': True}
        )
        
        logger.info(f"Demand instances created for simulation {simulation.id}")
        
    except Exception as e:
        logger.error(f"Error creating demand instances: {str(e)}")
        raise


def pages_faqs(request):
    """Vista para página de preguntas frecuentes"""
    return render(request, 'pages/faqs.html', {
        'title': 'Preguntas Frecuentes'
    })


def pagina_error_404(request, exception):
    """Vista personalizada para error 404"""
    return render(request, 'pages/404.html', {
        'title': 'Página no encontrada'
    }, status=404)


def pagina_error_500(request):
    """Vista personalizada para error 500"""
    return render(request, 'pages/500.html', {
        'title': 'Error del servidor'
    }, status=500)


# Vistas basadas en clase con context mejorado
class PagesMaintenanceView(PagesView):
    template_name = "pages/maintenance.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Sitio en Mantenimiento'
        return context


class PagesComingSoonView(PagesView):
    template_name = "pages/coming-soon.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Próximamente'
        context['launch_date'] = datetime.now() + timedelta(days=30)
        return context


class PagesPrivacyPolicyView(PagesView):
    template_name = "pages/privacy-policy.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Política de Privacidad'
        context['last_updated'] = datetime(2023, 11, 20)
        return context


class PagesTermsConditionsView(PagesView):
    template_name = "pages/term-conditions.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Términos y Condiciones'
        context['last_updated'] = datetime(2023, 11, 20)
        return context


# Instancias de vistas
pages_maintenance = PagesMaintenanceView.as_view()
pages_coming_soon = PagesComingSoonView.as_view()
pages_privacy_policy = PagesPrivacyPolicyView.as_view()
pages_terms_conditions = PagesTermsConditionsView.as_view()