# services/data_extractor.py
"""
Servicio para extraer y procesar datos de simulaciones.
Maneja la extracción de demanda histórica, variables y datos de cuestionarios.
"""
import json
import logging
from typing import Dict, List, Any, Optional
import numpy as np
from ..models import Simulation, ResultSimulation
from ..utils.data_parsers_utils import DataParser

logger = logging.getLogger(__name__)


class SimulationDataExtractor:
    """Extrae y procesa datos de simulaciones y cuestionarios"""
    
    def __init__(self):
        self.data_parser = DataParser()
    
    def extract_historical_demand(self, simulation_instance: Simulation) -> List[float]:
        """
        Extrae los datos históricos de demanda de múltiples fuentes
        """
        try:
            # Prioridad 1: Campo demand_history de la simulación
            if simulation_instance.demand_history:
                demand_data = self._parse_demand_from_field(simulation_instance.demand_history)
                if demand_data:
                    logger.info(f"Historical demand extracted from simulation field: {len(demand_data)} points")
                    return demand_data
            
            # Prioridad 2: Respuestas del cuestionario
            demand_data = self._extract_demand_from_questionnaire(simulation_instance)
            if demand_data:
                logger.info(f"Historical demand extracted from questionnaire: {len(demand_data)} points")
                return demand_data
            
            logger.warning("No historical demand data found")
            return []
            
        except Exception as e:
            logger.error(f"Error extracting historical demand: {str(e)}")
            return []
    
    def extract_real_values_from_questionnaire(self, simulation_instance: Simulation) -> Dict[str, float]:
        """
        Extrae valores reales del cuestionario para validación
        """
        real_values = {}
        
        try:
            answers = simulation_instance.fk_questionary_result.fk_question_result_answer.select_related(
                'fk_question__fk_variable'
            ).all()
            
            for answer in answers:
                if answer.fk_question.fk_variable and answer.answer:
                    var_initials = answer.fk_question.fk_variable.initials
                    value = self.data_parser.parse_numeric_answer(answer.answer)
                    
                    if value is not None:
                        real_values[var_initials] = value
            
            # Calcular valores derivados
            real_values = self._calculate_derived_real_values(real_values)
            
            logger.info(f"Extracted {len(real_values)} real values from questionnaire")
            return real_values
            
        except Exception as e:
            logger.error(f"Error extracting real values: {str(e)}")
            return {}
    
    def extract_variables_from_results(self, results_simulation: List[ResultSimulation]) -> List[Dict[str, Any]]:
        """
        Extrae todas las variables de los resultados de simulación
        """
        all_variables = []
        
        for idx, result in enumerate(results_simulation):
            try:
                day_data = self._extract_basic_day_data(result, idx)
                
                # Extraer variables adicionales
                if hasattr(result, 'variables') and result.variables:
                    additional_vars = self._extract_additional_variables(result.variables)
                    day_data.update(additional_vars)
                
                all_variables.append(day_data)
                
            except Exception as e:
                logger.error(f"Error processing result {idx}: {e}")
                # Agregar datos mínimos en caso de error
                all_variables.append(self._get_minimal_day_data(idx))
        
        logger.info(f"Extracted variables from {len(all_variables)} simulation days")
        return all_variables
    
    def extract_business_context(self, simulation_instance: Simulation) -> Dict[str, Any]:
        """
        Extrae contexto del negocio y producto
        """
        try:
            questionary_result = simulation_instance.fk_questionary_result
            questionary = questionary_result.fk_questionary
            product = questionary.fk_product
            business = product.fk_business
            
            return {
                'business_instance': business,
                'product_instance': product,
                'questionary_instance': questionary,
                'questionary_result_instance': questionary_result,
                'business_name': business.name if hasattr(business, 'name') else 'Unknown',
                'product_name': product.name if hasattr(product, 'name') else 'Unknown'
            }
            
        except Exception as e:
            logger.error(f"Error extracting business context: {e}")
            return {
                'business_instance': None,
                'product_instance': None,
                'questionary_instance': None,
                'questionary_result_instance': None,
                'business_name': 'Unknown',
                'product_name': 'Unknown'
            }
    
    def _parse_demand_from_field(self, demand_field: Any) -> List[float]:
        """Parsea demanda desde el campo demand_history"""
        try:
            if isinstance(demand_field, str):
                return json.loads(demand_field)
            elif isinstance(demand_field, list):
                return [float(x) for x in demand_field if isinstance(x, (int, float))]
            else:
                return []
        except (json.JSONDecodeError, ValueError, TypeError):
            return []
    
    def _extract_demand_from_questionnaire(self, simulation_instance: Simulation) -> List[float]:
        """Extrae demanda histórica desde las respuestas del cuestionario"""
        try:
            answers = simulation_instance.fk_questionary_result.fk_question_result_answer.all()
            
            for answer in answers:
                question_text = answer.fk_question.question.lower()
                
                # Buscar preguntas relacionadas con demanda histórica
                if ('históric' in question_text and 'demanda' in question_text) or \
                   ('historical' in question_text and 'demand' in question_text) or \
                   ('datos históricos' in question_text):
                    
                    if answer.answer:
                        return self._parse_demand_string(answer.answer)
            
            return []
            
        except Exception as e:
            logger.error(f"Error extracting demand from questionnaire: {e}")
            return []
    
    def _parse_demand_string(self, demand_str: str) -> List[float]:
        """Parsea string de demanda en múltiples formatos"""
        try:
            # Limpiar el string
            demand_str = demand_str.strip()
            
            # Intentar JSON primero
            try:
                return json.loads(demand_str)
            except json.JSONDecodeError:
                pass
            
            # Remover brackets si existen
            demand_str = demand_str.replace('[', '').replace(']', '')
            
            # Separadores posibles
            if ',' in demand_str:
                values = demand_str.split(',')
            elif ';' in demand_str:
                values = demand_str.split(';')
            elif ' ' in demand_str:
                values = demand_str.split()
            elif '\n' in demand_str:
                values = demand_str.split('\n')
            else:
                # Un solo valor
                values = [demand_str]
            
            # Convertir a float
            parsed_values = []
            for value in values:
                value = value.strip()
                if value:
                    try:
                        parsed_values.append(float(value))
                    except ValueError:
                        continue
            
            return parsed_values
            
        except Exception as e:
            logger.error(f"Error parsing demand string: {e}")
            return []
    
    def _extract_basic_day_data(self, result: ResultSimulation, day_index: int) -> Dict[str, Any]:
        """Extrae datos básicos del día"""
        return {
            'day': day_index + 1,
            'date': result.date.isoformat() if hasattr(result, 'date') and result.date else None,
            'demand_mean': float(result.demand_mean) if hasattr(result, 'demand_mean') and result.demand_mean is not None else 0.0,
            'demand_std': float(result.demand_std_deviation) if hasattr(result, 'demand_std_deviation') and result.demand_std_deviation is not None else 0.0
        }
    
    def _extract_additional_variables(self, variables_data: Any) -> Dict[str, Any]:
        """Extrae variables adicionales del resultado"""
        additional_vars = {}
        
        try:
            # Si es string JSON, parsearlo
            if isinstance(variables_data, str):
                try:
                    variables_dict = json.loads(variables_data)
                except json.JSONDecodeError:
                    logger.warning("Could not parse variables JSON")
                    return additional_vars
            elif isinstance(variables_data, dict):
                variables_dict = variables_data
            else:
                return additional_vars
            
            # Procesar cada variable
            for key, value in variables_dict.items():
                if not key.startswith('_'):  # Ignorar variables privadas
                    try:
                        # Intentar convertir a float si es posible
                        if isinstance(value, (int, float)):
                            additional_vars[key] = float(value)
                        elif isinstance(value, str) and self._is_numeric_string(value):
                            additional_vars[key] = float(value)
                        else:
                            additional_vars[key] = value
                    except (ValueError, TypeError):
                        additional_vars[key] = value
            
        except Exception as e:
            logger.error(f"Error extracting additional variables: {e}")
        
        return additional_vars
    
    def _is_numeric_string(self, value: str) -> bool:
        """Verifica si un string representa un número"""
        try:
            cleaned = value.strip().replace(',', '.')
            float(cleaned)
            return True
        except (ValueError, AttributeError):
            return False
    
    def _get_minimal_day_data(self, day_index: int) -> Dict[str, Any]:
        """Retorna datos mínimos para un día en caso de error"""
        return {
            'day': day_index + 1,
            'date': None,
            'demand_mean': 0.0,
            'demand_std': 0.0
        }
    
    def _calculate_derived_real_values(self, real_values: Dict[str, float]) -> Dict[str, float]:
        """Calcula valores derivados que no están directamente en el cuestionario"""
        try:
            # Ingreso total
            if 'IT' not in real_values and all(k in real_values for k in ['TPV', 'PVP']):
                real_values['IT'] = real_values['TPV'] * real_values['PVP']
            
            # Gastos totales
            if 'TG' not in real_values and 'GO' in real_values:
                real_values['TG'] = real_values['GO'] * 1.2  # Estimación
            
            # Ganancia total
            if 'GT' not in real_values and all(k in real_values for k in ['IT', 'TG']):
                real_values['GT'] = real_values['IT'] - real_values['TG']
            
            # Capacidad de producción
            if 'CPROD' not in real_values and 'QPL' in real_values:
                real_values['CPROD'] = real_values['QPL'] * 1.2  # 20% de margen
            
            # Demanda promedio histórica
            if 'DPH' not in real_values and 'DH' in real_values:
                if isinstance(real_values['DH'], list):
                    real_values['DPH'] = np.mean(real_values['DH'])
                else:
                    real_values['DPH'] = real_values['DH']
            
            return real_values
            
        except Exception as e:
            logger.error(f"Error calculating derived values: {e}")
            return real_values
    
    def extract_pagination_context(self, request, simulation_id: int) -> Dict[str, Any]:
        """Extrae contexto de paginación"""
        try:
            from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
            
            results = ResultSimulation.objects.filter(
                is_active=True,
                fk_simulation_id=simulation_id
            ).order_by('date')
            
            paginator = Paginator(results, 365)  # 365 resultados por página
            page = request.GET.get('page', 1)
            
            try:
                paginated_results = paginator.page(page)
            except PageNotAnInteger:
                paginated_results = paginator.page(1)
            except EmptyPage:
                paginated_results = paginator.page(paginator.num_pages)
            
            return {
                'results_simulation': paginated_results,
                'current_page': paginated_results.number,
                'total_pages': paginator.num_pages,
                'has_previous': paginated_results.has_previous(),
                'has_next': paginated_results.has_next(),
                'total_results': paginator.count
            }
            
        except Exception as e:
            logger.error(f"Error extracting pagination context: {e}")
            return {
                'results_simulation': [],
                'current_page': 1,
                'total_pages': 1,
                'has_previous': False,
                'has_next': False,
                'total_results': 0
            }
    
    def validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida y limpia los datos extraídos"""
        validation_report = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'data_quality_score': 100
        }
        
        try:
            # Validar demanda histórica
            historical_demand = data.get('historical_demand', [])
            if not historical_demand:
                validation_report['warnings'].append("No se encontraron datos históricos de demanda")
                validation_report['data_quality_score'] -= 20
            elif len(historical_demand) < 10:
                validation_report['warnings'].append(f"Pocos datos históricos: {len(historical_demand)} puntos")
                validation_report['data_quality_score'] -= 10
            
            # Validar variables extraídas
            all_variables = data.get('all_variables_extracted', [])
            if not all_variables:
                validation_report['errors'].append("No se pudieron extraer variables de los resultados")
                validation_report['is_valid'] = False
                validation_report['data_quality_score'] -= 50
            
            # Validar consistencia de datos
            results_simulation = data.get('results_simulation', [])
            if len(results_simulation) != len(all_variables):
                validation_report['warnings'].append("Inconsistencia entre resultados y variables extraídas")
                validation_report['data_quality_score'] -= 15
            
            # Validar valores reales
            real_values = data.get('real_values', {})
            if len(real_values) < 3:
                validation_report['warnings'].append("Pocos valores reales para validación")
                validation_report['data_quality_score'] -= 10
            
            return validation_report
            
        except Exception as e:
            logger.error(f"Error validating extracted data: {e}")
            return {
                'is_valid': False,
                'warnings': [],
                'errors': [f"Error en validación: {str(e)}"],
                'data_quality_score': 0
            }