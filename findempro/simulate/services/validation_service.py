# services/validation_service.py
"""
Enhanced validation service for simulation results.
Compares simulated values with real data on a daily basis.
"""
import base64
from io import BytesIO
import json
import logging
from simulate.utils.chart_utils import ChartGenerator
from simulate.services.statistical_service import StatisticalService
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta

from django.db.models import Avg, StdDev, Min, Max, Count
from simulate.models import ResultSimulation, Simulation
from questionary.models import Answer, QuestionaryResult

logger = logging.getLogger(__name__)

class SimulationValidationService:
    """Service for validating simulation results against real data"""
    
    def __init__(self):
        self.tolerance_thresholds = {
            'strict': 0.05,      # 5% tolerance
            'normal': 0.10,      # 10% tolerance
            'flexible': 0.20,    # 20% tolerance
            'loose': 0.30        # 30% tolerance
        }
        
        # Variable-specific tolerances
        self.variable_tolerances = {
            # Financial variables need strict validation
            'IT': 'normal',      # Total income
            'GT': 'flexible',    # Total profit (more variable)
            'GO': 'normal',      # Operating expenses
            'TG': 'normal',      # Total expenses
            
            # Production variables
            'QPL': 'normal',     # Production quantity
            'CPROD': 'strict',   # Production capacity (should be stable)
            'TPPRO': 'normal',   # Total production
            'FU': 'flexible',    # Utilization factor
            
            # Sales variables
            'TPV': 'normal',     # Total products sold
            'TCAE': 'normal',    # Total customers served
            'VPC': 'flexible',   # Sales per customer
            'NSC': 'normal',     # Service level
            
            # Inventory variables
            'IPF': 'flexible',   # Final product inventory
            'II': 'flexible',    # Input inventory
            'RTI': 'loose',      # Inventory turnover
            
            # HR and efficiency
            'PE': 'flexible',    # Employee productivity
            'HO': 'loose',       # Idle hours
            
            # Demand variables (special handling)
            'DPH': 'special',    # Daily demand - compared differently
            'DE': 'flexible',    # Expected demand
            'DI': 'loose',       # Unmet demand
        }
    
    
    def _validate_model_variables(self, simulation_instance, results_simulation, all_variables_extracted):
        """
        MÉTODO FALTANTE: Validar variables del modelo comparando valores simulados con reales
        """
        try:
            logger.info(f"Starting model variables validation for simulation {simulation_instance.id}")
            
            # Extraer valores reales del cuestionario
            real_values = self._extract_real_values(simulation_instance)
            
            # Inicializar estructura de resultados
            validation_results = {
                'summary': {
                    'total_variables': 0,
                    'precise_count': 0,
                    'acceptable_count': 0,
                    'inaccurate_count': 0,
                    'success_rate': 0.0,
                    'is_valid': False
                },
                'by_variable': {},
                'daily_details': {}
            }
            
            # Variables clave para validar
            key_variables = ['IT', 'GT', 'TG', 'TPV', 'NSC', 'EOG', 'DPH', 'CPROD']
            
            for var_key in key_variables:
                if var_key in real_values:
                    var_validation = self._validate_single_variable_across_days(
                        var_key, real_values[var_key], all_variables_extracted
                    )
                    
                    validation_results['by_variable'][var_key] = var_validation
                    validation_results['summary']['total_variables'] += 1
                    
                    # Contar por estado
                    if var_validation['status'] == 'PRECISA':
                        validation_results['summary']['precise_count'] += 1
                    elif var_validation['status'] == 'ACEPTABLE':
                        validation_results['summary']['acceptable_count'] += 1
                    else:
                        validation_results['summary']['inaccurate_count'] += 1
            
            # Calcular tasa de éxito
            total_vars = validation_results['summary']['total_variables']
            if total_vars > 0:
                success_count = (validation_results['summary']['precise_count'] + 
                            validation_results['summary']['acceptable_count'])
                validation_results['summary']['success_rate'] = success_count / total_vars * 100
                validation_results['summary']['is_valid'] = validation_results['summary']['success_rate'] >= 70
            
            logger.info(f"Model variables validation completed: {validation_results['summary']['success_rate']:.1f}% success rate")
            return validation_results
            
        except Exception as e:
            logger.error(f"Error in model variables validation: {str(e)}")
            return self._create_empty_validation_result()

    
    
    def _validate_single_variable_across_days(self, var_key, real_value, all_variables_extracted):
        """Validar una variable específica a través de todos los días"""
        try:
            simulated_values = []
            daily_details = {}
            
            # Extraer valores simulados para esta variable
            for day_idx, day_data in enumerate(all_variables_extracted):
                day_num = day_idx + 1
                
                if var_key in day_data and day_data[var_key] is not None:
                    try:
                        sim_value = float(day_data[var_key])
                        simulated_values.append(sim_value)
                        
                        # Calcular error para este día
                        error_pct = self._calculate_error_percentage(sim_value, real_value)
                        status = self._determine_validation_status(error_pct)
                        
                        daily_details[str(day_num)] = {
                            'simulated': sim_value,
                            'real': real_value,
                            'error_pct': error_pct,
                            'status': status
                        }
                    except (ValueError, TypeError):
                        continue
            
            # Calcular estadísticas de la variable
            if simulated_values:
                simulated_avg = sum(simulated_values) / len(simulated_values)
                overall_error = self._calculate_error_percentage(simulated_avg, real_value)
                overall_status = self._determine_validation_status(overall_error)
            else:
                simulated_avg = 0
                overall_error = 100.0
                overall_status = 'NO_DATA'
            
            return {
                'real_value': real_value,
                'simulated_avg': simulated_avg,
                'simulated_values_count': len(simulated_values),
                'error_pct': overall_error,
                'status': overall_status,
                'daily_details': daily_details,
                'description': self._get_variable_description(var_key),
                'unit': self._get_variable_unit(var_key),
                'type': self._get_variable_type(var_key)
            }
            
        except Exception as e:
            logger.error(f"Error validating variable {var_key}: {str(e)}")
            return {
                'real_value': real_value,
                'simulated_avg': 0,
                'simulated_values_count': 0,
                'error_pct': 100.0,
                'status': 'ERROR',
                'daily_details': {},
                'description': var_key,
                'unit': '',
                'type': 'Numeric'
            }
    
    def _generate_daily_validation_charts(self, daily_validation_results):
        """
        MÉTODO FALTANTE: Generar gráficos de validación diaria
        """
        try:
            daily_charts = {}
            
            if not daily_validation_results:
                logger.warning("No daily validation results provided for chart generation")
                return daily_charts
            
            # Gráfico de precisión por día
            daily_charts['daily_accuracy'] = self._generate_daily_accuracy_chart(daily_validation_results)
            
            # Gráfico de errores por variable
            daily_charts['variable_errors'] = self._generate_variable_error_chart(daily_validation_results)
            
            # Gráfico de tendencia de validación
            daily_charts['validation_trend'] = self._generate_validation_trend_chart(daily_validation_results)
            
            logger.info(f"Generated {len(daily_charts)} daily validation charts")
            return daily_charts
            
        except Exception as e:
            logger.error(f"Error generating daily validation charts: {str(e)}")
            return {}
    
    def _generate_variable_error_chart(self, daily_validation_results):
        """Generar gráfico de errores por variable"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            from io import BytesIO
            import base64
            import numpy as np
            
            # Recopilar errores por variable
            variable_errors = {}
            
            for day_validation in daily_validation_results:
                for var_name, validation in day_validation['validations'].items():
                    if var_name not in variable_errors:
                        variable_errors[var_name] = []
                    
                    error_rate = validation.get('error_rate', 0) * 100
                    variable_errors[var_name].append(error_rate)
            
            if not variable_errors:
                return None
            
            # Calcular estadísticas por variable
            variables = list(variable_errors.keys())
            mean_errors = [np.mean(variable_errors[var]) for var in variables]
            
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Crear gráfico de barras horizontales
            y_pos = np.arange(len(variables))
            colors = ['#E74C3C' if error > 20 else '#F39C12' if error > 10 else '#27AE60' 
                    for error in mean_errors]
            
            bars = ax.barh(y_pos, mean_errors, color=colors, alpha=0.8, edgecolor='black')
            
            # Agregar valores
            for i, (bar, error) in enumerate(zip(bars, mean_errors)):
                width = bar.get_width()
                ax.text(width + 0.5, bar.get_y() + bar.get_height()/2,
                    f'{error:.1f}%', ha='left', va='center', fontsize=10)
            
            ax.set_yticks(y_pos)
            ax.set_yticklabels(variables)
            ax.set_xlabel('Error Promedio (%)')
            ax.set_title('Error Promedio por Variable')
            ax.grid(True, alpha=0.3, axis='x')
            
            # Líneas de referencia
            ax.axvline(x=10, color='orange', linestyle='--', alpha=0.5, label='Aceptable (10%)')
            ax.axvline(x=20, color='red', linestyle='--', alpha=0.5, label='Crítico (20%)')
            ax.legend()
            
            # CORRECCIÓN: Layout seguro
            try:
                plt.tight_layout(pad=1.0)
            except:
                plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
            
            # Convertir a base64
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            return chart_base64
            
        except Exception as e:
            logger.error(f"Error generating variable error chart: {str(e)}")
            return None
    
    
    def _calculate_daily_validation_summary(self, daily_validation_results):
        """
        MÉTODO FALTANTE: Calcular resumen de validación diaria
        """
        try:
            if not daily_validation_results:
                return {
                    'total_days': 0,
                    'average_accuracy': 0.0,
                    'best_day': None,
                    'worst_day': None,
                    'total_variables_validated': 0,
                    'overall_success_rate': 0.0
                }
            
            total_days = len(daily_validation_results)
            accuracy_rates = []
            total_variables = 0
            total_successful = 0
            
            best_day = {'day': 1, 'accuracy': 0}
            worst_day = {'day': 1, 'accuracy': 100}
            
            for day_validation in daily_validation_results:
                accuracy = day_validation['accuracy_rate']
                accuracy_rates.append(accuracy)
                
                # Actualizar mejor y peor día
                if accuracy > best_day['accuracy']:
                    best_day = {'day': day_validation['day_number'], 'accuracy': accuracy}
                if accuracy < worst_day['accuracy']:
                    worst_day = {'day': day_validation['day_number'], 'accuracy': accuracy}
                
                # Contar variables
                summary = day_validation.get('summary', {})
                total_variables += summary.get('total', 0)
                total_successful += summary.get('precise', 0) + summary.get('acceptable', 0)
            
            # Calcular promedios
            average_accuracy = sum(accuracy_rates) / len(accuracy_rates) if accuracy_rates else 0
            overall_success_rate = (total_successful / total_variables * 100) if total_variables > 0 else 0
            
            return {
                'total_days': total_days,
                'average_accuracy': average_accuracy * 100,
                'best_day': best_day,
                'worst_day': worst_day,
                'total_variables_validated': total_variables,
                'overall_success_rate': overall_success_rate,
                'accuracy_std': np.std(accuracy_rates) * 100 if len(accuracy_rates) > 1 else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating daily validation summary: {str(e)}")
            return {
                'total_days': 0,
                'average_accuracy': 0.0,
                'best_day': None,
                'worst_day': None,
                'total_variables_validated': 0,
                'overall_success_rate': 0.0
            }
    
    def _safe_numeric_operation(self, value1, value2, operation='subtract'):
        """
        CORRECCIÓN: Operación matemática segura para evitar errores de tipo
        """
        try:
            # Convertir primer valor
            if hasattr(value1, 'demand_mean'):
                # Es un ResultSimulation
                num1 = float(value1.demand_mean)
            elif hasattr(value1, 'value'):
                # Tiene un atributo value
                num1 = float(value1.value)
            elif isinstance(value1, (int, float)):
                # Es un número directo
                num1 = float(value1)
            else:
                logger.warning(f"Cannot convert value1 to float: {type(value1)}")
                num1 = 0.0
            
            # Convertir segundo valor
            if hasattr(value2, 'demand_mean'):
                # Es un ResultSimulation
                num2 = float(value2.demand_mean)
            elif hasattr(value2, 'value'):
                # Tiene un atributo value
                num2 = float(value2.value)
            elif isinstance(value2, (int, float)):
                # Es un número directo
                num2 = float(value2)
            else:
                logger.warning(f"Cannot convert value2 to float: {type(value2)}")
                num2 = 0.0
            
            # Realizar operación
            if operation == 'subtract':
                return num1 - num2
            elif operation == 'add':
                return num1 + num2
            elif operation == 'multiply':
                return num1 * num2
            elif operation == 'divide':
                return num1 / num2 if num2 != 0 else 0
            else:
                return num1
                
        except (ValueError, TypeError, AttributeError) as e:
            logger.error(f"Error in safe numeric operation: {e}")
            return 0.0
    
    def _generate_daily_accuracy_chart(self, daily_validation_results):
        """Generar gráfico de precisión diaria"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            from io import BytesIO
            import base64
            
            days = []
            accuracy_rates = []
            
            for day_validation in daily_validation_results:
                days.append(day_validation['day_number'])
                accuracy_rates.append(day_validation['accuracy_rate'] * 100)
            
            if not days:
                return None
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Gráfico de barras coloreadas por rendimiento
            colors = []
            for rate in accuracy_rates:
                if rate >= 90:
                    colors.append('#27AE60')  # Verde
                elif rate >= 70:
                    colors.append('#F39C12')  # Naranja
                else:
                    colors.append('#E74C3C')  # Rojo
            
            bars = ax.bar(days, accuracy_rates, color=colors, alpha=0.8, edgecolor='black', linewidth=1)
            
            # Líneas de referencia
            ax.axhline(y=90, color='green', linestyle='--', alpha=0.5, label='Meta Excelente (90%)')
            ax.axhline(y=70, color='orange', linestyle='--', alpha=0.5, label='Meta Buena (70%)')
            
            # Agregar valores en las barras
            for bar, rate in zip(bars, accuracy_rates):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{rate:.1f}%', ha='center', va='bottom', fontsize=9)
            
            ax.set_xlabel('Día de Simulación')
            ax.set_ylabel('Precisión (%)')
            ax.set_title('Precisión de Validación por Día')
            ax.legend()
            ax.grid(True, alpha=0.3, axis='y')
            ax.set_ylim(0, 105)
            
            # CORRECCIÓN: Layout seguro
            try:
                plt.tight_layout(pad=1.0)
            except:
                plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
            
            # Convertir a base64
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            return chart_base64
            
        except Exception as e:
            logger.error(f"Error generating daily accuracy chart: {str(e)}")
            return None
    
    
    def _get_variable_description(self, var_key):
        """Obtener descripción de la variable"""
        descriptions = {
            'IT': 'Ingresos Totales',
            'GT': 'Ganancias Totales',
            'TG': 'Gastos Totales',
            'TPV': 'Total Productos Vendidos',
            'NSC': 'Nivel de Servicio al Cliente',
            'EOG': 'Eficiencia Operativa Global',
            'DPH': 'Demanda Promedio por Hora',
            'CPROD': 'Capacidad de Producción',
            'PVP': 'Precio de Venta por Producto',
            'CVU': 'Costo Variable Unitario',
            'CFD': 'Costos Fijos Diarios',
            'NR': 'Margen de Ganancia Neto',
            'RI': 'Retorno de Inversión',
            'IPF': 'Inventario de Productos Finales'
        }
        return descriptions.get(var_key, var_key)

    
    def _get_variable_type(self, var_key):
        """Obtener tipo de variable"""
        types = {
            'IT': 'Financiera',
            'GT': 'Financiera', 
            'TG': 'Financiera',
            'TPV': 'Producción',
            'NSC': 'Servicio',
            'EOG': 'Eficiencia',
            'DPH': 'Demanda',
            'CPROD': 'Capacidad',
            'PVP': 'Precio',
            'CVU': 'Costo',
            'CFD': 'Costo',
            'NR': 'Rentabilidad',
            'RI': 'Rentabilidad',
            'IPF': 'Inventario'
        }
        return types.get(var_key, 'Numérica')
    
    def _get_variable_unit(self, var_key):
        """Obtener unidad de la variable"""
        units = {
            'IT': 'Bs.',
            'GT': 'Bs.',
            'TG': 'Bs.',
            'TPV': 'Litros',
            'NSC': '%',
            'EOG': '%',
            'DPH': 'Litros/hora',
            'CPROD': 'Litros/día'
        }
        return units.get(var_key, '')
    
    
    def _validate_model_predictions(self, simulation_instance, predicted_values, real_values):
        """
        Validates model predictions against real values.
        This method was missing and causing AttributeError.
        """
        try:
            validation_results = {
                'predictions_validated': 0,
                'accuracy_metrics': {},
                'validation_status': 'PASSED',
                'errors': [],
                'warnings': []
            }
            
            if not predicted_values or not real_values:
                validation_results['validation_status'] = 'FAILED'
                validation_results['errors'].append("Insufficient data for validation")
                return validation_results
            
            # Calculate validation metrics
            total_predictions = len(predicted_values)
            accurate_predictions = 0
            error_rates = []
            
            for i, (predicted, real) in enumerate(zip(predicted_values, real_values)):
                if real != 0:
                    error_rate = abs(predicted - real) / abs(real)
                    error_rates.append(error_rate)
                    
                    # Consider accurate if within 15% tolerance
                    if error_rate <= 0.15:
                        accurate_predictions += 1
                else:
                    # Handle zero real values
                    if abs(predicted) <= 1:  # Small threshold for zero
                        accurate_predictions += 1
                    error_rates.append(0 if predicted == 0 else 1)
            
            # Calculate metrics
            if error_rates:
                validation_results['accuracy_metrics'] = {
                    'mean_absolute_percentage_error': sum(error_rates) / len(error_rates),
                    'accuracy_rate': accurate_predictions / total_predictions,
                    'total_predictions': total_predictions,
                    'accurate_predictions': accurate_predictions
                }
                
                # Determine validation status
                accuracy_rate = validation_results['accuracy_metrics']['accuracy_rate']
                if accuracy_rate >= 0.8:
                    validation_results['validation_status'] = 'PASSED'
                elif accuracy_rate >= 0.6:
                    validation_results['validation_status'] = 'WARNING'
                    validation_results['warnings'].append(
                        f"Model accuracy is moderate: {accuracy_rate:.1%}"
                    )
                else:
                    validation_results['validation_status'] = 'FAILED'
                    validation_results['errors'].append(
                        f"Model accuracy too low: {accuracy_rate:.1%}"
                    )
            
            validation_results['predictions_validated'] = total_predictions
            return validation_results
            
        except Exception as e:
            logger.error(f"Error in model prediction validation: {str(e)}")
            return {
                'predictions_validated': 0,
                'accuracy_metrics': {},
                'validation_status': 'ERROR',
                'errors': [f"Validation error: {str(e)}"],
                'warnings': []
            }
    
    def _validate_data_structure(self, data, expected_structure, context="data_validation"):
        """
        Validar estructura de datos antes de procesamiento
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
                self._enhanced_error_logging(
                    ValueError("Data structure validation failed"),
                    context,
                    validation_results
                )
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error in data structure validation: {e}")
            return {'is_valid': False, 'missing_fields': [], 'invalid_types': [], 'warnings': [str(e)]}
    
    def _get_safe_variable_unit(self, var_name):
        """Obtener unidad de variable de forma segura"""
        units = {
            'PVP': 'Bs./L',
            'TPV': 'L',
            'IT': 'Bs.',
            'TG': 'Bs.',
            'GT': 'Bs.',
            'NR': '%',
            'NSC': '%',
            'EOG': '%',
            'CFD': 'Bs.',
            'CVU': 'Bs./L',
            'DPH': 'L/día',
            'CPROD': 'L/día',
            'NEPP': 'empleados',
            'RI': '%',
            'IPF': 'L'
        }
        return units.get(var_name, '')

    def _process_accumulated_variables_safely(self, all_variables_extracted):
        """
        Procesar variables acumuladas con manejo de errores robusto
        """
        try:
            # Lista de variables esperadas (verificar que existan)
            expected_variables = [
                'PVP', 'TPV', 'IT', 'TG', 'GT', 'NR', 'NSC', 'EOG', 
                'CFD', 'CVU', 'DPH', 'CPROD', 'NEPP', 'RI', 'IPF'
            ]
            
            totales_acumulativos = {}
            
            # Verificar qué variables están realmente disponibles
            available_variables = set()
            for day_data in all_variables_extracted:
                if isinstance(day_data, dict):
                    available_variables.update(day_data.keys())
            
            logger.info(f"Available variables: {list(available_variables)}")
            
            # Procesar solo variables que existen
            for var_name in expected_variables:
                if var_name in available_variables:
                    try:
                        var_data = self._calculate_variable_totals_safe(all_variables_extracted, var_name)
                        if var_data['total'] != 0 or var_data['count'] > 0:
                            totales_acumulativos[var_name] = var_data
                    except Exception as e:
                        logger.warning(f"Error processing variable {var_name}: {e}")
                        continue
                else:
                    logger.debug(f"Variable {var_name} not found in extracted data")
            
            logger.info(f"Successfully processed {len(totales_acumulativos)} accumulated variables")
            return totales_acumulativos
            
        except Exception as e:
            logger.error(f"Error processing accumulated variables: {e}")
            return {}

    def _calculate_variable_totals_safe(self, all_variables_extracted, var_name):
        """
        Calcular totales de variable con manejo de errores
        """
        try:
            values = []
            
            for day_data in all_variables_extracted:
                if isinstance(day_data, dict) and var_name in day_data:
                    try:
                        value = day_data[var_name]
                        if value is not None:
                            # Intentar conversión a float
                            numeric_value = float(value)
                            values.append(numeric_value)
                    except (ValueError, TypeError) as e:
                        logger.debug(f"Could not convert {var_name} value '{value}' to float: {e}")
                        continue
            
            # Calcular estadísticas
            if values:
                total = sum(values)
                count = len(values)
                average = total / count
                min_val = min(values)
                max_val = max(values)
                
                # Calcular tendencia simple
                if len(values) >= 3:
                    first_half = values[:len(values)//2]
                    second_half = values[len(values)//2:]
                    trend = 'increasing' if sum(second_half) > sum(first_half) else 'decreasing'
                else:
                    trend = 'stable'
            else:
                total = count = average = min_val = max_val = 0
                trend = 'stable'
            
            return {
                'total': total,
                'count': count,
                'average': average,
                'min_value': min_val,
                'max_value': max_val,
                'trend': trend,
                'unit': self._get_safe_variable_unit(var_name)
            }
            
        except Exception as e:
            logger.error(f"Error calculating totals for {var_name}: {e}")
            return {
                'total': 0,
                'count': 0,
                'average': 0,
                'min_value': 0,
                'max_value': 0,
                'trend': 'stable',
                'unit': ''
            }
    
    def _enhanced_error_logging(self, error, context="operation", additional_data=None):
        """
        Logging mejorado para errores
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
            
            # Logging específico para errores conocidos
            if isinstance(error, TypeError) and "unsupported operand type" in str(error):
                logger.error("Detected unsupported operand type error - check numeric conversions")
            elif isinstance(error, AttributeError) and "has no attribute" in str(error):
                logger.error("Detected missing attribute error - check object structure")
            elif isinstance(error, KeyError):
                logger.error(f"Detected missing key error: {error} - check data structure")
            
        except Exception as logging_error:
            # Fallback logging
            logger.error(f"Error in enhanced logging: {logging_error}")
            logger.error(f"Original error: {error}")
    
    
    
    def validate_questionary_selection(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate questionary selection form data.
        
        Args:
            form_data: Dictionary containing form data to validate
            
        Returns:
            Dictionary with validation result and errors
        """
        errors = []
        
        try:
            # Validate questionary result ID
            questionary_id = form_data.get('selected_questionary_result_id')
            if not questionary_id:
                errors.append("Debe seleccionar un cuestionario")
            else:
                try:
                    questionary_id = int(questionary_id)
                    if questionary_id <= 0:
                        errors.append("ID de cuestionario inválido")
                    else:
                        # Check if questionary exists and is active
                        if not QuestionaryResult.objects.filter(id=questionary_id, is_active=True).exists():
                            errors.append("El cuestionario seleccionado no existe o no está activo")
                except (ValueError, TypeError):
                    errors.append("ID de cuestionario debe ser un número válido")
            
            # Validate quantity time
            quantity_time = form_data.get('selected_quantity_time')
            if not quantity_time:
                errors.append("Debe especificar la duración de la simulación")
            else:
                try:
                    quantity = int(quantity_time)
                    if quantity < 1:
                        errors.append("La duración debe ser mayor a 0")
                    elif quantity > 365:
                        errors.append("La duración no puede ser mayor a 365")
                except (ValueError, TypeError):
                    errors.append("La duración debe ser un número válido")
            
            # Validate unit time
            unit_time = form_data.get('selected_unit_time')
            valid_units = ['days', 'weeks', 'months']
            if not unit_time:
                errors.append("Debe seleccionar una unidad de tiempo")
            elif unit_time not in valid_units:
                errors.append(f"Unidad de tiempo debe ser una de: {', '.join(valid_units)}")
            
            # Additional business logic validations
            if not errors and questionary_id:
                try:
                    questionary = QuestionaryResult.objects.get(id=questionary_id)
                    
                    # Check if questionary has required data
                    answers_count = questionary.fk_question_result_answer.filter(is_active=True).count()
                    if answers_count == 0:
                        errors.append("El cuestionario seleccionado no tiene respuestas válidas")
                    
                    # Check if product is active
                    if not questionary.fk_questionary.fk_product.is_active:
                        errors.append("El producto asociado al cuestionario no está activo")
                    
                    # Check if business is active
                    if not questionary.fk_questionary.fk_product.fk_business.is_active:
                        errors.append("El negocio asociado al cuestionario no está activo")
                        
                except QuestionaryResult.DoesNotExist:
                    errors.append("El cuestionario seleccionado no existe")
                except Exception as e:
                    logger.error(f"Error validating questionary: {e}")
                    errors.append("Error validando el cuestionario seleccionado")
            
        except Exception as e:
            logger.error(f"Error in questionary validation: {e}")
            errors.append("Error interno en la validación")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }
    
    def validate_simulation_start(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate simulation start form data.
        
        Args:
            form_data: Dictionary containing simulation start data
            
        Returns:
            Dictionary with validation result and errors
        """
        errors = []
        
        try:
            # Validate questionary result
            questionary_id = form_data.get('fk_questionary_result')
            if not questionary_id:
                errors.append("El cuestionario es requerido")
            else:
                try:
                    questionary_id = int(questionary_id)
                    if not QuestionaryResult.objects.filter(id=questionary_id, is_active=True).exists():
                        errors.append("Cuestionario no válido o inactivo")
                except (ValueError, TypeError):
                    errors.append("ID de cuestionario inválido")
            
            # Validate FDP (Probability Density Function)
            fdp_id = form_data.get('fk_fdp')
            if not fdp_id:
                errors.append("La función de densidad de probabilidad es requerida")
            else:
                try:
                    fdp_id = int(fdp_id)
                    # Import here to avoid circular imports
                    from simulate.models import ProbabilisticDensityFunction
                    if not ProbabilisticDensityFunction.objects.filter(id=fdp_id, is_active=True).exists():
                        errors.append("Función de densidad de probabilidad no válida")
                except (ValueError, TypeError):
                    errors.append("ID de función de densidad inválido")
            
            # Validate quantity time
            quantity_time = form_data.get('quantity_time')
            if not quantity_time:
                errors.append("La duración de la simulación es requerida")
            else:
                try:
                    quantity = int(quantity_time)
                    if quantity < 1:
                        errors.append("La duración debe ser mayor a 0")
                    elif quantity > 365:
                        errors.append("La duración no puede ser mayor a 365")
                except (ValueError, TypeError):
                    errors.append("La duración debe ser un número válido")
            
            # Validate unit time
            unit_time = form_data.get('unit_time', 'days')
            valid_units = ['days', 'weeks', 'months']
            if unit_time not in valid_units:
                errors.append(f"Unidad de tiempo debe ser una de: {', '.join(valid_units)}")
            
            # Validate confidence level (optional)
            confidence_level = form_data.get('confidence_level')
            if confidence_level:
                try:
                    confidence = float(confidence_level)
                    if confidence < 0.1 or confidence > 0.99:
                        errors.append("El nivel de confianza debe estar entre 0.1 y 0.99")
                except (ValueError, TypeError):
                    errors.append("Nivel de confianza debe ser un número válido")
            
            # Validate random seed (optional)
            random_seed = form_data.get('random_seed')
            if random_seed:
                try:
                    seed = int(random_seed)
                    if seed < 0:
                        errors.append("La semilla aleatoria debe ser un número positivo")
                except (ValueError, TypeError):
                    errors.append("La semilla aleatoria debe ser un número entero")
            
            # Validate demand history
            demand_history = form_data.get('demand_history')
            if not demand_history:
                errors.append("Se requieren datos históricos de demanda")
            elif isinstance(demand_history, list) and len(demand_history) < 5:
                errors.append("Se requieren al menos 5 datos históricos de demanda")
            
        except Exception as e:
            logger.error(f"Error in simulation start validation: {e}")
            errors.append("Error interno en la validación")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }
    
    def validate_api_config(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate API configuration data.
        
        Args:
            data: Dictionary containing API configuration data
            
        Returns:
            Dictionary with validation result and errors
        """
        errors = []
        
        try:
            # Validate questionary_id
            questionary_id = data.get('questionary_id')
            if not questionary_id:
                errors.append("questionary_id es requerido")
            else:
                try:
                    questionary_id = int(questionary_id)
                    if not QuestionaryResult.objects.filter(id=questionary_id, is_active=True).exists():
                        errors.append("questionary_id no válido")
                except (ValueError, TypeError):
                    errors.append("questionary_id debe ser un número entero")
            
            # Validate optional parameters
            if 'quantity_time' in data:
                try:
                    quantity = int(data['quantity_time'])
                    if quantity < 1 or quantity > 365:
                        errors.append("quantity_time debe estar entre 1 y 365")
                except (ValueError, TypeError):
                    errors.append("quantity_time debe ser un número entero")
            
            if 'unit_time' in data:
                unit_time = data['unit_time']
                if unit_time not in ['days', 'weeks', 'months']:
                    errors.append("unit_time debe ser 'days', 'weeks' o 'months'")
            
            if 'confidence_level' in data:
                try:
                    confidence = float(data['confidence_level'])
                    if confidence < 0.1 or confidence > 0.99:
                        errors.append("confidence_level debe estar entre 0.1 y 0.99")
                except (ValueError, TypeError):
                    errors.append("confidence_level debe ser un número decimal")
            
        except Exception as e:
            logger.error(f"Error in API config validation: {e}")
            errors.append("Error interno en la validación de API")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }
    
    def generate_three_line_validation_chart(self, historical_demand, simulated_demand, 
                                       projected_demand=None, chart_generator=None):
        """
        Generate three-line validation chart for complete model validation
        
        Args:
            historical_demand: List of historical/real demand values
            simulated_demand: List of simulated demand values
            projected_demand: Optional list of projected demand values
            chart_generator: Chart generator instance
            
        Returns:
            Dictionary with chart image and validation metrics
        """
        try:
            if not chart_generator:
                from simulate.utils.chart_demand_utils import ChartDemand
                chart_generator = ChartDemand()
            
            # Log input data
            logger.info(f"Generating three-line chart - Historical: {len(historical_demand) if historical_demand else 0}, "
                    f"Simulated: {len(simulated_demand) if simulated_demand else 0}, "
                    f"Projected: {len(projected_demand) if projected_demand else 0}")
            
            # Ensure data is properly formatted
            historical_demand = [float(v) for v in historical_demand if v is not None] if historical_demand else []
            simulated_demand = [float(v) for v in simulated_demand if v is not None] if simulated_demand else []
            projected_demand = [float(v) for v in projected_demand if v is not None] if projected_demand else []
            
            # Generate the three-line validation chart
            validation_chart = chart_generator.generate_validation_comparison_chart(
                real_values=historical_demand,
                projected_values=projected_demand,
                simulated_values=simulated_demand
            )
            
            if not validation_chart:
                logger.error("Chart generation returned None")
                return None
            
            # Calculate validation metrics
            validation_metrics = self._calculate_three_line_metrics(
                historical_demand, simulated_demand, projected_demand
            )
            
            result = {
                'chart': validation_chart,
                'metrics': validation_metrics,
                'has_historical': bool(historical_demand),
                'has_projected': bool(projected_demand),
                'has_simulated': bool(simulated_demand)
            }
            
            logger.info("Three-line validation chart generated successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error generating three-line validation chart: {str(e)}")
            logger.exception("Full traceback:")
            return None
    
    def _calculate_three_line_metrics(self, historical, simulated, projected):
        """Calculate metrics for three-line validation"""
        metrics = {
            'historical_vs_simulated': {},
            'simulated_vs_projected': {},
            'overall_validation': {}
        }
        
        try:
            # Historical vs Simulated comparison
            if historical and simulated:
                min_len = min(len(historical), len(simulated))
                if min_len > 0:
                    hist_compare = historical[:min_len]
                    sim_compare = simulated[:min_len]
                    
                    # Calculate metrics
                    errors = []
                    squared_errors = []
                    absolute_errors = []
                    
                    for h, s in zip(hist_compare, sim_compare):
                        if h != 0:
                            error = abs((h - s) / h) * 100
                            errors.append(error)
                        squared_errors.append((h - s) ** 2)
                        absolute_errors.append(abs(h - s))
                    
                    mape = np.mean(errors) if errors else 0
                    rmse = np.sqrt(np.mean(squared_errors))
                    mae = np.mean(absolute_errors)
                    
                    metrics['historical_vs_simulated'] = {
                        'mape': round(mape, 2),
                        'rmse': round(rmse, 2),
                        'mae': round(mae, 2),
                        'accuracy_level': self._get_accuracy_level(mape),
                        'samples_compared': min_len
                    }
            
            # Simulated vs Projected comparison
            if projected and simulated and historical:
                # Compare the projected portion of simulated data
                hist_len = len(historical)
                if len(simulated) > hist_len:
                    sim_projected = simulated[hist_len:]
                    min_len = min(len(sim_projected), len(projected))
                    if min_len > 0:
                        sim_compare = sim_projected[:min_len]
                        proj_compare = projected[:min_len]
                        
                        errors = []
                        for s, p in zip(sim_compare, proj_compare):
                            if p != 0:
                                error = abs((s - p) / p) * 100
                                errors.append(error)
                        
                        mape = np.mean(errors) if errors else 0
                        
                        metrics['simulated_vs_projected'] = {
                            'mape': round(mape, 2),
                            'alignment': 'Buena' if mape < 15 else 'Regular' if mape < 30 else 'Pobre',
                            'samples_compared': min_len
                        }
            
            # Overall validation score
            scores = []
            if metrics['historical_vs_simulated'].get('mape') is not None:
                scores.append(max(0, 100 - metrics['historical_vs_simulated']['mape']))
            if metrics['simulated_vs_projected'].get('mape') is not None:
                scores.append(max(0, 100 - metrics['simulated_vs_projected']['mape']))
            
            if scores:
                overall_score = np.mean(scores)
                metrics['overall_validation'] = {
                    'score': round(overall_score, 1),
                    'status': 'Excelente' if overall_score > 90 else 'Bueno' if overall_score > 75 else 'Regular',
                    'components': len(scores)
                }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")
            return metrics
    
    def _validate_by_day(self, simulation_instance, results_simulation, real_values):
        """
        Validate simulation results day by day against real values
        """
        daily_validation_results = []
        
        # Get DH list for daily comparison if available
        dh_list = real_values.get('DH', []) if isinstance(real_values.get('DH'), list) else []
        
        for day_idx, result in enumerate(results_simulation):
            day_number = day_idx + 1
            day_validation = {
                'day': day_number,
                'date': result.date if hasattr(result, 'date') else None,
                'variables': {},
                'summary': {
                    'total': 0,
                    'precise': 0,
                    'acceptable': 0,
                    'inaccurate': 0
                }
            }
            
            # Extract simulated values for this day
            simulated_vars = result.variables if hasattr(result, 'variables') else {}
            
            # Variables to validate daily
            daily_variables = ['CPROD', 'TPV', 'IT', 'GT', 'GO', 'TPPRO', 'IPF']
            
            # Special handling for DH - compare with historical list
            if dh_list and day_idx < len(dh_list):
                real_dh = dh_list[day_idx]
                sim_dh = simulated_vars.get('DH', 0)
                
                error_pct = self._calculate_error_percentage(sim_dh, real_dh)
                status = self._determine_validation_status(error_pct)
                
                day_validation['variables']['DH'] = {
                    'real': real_dh,
                    'simulated': sim_dh,
                    'error_pct': error_pct,
                    'status': status
                }
                
                day_validation['summary']['total'] += 1
                day_validation['summary'][status.lower()] += 1
            
            # Validate other variables
            for var_key in daily_variables:
                if var_key in real_values and var_key in simulated_vars:
                    real_val = real_values[var_key]
                    sim_val = simulated_vars[var_key]
                    
                    # Skip if values are invalid
                    if real_val == 0 and sim_val == 0:
                        continue
                    
                    error_pct = self._calculate_error_percentage(sim_val, real_val)
                    status = self._determine_validation_status(error_pct)
                    
                    day_validation['variables'][var_key] = {
                        'real': real_val,
                        'simulated': sim_val,
                        'error_pct': error_pct,
                        'status': status
                    }
                    
                    day_validation['summary']['total'] += 1
                    day_validation['summary'][status.lower()] += 1
            
            # Calculate day success rate
            if day_validation['summary']['total'] > 0:
                day_validation['summary']['success_rate'] = (
                    (day_validation['summary']['precise'] + day_validation['summary']['acceptable']) / 
                    day_validation['summary']['total'] * 100
                )
            else:
                day_validation['summary']['success_rate'] = 0
            
            daily_validation_results.append(day_validation)
        
        return daily_validation_results
    
    def _get_accuracy_level(self, mape):
        """Determine accuracy level based on MAPE"""
        if mape < 10:
            return 'Excelente'
        elif mape < 20:
            return 'Buena'
        elif mape < 30:
            return 'Aceptable'
        else:
            return 'Mejorable'
    
    def _determine_validation_status(self, error_pct):
        """
        Determine validation status based on error percentage
        """
        if error_pct <= 5:
            return 'PRECISE'
        elif error_pct <= 10:
            return 'ACCEPTABLE'
        else:
            return 'INACCURATE'
    
    def _calculate_error_percentage(self, simulated, real):
        """Calcula porcentaje de error con manejo de casos especiales"""
        if real == 0:
            return 100.0 if simulated != 0 else 0.0
        
        error = abs(simulated - real) / abs(real) * 100
        return min(error, 999.99)  # Limitar errores extremos
    
    # Continuar con el resto de métodos del archivo original...
    # (Los demás métodos permanecen igual que en el archivo original)
    
    def validate_simulation(self, simulation_id: int) -> Dict[str, Any]:
        """
        Validate complete simulation results against real data.
        
        Returns:
            Dictionary with validation results, alerts, and summary
        """
        try:
            simulation = Simulation.objects.get(id=simulation_id)
            results = ResultSimulation.objects.filter(
                fk_simulation=simulation
            ).order_by('date')
            
            if not results.exists():
                return self._create_empty_validation_result()
            
            # Get real values from questionnaire
            real_values = self._extract_real_values(simulation)
            
            # Get historical demand for baseline
            demand_history = self._parse_demand_history(simulation.demand_history)
            hist_mean = float(np.mean(demand_history)) if demand_history else 0
            hist_std = float(np.std(demand_history)) if demand_history else 0
            
            # Validate each day
            daily_validations = []
            alerts = []
            
            for day_idx, result in enumerate(results):
                day_validation = self._validate_single_day(
                    result, real_values, hist_mean, hist_std, day_idx
                )
                daily_validations.append(day_validation)
                alerts.extend(day_validation['alerts'])
            
            # Aggregate validation results
            summary = self._generate_validation_summary(daily_validations, alerts)
            
            # Extract the required arguments for recommendations
            by_variable = summary.get('by_variable', {})
            success_rate = summary.get('overall_accuracy', 0) * 100  # Convert to percentage
            by_type_summary = summary.get('by_type', {})
            
            # Generate recommendations with correct arguments
            recommendations = self._generate_validation_recommendations(
                by_variable, success_rate, by_type_summary
            )
            
            return {
                'daily_validations': daily_validations,
                'alerts': alerts,
                'summary': summary,
                'recommendations': recommendations,
                'is_valid': summary['overall_accuracy'] >= 0.7,  # 70% threshold
                'real_values': real_values
            }
            
        except Exception as e:
            logger.error(f"Error validating simulation {simulation_id}: {str(e)}")
            return self._create_empty_validation_result()
    
    def _validate_single_day(self, result: ResultSimulation,
                           real_values: Dict[str, float],
                           hist_mean: float,
                           hist_std: float,
                           day_idx: int) -> Dict[str, Any]:
        """Validate a single day's simulation results"""
        variables = result.variables
        alerts = []
        validations = {}
        
        # Validate demand first (special case)
        demand = float(result.demand_mean)
        demand_validation = self._validate_demand_prediction(
            demand, hist_mean, hist_std, day_idx
        )
        validations['DPH'] = demand_validation
        
        if demand_validation['severity'] == 'ERROR':
            alerts.append({
                'day': result.date,
                'type': 'DEMAND_DEVIATION',
                'severity': 'ERROR',
                'message': f'Demand {demand:.2f} deviates significantly from expected range',
                'value': demand,
                'expected_range': demand_validation['expected_range']
            })
        
        # Validate other variables using single value validation
        for var_name, var_value in variables.items():
            if var_name.startswith('_') or var_name == 'DPH':
                continue
            
            if var_name in real_values and var_name in self.variable_tolerances:
                # Use single value validation for individual day validation
                validation = self._validate_single_value(
                    var_name,                              # var_name
                    var_value,                            # simulated_value
                    real_values[var_name],               # real_value
                    self.variable_tolerances[var_name]    # tolerance
                )
                validations[var_name] = validation
                
                if not validation['is_accurate'] and validation['error_rate'] > 0.3:
                    alerts.append({
                        'day': result.date,
                        'type': f'{var_name}_DEVIATION',
                        'severity': 'WARNING',
                        'message': f'{var_name} value {var_value:.2f} differs from expected {real_values[var_name]:.2f}',
                        'error_rate': validation['error_rate']
                    })
        
        # Calculate day accuracy
        accurate_count = sum(1 for v in validations.values() if v.get('is_accurate', False))
        total_count = len(validations)
        accuracy_rate = accurate_count / total_count if total_count > 0 else 0
        
        return {
            'date': result.date,
            'day_number': day_idx + 1,
            'validations': validations,
            'alerts': alerts,
            'accuracy_rate': accuracy_rate,
            'status': self._get_day_status(accuracy_rate)
        }
    
    def _validate_single_value(self, var_name: str, simulated_value: float, 
                          real_value: float, tolerance: float) -> Dict[str, Any]:
        """Validates a single simulated value against a real value"""
        if real_value is None or real_value == 0:
            return {
                'is_accurate': False,
                'error_rate': 1.0,
                'message': 'No real value for comparison',
                'status': 'NO_DATA'
            }
        
        try:
            simulated_float = float(simulated_value)
            real_float = float(real_value)
            
            # Calculate error rate
            error_rate = abs(simulated_float - real_float) / abs(real_float)
            is_accurate = error_rate <= tolerance
            
            return {
                'is_accurate': is_accurate,
                'error_rate': error_rate,
                'message': f'Error rate: {error_rate:.2%}',
                'status': 'ACCURATE' if is_accurate else 'INACCURATE',
                'simulated_value': simulated_float,
                'real_value': real_float,
                'difference': simulated_float - real_float,
                'tolerance': tolerance
            }
        
        except (ValueError, TypeError) as e:
            return {
                'is_accurate': False,
                'error_rate': 1.0,
                'message': f'Error processing values: {e}',
                'status': 'ERROR'
            }
    
    def _validate_demand_prediction(self, demand: float,
                                  hist_mean: float,
                                  hist_std: float,
                                  day_idx: int) -> Dict[str, Any]:
        """Validate demand prediction against historical patterns"""
        # Expected range based on historical data
        lower_bound = hist_mean - 2 * hist_std
        upper_bound = hist_mean + 2 * hist_std
        
        # Allow wider range in early days
        if day_idx < 7:
            expansion_factor = 1.5 - (day_idx * 0.07)  # 1.5x to 1x over first week
            range_expansion = hist_std * (expansion_factor - 1)
            lower_bound -= range_expansion
            upper_bound += range_expansion
        
        is_within_range = lower_bound <= demand <= upper_bound
        
        if is_within_range:
            severity = 'OK'
        elif hist_mean * 0.5 <= demand <= hist_mean * 1.5:
            severity = 'WARNING'
        else:
            severity = 'ERROR'
        
        deviation_from_mean = abs(demand - hist_mean) / hist_mean if hist_mean > 0 else 0
        
        return {
            'value': demand,
            'historical_mean': hist_mean,
            'historical_std': hist_std,
            'expected_range': (lower_bound, upper_bound),
            'is_within_range': is_within_range,
            'severity': severity,
            'deviation_rate': deviation_from_mean,
            'is_accurate': severity != 'ERROR'
        }
    
    def _extract_real_values(self, simulation: Simulation) -> Dict[str, float]:
        """Extract real values from questionnaire and business data"""
        real_values = {}
        
        try:
            # Get answers from questionnaire
            answers = Answer.objects.filter(
                fk_questionary_result=simulation.fk_questionary_result
            ).select_related('fk_question__fk_variable')
            
            for answer in answers:
                if answer.fk_question.fk_variable:
                    var_initials = answer.fk_question.fk_variable.initials
                    if var_initials and answer.answer:
                        try:
                            # Parse numeric value
                            value = self._parse_numeric_value(answer.answer)
                            if value is not None:
                                real_values[var_initials] = value
                        except:
                            continue
            
            # Calculate derived values
            real_values = self._calculate_derived_real_values(real_values)
            
            logger.info(f"Extracted {len(real_values)} real values for validation")
            
        except Exception as e:
            logger.error(f"Error extracting real values: {str(e)}")
        
        return real_values
    
    def _parse_numeric_value(self, value: Any) -> Optional[float]:
        """Parse a value to float, handling various formats"""
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Remove common formatting
            import re
            cleaned = re.sub(r'[^\d.-]', '', value)
            if cleaned:
                try:
                    return float(cleaned)
                except:
                    pass
        
        if isinstance(value, list) and len(value) > 0:
            # For lists, return average
            try:
                return float(np.mean([float(x) for x in value if x is not None]))
            except:
                pass
        
        return None
    
    def _calculate_derived_real_values(self, real_values: Dict[str, float]) -> Dict[str, float]:
        """Calculate derived values that aren't directly in questionnaire"""
        # Total income
        if 'IT' not in real_values and all(k in real_values for k in ['TPV', 'PVP']):
            real_values['IT'] = real_values['TPV'] * real_values['PVP']
        
        # Total expenses
        if 'TG' not in real_values and 'GO' in real_values:
            # Estimate general expenses as 20% of operating
            real_values['TG'] = real_values['GO'] * 1.2
        
        # Total profit
        if 'GT' not in real_values and all(k in real_values for k in ['IT', 'TG']):
            real_values['GT'] = real_values['IT'] - real_values['TG']
        
        # Production capacity
        if 'CPROD' not in real_values and 'QPL' in real_values:
            real_values['CPROD'] = real_values['QPL'] * 1.2  # 20% headroom
        
        # Customers served
        if 'TCAE' not in real_values and 'CPD' in real_values:
            real_values['TCAE'] = real_values['CPD'] * 0.95  # 95% efficiency
        
        return real_values
    
    def _parse_demand_history(self, demand_history) -> List[float]:
        """Parse demand history data"""
        try:
            import json
            if isinstance(demand_history, str):
                data = json.loads(demand_history)
            else:
                data = demand_history
            
            if isinstance(data, list):
                return [float(x) for x in data if x is not None]
            
        except Exception as e:
            logger.error(f"Error parsing demand history: {str(e)}")
        
        return []
    
    def _generate_validation_summary(self, 
                                   daily_validations: List[Dict],
                                   alerts: List[Dict]) -> Dict[str, Any]:
        """Generate summary of validation results"""
        total_days = len(daily_validations)
        
        # Calculate overall metrics
        accuracy_rates = [d['accuracy_rate'] for d in daily_validations]
        overall_accuracy = np.mean(accuracy_rates) if accuracy_rates else 0
        
        # Count days by status
        status_counts = {
            'EXCELLENT': sum(1 for d in daily_validations if d['status'] == 'EXCELLENT'),
            'GOOD': sum(1 for d in daily_validations if d['status'] == 'GOOD'),
            'FAIR': sum(1 for d in daily_validations if d['status'] == 'FAIR'),
            'POOR': sum(1 for d in daily_validations if d['status'] == 'POOR')
        }
        
        # Analyze alerts
        alert_counts = {}
        for alert in alerts:
            alert_type = alert['type']
            alert_counts[alert_type] = alert_counts.get(alert_type, 0) + 1
        
        # Variable-specific accuracy
        variable_accuracy = {}
        for day in daily_validations:
            for var_name, validation in day['validations'].items():
                if var_name not in variable_accuracy:
                    variable_accuracy[var_name] = []
                variable_accuracy[var_name].append(validation.get('is_accurate', False))
        
        variable_summary = {}
        for var_name, accuracies in variable_accuracy.items():
            variable_summary[var_name] = {
                'accuracy_rate': sum(accuracies) / len(accuracies) if accuracies else 0,
                'total_validations': len(accuracies),
                'accurate_count': sum(accuracies)
            }
        
        return {
            'total_days': total_days,
            'overall_accuracy': overall_accuracy,
            'accuracy_std': np.std(accuracy_rates) if len(accuracy_rates) > 1 else 0,
            'status_distribution': status_counts,
            'alert_summary': alert_counts,
            'variable_performance': variable_summary,
            'success_rate': (status_counts['EXCELLENT'] + status_counts['GOOD']) / total_days if total_days > 0 else 0,
            'by_variable': variable_summary,  # Alias for compatibility
            'by_type': {}  # Empty for now, can be expanded
        }
    
    def _get_day_status(self, accuracy_rate: float) -> str:
        """Determine day status based on accuracy rate"""
        if accuracy_rate >= 0.9:
            return 'EXCELLENT'
        elif accuracy_rate >= 0.75:
            return 'GOOD'
        elif accuracy_rate >= 0.6:
            return 'FAIR'
        else:
            return 'POOR'
    
    def _generate_validation_recommendations(self, by_variable, success_rate, by_type_summary):
        """Genera recomendaciones basadas en los resultados de validación"""
        recommendations = []
        
        # Recomendación general basada en tasa de éxito
        if success_rate >= 90:
            recommendations.append({
                'type': 'success',
                'message': 'El modelo muestra una excelente precisión general. Los valores simulados son altamente confiables.',
                'priority': 'low'
            })
        elif success_rate >= 70:
            recommendations.append({
                'type': 'warning',
                'message': 'El modelo tiene precisión aceptable pero puede mejorarse. Revise las variables con mayor error.',
                'priority': 'medium'
            })
        else:
            recommendations.append({
                'type': 'error',
                'message': 'El modelo requiere calibración significativa. Muchas variables muestran desviaciones importantes.',
                'priority': 'high'
            })
        
        # Recomendaciones específicas por variable
        critical_vars = []
        for var_key, var_data in by_variable.items():
            if isinstance(var_data, dict) and var_data.get('accuracy_rate', 1) < 0.5:
                critical_vars.append({
                    'variable': var_key,
                    'accuracy': var_data.get('accuracy_rate', 0) * 100
                })
        
        if critical_vars:
            # Ordenar por precisión ascendente
            critical_vars.sort(key=lambda x: x['accuracy'])
            
            # Tomar las 3 peores
            worst_vars = critical_vars[:3]
            var_list = ', '.join([f"{v['variable']} ({v['accuracy']:.1f}% precisión)" for v in worst_vars])
            
            recommendations.append({
                'type': 'error',
                'message': f'Variables críticas que requieren revisión: {var_list}',
                'priority': 'high'
            })
        
        # Recomendaciones por tipo
        for var_type, type_data in by_type_summary.items():
            if isinstance(type_data, dict) and type_data.get('total', 0) > 0:
                type_success_rate = (type_data.get('precise', 0) / type_data['total']) * 100
                
                if type_success_rate < 50:
                    recommendations.append({
                        'type': 'warning',
                        'message': f'Las variables de tipo "{var_type}" muestran baja precisión ({type_success_rate:.1f}%). Considere revisar las ecuaciones relacionadas.',
                        'priority': 'medium'
                    })
        
        return recommendations
    
    def _create_empty_validation_result(self) -> Dict[str, Any]:
        """Create empty validation result structure"""
        return {
            'daily_validations': [],
            'alerts': [],
            'summary': {
                'total_days': 0,
                'overall_accuracy': 0,
                'accuracy_std': 0,
                'status_distribution': {},
                'alert_summary': {},
                'variable_performance': {},
                'success_rate': 0,
                'by_variable': {},
                'by_type': {}
            },
            'recommendations': ["No se encontraron resultados para validar"],
            'is_valid': False,
            'real_values': {}
        }