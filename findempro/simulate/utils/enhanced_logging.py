# ========================================================================
# ARCHIVO NUEVO: simulate/utils/enhanced_logging.py
# CREAR ESTE ARCHIVO NUEVO para manejo centralizado de errores
# ========================================================================

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def enhanced_error_logging(error: Exception, context: str = "operation", 
                          additional_data: Optional[Dict[str, Any]] = None) -> None:
    """
    Logging mejorado para errores específicos de simulación
    
    Args:
        error: La excepción capturada
        context: Contexto donde ocurrió el error
        additional_data: Datos adicionales para el debugging
    """
    try:
        error_info = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'timestamp': datetime.now().isoformat()
        }
        
        if additional_data:
            error_info['additional_data'] = additional_data
        
        logger.error(f"Enhanced error log: {json.dumps(error_info, indent=2)}")
        
        # Logging específico para errores conocidos de simulación
        error_msg = str(error).lower()
        
        if "unsupported operand type" in error_msg:
            logger.error("🔧 FIX NEEDED: Detected unsupported operand type error")
            logger.error("   → Ensure all mathematical operations use compatible types")
            logger.error("   → Use _safe_numeric_operation() for ResultSimulation objects")
            logger.error(f"   → Error in context: {context}")
        
        elif "has no attribute" in error_msg:
            logger.error("🔧 FIX NEEDED: Detected missing attribute error")
            logger.error("   → Verify method exists before calling")
            logger.error("   → Use hasattr() checks for dynamic methods")
            logger.error(f"   → Missing attribute in context: {context}")
        
        elif "tight_layout" in error_msg:
            logger.error("🔧 FIX NEEDED: Matplotlib tight_layout warning")
            logger.error("   → Replace plt.tight_layout() with plt.tight_layout(pad=1.0)")
            logger.error("   → Use _apply_safe_layout() method instead")
        
        elif "metric_value" in error_msg or "threshold_value" in error_msg:
            logger.error("🔧 FIX NEEDED: Missing required fields in recommendation")
            logger.error("   → Use _validate_recommendation_data() before saving")
            logger.error("   → Ensure all recommendations have metric_value and threshold_value")
        
        elif "accumulated_totals_variables" in error_msg:
            logger.error("🔧 FIX NEEDED: Variable not found in accumulated totals")
            logger.error("   → Use _process_accumulated_variables_safely() method")
            logger.error("   → Check variable availability before processing")
        
        elif "_generate_daily_validation_charts" in error_msg:
            logger.error("🔧 FIX NEEDED: Missing method in validation service")
            logger.error("   → Add _generate_daily_validation_charts() method to SimulationValidationService")
            logger.error("   → Use fallback charts if method is not available")
        
        elif "_validate_model_variables" in error_msg:
            logger.error("🔧 FIX NEEDED: Missing method in validation service")
            logger.error("   → Add _validate_model_variables() method to SimulationValidationService")
            logger.error("   → Check method existence with hasattr() before calling")
        
    except Exception as logging_error:
        # Fallback logging
        logger.error(f"Error in enhanced logging: {logging_error}")
        logger.error(f"Original error: {error}")

def validate_data_structure(data: Any, expected_structure: Dict[str, type], 
                           context: str = "data_validation") -> Dict[str, Any]:
    """
    Validar estructura de datos antes de procesamiento
    
    Args:
        data: Los datos a validar
        expected_structure: Diccionario con campo -> tipo esperado
        context: Contexto de la validación
        
    Returns:
        Diccionario con resultados de validación
    """
    try:
        validation_results = {
            'is_valid': True,
            'missing_fields': [],
            'invalid_types': [],
            'warnings': []
        }
        
        if not isinstance(data, dict):
            validation_results['is_valid'] = False
            validation_results['warnings'].append(f"Expected dict, got {type(data)}")
            return validation_results
        
        for field, expected_type in expected_structure.items():
            if field not in data:
                validation_results['missing_fields'].append(field)
                validation_results['is_valid'] = False
            elif not isinstance(data[field], expected_type):
                validation_results['invalid_types'].append({
                    'field': field,
                    'expected': expected_type.__name__,
                    'actual': type(data[field]).__name__
                })
                validation_results['warnings'].append(f"Field {field} type mismatch")
        
        if not validation_results['is_valid']:
            enhanced_error_logging(
                ValueError("Data structure validation failed"),
                context,
                validation_results
            )
        
        return validation_results
        
    except Exception as e:
        logger.error(f"Error in data structure validation: {e}")
        return {
            'is_valid': False, 
            'missing_fields': [], 
            'invalid_types': [], 
            'warnings': [str(e)]
        }

def safe_method_call(obj: Any, method_name: str, *args, fallback_result: Any = None, **kwargs) -> Any:
    """
    Llamar método de forma segura con fallback
    
    Args:
        obj: Objeto que contiene el método
        method_name: Nombre del método a llamar
        *args: Argumentos posicionales
        fallback_result: Resultado a retornar si el método no existe
        **kwargs: Argumentos con nombre
        
    Returns:
        Resultado del método o fallback_result
    """
    try:
        if hasattr(obj, method_name):
            method = getattr(obj, method_name)
            if callable(method):
                return method(*args, **kwargs)
            else:
                logger.warning(f"Attribute {method_name} exists but is not callable")
                return fallback_result
        else:
            logger.warning(f"Method {method_name} not found in {type(obj).__name__}")
            return fallback_result
            
    except Exception as e:
        enhanced_error_logging(e, f"safe_method_call_{method_name}", {
            'object_type': type(obj).__name__,
            'method_name': method_name,
            'args_count': len(args),
            'kwargs_keys': list(kwargs.keys())
        })
        return fallback_result

