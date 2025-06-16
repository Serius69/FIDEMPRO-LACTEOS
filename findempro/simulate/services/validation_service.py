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
from questionary.models import Answer

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
    def _calculate_daily_validation_summary(self, daily_validation_results):
        """
        Calculate summary statistics for daily validation
        """
        total_days = len(daily_validation_results)
        total_variables = 0
        total_precise = 0
        total_acceptable = 0
        total_inaccurate = 0
        
        for day_result in daily_validation_results:
            total_variables += day_result['summary']['total']
            total_precise += day_result['summary']['precise']
            total_acceptable += day_result['summary']['acceptable']
            total_inaccurate += day_result['summary']['inaccurate']
        
        return {
            'total_days': total_days,
            'total_validations': total_variables,
            'total_precise': total_precise,
            'total_acceptable': total_acceptable,
            'total_inaccurate': total_inaccurate,
            'overall_success_rate': (
                (total_precise + total_acceptable) / total_variables * 100 
                if total_variables > 0 else 0
            ),
            'precision_rate': (total_precise / total_variables * 100) if total_variables > 0 else 0
        }
    def _generate_daily_validation_charts(self, daily_validation_results, selected_variables=None):
        """
        Generate validation charts comparing real vs simulated values by day
        """
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')
        
        charts = {}
        
        # Default variables to chart if none selected
        if not selected_variables:
            selected_variables = ['DH', 'CPROD', 'TPV', 'IT', 'GT']
        
        for var_key in selected_variables:
            try:
                # Collect data for this variable across all days
                days = []
                real_values = []
                simulated_values = []
                errors = []
                
                for day_result in daily_validation_results:
                    if var_key in day_result['variables']:
                        var_data = day_result['variables'][var_key]
                        days.append(day_result['day'])
                        real_values.append(var_data['real'])
                        simulated_values.append(var_data['simulated'])
                        errors.append(var_data['error_pct'])
                
                if len(days) < 2:
                    continue
                
                # Create figure with two subplots
                fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), 
                                            gridspec_kw={'height_ratios': [3, 1]})
                
                # Main plot: Real vs Simulated
                ax1.plot(days, real_values, 'b-', marker='o', markersize=6, 
                        linewidth=2, label='Real Values', alpha=0.8)
                ax1.plot(days, simulated_values, 'r--', marker='s', markersize=6, 
                        linewidth=2, label='Simulated Values', alpha=0.8)
                
                # Fill area between lines
                ax1.fill_between(days, real_values, simulated_values, 
                            where=[r >= s for r, s in zip(real_values, simulated_values)],
                            alpha=0.2, color='green', label='Real > Simulated')
                ax1.fill_between(days, real_values, simulated_values,
                            where=[r < s for r, s in zip(real_values, simulated_values)],
                            alpha=0.2, color='red', label='Simulated > Real')
                
                ax1.set_xlabel('Simulation Day', fontsize=12)
                ax1.set_ylabel(f'Value ({self._get_unit_for_variable(var_key)})', fontsize=12)
                ax1.set_title(f'{var_key} - Daily Validation Comparison', fontsize=14, fontweight='bold')
                ax1.legend(loc='best')
                ax1.grid(True, alpha=0.3)
                
                # Error plot
                colors = ['green' if e <= 5 else 'orange' if e <= 10 else 'red' for e in errors]
                bars = ax2.bar(days, errors, color=colors, alpha=0.7)
                
                # Add horizontal lines for thresholds
                ax2.axhline(y=5, color='green', linestyle='--', alpha=0.5, label='Precise (5%)')
                ax2.axhline(y=10, color='orange', linestyle='--', alpha=0.5, label='Acceptable (10%)')
                
                ax2.set_xlabel('Simulation Day', fontsize=12)
                ax2.set_ylabel('Error %', fontsize=12)
                ax2.set_title('Daily Error Percentage', fontsize=12)
                ax2.legend(loc='upper right', fontsize=9)
                ax2.grid(True, alpha=0.3, axis='y')
                
                plt.tight_layout()
                
                # Convert to base64
                buffer = BytesIO()
                fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
                buffer.seek(0)
                charts[var_key] = base64.b64encode(buffer.getvalue()).decode('utf-8')
                plt.close(fig)
                
            except Exception as e:
                logger.error(f"Error generating daily validation chart for {var_key}: {str(e)}")
                plt.close('all')
                continue
        
        return charts
    
    def _get_unit_for_variable(self, var_key):
        """
        Get unit for a variable key
        """
        unit_map = {
            'DH': 'L',
            'DE': 'L',
            'CPROD': 'L',
            'TPV': 'L',
            'IT': 'Bs',
            'GT': 'Bs',
            'GO': 'Bs',
            'TPPRO': 'L',
            'IPF': 'L'
        }
        return unit_map.get(var_key, '')
    
    def _validate_model_predictions(self, simulation_instance, results_simulation, historical_demand):
        """Valida las predicciones del modelo contra todos los días simulados"""
        
        validation_details = []
        all_errors = []
        precise_count = 0
        acceptable_count = 0
        inaccurate_count = 0
        
        # Validar todos los días de simulación
        for i, result in enumerate(results_simulation):
            simulated = float(result.demand_mean)
            
            # Si hay dato histórico para ese día lo usamos para comparar
            real = None
            if historical_demand and i < len(historical_demand):
                real = float(historical_demand[i])
            else:
                # Si no hay dato histórico, usamos el valor esperado de la distribución
                real = float(result.demand_expected)
            
            difference = simulated - real
            error_pct = abs(difference) / real * 100 if real > 0 else 0
            
            # Determinar veredicto
            if error_pct < 10:
                verdict = 'PRECISA'
                precise_count += 1
            elif error_pct < 20:
                verdict = 'ACEPTABLE'
                acceptable_count += 1
            else:
                verdict = 'INEXACTA'
                inaccurate_count += 1
            
            all_errors.append(error_pct)
            
            validation_details.append({
                'pyme_id': f'QRS-{simulation_instance.id}{i:03d}',
                'business_name': simulation_instance.fk_questionary_result.fk_questionary.fk_product.fk_business.name,
                'product': simulation_instance.fk_questionary_result.fk_questionary.fk_product.name,
                'period': f'Día {i+1}',
                'simulated_demand': simulated,
                'real_demand': real,
                'difference': difference,
                'error_percentage': error_pct,
                'verdict': verdict,
                'is_historical': i < len(historical_demand) if historical_demand else False
            })
        
        # Calcular métricas agregadas
        if all_errors:
            mae = np.mean([abs(d['difference']) for d in validation_details])
            mape = np.mean(all_errors)
            rmse = np.sqrt(np.mean([d['difference']**2 for d in validation_details]))
            
            # Calcular R²
            real_values = [d['real_demand'] for d in validation_details]
            sim_values = [d['simulated_demand'] for d in validation_details]
            if len(real_values) > 1:
                correlation = np.corrcoef(real_values, sim_values)[0, 1]
                r_squared = correlation ** 2
            else:
                r_squared = 0
        else:
            mae = mape = rmse = r_squared = 0
        
        # Análisis por distribución
        dist_name = simulation_instance.fk_fdp.get_distribution_type_display()
        by_distribution = {
            dist_name: {
                'count': len(validation_details),
                'avg_mape': mape,
                'best_fit_product': simulation_instance.fk_questionary_result.fk_questionary.fk_product.name if mape < 10 else None
            }
        }
        
        # Generar recomendaciones basadas en todos los días
        recommendations = []
        if mape < 10:
            recommendations.append("El modelo muestra una precisión excelente para todo el período simulado.")
        elif mape < 20:
            recommendations.append("El modelo tiene precisión aceptable. Se sugiere monitorear los días más inexactos.")
        else:
            recommendations.append("El modelo requiere calibración. Revise especialmente los días con mayor error.")
        
        if r_squared < 0.7:
            recommendations.append("La correlación entre valores simulados y esperados es baja. Considere ajustar parámetros.")
        
        # Alertas específicas para días con error alto
        high_error_days = [d for d in validation_details if d['error_percentage'] > 30]
        if high_error_days:
            recommendations.append(f"Hay {len(high_error_days)} días con error superior al 30%. Revisar estos períodos.")
        
        total = len(validation_details)
        success_rate = (precise_count / total * 100) if total > 0 else 0
        
        return {
            'summary': {
                'is_valid': mape < 20,
                'success_rate': success_rate,
                'avg_mape': mape,
                'precise_count': precise_count,
                'acceptable_count': acceptable_count,
                'inaccurate_count': inaccurate_count,
                'total_days': total
            },
            'details': validation_details,
            'metrics': {
                'mae': mae,
                'mape': mape,
                'rmse': rmse,
                'r_squared': r_squared
            },
            'by_distribution': by_distribution,
            'recommendations': recommendations,
            'alerts': {
                'high_error_days': len(high_error_days) if high_error_days else 0
            }
        }
        
    def _extract_output_variable_from_equation(self, expression):
        """Extrae la variable de salida de una ecuación"""
        if '=' in expression:
            lhs = expression.split('=')[0].strip()
            # Extraer solo letras mayúsculas (variables)
            import re
            match = re.match(r'^([A-Z][A-Z0-9]*)$', lhs)
            if match:
                return match.group(1)
        return None
    def _get_variable_type_name(self, type_code):
        """Convierte el código de tipo a nombre descriptivo"""
        type_names = {
            1: 'Exógena',
            2: 'Estado',
            3: 'Endógena'
        }
        return type_names.get(type_code, 'Otra')
    def _validate_model_variables(self, simulation_instance, results_simulation, all_variables_extracted):
        """Valida todas las variables del modelo (excepto demanda) contra valores reales de la base de datos"""
        
        # Obtener TODAS las variables disponibles en el sistema desde la base de datos
        from variable.models import Variable, Equation
        
        # Cargar todas las variables del producto desde la base de datos
        product = simulation_instance.fk_questionary_result.fk_questionary.fk_product
        db_variables = Variable.objects.filter(
            fk_product=product,
            is_active=True
        ).values('initials', 'name', 'unit', 'type')
        
        # CORRECCIÓN: Obtener ecuaciones activas para identificar variables calculadas
        active_equations = Equation.objects.filter(
            is_active=True,
            fk_area__fk_product=product
        ).select_related('fk_area')
        
        # Extraer variables que son output de ecuaciones activas
        calculated_variables = set()
        for equation in active_equations:
            output_var = self._extract_output_variable_from_equation(equation.expression)
            if output_var:
                calculated_variables.add(output_var)
        
        logger.info(f"Found {len(calculated_variables)} variables with active equations")
        
        # Crear diccionario dinámico de variables a validar
        variables_to_validate = {}
        for var in db_variables:
            # CORRECCIÓN: Solo incluir variables que tienen ecuaciones activas
            if var['initials'] not in calculated_variables:
                continue
                
            # Excluir variables de demanda ya validadas en otra sección
            if var['initials'] in ['DE', 'DH', 'DI']:
                continue
                
            # Determinar tolerancia según tipo de variable
            tolerance = self._determine_tolerance_by_type(var['initials'], var['type'])
            
            variables_to_validate[var['initials']] = {
                'description': var['name'],
                'unit': var['unit'] or '',
                'type': self._get_variable_type_name(var['type']),
                'tolerance': tolerance
            }
        
        # Obtener valores reales desde múltiples fuentes en la base de datos
        real_values = self._extract_complete_real_values_from_database(simulation_instance)
        
        if not real_values:
            logger.warning("No real values found in database")
            return self._create_empty_validation_result()
        
        # Inicializar contadores y estructuras
        by_variable = {}
        daily_details = []
        total_variables = 0
        precise_count = 0
        acceptable_count = 0
        inaccurate_count = 0
        by_type_summary = {}
        
        # Validar cada variable encontrada
        for var_key, var_info in variables_to_validate.items():
            # Solo validar si tenemos valores reales
            if var_key not in real_values:
                logger.debug(f"No real value found for {var_key}, skipping validation")
                continue
            
            real_value = float(real_values[var_key])
            
            # Recolectar valores simulados para todos los días
            validation_result = self._validate_single_variable(
                var_key, var_info, real_value, results_simulation, all_variables_extracted
            )
            
            # CORRECCIÓN: Solo incluir si la variable fue realmente calculada (tiene valores != 0)
            if (validation_result['status'] != 'NO_DATA' and 
                validation_result.get('simulated_values_count', 0) > 0 and 
                validation_result.get('simulated_avg', 0) != 0):
                
                total_variables += 1
                
                # Actualizar contadores según el resultado
                if validation_result['status'] == 'PRECISA':
                    precise_count += 1
                elif validation_result['status'] == 'ACEPTABLE':
                    acceptable_count += 1
                elif validation_result['status'] == 'INEXACTA':
                    inaccurate_count += 1
                
                # Agregar a resumen por variable
                by_variable[var_key] = validation_result
                
                # Agregar detalles diarios si existen
                if 'daily_details' in validation_result:
                    for day, details in validation_result['daily_details'].items():
                        daily_details.append({
                            'variable': var_key,
                            'description': var_info['description'],
                            'type': var_info['type'],
                            **details
                        })
                
                # Actualizar resumen por tipo
                var_type = var_info['type']
                if var_type not in by_type_summary:
                    by_type_summary[var_type] = {
                        'total': 0,
                        'precise': 0,
                        'acceptable': 0,
                        'inaccurate': 0
                    }
                
                by_type_summary[var_type]['total'] += 1
                if validation_result['status'] == 'PRECISA':
                    by_type_summary[var_type]['precise'] += 1
                elif validation_result['status'] == 'ACEPTABLE':
                    by_type_summary[var_type]['acceptable'] += 1
                else:
                    by_type_summary[var_type]['inaccurate'] += 1
            else:
                logger.debug(f"Variable {var_key} excluded from validation (no data or all zeros)")
        
        # Generar gráficos comparativos
        chart_generator =ChartGenerator()
        comparison_charts = {}
        if by_variable:
            comparison_charts = chart_generator._generate_variable_comparison_charts(by_variable, real_values)
        
        # Calcular métricas agregadas
        success_rate = (precise_count / total_variables * 100) if total_variables > 0 else 0
        
        # Generar recomendaciones basadas en la validación
        validation_recommendations = self._generate_validation_recommendations(
            by_variable, success_rate, by_type_summary
        )
        
        logger.info(f"Model variables validation completed: {total_variables} variables processed")
        logger.info(f"Results: {precise_count} precise, {acceptable_count} acceptable, {inaccurate_count} inaccurate")
        logger.info(f"Excluded {len(variables_to_validate) - total_variables} variables without active equations or with zero values")
        
        chart_generator = ChartGenerator()
        validation_charts = chart_generator._generate_validation_charts_for_variables(
            by_variable, results_simulation, all_variables_extracted
        )
        print(f"Generated {len(validation_charts)} validation charts")
        
        return {
            'summary': {
                'total_variables': total_variables,
                'precise_count': precise_count,
                'acceptable_count': acceptable_count,
                'inaccurate_count': inaccurate_count,
                'success_rate': success_rate,
                'is_valid': success_rate >= 70,
                'validation_score': self._calculate_validation_score(precise_count, acceptable_count, total_variables),
                'excluded_count': len(calculated_variables) - total_variables
            },
            'by_variable': by_variable,
            'by_type': by_type_summary,
            'daily_details': daily_details,
            'comparison_charts': comparison_charts,
            'recommendations': validation_recommendations,
            'validation_charts': validation_charts
        }
        
    def _calculate_validation_score(self, precise, acceptable, total):
        """Calcula un score de validación ponderado"""
        if total == 0:
            return 0
        
        # Ponderaciones: preciso=100%, aceptable=50%, inexacto=0%
        score = (precise * 1.0 + acceptable * 0.5) / total * 100
        return round(score, 2)
    def _extract_real_values_from_questionnaire(self, simulation_instance):
        """
        Extract real values from questionnaire with proper parsing for DH, DE, and ED
        """
        real_values = {}
        
        try:
            questionary_result = simulation_instance.fk_questionary_result
            if not questionary_result:
                logger.warning("No questionary result found for simulation")
                return real_values
            
            # Get answers with related questions and variables
            answers = questionary_result.fk_question_result_answer.select_related(
                'fk_question__fk_variable'
            ).all()
            
            logger.info(f"Found {answers.count()} answers in questionnaire")
            
            for answer in answers:
                try:
                    if answer.fk_question.fk_variable:
                        var_initials = answer.fk_question.fk_variable.initials
                        
                        if var_initials and answer.answer:
                            # Special handling for specific variables
                            if var_initials == 'DH':
                                # DH is a list of daily values
                                parsed_list = self._parse_demand_history_list(answer.answer)
                                if parsed_list:
                                    real_values[var_initials] = parsed_list  # Keep full list
                                    real_values[f'{var_initials}_AVG'] = float(np.mean(parsed_list))  # Store average
                                    logger.debug(f"DH parsed: {len(parsed_list)} values, avg: {real_values[f'{var_initials}_AVG']:.2f}")
                            
                            elif var_initials == 'DE':
                                # DE is expected daily demand (single float)
                                value = self._parse_numeric_value(answer.answer)
                                if value is not None:
                                    real_values[var_initials] = float(value)
                                    logger.debug(f"DE parsed: {real_values[var_initials]}")
                            
                            elif var_initials == 'ED':
                                # ED is seasonality (boolean converted to float)
                                value = self._parse_seasonality_value(answer.answer)
                                real_values[var_initials] = value
                                logger.debug(f"ED parsed: {answer.answer} -> {value}")
                            
                            else:
                                # Standard numeric parsing for other variables
                                value = self._parse_numeric_value(answer.answer)
                                if value is not None:
                                    real_values[var_initials] = value
                                    logger.debug(f"{var_initials} parsed: {value}")
                    
                except Exception as e:
                    logger.error(f"Error processing answer {answer.id}: {str(e)}")
                    continue
            
            # Calculate derived values
            real_values = self._calculate_derived_values(real_values, answers)
            
            logger.info(f"Real values extracted: {len(real_values)} variables")
            return real_values
            
        except Exception as e:
            logger.error(f"Error extracting real values from questionnaire: {str(e)}")
            return real_values
    
    def _parse_seasonality_value(self, value):
        """
        Parse seasonality boolean value to float (1.0 or 0.0)
        """
        if value is None:
            return 0.0
        
        # Handle boolean types
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        
        # Handle numeric types
        if isinstance(value, (int, float)):
            return 1.0 if value > 0 else 0.0
        
        # Handle string types
        if isinstance(value, str):
            value_lower = value.lower().strip()
            
            # Positive values
            if value_lower in ['sí', 'si', 'sí.', 'si.', 'yes', 'true', '1', 's']:
                return 1.0
            
            # Negative values
            if value_lower in ['no', 'no.', 'false', '0', 'n']:
                return 0.0
        
        # Default to no seasonality
        return 0.0
    
    def _calculate_derived_values(self, real_values, questionary_answers):
        """
        Calcula valores derivados que no están directamente en el cuestionario
        pero pueden ser calculados a partir de otros valores
        """
        try:
            derived_count = 0
            
            # Calcular Total Gastos si no existe pero tenemos componentes
            if 'TG' not in real_values:
                go = real_values.get('GO', 0)
                gg = real_values.get('GG', 0)
                cfd = real_values.get('CFD', 0)
                se = real_values.get('SE', 0) / 30 if real_values.get('SE', 0) > 1000 else real_values.get('SE', 0)
                
                if any([go, gg, cfd, se]):
                    real_values['TG'] = go + gg + cfd + se
                    derived_count += 1
            
            # Calcular Gastos Operativos si no existe
            if 'GO' not in real_values and 'CFD' in real_values:
                real_values['GO'] = real_values['CFD'] * 1.5  # Estimación
                derived_count += 1
            
            # Calcular Ingresos Totales si tenemos precio y ventas
            if 'IT' not in real_values and 'PVP' in real_values and 'TPV' in real_values:
                real_values['IT'] = real_values['PVP'] * real_values['TPV']
                derived_count += 1
            
            # Calcular TPV si tenemos clientes y ventas por cliente
            if 'TPV' not in real_values and 'CPD' in real_values and 'VPC' in real_values:
                real_values['TPV'] = real_values['CPD'] * real_values['VPC']
                derived_count += 1
            elif 'TPV' not in real_values and 'CPD' in real_values:
                # Estimar VPC basado en el precio
                pvp = real_values.get('PVP', 15.5)
                if pvp < 10:
                    vpc = 2.5  # Productos baratos, más unidades por cliente
                else:
                    vpc = 1.5  # Productos caros, menos unidades
                real_values['VPC'] = vpc
                real_values['TPV'] = real_values['CPD'] * vpc
                derived_count += 2
            
            # Calcular TCAE si no existe
            if 'TCAE' not in real_values and 'CPD' in real_values:
                real_values['TCAE'] = real_values['CPD'] * 0.95  # 95% de efectividad
                derived_count += 1
            
            # Calcular TPPRO si no existe pero tenemos TPV
            if 'TPPRO' not in real_values and 'TPV' in real_values:
                real_values['TPPRO'] = real_values['TPV'] * 1.05  # 5% buffer de producción
                derived_count += 1
            
            # Calcular Ganancias Totales si tenemos ingresos y gastos
            if 'GT' not in real_values and 'IT' in real_values and 'TG' in real_values:
                real_values['GT'] = real_values['IT'] - real_values['TG']
                derived_count += 1
            
            # Convertir valores mensuales a diarios donde sea necesario
            monthly_to_daily = {
                'SE': 30,  # Sueldos
                'GMM': 30, # Marketing
            }
            
            for var, divisor in monthly_to_daily.items():
                if var in real_values and real_values[var] > 1000:
                    real_values[f"{var}_MONTHLY"] = real_values[var]
                    real_values[var] = real_values[var] / divisor
                    derived_count += 1
            
            logger.info(f"Derived values calculated. Total variables: {derived_count}")
            
            return real_values
            
        except Exception as e:
            logger.error(f"Error calculating derived values: {str(e)}")
            return real_values
    
    def _parse_demand_history_list(self, value):
        """
        Parse demand history list from various formats
        """
        try:
            if isinstance(value, list):
                return [float(x) for x in value if x is not None]
            
            if isinstance(value, str):
                # Try JSON parse first
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        return [float(x) for x in parsed if x is not None]
                except:
                    pass
                
                # Clean string and parse
                cleaned = value.strip()
                cleaned = cleaned.replace('[', '').replace(']', '').replace('{', '').replace('}', '')
                
                # Try different delimiters
                if ',' in cleaned:
                    values = [x.strip() for x in cleaned.split(',')]
                elif ';' in cleaned:
                    values = [x.strip() for x in cleaned.split(';')]
                elif '\n' in cleaned:
                    values = [x.strip() for x in cleaned.split('\n')]
                elif ' ' in cleaned:
                    values = [x.strip() for x in cleaned.split()]
                else:
                    return []
                
                # Convert to float
                result = []
                for val in values:
                    try:
                        if val:
                            num = float(val.replace(',', '.'))
                            if not np.isnan(num) and not np.isinf(num):
                                result.append(num)
                    except:
                        continue
                
                return result
            
            return []
            
        except Exception as e:
            logger.error(f"Error parsing demand history: {str(e)}")
            return []
    
    def _extract_values_from_product(self, product):
        """Extrae valores relevantes del modelo Product"""
        values = {}
        
        try:
            # Valores financieros del producto
            if product.profit_margin is not None:
                values['MB'] = float(product.profit_margin) / 100  # Convertir porcentaje
            
            if product.earnings is not None:
                values['GT_PRODUCT'] = float(product.earnings)
            
            if product.costs is not None:
                values['CT_PRODUCT'] = float(product.costs)
            
            # Valores de producción
            if product.production_output is not None:
                values['CPROD_BASE'] = float(product.production_output)
            
            if product.inventory_levels is not None:
                values['INV_PRODUCT'] = float(product.inventory_levels)
            
            if product.demand_forecast is not None:
                values['DF_PRODUCT'] = float(product.demand_forecast)
                
        except Exception as e:
            logger.debug(f"Error extracting product values: {e}")
        
        return values
    
    
    
    def _extract_complete_real_values_from_database(self, simulation_instance):
        """
        Extrae valores reales desde TODAS las fuentes disponibles en la base de datos
        """
        real_values = {}
        
        try:
            # 1. Valores del cuestionario (QuestionaryResult)
            try:
                questionary_values = self._extract_real_values_from_questionnaire(simulation_instance)
                real_values.update(questionary_values)
            except Exception as e:
                logger.error(f"Error in questionnaire extraction: {str(e)}")
            
            # 2. Valores del producto
            try:
                product = simulation_instance.fk_questionary_result.fk_questionary.fk_product
                if product:
                    product_values = self._extract_values_from_product(product)
                    real_values.update(product_values)
            except Exception as e:
                logger.error(f"Error in product extraction: {str(e)}")
            
            # 3. Valores del negocio
            try:
                business = product.fk_business if product else None
                if business:
                    business_values = self._extract_values_from_business(business)
                    real_values.update(business_values)
            except Exception as e:
                logger.error(f"Error in business extraction: {str(e)}")
            
            # 4. Valores de áreas
            try:
                if product:
                    area_values = self._extract_values_from_areas(product)
                    real_values.update(area_values)
            except Exception as e:
                logger.error(f"Error in areas extraction: {str(e)}")
            
            # 5. Valores históricos
            try:
                historical_values = self._extract_historical_simulation_values(product)
                for key, value in historical_values.items():
                    if key not in real_values:
                        real_values[key] = value
            except Exception as e:
                logger.error(f"Error in historical extraction: {str(e)}")
            
            logger.info(f"Extracted {len(real_values)} real values from database")
            
            return real_values
            
        except Exception as e:
            logger.error(f"Error extracting complete real values: {str(e)}")
            return {}
    
    def _extract_values_from_business(self, business):
        """Extrae valores relevantes del modelo Business"""
        values = {}
        
        try:
            # Valores del negocio que pueden ser útiles
            if hasattr(business, 'monthly_revenue') and business.monthly_revenue:
                values['IT_MONTHLY'] = float(business.monthly_revenue)
                values['IT'] = float(business.monthly_revenue) / 30  # Diario
            
            if hasattr(business, 'monthly_expenses') and business.monthly_expenses:
                values['GO_MONTHLY'] = float(business.monthly_expenses)
                values['GO'] = float(business.monthly_expenses) / 30  # Diario
                
            if hasattr(business, 'employee_count') and business.employee_count:
                values['NEPP'] = float(business.employee_count)
                
        except Exception as e:
            logger.debug(f"Error extracting business values: {e}")
        
        return values

    def _extract_values_from_areas(self, product):
        """Extrae valores de las áreas asociadas al producto"""
        values = {}
        
        try:
            from product.models import Area
            
            areas = Area.objects.filter(
                fk_product=product,
                is_active=True
            )
            
            for area in areas:
                if area.params:
                    # Si params es un diccionario con valores numéricos
                    if isinstance(area.params, dict):
                        for key, value in area.params.items():
                            if isinstance(value, (int, float)):
                                # Mapear nombres de parámetros a variables
                                mapped_key = self._map_area_param_to_variable(key)
                                if mapped_key:
                                    values[mapped_key] = float(value)
                                    
        except Exception as e:
            logger.debug(f"Error extracting area values: {e}")
        
        return values

    
    def _map_area_param_to_variable(self, param_name):
        """Mapea nombres de parámetros de área a variables del sistema"""
        mapping = {
            'capacidad_produccion': 'CPROD',
            'capacidad_inventario': 'CIP',
            'empleados': 'NEPP',
            'costo_fijo': 'CFD',
            'precio_venta': 'PVP',
            'costo_unitario': 'CUIP',
            'stock_seguridad': 'SI',
            'clientes_diarios': 'CPD',
            'margen_ganancia': 'MB',
            'gastos_marketing': 'GMM',
            'tiempo_produccion': 'TPE',
            'demanda_esperada': 'DE',
        }
        
        return mapping.get(param_name.lower())
    
    def _extract_historical_simulation_values(self, product):
        """Extrae valores promedio de simulaciones históricas exitosas"""
        values = {}
        
        try:
            # Buscar simulaciones previas exitosas del mismo producto
            from simulate.models import Simulation, ResultSimulation
            from django.utils import timezone
            from datetime import timedelta
            
            # Últimas simulaciones exitosas (últimos 30 días)
            recent_date = timezone.now() - timedelta(days=30)
            
            recent_simulations = Simulation.objects.filter(
                fk_questionary_result__fk_questionary__fk_product=product,
                is_active=True,
                date_created__gte=recent_date
            ).order_by('-date_created')[:5]  # Últimas 5 simulaciones
            
            if recent_simulations.exists():
                # Recolectar valores promedio de todas las simulaciones
                aggregated_values = {}
                counts = {}
                
                for sim in recent_simulations:
                    results = ResultSimulation.objects.filter(
                        fk_simulation=sim,
                        is_active=True
                    )
                    
                    for result in results:
                        if result.variables:
                            for var_key, var_value in result.variables.items():
                                if isinstance(var_value, (int, float)):
                                    if var_key not in aggregated_values:
                                        aggregated_values[var_key] = 0
                                        counts[var_key] = 0
                                    
                                    aggregated_values[var_key] += float(var_value)
                                    counts[var_key] += 1
                
                # Calcular promedios
                for var_key in aggregated_values:
                    if counts[var_key] > 0:
                        values[f"{var_key}_HIST"] = aggregated_values[var_key] / counts[var_key]
                        
        except Exception as e:
            logger.debug(f"Error extracting historical simulation values: {e}")
        
        return values
    
    def _determine_tolerance_by_type(self, var_initials, var_type):
        """Determina la tolerancia según el tipo y naturaleza de la variable"""
        # Tolerancias específicas por variable
        specific_tolerances = {
            # Variables financieras críticas
            'IT': 0.10,  # Ingresos totales
            'GT': 0.15,  # Ganancias totales
            'GO': 0.05,  # Gastos operativos
            'CFD': 0.02, # Costos fijos (más estricto)
            
            # Variables de producción
            'CPROD': 0.02,  # Capacidad debe ser precisa
            'TPV': 0.10,    # Ventas pueden variar más
            'TPPRO': 0.05,  # Producción moderada
            
            # Variables de inventario
            'IPF': 0.15,  # Inventario puede fluctuar más
            'SI': 0.10,   # Stock de seguridad
            
            # Variables exactas
            'NEPP': 0.01,  # Número de empleados debe ser exacto
            'PVP': 0.05,   # Precios relativamente fijos
        }
        
        if var_initials in specific_tolerances:
            return specific_tolerances[var_initials]
        
        # Tolerancias por tipo de variable
        type_tolerances = {
            1: 0.05,  # Exógenas (deberían ser precisas)
            2: 0.10,  # Estado (pueden variar)
            3: 0.15,  # Endógenas (mayor variación esperada)
        }
        
        return type_tolerances.get(var_type, 0.10)
    
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
    
    def validate_daily_results(self, 
                             simulated_values: Dict[str, float],
                             real_values: Dict[str, float],
                             day_index: int = 0) -> Dict[str, Any]:
        """
        Validate a single day's results against real values.
        
        Args:
            simulated_values: Dictionary of simulated variable values
            real_values: Dictionary of real/expected values
            day_index: Day number in simulation
            
        Returns:
            Validation results for the day
        """
        validations = {}
        total_variables = 0
        accurate_count = 0
        
        for var_name, sim_value in simulated_values.items():
            # Skip metadata and internal variables
            if var_name.startswith('_') or var_name not in self.variable_tolerances:
                continue
            
            # Check if we have a real value to compare
            if var_name not in real_values:
                continue
            
            real_value = real_values[var_name]
            tolerance_type = self.variable_tolerances.get(var_name, 'normal')
            
            # Special handling for demand variables
            if tolerance_type == 'special':
                validation = self._validate_demand_variable(
                    var_name, sim_value, real_value, day_index
                )
            else:
                validation = self._validate_single_variable(
                    var_name, sim_value, real_value, tolerance_type
                )
            
            validations[var_name] = validation
            total_variables += 1
            
            if validation['is_accurate']:
                accurate_count += 1
        
        accuracy_rate = accurate_count / total_variables if total_variables > 0 else 0
        
        return {
            'day': day_index + 1,
            'validations': validations,
            'total_variables': total_variables,
            'accurate_count': accurate_count,
            'accuracy_rate': accuracy_rate,
            'status': self._get_day_status(accuracy_rate)
        }
    
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
    
    def _validate_single_variable(self, var_key, var_info, real_value, results_simulation, all_variables_extracted):
        """Valida una sola variable con mejor manejo de casos especiales"""
        
        # Validación inicial de valor real
        if real_value is None or (isinstance(real_value, (int, float)) and real_value == 0):
            logger.debug(f"Variable {var_key}: real value is zero or None, skipping validation")
            return {
                'description': var_info['description'],
                'unit': var_info['unit'],
                'type': var_info['type'],
                'real_value': real_value,
                'status': 'NO_DATA',
                'error': 'Sin valor real para comparación',
                'simulated_values_count': 0
            }
        
        simulated_values = []
        daily_details_by_day = {}
        
        # Casos especiales por variable
        special_cases = {
            'DH': self._handle_demand_history,
            'DE': self._handle_expected_demand,
            'ED': self._handle_seasonality
        }
        
        # Si es un caso especial, manejarlo diferente
        if var_key in special_cases:
            return special_cases[var_key](var_info, real_value, results_simulation)
        
        # Recolectar valores simulados de cada día
        for idx, result in enumerate(results_simulation):
            simulated_value = None
            
            try:
                # Extraer valor simulado con múltiples intentos
                simulated_value = self._extract_simulated_value(result, var_key, idx, all_variables_extracted)
                
                # Validar y procesar valor
                if simulated_value is not None:
                    try:
                        simulated_value_float = float(simulated_value)
                        
                        # Solo incluir valores diferentes de 0 y válidos
                        if simulated_value_float != 0 and not np.isnan(simulated_value_float) and not np.isinf(simulated_value_float):
                            simulated_values.append(simulated_value_float)
                            
                            # Calcular error diario
                            error_pct = self._calculate_error_percentage(simulated_value_float, real_value)
                            
                            daily_details_by_day[idx + 1] = {
                                'day': idx + 1,
                                'simulated': simulated_value_float,
                                'real': real_value,
                                'difference': simulated_value_float - real_value,
                                'error_pct': error_pct,
                                'is_acceptable': error_pct <= var_info['tolerance'] * 100
                            }
                            
                    except (ValueError, TypeError) as e:
                        logger.debug(f"Could not convert {var_key} value to float: {simulated_value}")
            
            except Exception as e:
                logger.debug(f"Error extracting {var_key} for day {idx+1}: {e}")
                continue
        
        # Si no hay valores simulados válidos
        if not simulated_values:
            return self._create_no_data_result(var_info, real_value)
        
        # Calcular estadísticas y resultado
        return self._calculate_validation_result(var_key, var_info, real_value, simulated_values, daily_details_by_day, len(results_simulation))
    
    def _extract_simulated_value(self, result, var_key, idx, all_variables_extracted):
        """Extrae valor simulado con múltiples estrategias"""
        simulated_value = None
        
        # 1. Intentar obtener de variables directamente
        if hasattr(result, 'variables') and result.variables:
            simulated_value = result.variables.get(var_key)
            
            # También buscar variantes del nombre
            if simulated_value is None:
                for key in result.variables.keys():
                    if key.upper() == var_key.upper():
                        simulated_value = result.variables[key]
                        break
        
        # 2. Intentar con el método get_variable_value si existe
        if simulated_value is None and hasattr(result, 'get_variable_value'):
            simulated_value = result.get_variable_value(var_key)
        
        # 3. Buscar en all_variables_extracted
        if simulated_value is None and all_variables_extracted and idx < len(all_variables_extracted):
            day_data = all_variables_extracted[idx]
            
            if isinstance(day_data, dict):
                # Buscar en totales_por_variable
                if 'totales_por_variable' in day_data:
                    vars_dict = day_data['totales_por_variable']
                    
                    # Buscar por clave exacta
                    if var_key in vars_dict:
                        if isinstance(vars_dict[var_key], dict):
                            simulated_value = vars_dict[var_key].get('total', vars_dict[var_key].get('value'))
                        else:
                            simulated_value = vars_dict[var_key]
                    else:
                        # Buscar por nombre de variable
                        for v_key, v_data in vars_dict.items():
                            if v_key.upper() == var_key.upper():
                                if isinstance(v_data, dict):
                                    simulated_value = v_data.get('total', v_data.get('value'))
                                else:
                                    simulated_value = v_data
                                break
                
                # Buscar directamente en day_data
                if simulated_value is None and var_key in day_data:
                    simulated_value = day_data[var_key]
                
                # Buscar en endogenous_results
                if simulated_value is None and 'endogenous_results' in day_data:
                    simulated_value = day_data['endogenous_results'].get(var_key)
                
                # Buscar en variable_initials_dict
                if simulated_value is None and 'variable_initials_dict' in day_data:
                    simulated_value = day_data['variable_initials_dict'].get(var_key)
        
        return simulated_value
    
    def _calculate_error_percentage(self, simulated, real):
        """Calcula porcentaje de error con manejo de casos especiales"""
        if real == 0:
            return 100.0 if simulated != 0 else 0.0
        
        error = abs(simulated - real) / abs(real) * 100
        return min(error, 999.99)  # Limitar errores extremos
    def _create_no_data_result(self, var_info, real_value):
        """Crea un resultado de no datos para una variable"""
        return {
            'description': var_info['description'],
            'unit': var_info['unit'],
            'type': var_info['type'],
            'real_value': real_value,
            'status': 'NO_DATA',
            'error': 'Variable no calculada por el modelo o todos los valores son cero',
            'simulated_values_count': 0,
            'simulated_avg': 0,
            'simulated_min': 0,
            'simulated_max': 0,
            'simulated_std': 0
        }
    
    def _calculate_std_dev(self, values):
        """Calcula desviación estándar manualmente"""
        if len(values) < 2:
            return 0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5
    
    def _calculate_validation_result(self, var_key, var_info, real_value, simulated_values, daily_details_by_day, total_days):
        """Calcula resultado completo de validación"""
        simulation_service = StatisticalService()
        
        # Calcular estadísticas
        avg_simulated = sum(simulated_values) / len(simulated_values)
        min_simulated = min(simulated_values)
        max_simulated = max(simulated_values)
        std_simulated = self._calculate_std_dev(simulated_values)
        
        # Calcular error promedio
        error_pct = self._calculate_error_percentage(avg_simulated, real_value)
        
        # Determinar estado de validación
        tolerance = var_info['tolerance'] * 100
        if error_pct <= tolerance:
            status = 'PRECISA'
        elif error_pct <= tolerance * 2:
            status = 'ACEPTABLE'
        else:
            status = 'INEXACTA'
        
        # Calcular tendencia
        trend = 'stable'
        if len(simulated_values) >= 3:
            trend = simulation_service._calculate_trend(simulated_values)
        
        return {
            'description': var_info['description'],
            'unit': var_info['unit'],
            'type': var_info['type'],
            'real_value': real_value,
            'simulated_avg': avg_simulated,
            'simulated_min': min_simulated,
            'simulated_max': max_simulated,
            'simulated_std': std_simulated,
            'simulated_values_count': len(simulated_values),
            'total_days': total_days,
            'days_with_values': len(simulated_values),
            'error_pct': error_pct,
            'status': status,
            'tolerance': tolerance,
            'daily_details': daily_details_by_day,
            'trend': trend,
            'coverage': (len(simulated_values) / total_days * 100) if total_days > 0 else 0
        }
    def _handle_expected_demand(self, var_info, real_value, results_simulation):
        """Manejo especial para DE (Demanda Esperada)"""
        # DE se valida normalmente pero con tolerancia más alta
        simulated_values = []
        daily_details_by_day = {}
        
        for idx, result in enumerate(results_simulation):
            if hasattr(result, 'demand_mean'):
                simulated_value = float(result.demand_mean)
                simulated_values.append(simulated_value)
                
                error_pct = self._calculate_error_percentage(simulated_value, real_value)
                
                daily_details_by_day[idx + 1] = {
                    'day': idx + 1,
                    'simulated': simulated_value,
                    'real': real_value,
                    'difference': simulated_value - real_value,
                    'error_pct': error_pct,
                    'is_acceptable': error_pct <= 20  # Mayor tolerancia para demanda
                }
        
        if not simulated_values:
            return self._create_no_data_result(var_info, real_value)
        
        # Usar tolerancia especial para demanda
        var_info_copy = var_info.copy()
        var_info_copy['tolerance'] = 0.20  # 20% de tolerancia
        
        return self._calculate_validation_result(
            'DE', var_info_copy, real_value, simulated_values, 
            daily_details_by_day, len(results_simulation)
        )
    def _handle_demand_history(self, var_info, real_value, results_simulation):
        """Manejo especial para DH (Demanda Histórica)"""
        # DH es típicamente una lista, calcular su media
        if isinstance(real_value, list):
            real_value = np.mean(real_value) if real_value else 0
        
        return {
            'description': var_info['description'],
            'unit': var_info['unit'],
            'type': var_info['type'],
            'real_value': real_value,
            'status': 'INFORMATIVO',
            'error': 'Variable histórica - no requiere validación',
            'simulated_values_count': 0
        }

    def _handle_seasonality(self, var_info, real_value, results_simulation):
        """Manejo especial para ED (Estacionalidad)"""
        return {
            'description': var_info['description'],
            'unit': var_info['unit'],
            'type': var_info['type'],
            'real_value': real_value,
            'status': 'PARAMETRO',
            'error': 'Parámetro de configuración - no requiere validación',
            'simulated_values_count': 0
        }
    
    def _validate_demand_variable(self, var_name: str,
                                simulated: float,
                                real: float,
                                day_index: int) -> Dict[str, Any]:
        """Special validation for demand variables"""
        # For DPH (daily demand), we expect variation but within reasonable bounds
        if var_name == 'DPH':
            # Allow more variation in early days, stabilizing over time
            base_tolerance = 0.3  # 30% base
            time_factor = max(0.1, 1 - (day_index / 30))  # Decreases over time
            tolerance = base_tolerance * (1 + time_factor)
        else:
            tolerance = self.tolerance_thresholds['flexible']
        
        error_rate = abs(simulated - real) / abs(real) if real != 0 else 0
        is_accurate = error_rate <= tolerance
        
        return {
            'simulated': simulated,
            'real': real,
            'error_rate': error_rate,
            'tolerance': tolerance,
            'is_accurate': is_accurate,
            'deviation': simulated - real,
            'status': 'PASS' if is_accurate else 'FAIL',
            'note': f'Day {day_index + 1} demand validation'
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
            'success_rate': (status_counts['EXCELLENT'] + status_counts['GOOD']) / total_days if total_days > 0 else 0
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
            if var_data.get('status') == 'INEXACTA':
                critical_vars.append({
                    'variable': var_data['description'],
                    'error': var_data.get('error_pct', 0)
                })
        
        if critical_vars:
            # Ordenar por error descendente
            critical_vars.sort(key=lambda x: x['error'], reverse=True)
            
            # Tomar las 3 peores
            worst_vars = critical_vars[:3]
            var_list = ', '.join([f"{v['variable']} ({v['error']:.1f}% error)" for v in worst_vars])
            
            recommendations.append({
                'type': 'error',
                'message': f'Variables críticas que requieren revisión: {var_list}',
                'priority': 'high'
            })
        
        # Recomendaciones por tipo
        for var_type, type_data in by_type_summary.items():
            if type_data['total'] > 0:
                type_success_rate = (type_data['precise'] / type_data['total']) * 100
                
                if type_success_rate < 50:
                    recommendations.append({
                        'type': 'warning',
                        'message': f'Las variables de tipo "{var_type}" muestran baja precisión ({type_success_rate:.1f}%). Considere revisar las ecuaciones relacionadas.',
                        'priority': 'medium'
                    })
        
        # Recomendaciones sobre datos faltantes
        no_data_count = sum(1 for v in by_variable.values() if v.get('status') == 'NO_DATA')
        if no_data_count > 0:
            recommendations.append({
                'type': 'info',
                'message': f'{no_data_count} variables no pudieron ser validadas por falta de datos simulados. Verifique las ecuaciones del modelo.',
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
                'success_rate': 0
            },
            'recommendations': ["No se encontraron resultados para validar"],
            'is_valid': False,
            'real_values': {}
        }
    
    def compare_simulations(self, 
                          simulation_ids: List[int],
                          variables: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Compare multiple simulations to identify best performing parameters.
        
        Args:
            simulation_ids: List of simulation IDs to compare
            variables: Optional list of variables to focus on
            
        Returns:
            Comparison results and recommendations
        """
        if not simulation_ids:
            return {'error': 'No simulations to compare'}
        
        comparison_data = []
        
        for sim_id in simulation_ids:
            validation = self.validate_simulation(sim_id)
            
            if validation['is_valid']:
                comparison_data.append({
                    'simulation_id': sim_id,
                    'overall_accuracy': validation['summary']['overall_accuracy'],
                    'success_rate': validation['summary']['success_rate'],
                    'variable_performance': validation['summary']['variable_performance']
                })
        
        if not comparison_data:
            return {'error': 'No valid simulations found'}
        
        # Find best performing simulation
        best_sim = max(comparison_data, key=lambda x: x['overall_accuracy'])
        
        # Identify best practices
        best_practices = self._identify_best_practices(comparison_data, variables)
        
        return {
            'best_simulation': best_sim,
            'all_comparisons': comparison_data,
            'best_practices': best_practices,
            'recommendation': f"Simulation {best_sim['simulation_id']} shows best overall performance"
        }
    
    def _identify_best_practices(self, 
                               comparison_data: List[Dict],
                               focus_variables: Optional[List[str]] = None) -> Dict[str, Any]:
        """Identify best practices from multiple simulations"""
        best_practices = {}
        
        # Get all variables
        all_variables = set()
        for comp in comparison_data:
            all_variables.update(comp['variable_performance'].keys())
        
        # Filter if specific variables requested
        if focus_variables:
            all_variables = all_variables.intersection(set(focus_variables))
        
        # Find best performer for each variable
        for var in all_variables:
            best_accuracy = 0
            best_sim_id = None
            
            for comp in comparison_data:
                var_perf = comp['variable_performance'].get(var, {})
                accuracy = var_perf.get('accuracy_rate', 0)
                
                if accuracy > best_accuracy:
                    best_accuracy = accuracy
                    best_sim_id = comp['simulation_id']
            
            if best_sim_id:
                best_practices[var] = {
                    'best_simulation': best_sim_id,
                    'accuracy': best_accuracy
                }
        
        return best_practices