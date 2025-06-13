# views/simulate_result_view.py
from typing import List
from ..services.validation_service import SimulationValidationService
import numpy as np
from django.views.generic import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import View

from ..models import Simulation, ResultSimulation
from ..services.simulation_core import SimulationCore
from ..services.simulation_financial import SimulationFinancial
from ..utils.chart_utils import ChartGenerator
from finance.models import FinanceRecommendation, FinanceRecommendationSimulation

import json
import logging

logger = logging.getLogger(__name__)

class SimulateResultView(LoginRequiredMixin, View):
    """Display simulation results with complete analysis and visualization"""
    
    def get(self, request, simulation_id, *args, **kwargs):
        """Display simulation results with enhanced visualization"""
        try:
            # Get simulation with optimized queries
            simulation_instance = get_object_or_404(
                Simulation.objects.select_related(
                    'fk_questionary_result__fk_questionary__fk_product__fk_business',
                    'fk_fdp'
                ).prefetch_related(
                    'fk_questionary_result__fk_question_result_answer__fk_question'
                ),
                pk=simulation_id
            )
            
            # Check permissions
            if not self._user_can_view_simulation(request.user, simulation_instance):
                messages.error(request, "No tiene permisos para ver esta simulación.")
                return redirect('simulate:simulate.show')
            
            # Get results with pagination
            results_simulation = self._get_paginated_results(request, simulation_id)
            
            # Get historical demand data
            historical_demand = self._get_historical_demand(simulation_instance)
            
            # Generate comprehensive analysis
            context = self._prepare_complete_results_context(
                simulation_id, simulation_instance, results_simulation, historical_demand
            )
            
            return render(request, 'simulate/simulate-result.html', context)
            
        except Exception as e:
            logger.error(f"Error displaying results: {str(e)}")
            messages.error(request, "Error al mostrar los resultados.")
            return redirect('simulate:simulate.show')
    
    def _get_historical_demand(self, simulation_instance):
        """Extract historical demand data from questionary results"""
        try:
            # Get from simulation demand_history first
            if simulation_instance.demand_history:
                if isinstance(simulation_instance.demand_history, str):
                    try:
                        return json.loads(simulation_instance.demand_history)
                    except:
                        pass
                elif isinstance(simulation_instance.demand_history, list):
                    return simulation_instance.demand_history
            
            # Get from questionary answers
            for answer in simulation_instance.fk_questionary_result.fk_question_result_answer.all():
                if answer.fk_question.question == 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).':
                    if answer.answer:
                        try:
                            # Try JSON parse
                            return json.loads(answer.answer)
                        except:
                            # Try other parsing methods
                            demand_str = answer.answer.strip()
                            demand_str = demand_str.replace('[', '').replace(']', '')
                            if ',' in demand_str:
                                return [float(x.strip()) for x in demand_str.split(',') if x.strip()]
                            elif ' ' in demand_str:
                                return [float(x) for x in demand_str.split() if x]
                            elif '\n' in demand_str:
                                return [float(x.strip()) for x in demand_str.split('\n') if x.strip()]
            
            return []
        except Exception as e:
            logger.error(f"Error extracting historical demand: {str(e)}")
            return []
    
    def _prepare_complete_results_context(self, simulation_id, simulation_instance, 
                                    results_simulation, historical_demand):
        """Prepare comprehensive context data for results view"""
        # Generate all charts with historical comparison
        chart_generator = ChartGenerator()
        
        # Create enhanced chart data with historical demand
        chart_data = self._create_enhanced_chart_data(
            list(results_simulation), historical_demand
        )
        
        # Generate main analysis charts
        analysis_data = chart_generator.generate_all_charts(
            simulation_id, simulation_instance, list(results_simulation), historical_demand
        )
        
        # Log what charts were generated
        logger.info(f"Charts generated: {list(analysis_data.get('chart_images', {}).keys())}")
        
        # Generate comparison chart: Historical vs Simulated
        comparison_chart = None
        if historical_demand:
            comparison_chart = self.generate_demand_comparison_chart(
                historical_demand, list(results_simulation)
            )
            if comparison_chart:
                logger.info("Demand comparison chart generated successfully")
        
        # Get financial analysis and recommendations
        simulation_service = SimulationFinancial()
        financial_results = simulation_service.analyze_financial_results(
            simulation_id, analysis_data['totales_acumulativos']
        )
        
        # Generate dynamic recommendations based on results
        recommendations = self._generate_dynamic_recommendations(
            simulation_instance, analysis_data['totales_acumulativos'], 
            financial_results
        )
        
        # Calculate comprehensive statistics
        demand_stats = self._calculate_comprehensive_statistics(
            historical_demand, results_simulation
        )
        
        # Get related instances
        product_instance = simulation_instance.fk_questionary_result.fk_questionary.fk_product
        business_instance = product_instance.fk_business
        
        # Log accumulated totals for debugging
        logger.info(f"Accumulated totals variables: {list(analysis_data['totales_acumulativos'].keys())}")
        
        
        # Add validation results
        validation_service = SimulationValidationService()
        validation_results = validation_service.validate_simulation(simulation_id)
        
        # Add alerts to context
        if validation_results['alerts']:
            # Group alerts by type
            alerts_by_type = {}
            for alert in validation_results['alerts']:
                alert_type = alert['type']
                if alert_type not in alerts_by_type:
                    alerts_by_type[alert_type] = []
                alerts_by_type[alert_type].append(alert)
        
        # Prepare complete context
        context = {
            'simulation_instance': simulation_instance,
            'results_simulation': results_simulation,
            'results': results_simulation,
            'product_instance': product_instance,
            'business_instance': business_instance,
            'all_variables_extracted': analysis_data['all_variables_extracted'],
            'totales_acumulativos': analysis_data['totales_acumulativos'],
            'historical_demand': historical_demand,
            'demand_stats': demand_stats,
            'comparison_chart': comparison_chart,
            'financial_recommendations': recommendations,
            'financial_recommendations_to_show': recommendations,
            **analysis_data.get('chart_images', {}),  # Unpack all chart images
            **financial_results,
        }
        context['validation_alerts'] = alerts_by_type
        context['validation_summary'] = validation_results['summary']
        context['simulation_valid'] = validation_results['is_valid']
        
        # Calculate realistic statistics
        if historical_demand and results_simulation:
            comparison = self._calculate_realistic_comparison(historical_demand, results_simulation)
            context['realistic_comparison'] = comparison
        
        # Log final context keys for debugging
        chart_keys = [k for k in context.keys() if k.startswith('image_data')]
        logger.info(f"Chart keys in context: {chart_keys}")
        
        # Agregar validación del modelo
        validation_results = self._validate_model_predictions(
            simulation_instance, results_simulation, historical_demand
        )
        
        context.update({
            'validation_summary': validation_results['summary'],
            'validation_details': validation_results['details'],
            'validation_metrics': validation_results['metrics'],
            'validation_by_distribution': validation_results['by_distribution'],
            'validation_recommendations': validation_results['recommendations'],
            'validation_alerts': validation_results.get('alerts', {})
        })
        
        # **NUEVA VALIDACIÓN DE VARIABLES DEL MODELO**
        # Validar todas las variables del modelo contra valores reales
        model_validation_results = self._validate_model_variables(
            simulation_instance, results_simulation, analysis_data['all_variables_extracted']
        )
        
        # Agregar resultados de validación de variables al contexto
        context.update({
            'model_validation_summary': model_validation_results['summary'],
            'model_validation_by_variable': model_validation_results['by_variable'],
            'model_validation_daily_details': model_validation_results['daily_details'],
            'model_variables_valid': model_validation_results['summary']['is_valid']
        })
        
        # Log información sobre la validación de variables
        logger.info(f"Model validation completed: {model_validation_results['summary']['success_rate']:.1f}% success rate")
        logger.info(f"Variables validated: {model_validation_results['summary']['total_variables']} total, "
                f"{model_validation_results['summary']['precise_count']} precise, "
                f"{model_validation_results['summary']['acceptable_count']} acceptable, "
                f"{model_validation_results['summary']['inaccurate_count']} inaccurate")
        
        return context
    
    def _validate_model_variables(self, simulation_instance, results_simulation, all_variables_extracted):
        """Valida todas las variables del modelo (excepto demanda) contra valores reales"""
        
        # Variables a validar basadas en las que existen en el modelo
        variables_to_validate = {
            # Variables Financieras
            'IT': {'description': 'Ingresos Totales', 'unit': 'BS', 'type': 'Financiera', 'tolerance': 0.10},
            'GT': {'description': 'Ganancias Totales', 'unit': 'BS', 'type': 'Financiera', 'tolerance': 0.15},
            'GO': {'description': 'Gastos Operativos', 'unit': 'BS', 'type': 'Financiera', 'tolerance': 0.05},
            'GG': {'description': 'Gastos Generales', 'unit': 'BS', 'type': 'Financiera', 'tolerance': 0.05},
            'TG': {'description': 'Total Gastos', 'unit': 'BS', 'type': 'Financiera', 'tolerance': 0.05},
            'CTAI': {'description': 'Costo Total Adquisición Insumos', 'unit': 'BS', 'type': 'Costos', 'tolerance': 0.05},
            'CFD': {'description': 'Costo Fijo Diario', 'unit': 'BS', 'type': 'Costos', 'tolerance': 0.02},
            
            # Variables de Producción
            'TPV': {'description': 'Total Productos Vendidos', 'unit': 'L', 'type': 'Producción', 'tolerance': 0.10},
            'TPPRO': {'description': 'Total Productos Producidos', 'unit': 'L', 'type': 'Producción', 'tolerance': 0.05},
            'CPROD': {'description': 'Capacidad de Producción', 'unit': 'L', 'type': 'Producción', 'tolerance': 0.02},
            'QPL': {'description': 'Cantidad Producción Lote', 'unit': 'L', 'type': 'Producción', 'tolerance': 0.05},
            
            # Variables de Inventario
            'IPF': {'description': 'Inventario Productos Finales', 'unit': 'L', 'type': 'Inventario', 'tolerance': 0.15},
            'SI': {'description': 'Stock de Seguridad', 'unit': 'L', 'type': 'Inventario', 'tolerance': 0.10},
            'CIP': {'description': 'Capacidad Inventario Productos', 'unit': 'L', 'type': 'Inventario', 'tolerance': 0.02},
            
            # Variables de RRHH
            'PE': {'description': 'Productividad Empleados', 'unit': 'L/Empleado', 'type': 'RRHH', 'tolerance': 0.10},
            'NEPP': {'description': 'Número de Empleados', 'unit': 'Empleados', 'type': 'RRHH', 'tolerance': 0.01},
            'SE': {'description': 'Sueldos Empleados', 'unit': 'BS', 'type': 'RRHH', 'tolerance': 0.02},
            
            # Variables de Clientes
            'CPD': {'description': 'Clientes Por Día', 'unit': 'Clientes', 'type': 'Ventas', 'tolerance': 0.10},
            'VPC': {'description': 'Ventas Por Cliente', 'unit': 'L/Cliente', 'type': 'Ventas', 'tolerance': 0.10},
            'TCAE': {'description': 'Total Clientes Atendidos Efectivamente', 'unit': 'Clientes', 'type': 'Ventas', 'tolerance': 0.10},
            
            # Variables de Precios
            'PVP': {'description': 'Precio de Venta del Producto', 'unit': 'BS/L', 'type': 'Precios', 'tolerance': 0.05},
            'PC': {'description': 'Precio Competencia', 'unit': 'BS/L', 'type': 'Precios', 'tolerance': 0.05},
            'CUIP': {'description': 'Costo Unitario Insumo Principal', 'unit': 'BS/L', 'type': 'Costos', 'tolerance': 0.05},
        }
        
        # Obtener valores reales del cuestionario
        real_values = self._extract_real_values_from_questionnaire(simulation_instance)
        
        if not real_values:
            logger.warning("No real values found in questionnaire")
            return {
                'summary': {
                    'total_variables': 0,
                    'precise_count': 0,
                    'acceptable_count': 0,
                    'inaccurate_count': 0,
                    'success_rate': 0,
                    'is_valid': False
                },
                'by_variable': {},
                'daily_details': []
            }
        
        # Validar cada variable
        by_variable = {}
        daily_details = []
        total_variables = 0
        precise_count = 0
        acceptable_count = 0
        inaccurate_count = 0
        
        for var_key, var_info in variables_to_validate.items():
            if var_key not in real_values:
                continue
                
            total_variables += 1
            real_value = float(real_values[var_key])
            
            # Inicializar variables para esta iteración
            simulated_values = []
            daily_details_by_day = {}
            
            # Recolectar valores simulados para todos los días
            day_counter = 1
            for result in results_simulation:
                # Extract values for each day
                simulated_value = None
                
                # Try to get simulated value - intentar diferentes formas
                try:
                    # Primero intentar con el nombre exacto
                    if hasattr(result, var_key):
                        simulated_value = getattr(result, var_key)
                    # Intentar con minúsculas
                    elif hasattr(result, var_key.lower()):
                        simulated_value = getattr(result, var_key.lower())
                    # Intentar con un diccionario de variables si existe
                    elif hasattr(result, 'variables') and result.variables:
                        simulated_value = result.variables.get(var_key)
                    # Intentar acceder como diccionario si el objeto lo permite
                    elif hasattr(result, '__getitem__'):
                        try:
                            simulated_value = result[var_key]
                        except (KeyError, TypeError):
                            pass
                    # Intentar con all_variables_extracted si está disponible
                    elif all_variables_extracted and var_key in all_variables_extracted:
                        # Si all_variables_extracted es una lista de diccionarios por día
                        if isinstance(all_variables_extracted[var_key], list) and len(all_variables_extracted[var_key]) > day_counter - 1:
                            simulated_value = all_variables_extracted[var_key][day_counter - 1]
                        # Si es un valor único
                        elif not isinstance(all_variables_extracted[var_key], list):
                            simulated_value = all_variables_extracted[var_key]
                            
                except (AttributeError, TypeError, IndexError) as e:
                    logger.debug(f"Could not extract {var_key} for day {day_counter}: {e}")
                    continue
                
                if simulated_value is not None:
                    try:
                        simulated_value = float(simulated_value)
                        simulated_values.append(simulated_value)
                        
                        # Calculate daily error
                        if real_value > 0:
                            error_pct = abs(simulated_value - real_value) / real_value * 100
                        else:
                            error_pct = abs(simulated_value) * 100  # Error absoluto si real_value es 0
                            
                        daily_details_by_day[day_counter] = {
                            'day': day_counter,
                            'simulated': simulated_value,
                            'real': real_value,
                            'error_pct': error_pct,
                            'is_acceptable': error_pct <= var_info['tolerance'] * 100
                        }
                    except (ValueError, TypeError):
                        logger.debug(f"Could not convert {var_key} value to float: {simulated_value}")
                        
                day_counter += 1
            
            # Skip if no simulated values found
            if not simulated_values:
                by_variable[var_key] = {
                    'description': var_info['description'],
                    'unit': var_info['unit'],
                    'type': var_info['type'],
                    'real_value': real_value,
                    'status': 'NO_DATA',
                    'error': 'No simulated values found'
                }
                inaccurate_count += 1  # Contar como inexacta si no hay datos
                continue
            
            # Calculate average values and error
            avg_simulated = sum(simulated_values) / len(simulated_values)  # Usar sum() en lugar de np.mean()
            
            if real_value > 0:
                error_pct = abs(avg_simulated - real_value) / real_value * 100
            else:
                error_pct = abs(avg_simulated) * 100
            
            # Determine validation status
            tolerance = var_info['tolerance'] * 100
            if error_pct <= tolerance:
                status = 'PRECISA'
                precise_count += 1
            elif error_pct <= tolerance * 2:
                status = 'ACEPTABLE'
                acceptable_count += 1
            else:
                status = 'INEXACTA'
                inaccurate_count += 1
            
            # Add to variables summary
            by_variable[var_key] = {
                'description': var_info['description'],
                'unit': var_info['unit'],
                'type': var_info['type'],
                'real_value': real_value,
                'simulated_avg': avg_simulated,
                'simulated_values_count': len(simulated_values),
                'error_pct': error_pct,
                'status': status,
                'tolerance': tolerance,
                'daily_details': daily_details_by_day
            }
            
            # Add to daily details
            for details in daily_details_by_day.values():
                daily_details.append({
                    'variable': var_key,
                    'description': var_info['description'],
                    'type': var_info['type'],
                    **details
                })
        
        # Calculate success rate
        success_rate = (precise_count / total_variables * 100) if total_variables > 0 else 0
        
        logger.info(f"Model variables validation completed: {total_variables} variables processed")
        logger.info(f"Results: {precise_count} precise, {acceptable_count} acceptable, {inaccurate_count} inaccurate")
        
        return {
            'summary': {
                'total_variables': total_variables,
                'precise_count': precise_count,
                'acceptable_count': acceptable_count,
                'inaccurate_count': inaccurate_count,
                'success_rate': success_rate,
                'is_valid': success_rate >= 70
            },
            'by_variable': by_variable,
            'daily_details': daily_details
        }
        """Valida todas las variables del modelo (excepto demanda) contra valores reales"""
        
        # Variables a validar basadas en las que existen en el modelo
        variables_to_validate = {
            # Variables Financieras
            'IT': {'description': 'Ingresos Totales', 'unit': 'BS', 'type': 'Financiera', 'tolerance': 0.10},
            'GT': {'description': 'Ganancias Totales', 'unit': 'BS', 'type': 'Financiera', 'tolerance': 0.15},
            'GO': {'description': 'Gastos Operativos', 'unit': 'BS', 'type': 'Financiera', 'tolerance': 0.05},
            'GG': {'description': 'Gastos Generales', 'unit': 'BS', 'type': 'Financiera', 'tolerance': 0.05},
            'TG': {'description': 'Total Gastos', 'unit': 'BS', 'type': 'Financiera', 'tolerance': 0.05},
            'CTAI': {'description': 'Costo Total Adquisición Insumos', 'unit': 'BS', 'type': 'Costos', 'tolerance': 0.05},
            'CFD': {'description': 'Costo Fijo Diario', 'unit': 'BS', 'type': 'Costos', 'tolerance': 0.02},
            
            # Variables de Producción
            'TPV': {'description': 'Total Productos Vendidos', 'unit': 'L', 'type': 'Producción', 'tolerance': 0.10},
            'TPPRO': {'description': 'Total Productos Producidos', 'unit': 'L', 'type': 'Producción', 'tolerance': 0.05},
            'CPROD': {'description': 'Capacidad de Producción', 'unit': 'L', 'type': 'Producción', 'tolerance': 0.02},
            'QPL': {'description': 'Cantidad Producción Lote', 'unit': 'L', 'type': 'Producción', 'tolerance': 0.05},
            
            # Variables de Inventario
            'IPF': {'description': 'Inventario Productos Finales', 'unit': 'L', 'type': 'Inventario', 'tolerance': 0.15},
            'SI': {'description': 'Stock de Seguridad', 'unit': 'L', 'type': 'Inventario', 'tolerance': 0.10},
            'CIP': {'description': 'Capacidad Inventario Productos', 'unit': 'L', 'type': 'Inventario', 'tolerance': 0.02},
            
            # Variables de RRHH
            'PE': {'description': 'Productividad Empleados', 'unit': 'L/Empleado', 'type': 'RRHH', 'tolerance': 0.10},
            'NEPP': {'description': 'Número de Empleados', 'unit': 'Empleados', 'type': 'RRHH', 'tolerance': 0.01},
            'SE': {'description': 'Sueldos Empleados', 'unit': 'BS', 'type': 'RRHH', 'tolerance': 0.02},
            
            # Variables de Clientes
            'CPD': {'description': 'Clientes Por Día', 'unit': 'Clientes', 'type': 'Ventas', 'tolerance': 0.10},
            'VPC': {'description': 'Ventas Por Cliente', 'unit': 'L/Cliente', 'type': 'Ventas', 'tolerance': 0.10},
            'TCAE': {'description': 'Total Clientes Atendidos Efectivamente', 'unit': 'Clientes', 'type': 'Ventas', 'tolerance': 0.10},
            
            # Variables de Precios
            'PVP': {'description': 'Precio de Venta del Producto', 'unit': 'BS/L', 'type': 'Precios', 'tolerance': 0.05},
            'PC': {'description': 'Precio Competencia', 'unit': 'BS/L', 'type': 'Precios', 'tolerance': 0.05},
            'CUIP': {'description': 'Costo Unitario Insumo Principal', 'unit': 'BS/L', 'type': 'Costos', 'tolerance': 0.05},
        }
        
        # Obtener valores reales del cuestionario
        real_values = self._extract_real_values_from_questionnaire(simulation_instance)
        
        # Validar cada variable
        by_variable = {}
        daily_details = []
        total_variables = 0
        precise_count = 0
        acceptable_count = 0
        inaccurate_count = 0
        
        for var_key, var_info in variables_to_validate.items():
            if var_key not in real_values:
                continue
                
            total_variables += 1
            real_value = float(real_values[var_key])
            
            # Recolectar valores simulados para todos los días
            simulated_values = []
            daily_details_by_day = {}
            
        for result in results_simulation:
            # Extract values for each day
            simulated_value = None
            
            # Try to get simulated value
            try:
                if hasattr(result, var_key.lower()):
                    simulated_value = getattr(result, var_key.lower())
                elif hasattr(result, var_key):
                    simulated_value = getattr(result, var_key)
                elif hasattr(result, 'variables'):
                    simulated_value = result.variables.get(var_key)
            except AttributeError:
                continue
            
            if simulated_value is not None:
                simulated_values.append(float(simulated_value))
                
                # Calculate daily error
                if real_value > 0:
                    error_pct = abs(simulated_value - real_value) / real_value * 100
                    daily_details_by_day[len(simulated_values)] = {
                        'day': len(simulated_values),
                        'simulated': simulated_value,
                        'real': real_value,
                        'error_pct': error_pct,
                        'is_acceptable': error_pct <= var_info['tolerance'] * 100
                    }
        
        # Skip if no simulated values found
        if not simulated_values:
            by_variable[var_key] = {
                'description': var_info['description'],
                'unit': var_info['unit'],
                'type': var_info['type'],
                'status': 'NO_DATA',
                'error': 'No simulated values found'
            }
            return by_variable[var_key]
        
        # Calculate average values and error
        avg_simulated = np.mean(simulated_values)
        error_pct = abs(avg_simulated - real_value) / real_value * 100 if real_value > 0 else 0
        
        # Determine validation status
        tolerance = var_info['tolerance'] * 100
        if error_pct <= tolerance:
            status = 'PRECISA'
            precise_count += 1
        elif error_pct <= tolerance * 2:
            status = 'ACEPTABLE'
            acceptable_count += 1
        else:
            status = 'INEXACTA'
            inaccurate_count += 1
        
        # Add to variables summary
        by_variable[var_key] = {
            'description': var_info['description'],
            'unit': var_info['unit'],
            'type': var_info['type'],
            'real_value': real_value,
            'simulated_avg': avg_simulated,
            'error_pct': error_pct,
            'status': status,
            'tolerance': tolerance,
            'daily_details': daily_details_by_day
        }
        
        # Add to daily details
        daily_details.extend([
            {
                'variable': var_key,
                'description': var_info['description'],
                'type': var_info['type'],
                **details
            } for details in daily_details_by_day.values()
        ])
        
        success_rate = (precise_count / total_variables * 100) if total_variables > 0 else 0
        
        return {
            'summary': {
                'total_variables': total_variables,
                'precise_count': precise_count,
                'acceptable_count': acceptable_count,
                'inaccurate_count': inaccurate_count,
                'success_rate': success_rate,
                'is_valid': success_rate >= 70
            },
            'by_variable': by_variable,
            'daily_details': daily_details
        }
     
    def _extract_real_values_from_questionnaire(self, simulation_instance):
        """
        Extrae los valores reales del cuestionario asociado a la simulación
        para comparar con los valores simulados
        
        Args:
            simulation_instance: Instancia de la simulación
            
        Returns:
            dict: Diccionario con los valores reales extraídos del cuestionario
        """
        real_values = {}
        
        try:
            # Obtener el resultado del cuestionario
            questionary_result = simulation_instance.fk_questionary_result
            if not questionary_result:
                logger.warning("No questionary result found for simulation")
                return real_values
            
            # Obtener las respuestas del cuestionario
            questionary_answers = questionary_result.questionary_answers.all()
            
            # Mapeo de preguntas del cuestionario a variables del modelo
            question_to_variable_mapping = {
                # Variables Financieras
                'ingresos_totales_mensuales': 'IT',
                'ganancias_totales_mensuales': 'GT',
                'gastos_operativos_mensuales': 'GO',
                'gastos_generales_mensuales': 'GG',
                'total_gastos_mensuales': 'TG',
                'costo_total_insumos_mensuales': 'CTAI',
                'costos_fijos_diarios': 'CFD',
                
                # Variables de Producción
                'productos_vendidos_diarios': 'TPV',
                'productos_producidos_diarios': 'TPPRO',
                'capacidad_produccion_diaria': 'CPROD',
                'cantidad_lote_produccion': 'QPL',
                
                # Variables de Inventario
                'inventario_productos_finales': 'IPF',
                'stock_seguridad': 'SI',
                'capacidad_inventario_productos': 'CIP',
                
                # Variables de RRHH
                'productividad_empleados': 'PE',
                'numero_empleados': 'NEPP',
                'sueldos_empleados_mensuales': 'SE',
                
                # Variables de Clientes/Ventas
                'clientes_por_dia': 'CPD',
                'ventas_por_cliente': 'VPC',
                'clientes_atendidos_diarios': 'TCAE',
                
                # Variables de Precios
                'precio_venta_producto': 'PVP',
                'precio_competencia': 'PC',
                'costo_unitario_insumo_principal': 'CUIP',
            }
            
            # Extraer valores de las respuestas
            for answer in questionary_answers:
                question_key = answer.fk_question.key if hasattr(answer.fk_question, 'key') else None
                question_text = answer.fk_question.question_text.lower().replace(' ', '_') if hasattr(answer.fk_question, 'question_text') else None
                
                # Intentar mapear por clave de pregunta
                if question_key and question_key in question_to_variable_mapping:
                    variable_key = question_to_variable_mapping[question_key]
                    real_values[variable_key] = self._parse_numeric_value(answer.answer_value)
                    continue
                
                # Intentar mapear por texto de pregunta
                if question_text:
                    for question_pattern, variable_key in question_to_variable_mapping.items():
                        if question_pattern in question_text:
                            real_values[variable_key] = self._parse_numeric_value(answer.answer_value)
                            break
            
            # Valores calculados o derivados si no están directamente en el cuestionario
            real_values = self._calculate_derived_values(real_values, questionary_answers)
            
            # Log de valores extraídos
            logger.info(f"Real values extracted from questionnaire: {len(real_values)} variables")
            logger.debug(f"Real values: {real_values}")
            
            return real_values
            
        except Exception as e:
            logger.error(f"Error extracting real values from questionnaire: {str(e)}")
            return real_values

    def _parse_numeric_value(self, value):
        """
        Convierte un valor de respuesta a numérico
        
        Args:
            value: Valor a convertir
            
        Returns:
            float: Valor numérico o 0 si no se puede convertir
        """
        if value is None:
            return 0.0
        
        try:
            # Si ya es numérico
            if isinstance(value, (int, float)):
                return float(value)
            
            # Si es string, limpiar y convertir
            if isinstance(value, str):
                # Remover caracteres no numéricos excepto punto y coma
                clean_value = ''.join(c for c in value if c.isdigit() or c in ['.', ','])
                
                # Reemplazar coma por punto si es necesario
                clean_value = clean_value.replace(',', '.')
                
                if clean_value:
                    return float(clean_value)
            
            return 0.0
            
        except (ValueError, TypeError):
            logger.warning(f"Could not parse numeric value: {value}")
            return 0.0

    def _calculate_derived_values(self, real_values, questionary_answers):
        """
        Calcula valores derivados que no están directamente en el cuestionario
        pero pueden ser calculados a partir de otros valores
        
        Args:
            real_values: Diccionario de valores reales extraídos
            questionary_answers: Respuestas del cuestionario
            
        Returns:
            dict: Diccionario actualizado con valores derivados
        """
        try:
            # Calcular Total Gastos si no existe pero tenemos componentes
            if 'TG' not in real_values and ('GO' in real_values or 'GG' in real_values):
                go = real_values.get('GO', 0)
                gg = real_values.get('GG', 0)
                se = real_values.get('SE', 0)
                real_values['TG'] = go + gg + se
            
            # Calcular Ganancias Totales si tenemos ingresos y gastos
            if 'GT' not in real_values and 'IT' in real_values and 'TG' in real_values:
                real_values['GT'] = real_values['IT'] - real_values['TG']
            
            # Calcular Total Clientes Atendidos si no existe pero tenemos clientes por día
            if 'TCAE' not in real_values and 'CPD' in real_values:
                real_values['TCAE'] = real_values['CPD']  # Asumiendo que todos los clientes son atendidos
            
            # Calcular Productos Vendidos si tenemos clientes y ventas por cliente
            if 'TPV' not in real_values and 'CPD' in real_values and 'VPC' in real_values:
                real_values['TPV'] = real_values['CPD'] * real_values['VPC']
            
            # Calcular Productos Producidos si no existe pero tenemos vendidos
            if 'TPPRO' not in real_values and 'TPV' in real_values:
                # Asumiendo que se produce lo que se vende más un buffer
                real_values['TPPRO'] = real_values['TPV'] * 1.1  # 10% buffer
            
            # Convertir valores mensuales a diarios donde sea necesario
            monthly_to_daily_variables = ['IT', 'GT', 'GO', 'GG', 'TG', 'CTAI', 'SE']
            for var in monthly_to_daily_variables:
                if var in real_values:
                    real_values[var] = real_values[var] / 30  # Convertir mensual a diario
            
            logger.info(f"Derived values calculated. Total variables: {len(real_values)}")
            
            return real_values
            
        except Exception as e:
            logger.error(f"Error calculating derived values: {str(e)}")
            return real_values
    
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
      
    def _calculate_realistic_comparison(self, historical_demand, results_simulation):
        """Calculate realistic comparison metrics"""
        hist_mean = np.mean(historical_demand)
        hist_std = np.std(historical_demand)
        
        sim_demands = [float(r.demand_mean) for r in results_simulation]
        sim_mean = np.mean(sim_demands)
        sim_std = np.std(sim_demands)
        
        # Calculate realistic growth
        growth_rate = ((sim_mean - hist_mean) / hist_mean * 100) if hist_mean > 0 else 0
        
        # Flag if growth seems unrealistic
        is_realistic = abs(growth_rate) < 50  # Less than 50% change
        
        return {
            'historical_mean': hist_mean,
            'simulated_mean': sim_mean,
            'growth_rate': growth_rate,
            'is_realistic': is_realistic,
            'deviation_percentage': abs(growth_rate),
            'recommendation': self._get_growth_recommendation(growth_rate, is_realistic)
        }
    
    def _create_enhanced_chart_data(self, results_simulation, historical_demand):
        """Create enhanced chart data including historical demand"""
        chart_data = {
            'historical_demand': historical_demand,
            'labels': list(range(1, len(results_simulation) + 1)),
            'datasets': [
                {
                    'label': 'Demanda Simulada',
                    'values': [float(r.demand_mean) for r in results_simulation]
                }
            ],
            'x_label': 'Días',
            'y_label': 'Demanda (Litros)'
        }
        
        return chart_data
    
    def _get_growth_recommendation(self, growth_rate, is_realistic):
        """Get recommendation based on growth rate"""
        if not is_realistic:
            if growth_rate > 50:
                return "La predicción parece sobreestimar la demanda. Revise los parámetros del modelo."
            else:
                return "La predicción muestra una caída drástica. Verifique los datos de entrada."
        else:
            if growth_rate > 20:
                return "Crecimiento optimista pero realista. Prepare capacidad adicional."
            elif growth_rate > 0:
                return "Crecimiento moderado esperado. Mantenga niveles actuales."
            elif growth_rate > -10:
                return "Ligera contracción esperada. Optimice costos operativos."
            else:
                return "Contracción significativa. Implemente estrategias de retención."
    
    def generate_demand_comparison_chart(self, historical_demand: List[float], 
                                       results_simulation: List) -> str:
        """Generate comparison chart between historical and simulated demand"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), 
                                          gridspec_kw={'height_ratios': [3, 1]})
            
            # Main comparison plot
            if historical_demand and len(historical_demand) > 0:
                # Historical demand
                hist_periods = list(range(1, len(historical_demand) + 1))
                ax1.plot(hist_periods, historical_demand, 'b-', marker='s', 
                        markersize=5, linewidth=2, label='Demanda Histórica', 
                        alpha=0.8)
                
                # Historical statistics
                hist_mean = np.mean(historical_demand)
                hist_std = np.std(historical_demand)
                ax1.axhline(y=hist_mean, color='blue', linestyle=':', alpha=0.5,
                          label=f'Media Histórica: {hist_mean:.2f}')
                
                # Historical confidence interval
                ax1.fill_between(hist_periods, 
                               hist_mean - hist_std, 
                               hist_mean + hist_std,
                               alpha=0.1, color='blue')
            
            # Simulated demand
            simulated_values = [float(r.demand_mean) for r in results_simulation]
            sim_start = len(historical_demand) + 1 if historical_demand else 1
            sim_periods = list(range(sim_start, sim_start + len(simulated_values)))
            
            ax1.plot(sim_periods, simulated_values, 'r-', marker='o',
                    markersize=5, linewidth=2, label='Demanda Simulada',
                    alpha=0.8)
            
            # Simulated statistics
            sim_mean = np.mean(simulated_values)
            sim_std = np.std(simulated_values)
            ax1.axhline(y=sim_mean, color='red', linestyle=':', alpha=0.5,
                      label=f'Media Simulada: {sim_mean:.2f}')
            
            # Simulated confidence interval
            ax1.fill_between(sim_periods,
                           sim_mean - sim_std,
                           sim_mean + sim_std,
                           alpha=0.1, color='red')
            
            # Add transition line
            if historical_demand and len(historical_demand) > 0:
                ax1.axvline(x=len(historical_demand), color='gray', 
                          linestyle='--', alpha=0.5, label='Inicio Simulación')
                
                # Add trend lines
                if len(historical_demand) > 1:
                    z = np.polyfit(hist_periods, historical_demand, 1)
                    p = np.poly1d(z)
                    ax1.plot(hist_periods, p(hist_periods), 'b--', alpha=0.5,
                           label=f'Tendencia Histórica: {z[0]:.2f}')
                
                if len(simulated_values) > 1:
                    z = np.polyfit(range(len(simulated_values)), simulated_values, 1)
                    p = np.poly1d(z)
                    ax1.plot(sim_periods, p(range(len(simulated_values))), 'r--', 
                           alpha=0.5, label=f'Tendencia Simulada: {z[0]:.2f}')
            
            # Configure main plot
            ax1.set_xlabel('Período de Tiempo', fontsize=12)
            ax1.set_ylabel('Demanda (Litros)', fontsize=12)
            ax1.set_title('Comparación Completa: Demanda Histórica vs Simulada', 
                         fontsize=16, fontweight='bold', pad=20)
            ax1.legend(loc='upper left', bbox_to_anchor=(1, 1))
            ax1.grid(True, alpha=0.3)
            
            # Set x-axis limits
            total_periods = len(historical_demand) + len(simulated_values) if historical_demand else len(simulated_values)
            ax1.set_xlim(0, total_periods + 1)
            
            # Difference plot (bottom subplot)
            if historical_demand and len(historical_demand) > 0 and len(simulated_values) > 0:
                # Calculate percentage differences
                comparison_length = min(10, len(historical_demand), len(simulated_values))
                
                if comparison_length > 0:
                    hist_last_values = historical_demand[-comparison_length:]
                    sim_first_values = simulated_values[:comparison_length]
                    
                    periods_diff = list(range(1, comparison_length + 1))
                    differences = []
                    
                    for h, s in zip(hist_last_values, sim_first_values):
                        if h != 0:
                            diff = ((s - h) / h) * 100
                        else:
                            diff = 0
                        differences.append(diff)
                    
                    bars = ax2.bar(periods_diff, differences, alpha=0.7,
                                  color=['green' if d >= 0 else 'red' for d in differences])
                    
                    # Add value labels on bars
                    for bar, diff in zip(bars, differences):
                        height = bar.get_height()
                        ax2.text(bar.get_x() + bar.get_width()/2., height,
                               f'{diff:.1f}%', ha='center', 
                               va='bottom' if height >= 0 else 'top',
                               fontsize=8)
                    
                    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
                    ax2.set_xlabel('Período de Comparación')
                    ax2.set_ylabel('Diferencia (%)')
                    ax2.set_title('Diferencia Porcentual entre Últimos Valores Históricos y Primeros Simulados')
                    ax2.grid(True, alpha=0.3, axis='y')
            else:
                # If no comparison possible, show a message
                ax2.text(0.5, 0.5, 'No hay suficientes datos para comparación detallada', 
                        transform=ax2.transAxes, ha='center', va='center',
                        fontsize=12, color='gray')
                ax2.set_xticks([])
                ax2.set_yticks([])
            
            plt.tight_layout()
            
            # Convert to base64
            from io import BytesIO
            import base64
            
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
            buffer.close()
            plt.close(fig)
            
            return image_data
            
        except Exception as e:
            logger.error(f"Error generating demand comparison chart: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            if 'fig' in locals():
                plt.close(fig)
            return None
    
    def _calculate_comprehensive_statistics(self, historical_demand, results_simulation):
        """Calculate comprehensive statistics for analysis"""
        stats = {
            'historical': {},
            'simulated': {},
            'comparison': {},
            'forecast_accuracy': {}
        }
        
        # Historical statistics
        if historical_demand:
            historical_array = np.array(historical_demand)
            stats['historical'] = {
                'mean': np.mean(historical_array),
                'std': np.std(historical_array),
                'min': np.min(historical_array),
                'max': np.max(historical_array),
                'median': np.median(historical_array),
                'cv': np.std(historical_array) / np.mean(historical_array) if np.mean(historical_array) > 0 else 0,
                'trend': self._calculate_trend(historical_array)
            }
        
        # Simulated statistics
        try:
            simulated_values = [float(r.demand_mean) for r in results_simulation]
        except (AttributeError, ValueError, TypeError) as e:
            logger.error(f"Error extracting simulated values: {str(e)}")
            simulated_values = []
        
        if simulated_values:
            simulated_array = np.array(simulated_values)
            stats['simulated'] = {
                'mean': np.mean(simulated_array),
                'std': np.std(simulated_array),
                'min': np.min(simulated_array),
                'max': np.max(simulated_array),
                'median': np.median(simulated_array),
                'cv': np.std(simulated_array) / np.mean(simulated_array) if np.mean(simulated_array) > 0 else 0,
                'trend': self._calculate_trend(simulated_array)
            }
            
            # Comparison metrics
            if historical_demand and stats['historical']:
                stats['comparison'] = {
                    'mean_diff': stats['simulated']['mean'] - stats['historical']['mean'],
                    'mean_diff_pct': ((stats['simulated']['mean'] - stats['historical']['mean']) / 
                                    stats['historical']['mean'] * 100) if stats['historical']['mean'] > 0 else 0,
                    'std_diff': stats['simulated']['std'] - stats['historical']['std'],
                    'cv_diff': stats['simulated']['cv'] - stats['historical']['cv'],
                    'trend_change': stats['simulated']['trend'] - stats['historical']['trend']
                }
                
                # Forecast accuracy metrics
                try:
                    stats['forecast_accuracy'] = {
                        'mape': self._calculate_mape(historical_demand, simulated_values),
                        'rmse': self._calculate_rmse(historical_demand, simulated_values),
                        'mae': self._calculate_mae(historical_demand, simulated_values)
                    }
                except Exception as e:
                    logger.error(f"Error calculating forecast accuracy: {str(e)}")
                    stats['forecast_accuracy'] = {
                        'mape': 0,
                        'rmse': 0,
                        'mae': 0
                    }
        
        return stats
    
    def _calculate_trend(self, data):
        """Calculate trend slope"""
        try:
            data_array = np.array(data)
            if len(data_array) < 2:
                return 0
            x = np.arange(len(data_array))
            z = np.polyfit(x, data_array, 1)
            return float(z[0])
        except (ValueError, TypeError) as e:
            logger.error(f"Error calculating trend: {str(e)}")
            return 0
    
    def _calculate_mape(self, actual, predicted):
        """Calculate Mean Absolute Percentage Error"""
        if len(actual) == 0 or len(predicted) == 0:
            return 0
        
        # Convert to numpy arrays
        actual = np.array(actual)
        predicted = np.array(predicted)
        
        # Ensure same length
        n = min(len(actual), len(predicted))
        actual = actual[:n]
        predicted = predicted[:n]
        
        # Avoid division by zero
        mask = actual != 0
        if not np.any(mask):
            return 0
        
        return np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100
    
    def _calculate_rmse(self, actual, predicted):
        """Calculate Root Mean Square Error"""
        if len(actual) == 0 or len(predicted) == 0:
            return 0
        
        # Convert to numpy arrays
        actual = np.array(actual)
        predicted = np.array(predicted)
        
        # Ensure same length
        n = min(len(actual), len(predicted))
        actual = actual[:n]
        predicted = predicted[:n]
        
        return np.sqrt(np.mean((actual - predicted) ** 2))
    
    def _calculate_mae(self, actual, predicted):
        """Calculate Mean Absolute Error"""
        if len(actual) == 0 or len(predicted) == 0:
            return 0
        
        # Convert to numpy arrays
        actual = np.array(actual)
        predicted = np.array(predicted)
        
        # Ensure same length
        n = min(len(actual), len(predicted))
        actual = actual[:n]
        predicted = predicted[:n]
        
        return np.mean(np.abs(actual - predicted))
    def _generate_dynamic_recommendations(self, simulation_instance, 
                                    totales_acumulativos, financial_results):
        """Generate dynamic recommendations based on simulation results"""
        recommendations = []
        business = simulation_instance.fk_questionary_result.fk_questionary.fk_product.fk_business
        
        # Get finance recommendations from database
        db_recommendations = FinanceRecommendation.objects.filter(
            fk_business=business,
            is_active=True
        ).order_by('threshold_value')
        
        # Check each recommendation against results
        for rec in db_recommendations:
            if rec.variable_name in totales_acumulativos:
                value = totales_acumulativos[rec.variable_name]['total']
                threshold = float(rec.threshold_value) if rec.threshold_value else 0
                
                # Check if value exceeds threshold
                if threshold > 0 and value > threshold:
                    severity = ((value - threshold) / threshold * 100)
                    
                    recommendations.append({
                        'name': rec.name,
                        'description': rec.description or rec.recommendation,
                        'recommendation': rec.recommendation,
                        'severity': min(100, severity),
                        'value': value,
                        'threshold': threshold,
                        'variable': rec.variable_name,
                        'priority': 'high' if severity > 50 else 'medium' if severity > 20 else 'low',
                        'icon': self._get_recommendation_icon(rec.variable_name),
                        'color': self._get_recommendation_color(severity)
                    })
        
        # Add dynamic recommendations based on calculated metrics
        
        # 1. Efficiency Analysis
        if 'TOTAL PRODUCTOS VENDIDOS' in totales_acumulativos and 'TOTAL PRODUCTOS PRODUCIDOS' in totales_acumulativos:
            vendidos = totales_acumulativos['TOTAL PRODUCTOS VENDIDOS']['total']
            producidos = totales_acumulativos['TOTAL PRODUCTOS PRODUCIDOS']['total']
            if producidos > 0:
                efficiency = (vendidos / producidos) * 100
                if efficiency < 80:
                    recommendations.append({
                        'name': 'Eficiencia de Ventas Baja',
                        'description': f'Solo se está vendiendo el {efficiency:.1f}% de la producción',
                        'recommendation': 'Revisar estrategias de ventas y marketing. Considerar promociones o ajustar producción.',
                        'severity': 90 - efficiency,
                        'priority': 'high' if efficiency < 60 else 'medium',
                        'variable': 'EFICIENCIA_VENTAS',
                        'icon': 'bx-trending-down',
                        'color': 'danger' if efficiency < 60 else 'warning'
                    })
        
        # 2. Profitability Analysis
        if 'INGRESOS TOTALES' in totales_acumulativos and 'GASTOS TOTALES' in totales_acumulativos:
            ingresos = totales_acumulativos['INGRESOS TOTALES']['total']
            gastos = totales_acumulativos.get('GASTOS TOTALES', {}).get('total', 0) or totales_acumulativos.get('Total Gastos', {}).get('total', 0)
            
            if ingresos > 0:
                profit_margin = ((ingresos - gastos) / ingresos) * 100
                if profit_margin < 10:
                    recommendations.append({
                        'name': 'Margen de Ganancia Bajo',
                        'description': f'El margen de ganancia es solo {profit_margin:.1f}%',
                        'recommendation': 'Analizar estructura de costos y considerar optimizaciones o ajuste de precios.',
                        'severity': 80,
                        'priority': 'high',
                        'variable': 'MARGEN_GANANCIA',
                        'icon': 'bx-dollar-circle',
                        'color': 'danger'
                    })
                elif profit_margin > 40:
                    recommendations.append({
                        'name': 'Excelente Margen de Ganancia',
                        'description': f'El margen de ganancia es {profit_margin:.1f}%',
                        'recommendation': 'Mantener estrategia actual. Considerar expansión o inversión en crecimiento.',
                        'severity': 20,
                        'priority': 'low',
                        'variable': 'MARGEN_GANANCIA',
                        'icon': 'bx-trophy',
                        'color': 'success'
                    })
        
        # 3. Inventory Analysis
        if 'DEMANDA INSATISFECHA' in totales_acumulativos:
            demanda_insatisfecha = totales_acumulativos['DEMANDA INSATISFECHA']['total']
            if demanda_insatisfecha > 0:
                recommendations.append({
                    'name': 'Demanda Insatisfecha Detectada',
                    'description': f'Se dejó de atender {demanda_insatisfecha:.0f} unidades de demanda',
                    'recommendation': 'Aumentar capacidad de producción o mejorar gestión de inventarios.',
                    'severity': min(100, demanda_insatisfecha / 100),
                    'priority': 'high',
                    'variable': 'DEMANDA_INSATISFECHA',
                    'icon': 'bx-error-circle',
                    'color': 'danger'
                })
        
        # 4. Cost Structure Analysis
        if 'GASTOS OPERATIVOS' in totales_acumulativos and 'INGRESOS TOTALES' in totales_acumulativos:
            gastos_op = totales_acumulativos['GASTOS OPERATIVOS']['total']
            ingresos = totales_acumulativos['INGRESOS TOTALES']['total']
            if ingresos > 0:
                cost_ratio = (gastos_op / ingresos) * 100
                if cost_ratio > 70:
                    recommendations.append({
                        'name': 'Costos Operativos Elevados',
                        'description': f'Los costos operativos representan el {cost_ratio:.1f}% de los ingresos',
                        'recommendation': 'Revisar y optimizar procesos operativos. Buscar eficiencias en la cadena de suministro.',
                        'severity': cost_ratio,
                        'priority': 'high',
                        'variable': 'COSTOS_OPERATIVOS',
                        'icon': 'bx-receipt',
                        'color': 'warning'
                    })
        
        # 5. Growth Analysis
        if 'growth_rate' in financial_results:
            growth = financial_results['growth_rate']
            if growth < -5:
                recommendations.append({
                    'name': 'Tendencia Negativa en Demanda',
                    'description': f'La demanda muestra una caída del {abs(growth):.1f}%',
                    'recommendation': 'Implementar estrategias de retención y recuperación de clientes. Revisar competitividad.',
                    'severity': min(100, abs(growth) * 2),
                    'priority': 'high',
                    'variable': 'CRECIMIENTO',
                    'icon': 'bx-down-arrow-alt',
                    'color': 'danger'
                })
            elif growth > 20:
                recommendations.append({
                    'name': 'Crecimiento Acelerado',
                    'description': f'La demanda crece al {growth:.1f}%',
                    'recommendation': 'Preparar infraestructura para expansión. Asegurar capital de trabajo suficiente.',
                    'severity': 30,
                    'priority': 'medium',
                    'variable': 'CRECIMIENTO',
                    'icon': 'bx-up-arrow-alt',
                    'color': 'info'
                })
        
        # 6. ROI Analysis
        if 'Retorno Inversión' in totales_acumulativos:
            roi = totales_acumulativos['Retorno Inversión']['total']
            if roi < 1:
                recommendations.append({
                    'name': 'ROI Bajo',
                    'description': f'El retorno de inversión es {roi:.2f}',
                    'recommendation': 'Revisar estrategia de inversión y buscar oportunidades de mejora en eficiencia.',
                    'severity': 70,
                    'priority': 'medium',
                    'variable': 'ROI',
                    'icon': 'bx-line-chart-down',
                    'color': 'warning'
                })
        
        # Sort by priority and severity
        recommendations.sort(key=lambda x: (
            {'high': 0, 'medium': 1, 'low': 2}.get(x.get('priority', 'low'), 3),
            -x.get('severity', 0)
        ))
        
        # Save recommendations to database
        if recommendations:
            self._save_recommendations_to_db(simulation_instance, recommendations[:10])
        
        return recommendations[:10]  # Return top 10 recommendations
    
    def _get_recommendation_icon(self, variable_name):
        """Get appropriate icon for recommendation type"""
        icon_map = {
            'EFICIENCIA': 'bx-tachometer',
            'RENTABILIDAD': 'bx-dollar-circle',
            'RIESGO': 'bx-error-alt',
            'CRECIMIENTO': 'bx-trending-up',
            'COSTOS': 'bx-receipt',
            'INVENTARIO': 'bx-box',
            'VENTAS': 'bx-cart',
            'PRODUCCION': 'bx-factory'
        }
        
        for key, icon in icon_map.items():
            if key in variable_name.upper():
                return icon
        
        return 'bx-bulb'  # Default icon

    def _get_recommendation_color(self, severity):
        """Get color class based on severity"""
        if severity >= 70:
            return 'danger'
        elif severity >= 40:
            return 'warning'
        elif severity >= 20:
            return 'info'
        else:
            return 'success'
    
    def _save_recommendations_to_db(self, simulation_instance, recommendations):
        """Save generated recommendations to database"""
        try:
            finance_recs_to_save = []
            
            for rec in recommendations:
                if 'value' in rec and 'threshold' in rec:
                    # Find matching FinanceRecommendation
                    db_rec = FinanceRecommendation.objects.filter(
                        fk_business=simulation_instance.fk_questionary_result.fk_questionary.fk_product.fk_business,
                        variable_name=rec.get('variable', ''),
                        is_active=True
                    ).first()
                    
                    if db_rec:
                        finance_recs_to_save.append(
                            FinanceRecommendationSimulation(
                                data=rec['value'],
                                fk_simulation=simulation_instance,
                            )
                        )
            
            if finance_recs_to_save:
                FinanceRecommendationSimulation.objects.bulk_create(
                    finance_recs_to_save, ignore_conflicts=True
                )
        except Exception as e:
            logger.error(f"Error saving recommendations: {str(e)}")
    
    def _user_can_view_simulation(self, user, simulation_instance):
        """Check if user has permission to view simulation"""
        business = simulation_instance.fk_questionary_result.fk_questionary.fk_product.fk_business
        return business.fk_user == user
    
    def _get_paginated_results(self, request, simulation_id):
        """Get paginated simulation results"""
        page = request.GET.get('page', 1)
        per_page = 50
        
        results = ResultSimulation.objects.filter(
            is_active=True,
            fk_simulation_id=simulation_id
        ).order_by('date')
        
        paginator = Paginator(results, per_page)
        
        try:
            results_page = paginator.page(page)
        except PageNotAnInteger:
            results_page = paginator.page(1)
        except EmptyPage:
            results_page = paginator.page(paginator.num_pages)
        
        return results_page

def simulate_result_simulation_view(request, simulation_id):
    view = SimulateResultView.as_view()
    return view(request, simulation_id=simulation_id)