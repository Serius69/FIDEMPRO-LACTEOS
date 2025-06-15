"""
views/business_creator.py - Creación de negocio, productos y componentes relacionados
"""
import logging
from django.contrib.auth.models import User
from django.http import Http404

from business.models import Business
from product.models import Product, Area
from variable.models import Variable, Equation
from questionary.models import Questionary, Question

from .base import copy_existing_image
from .questionary_creator import create_and_save_questions

logger = logging.getLogger(__name__)


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
        # Importar datos
        from product.data.product_test_data import products_data
        
        created_products = []
        
        for data in products_data:
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
                'Yogur con Frutas': 'yogur_frutas.jpg',
                'Mantequilla': 'mantequilla.jpg',
                'Crema de Leche': 'crema_leche.jpg',
                'Leche Deslactosada': 'leche_deslactosada.jpg',
                'Dulce de Leche': 'dulce_leche.jpg'
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
        logger.info("Continuing with business creation despite product errors")


def create_and_save_areas(product: Product) -> None:
    """
    Crear y guardar áreas para un producto con manejo mejorado de imágenes
    """
    try:
        from product.data.area_test_data import areas_data
        
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
            'Mantenimiento': 'mantenimiento.jpg',
            'Control de Calidad': 'control_calidad.jpg'
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
        logger.info("Continuing despite area creation errors")


def create_variables_and_equations(product: Product) -> None:
    """
    Crear variables y ecuaciones para un producto usando datos mejorados
    """
    try:
        from variable.data.variable_test_data import variables_data
        
        created_variables = []
        
        # Crear variables
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
        
        logger.info(f"{len(created_variables)} variables created for product {product.id}")
        
        # Crear ecuaciones
        create_equations(product)
            
    except Exception as e:
        logger.error(f"Error creating variables and equations for product {product.id}: {str(e)}")
        raise


def create_equations(product: Product) -> None:
    """
    Crear ecuaciones para un producto
    """
    try:
        from variable.data.equation_test_data import equations_data
        
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
        from questionary.data.questionary_test_data import questionary_data
        
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


# Funciones auxiliares
def get_variable_by_initials(variable_initials: str, product_id: int):
    """Obtener variable por iniciales y producto"""
    if variable_initials is None:
        return None
    
    try:
        return Variable.objects.get(initials=variable_initials, fk_product_id=product_id)
    except Variable.DoesNotExist:
        raise Http404(f"Variable with initials '{variable_initials}' for product id '{product_id}' does not exist.")
    except Variable.MultipleObjectsReturned:
        logger.warning(f"Multiple variables found with initials '{variable_initials}' for product {product_id}. Using first one.")
        return Variable.objects.filter(initials=variable_initials, fk_product_id=product_id).first()


def get_area_by_name(area_name: str, product_id: int) -> Area:
    """Obtener área por nombre y producto"""
    try:
        return Area.objects.get(name=area_name, fk_product_id=product_id)
    except Area.DoesNotExist:
        raise Http404(f"Area with name '{area_name}' for product id '{product_id}' does not exist.")
    except Area.MultipleObjectsReturned:
        logger.warning(f"Multiple areas found with name '{area_name}' for product {product_id}. Using first one.")
        return Area.objects.filter(name=area_name, fk_product_id=product_id).first()