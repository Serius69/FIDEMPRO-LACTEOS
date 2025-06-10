"""
views/preview_data.py - Preparación de datos para la vista previa (Versión Segura)
"""
import logging
import random
import traceback
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def safe_import(module_path: str, item_name: str, default=None):
    """Importación segura con fallback y logging detallado"""
    try:
        logger.debug(f"Attempting to import {item_name} from {module_path}")
        module = __import__(module_path, fromlist=[item_name])
        result = getattr(module, item_name, default)
        logger.debug(f"Successfully imported {item_name}")
        return result
    except (ImportError, AttributeError) as e:
        logger.warning(f"Could not import {item_name} from {module_path}: {e}")
        return default
    except Exception as e:
        logger.error(f"Unexpected error importing {item_name} from {module_path}: {e}")
        return default


def prepare_preview_data() -> Dict[str, Any]:
    """
    Preparar todos los datos necesarios para la vista previa
    Versión segura que evita operaciones de multiplicación problemáticas
    """
    logger.info("Starting prepare_preview_data()")
    
    try:
        # Importar datos con manejo de errores MUY granular
        logger.debug("Importing products_data")
        products_data = safe_import('product.data.products_data', 'products_data', [])
        
        logger.debug("Importing areas_data")
        areas_data = safe_import('product.data.areas_data', 'areas_data', [])
        area_relationships = safe_import('product.data.areas_data', 'area_relationships', {})
        area_performance_benchmarks = safe_import('product.data.areas_data', 'area_performance_benchmarks', {})
        
        logger.debug("Importing product categories and metrics")
        product_categories = safe_import('product.data.products_data', 'product_categories', {})
        product_metrics = safe_import('product.data.products_data', 'product_metrics', {})
        
        logger.debug("Importing variables and equations")
        variables_data = safe_import('variable.variables_data', 'variables_data', [])
        equations_data = safe_import('variable.equations_data', 'equations_data', [])
        
        logger.debug("Importing questionary data")
        questionary_data = safe_import('questionary.data.questionary_data', 'questionary_data', [])
        question_data = safe_import('questionary.data.questionary_data', 'question_data', [])
        
        # Importar simulaciones con logging detallado
        logger.debug("Importing simulation data")
        simulation_data_leche = safe_import('simulate.data.simulate_data', 'simulation_data_leche', [])
        simulation_data_queso = safe_import('simulate.data.simulate_data', 'simulation_data_queso', [])
        simulation_data_yogur = safe_import('simulate.data.simulate_data', 'simulation_data_yogur', [])
        simulation_data_mantequilla = safe_import('simulate.data.simulate_data', 'simulation_data_mantequilla', [])
        simulation_data_crema = safe_import('simulate.data.simulate_data', 'simulation_data_crema', [])
        simulation_data_leche_deslactosada = safe_import('simulate.data.simulate_data', 'simulation_data_leche_deslactosada', [])
        simulation_data_dulce_leche = safe_import('simulate.data.simulate_data', 'simulation_data_dulce_leche', [])
        
        logger.debug("Importing PDF and recommendation data")
        pdf_data = safe_import('simulate.data.simulate_data', 'pdf_data', [])
        get_pdf_config_by_product = safe_import('simulate.data.simulate_data', 'get_pdf_config_by_product', lambda x: {})
        
        # Importar respuestas con logging
        logger.debug("Importing answer data")
        answer_data_leche = safe_import('questionary.data.questionary_result_data', 'answer_data_leche', [])
        answer_data_queso = safe_import('questionary.data.questionary_result_data', 'answer_data_queso', [])
        answer_data_yogur = safe_import('questionary.data.questionary_result_data', 'answer_data_yogur', [])
        answer_data_mantequilla = safe_import('questionary.data.questionary_result_data', 'answer_data_mantequilla', [])
        answer_data_crema = safe_import('questionary.data.questionary_result_data', 'answer_data_crema', [])
        answer_data_leche_deslactosada = safe_import('questionary.data.questionary_result_data', 'answer_data_leche_deslactosada', [])
        answer_data_dulce_leche = safe_import('questionary.data.questionary_result_data', 'answer_data_dulce_leche', [])
        
        recommendation_data = safe_import('finance.data.finance_data', 'recommendation_data', [])
        
        logger.debug("Processing products data")
        # Preparar datos de productos con información adicional
        products_preview = []
        try:
            for product in products_data:
                product_info = product.copy()
                # Agregar métricas si existen
                if product_metrics and product.get('name') in product_metrics:
                    product_info['metrics'] = product_metrics[product['name']]
                # Agregar categorías
                if product_categories:
                    product_info['categories'] = [cat for cat, prods in product_categories.items() 
                                                 if product.get('name') in prods]
                products_preview.append(product_info)
        except Exception as e:
            logger.error(f"Error processing products: {e}")
            products_preview = []
        
        logger.debug("Processing areas data")
        # Preparar datos de áreas con relaciones
        areas_preview = []
        try:
            for area in areas_data:
                area_info = area.copy()
                # Agregar relaciones
                if area_relationships and area.get('name') in area_relationships:
                    area_info['relationships'] = area_relationships[area['name']]
                # Agregar benchmarks si existen
                if area_performance_benchmarks and area.get('name') in area_performance_benchmarks:
                    area_info['benchmarks'] = area_performance_benchmarks[area['name']]
                areas_preview.append(area_info)
        except Exception as e:
            logger.error(f"Error processing areas: {e}")
            areas_preview = []
        
        logger.debug("Organizing variables by type")
        # Organizar variables por tipo
        variables_by_type = {
            'exogenas': [],
            'estado': [],
            'endogenas': []
        }
        try:
            variables_by_type = {
                'exogenas': [v for v in variables_data if v.get('type') == 3],
                'estado': [v for v in variables_data if v.get('type') == 2],
                'endogenas': [v for v in variables_data if v.get('type') == 1]
            }
        except Exception as e:
            logger.error(f"Error organizing variables: {e}")
        
        logger.debug("Preparing simulations preview")
        # Preparar simulaciones con configuración completa
        simulations_preview = {}
        try:
            simulations_preview = {
                'leche': {
                    'simulations': simulation_data_leche or _generate_safe_default_simulations('leche'),
                    'pdf_config': get_pdf_config_by_product('leche') if callable(get_pdf_config_by_product) else {},
                    'result_data': {}
                },
                'queso': {
                    'simulations': simulation_data_queso or _generate_safe_default_simulations('queso'),
                    'pdf_config': get_pdf_config_by_product('queso') if callable(get_pdf_config_by_product) else {},
                    'result_data': {}
                },
                'yogur': {
                    'simulations': simulation_data_yogur or _generate_safe_default_simulations('yogur'),
                    'pdf_config': get_pdf_config_by_product('yogur') if callable(get_pdf_config_by_product) else {},
                    'result_data': {}
                },
                'mantequilla': {
                    'simulations': simulation_data_mantequilla or _generate_safe_default_simulations('mantequilla'),
                    'pdf_config': get_pdf_config_by_product('mantequilla') if callable(get_pdf_config_by_product) else {},
                    'result_data': {}
                },
                'crema': {
                    'simulations': simulation_data_crema or _generate_safe_default_simulations('crema'),
                    'pdf_config': get_pdf_config_by_product('crema') if callable(get_pdf_config_by_product) else {},
                    'result_data': {}
                },
                'leche_deslactosada': {
                    'simulations': simulation_data_leche_deslactosada or _generate_safe_default_simulations('leche_deslactosada'),
                    'pdf_config': get_pdf_config_by_product('leche_deslactosada') if callable(get_pdf_config_by_product) else {},
                    'result_data': {}
                },
                'dulce_leche': {
                    'simulations': simulation_data_dulce_leche or _generate_safe_default_simulations('dulce_leche'),
                    'pdf_config': get_pdf_config_by_product('dulce_leche') if callable(get_pdf_config_by_product) else {},
                    'result_data': {}
                }
            }
        except Exception as e:
            logger.error(f"Error in simulations preview: {e}")
            logger.error(f"Simulations error traceback: {traceback.format_exc()}")
            simulations_preview = {}
        
        logger.debug("Processing questions with answers")
        # Procesar preguntas con respuestas de ejemplo
        questions_with_answers = []
        try:
            for question in question_data:
                q_info = question.copy()
                # Buscar respuestas de ejemplo para cada producto
                q_info['sample_answers'] = {}
                
                answer_sources = {
                    'leche': answer_data_leche,
                    'queso': answer_data_queso, 
                    'yogur': answer_data_yogur,
                    'mantequilla': answer_data_mantequilla,
                    'crema': answer_data_crema,
                    'leche_deslactosada': answer_data_leche_deslactosada,
                    'dulce_leche': answer_data_dulce_leche
                }
                
                for product, answers in answer_sources.items():
                    if answers:
                        for answer in answers:
                            if answer.get('question') == question.get('question'):
                                q_info['sample_answers'][product] = answer
                                break
                
                questions_with_answers.append(q_info)
        except Exception as e:
            logger.error(f"Error processing questions: {e}")
            questions_with_answers = []
        
        logger.debug("Creating demand examples (SAFE VERSION)")
        # Datos de ejemplo de demanda - VERSIÓN COMPLETAMENTE SEGURA
        demand_example = {}
        try:
            # Usar valores fijos sin ninguna multiplicación
            demand_example = {
                'leche': [2500] * 30,  # Sin random, sin multiplicación
                'queso': [185] * 30,
                'yogur': [330] * 30,
                'mantequilla': [280] * 30,
                'crema': [850] * 30,
                'leche_deslactosada': [1800] * 30,
                'dulce_de_leche': [420] * 30
            }
        except Exception as e:
            logger.error(f"Error creating demand_example: {e}")
            demand_example = {'leche': [2500] * 30}
        
        # Configuraciones de demanda - VALORES FIJOS
        demand_configurations_preview = {
            'leche': {'base_demand': 2500, 'seasonality': True, 'growth_rate': 0.02, 'volatility': 0.1},
            'queso': {'base_demand': 185, 'seasonality': False, 'growth_rate': 0.01, 'volatility': 0.08},
            'yogur': {'base_demand': 330, 'seasonality': True, 'growth_rate': 0.05, 'volatility': 0.15},
            'dulce de leche': {'base_demand': 420, 'seasonality': True, 'growth_rate': 0.03, 'volatility': 0.12},
            'leche deslactosada': {'base_demand': 1800, 'seasonality': True, 'growth_rate': 0.015, 'volatility': 0.12},
            'mantequilla': {'base_demand': 280, 'seasonality': False, 'growth_rate': 0.01, 'volatility': 0.09},
            'crema de leche': {'base_demand': 850, 'seasonality': True, 'growth_rate': 0.03, 'volatility': 0.11}
        }
        
        # Ejemplo de resultado de simulación - VALORES FIJOS
        result_simulation_preview = {
            'demand_mean': 2500.0,
            'demand_std_deviation': 250.0,
            'confidence_intervals': {
                'demand_mean': {
                    'lower': 2400.0,
                    'upper': 2600.0
                }
            },
            'unit': {
                'measurement': 'litros',
                'value': 1.0
            },
            'roi': {
                'value': 0.25,
                'confidence_interval': {
                    'lower': 0.20,
                    'upper': 0.30
                }
            },
            'profit_margin': {
                'value': 0.20,
                'confidence_interval': {
                    'lower': 0.15,
                    'upper': 0.25
                }
            }
        }
        
        # Usar una simulación de ejemplo
        simulate_preview = simulation_data_leche[0] if simulation_data_leche else _generate_safe_default_simulation()
        
        # Estadísticas resumen
        summary_stats = {
            'total_products': len(products_data),
            'total_areas': len(areas_data),
            'total_variables': len(variables_data),
            'variables_by_type': {
                'exogenas': len(variables_by_type['exogenas']),
                'estado': len(variables_by_type['estado']),
                'endogenas': len(variables_by_type['endogenas'])
            },
            'total_equations': len(equations_data),
            'total_questions': len(question_data),
            'total_simulations': sum(len(sims.get('simulations', [])) for sims in simulations_preview.values()),
            'total_recommendations': len(recommendation_data),
            'total_pdfs': len(pdf_data)
        }
        
        # Preparar respuestas por producto
        questionary_results_preview = {
            'leche': answer_data_leche,
            'queso': answer_data_queso,
            'yogur': answer_data_yogur,
            'dulce de leche': answer_data_dulce_leche,
            'leche deslactosada': answer_data_leche_deslactosada,
            'mantequilla': answer_data_mantequilla,
            'crema de leche': answer_data_crema
        }
        
        logger.info("prepare_preview_data completed successfully")
        
        return {
            # Información del negocio
            'business': {
                'name': "Empresa Láctea Demo",
                'location': "La Paz, Bolivia",
                'type': "Pequeña empresa láctea",
                'employees': 15,
                'years_in_business': 5,
                'image_src': "business/pyme_lactea_default.jpg",
            },
            
            # Datos principales
            'products_preview': products_preview,
            'areas_preview': areas_preview,
            'variable_preview': variables_data,
            'variables_by_type': variables_by_type,
            'equation_preview': equations_data,
            'questionary_preview': questionary_data,
            'question_preview': questions_with_answers,
            'simulations_preview': simulations_preview,
            'simulate_preview': simulate_preview,
            'pdf_preview': pdf_data,
            'recommendations_preview': recommendation_data,
            
            # Datos adicionales para visualización
            'demand_example': demand_example,
            'demand_configurations_preview': demand_configurations_preview,
            'result_simulation_preview': result_simulation_preview,
            
            # Estadísticas
            'summary_stats': summary_stats,
            
            # Datos de respuestas por producto
            'questionary_results_preview': questionary_results_preview
        }
        
    except Exception as e:
        logger.error(f"Critical error in prepare_preview_data: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Retornar datos mínimos completamente seguros
        return {
            'error': True,
            'error_message': str(e),
            'business': {
                'name': "Error - Datos no disponibles",
                'location': "N/A",
                'type': "N/A",
                'employees': 0,
                'years_in_business': 0,
                'image_src': "",
            },
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
            'simulate_preview': {},
            'pdf_preview': [],
            'recommendations_preview': [],
            'demand_example': {},
            'demand_configurations_preview': {},
            'result_simulation_preview': {},
            'summary_stats': {
                'total_products': 0,
                'total_areas': 0,
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


def _generate_safe_default_simulations(product: str) -> List[Dict[str, Any]]:
    """Generar simulaciones por defecto SIN multiplicaciones"""
    logger.debug(f"Generating safe default simulations for {product}")
    
    try:
        scenarios = [
            {
                'name': f'Escenario Optimista - {product}',
                'scenario': 'Optimista',
                'description': 'Escenario con crecimiento sostenido y condiciones favorables',
                'demand_history': [2800] * 30,  # VALORES FIJOS, SIN MULTIPLICACIÓN
                'parameters': {
                    'growth_rate': 0.05,
                    'production_efficiency': 0.90
                },
                'expected_results': {
                    'roi': 0.35,
                    'profit_margin': 0.25,
                    'demand_mean': 2800
                }
            },
            {
                'name': f'Escenario Base - {product}',
                'scenario': 'Base',
                'description': 'Escenario con condiciones normales de mercado',
                'demand_history': [2500] * 30,  # VALORES FIJOS, SIN MULTIPLICACIÓN
                'parameters': {
                    'growth_rate': 0.02,
                    'production_efficiency': 0.85
                },
                'expected_results': {
                    'roi': 0.25,
                    'profit_margin': 0.20,
                    'demand_mean': 2500
                }
            },
            {
                'name': f'Escenario Pesimista - {product}',
                'scenario': 'Pesimista',
                'description': 'Escenario con condiciones adversas de mercado',
                'demand_history': [2000] * 30,  # VALORES FIJOS, SIN MULTIPLICACIÓN
                'parameters': {
                    'growth_rate': -0.01,
                    'production_efficiency': 0.75
                },
                'expected_results': {
                    'roi': 0.15,
                    'profit_margin': 0.15,
                    'demand_mean': 2000
                }
            }
        ]
        return scenarios
    except Exception as e:
        logger.error(f"Error generating safe default simulations for {product}: {e}")
        return []


def _generate_safe_default_simulation() -> Dict[str, Any]:
    """Generar simulación por defecto SIN multiplicaciones"""
    logger.debug("Generating safe default simulation")
    
    try:
        return {
            'unit_time': 'days',
            'quantity_time': 30,
            'confidence_level': 0.95,
            'random_seed': 42,
            'fk_fdp': 1,
            'demand_history': [2500] * 30,  # VALORES FIJOS, SIN MULTIPLICACIÓN
            'parameters': {}
        }
    except Exception as e:
        logger.error(f"Error generating safe default simulation: {e}")
        return {
            'unit_time': 'days',
            'quantity_time': 30,
            'confidence_level': 0.95,
            'random_seed': 42,
            'fk_fdp': 1,
            'demand_history': [],
            'parameters': {}
        }