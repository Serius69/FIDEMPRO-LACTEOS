# views.py - Versión adaptada
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.core.exceptions import MultipleObjectsReturned
from django.http import Http404, JsonResponse
from django.contrib.auth.models import User
from django.db import transaction
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect

from .forms import RegisterElementsForm
from user.models import UserProfile
from business.models import Business
from product.models import Product, Area
from variable.models import Variable, Equation
from questionary.models import Questionary, Question, QuestionaryResult, Answer
from simulate.models import Simulation, ResultSimulation, Demand, DemandBehavior, ProbabilisticDensityFunction

# Importar los datos mejorados
try:
    from product.data.products_data import products_data as enhanced_products_data
except ImportError:
    from product.data.products_data import products_data as enhanced_products_data

from product.data.areas_data import areas_data
from questionary.data.questionary_data import questionary_data, question_data

# Importar datos mejorados de questionary_result_data
try:
    from questionary.data.questionary_result_data import (
        get_realistic_answers,
        answer_data_leche,
        answer_data_queso, 
        answer_data_yogur
    )
except ImportError:
    from questionary.data.questionary_result_data import answer_data

# Importar datos mejorados de variables y ecuaciones
from variable.variables_data import variables_data
from variable.equations_data import equations_data

# Importar datos mejorados de simulación
try:
    from simulate.data.simulate_data import (
        pdf_data,
        simulation_data_leche,
        simulation_data_queso,
        simulation_data_yogur,
        get_simulations_by_product,
        pdf_config_by_product,
        create_complete_simulation
    )
except ImportError:
    from simulate.data.simulate_data import simulation_data

# Importar utilidades de integración si existen
try:
    from .integration_helpers import (
        load_equations_into_model,
        load_variables_into_model,
        load_questionary_answers,
        create_simulation_from_config,
        generate_simulation_results,
        validate_data_coherence
    )
except ImportError:
    pass

import random
import numpy as np
from datetime import datetime, timedelta
import logging
from django.conf import settings
import os
from typing import Optional, Dict, Any, List
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


class PagesView(TemplateView):
    """Vista base para páginas estáticas"""
    pass


def get_media_path(relative_path: str) -> str:
    """
    Obtener la ruta completa de un archivo en media
    
    Args:
        relative_path: Ruta relativa dentro de media
        
    Returns:
        Ruta completa del archivo
    """
    return os.path.join(settings.MEDIA_ROOT, relative_path)


def copy_existing_image(source_name: str, dest_folder: str, dest_name: str) -> str:
    """
    Copiar una imagen existente desde la carpeta media o crear un placeholder
    
    Args:
        source_name: Nombre del archivo fuente
        dest_folder: Carpeta destino (relative a media)
        dest_name: Nombre del archivo destino
        
    Returns:
        Ruta relativa del archivo copiado o placeholder
    """
    try:
        # Crear directorio destino si no existe
        dest_dir = os.path.join(settings.MEDIA_ROOT, dest_folder)
        os.makedirs(dest_dir, exist_ok=True)
        
        # Ruta del archivo destino
        dest_path = os.path.join(dest_dir, dest_name)
        
        # Si el archivo destino ya existe, retornar su ruta
        if os.path.exists(dest_path):
            return os.path.join(dest_folder, dest_name)
        
        # Buscar el archivo fuente en diferentes ubicaciones posibles
        possible_sources = [
            os.path.join(settings.MEDIA_ROOT, source_name),
            os.path.join(settings.MEDIA_ROOT, dest_folder, source_name),
            os.path.join(settings.MEDIA_ROOT, 'images', source_name),
            os.path.join(settings.MEDIA_ROOT, 'images', dest_folder, source_name),
            # Añadir más ubicaciones comunes
            os.path.join(settings.STATIC_ROOT or '', 'images', source_name) if settings.STATIC_ROOT else None,
            os.path.join(settings.STATICFILES_DIRS[0], 'images', source_name) if hasattr(settings, 'STATICFILES_DIRS') and settings.STATICFILES_DIRS else None,
        ]
        
        # Filtrar None values
        possible_sources = [path for path in possible_sources if path is not None]
        
        source_path = None
        
        # Buscar archivo exacto primero
        for path in possible_sources:
            if os.path.exists(path):
                source_path = path
                break
        
        # Si no se encuentra, buscar con diferentes extensiones
        if not source_path:
            extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
            name_without_ext = os.path.splitext(source_name)[0]
            
            for ext in extensions:
                for base_path in possible_sources:
                    if base_path:
                        test_path = os.path.join(os.path.dirname(base_path), name_without_ext + ext)
                        if os.path.exists(test_path):
                            source_path = test_path
                            break
                if source_path:
                    break
        
        # Si se encontró el archivo fuente, copiarlo
        if source_path and os.path.exists(source_path):
            shutil.copy2(source_path, dest_path)
            logger.info(f"Image copied from {source_path} to {dest_path}")
            return os.path.join(dest_folder, dest_name)
        
        # Si no se puede copiar, crear un placeholder simple
        logger.warning(f"Source image {source_name} not found, creating placeholder")
        create_placeholder_image(dest_path, dest_name)
        return os.path.join(dest_folder, dest_name)
    
    except Exception as e:
        logger.warning(f"Error copying image {source_name}: {str(e)}")
        # Crear placeholder en caso de error
        try:
            dest_dir = os.path.join(settings.MEDIA_ROOT, dest_folder)
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, dest_name)
            create_placeholder_image(dest_path, dest_name)
            return os.path.join(dest_folder, dest_name)
        except Exception as e2:
            logger.error(f"Error creating placeholder for {dest_name}: {str(e2)}")
            # Retornar ruta por defecto sin archivo físico
            return os.path.join(dest_folder, dest_name)



