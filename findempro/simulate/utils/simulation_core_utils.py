# utils/simulation_core_utils.py
"""
VERSIÓN CORREGIDA: Núcleo principal de simulación con motor de ecuaciones integrado.
Maneja la creación, ejecución y gestión completa del proceso de simulación.
"""
from decimal import Decimal
import logging
import json
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from django.db import transaction
from django.utils import timezone

# Importaciones del proyecto
from ..models import Simulation, ResultSimulation, ProbabilisticDensityFunction
from ..utils.simulation_math_utils import SimulationMathEngine
from ..utils.variable_mapper import VariableMapper
from questionary.models import QuestionaryResult
from variable.models import Variable

logger = logging.getLogger(__name__)

def make_json_serializable(obj):
    """Convertir objetos numpy y otros tipos a tipos serializables por JSON"""
    if isinstance(obj, dict):
        return {key: make_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(make_json_serializable(item) for item in obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.int_, np.intc, np.intp, np.int8, np.int16, np.int32, np.int64,
                         np.uint8, np.uint16, np.uint32, np.uint64)):
        return int(obj)
    elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.bool_)):
        return bool(obj)
    elif isinstance(obj, Decimal):
        return float(obj)
    elif hasattr(obj, 'item'):  # Para otros tipos numpy
        return obj.item()
    else:
        return obj


class CustomJSONEncoder(json.JSONEncoder):
    """Encoder personalizado para manejar tipos numpy"""
    def default(self, obj):
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8, np.int16, np.int32, np.int64,
                           np.uint8, np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.bool_)):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, 'item'):
            return obj.item()
        return super().default(obj)


