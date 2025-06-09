# validators/simulation_validators.py
import re
import logging
from typing import List, Dict, Any
from django.core.exceptions import ValidationError

from simulate.models import ProbabilisticDensityFunction

logger = logging.getLogger(__name__)


class SimulationValidator:
    """Validaciones para simulaciones y datos relacionados."""
    
    @staticmethod
    def validate_demand_data(data: List[float]) -> List[float]:
        """Valida datos históricos de demanda."""
        if not data:
            raise ValidationError("Los datos de demanda no pueden estar vacíos")
        
        if len(data) < 30:
            raise ValidationError(
                f"Se requieren mínimo 30 datos históricos. Proporcionados: {len(data)}"
            )
        
        if len(data) > 1000:
            raise ValidationError(
                f"Máximo 1000 datos históricos permitidos. Proporcionados: {len(data)}"
            )
        
        # Validar que todos sean números positivos
        invalid_values = [x for x in data if x <= 0]
        if invalid_values:
            raise ValidationError(
                f"Todos los valores de demanda deben ser positivos. "
                f"Valores inválidos encontrados: {len(invalid_values)}"
            )
        
        # Validar rango razonable
        min_value = min(data)
        max_value = max(data)
        
        if max_value / min_value > 100:  # Variación extrema
            raise ValidationError(
                "Los datos muestran variación extrema. "
                f"Rango: {min_value:.2f} - {max_value:.2f}"
            )
        
        return data
    
    @staticmethod
    def validate_fdp_parameters(fdp) -> Dict[str, Any]:
        """
        Valida que la FDP tenga los parámetros requeridos según su tipo de distribución.
        Retorna un diccionario con la validación y los datos de la FDP.
        """
        errors = []
        fdp_data = {
            'id': fdp.id,
            'name': fdp.name,
            'distribution_type': fdp.distribution_type,
            'distribution_name': fdp.get_distribution_type_display()
        }
        
        # Validar parámetros según el tipo de distribución
        if fdp.distribution_type == 1:  # Normal
            if fdp.mean_param is None:
                errors.append("Distribución Normal requiere parámetro de media")
            else:
                fdp_data['mean'] = fdp.mean_param
                
            if fdp.std_dev_param is None or fdp.std_dev_param <= 0:
                errors.append("Distribución Normal requiere desviación estándar positiva")
            else:
                fdp_data['std_dev'] = fdp.std_dev_param
                
        elif fdp.distribution_type == 2:  # Exponential
            if fdp.lambda_param is None or fdp.lambda_param <= 0:
                errors.append("Distribución Exponencial requiere parámetro lambda positivo")
            else:
                fdp_data['lambda'] = fdp.lambda_param
                
        elif fdp.distribution_type == 3:  # Log-Normal
            if fdp.mean_param is None:
                errors.append("Distribución Log-Normal requiere parámetro de media")
            else:
                fdp_data['mean'] = fdp.mean_param
                
            if fdp.std_dev_param is None or fdp.std_dev_param <= 0:
                errors.append("Distribución Log-Normal requiere desviación estándar positiva")
            else:
                fdp_data['std_dev'] = fdp.std_dev_param
                
        elif fdp.distribution_type == 4:  # Gamma
            if fdp.shape_param is None or fdp.shape_param <= 0:
                errors.append("Distribución Gamma requiere parámetro de forma (α) positivo")
            else:
                fdp_data['shape'] = fdp.shape_param
                
            if fdp.scale_param is None or fdp.scale_param <= 0:
                errors.append("Distribución Gamma requiere parámetro de escala (β) positivo")
            else:
                fdp_data['scale'] = fdp.scale_param
                
        elif fdp.distribution_type == 5:  # Uniform
            if fdp.min_param is None:
                errors.append("Distribución Uniforme requiere valor mínimo")
            else:
                fdp_data['min'] = fdp.min_param
                
            if fdp.max_param is None:
                errors.append("Distribución Uniforme requiere valor máximo")
            else:
                fdp_data['max'] = fdp.max_param
                
            # Validar que min < max
            if fdp.min_param is not None and fdp.max_param is not None:
                if fdp.min_param >= fdp.max_param:
                    errors.append("En distribución Uniforme, el valor mínimo debe ser menor que el máximo")
        else:
            errors.append(f"Tipo de distribución no soportado: {fdp.distribution_type}")
        
        # Añadir CDF si está disponible
        if fdp.cumulative_distribution_function is not None:
            fdp_data['cdf'] = fdp.cumulative_distribution_function
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'fdp_data': fdp_data if len(errors) == 0 else None
        }
    
    @staticmethod
    def validate_simulation_parameters(simulation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida parámetros de simulación y retorna los datos validados."""
        errors = []
        validated_data = {}
        
        # Validar ID de cuestionario
        questionary_id = simulation_data.get('fk_questionary_result')
        if not questionary_id:
            errors.append("ID de cuestionario requerido")
        else:
            try:
                questionary_id = int(questionary_id)
                if questionary_id <= 0:
                    errors.append("ID de cuestionario debe ser positivo")
                else:
                    validated_data['fk_questionary_result'] = questionary_id
            except (ValueError, TypeError):
                errors.append("ID de cuestionario debe ser un número válido")
        
        # Validar tiempo de simulación
        quantity_time = simulation_data.get('quantity_time')
        if not quantity_time:
            errors.append("Cantidad de tiempo requerida")
        else:
            try:
                quantity_time = int(quantity_time)
                if quantity_time < 1:
                    errors.append("Cantidad de tiempo debe ser al menos 1")
                elif quantity_time > 365:
                    errors.append("Cantidad de tiempo no puede exceder 365 días")
                else:
                    validated_data['quantity_time'] = quantity_time
            except (ValueError, TypeError):
                errors.append("Cantidad de tiempo debe ser un número válido")
        
        # Validar unidad de tiempo - con mapeo mejorado
        unit_time = simulation_data.get('unit_time')
        
        # Mapeo de unidades en inglés a español
        time_unit_mapping = {
            'days': 'días',
            'weeks': 'semanas', 
            'months': 'meses',
            'day': 'días',
            'week': 'semanas',
            'month': 'meses',
            'días': 'días',
            'semanas': 'semanas',
            'meses': 'meses'
        }
        
        if not unit_time:
            errors.append("Unidad de tiempo requerida")
        else:
            # Normalizar la unidad de tiempo
            normalized_unit = time_unit_mapping.get(unit_time.lower(), unit_time)
            valid_units = ['días', 'semanas', 'meses']
            
            if normalized_unit not in valid_units:
                errors.append(f"Unidad de tiempo debe ser una de: {', '.join(valid_units)}")
            else:
                validated_data['unit_time'] = unit_time  # Mantener el valor original
        
        # Validar datos históricos
        demand_history = simulation_data.get('demand_history')
        
        if not demand_history:
            errors.append("Datos históricos de demanda requeridos")
        else:
            try:
                # Intentar parsear los datos
                from ..utils.data_parsers import DataParser
                parser = DataParser()
                
                # Si demand_history es string con comas problemáticas, limpiar primero
                if isinstance(demand_history, str):
                    # Remover comas al final de números
                    demand_history = re.sub(r'(\d),(?=\s|$|\])', r'\1', demand_history)
                
                parsed_data = parser.parse_demand_history(demand_history)
                validated_demand = SimulationValidator.validate_demand_data(parsed_data)
                validated_data['demand_history'] = validated_demand  # Store parsed data
                
            except ValidationError as e:
                errors.append(f"Error en datos históricos: {str(e)}")
            except Exception as e:
                logger.error(f"Error parsing demand history: {str(e)}")
                errors.append(f"Formato de datos históricos inválido: {str(e)}")
        
        # Validar FDP
        fdp_id = simulation_data.get('fk_fdp_id')
        
        if not fdp_id:
            errors.append("Función de densidad probabilística requerida")
        else:
            try:
                fdp_id = int(fdp_id)
                if fdp_id <= 0:
                    errors.append("ID de FDP debe ser positivo")
                else:
                    # Validate FDP exists and is active
                    try:
                        fdp = ProbabilisticDensityFunction.objects.filter(
                            id=fdp_id, 
                            is_active=True
                        ).first()
                        
                        if not fdp:
                            errors.append("FDP no encontrada o inactiva")
                        else:
                            # Validate FDP has required parameters based on distribution type
                            fdp_validation_result = SimulationValidator.validate_fdp_parameters(fdp)
                            if fdp_validation_result['valid']:
                                validated_data['fdp'] = fdp_validation_result['fdp_data']
                                validated_data['fk_fdp_id'] = fdp_id
                            else:
                                errors.extend(fdp_validation_result['errors'])
                    except Exception as e:
                        logger.error(f"Error al validar FDP: {str(e)}")
                        errors.append(f"Error al validar FDP: {str(e)}")
            except (ValueError, TypeError):
                errors.append("ID de FDP debe ser un número válido")
        
        # Raise error if any validation failed
        if errors:
            raise ValidationError("; ".join(errors))
        
        # Return validated data
        return validated_data
    
    @staticmethod
    def validate_numeric_range(value: float, min_val: float, max_val: float, 
                             field_name: str) -> float:
        """Valida que un valor numérico esté en un rango específico."""
        try:
            value = float(value)
            
            if value < min_val or value > max_val:
                raise ValidationError(
                    f"{field_name} debe estar entre {min_val} y {max_val}. "
                    f"Valor proporcionado: {value}"
                )
            
            return value
            
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} debe ser un número válido")
    
    @staticmethod
    def validate_statistical_data(data: List[float], min_variance: float = 0.01):
        """Valida que los datos sean estadísticamente válidos."""
        try:
            import numpy as np
            
            data_array = np.array(data)
            
            # Validar varianza mínima
            variance = np.var(data_array)
            if variance < min_variance:
                raise ValidationError(
                    f"Los datos muestran muy poca varianza ({variance:.6f}). "
                    f"Se requiere al menos {min_variance}"
                )
            
            # Validar ausencia de outliers extremos
            q1 = np.percentile(data_array, 25)
            q3 = np.percentile(data_array, 75)
            iqr = q3 - q1
            
            lower_bound = q1 - 3 * iqr
            upper_bound = q3 + 3 * iqr
            
            outliers = [x for x in data if x < lower_bound or x > upper_bound]
            if len(outliers) > len(data) * 0.1:  # Más del 10% son outliers
                raise ValidationError(
                    f"Demasiados valores atípicos detectados: {len(outliers)} de {len(data)}"
                )
            
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Error en validación estadística: {str(e)}")
    
    @staticmethod
    def validate_user_input_safety(input_string: str, max_length: int = 10000) -> str:
        """Valida y sanitiza entrada de usuario."""
        if not isinstance(input_string, str):
            raise ValidationError("La entrada debe ser texto")
        
        if len(input_string) > max_length:
            raise ValidationError(f"Entrada demasiado larga. Máximo: {max_length}")
        
        # Remover caracteres potencialmente peligrosos
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
        for char in dangerous_chars:
            if char in input_string:
                raise ValidationError(f"Carácter no permitido encontrado: {char}")
        
        return input_string.strip()
    
    @staticmethod
    def validate_file_format(file_content: str, expected_format: str = 'json'):
        """Valida formato de archivo."""
        try:
            if expected_format == 'json':
                import json
                json.loads(file_content)
            elif expected_format == 'csv':
                # Validación básica para CSV
                lines = file_content.strip().split('\n')
                if len(lines) < 2:
                    raise ValidationError("Archivo CSV debe tener al menos 2 líneas")
            else:
                raise ValidationError(f"Formato no soportado: {expected_format}")
                
        except json.JSONDecodeError:
            raise ValidationError("Formato JSON inválido")
        except Exception as e:
            raise ValidationError(f"Error validando formato: {str(e)}")


class BusinessRuleValidator:
    """Validaciones específicas de reglas de negocio."""
    
    @staticmethod
    def validate_simulation_frequency(user, time_window_hours: int = 24, max_simulations: int = 10):
        """Valida frecuencia de simulaciones por usuario."""
        try:
            from datetime import datetime, timedelta
            from ..models import Simulation
            
            cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
            
            recent_simulations = Simulation.objects.filter(
                fk_questionary_result__fk_questionary__fk_product__fk_business__fk_user=user,
                date_created__gte=cutoff_time
            ).count()
            
            if recent_simulations >= max_simulations:
                raise ValidationError(
                    f"Límite de simulaciones alcanzado. "
                    f"Máximo {max_simulations} en {time_window_hours} horas."
                )
                
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Error validando frecuencia: {str(e)}")
    
    @staticmethod
    def validate_business_permissions(user, business_id: int):
        """Valida permisos de usuario sobre un negocio."""
        try:
            from business.models import Business
            
            if not Business.objects.filter(id=business_id, fk_user=user).exists():
                raise ValidationError("No tiene permisos sobre este negocio")
                
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Error validando permisos: {str(e)}")