def create_placeholder_image(dest_path: str, filename: str) -> None:
    """
    Crear una imagen placeholder simple si PIL está disponible,
    de lo contrario crear un archivo de texto placeholder
    """
    try:
        # Intentar crear imagen con PIL
        from PIL import Image, ImageDraw, ImageFont
        
        # Crear imagen placeholder de 300x200 píxeles
        img = Image.new('RGB', (300, 200), color='#f0f0f0')
        draw = ImageDraw.Draw(img)
        
        # Añadir texto
        try:
            # Intentar usar fuente por defecto
            font = ImageFont.load_default()
        except:
            font = None
        
        text = f"Imagen\n{os.path.splitext(filename)[0]}"
        
        # Calcular posición del texto (centrado)
        if font:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            text_width, text_height = 100, 20
        
        x = (300 - text_width) // 2
        y = (200 - text_height) // 2
        
        draw.text((x, y), text, fill='#666666', font=font)
        
        # Guardar imagen
        img.save(dest_path, 'JPEG')
        logger.info(f"Placeholder image created: {dest_path}")
        
    except ImportError:
        # PIL no disponible, crear archivo de texto placeholder
        logger.warning("PIL not available, creating text placeholder")
        create_text_placeholder(dest_path, filename)
    except Exception as e:
        logger.warning(f"Error creating PIL placeholder: {str(e)}, creating text placeholder")
        create_text_placeholder(dest_path, filename)


def create_text_placeholder(dest_path: str, filename: str) -> None:
    """
    Crear un archivo de texto como placeholder
    """
    try:
        placeholder_content = f"""
Placeholder para imagen: {filename}
Creado automáticamente
Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Este archivo debe ser reemplazado por la imagen correspondiente.
        """.strip()
        
        # Cambiar extensión a .txt
        text_path = os.path.splitext(dest_path)[0] + '.txt'
        
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(placeholder_content)
            
        logger.info(f"Text placeholder created: {text_path}")
        
    except Exception as e:
        logger.error(f"Error creating text placeholder: {str(e)}")