class SimulationCore:
    """
    Núcleo principal del sistema de simulación con motor de ecuaciones integrado
    """
    
    def __init__(self):
        self.math_engine = SimulationMathEngine()
        self.variable_mapper = VariableMapper()
        
        # Configuración de simulación
        self.config = {
            'max_iterations_per_day': 10,
            'convergence_tolerance': 1e-6,
            'enable_validation': True,
            'save_intermediate_results': True,
            'batch_size': 50  # Para optimización de BD
        }
    
    @transaction.atomic
    def create_simulation(self, simulation_data: Dict[str, Any]) -> Simulation:
        """
        Crear nueva simulación con validación completa de datos
        """
        try:
            logger.info("Creating new simulation with enhanced data validation")
            
            # Validar datos de entrada
            validated_data = self._validate_simulation_data(simulation_data)
            
            # Obtener instancias relacionadas
            questionary_result = QuestionaryResult.objects.get(
                id=validated_data['fk_questionary_result']
            )
            
            fdp = ProbabilisticDensityFunction.objects.get(
                id=validated_data['fk_fdp_id']
            )
            
            # Extraer y validar variables desde BD
            extracted_variables = self.variable_mapper.extract_all_variables(questionary_result)
            
            # Generar reporte de extracción
            extraction_report = self.variable_mapper.generate_extraction_report(extracted_variables)
            logger.info(f"Variable extraction report: {extraction_report['coverage_analysis']}")
            
            # Preparar configuración de demanda
            demand_config = self._prepare_demand_configuration(
                validated_data['demand_history'], 
                fdp
            )
            
            # Crear instancia de simulación
            simulation = Simulation.objects.create(
                fk_questionary_result=questionary_result,
                fk_fdp=fdp,
                quantity_time=validated_data['quantity_time'],
                unit_time=validated_data['unit_time'],
                demand_history=json.dumps(validated_data['demand_history']),
                confidence_level=validated_data.get('confidence_level', 0.95),
                random_seed=validated_data.get('random_seed'),
                is_active=True,
                date_created=timezone.now(),
                
                # Metadatos adicionales
                extracted_variables=extracted_variables,  # En lugar de json.dumps()
                demand_config=demand_config,              # En lugar de json.dumps()
                extraction_report=extraction_report       # En lugar de json.dumps()
            )
            
            logger.info(f"Simulation created successfully with ID: {simulation.id}")
            return simulation
            
        except Exception as e:
            logger.error(f"Error creating simulation: {str(e)}")
            raise
    
    def execute_simulation(self, simulation: Simulation) -> bool:
        """
        Ejecutar simulación completa con motor de ecuaciones
        """
        try:
            logger.info(f"Starting execution of simulation {simulation.id}")
            
            # Preparar datos para simulación
            simulation_context = self._prepare_simulation_context(simulation)
            
            # Ejecutar simulación día por día
            success = self._execute_daily_simulation(simulation, simulation_context)
            
            if success:
                # Actualizar estado de simulación
                simulation.is_completed = True
                simulation.completion_date = timezone.now()
                simulation.save(update_fields=['is_completed', 'completion_date'])
                
                logger.info(f"Simulation {simulation.id} completed successfully")
            else:
                logger.error(f"Simulation {simulation.id} failed during execution")
            
            return success
            
        except Exception as e:
            logger.error(f"Error executing simulation {simulation.id}: {str(e)}")
            return False
    
    def _validate_simulation_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validar datos de entrada para simulación"""
        
        validated = {}
        errors = []
        
        # Validar questionary_result
        try:
            questionary_id = int(data['fk_questionary_result'])
            if not QuestionaryResult.objects.filter(id=questionary_id, is_active=True).exists():
                errors.append(f"Questionary result {questionary_id} not found or inactive")
            validated['fk_questionary_result'] = questionary_id
        except (ValueError, KeyError):
            errors.append("Invalid questionary_result ID")
        
        # Validar FDP
        try:
            fdp_id = int(data['fk_fdp_id'])
            if not ProbabilisticDensityFunction.objects.filter(id=fdp_id, is_active=True).exists():
                errors.append(f"FDP {fdp_id} not found or inactive")
            validated['fk_fdp_id'] = fdp_id
        except (ValueError, KeyError):
            errors.append("Invalid FDP ID")
        
        # Validar tiempo
        try:
            quantity = int(data['quantity_time'])
            if quantity < 1 or quantity > 365:
                errors.append("Quantity time must be between 1 and 365")
            validated['quantity_time'] = quantity
        except (ValueError, KeyError):
            errors.append("Invalid quantity_time")
        
        # Validar unidad de tiempo
        valid_units = ['days', 'weeks', 'months']
        unit_time = data.get('unit_time', 'days')
        if unit_time not in valid_units:
            errors.append(f"Unit time must be one of: {valid_units}")
        validated['unit_time'] = unit_time
        
        # Validar demanda histórica
        demand_history = data.get('demand_history', [])
        if not isinstance(demand_history, list) or len(demand_history) < 5:
            errors.append("Demand history must be a list with at least 5 values")
        else:
            try:
                validated['demand_history'] = [float(x) for x in demand_history if x is not None]
            except (ValueError, TypeError):
                errors.append("Demand history contains invalid values")
        
        # Validar nivel de confianza
        confidence = data.get('confidence_level', 0.95)
        try:
            confidence = float(confidence)
            if confidence < 0.1 or confidence > 0.99:
                errors.append("Confidence level must be between 0.1 and 0.99")
            validated['confidence_level'] = confidence
        except (ValueError, TypeError):
            validated['confidence_level'] = 0.95
        
        # Validar semilla aleatoria
        seed = data.get('random_seed')
        if seed is not None:
            try:
                validated['random_seed'] = int(seed)
            except (ValueError, TypeError):
                validated['random_seed'] = None
        
        if errors:
            raise ValueError(f"Simulation data validation failed: {errors}")
        
        return validated
    
    def _prepare_demand_configuration(self, demand_history: List[float], 
                                    fdp: ProbabilisticDensityFunction) -> Dict[str, Any]:
        """Preparar configuración de demanda para simulación"""
        
        # Calcular estadísticas de demanda histórica
        demand_array = np.array(demand_history)
        demand_stats = {
            'mean': float(np.mean(demand_array)),
            'std': float(np.std(demand_array)),
            'min': float(np.min(demand_array)),
            'max': float(np.max(demand_array)),
            'median': float(np.median(demand_array)),
            'cv': float(np.std(demand_array) / np.mean(demand_array)) if np.mean(demand_array) > 0 else 0
        }
        
        # Configurar distribución según FDP
        distribution_config = {
            'type': fdp.distribution_type,
            'name': fdp.get_distribution_type_display(),
            'parameters': self._calculate_distribution_parameters(demand_history, fdp.distribution_type)
        }
        
        # Detectar tendencia
        if len(demand_history) >= 5:
            x = np.arange(len(demand_history))
            trend_slope = np.polyfit(x, demand_history, 1)[0]
            trend_config = {
                'has_trend': abs(trend_slope) > 0.01,
                'slope': float(trend_slope),
                'direction': 'increasing' if trend_slope > 0 else 'decreasing' if trend_slope < 0 else 'stable'
            }
        else:
            trend_config = {'has_trend': False, 'slope': 0, 'direction': 'stable'}
        
        # Detectar estacionalidad (simplificado)
        seasonality_config = self._detect_seasonality(demand_history)
        
        return {
            'demand_stats': demand_stats,
            'distribution': distribution_config,
            'trend': trend_config,
            'seasonality': seasonality_config,
            'historical_data': demand_history
        }
    
    def _calculate_distribution_parameters(self, data: List[float], dist_type: int) -> Dict[str, float]:
        """Calcular parámetros óptimos para la distribución especificada"""
        
        data_array = np.array(data)
        
        if dist_type == 1:  # Normal
            return {
                'mean': float(np.mean(data_array)),
                'std': float(np.std(data_array))
            }
        elif dist_type == 2:  # Exponencial
            return {
                'lambda': float(1 / np.mean(data_array)) if np.mean(data_array) > 0 else 1
            }
        elif dist_type == 3:  # Log-Normal
            log_data = np.log(data_array[data_array > 0])
            return {
                'mu': float(np.mean(log_data)),
                'sigma': float(np.std(log_data))
            }
        elif dist_type == 4:  # Gamma
            # Método de momentos para Gamma
            mean_val = np.mean(data_array)
            var_val = np.var(data_array)
            if var_val > 0:
                scale = var_val / mean_val
                shape = mean_val / scale
            else:
                scale = shape = 1
            return {
                'shape': float(shape),
                'scale': float(scale)
            }
        elif dist_type == 5:  # Uniforme
            return {
                'min': float(np.min(data_array)),
                'max': float(np.max(data_array))
            }
        else:
            # Por defecto usar normal
            return {
                'mean': float(np.mean(data_array)),
                'std': float(np.std(data_array))
            }
    
    def _detect_seasonality(self, demand_history: List[float]) -> Dict[str, Any]:
        """Detectar patrones estacionales en la demanda (simplificado)"""
        
        if len(demand_history) < 14:  # Necesitamos al menos 2 semanas
            return {'has_seasonality': False, 'period': 7, 'amplitude': 0}
        
        # Buscar periodicidad semanal (7 días)
        weekly_pattern = []
        for i in range(7):
            day_values = [demand_history[j] for j in range(i, len(demand_history), 7)]
            if day_values:
                weekly_pattern.append(np.mean(day_values))
        
        if len(weekly_pattern) == 7:
            weekly_std = np.std(weekly_pattern)
            weekly_mean = np.mean(weekly_pattern)
            cv_weekly = weekly_std / weekly_mean if weekly_mean > 0 else 0
            
            # Si hay variación significativa entre días de la semana
            has_seasonality = cv_weekly > 0.1
            
            return {
                'has_seasonality': has_seasonality,
                'period': 7,
                'amplitude': weekly_std,
                'pattern': weekly_pattern,
                'cv': cv_weekly
            }
        
        return {'has_seasonality': False, 'period': 7, 'amplitude': 0}
    
    def _prepare_simulation_context(self, simulation: Simulation) -> Dict[str, Any]:
        """Preparar contexto completo para la simulación"""
        
        # Cargar variables extraídas
        try:
            extracted_variables = json.loads(simulation.extracted_variables)
        except (json.JSONDecodeError, AttributeError):
            logger.warning("Could not load extracted variables, using mapper")
            extracted_variables = self.variable_mapper.extract_all_variables(
                simulation.fk_questionary_result
            )
        
        # Cargar configuración de demanda
        try:
            demand_config = json.loads(simulation.demand_config)
        except (json.JSONDecodeError, AttributeError):
            logger.warning("Could not load demand config, regenerating")
            demand_history = json.loads(simulation.demand_history)
            demand_config = self._prepare_demand_configuration(
                demand_history, simulation.fk_fdp
            )
        
        # Preparar generador de demanda
        demand_generator = self._create_demand_generator(demand_config, simulation)
        
        # Estado inicial
        initial_state = {
            'IPF': extracted_variables.get('IPF', 1000),
            'II': extracted_variables.get('II', 5000),
            '_day': 1,
            '_simulation_id': simulation.id
        }
        
        return {
            'simulation': simulation,
            'variables': extracted_variables,
            'demand_config': demand_config,
            'demand_generator': demand_generator,
            'initial_state': initial_state,
            'total_days': simulation.quantity_time
        }
    
    def _create_demand_generator(self, demand_config: Dict[str, Any], 
                               simulation: Simulation) -> callable:
        """Crear generador de demanda basado en la configuración"""
        
        # Configurar semilla aleatoria si está especificada
        if simulation.random_seed:
            np.random.seed(simulation.random_seed)
        
        dist_config = demand_config['distribution']
        trend_config = demand_config['trend']
        seasonality_config = demand_config['seasonality']
        
        def generate_demand(day: int) -> float:
            """Generar demanda para un día específico"""
            
            # Demanda base desde distribución
            if dist_config['type'] == 1:  # Normal
                params = dist_config['parameters']
                base_demand = np.random.normal(params['mean'], params['std'])
            elif dist_config['type'] == 2:  # Exponencial
                params = dist_config['parameters']
                base_demand = np.random.exponential(1 / params['lambda'])
            elif dist_config['type'] == 5:  # Uniforme
                params = dist_config['parameters']
                base_demand = np.random.uniform(params['min'], params['max'])
            else:  # Por defecto normal
                params = dist_config['parameters']
                base_demand = np.random.normal(params.get('mean', 100), params.get('std', 20))
            
            # Aplicar tendencia
            if trend_config['has_trend']:
                trend_factor = 1 + (trend_config['slope'] * day / 100)
                base_demand *= trend_factor
            
            # Aplicar estacionalidad
            if seasonality_config['has_seasonality']:
                day_of_cycle = (day - 1) % seasonality_config['period']
                seasonal_pattern = seasonality_config.get('pattern', [1] * 7)
                if day_of_cycle < len(seasonal_pattern):
                    seasonal_factor = seasonal_pattern[day_of_cycle] / np.mean(seasonal_pattern)
                    base_demand *= seasonal_factor
            
            # Asegurar valor positivo
            return max(1.0, base_demand)
        
        return generate_demand
    
    def _execute_daily_simulation(self, simulation: Simulation, 
                                context: Dict[str, Any]) -> bool:
        """Ejecutar simulación día por día con motor de ecuaciones"""
        
        try:
            variables = context['variables']
            demand_generator = context['demand_generator']
            total_days = context['total_days']
            current_state = context['initial_state'].copy()
            
            # Lista para almacenar resultados en lotes
            results_batch = []
            demand_history = []
            
            logger.info(f"Starting daily simulation for {total_days} days")
            
            for day in range(1, total_days + 1):
                try:
                    # Generar demanda para este día
                    current_demand = demand_generator(day)
                    demand_history.append(current_demand)
                    
                    # Ejecutar simulación completa del día
                    day_results = self.math_engine.simulate_complete_day(
                        current_demand=current_demand,
                        previous_state=current_state,
                        parameters=variables,
                        demand_history=demand_history[-30:]  # Últimos 30 días para tendencias
                    )
                    
                    # Validar resultados del día
                    validation_report = self.math_engine.validate_calculation_completeness(day_results)
                    
                    if validation_report['calculation_quality'] in ['INCOMPLETE', 'INVALID']:
                        logger.warning(f"Day {day} calculation issues: {validation_report}")
                        
                        # Intentar corrección usando valores del día anterior
                        if day > 1 and results_batch:
                            day_results = self._correct_day_results(day_results, results_batch[-1])
                    
                    # Crear resultado de simulación
                    result_data = self._prepare_result_data(
                        simulation, day, current_demand, day_results, validation_report
                    )
                    
                    results_batch.append(result_data)
                    
                    # Actualizar estado para el siguiente día
                    current_state = day_results.get('_state', current_state)
                    current_state['_day'] = day + 1
                    
                    # Guardar en lotes para optimizar BD
                    if len(results_batch) >= self.config['batch_size'] or day == total_days:
                        self._save_results_batch(results_batch)
                        results_batch = []
                    
                    # Log progreso cada 10%
                    if day % max(1, total_days // 10) == 0:
                        logger.info(f"Simulation progress: {day}/{total_days} days ({day/total_days*100:.1f}%)")
                
                except Exception as e:
                    logger.error(f"Error in day {day} simulation: {str(e)}")
                    
                    # Crear resultado de error
                    error_result = self._create_error_result(simulation, day, current_demand, str(e))
                    results_batch.append(error_result)
                    
                    # Continuar con el siguiente día usando estado anterior
                    continue
            
            # Guardar resultados finales si quedan
            if results_batch:
                self._save_results_batch(results_batch)
            
            # Generar reporte final
            final_report = self._generate_simulation_report(simulation, demand_history)
            self._save_simulation_report(simulation, final_report)
            
            logger.info(f"Daily simulation completed for simulation {simulation.id}")
            return True
            
        except Exception as e:
            logger.error(f"Critical error in daily simulation: {str(e)}")
            return False
    
    def _correct_day_results(self, current_results: Dict[str, Any], 
                           previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Corregir resultados del día usando datos del día anterior"""
        
        corrected = current_results.copy()
        corrections_applied = []
        
        # Variables críticas que deben tener valores válidos
        critical_vars = ['TPV', 'IT', 'GT', 'TG', 'NSC', 'PE', 'IPF', 'II']
        
        for var in critical_vars:
            if var not in corrected or corrected[var] is None or np.isnan(corrected[var]):
                if 'variables' in previous_results and var in previous_results['variables']:
                    corrected[var] = previous_results['variables'][var] * 0.95  # 5% decay
                    corrections_applied.append(f"{var} from previous day")
                elif var in previous_results:
                    corrected[var] = previous_results[var] * 0.95
                    corrections_applied.append(f"{var} from previous day")
        
        # Corregir márgenes extremos
        if 'NR' in corrected and (corrected['NR'] < -1 or corrected['NR'] > 1):
            if 'IT' in corrected and 'GT' in corrected and corrected['IT'] > 0:
                corrected['NR'] = max(-0.5, min(0.8, corrected['GT'] / corrected['IT']))
                corrections_applied.append("NR recalculated")
        
        if 'MB' in corrected and (corrected['MB'] < -1 or corrected['MB'] > 1):
            if 'IT' in corrected and 'IB' in corrected and corrected['IT'] > 0:
                corrected['MB'] = max(-0.3, min(0.9, corrected['IB'] / corrected['IT']))
                corrections_applied.append("MB recalculated")
        
        if corrections_applied:
            logger.info(f"Applied corrections: {corrections_applied}")
            corrected['_corrections_applied'] = corrections_applied
        
        return corrected
    
    def _prepare_result_data(self, simulation: Simulation, day: int, 
                           demand: float, day_results: Dict[str, Any],
                           validation_report: Dict[str, Any]) -> Dict[str, Any]:
        """Preparar datos del resultado para guardar en BD"""
        
        # Extraer variables principales
        variables = {k: v for k, v in day_results.items() if not k.startswith('_')}
        
        # Metadatos del cálculo
        metadata = day_results.get('_metadata', {})
        metadata.update({
            'validation_quality': validation_report['calculation_quality'],
            'variables_calculated': validation_report['total_variables_calculated'],
            'warnings': validation_report.get('warnings', []),
            'day_number': day
        })
        
        return {
            'fk_simulation': simulation,
            'date': simulation.date_created + timedelta(days=day-1),
            'demand_mean': demand,
            'demand_std_deviation': day_results.get('DSD', demand * 0.1),
            'variables': variables,
            'metadata': metadata,
            'is_active': True,
            'calculation_quality': validation_report['calculation_quality']
        }
    
    def _create_error_result(self, simulation: Simulation, day: int, 
                           demand: float, error_message: str) -> Dict[str, Any]:
        """Crear resultado de error para un día fallido"""
        
        # Variables mínimas de fallback
        fallback_variables = self.math_engine.calculate_basic_variables(demand, day)
        
        return {
            'fk_simulation': simulation,
            'date': simulation.date_created + timedelta(days=day-1),
            'demand_mean': demand,
            'demand_std_deviation': demand * 0.1,
            'variables': fallback_variables,
            'metadata': {
                'calculation_method': 'error_fallback',
                'error_message': error_message,
                'day_number': day,
                'calculation_quality': 'ERROR'
            },
            'is_active': True,
            'calculation_quality': 'ERROR'
        }
    
    @transaction.atomic
    def _save_results_batch(self, results_batch: List[Dict[str, Any]]) -> None:
        """Guardar lote de resultados en la base de datos"""
        
        try:
            result_objects = []
            
            for result_data in results_batch:
                result_obj = ResultSimulation(
                    fk_simulation=result_data['fk_simulation'],
                    date=result_data['date'],
                    demand_mean=result_data['demand_mean'],
                    demand_std_deviation=result_data['demand_std_deviation'],
                    variables=json.dumps(result_data['variables']),
                    metadata=json.dumps(result_data['metadata']),
                    is_active=result_data['is_active']
                )
                result_objects.append(result_obj)
            
            # Inserción en lote para mejor performance
            ResultSimulation.objects.bulk_create(result_objects, batch_size=50)
            
            logger.debug(f"Saved batch of {len(result_objects)} results to database")
            
        except Exception as e:
            logger.error(f"Error saving results batch: {str(e)}")
            
            # Intentar guardar uno por uno en caso de error
            for result_data in results_batch:
                try:
                    ResultSimulation.objects.create(
                        fk_simulation=result_data['fk_simulation'],
                        date=result_data['date'],
                        demand_mean=result_data['demand_mean'],
                        demand_std_deviation=result_data['demand_std_deviation'],
                        variables=json.dumps(result_data['variables']),
                        metadata=json.dumps(result_data['metadata']),
                        is_active=result_data['is_active']
                    )
                except Exception as individual_error:
                    logger.error(f"Error saving individual result: {str(individual_error)}")
    
    def _generate_simulation_report(self, simulation: Simulation, 
                                  demand_history: List[float]) -> Dict[str, Any]:
        """Generar reporte final de la simulación"""
        
        try:
            # Obtener todos los resultados
            results = ResultSimulation.objects.filter(
                fk_simulation=simulation,
                is_active=True
            ).order_by('date')
            
            if not results.exists():
                return {'error': 'No results found for simulation'}
            
            # Estadísticas de demanda
            demand_stats = {
                'mean': np.mean(demand_history),
                'std': np.std(demand_history),
                'min': np.min(demand_history),
                'max': np.max(demand_history),
                'cv': np.std(demand_history) / np.mean(demand_history) if np.mean(demand_history) > 0 else 0
            }
            
            # Estadísticas de performance
            performance_stats = self._calculate_performance_statistics(results)
            
            # Análisis de calidad de cálculo
            quality_analysis = self._analyze_calculation_quality(results)
            
            # Resumen de variables faltantes
            missing_variables_summary = self._analyze_missing_variables(results)
            
            report = {
                'simulation_id': simulation.id,
                'execution_date': timezone.now().isoformat(),
                'total_days_simulated': len(demand_history),
                'total_results_created': results.count(),
                'demand_statistics': demand_stats,
                'performance_statistics': performance_stats,
                'calculation_quality': quality_analysis,
                'missing_variables_analysis': missing_variables_summary,
                'execution_success_rate': results.count() / simulation.quantity_time * 100,
                'variables_coverage': self._calculate_variables_coverage(results)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating simulation report: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_performance_statistics(self, results) -> Dict[str, Any]:
        """Calcular estadísticas de performance de la simulación"""
        
        performance = {
            'financial': {},
            'operational': {},
            'service': {}
        }
        
        try:
            # Extraer datos financieros
            profits = []
            revenues = []
            margins = []
            
            # Extraer datos operacionales
            efficiency_values = []
            service_levels = []
            
            for result in results:
                if result.variables:
                    try:
                        variables = json.loads(result.variables) if isinstance(result.variables, str) else result.variables
                        
                        # Financieros
                        if 'GT' in variables and variables['GT'] is not None:
                            profits.append(float(variables['GT']))
                        if 'IT' in variables and variables['IT'] is not None:
                            revenues.append(float(variables['IT']))
                        if 'NR' in variables and variables['NR'] is not None:
                            margins.append(float(variables['NR']))
                        
                        # Operacionales
                        if 'EOG' in variables and variables['EOG'] is not None:
                            efficiency_values.append(float(variables['EOG']))
                        if 'NSC' in variables and variables['NSC'] is not None:
                            service_levels.append(float(variables['NSC']))
                            
                    except (json.JSONDecodeError, ValueError, TypeError):
                        continue
            
            # Calcular estadísticas financieras
            if profits:
                performance['financial'] = {
                    'total_profit': sum(profits),
                    'average_daily_profit': np.mean(profits),
                    'profit_volatility': np.std(profits),
                    'profitable_days': sum(1 for p in profits if p > 0),
                    'profit_trend': self._calculate_trend(profits)
                }
            
            if revenues:
                performance['financial']['total_revenue'] = sum(revenues)
                performance['financial']['average_daily_revenue'] = np.mean(revenues)
            
            if margins:
                performance['financial']['average_margin'] = np.mean(margins)
                performance['financial']['margin_stability'] = 1 - (np.std(margins) / abs(np.mean(margins))) if np.mean(margins) != 0 else 0
            
            # Calcular estadísticas operacionales
            if efficiency_values:
                performance['operational'] = {
                    'average_efficiency': np.mean(efficiency_values),
                    'efficiency_consistency': 1 - np.std(efficiency_values),
                    'days_above_target': sum(1 for e in efficiency_values if e > 0.85)
                }
            
            # Calcular estadísticas de servicio
            if service_levels:
                performance['service'] = {
                    'average_service_level': np.mean(service_levels),
                    'service_consistency': 1 - np.std(service_levels),
                    'days_above_95_percent': sum(1 for s in service_levels if s > 0.95)
                }
            
        except Exception as e:
            logger.error(f"Error calculating performance statistics: {str(e)}")
        
        return performance
    
    def _analyze_calculation_quality(self, results) -> Dict[str, Any]:
        """Analizar la calidad de los cálculos realizados"""
        
        quality_counts = {
            'COMPLETE': 0,
            'WARNING': 0,
            'INCOMPLETE': 0,
            'INVALID': 0,
            'ERROR': 0
        }
        
        total_results = results.count()
        corrections_applied = 0
        
        for result in results:
            # Obtener calidad desde metadata
            try:
                if result.metadata:
                    metadata = json.loads(result.metadata) if isinstance(result.metadata, str) else result.metadata
                    quality = metadata.get('validation_quality', 'UNKNOWN')
                    
                    if quality in quality_counts:
                        quality_counts[quality] += 1
                    
                    if metadata.get('corrections_applied'):
                        corrections_applied += 1
                        
            except (json.JSONDecodeError, ValueError):
                quality_counts['ERROR'] += 1
        
        # Calcular porcentajes
        quality_percentages = {
            quality: (count / total_results * 100) if total_results > 0 else 0 
            for quality, count in quality_counts.items()
        }
        
        return {
            'quality_distribution': quality_counts,
            'quality_percentages': quality_percentages,
            'overall_quality_score': (
                quality_counts['COMPLETE'] * 1.0 + 
                quality_counts['WARNING'] * 0.8 + 
                quality_counts['INCOMPLETE'] * 0.5 + 
                quality_counts['INVALID'] * 0.2
            ) / total_results if total_results > 0 else 0,
            'corrections_applied': corrections_applied,
            'correction_rate': corrections_applied / total_results * 100 if total_results > 0 else 0
        }
    
    def _analyze_missing_variables(self, results) -> Dict[str, Any]:
        """Analizar variables faltantes en los resultados"""
        
        expected_variables = set(self.math_engine.equation_solver.equations.keys())
        missing_count = {var: 0 for var in expected_variables}
        total_days = results.count()
        
        for result in results:
            try:
                if result.variables:
                    variables = json.loads(result.variables) if isinstance(result.variables, str) else result.variables
                    present_variables = set(variables.keys())
                    missing_vars = expected_variables - present_variables
                    
                    for var in missing_vars:
                        missing_count[var] += 1
                        
            except (json.JSONDecodeError, ValueError):
                # Si no se pueden parsear las variables, contar todas como faltantes
                for var in expected_variables:
                    missing_count[var] += 1
        
        # Calcular porcentajes de variables faltantes
        missing_percentages = {
            var: (count / total_days * 100) if total_days > 0 else 0 
            for var, count in missing_count.items()
        }
        
        # Identificar variables más problemáticas
        most_missing = sorted(missing_percentages.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'missing_variables_count': missing_count,
            'missing_percentages': missing_percentages,
            'most_problematic_variables': most_missing,
            'overall_variable_coverage': (1 - sum(missing_count.values()) / (len(expected_variables) * total_days)) * 100 if total_days > 0 else 0
        }
    
    def _calculate_variables_coverage(self, results) -> Dict[str, float]:
        """Calcular cobertura de variables por categoría"""
        
        categories = {
            'financial': ['GT', 'IT', 'TG', 'NR', 'MB', 'RI'],
            'operational': ['TPV', 'QPL', 'NSC', 'PE', 'EOG'],
            'inventory': ['IPF', 'II', 'IOP', 'RTI'],
            'costs': ['GO', 'GG', 'CTAI', 'CVU']
        }
        
        coverage_by_category = {}
        total_days = results.count()
        
        for category, variables in categories.items():
            category_coverage = 0
            
            for result in results:
                try:
                    if result.variables:
                        variables_dict = json.loads(result.variables) if isinstance(result.variables, str) else result.variables
                        present_vars = sum(1 for var in variables if var in variables_dict and variables_dict[var] is not None)
                        category_coverage += present_vars / len(variables)
                except (json.JSONDecodeError, ValueError):
                    continue
            
            coverage_by_category[category] = (category_coverage / total_days * 100) if total_days > 0 else 0
        
        return coverage_by_category
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calcular tendencia de una serie de valores"""
        
        if len(values) < 3:
            return 'insufficient_data'
        
        try:
            x = np.arange(len(values))
            slope = np.polyfit(x, values, 1)[0]
            
            if slope > 0.01:
                return 'increasing'
            elif slope < -0.01:
                return 'decreasing'
            else:
                return 'stable'
        except:
            return 'unknown'
    
    def _save_simulation_report(self, simulation: Simulation, report: Dict[str, Any]) -> None:
        """Guardar reporte de simulación en la BD"""
        
        try:
            simulation.execution_report = json.dumps(report)
            simulation.save(update_fields=['execution_report'])
            logger.info(f"Simulation report saved for simulation {simulation.id}")
        except Exception as e:
            logger.error(f"Error saving simulation report: {str(e)}")
    
    def get_simulation_status(self, simulation_id: int) -> Dict[str, Any]:
        """Obtener estado actual de una simulación"""
        
        try:
            simulation = Simulation.objects.get(id=simulation_id)
            results_count = ResultSimulation.objects.filter(
                fk_simulation=simulation,
                is_active=True
            ).count()
            
            progress_percentage = (results_count / simulation.quantity_time * 100) if simulation.quantity_time > 0 else 0
            
            status = {
                'simulation_id': simulation_id,
                'is_active': simulation.is_active,
                'is_completed': getattr(simulation, 'is_completed', False),
                'total_days': simulation.quantity_time,
                'completed_days': results_count,
                'progress_percentage': min(progress_percentage, 100),
                'created_at': simulation.date_created.isoformat(),
                'status': 'completed' if progress_percentage >= 100 else 'running' if simulation.is_active else 'stopped'
            }
            
            return status
            
        except Simulation.DoesNotExist:
            return {'error': 'Simulation not found'}
        except Exception as e:
            return {'error': str(e)}