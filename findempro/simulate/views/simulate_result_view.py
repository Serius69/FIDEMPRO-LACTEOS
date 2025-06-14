# views/simulate_result_view.py
from typing import List

from questionary.models import Answer
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
        
        logger.info(f"all_variables_extracted type: {type(analysis_data.get('all_variables_extracted'))}")
        if analysis_data.get('all_variables_extracted'):
            first_item = analysis_data['all_variables_extracted'][0] if analysis_data['all_variables_extracted'] else None
            logger.info(f"First item structure: {first_item.keys() if isinstance(first_item, dict) else 'Not a dict'}")

        # Asegurar que el formato sea correcto antes de validar
        if not analysis_data.get('all_variables_extracted'):
            logger.warning("No extracted variables found for validation")
            
        # Continuar con la validación...
        model_validation_results = self._validate_model_variables(
            simulation_instance, results_simulation, analysis_data['all_variables_extracted']
        )
        
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
        
        # Agregar validación del modelo mejorada
        validation_results = self._validate_model_predictions(
            simulation_instance, results_simulation, historical_demand
        )

        # **NUEVA VALIDACIÓN DE VARIABLES DEL MODELO**
        model_validation_results = self._validate_model_variables(
            simulation_instance, results_simulation, analysis_data['all_variables_extracted']
        )

        # Agregar resultados al contexto
        context.update({            
            # Nuevos datos de validación de variables
            'model_validation_summary': model_validation_results['summary'],
            'model_validation_by_variable': model_validation_results['by_variable'],
            'model_validation_by_type': model_validation_results.get('by_type', {}),
            'model_validation_daily_details': model_validation_results['daily_details'],
            'model_validation_charts': model_validation_results.get('comparison_charts', {}),
            'model_validation_recommendations': model_validation_results.get('recommendations', []),
            'model_variables_valid': model_validation_results['summary']['is_valid']
        })
        
        
        return context
    
    def _validate_model_variables(self, simulation_instance, results_simulation, all_variables_extracted):
        """Valida todas las variables del modelo (excepto demanda) contra valores reales de la base de datos"""
        
        # Obtener TODAS las variables disponibles en el sistema desde la base de datos
        from variable.models import Variable
        
        # Cargar todas las variables del producto desde la base de datos
        product = simulation_instance.fk_questionary_result.fk_questionary.fk_product
        db_variables = Variable.objects.filter(
            fk_product=product,
            is_active=True
        ).values('initials', 'name', 'unit', 'type')
        
        # Crear diccionario dinámico de variables a validar
        variables_to_validate = {}
        for var in db_variables:
            # Excluir variables de demanda ya validadas
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
                continue
                
            total_variables += 1
            real_value = float(real_values[var_key])
            
            # Recolectar valores simulados para todos los días
            validation_result = self._validate_single_variable(
                var_key, var_info, real_value, results_simulation, all_variables_extracted
            )
            
            # Actualizar contadores según el resultado
            if validation_result['status'] == 'PRECISA':
                precise_count += 1
            elif validation_result['status'] == 'ACEPTABLE':
                acceptable_count += 1
            elif validation_result['status'] == 'INEXACTA':
                inaccurate_count += 1
            elif validation_result['status'] == 'NO_DATA':
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
        
        # Generar gráficos comparativos
        comparison_charts = self._generate_variable_comparison_charts(by_variable, real_values)
        
        # Calcular métricas agregadas
        success_rate = (precise_count / total_variables * 100) if total_variables > 0 else 0
        
        # Generar recomendaciones basadas en la validación
        validation_recommendations = self._generate_validation_recommendations(
            by_variable, success_rate, by_type_summary
        )
        
        logger.info(f"Model variables validation completed: {total_variables} variables processed")
        logger.info(f"Results: {precise_count} precise, {acceptable_count} acceptable, {inaccurate_count} inaccurate")
        
        return {
            'summary': {
                'total_variables': total_variables,
                'precise_count': precise_count,
                'acceptable_count': acceptable_count,
                'inaccurate_count': inaccurate_count,
                'success_rate': success_rate,
                'is_valid': success_rate >= 70,
                'validation_score': self._calculate_validation_score(precise_count, acceptable_count, total_variables)
            },
            'by_variable': by_variable,
            'by_type': by_type_summary,
            'daily_details': daily_details,
            'comparison_charts': comparison_charts,
            'recommendations': validation_recommendations
        }
    
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
    
    
    
    def _get_variable_type_name(self, type_code):
        """Convierte el código de tipo a nombre descriptivo"""
        type_names = {
            1: 'Exógena',
            2: 'Estado',
            3: 'Endógena'
        }
        return type_names.get(type_code, 'Otra')
    
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

    
    def _validate_single_variable(self, var_key, var_info, real_value, results_simulation, all_variables_extracted):
        """Valida una sola variable comparando valores simulados vs reales"""
        simulated_values = []
        daily_details_by_day = {}
        
        # Recolectar valores simulados de cada día
        for idx, result in enumerate(results_simulation):
            simulated_value = None
            
            try:
                # 1. Intentar obtener de variables directamente
                if hasattr(result, 'variables') and result.variables:
                    simulated_value = result.variables.get(var_key)
                    
                    # También buscar variantes del nombre
                    if simulated_value is None:
                        # Buscar con diferentes formatos
                        for key in result.variables.keys():
                            if key.upper() == var_key.upper():
                                simulated_value = result.variables[key]
                                break
                
                # 2. Intentar con el método get_variable_value
                if simulated_value is None and hasattr(result, 'get_variable_value'):
                    simulated_value = result.get_variable_value(var_key)
                
                # 3. Buscar en all_variables_extracted de forma más exhaustiva
                if simulated_value is None and all_variables_extracted and idx < len(all_variables_extracted):
                    day_data = all_variables_extracted[idx]
                    
                    if isinstance(day_data, dict):
                        # Buscar en totales_por_variable
                        if 'totales_por_variable' in day_data:
                            vars_dict = day_data['totales_por_variable']
                            
                            # Buscar por clave exacta
                            if var_key in vars_dict:
                                simulated_value = vars_dict[var_key].get('total')
                            else:
                                # Buscar por nombre de variable
                                for v_key, v_data in vars_dict.items():
                                    if v_key.upper() == var_key.upper():
                                        simulated_value = v_data.get('total')
                                        break
                        
                        # Buscar directamente en day_data
                        if simulated_value is None and var_key in day_data:
                            simulated_value = day_data[var_key]
                
            except Exception as e:
                logger.debug(f"Error extracting {var_key} for day {idx+1}: {e}")
                continue
            
            if simulated_value is not None:
                try:
                    simulated_value = float(simulated_value)
                    simulated_values.append(simulated_value)
                    
                    # Calcular error diario
                    if real_value > 0:
                        error_pct = abs(simulated_value - real_value) / real_value * 100
                    else:
                        error_pct = abs(simulated_value) * 100
                    
                    daily_details_by_day[idx + 1] = {
                        'day': idx + 1,
                        'simulated': simulated_value,
                        'real': real_value,
                        'difference': simulated_value - real_value,
                        'error_pct': error_pct,
                        'is_acceptable': error_pct <= var_info['tolerance'] * 100
                    }
                except (ValueError, TypeError):
                    logger.debug(f"Could not convert {var_key} value to float: {simulated_value}")
        
        # Log para debugging
        logger.debug(f"Variable {var_key}: found {len(simulated_values)} simulated values")
        
        # Si no hay valores simulados
        if not simulated_values:
            return {
                'description': var_info['description'],
                'unit': var_info['unit'],
                'type': var_info['type'],
                'real_value': real_value,
                'status': 'NO_DATA',
                'error': 'No se encontraron valores simulados',
                'simulated_values_count': 0
            }
        
        # Calcular estadísticas
        avg_simulated = sum(simulated_values) / len(simulated_values)
        min_simulated = min(simulated_values)
        max_simulated = max(simulated_values)
        std_simulated = self._calculate_std_dev(simulated_values)
        
        # Calcular error promedio
        if real_value > 0:
            error_pct = abs(avg_simulated - real_value) / real_value * 100
        else:
            error_pct = abs(avg_simulated) * 100
        
        # Determinar estado de validación
        tolerance = var_info['tolerance'] * 100
        if error_pct <= tolerance:
            status = 'PRECISA'
        elif error_pct <= tolerance * 2:
            status = 'ACEPTABLE'
        else:
            status = 'INEXACTA'
        
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
            'error_pct': error_pct,
            'status': status,
            'tolerance': tolerance,
            'daily_details': daily_details_by_day,
            'trend': self._calculate_trend(simulated_values)
        }
    
    def _generate_variable_comparison_charts(self, by_variable, real_values):
        """Genera gráficos comparativos para las variables validadas"""
        charts = {}
        
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            import base64
            from io import BytesIO
            
            # Gráfico 1: Comparación Real vs Simulado por Variable
            fig, ax = plt.subplots(figsize=(14, 8))
            
            variables = []
            real_vals = []
            sim_vals = []
            colors = []
            
            for var_key, var_data in by_variable.items():
                if var_data.get('status') != 'NO_DATA':
                    variables.append(var_data['description'][:20] + '...' if len(var_data['description']) > 20 else var_data['description'])
                    real_vals.append(var_data.get('real_value', 0))
                    sim_vals.append(var_data.get('simulated_avg', 0))
                    
                    # Color según estado
                    if var_data['status'] == 'PRECISA':
                        colors.append('green')
                    elif var_data['status'] == 'ACEPTABLE':
                        colors.append('orange')
                    else:
                        colors.append('red')
            
            if variables:
                x = range(len(variables))
                width = 0.35
                
                bars1 = ax.bar([i - width/2 for i in x], real_vals, width, 
                            label='Valor Real', alpha=0.8, color='steelblue')
                bars2 = ax.bar([i + width/2 for i in x], sim_vals, width,
                            label='Valor Simulado', alpha=0.8)
                
                # Colorear barras simuladas según precisión
                for bar, color in zip(bars2, colors):
                    bar.set_color(color)
                
                ax.set_xlabel('Variables', fontsize=12)
                ax.set_ylabel('Valor', fontsize=12)
                ax.set_title('Comparación de Variables: Real vs Simulado', fontsize=16, fontweight='bold')
                ax.set_xticks(x)
                ax.set_xticklabels(variables, rotation=45, ha='right')
                ax.legend()
                ax.grid(True, alpha=0.3, axis='y')
                
                plt.tight_layout()
                
                # Convertir a base64
                buffer = BytesIO()
                fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
                buffer.seek(0)
                charts['comparison_bar'] = base64.b64encode(buffer.getvalue()).decode('utf-8')
                plt.close(fig)
            
            # Gráfico 2: Distribución de Errores
            fig2, ax2 = plt.subplots(figsize=(10, 6))
            
            errors = []
            labels = []
            colors_pie = []
            
            precise = sum(1 for v in by_variable.values() if v.get('status') == 'PRECISA')
            acceptable = sum(1 for v in by_variable.values() if v.get('status') == 'ACEPTABLE')
            inaccurate = sum(1 for v in by_variable.values() if v.get('status') == 'INEXACTA')
            
            if precise > 0:
                errors.append(precise)
                labels.append(f'Precisas ({precise})')
                colors_pie.append('green')
            
            if acceptable > 0:
                errors.append(acceptable)
                labels.append(f'Aceptables ({acceptable})')
                colors_pie.append('orange')
            
            if inaccurate > 0:
                errors.append(inaccurate)
                labels.append(f'Inexactas ({inaccurate})')
                colors_pie.append('red')
            
            if errors:
                ax2.pie(errors, labels=labels, colors=colors_pie, autopct='%1.1f%%',
                    startangle=90, textprops={'fontsize': 12})
                ax2.set_title('Distribución de Precisión de Variables', fontsize=16, fontweight='bold')
                
                # Convertir a base64
                buffer2 = BytesIO()
                fig2.savefig(buffer2, format='png', dpi=100, bbox_inches='tight')
                buffer2.seek(0)
                charts['error_distribution'] = base64.b64encode(buffer2.getvalue()).decode('utf-8')
                plt.close(fig2)
            
        except Exception as e:
            logger.error(f"Error generating comparison charts: {str(e)}")
        
        return charts
    
    
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

    def _calculate_std_dev(self, values):
        """Calcula desviación estándar manualmente"""
        if len(values) < 2:
            return 0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5

    def _calculate_trend(self, values):
        """Calcula la tendencia de una serie de valores"""
        if len(values) < 2:
            return 'stable'
        
        # Calcular pendiente simple
        x = list(range(len(values)))
        n = len(values)
        
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(xi ** 2 for xi in x)
        
        if n * sum_x2 - sum_x ** 2 == 0:
            return 'stable'
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        
        if slope > 0.01:
            return 'increasing'
        elif slope < -0.01:
            return 'decreasing'
        else:
            return 'stable'

    def _create_empty_validation_result(self):
        """Crea un resultado de validación vacío"""
        return {
            'summary': {
                'total_variables': 0,
                'precise_count': 0,
                'acceptable_count': 0,
                'inaccurate_count': 0,
                'success_rate': 0,
                'is_valid': False,
                'validation_score': 0
            },
            'by_variable': {},
            'by_type': {},
            'daily_details': [],
            'comparison_charts': {},
            'recommendations': []
        }

    def _calculate_validation_score(self, precise, acceptable, total):
        """Calcula un score de validación ponderado"""
        if total == 0:
            return 0
        
        # Ponderaciones: preciso=100%, aceptable=50%, inexacto=0%
        score = (precise * 1.0 + acceptable * 0.5) / total * 100
        return round(score, 2)

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
    
    def _extract_real_values_from_questionnaire(self, simulation_instance):
        """
        Extrae los valores reales del cuestionario asociado a la simulación
        para comparar con los valores simulados
        """
        real_values = {}
        
        try:
            # Obtener el resultado del cuestionario
            questionary_result = simulation_instance.fk_questionary_result
            if not questionary_result:
                logger.warning("No questionary result found for simulation")
                return real_values
            
            # Obtener las respuestas del cuestionario con sus variables asociadas
            answers = questionary_result.fk_question_result_answer.select_related(
                'fk_question__fk_variable'
            ).all()
            
            logger.info(f"Found {answers.count()} answers in questionnaire")
            
            # Mapeo mejorado de preguntas a variables
            question_to_variable_mapping = {
                # Texto completo de pregunta -> variable
                'precio de venta del producto': 'PVP',
                'precio venta producto': 'PVP',
                'capacidad de producción diaria': 'CPROD',
                'capacidad producción': 'CPROD',
                'clientes por día': 'CPD',
                'clientes diarios': 'CPD',
                'número de empleados': 'NEPP',
                'empleados': 'NEPP',
                'costos fijos diarios': 'CFD',
                'costo fijo diario': 'CFD',
                'costo unitario del insumo': 'CUIP',
                'costo unitario insumo': 'CUIP',
                'inventario productos finales': 'IPF',
                'stock de seguridad': 'SI',
                'stock seguridad': 'SI',
                'sueldos empleados': 'SE',
                'salarios': 'SE',
                'precio competencia': 'PC',
                'gastos marketing': 'GMM',
                'marketing mensual': 'GMM',
            }
            
            # Procesar cada respuesta
            for answer in answers:
                try:
                    # Primero intentar con la variable directamente asociada
                    if answer.fk_question.fk_variable:
                        var_initials = answer.fk_question.fk_variable.initials
                        if var_initials and answer.answer:
                            value = self._parse_numeric_value(answer.answer)
                            if value is not None:
                                real_values[var_initials] = value
                                logger.debug(f"Extracted {var_initials} = {value} from variable association")
                    
                    # Luego intentar con mapeo de texto de pregunta
                    question_text = answer.fk_question.question.lower().strip()
                    
                    # Buscar coincidencias en el mapeo
                    for question_pattern, var_key in question_to_variable_mapping.items():
                        if question_pattern in question_text:
                            if var_key not in real_values and answer.answer:  # No sobrescribir
                                value = self._parse_numeric_value(answer.answer)
                                if value is not None:
                                    real_values[var_key] = value
                                    logger.debug(f"Extracted {var_key} = {value} from question text mapping")
                                    break
                    
                except Exception as e:
                    logger.error(f"Error processing answer {answer.id}: {str(e)}")
                    continue
            
            # Calcular valores derivados
            real_values = self._calculate_derived_values(real_values, answers)
            
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