@login_required
def register_elements(request):
    """
    Vista para mostrar el formulario de registro de elementos.
    Muestra un preview de los datos mejorados a crear antes de confirmar.
    """
    # Usar datos mejorados si están disponibles
    products_preview = enhanced_products_data if 'enhanced_products_data' in globals() else products_data
    
    preview_data = {
        'business': {
            'name': "Pyme Láctea",
            'location': "La Paz",
            'image_src': "business/pyme_lactea_default.jpg",
        },
        'products_preview': products_preview,
        'areas_preview': areas_data,
        'variable_preview': variables_data,  # Mostrar solo las primeras 20 para el preview
        'equation_preview': equations_data,  # Mostrar solo las primeras 20
        'questionarie_preview': questionary_data,
        'question_preview': question_data,  # Mostrar solo las primeras 10
        'simulate_preview': {
            'leche': simulation_data_leche if 'simulation_data_leche' in globals() else [],
            'queso': simulation_data_queso if 'simulation_data_queso' in globals() else [],
            'yogur': simulation_data_yogur if 'simulation_data_yogur' in globals() else [],
        },
        'pdf_preview': pdf_data if 'pdf_data' in globals() else [],
    }
    
    form = RegisterElementsForm()
    return render(request, 'pages/register_elements.html', {
        'form': form,
        'preview_data': preview_data,
        'title': 'Previsualización de Elementos'
    })


@login_required
@require_http_methods(["POST"])
@csrf_protect
@transaction.atomic
def register_elements_create(request):
    """
    Realiza la creación de los elementos del negocio para el usuario actual.
    Solo acepta métodos POST y requiere confirmación.
    """
    # Verificar que se envió la confirmación
    if not request.POST.get('confirm_setup'):
        messages.error(request, _('Solicitud inválida. Por favor, intente nuevamente.'))
        return redirect("dashboard:index")
    
    try:
        # Verificar si el usuario ya tiene un negocio configurado
        if hasattr(request.user, 'business') and request.user.business.exists():
            messages.warning(request, _('Ya tiene una configuración de negocio existente.'))
            return redirect("dashboard:index")
        
        # Crear el negocio y sus elementos
        logger.info(f"Iniciando creación de negocio para usuario {request.user.id}")
        
        business = create_and_save_business(request.user)
        logger.info(f"Negocio creado con ID: {business.id}")
        
        # Crear funciones de densidad probabilística
        create_probability_density_functions(business)
        
        # Registrar elementos de simulación
        register_elements_simulation(request)
        logger.info(f"Elementos de simulación registrados para usuario {request.user.id}")
        
        messages.success(
            request, 
            _(
                'Configuración creada exitosamente. '
                'Su negocio lácteo ha sido configurado con todos los elementos iniciales. '
                'Puede personalizar la información desde el panel de control.'
            )
        )
        
    except Exception as e:
        logger.error(f"Error creating business for user {request.user.id}: {str(e)}")
        messages.error(
            request, 
            _(
                'Error al crear la configuración del negocio. '
                'Por favor, contacte al soporte técnico si el problema persiste.'
            )
        )
        return redirect("dashboard:index")
    
    return redirect("dashboard:index")


