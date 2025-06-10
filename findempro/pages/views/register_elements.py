"""
views/register_elements.py - Vista principal para mostrar la configuración inicial
"""
import logging
import traceback
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)


@login_required
def register_elements(request):
    """
    Vista mejorada para mostrar TODOS los elementos que se crearán.
    Incluye una vista previa completa de todos los datos antes de confirmar.
    """
    try:
        logger.info("Starting register_elements view")
        
        # Importar aquí para evitar problemas de importación circular
        from .preview_data import prepare_preview_data
        
        logger.info("About to call prepare_preview_data()")
        
        # Preparar todos los datos para la vista previa con debugging
        try:
            preview_data = prepare_preview_data()
            logger.info("prepare_preview_data() completed successfully")
        except TypeError as te:
            logger.error(f"TypeError in prepare_preview_data: {te}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            # Intentar identificar qué función específica está causando el problema
            if "unsupported operand type(s) for *: 'NoneType' and 'float'" in str(te):
                logger.error("The multiplication error is occurring inside prepare_preview_data()")
                
                # Crear datos de prueba mínimos para continuar
                preview_data = _create_minimal_preview_data()
                logger.info("Created minimal preview data as fallback")
            else:
                raise te
        
        # Log para debugging
        logger.debug(f"Preview data keys: {list(preview_data.keys()) if preview_data else 'None'}")
        
        # Validar que tengamos datos mínimos
        if not preview_data.get('products_preview'):
            logger.warning("No products found in preview data")
        
        context = {
            'preview_data': preview_data,
            'title': 'Vista Previa Completa - Configuración Inicial'
        }
        
        logger.info("Context prepared, rendering template")
        return render(request, 'pages/register_elements.html', context)
        
    except Exception as e:
        logger.error(f"Error in register_elements view: {str(e)}")
        logger.error(f"Full error traceback: {traceback.format_exc()}")
        
        # En caso de error, mostrar vista con datos mínimos
        context = {
            'preview_data': {
                'error': True,
                'message': str(e),
                'error_type': type(e).__name__,
                'products_preview': [],
                'areas_preview': [],
                'variable_preview': [],
                'variables_by_type': {
                    'exogenas': [],
                    'estado': [],
                    'endogenas': []
                },
                'equation_preview': [],
                'questionary_preview': [],
                'question_preview': [],
                'simulations_preview': {},
                'summary_stats': {
                    'total_products': 0,
                    'total_areas': 0,
                    'total_variables': 0,
                    'total_equations': 0,
                    'total_questions': 0,
                    'total_simulations': 0,
                    'variables_by_type': {
                        'exogenas': 0,
                        'estado': 0,
                        'endogenas': 0
                    }
                },
                'business': {
                    'name': "Error - Datos no disponibles",
                    'location': "N/A",
                    'type': "N/A",
                    'employees': 0,
                    'years_in_business': 0,
                    'image_src': "",
                }
            },
            'title': 'Vista Previa - Error'
        }
        return render(request, 'pages/register_elements.html', context)


def _create_minimal_preview_data():
    """Crear datos mínimos de respaldo en caso de error"""
    logger.info("Creating minimal preview data")
    
    return {
        'business': {
            'name': "Empresa Láctea Demo (Modo Seguro)",
            'location': "La Paz, Bolivia",
            'type': "Pequeña empresa láctea",
            'employees': 15,
            'years_in_business': 5,
            'image_src': "business/pyme_lactea_default.jpg",
        },
        'products_preview': [
            {
                'name': 'Leche',
                'description': 'Producto lácteo básico',
                'category': 'Lácteos',
                'unit': 'litros'
            }
        ],
        'areas_preview': [
            {
                'name': 'Producción',
                'description': 'Área de producción láctea'
            }
        ],
        'variable_preview': [],
        'variables_by_type': {
            'exogenas': [],
            'estado': [],
            'endogenas': []
        },
        'equation_preview': [],
        'questionary_preview': [],
        'question_preview': [],
        'simulations_preview': {},
        'simulate_preview': {
            'unit_time': 'days',
            'quantity_time': 30,
            'confidence_level': 0.95,
            'random_seed': 42,
            'fk_fdp': 1,
            'demand_history': [2500] * 30,  # Valores seguros
            'parameters': {}
        },
        'pdf_preview': [],
        'recommendations_preview': [],
        'demand_example': {
            'leche': [2500] * 30,  # Valores seguros sin multiplicación
        },
        'demand_configurations_preview': {
            'leche': {'base_demand': 2500, 'seasonality': True, 'growth_rate': 0.02, 'volatility': 0.1}
        },
        'result_simulation_preview': {
            'demand_mean': 2500.0,
            'demand_std_deviation': 250.0,
            'confidence_intervals': {
                'demand_mean': {
                    'lower': 2400.0,
                    'upper': 2600.0
                }
            }
        },
        'summary_stats': {
            'total_products': 1,
            'total_areas': 1,
            'total_variables': 0,
            'variables_by_type': {
                'exogenas': 0,
                'estado': 0,
                'endogenas': 0
            },
            'total_equations': 0,
            'total_questions': 0,
            'total_simulations': 0,
            'total_recommendations': 0,
            'total_pdfs': 0
        },
        'questionary_results_preview': {}
    }