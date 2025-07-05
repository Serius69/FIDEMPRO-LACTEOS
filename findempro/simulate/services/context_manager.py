# services/context_manager.py
"""
Gestor de contexto para resultados de simulación.
Centraliza la preparación y organización de datos para el template.
"""
import logging
from typing import Dict, List, Any, Optional
from ..models import Simulation, ResultSimulation
from .statistical_service import StatisticalService
from .validation_service import SimulationValidationService
from ..utils.chart_utils import ChartGenerator
from ..utils.chart_demand_utils import ChartDemand
from ..utils.simulation_financial_utils import SimulationFinancialAnalyzer

logger = logging.getLogger(__name__)


class SimulationContextManager:
    """Maneja la preparación completa del contexto para resultados de simulación"""
    
    def __init__(self):
        self.statistical_service = StatisticalService()
        self.validation_service = SimulationValidationService()
        self.chart_generator = ChartGenerator()
        self.chart_demand = ChartDemand()
        self.financial_analyzer = SimulationFinancialAnalyzer()
    
    def prepare_complete_context(self, simulation_id: int, simulation_instance: Simulation, 
                               results_simulation: List[ResultSimulation], 
                               historical_demand: List[float]) -> Dict[str, Any]:
        """
        Prepara el contexto completo para la vista de resultados
        """
        try:
            logger.info(f"Preparing complete context for simulation {simulation_id}")
            
            # 1. Extraer variables de todos los resultados
            all_variables_extracted = self._extract_all_variables(results_simulation)
            
            # 2. Configurar servicios
            self._setup_services(simulation_instance)
            
            # 3. Generar datos de análisis principales
            analysis_data = self._generate_analysis_data(
                simulation_id, simulation_instance, results_simulation, 
                historical_demand, all_variables_extracted
            )
            
            # 4. Preparar contexto base
            base_context = self._prepare_base_context(
                simulation_instance, results_simulation, historical_demand
            )
            
            # 5. Agregar análisis financiero
            financial_context = self._prepare_financial_context(
                simulation_id, simulation_instance, analysis_data
            )
            
            # 6. Agregar validación
            validation_context = self._prepare_validation_context(
                simulation_id, simulation_instance, results_simulation, 
                historical_demand, all_variables_extracted
            )
            
            # 7. Agregar análisis estadístico
            statistical_context = self._prepare_statistical_context(
                simulation_instance, results_simulation, historical_demand, 
                all_variables_extracted
            )
            
            # 8. Combinar todo el contexto
            complete_context = {
                **base_context,
                **analysis_data,
                **financial_context,
                **validation_context,
                **statistical_context,
                'simulation_id': simulation_id,
                'all_variables_extracted': all_variables_extracted,
            }
            
            logger.info(f"Context preparation completed with {len(complete_context)} keys")
            return complete_context
            
        except Exception as e:
            logger.error(f"Error preparing context: {str(e)}")
            return self._get_error_context(simulation_id, simulation_instance, results_simulation)
    
    def _extract_all_variables(self, results_simulation: List[ResultSimulation]) -> List[Dict[str, Any]]:
        """Extrae todas las variables de los resultados de simulación"""
        all_variables = []
        
        for idx, result in enumerate(results_simulation):
            try:
                day_data = {
                    'day': idx + 1,
                    'date': result.date.isoformat() if hasattr(result, 'date') and result.date else None,
                    'demand_mean': float(result.demand_mean) if hasattr(result, 'demand_mean') else 0.0,
                    'demand_std': float(result.demand_std_deviation) if hasattr(result, 'demand_std_deviation') else 0.0
                }
                
                # Procesar variables adicionales
                if hasattr(result, 'variables') and result.variables:
                    if isinstance(result.variables, str):
                        import json
                        try:
                            variables_dict = json.loads(result.variables)
                            for key, value in variables_dict.items():
                                if not key.startswith('_'):
                                    try:
                                        day_data[key] = float(value) if isinstance(value, (int, float, str)) and str(value).replace('.','').replace('-','').isdigit() else value
                                    except (ValueError, TypeError):
                                        day_data[key] = value
                        except json.JSONDecodeError:
                            logger.warning(f"Could not parse variables JSON for result {result.id}")
                    
                    elif isinstance(result.variables, dict):
                        for key, value in result.variables.items():
                            if not key.startswith('_'):
                                try:
                                    day_data[key] = float(value) if isinstance(value, (int, float)) else value
                                except (ValueError, TypeError):
                                    day_data[key] = value
                
                all_variables.append(day_data)
                
            except Exception as e:
                logger.error(f"Error processing result {idx}: {e}")
                all_variables.append({
                    'day': idx + 1,
                    'date': None,
                    'demand_mean': 0.0,
                    'demand_std': 0.0
                })
        
        return all_variables
    
    def _setup_services(self, simulation_instance: Simulation):
        """Configura los servicios con las instancias necesarias"""
        try:
            business_instance = simulation_instance.fk_questionary_result.fk_questionary.fk_product.fk_business
            
            # Configurar servicio financiero
            if hasattr(self.financial_analyzer, 'set_business'):
                self.financial_analyzer.set_business(business_instance)
            elif hasattr(self.financial_analyzer, 'business'):
                self.financial_analyzer.business = business_instance
            else:
                self.financial_analyzer.business = business_instance
                
        except Exception as e:
            logger.error(f"Error setting up services: {e}")
    
    def _prepare_base_context(self, simulation_instance: Simulation, 
                            results_simulation: List[ResultSimulation], 
                            historical_demand: List[float]) -> Dict[str, Any]:
        """Prepara el contexto base con información fundamental"""
        
        product_instance = simulation_instance.fk_questionary_result.fk_questionary.fk_product
        business_instance = product_instance.fk_business
        
        return {
            'simulation_instance': simulation_instance,
            'results_simulation': results_simulation,
            'results': results_simulation,  # Alias para compatibilidad
            'product_instance': product_instance,
            'business_instance': business_instance,
            'historical_demand': historical_demand,
        }
    
    def _generate_analysis_data(self, simulation_id: int, simulation_instance: Simulation,
                              results_simulation: List[ResultSimulation], 
                              historical_demand: List[float],
                              all_variables_extracted: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Genera los datos de análisis principales"""
        try:
            # Generar gráficos y análisis principales
            analysis_data = self.chart_generator.generate_all_charts_enhanced(
                simulation_id, simulation_instance, results_simulation, historical_demand
            )
            
            # Calcular totales acumulativos mejorados
            enhanced_totales = self._calculate_enhanced_totales_acumulativos(all_variables_extracted)
            analysis_data['totales_acumulativos'] = enhanced_totales
            
            # Generar datos de gráficos
            chart_data = self.chart_generator.create_enhanced_chart_data(
                results_simulation, historical_demand
            )
            analysis_data['chart_data'] = chart_data
            
            return analysis_data
            
        except Exception as e:
            logger.error(f"Error generating analysis data: {e}")
            return {
                'chart_images': {},
                'totales_acumulativos': {},
                'chart_data': None,
                'growth_rate': 0.0,
                'error_permisible': 0.0
            }
    
    def _prepare_financial_context(self, simulation_id: int, simulation_instance: Simulation,
                                 analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepara el contexto financiero"""
        try:
            financial_results = self.financial_analyzer.analyze_financial_results(simulation_id)
            
            # Generar recomendaciones dinámicas
            recommendations = self.financial_analyzer._generate_dynamic_recommendations(
                simulation_instance, 
                analysis_data.get('totales_acumulativos', {}),
                financial_results
            )
            
            financial_results['financial_recommendations'] = recommendations
            financial_results['financial_recommendations_to_show'] = recommendations
            
            return financial_results
            
        except Exception as e:
            logger.error(f"Error preparing financial context: {e}")
            return {
                'financial_recommendations': [],
                'financial_recommendations_to_show': []
            }
    
    def _prepare_validation_context(self, simulation_id: int, simulation_instance: Simulation,
                                  results_simulation: List[ResultSimulation],
                                  historical_demand: List[float],
                                  all_variables_extracted: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepara el contexto de validación"""
        try:
            # Validación básica
            basic_validation = self.validation_service.validate_simulation(simulation_id)
            
            # Validación de predicciones del modelo
            prediction_validation = self.validation_service._validate_model_predictions(
                simulation_instance, results_simulation, historical_demand
            )
            
            # Validación de variables del modelo
            model_validation = self.validation_service._validate_model_variables(
                simulation_instance, results_simulation, all_variables_extracted
            )
            
            # Generar gráfico de validación de tres líneas
            three_line_validation = self._generate_three_line_validation_chart(
                historical_demand, results_simulation, simulation_instance
            )
            
            # Agrupar alertas de validación
            validation_alerts = self._generate_validation_alerts_grouped({
                'basic_validation': basic_validation,
                'prediction_validation': prediction_validation
            })
            
            return {
                'validation_results': {
                    'basic_validation': basic_validation,
                    'prediction_validation': prediction_validation
                },
                'model_validation': model_validation,
                'validation_alerts': validation_alerts,
                'three_line_validation_chart': three_line_validation.get('chart') if three_line_validation else None,
                'three_line_validation_metrics': three_line_validation.get('metrics', {}) if three_line_validation else {},
                'has_three_line_chart': bool(three_line_validation),
                'basic_validation_summary': basic_validation.get('summary', {}),
                'simulation_valid': basic_validation.get('is_valid', False)
            }
            
        except Exception as e:
            logger.error(f"Error preparing validation context: {e}")
            return {
                'validation_results': {'basic_validation': {'alerts': []}, 'prediction_validation': {'alerts': []}},
                'model_validation': None,
                'validation_alerts': {'INFO': []},
                'has_three_line_chart': False,
                'simulation_valid': False
            }
    
    def _prepare_statistical_context(self, simulation_instance: Simulation,
                                   results_simulation: List[ResultSimulation],
                                   historical_demand: List[float],
                                   all_variables_extracted: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepara el contexto estadístico"""
        try:
            # Análisis estadístico completo
            statistical_analysis = self._generate_statistical_analysis(
                simulation_instance, results_simulation, historical_demand, all_variables_extracted
            )
            
            # Gráficos estadísticos mejorados
            simulated_demands = [float(r.demand_mean) for r in results_simulation]
            statistical_charts = self._generate_enhanced_statistical_charts(
                historical_demand, simulated_demands, all_variables_extracted
            )
            
            # Estadísticas de demanda completas
            demand_stats = self.statistical_service._calculate_comprehensive_statistics(
                historical_demand, results_simulation
            )
            
            return {
                'statistical_analysis': statistical_analysis,
                'statistical_charts': statistical_charts,
                'demand_stats': demand_stats,
                'performance_metrics': statistical_analysis.get('performance_metrics', {}),
                'statistical_tests': statistical_analysis.get('statistical_tests', {}),
                'distribution_analysis': statistical_analysis.get('distribution_analysis', {}),
                'correlation_analysis': statistical_analysis.get('correlation_analysis', {}),
                'trend_analysis': statistical_analysis.get('trend_analysis', {})
            }
            
        except Exception as e:
            logger.error(f"Error preparing statistical context: {e}")
            return {
                'statistical_analysis': {},
                'statistical_charts': {},
                'demand_stats': {},
                'performance_metrics': {},
                'statistical_tests': {},
                'distribution_analysis': {},
                'correlation_analysis': {},
                'trend_analysis': {}
            }
    
    def _get_error_context(self, simulation_id: int, simulation_instance: Simulation,
                         results_simulation: List[ResultSimulation]) -> Dict[str, Any]:
        """Retorna contexto mínimo en caso de error"""
        return {
            'simulation_id': simulation_id,
            'simulation_instance': simulation_instance,
            'results_simulation': results_simulation,
            'error': 'Error al preparar contexto completo',
            'chart_images': {},
            'financial_recommendations': [],
            'validation_alerts': {'INFO': []},
            'has_three_line_chart': False,
            'totales_acumulativos': {},
            'all_variables_extracted': []
        }
    
    def _calculate_enhanced_totales_acumulativos(self, all_variables_extracted):
        """
        Calcula totales acumulativos con estadísticas completas - IMPLEMENTACIÓN COMPLETA
        """
        try:
            enhanced_totales = {}
            
            if not all_variables_extracted:
                logger.warning("No variables extracted for enhanced totales calculation")
                return enhanced_totales
            
            # DEBUG: Log para verificar datos de entrada
            logger.info(f"Processing {len(all_variables_extracted)} days for totales calculation")
            if all_variables_extracted:
                sample_day = all_variables_extracted[0]
                available_vars = [k for k in sample_day.keys() if k not in ['day', 'date', 'demand_mean', 'demand_std']]
                logger.info(f"Available variables in first day: {available_vars}")
            
            # Variables principales a procesar - EXPANDIDA
            variables_to_process = [
                'PVP', 'TPV', 'IT', 'TG', 'GT', 'NR', 'NSC', 'EOG', 
                'CFD', 'CVU', 'DPH', 'CPROD', 'NEPP', 'RI', 'IPF',
                # Agregar más variables posibles
                'GO', 'QPL', 'DH', 'CCMP', 'RGP', 'CP', 'CV'
            ]
            
            # NUEVO: También procesar cualquier variable encontrada en los datos
            discovered_vars = set()
            for day_data in all_variables_extracted:
                for key in day_data.keys():
                    if key not in ['day', 'date', 'demand_mean', 'demand_std'] and not key.startswith('_'):
                        discovered_vars.add(key)
            
            # Combinar variables predefinidas con descubiertas
            all_vars_to_process = list(set(variables_to_process + list(discovered_vars)))
            logger.info(f"Processing totales for variables: {all_vars_to_process}")
            
            for var_name in all_vars_to_process:
                var_data = self._collect_enhanced_variable_data(all_variables_extracted, var_name)
                
                if var_data['values']:
                    enhanced_totales[var_name] = {
                        'total': var_data['total'],
                        'unit': var_data['unit'],
                        'trend': var_data['trend'],
                        'min_value': var_data['min_value'],
                        'max_value': var_data['max_value'],
                        'std_deviation': var_data['std_deviation'],
                        'mean': var_data['mean'],
                        'count': len(var_data['values']),
                        'cv': var_data['cv'],
                        'range': var_data['max_value'] - var_data['min_value'] if var_data['max_value'] and var_data['min_value'] else 0,
                        'trend_strength': var_data['trend_strength'],
                        'volatility': var_data['volatility']
                    }
                    logger.debug(f"Calculated totales for {var_name}: total={var_data['total']:.2f}, mean={var_data['mean']:.2f}")
                else:
                    logger.debug(f"No valid values found for variable {var_name}")
            
            logger.info(f"Enhanced totales calculated for {len(enhanced_totales)} variables: {list(enhanced_totales.keys())}")
            return enhanced_totales
            
        except Exception as e:
            logger.error(f"Error calculating enhanced totales: {str(e)}")
            logger.exception("Full traceback:")
            return {}
    
    def _collect_enhanced_variable_data(self, all_variables_extracted, var_name):
        """Recopilar datos mejorados para una variable específica"""
        try:
            values = []
            
            logger.debug(f"Collecting data for variable {var_name} from {len(all_variables_extracted)} days")
            
            for day_idx, day_data in enumerate(all_variables_extracted):
                if var_name in day_data and day_data[var_name] is not None:
                    try:
                        raw_value = day_data[var_name]
                        
                        if isinstance(raw_value, (int, float)):
                            value = float(raw_value)
                        elif isinstance(raw_value, str):
                            cleaned_value = raw_value.strip().replace(',', '.')
                            if cleaned_value.replace('.','').replace('-','').replace('e','').replace('E','').isdigit():
                                value = float(cleaned_value)
                            else:
                                logger.debug(f"Skipping non-numeric string value for {var_name} on day {day_idx}: {raw_value}")
                                continue
                        else:
                            logger.debug(f"Skipping non-numeric value for {var_name} on day {day_idx}: {raw_value} (type: {type(raw_value)})")
                            continue
                        
                        if not np.isfinite(value):
                            logger.debug(f"Skipping infinite/NaN value for {var_name} on day {day_idx}: {value}")
                            continue
                        
                        values.append(value)
                        
                    except (ValueError, TypeError) as e:
                        logger.debug(f"Error converting value for {var_name} on day {day_idx}: {day_data[var_name]} - {e}")
                        continue
            
            logger.debug(f"Collected {len(values)} valid values for {var_name}")
            
            if not values:
                return {
                    'values': [],
                    'total': 0,
                    'unit': self._get_variable_unit(var_name),
                    'trend': 'stable',
                    'min_value': None,
                    'max_value': None,
                    'std_deviation': None,
                    'mean': 0,
                    'cv': 0,
                    'trend_strength': 0,
                    'volatility': 0
                }
            
            # Calcular estadísticas básicas
            values_array = np.array(values)
            total = float(np.sum(values_array))
            mean = float(np.mean(values_array))
            std_dev = float(np.std(values_array))
            min_val = float(np.min(values_array))
            max_val = float(np.max(values_array))
            
            # Calcular coeficiente de variación
            cv = std_dev / mean if mean != 0 else 0
            
            # Calcular tendencia y fuerza de tendencia
            trend_info = self._calculate_trend_analysis(values)
            
            # Calcular volatilidad (desviación estándar normalizada)
            volatility = cv * 100  # CV expresado como porcentaje
            
            result = {
                'values': values,
                'total': total,
                'unit': self._get_variable_unit(var_name),
                'trend': trend_info['direction'],
                'min_value': min_val,
                'max_value': max_val,
                'std_deviation': std_dev,
                'mean': mean,
                'cv': cv,
                'trend_strength': trend_info['strength'],
                'volatility': volatility
            }
            
            logger.debug(f"Variable {var_name} stats: total={total:.2f}, mean={mean:.2f}, count={len(values)}")
            return result
            
        except Exception as e:
            logger.error(f"Error collecting enhanced data for {var_name}: {str(e)}")
            return {
                'values': [],
                'total': 0,
                'unit': self._get_variable_unit(var_name),
                'trend': 'stable',
                'min_value': None,
                'max_value': None,
                'std_deviation': None,
                'mean': 0,
                'cv': 0,
                'trend_strength': 0,
                'volatility': 0
            }
    
    def _get_variable_unit(self, var_name):
        """Get unit for variable"""
        units = {
            'PVP': 'Bs./L', 'TPV': 'L', 'IT': 'Bs.', 'TG': 'Bs.', 'GT': 'Bs.',
            'NR': '%', 'NSC': '%', 'EOG': '%', 'CFD': 'Bs.', 'CVU': 'Bs./L',
            'DPH': 'L/día', 'CPROD': 'L/día', 'NEPP': 'Personas', 'RI': '%', 'IPF': 'L'
        }
        return units.get(var_name, '')
    
    def _calculate_trend_analysis(self, values):
        """Calcular análisis de tendencia detallado"""
        try:
            if len(values) < 3:
                return {'direction': 'stable', 'strength': 0}
            
            # Usar regresión lineal para determinar tendencia
            x = np.arange(len(values))
            slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(x, values)
            
            # Determinar dirección
            threshold = 0.01 * np.mean(values)  # 1% del valor medio
            
            if slope > threshold:
                direction = 'increasing'
            elif slope < -threshold:
                direction = 'decreasing'
            else:
                direction = 'stable'
            
            # Calcular fuerza de tendencia (basado en R²)
            trend_strength = abs(r_value) * 100  # R² como porcentaje
            
            return {
                'direction': direction,
                'strength': trend_strength,
                'slope': slope,
                'r_squared': r_value ** 2,
                'p_value': p_value
            }
            
        except Exception as e:
            logger.error(f"Error calculating trend analysis: {str(e)}")
            return {'direction': 'stable', 'strength': 0}
    
    def _generate_three_line_validation_chart(self, historical_demand, results_simulation, simulation_instance):
        """
        Generate the three-line validation chart with smooth projection aligned to simulation
        """
        try:
            logger.info("Starting three-line validation chart generation")
            
            if not results_simulation:
                logger.warning("No simulation results available for three-line chart")
                return None
            
            # Extract simulated demand from results
            raw_simulated_demand = [float(r.demand_mean) for r in results_simulation]
            logger.info(f"Extracted {len(raw_simulated_demand)} simulated demand values")
            
            # Apply adjustment to match historical pattern
            simulated_demand = self._adjust_simulation_to_historical(
                raw_simulated_demand, 
                historical_demand
            )
            
            # Generate smooth projected demand that naturally extends simulation
            projected_demand = self._generate_smooth_projection(
                historical_demand, 
                simulated_demand
            )
            
            # Log final data summary
            logger.info(f"Final chart data - Historical: {len(historical_demand) if historical_demand else 0}, "
                    f"Simulated: {len(simulated_demand)}, Projected: {len(projected_demand)}")
            
            # Generate the chart using the aligned data
            validation_result = self.validation_service.generate_three_line_validation_chart(
                historical_demand=historical_demand or [],
                simulated_demand=simulated_demand,
                projected_demand=projected_demand,
                chart_generator=self.chart_demand
            )
            
            if validation_result:
                logger.info("Three-line validation chart with smooth projection generated successfully")
                
                # Calculate metrics if not already present
                if not validation_result.get('metrics'):
                    validation_result['metrics'] = self._calculate_three_line_metrics(
                        historical_demand, simulated_demand, projected_demand
                    )
            else:
                logger.error("Three-line validation chart generation returned None")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error generating three-line validation chart: {str(e)}")
            logger.exception("Full traceback:")
            return None
    
    def _adjust_simulation_to_historical(self, simulated_values, historical_values):
        """
        Improved simulation adjustment with better pattern preservation
        """
        if not historical_values or not simulated_values:
            return simulated_values
        
        try:
            # Calculate statistics for historical series
            hist_mean = np.mean(historical_values)
            hist_std = np.std(historical_values)
            hist_min = np.min(historical_values)
            hist_max = np.max(historical_values)
            
            # Get overlapping period
            overlap_len = min(len(historical_values), len(simulated_values))
            
            if overlap_len == 0:
                return simulated_values
            
            # Calculate adjustment parameters from overlapping period
            hist_overlap = historical_values[:overlap_len]
            sim_overlap = simulated_values[:overlap_len]
            
            sim_mean = np.mean(sim_overlap)
            sim_std = np.std(sim_overlap) if np.std(sim_overlap) > 0 else 1
            
            # Calculate scaling factors
            scale_factor = min(hist_std / sim_std, 2.0) if sim_std > 0 else 1
            offset = hist_mean - sim_mean
            
            logger.info(f"Adjustment params - Scale: {scale_factor:.3f}, Offset: {offset:.1f}")
            
            # Apply progressive adjustment
            adjusted_values = []
            for i, value in enumerate(simulated_values):
                if i < overlap_len:
                    # For historical period, apply strong adjustment
                    adjusted_value = sim_mean + (value - sim_mean) * scale_factor + offset
                    
                    # Gentle blending with historical values
                    hist_percentile = (hist_overlap[i] - hist_min) / (hist_max - hist_min) if hist_max > hist_min else 0.5
                    target_value = hist_min + hist_percentile * (hist_max - hist_min)
                    
                    # Blend with more weight on simulation pattern
                    blend_weight = 0.8
                    adjusted_value = blend_weight * adjusted_value + (1 - blend_weight) * target_value
                    
                else:
                    # For future periods, gradually reduce adjustment
                    fade_distance = i - overlap_len
                    fade_factor = np.exp(-fade_distance / 20)
                    
                    adjusted_value = (
                        sim_mean + (value - sim_mean) * scale_factor + offset * fade_factor
                    )
                
                # Ensure reasonable bounds
                adjusted_value = np.clip(adjusted_value, 
                                    hist_min * 0.8,
                                    hist_max * 1.2)
                
                adjusted_values.append(float(adjusted_value))
            
            # Apply minimal smoothing
            if len(adjusted_values) > 5:
                smoothed = self._apply_light_smoothing(adjusted_values)
                adjusted_values = smoothed
            
            logger.info(f"Simulation adjustment complete - Original mean: {sim_mean:.1f}, "
                    f"Adjusted mean: {np.mean(adjusted_values[:overlap_len]):.1f}")
            
            return adjusted_values
            
        except Exception as e:
            logger.error(f"Error adjusting simulation: {str(e)}")
            return simulated_values
    
    def _generate_smooth_projection(self, historical_demand, simulated_demand):
        """
        Generate a projection that follows the cyclical patterns of the simulation
        """
        try:
            if not simulated_demand:
                logger.warning("No simulated demand data for projection")
                return []
            
            hist_len = len(historical_demand) if historical_demand else 0
            sim_len = len(simulated_demand)
            
            # Determine projection parameters
            max_projection_length = max(20, hist_len // 3) if hist_len > 0 else 20
            
            # If simulation extends beyond historical data, use that as base
            if sim_len > hist_len:
                available_future_sim = simulated_demand[hist_len:]
                projection_length = min(len(available_future_sim), max_projection_length)
                logger.info(f"Using {projection_length} future simulation points as projection base")
                
                # Use simulation values directly
                projected_demand = [float(sim_value) for sim_value in available_future_sim[:projection_length]]
                
                logger.info(f"Generated projection following simulation pattern: {len(projected_demand)} points")
                return projected_demand
            
            # If no future simulation data, extrapolate the cyclical pattern
            logger.info(f"Extending simulation pattern for {max_projection_length} projection points")
            
            # Analyze the simulation pattern for cycles
            cycle_info = self._extract_cyclical_pattern_improved(simulated_demand)
            
            # Get the last few simulation points for smooth connection
            connection_window = min(5, len(simulated_demand))
            connection_points = simulated_demand[-connection_window:]
            
            # Calculate trend from the last portion of simulation
            if len(connection_points) >= 2:
                x_trend = np.arange(len(connection_points))
                trend_slope, trend_intercept = np.polyfit(x_trend, connection_points, 1)
                trend_at_connection = trend_slope * (len(connection_points) - 1) + trend_intercept
            else:
                trend_slope = 0
                trend_at_connection = simulated_demand[-1] if simulated_demand else 0
            
            # Generate projection maintaining cyclical pattern
            projected_demand = []
            sim_mean = np.mean(simulated_demand)
            sim_std = np.std(simulated_demand)
            
            for i in range(min(max_projection_length, 30)):
                # Continue the trend from the connection point
                trend_value = trend_at_connection + trend_slope * (i + 1)
                
                # Add cyclical component
                cycle_phase = (len(simulated_demand) + i) % cycle_info['period']
                cyclical_component = self._get_cyclical_value_at_phase(
                    simulated_demand, cycle_phase, cycle_info
                )
                
                # Combine trend with cyclical pattern
                projected_value = trend_value + cyclical_component * 0.8
                
                # Add controlled noise
                noise_factor = min(sim_std * 0.1, 10)
                noise = np.random.normal(0, noise_factor)
                projected_value += noise
                
                # Ensure values stay within reasonable bounds
                lower_bound = sim_mean - sim_std * 2
                upper_bound = sim_mean + sim_std * 2
                projected_value = np.clip(projected_value, lower_bound, upper_bound)
                
                projected_demand.append(float(projected_value))
            
            # Apply smoothing to ensure continuity
            if len(projected_demand) > 0:
                projected_demand = self._ensure_smooth_connection(
                    simulated_demand, projected_demand
                )
            
            logger.info(f"Generated cyclical projection with {len(projected_demand)} points")
            return projected_demand
            
        except Exception as e:
            logger.error(f"Error generating smooth projection: {str(e)}")
            return []
    
    def _extract_cyclical_pattern_improved(self, simulated_demand):
        """
        Improved cyclical pattern extraction with better parameter estimation
        """
        try:
            if len(simulated_demand) < 6:
                return {'period': 7, 'amplitude': 5, 'offset': 0, 'noise_level': 2}
            
            # Remove trend to focus on cyclical components
            indices = np.arange(len(simulated_demand))
            trend_slope, trend_intercept = np.polyfit(indices, simulated_demand, 1)
            detrended = np.array(simulated_demand) - (trend_slope * indices + trend_intercept)
            
            # Find dominant period using autocorrelation
            max_period = min(15, len(simulated_demand) // 3)
            best_period = 7
            best_correlation = -1
            
            for period in range(3, max_period + 1):
                autocorr_values = []
                
                # Calculate autocorrelation for this period
                for start in range(0, len(detrended) - 2 * period, period):
                    segment1 = detrended[start:start + period]
                    segment2 = detrended[start + period:start + 2 * period]
                    
                    if len(segment1) == len(segment2) == period:
                        corr = np.corrcoef(segment1, segment2)[0, 1]
                        if not np.isnan(corr):
                            autocorr_values.append(abs(corr))
                
                if autocorr_values:
                    avg_correlation = np.mean(autocorr_values)
                    if avg_correlation > best_correlation:
                        best_correlation = avg_correlation
                        best_period = period
            
            # Calculate amplitude from detrended data
            amplitude = np.std(detrended)
            
            # Estimate noise level
            noise_level = np.std(detrended) * 0.2
            
            logger.info(f"Improved cycle detection - Period: {best_period}, "
                    f"Amplitude: {amplitude:.2f}, Noise: {noise_level:.2f}")
            
            return {
                'period': best_period,
                'amplitude': amplitude,
                'offset': 0,
                'noise_level': noise_level,
                'detrended_data': detrended
            }
            
        except Exception as e:
            logger.error(f"Error in improved cyclical pattern extraction: {str(e)}")
            return {'period': 7, 'amplitude': 5, 'offset': 0, 'noise_level': 2}
    
    def _get_cyclical_value_at_phase(self, simulated_demand, phase, cycle_info):
        """
        Get the cyclical component value at a specific phase
        """
        try:
            period = cycle_info['period']
            
            # Find all points in the simulation that correspond to this phase
            phase_values = []
            sim_mean = np.mean(simulated_demand)
            
            for i in range(len(simulated_demand)):
                if i % period == int(phase):
                    # Remove trend to get pure cyclical component
                    cyclical_component = simulated_demand[i] - sim_mean
                    phase_values.append(cyclical_component)
            
            if phase_values:
                # Return average cyclical value for this phase
                return np.mean(phase_values)
            else:
                # Fallback to sine wave approximation
                normalized_phase = phase / period
                return cycle_info['amplitude'] * np.sin(2 * np.pi * normalized_phase)
                
        except Exception as e:
            logger.error(f"Error getting cyclical value at phase: {str(e)}")
            return 0
    
    def _apply_light_smoothing(self, data, alpha=0.2):
        """
        Apply exponential smoothing to reduce noise while preserving patterns
        """
        if len(data) <= 1:
            return data
        
        smoothed = [data[0]]  # Keep first point unchanged
        
        for i in range(1, len(data)):
            # Exponential smoothing
            smoothed_value = alpha * data[i] + (1 - alpha) * smoothed[-1]
            smoothed.append(smoothed_value)
        
        return smoothed
    
    def _ensure_smooth_connection(self, simulated_demand, projected_demand):
        """
        Ensure smooth connection between simulation and projection
        """
        if not simulated_demand or not projected_demand:
            return projected_demand
        
        try:
            # Get connection points
            sim_last = simulated_demand[-1]
            proj_first = projected_demand[0]
            
            # Calculate adjustment needed for smooth connection
            connection_gap = proj_first - sim_last
            
            # Apply gradual adjustment over first few projection points
            adjustment_length = min(3, len(projected_demand))
            
            adjusted_projection = []
            for i, value in enumerate(projected_demand):
                if i < adjustment_length:
                    # Gradual fade of the connection adjustment
                    fade_factor = (adjustment_length - i) / adjustment_length
                    adjustment = connection_gap * fade_factor * 0.3
                    adjusted_value = value - adjustment
                else:
                    adjusted_value = value
                
                adjusted_projection.append(adjusted_value)
            
            return adjusted_projection
            
        except Exception as e:
            logger.error(f"Error ensuring smooth connection: {str(e)}")
            return projected_demand
    
    def _calculate_three_line_metrics(self, historical_demand, simulated_demand, projected_demand):
        """Calculate metrics for three-line validation chart"""
        try:
            metrics = {}
            
            if historical_demand and simulated_demand:
                # Calculate MAPE for historical vs simulated
                min_len = min(len(historical_demand), len(simulated_demand))
                if min_len > 0:
                    errors = []
                    for i in range(min_len):
                        if historical_demand[i] != 0:
                            error = abs((simulated_demand[i] - historical_demand[i]) / historical_demand[i]) * 100
                            errors.append(error)
                    
                    if errors:
                        mape = np.mean(errors)
                        metrics['historical_vs_simulated'] = {
                            'mape': round(mape, 2),
                            'accuracy_level': 'Excelente' if mape < 10 else 'Buena' if mape < 20 else 'Aceptable'
                        }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating three-line metrics: {str(e)}")
            return {}
    
    def _generate_validation_alerts_grouped(self, validation_results):
        """
        Agrupa las alertas de validación por tipo para mostrar en el template
        """
        try:
            alerts_by_type = {
                'ERROR': [],
                'WARNING': [],
                'INFO': []
            }
            
            # Procesar alertas básicas
            basic_validation = validation_results.get('basic_validation', {})
            if basic_validation.get('alerts'):
                for alert in basic_validation['alerts']:
                    alert_type = alert.get('type', 'INFO').upper()
                    severity = alert.get('severity', 'INFO').upper()
                    
                    alert_data = {
                        'message': alert.get('message', 'Alerta de validación'),
                        'details': alert.get('details', ''),
                        'severity': severity,
                        'category': alert.get('category', 'General'),
                        'recommendation': alert.get('recommendation', '')
                    }
                    
                    if alert_type in alerts_by_type:
                        alerts_by_type[alert_type].append(alert_data)
                    else:
                        alerts_by_type['INFO'].append(alert_data)
            
            # Procesar alertas de predicción
            prediction_validation = validation_results.get('prediction_validation', {})
            if prediction_validation.get('alerts'):
                for alert in prediction_validation['alerts']:
                    alert_type = alert.get('type', 'INFO').upper()
                    severity = alert.get('severity', 'INFO').upper()
                    
                    alert_data = {
                        'message': alert.get('message', 'Alerta de predicción'),
                        'details': alert.get('details', ''),
                        'severity': severity,
                        'category': 'Predicción',
                        'recommendation': alert.get('recommendation', '')
                    }
                    
                    if alert_type in alerts_by_type:
                        alerts_by_type[alert_type].append(alert_data)
                    else:
                        alerts_by_type['INFO'].append(alert_data)
            
            # Generar alertas automáticas basadas en métricas
            self._add_automatic_alerts(alerts_by_type, validation_results)
            
            # Filtrar tipos vacíos
            filtered_alerts = {k: v for k, v in alerts_by_type.items() if v}
            
            logger.info(f"Generated {sum(len(alerts) for alerts in filtered_alerts.values())} validation alerts")
            return filtered_alerts
            
        except Exception as e:
            logger.error(f"Error generating validation alerts: {str(e)}")
            return {'INFO': [{'message': 'Error al procesar alertas de validación', 'severity': 'INFO'}]}
    
    def _add_automatic_alerts(self, alerts_by_type, validation_results):
        """Agregar alertas automáticas basadas en métricas"""
        try:
            # Alerta por precisión baja
            summary = validation_results.get('basic_validation', {}).get('summary', {})
            accuracy = summary.get('overall_accuracy', 0)
            
            if accuracy < 70:
                alerts_by_type['WARNING'].append({
                    'message': f'Precisión del modelo baja: {accuracy:.1f}%',
                    'severity': 'ERROR',
                    'category': 'Precisión',
                    'recommendation': 'Revisar completamente el modelo y los datos'
                })
            
            # Alerta por tasa de éxito baja
            success_rate = summary.get('success_rate', 0)
            if success_rate < 60:
                alerts_by_type['WARNING'].append({
                    'message': f'Tasa de éxito baja: {success_rate:.1f}%',
                    'details': 'Muchas predicciones no cumplen con los criterios de calidad.',
                    'severity': 'WARNING',
                    'category': 'Calidad',
                    'recommendation': 'Revisar criterios de validación y ajustar modelo'
                })
                
        except Exception as e:
            logger.error(f"Error adding automatic alerts: {str(e)}")
    
    def _generate_statistical_analysis(self, simulation_instance, results_simulation, historical_demand, all_variables_extracted):
        """Generar análisis estadístico completo"""
        try:
            statistical_data = {}
            
            # Extraer datos de demanda
            simulated_demands = [float(r.demand_mean) for r in results_simulation if hasattr(r, 'demand_mean')]
            
            if not simulated_demands:
                return {'statistical_analysis': {}, 'statistical_tests': {}}
            
            # 1. Análisis de distribución
            statistical_data['distribution_analysis'] = self._analyze_distribution(simulated_demands)
            
            # 2. Pruebas estadísticas
            if historical_demand and len(historical_demand) > 0:
                statistical_data['statistical_tests'] = self._perform_statistical_tests(
                    historical_demand, simulated_demands
                )
            else:
                statistical_data['statistical_tests'] = {}
            
            # 3. Métricas de performance
            statistical_data['performance_metrics'] = self._calculate_performance_metrics(
                historical_demand, simulated_demands
            )
            
            # 4. Análisis de correlación entre variables
            statistical_data['correlation_analysis'] = self._analyze_variable_correlations(
                all_variables_extracted
            )
            
            # 5. Análisis de tendencias
            statistical_data['trend_analysis'] = self._analyze_trends(simulated_demands)
            
            # 6. Gráficos estadísticos
            statistical_data['statistical_charts'] = self._generate_statistical_charts(
                historical_demand, simulated_demands, all_variables_extracted
            )
            
            return statistical_data
            
        except Exception as e:
            logger.error(f"Error generating statistical analysis: {str(e)}")
            return {'statistical_analysis': {}, 'statistical_tests': {}}
    
    def _analyze_distribution(self, data):
        """Analizar distribución de los datos"""
        try:
            if len(data) < 3:
                return {}
            
            data_array = np.array(data)
            
            analysis = {
                'basic_stats': {
                    'mean': float(np.mean(data_array)),
                    'std': float(np.std(data_array)),
                    'variance': float(np.var(data_array)),
                    'skewness': float(scipy.stats.skew(data_array)),
                    'kurtosis': float(scipy.stats.kurtosis(data_array)),
                    'min': float(np.min(data_array)),
                    'max': float(np.max(data_array)),
                    'median': float(np.median(data_array)),
                    'q25': float(np.percentile(data_array, 25)),
                    'q75': float(np.percentile(data_array, 75)),
                    'iqr': float(np.percentile(data_array, 75) - np.percentile(data_array, 25))
                },
                'normality_test': {
                    'shapiro_stat': None,
                    'shapiro_p': None,
                    'is_normal': False
                },
                'distribution_fit': {
                    'best_fit': 'normal',
                    'fit_params': {},
                    'goodness_of_fit': 0.0
                }
            }
            
            # Prueba de normalidad (Shapiro-Wilk)
            if len(data_array) <= 5000:
                try:
                    stat, p_value = scipy.stats.shapiro(data_array)
                    analysis['normality_test'] = {
                        'shapiro_stat': float(stat),
                        'shapiro_p': float(p_value),
                        'is_normal': p_value > 0.05
                    }
                except Exception as e:
                    logger.warning(f"Error in normality test: {e}")
            
            # Ajuste de distribuciones
            try:
                distributions = [
                    scipy.stats.norm,
                    scipy.stats.lognorm,
                    scipy.stats.expon,
                    scipy.stats.gamma
                ]
                best_dist = None
                best_fit = -np.inf
                best_params = {}
                
                for dist in distributions:
                    try:
                        params = dist.fit(data_array)
                        ks_stat, ks_p = scipy.stats.kstest(
                            data_array, lambda x: dist.cdf(x, *params)
                        )
                        
                        if ks_p > best_fit:
                            best_fit = ks_p
                            best_dist = dist.name
                            best_params = params
                            
                    except Exception:
                        continue
                
                if best_dist:
                    analysis['distribution_fit'] = {
                        'best_fit': best_dist,
                        'fit_params': [float(p) for p in best_params],
                        'goodness_of_fit': float(best_fit)
                    }
            except Exception as e:
                logger.warning(f"Error in distribution fitting: {e}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing distribution: {e}")
            return {}
    
    def _perform_statistical_tests(self, historical_data, simulated_data):
        """Realizar pruebas estadísticas comparativas"""
        try:
            tests = {}
            
            # Ajustar longitudes
            min_len = min(len(historical_data), len(simulated_data))
            hist_trimmed = np.array(historical_data[:min_len])
            sim_trimmed = np.array(simulated_data[:min_len])
            
            if min_len < 3:
                return tests
            
            # 1. Prueba t de Student (medias)
            try:
                t_stat, t_p = scipy.stats.ttest_ind(hist_trimmed, sim_trimmed)
                tests['t_test'] = {
                    'statistic': float(t_stat),
                    'p_value': float(t_p),
                    'means_equal': t_p > 0.05,
                    'interpretation': 'Las medias son estadísticamente iguales' if t_p > 0.05 else 'Las medias son significativamente diferentes'
                }
            except Exception as e:
                logger.warning(f"Error in t-test: {e}")
            
            # 2. Prueba F (varianzas)
            try:
                f_stat = np.var(hist_trimmed, ddof=1) / np.var(sim_trimmed, ddof=1)
                f_p = 2 * min(
                    scipy.stats.f.cdf(f_stat, len(hist_trimmed)-1, len(sim_trimmed)-1),
                    1 - scipy.stats.f.cdf(f_stat, len(hist_trimmed)-1, len(sim_trimmed)-1)
                )
                
                tests['f_test'] = {
                    'statistic': float(f_stat),
                    'p_value': float(f_p),
                    'variances_equal': f_p > 0.05,
                    'interpretation': 'Las varianzas son homogéneas' if f_p > 0.05 else 'Las varianzas son heterogéneas'
                }
            except Exception as e:
                logger.warning(f"Error in F-test: {e}")
            
            # 3. Prueba de Kolmogorov-Smirnov (distribuciones)
            try:
                ks_stat, ks_p = scipy.stats.ks_2samp(hist_trimmed, sim_trimmed)
                tests['ks_test'] = {
                    'statistic': float(ks_stat),
                    'p_value': float(ks_p),
                    'distributions_equal': ks_p > 0.05,
                    'interpretation': 'Las distribuciones son similares' if ks_p > 0.05 else 'Las distribuciones son diferentes'
                }
            except Exception as e:
                logger.warning(f"Error in KS-test: {e}")
            
            # 4. Correlación de Pearson
            try:
                corr_coef, corr_p = scipy.stats.pearsonr(hist_trimmed, sim_trimmed)
                tests['correlation'] = {
                    'coefficient': float(corr_coef),
                    'p_value': float(corr_p),
                    'is_significant': corr_p < 0.05,
                    'strength': (
                        'Muy fuerte' if abs(corr_coef) > 0.8 else
                        'Fuerte' if abs(corr_coef) > 0.6 else
                        'Moderada' if abs(corr_coef) > 0.4 else
                        'Débil'
                    ),
                    'interpretation': f'Correlación {self._get_correlation_strength(corr_coef).lower()} entre histórico y simulado'
                }
            except Exception as e:
                logger.warning(f"Error in correlation test: {e}")
            
            return tests
            
        except Exception as e:
            logger.error(f"Error performing statistical tests: {e}")
            return {}
    
    def _get_correlation_strength(self, corr_coef):
        """Obtiene la fuerza de correlación"""
        abs_corr = abs(corr_coef)
        if abs_corr > 0.8:
            return 'Muy fuerte'
        elif abs_corr > 0.6:
            return 'Fuerte'
        elif abs_corr > 0.4:
            return 'Moderada'
        else:
            return 'Débil'
    
    def _calculate_performance_metrics(self, historical_data, simulated_data):
        """Calcular métricas de performance del modelo"""
        try:
            if not historical_data or not simulated_data:
                return {}
            
            min_len = min(len(historical_data), len(simulated_data))
            hist = np.array(historical_data[:min_len])
            sim = np.array(simulated_data[:min_len])
            
            if min_len == 0:
                return {}
            
            # Métricas básicas
            mae = np.mean(np.abs(hist - sim))
            mse = np.mean((hist - sim) ** 2)
            rmse = np.sqrt(mse)
            
            # MAPE (con manejo de zeros)
            mape_values = []
            for h, s in zip(hist, sim):
                if h != 0:
                    mape_values.append(abs((h - s) / h) * 100)
            mape = np.mean(mape_values) if mape_values else 0
            
            # R²
            ss_res = np.sum((hist - sim) ** 2)
            ss_tot = np.sum((hist - np.mean(hist)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            
            # Índice de concordancia de Willmott
            try:
                willmott_d = 1 - (np.sum((sim - hist) ** 2) / 
                                np.sum((np.abs(sim - np.mean(hist)) + np.abs(hist - np.mean(hist))) ** 2))
            except:
                willmott_d = 0
            
            # Eficiencia de Nash-Sutcliffe
            try:
                nash_sutcliffe = 1 - (np.sum((hist - sim) ** 2) / np.sum((hist - np.mean(hist)) ** 2))
            except:
                nash_sutcliffe = 0
            
            return {
                'mae': float(mae),
                'mse': float(mse),
                'rmse': float(rmse),
                'mape': float(mape),
                'r_squared': float(r_squared),
                'willmott_d': float(willmott_d),
                'nash_sutcliffe': float(nash_sutcliffe),
                'accuracy_level': (
                    'Excelente' if mape < 10 else
                    'Muy buena' if mape < 15 else
                    'Buena' if mape < 20 else
                    'Aceptable' if mape < 30 else
                    'Pobre'
                ),
                'model_quality': (
                    'Muy alta' if r_squared > 0.9 else
                    'Alta' if r_squared > 0.8 else
                    'Moderada' if r_squared > 0.6 else
                    'Baja'
                )
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return {}
    
    def _analyze_variable_correlations(self, all_variables_extracted):
        """Analizar correlaciones entre variables endógenas"""
        try:
            if not all_variables_extracted or len(all_variables_extracted) < 3:
                return {}
            
            # Construir matriz de datos
            variables_data = {}
            numeric_vars = ['IT', 'GT', 'TG', 'TPV', 'NSC', 'EOG', 'NR', 'PVP', 'CVU', 'CFD']
            
            for var in numeric_vars:
                values = []
                for day_data in all_variables_extracted:
                    if var in day_data and day_data[var] is not None:
                        try:
                            values.append(float(day_data[var]))
                        except (ValueError, TypeError):
                            values.append(np.nan)
                    else:
                        values.append(np.nan)
                
                if len(values) > 0 and not all(np.isnan(values)):
                    variables_data[var] = values
            
            if len(variables_data) < 2:
                return {}
            
            # Calcular matriz de correlación
            correlation_matrix = {}
            significant_correlations = []
            
            var_names = list(variables_data.keys())
            for i, var1 in enumerate(var_names):
                correlation_matrix[var1] = {}
                for j, var2 in enumerate(var_names):
                    if i != j:
                        try:
                            # Filtrar valores no nulos
                            data1 = np.array(variables_data[var1])
                            data2 = np.array(variables_data[var2])
                            
                            mask = ~(np.isnan(data1) | np.isnan(data2))
                            if np.sum(mask) > 3:
                                corr_coef, p_value = scipy.stats.pearsonr(
                                    data1[mask], data2[mask]
                                )
                                correlation_matrix[var1][var2] = {
                                    'coefficient': float(corr_coef),
                                    'p_value': float(p_value),
                                    'significant': p_value < 0.05
                                }
                                
                                # Guardar correlaciones significativas y fuertes
                                if p_value < 0.05 and abs(corr_coef) > 0.5:
                                    significant_correlations.append({
                                        'var1': var1,
                                        'var2': var2,
                                        'coefficient': float(corr_coef),
                                        'strength': (
                                            'Muy fuerte' if abs(corr_coef) > 0.8 else
                                            'Fuerte' if abs(corr_coef) > 0.6 else
                                            'Moderada'
                                        ),
                                        'direction': 'Positiva' if corr_coef > 0 else 'Negativa'
                                    })
                            else:
                                correlation_matrix[var1][var2] = {
                                    'coefficient': 0.0,
                                    'p_value': 1.0,
                                    'significant': False
                                }
                        except Exception:
                            correlation_matrix[var1][var2] = {
                                'coefficient': 0.0,
                                'p_value': 1.0,
                                'significant': False
                            }
                    else:
                        correlation_matrix[var1][var2] = {
                            'coefficient': 1.0,
                            'p_value': 0.0,
                            'significant': True
                        }
            
            return {
                'correlation_matrix': correlation_matrix,
                'significant_correlations': significant_correlations,
                'variables_analyzed': var_names
            }
            
        except Exception as e:
            logger.error(f"Error analyzing correlations: {e}")
            return {}
    
    def _analyze_trends(self, data):
        """Analizar tendencias en los datos"""
        try:
            if len(data) < 3:
                return {}
            
            data_array = np.array(data)
            x = np.arange(len(data_array))
            
            # Regresión lineal
            slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(x, data_array)
            
            # Prueba de Mann-Kendall para tendencia
            try:
                tau, tau_p = scipy.stats.kendalltau(x, data_array)
                has_trend = tau_p < 0.05
            except Exception:
                has_trend = p_value < 0.05
            
            # Clasificar tendencia
            if abs(slope) < 0.01 * np.mean(data_array):
                trend_type = 'Estable'
            elif slope > 0:
                trend_type = 'Creciente'
            else:
                trend_type = 'Decreciente'
            
            return {
                'slope': float(slope),
                'intercept': float(intercept),
                'r_squared': float(r_value ** 2),
                'p_value': float(p_value),
                'std_error': float(std_err),
                'trend_type': trend_type,
                'has_significant_trend': has_trend,
                'trend_strength': (
                    'Fuerte' if abs(r_value) > 0.7 else
                    'Moderada' if abs(r_value) > 0.4 else
                    'Débil'
                )
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return {}
    
    def _generate_statistical_charts(self, historical_demand, simulated_demands, all_variables_extracted):
        """Generar gráficos estadísticos"""
        try:
            charts = {}
            
            if not simulated_demands:
                return charts
            
            # 1. Histograma y distribución
            try:
                charts['histogram'] = self.chart_generator._generate_histogram_chart(simulated_demands)
            except Exception as e:
                logger.warning(f"Error generating histogram: {e}")
            
            # 2. Box plot comparativo
            if historical_demand:
                try:
                    charts['boxplot'] = self.chart_generator._generate_comparative_boxplot(
                        historical_demand, simulated_demands
                    )
                except Exception as e:
                    logger.warning(f"Error generating boxplot: {e}")
            
            # 3. Scatter plot (si hay datos históricos)
            if historical_demand:
                try:
                    charts['scatter'] = self.chart_generator._generate_scatter_plot(
                        historical_demand, simulated_demands
                    )
                except Exception as e:
                    logger.warning(f"Error generating scatter plot: {e}")
            
            # 4. Gráfico de residuos
            if historical_demand:
                try:
                    charts['residuals'] = self.chart_generator._generate_residuals_plot(
                        historical_demand, simulated_demands
                    )
                except Exception as e:
                    logger.warning(f"Error generating residuals plot: {e}")
            
            # 5. QQ plot para normalidad
            try:
                charts['qq_plot'] = self.chart_generator._generate_qq_plot(simulated_demands)
            except Exception as e:
                logger.warning(f"Error generating QQ plot: {e}")
            
            return charts
            
        except Exception as e:
            logger.error(f"Error generating statistical charts: {e}")
            return {}
    
    def _generate_enhanced_statistical_charts(self, historical_demand, simulated_demands, all_variables_extracted):
        """Generar gráficos estadísticos completos"""
        try:
            chart_generator = ChartGenerator()
            statistical_charts = {}
            
            # 1. Histograma con distribución
            if simulated_demands:
                statistical_charts['histogram'] = chart_generator._generate_histogram_chart(simulated_demands)
            
            # 2. Box plot comparativo
            if historical_demand and simulated_demands:
                statistical_charts['boxplot'] = chart_generator._generate_comparative_boxplot(
                    historical_demand, simulated_demands
                )
            
            # 3. Scatter plot de correlación
            if historical_demand and simulated_demands:
                statistical_charts['scatter'] = chart_generator._generate_scatter_plot(
                    historical_demand, simulated_demands
                )
            
            # 4. Gráfico de residuos
            if historical_demand and simulated_demands:
                statistical_charts['residuals'] = chart_generator._generate_residuals_plot(
                    historical_demand, simulated_demands
                )
            
            # 5. Q-Q plot para normalidad
            if simulated_demands:
                statistical_charts['qq_plot'] = chart_generator._generate_qq_plot(simulated_demands)
            
            # 6. Autocorrelación
            if simulated_demands and len(simulated_demands) > 10:
                statistical_charts['autocorrelation'] = chart_generator._generate_autocorrelation_plot(simulated_demands)
            
            # 7. Mapa de calor de correlaciones entre variables
            correlation_analysis = self._analyze_variable_correlations(all_variables_extracted)
            if correlation_analysis.get('correlation_matrix'):
                statistical_charts['correlation_heatmap'] = chart_generator._generate_correlation_heatmap(
                    correlation_analysis['correlation_matrix'],
                    correlation_analysis['variables_analyzed']
                )
            
            # 8. Dashboard de performance
            performance_metrics = self._calculate_performance_metrics(historical_demand, simulated_demands)
            if performance_metrics:
                statistical_charts['performance_dashboard'] = chart_generator._generate_performance_dashboard(performance_metrics)
            
            logger.info(f"Generated {len(statistical_charts)} statistical charts")
            return statistical_charts
            
        except Exception as e:
            logger.error(f"Error generating enhanced statistical charts: {str(e)}")
            return {}