def create_and_save_business(user: User) -> Business:
    """
    Crear y guardar business para un usuario, permitiendo múltiples negocios con nombres únicos.
    """
    try:
        # Generar nombre único
        base_name = "Pyme Láctea"
        name = base_name
        counter = 1

        while Business.objects.filter(fk_user=user, name=name).exists():
            counter += 1
            name = f"{base_name} #{counter}"

        # Usar imagen existente o crear placeholder
        image_src = copy_existing_image(
            "pyme_lactea_default.jpg",
            "business",
            "pyme_lactea_default.jpg"
        )

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
    Crear y guardar productos para un business usando datos mejorados
    """
    try:
        created_products = []
        
        # Usar datos mejorados si están disponibles
        products_to_create = enhanced_products_data if 'enhanced_products_data' in globals() else products_data

        for data in products_to_create:
            if not data.get('name'):
                logger.warning(f"Skipping product with incomplete data: {data}")
                continue

            # Mapear nombres a imágenes más específicas
            image_mapping = {
                'Leche': 'leche.jpg',
                'Leche Entera': 'leche_entera.jpg',
                'Leche Descremada': 'leche_descremada.jpg',
                'Queso': 'queso.jpg',
                'Queso Fresco': 'queso_fresco.jpg',
                'Queso Madurado': 'queso_madurado.jpg',
                'Yogur': 'yogur.jpg',
                'Yogur Natural': 'yogur_natural.jpg',
                'Yogur con Frutas': 'yogur_frutas.jpg'
            }
            
            # Usar mapeo específico o generar nombre de archivo
            source_image = image_mapping.get(data['name'])
            if not source_image:
                # Generar nombre de archivo basado en el nombre del producto
                clean_name = data['name'].lower().replace(' ', '_').replace('ñ', 'n')
                source_image = f"{clean_name}.jpg"
            
            # Usar función mejorada de copia de imagen
            image_src = copy_existing_image(
                source_image,
                "product",
                source_image
            )

            try:
                product = Product.objects.create(
                    name=data['name'],
                    description=data.get('description', ''),
                    image_src=image_src,
                    type=data.get('type', 1),
                    is_active=True,
                    fk_business=business,
                )
                created_products.append(product)

                # Crear componentes relacionados
                create_and_save_areas(product)
                create_variables_and_equations(product)
                create_and_save_questionary(product)
                
                logger.info(f"Product '{product.name}' created successfully")

            except Exception as e:
                logger.error(f"Error creating product '{data['name']}': {str(e)}")
                continue

        logger.info(f'{len(created_products)} products created successfully for business {business.id}')

    except Exception as e:
        logger.error(f"Error creating products for business {business.id}: {str(e)}")
        # En lugar de hacer raise, continuar con el proceso
        logger.info("Continuing with business creation despite product errors")



def create_and_save_areas(product: Product) -> None:
    """
    Crear y guardar áreas para un producto con manejo mejorado de imágenes
    """
    try:
        created_areas = []
        
        # Mapeo de áreas a imágenes existentes
        area_image_mapping = {
            'Abastecimiento': 'abastecimiento.jpg',
            'Inventario Insumos': 'inventario_insumos.jpg',
            'Producción': 'produccion.jpg',
            'Inspección': 'inspeccion.jpg',
            'Inventario Productos Finales': 'inventario_productos.jpg',
            'Distribución': 'distribucion.jpg',
            'Ventas': 'ventas.jpg',
            'Competencia': 'competencia.jpg',
            'Marketing': 'marketing.jpg',
            'Contabilidad': 'contabilidad.jpg',
            'Recursos Humanos': 'recursos_humanos.jpg',
            'Mantenimiento': 'mantenimiento.jpg'
        }

        for data in areas_data:
            if not data.get('name'):
                continue

            source_image = area_image_mapping.get(data['name'])
            if not source_image:
                # Generar nombre de archivo basado en el nombre del área
                clean_name = data['name'].lower().replace(' ', '_').replace('ñ', 'n')
                source_image = f"{clean_name}.jpg"

            # Usar función mejorada de copia de imagen
            image_src = copy_existing_image(
                source_image,
                "area",
                source_image
            )

            try:
                area = Area.objects.create(
                    name=data['name'],
                    description=data.get('description', ''),
                    params=data.get('params', {}),
                    image_src=image_src,
                    is_active=True,
                    fk_product=product,
                )
                created_areas.append(area)
                
            except Exception as e:
                logger.error(f"Error creating area '{data['name']}': {str(e)}")
                continue

        logger.info(f'{len(created_areas)} areas created successfully for product {product.id}')

    except Exception as e:
        logger.error(f"Error creating areas for product {product.id}: {str(e)}")
        # Continuar con el proceso
        logger.info("Continuing despite area creation errors")


def create_variables_and_equations(product: Product) -> None:
    """
    Crear variables y ecuaciones para un producto usando datos mejorados
    """
    try:
        # Si existe la función helper, usarla
        if 'load_variables_into_model' in globals():
            created_variables = load_variables_into_model(Variable, product)
            logger.info(f"{len(created_variables)} variables created using helper function")
        else:
            # Crear variables manualmente
            created_variables = []
            for data in variables_data:
                if not all([data.get('name'), data.get('initials'), data.get('type')]):
                    logger.warning(f"Skipping variable with incomplete data: {data}")
                    continue
                    
                # Usar imagen genérica para variables
                image_src = copy_existing_image(
                    "variable_default.jpg",
                    "variable",
                    f"{data.get('initials', 'VAR').lower()}.jpg"
                )
                
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
        
        # Crear ecuaciones
        if 'load_equations_into_model' in globals():
            areas = Area.objects.filter(fk_product=product)
            created_equations = load_equations_into_model(Equation, Variable, Area, product)
            logger.info(f"{len(created_equations)} equations created using helper function")
        else:
            create_equations(product)
            
    except Exception as e:
        logger.error(f"Error creating variables and equations for product {product.id}: {str(e)}")
        raise


def create_equations(product: Product) -> None:
    """
    Crear ecuaciones para un producto
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