def log_performance_metrics(context: str, start_time: datetime, 
                           additional_metrics: Optional[Dict[str, Any]] = None) -> None:
    """
    Log métricas de rendimiento
    
    Args:
        context: Contexto de la operación
        start_time: Tiempo de inicio
        additional_metrics: Métricas adicionales
    """
    try:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        metrics = {
            'context': context,
            'duration_seconds': duration,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }
        
        if additional_metrics:
            metrics.update(additional_metrics)
        
        logger.info(f"Performance metrics: {json.dumps(metrics, indent=2)}")
        
        # Alertas de rendimiento
        if duration > 30:  # Más de 30 segundos
            logger.warning(f"⚠️ SLOW OPERATION: {context} took {duration:.2f} seconds")
        elif duration > 60:  # Más de 1 minuto
            logger.error(f"🐌 VERY SLOW OPERATION: {context} took {duration:.2f} seconds")
            
    except Exception as e:
        logger.error(f"Error logging performance metrics: {e}")

class SimulationErrorHandler:
    """Manejador de errores específico para simulaciones"""
    
    def __init__(self, simulation_id: Optional[int] = None):
        self.simulation_id = simulation_id
        self.error_count = 0
        self.warnings_count = 0
    
    def handle_error(self, error: Exception, context: str, 
                    additional_data: Optional[Dict[str, Any]] = None) -> None:
        """Manejar error específico de simulación"""
        self.error_count += 1
        
        error_data = additional_data or {}
        if self.simulation_id:
            error_data['simulation_id'] = self.simulation_id
        error_data['error_number'] = self.error_count
        
        enhanced_error_logging(error, context, error_data)
    
    def handle_warning(self, message: str, context: str, 
                      additional_data: Optional[Dict[str, Any]] = None) -> None:
        """Manejar warning específico de simulación"""
        self.warnings_count += 1
        
        warning_data = additional_data or {}
        if self.simulation_id:
            warning_data['simulation_id'] = self.simulation_id
        warning_data['warning_number'] = self.warnings_count
        
        logger.warning(f"Simulation warning [{context}]: {message}")
        if warning_data:
            logger.warning(f"Warning details: {json.dumps(warning_data, indent=2)}")
    
    def get_error_summary(self) -> Dict[str, int]:
        """Obtener resumen de errores"""
        return {
            'total_errors': self.error_count,
            'total_warnings': self.warnings_count,
            'simulation_id': self.simulation_id
        }

# Decorador para manejo automático de errores
def handle_simulation_errors(context: str = None):
    """
    Decorador para manejo automático de errores en métodos de simulación
    
    Args:
        context: Contexto específico del método
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            method_context = context or f"{self.__class__.__name__}.{func.__name__}"
            start_time = datetime.now()
            
            try:
                # Crear error handler si no existe
                if not hasattr(self, '_error_handler'):
                    simulation_id = getattr(self, 'simulation_id', None) or \
                                   getattr(self, 'id', None) or \
                                   (hasattr(self, 'simulation_instance') and 
                                    getattr(self.simulation_instance, 'id', None))
                    self._error_handler = SimulationErrorHandler(simulation_id)
                
                result = func(self, *args, **kwargs)
                
                # Log métricas de rendimiento
                log_performance_metrics(method_context, start_time, {
                    'method': func.__name__,
                    'args_count': len(args),
                    'success': True
                })
                
                return result
                
            except Exception as e:
                # Manejar error
                self._error_handler.handle_error(e, method_context, {
                    'method': func.__name__,
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys())
                })
                
                # Log métricas de rendimiento con error
                log_performance_metrics(method_context, start_time, {
                    'method': func.__name__,
                    'success': False,
                    'error_type': type(e).__name__
                })
                
                # Re-raise el error
                raise
        
        return wrapper
    return decorator

# Utilidades de debugging
def debug_variable_structure(variables_data: Any, context: str = "debug") -> None:
    """Debug de estructura de variables"""
    try:
        logger.debug(f"=== DEBUG {context.upper()} ===")
        logger.debug(f"Data type: {type(variables_data)}")
        
        if isinstance(variables_data, dict):
            logger.debug(f"Dictionary keys: {list(variables_data.keys())}")
            for key, value in list(variables_data.items())[:3]:  # Solo primeros 3
                logger.debug(f"  {key}: {type(value)} = {value}")
        
        elif isinstance(variables_data, list):
            logger.debug(f"List length: {len(variables_data)}")
            if variables_data:
                first_item = variables_data[0]
                logger.debug(f"First item type: {type(first_item)}")
                if isinstance(first_item, dict):
                    logger.debug(f"First item keys: {list(first_item.keys())}")
        
        logger.debug(f"=== END DEBUG {context.upper()} ===")
        
    except Exception as e:
        logger.error(f"Error in debug_variable_structure: {e}")

def check_service_health(service_obj: Any, required_methods: list) -> Dict[str, bool]:
    """Verificar salud de un servicio"""
    try:
        health_status = {
            'service_available': service_obj is not None,
            'service_type': type(service_obj).__name__ if service_obj else 'None'
        }
        
        if service_obj:
            for method_name in required_methods:
                health_status[f'has_{method_name}'] = hasattr(service_obj, method_name)
        
        # Log estado de salud
        available_methods = sum(1 for k, v in health_status.items() 
                               if k.startswith('has_') and v)
        total_methods = len(required_methods)
        
        logger.info(f"Service health check: {available_methods}/{total_methods} methods available")
        
        if available_methods < total_methods:
            missing_methods = [method for method in required_methods 
                             if not health_status.get(f'has_{method}', False)]
            logger.warning(f"Missing methods in service: {missing_methods}")
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error checking service health: {e}")
        return {'service_available': False, 'error': str(e)}