def create_and_save_questionary(product: Product) -> None:
    """
    Crear cuestionario para un producto
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
            # Usar respuestas realistas según el producto
            product_name = questionary.fk_product.name.lower()
            
            if 'get_realistic_answers' in globals():
                # Usar función helper para obtener respuestas realistas
                answers_data = get_realistic_answers(product_name)
                created_answers = []
                
                questions = Question.objects.filter(
                    fk_questionary=questionary,
                    is_active=True
                )
                
                for answer_data in answers_data:
                    question = questions.filter(question=answer_data.get('question')).first()
                    if question:
                        answer_value = answer_data['answer']
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
                
                logger.info(f"{len(created_answers)} realistic answers created")
            else:
                # Usar método original
                create_and_save_answers(questionary_result)
            
            # Crear simulación con datos mejorados
            create_enhanced_simulation(questionary_result)
            
            logger.info(f'Questionary result created for questionary {questionary.id}')
            return True
        else:
            logger.info(f'Questionary result already exists for questionary {questionary.id}')
            return False

    except Exception as e:
        logger.error(f"Error creating questionary result: {str(e)}")
        return False


def create_enhanced_simulation(questionary_result: QuestionaryResult) -> None:
    """
    Crear simulación mejorada para un resultado de cuestionario
    """
    try:
        product_name = questionary_result.fk_questionary.fk_product.name.lower()
        
        # Obtener configuración PDF específica del producto
        if 'pdf_config_by_product' in globals():
            pdf_config = pdf_config_by_product.get(product_name, {})
        else:
            pdf_config = {}
        
        # Crear o obtener instancia FDP
        business = questionary_result.fk_questionary.fk_product.fk_business
        
        if pdf_config:
            fdp_instance, _ = ProbabilisticDensityFunction.objects.get_or_create(
                distribution_type=pdf_config.get('distribution_type', 1),
                fk_business=business,
                defaults={
                    'name': pdf_config.get('name', f'Distribución {product_name}'),
                    'mean_param': pdf_config.get('mean_param'),
                    'std_dev_param': pdf_config.get('std_dev_param'),
                    'lambda_param': pdf_config.get('lambda_param'),
                    'shape_param': pdf_config.get('shape_param'),
                    'scale_param': pdf_config.get('scale_param'),
                    'min_param': pdf_config.get('min_param'),
                    'max_param': pdf_config.get('max_param'),
                    'is_active': True
                }
            )
        else:
            fdp_instance = business.probability_distributions.first()
        
        if not fdp_instance:
            logger.warning(f"No FDP instance available for business {business.id}")
            return
        
        # Obtener datos de simulación específicos del producto
        simulations_data = []
        if product_name == 'leche' and 'simulation_data_leche' in globals():
            simulations_data = simulation_data_leche
        elif product_name == 'queso' and 'simulation_data_queso' in globals():
            simulations_data = simulation_data_queso
        elif product_name == 'yogur' and 'simulation_data_yogur' in globals():
            simulations_data = simulation_data_yogur
        
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
                
                # Generar resultados de simulación
                if 'generate_simulation_results' in globals():
                    results = generate_simulation_results(ResultSimulation, simulation, product_name)
                    logger.info(f"{len(results)} simulation results generated")
                else:
                    create_enhanced_result_simulations(simulation, sim_data)
        else:
            # Crear simulación por defecto
            create_and_save_simulation(questionary_result)
        
    except Exception as e:
        logger.error(f"Error creating enhanced simulation: {str(e)}")
        raise


def create_enhanced_result_simulations(simulation: Simulation, sim_data: dict) -> None:
    """
    Crear resultados de simulación mejorados basados en datos específicos
    """
    try:
        current_date = simulation.date_created
        result_simulations = []
        
        # Obtener parámetros esperados
        expected = sim_data.get('expected_results', {})
        params = sim_data.get('parameters', {})
        
        base_demand = expected.get('demand_mean', 2500)
        demand_std = expected.get('demand_std_deviation', 250)
        
        for day in range(int(simulation.quantity_time)):
            # Aplicar tendencia de crecimiento
            growth_factor = (1 + params.get('growth_rate', 0)) ** (day / 30)
            seasonal_factor = params.get('seasonality_factor', 1.0)
            
            # Calcular demanda diaria
            daily_demand = base_demand * growth_factor * seasonal_factor
            daily_demand += np.random.normal(0, demand_std * 0.1)
            
            # Generar variables correlacionadas
            variables = generate_realistic_variables(
                daily_demand,
                params,
                expected,
                simulation.fk_questionary_result.fk_questionary.fk_product.name
            )
            
            current_date += timedelta(days=1)
            
            result_simulation = ResultSimulation(
                demand_mean=daily_demand,
                demand_std_deviation=demand_std,
                date=current_date,
                variables=variables,
                fk_simulation=simulation,
                is_active=True
            )
            result_simulations.append(result_simulation)
        
        # Bulk create
        ResultSimulation.objects.bulk_create(result_simulations)
        
        # Crear demandas
        create_demand_instances(simulation, daily_demand)
        
        logger.info(f"Created {len(result_simulations)} enhanced result simulations")
        
    except Exception as e:
        logger.error(f"Error creating enhanced result simulations: {str(e)}")
        raise


def generate_realistic_variables(demand: float, params: dict, expected: dict, product_name: str) -> dict:
    """
    Generar variables realistas basadas en el tipo de producto y parámetros
    """
    # Precios base por producto
    price_map = {
        'leche': 15.50,
        'queso': 85.00,
        'yogur': 22.00
    }
    
    price = price_map.get(product_name.lower(), 20.0)
    profit_margin = expected.get('profit_margin', 0.20)
    efficiency = params.get('production_efficiency', 0.85)
    
    # Calcular variables financieras
    revenue = demand * price
    costs = revenue * (1 - profit_margin)
    
    return {
        # Variables de producción
        "TPV": demand * (1 - params.get('waste_percentage', 0.03)),
        "TPPRO": demand * 1.05,
        "DI": max(0, demand * 0.02),
        "VPC": demand / 50,
        
        # Variables financieras
        "IT": revenue,
        "GT": costs,
        "NR": profit_margin,
        "MB": profit_margin * 1.1,
        "RI": expected.get('roi', 0.25),
        
        # Variables de eficiencia
        "FU": efficiency,
        "PE": demand / 15,
        "PM": 0.15 + params.get('market_share_growth', 0),
        
        # Variables de costos
        "CTAI": costs * 0.6,
        "GO": costs * 0.2,
        "GG": costs * 0.15,
        "TG": costs * 0.95,
        
        # Otras variables importantes
        "CPROD": demand * 1.2,
        "IPF": demand * 1.5,
        "II": demand * 2.0,
        "RTI": 0.67,
        "CA": revenue * 0.02,
    }


def create_probability_density_functions(business: Business) -> None:
    """
    Crear funciones de densidad probabilística para el negocio
    """
    try:
        if 'pdf_data' in globals():
            # Usar datos de PDF mejorados
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
            # Usar método original del signal
            pass
            
    except Exception as e:
        logger.error(f"Error creating PDF instances: {str(e)}")


# Función principal para registrar todos los datos de ejemplo
@login_required
@require_http_methods(["POST"])
def register_all_example_data(request):
    """
    Función para registrar todos los datos de ejemplo de una vez
    """
    try:
        with transaction.atomic():
            # Validar que no exista configuración previa
            if hasattr(request.user, 'business') and request.user.business.exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Ya existe una configuración de negocio para este usuario'
                })
            
            # Validar coherencia de datos si está disponible
            if 'validate_data_coherence' in globals():
                validation = validate_data_coherence()
                if not validation['valid']:
                    logger.error(f"Data validation failed: {validation['errors']}")
                    return JsonResponse({
                        'success': False,
                        'message': 'Error en la validación de datos',
                        'errors': validation['errors']
                    })
            
            # Crear negocio
            business = create_and_save_business(request.user)
            
            # Crear funciones de densidad probabilística
            create_probability_density_functions(business)
            
            # Obtener productos creados
            products = Product.objects.filter(fk_business=business)
            
            stats = {
                'business': 1,
                'products': products.count(),
                'areas': Area.objects.filter(fk_product__in=products).count(),
                'variables': Variable.objects.filter(fk_product__in=products).count(),
                'equations': Equation.objects.filter(fk_area__fk_product__in=products).count(),
                'questionaries': 0,
                'questions': 0,
                'answers': 0,
                'simulations': 0,
                'results': 0
            }
            
            # Crear cuestionarios y simulaciones
            for product in products:
                questionaries = Questionary.objects.filter(fk_product=product)
                stats['questionaries'] += questionaries.count()
                
                for questionary in questionaries:
                    stats['questions'] += Question.objects.filter(fk_questionary=questionary).count()
                    
                    # Crear resultado de cuestionario con respuestas realistas
                    if create_and_save_questionary_result(questionary):
                        questionary_result = QuestionaryResult.objects.filter(
                            fk_questionary=questionary
                        ).latest('date_created')
                        
                        stats['answers'] += Answer.objects.filter(
                            fk_questionary_result=questionary_result
                        ).count()
                        
                        # Contar simulaciones creadas
                        simulations = Simulation.objects.filter(
                            fk_questionary_result=questionary_result
                        )
                        stats['simulations'] += simulations.count()
                        
                        # Contar resultados de simulación
                        for simulation in simulations:
                            stats['results'] += ResultSimulation.objects.filter(
                                fk_simulation=simulation
                            ).count()
            
            logger.info(f"Example data registered successfully: {stats}")
            
            return JsonResponse({
                'success': True,
                'message': 'Datos de ejemplo registrados exitosamente',
                'stats': stats
            })
            
    except Exception as e:
        logger.error(f"Error registering example data: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error al registrar datos: {str(e)}'
        })


def register_elements_simulation(request, user=None):
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


def create_and_save_answers(questionary_result: QuestionaryResult) -> None:
    """
    Crear respuestas para un resultado de cuestionario
    """
    try:
        created_answers = []
        questions = Question.objects.filter(
            fk_questionary=questionary_result.fk_questionary,
            is_active=True
        )
        
        # Usar answer_data genérico si no hay datos específicos
        answers_to_use = answer_data if 'answer_data' in globals() else []
        
        for data in answers_to_use:
            question = get_question_by_text(data.get('question'), questions)
            if question and data.get('answer'):
                answer, created = Answer.objects.get_or_create(
                    fk_question=question,
                    fk_questionary_result=questionary_result,
                    defaults={
                        'answer': str(data['answer']),
                        'is_active': True
                    }
                )
                if created:
                    created_answers.append(answer)
                    
        logger.info(f"{len(created_answers)} answers created for questionary result {questionary_result.id}")
                
    except Exception as e:
        logger.error(f"Error creating answers: {str(e)}")
        raise


def create_and_save_simulation(questionary_result: QuestionaryResult) -> None:
    """
    Crear simulación para un resultado de cuestionario (fallback)
    """
    try:
        # Obtener FDP instance
        fdp_instance = questionary_result.fk_questionary.fk_product.fk_business.probability_distributions.first()
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
                'unit_time': 'days',
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


def create_and_save_questions(questionary: Questionary) -> None:
    """
    Crear preguntas para un cuestionario
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


# Mantener funciones auxiliares existentes
def get_variable_by_initials(variable_initials: Optional[str], product_id: int) -> Optional[Variable]:
    """
    Obtener variable por iniciales y producto
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


def get_question_by_text(question_text: Optional[str], questions_queryset=None) -> Optional[Question]:
    """
    Obtener pregunta por texto
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