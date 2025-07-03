# views/simulate_result_view.py
"""
Refactored simulation results view.
Focuses on daily comparisons and proper data visualization.
"""
import json
import logging
from typing import Dict, List, Any, Optional
import scipy.stats
from scipy import stats
from simulate.services.statistical_service import StatisticalService
from simulate.utils.chart_demand_utils import ChartDemand
import numpy as np
from django.views.generic import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from ..models import Simulation, ResultSimulation
from ..utils.simulation_math_utils import SimulationMathEngine
from ..services.validation_service import SimulationValidationService
from ..utils.simulation_financial_utils import SimulationFinancialAnalyzer
from ..utils.chart_utils import ChartGenerator
from ..utils.data_parsers_utils import DataParser
from questionary.models import Answer
from variable.models import Variable, Equation
from finance.models import FinanceRecommendation, FinanceRecommendationSimulation

logger = logging.getLogger(__name__)


class SimulateResultView(LoginRequiredMixin, View):
    """Enhanced view for displaying simulation results with daily analysis"""
    
    def __init__(self):
        super().__init__()
        self.validation_service = SimulationValidationService()
        self.statistical_service = StatisticalService()
        self.chart_demand = ChartDemand()
        self.financial_analyzer = SimulationFinancialAnalyzer()
        self.chart_generator = ChartGenerator()
        self.data_parser = DataParser()
        self.math_engine = SimulationMathEngine()
    
    def get(self, request, simulation_id, *args, **kwargs):
        """Display simulation results with enhanced visualization"""
        
        # Debug logging
        logger.info(f"GET request for simulation_id: {simulation_id} (type: {type(simulation_id)})")
        
        try:
            # Validate simulation_id
            if not isinstance(simulation_id, (int, str)):
                logger.error(f"Invalid simulation_id type: {type(simulation_id)}")
                messages.error(request, "ID de simulación inválido.")
                return redirect('simulate:simulate.show')
            
            # Convert to int if string
            try:
                simulation_id = int(simulation_id)
            except (ValueError, TypeError):
                logger.error(f"Cannot convert simulation_id to int: {simulation_id}")
                messages.error(request, "ID de simulación inválido.")
                return redirect('simulate:simulate.show')
            
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
            
            # Get results with pagination - FIXED
            results_simulation = self._get_paginated_results(request, simulation_id)
            
            
            # Get historical demand data
            historical_demand = self._get_historical_demand(simulation_instance)
            
            # Generate comprehensive analysis
            context = self._prepare_complete_results_context(
                simulation_id, simulation_instance, results_simulation, historical_demand
            )
            
            return render(request, 'simulate/simulate-result.html', context)
            
        except Exception as e:
            logger.error(f"Error displaying results for simulation {simulation_id}: {str(e)}")
            messages.error(request, "Error al mostrar los resultados.")
            return redirect('simulate:simulate.show')
    
    
    def _prepare_complete_results_context(self, simulation_id, simulation_instance, results_simulation, historical_demand):
        """Prepare comprehensive context data for results view - OPTIMIZADO Y CORREGIDO"""
        
        # Initialize all services once
        chart_generator = ChartGenerator()
        chart_demand = ChartDemand()
        financial_service = SimulationFinancialAnalyzer()
        statistical_service = StatisticalService()
        validation_service = SimulationValidationService()
        
        # Store services as instance variables for use in helper methods
        self.chart_demand = chart_demand
        self.validation_service = validation_service
        
        # Get related instances first
        product_instance = simulation_instance.fk_questionary_result.fk_questionary.fk_product
        business_instance = product_instance.fk_business
        
        # Set business instance on financial service
        self._set_business_on_service(financial_service, business_instance)
        
        # Debug logging
        logger.info(f"Preparing context for simulation_id: {simulation_id} (type: {type(simulation_id)})")
        
        try:
            # PASO 1: Extract variables FIRST - CRÍTICO PARA TOTALES ACUMULATIVOS
            all_variables_extracted = self._extract_all_variables(list(results_simulation))
            logger.info(f"Variables extraction result: {len(all_variables_extracted)} days extracted")
            
            if all_variables_extracted:
                sample_vars = [k for k in all_variables_extracted[0].keys() if k not in ['day', 'date', 'demand_mean', 'demand_std']]
                logger.info(f"Sample variables from first day: {sample_vars}")
            
            # PASO 2: Create enhanced chart data with historical demand
            chart_data = chart_generator.create_enhanced_chart_data(
                list(results_simulation), historical_demand
            )
            
            # PASO 3: Generate main analysis charts usando variables extraídas
            analysis_data = chart_generator.generate_all_charts_enhanced(
                simulation_id, simulation_instance, list(results_simulation), historical_demand
            )
            
            # CORRECCIÓN CRÍTICA: Calcular totales_acumulativos DESPUÉS de tener all_variables_extracted
            try:
                # Calcular totales acumulativos mejorados
                enhanced_totales = self._calculate_enhanced_totales_acumulativos(all_variables_extracted)
                
                # Actualizar analysis_data con los totales mejorados
                analysis_data['totales_acumulativos'] = enhanced_totales
                analysis_data['all_variables_extracted'] = all_variables_extracted
                
                logger.info(f"Updated totales_acumulativos with {len(enhanced_totales)} variables")
                
            except Exception as e:
                logger.error(f"Error calculating enhanced totales: {str(e)}")
                # Fallback: usar los totales básicos de analysis_data
                enhanced_totales = analysis_data.get('totales_acumulativos', {})
            
            # Log what charts were generated
            logger.info(f"Charts generated: {list(analysis_data.get('chart_images', {}).keys())}")
            
            # PASO 4: Generate additional charts
            # Generate comparison chart: Historical vs Simulated
            comparison_chart = self._generate_comparison_chart(chart_demand, historical_demand, results_simulation)
            
            # Generate three-line validation chart
            three_line_validation = self._generate_three_line_validation_chart(
                historical_demand, results_simulation, simulation_instance
            )
            
            # NUEVA FUNCIONALIDAD: Generate endogenous variables charts
            endogenous_charts = chart_generator.generate_endogenous_variables_charts(
                all_variables_extracted, enhanced_totales
            )
            
            # PASO 5: Get financial analysis and recommendations
            financial_results = self._get_financial_analysis(
                financial_service, simulation_id, simulation_instance, analysis_data
            )
            
            # PASO 6: Calculate comprehensive statistics
            demand_stats = statistical_service._calculate_comprehensive_statistics(
                historical_demand, results_simulation
            )
            
            # Log accumulated totals for debugging
            logger.info(f"Accumulated totals variables: {list(enhanced_totales.keys())}")
            
            # PASO 7: Get validation results
            validation_results = self._get_validation_results(
                validation_service, simulation_id, simulation_instance, results_simulation, historical_demand
            )
            
            # PASO 8: Prepare base context
            context = self._build_base_context(
                simulation_instance, results_simulation, product_instance, business_instance,
                analysis_data, historical_demand, demand_stats, comparison_chart,
                financial_results, validation_results
            )
            
            # PASO 9: Add core data to context
            context.update({
                'simulation_id': simulation_id,
                'chart_data': chart_data,
                'totales_acumulativos': enhanced_totales,  # Usar enhanced_totales
                'all_variables_extracted': all_variables_extracted,
                'endogenous_charts': endogenous_charts,
            })
            
            # PASO 10: Add three-line validation chart to context
            if three_line_validation:
                context.update({
                    'three_line_validation_chart': three_line_validation.get('chart'),
                    'three_line_validation_metrics': three_line_validation.get('metrics', {}),
                    'has_three_line_chart': True
                })
            else:
                context['has_three_line_chart'] = False
            
            # PASO 11: Add realistic comparison statistics
            if historical_demand and results_simulation:
                comparison = statistical_service._calculate_realistic_comparison(historical_demand, results_simulation)
                context['realistic_comparison'] = comparison
            
            # PASO 12: Add model validation if variables are available
            if all_variables_extracted:
                model_validation = self._add_model_validation(
                    validation_service, simulation_instance, results_simulation, analysis_data
                )
                context.update(model_validation)
            else:
                logger.warning("No extracted variables found for model validation")
                context['model_validation'] = None
            
            # PASO 13: Add daily validation
            daily_validation = self._add_daily_validation(
                validation_service, simulation_instance, results_simulation
            )
            context.update(daily_validation)
            
            # PASO 14: Add validation charts with three-line chart
            validation_charts = self._add_validation_charts(
                chart_generator, validation_results, results_simulation, analysis_data,
                three_line_validation
            )
            context.update(validation_charts)
            
            # PASO 15: Add advanced charts
            context.update({
                # Nuevos gráficos avanzados
                'cost_distribution_chart': analysis_data['chart_images'].get('image_data_cost_distribution'),
                'capacity_demand_chart': analysis_data['chart_images'].get('image_data_capacity_vs_demand'),
                'financial_efficiency_chart': analysis_data['chart_images'].get('image_data_financial_efficiency'),
                'production_evolution_chart': analysis_data['chart_images'].get('image_data_production_evolution'),
                
                # Flag para mostrar nuevos gráficos en template
                'has_advanced_charts': True
            })
            
            # PASO 16: Ensure all expected keys are present with default values
            context.setdefault('chart_images', {})
            context.setdefault('financial_recommendations', financial_results.get('financial_recommendations', []))
            context.setdefault('daily_validation_results', daily_validation.get('daily_validation_results', []))
            
            statistical_analysis = self._generate_statistical_analysis(
                simulation_instance, results_simulation, historical_demand, all_variables_extracted
            )
            
            statistical_charts = self._generate_enhanced_statistical_charts(
                historical_demand, simulated_demands=[float(r.demand_mean) for r in results_simulation], 
                all_variables_extracted=all_variables_extracted
            )
            
            # PASO 13.7: Análisis de validación mejorado
            enhanced_validation = self._enhanced_validation_analysis(
                simulation_instance, results_simulation, historical_demand, all_variables_extracted
            )
            
            # NUEVO: Validación KS específica para distribuciones
            ks_validation_results = self._perform_ks_validation(
                simulation_instance, results_simulation, all_variables_extracted
            )
            
            context.update({
                'statistical_analysis': statistical_analysis,
                'statistical_charts': statistical_charts,
                'enhanced_validation': enhanced_validation,
                'performance_metrics': statistical_analysis.get('performance_metrics', {}),
                'statistical_tests': statistical_analysis.get('statistical_tests', {}),
                'distribution_analysis': statistical_analysis.get('distribution_analysis', {}),
                'correlation_analysis': statistical_analysis.get('correlation_analysis', {}),
                'trend_analysis': statistical_analysis.get('trend_analysis', {}),
            })
            
            
            # PASO XX: Agregar validación KS al contexto
            context.update({
                'ks_validation': ks_validation_results,
                'has_ks_validation': bool(ks_validation_results),
                'distribution_alerts': ks_validation_results.get('alerts', []),
                'confidence_intervals': ks_validation_results.get('confidence_intervals', {}),
                'reliability_report': ks_validation_results.get('reliability_report', {}),
                'ks_test_results': ks_validation_results.get('ks_tests', {}),
                'distribution_analysis': ks_validation_results.get('distribution_analysis', {}),
            })

              
            
            # Final logging
            self._log_context_summary(context)
            
            return context
            
        except Exception as e:
            logger.error(f"Error preparing context for simulation {simulation_id}: {str(e)}")
            logger.exception("Full traceback:")
            
            # Return minimal context on error
            return {
                'simulation_id': simulation_id,
                'simulation_instance': simulation_instance,
                'results_simulation': results_simulation,
                'product_instance': product_instance if 'product_instance' in locals() else None,
                'business_instance': business_instance if 'business_instance' in locals() else None,
                'historical_demand': historical_demand,
                'error': str(e),
                'error_type': type(e).__name__,
                'chart_images': {},
                'financial_recommendations': [],
                'daily_validation_results': [],
                'validation_results': {'basic_validation': {'alerts': []}},
                'chart_data': None,
                'analysis_data': None,
                'realistic_comparison': None,
                'model_validation': None,
                'has_three_line_chart': False,
                'three_line_validation_chart': None,
                'three_line_validation_metrics': {},
                'totales_acumulativos': {},
                'all_variables_extracted': [],
                'endogenous_charts': {},
                'has_advanced_charts': False
            }

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
    
    
    def _enhance_totales_acumulativos(self, totales_acumulativos, all_variables_extracted):
        """Enhanced totales with trends and additional statistics"""
        try:
            enhanced_totales = {}
            
            for var_name, var_info in totales_acumulativos.items():
                enhanced_info = dict(var_info)  # Copy existing info
                
                # Calculate trend
                values = []
                for day_data in all_variables_extracted:
                    if var_name in day_data and day_data[var_name] is not None:
                        values.append(float(day_data[var_name]))
                
                if len(values) > 3:
                    # Calculate trend using linear regression
                    try:
                        x = np.arange(len(values))
                        slope, _, _, _, _ = scipy.stats.linregress(x, values)
                    except ImportError:
                        # Fallback simple calculation
                        slope = (values[-1] - values[0]) / len(values) if len(values) > 1 else 0
                    
                    if slope > 0.01:
                        enhanced_info['trend'] = 'increasing'
                    elif slope < -0.01:
                        enhanced_info['trend'] = 'decreasing'
                    else:
                        enhanced_info['trend'] = 'stable'
                    
                    # Add min/max values
                    enhanced_info['min_value'] = min(values)
                    enhanced_info['max_value'] = max(values)
                    enhanced_info['std_deviation'] = np.std(values)
                    
                else:
                    enhanced_info['trend'] = 'stable'
                    enhanced_info['min_value'] = None
                    enhanced_info['max_value'] = None
                    enhanced_info['std_deviation'] = None
                
                enhanced_totales[var_name] = enhanced_info
            
            return enhanced_totales
            
        except Exception as e:
            logger.error(f"Error enhancing totales_acumulativos: {str(e)}")
            return totales_acumulativos
    
    def _set_business_on_service(self, financial_service, business_instance):
        """Set business instance oQn financial service using available method/attribute"""
        if hasattr(financial_service, 'set_business'):
            financial_service.set_business(business_instance)
        elif hasattr(financial_service, 'business'):
            financial_service.business = business_instance
        elif hasattr(financial_service, '_business'):
            financial_service._business = business_instance
        else:
            # If no specific method/attribute exists, set it anyway
            financial_service.business = business_instance

    def _generate_comparison_chart(self, chart_demand, historical_demand, results_simulation):
        """Generate demand comparison chart if historical data is available"""
        comparison_chart = None
        if historical_demand:
            comparison_chart = chart_demand.generate_demand_comparison_chart(
                historical_demand, list(results_simulation)
            )
            if comparison_chart:
                logger.info("Demand comparison chart generated successfully")
        return comparison_chart

    def _get_financial_analysis(self, financial_service, simulation_id, simulation_instance, analysis_data):
        """Get financial analysis and recommendations with error handling"""
        financial_results = {}
        recommendations = []
        
        # Get financial analysis
        try:
            financial_results = financial_service.analyze_financial_results(simulation_id)
        except Exception as e:
            logger.error(f"Error in financial analysis: {e}")
            financial_results = {}
        
        # Generate dynamic recommendations
        try:
            recommendations = financial_service._generate_dynamic_recommendations(
                simulation_instance, analysis_data['totales_acumulativos'], 
                financial_results
            )
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations = []
        
        # Add recommendations to financial results
        financial_results['financial_recommendations'] = recommendations
        financial_results['financial_recommendations_to_show'] = recommendations
        
        return financial_results

    def _get_validation_results(self, validation_service, simulation_id, simulation_instance, results_simulation, historical_demand):
        """Get comprehensive validation results"""
        try:
            # Basic validation
            validation_results = validation_service.validate_simulation(simulation_id)
            
            # Model predictions validation - CORREGIR ESTE ERROR
            prediction_validation_results = {}
            try:
                prediction_validation_results = validation_service._validate_model_predictions(
                    simulation_instance, list(results_simulation), historical_demand
                )
            except Exception as e:
                logger.error(f"Error in model prediction validation: {e}")
                prediction_validation_results = {
                    'summary': {'success_rate': 0.0, 'avg_mape': 100.0},
                    'details': {},
                    'metrics': {},
                    'alerts': []
                }
            
            # Combine validation results
            combined_validation = {
                'basic_validation': validation_results,
                'prediction_validation': prediction_validation_results
            }
            
            return combined_validation
            
        except Exception as e:
            logger.error(f"Error getting validation results: {e}")
            return {
                'basic_validation': {'alerts': [], 'summary': {}},
                'prediction_validation': {'summary': {}, 'alerts': []}
            }

    
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
                    'details': 'El modelo tiene una precisión inferior al 70%, considere revisar los parámetros.',
                    'severity': 'WARNING',
                    'category': 'Precisión',
                    'recommendation': 'Revisar parámetros del modelo y datos de entrada'
                })
            elif accuracy < 50:
                alerts_by_type['ERROR'].append({
                    'message': f'Precisión del modelo crítica: {accuracy:.1f}%',
                    'details': 'El modelo tiene una precisión muy baja, requiere revisión urgente.',
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
    
    def _build_base_context(self, simulation_instance, results_simulation, product_instance, business_instance,
                    analysis_data, historical_demand, demand_stats, comparison_chart, financial_results, validation_results):
        """Build the base context dictionary"""
        
        # Group alerts by type
        alerts_by_type = {}
        basic_validation = validation_results.get('basic_validation', {})
        if basic_validation.get('alerts'):
            for alert in basic_validation['alerts']:
                alert_type = alert['type']
                if alert_type not in alerts_by_type:
                    alerts_by_type[alert_type] = []
                alerts_by_type[alert_type].append(alert)
        
        # Get prediction validation results
        prediction_validation = validation_results.get('prediction_validation', {})
        
        # Generate validation alerts grouped
        validation_alerts = self._generate_validation_alerts_grouped(validation_results)
        
        context = {
            'growth_rate': analysis_data.get('growth_rate', 0.0),
            'error_permisible': analysis_data.get('error_permisible', 0.0),
            'simulation_instance': simulation_instance,
            'results_simulation': results_simulation,
            'results': results_simulation,
            'product_instance': product_instance,
            'business_instance': business_instance,
            'all_variables_extracted': analysis_data.get('all_variables_extracted', []),
            'totales_acumulativos': analysis_data.get('totales_acumulativos', {}),
            'historical_demand': historical_demand,
            'demand_stats': demand_stats,
            'comparison_chart': comparison_chart,
            'validation_alerts': validation_alerts,  # Usar la versión agrupada
            'basic_validation_summary': basic_validation.get('summary', {}),  # Cambiar nombre
            'simulation_valid': basic_validation.get('is_valid', False),
            # Prediction validation results
            'validation_summary': prediction_validation.get('summary', {}),
            'validation_details': prediction_validation.get('details', {}),
            'validation_metrics': prediction_validation.get('metrics', {}),
            'validation_by_distribution': prediction_validation.get('by_distribution', {}),
            'validation_recommendations': prediction_validation.get('recommendations', []),
            **analysis_data.get('chart_images', {}),  # Unpack all chart images
            **financial_results,
        }

        return context

    def _add_model_validation(self, validation_service, simulation_instance, results_simulation, analysis_data):
        """Add model variables validation to context"""
        model_validation_results = validation_service._validate_model_variables(
            simulation_instance, results_simulation, analysis_data['all_variables_extracted']
        )
        
        model_validation_context = {
            'model_validation_summary': model_validation_results['summary'],
            'model_validation_by_variable': model_validation_results['by_variable'],
            'model_validation_daily_details': model_validation_results['daily_details'],
            'model_variables_valid': model_validation_results['summary']['is_valid']
        }
        
        # Log model validation info
        logger.info(f"Model validation completed: {model_validation_results['summary']['success_rate']:.1f}% success rate")
        logger.info(f"Variables validated: {model_validation_results['summary']['total_variables']} total, "
                    f"{model_validation_results['summary']['precise_count']} precise, "
                    f"{model_validation_results['summary']['acceptable_count']} acceptable, "
                    f"{model_validation_results['summary']['inaccurate_count']} inaccurate")
        
        return model_validation_context

    def _add_daily_validation(self, validation_service, simulation_instance, results_simulation):
        """Add daily validation results to context"""
        try:
            # Extract real values from questionnaire
            real_values = self._extract_real_values_from_questionnaire(simulation_instance)
            
            # Perform daily validation - CORREGIR
            daily_validation_results = []
            daily_validation_charts = {}
            daily_validation_summary = {'success_rate': 0.0, 'avg_accuracy': 0.0}
            
            try:
                daily_validation_results = validation_service._validate_by_day(
                    simulation_instance, list(results_simulation), real_values
                )
            except Exception as e:
                logger.error(f"Error in daily validation: {e}")
            
            # Generate daily validation charts - PROTEGER DE ERRORES
            try:
                if hasattr(validation_service, '_generate_daily_validation_charts'):
                    daily_validation_charts = validation_service._generate_daily_validation_charts(
                        daily_validation_results
                    )
            except Exception as e:
                logger.error(f"Error generating daily validation charts: {e}")
            
            # Calculate summary - PROTEGER DE ERRORES
            try:
                if hasattr(validation_service, '_calculate_daily_validation_summary'):
                    daily_validation_summary = validation_service._calculate_daily_validation_summary(
                        daily_validation_results
                    )
            except Exception as e:
                logger.error(f"Error calculating daily validation summary: {e}")
            
            return {
                'daily_validation_results': daily_validation_results,
                'daily_validation_charts': daily_validation_charts,
                'daily_validation_summary': daily_validation_summary
            }
            
        except Exception as e:
            logger.error(f"Error in daily validation: {e}")
            return {
                'daily_validation_results': [],
                'daily_validation_charts': {},
                'daily_validation_summary': {'success_rate': 0.0, 'avg_accuracy': 0.0}
            }

    def _add_validation_charts(self, chart_generator, validation_results, results_simulation, 
                      analysis_data, three_line_validation=None):
        """Add validation charts to context including three-line chart"""
        try:
            validation_chart_context = {}
            
            # Generate basic validation charts - PROTEGER DE ERRORES
            basic_validation = validation_results.get('basic_validation', {})
            if basic_validation:
                try:
                    validation_chart_context = chart_generator.generate_validation_charts_context(basic_validation)
                except Exception as e:
                    logger.error(f"Error generating basic validation charts: {e}")
                    validation_chart_context = {'charts': {}, 'chart_images': {}}
            
            # Get variables for chart generation
            all_variables_extracted = analysis_data.get('all_variables_extracted', [])
            totales_acumulativos = analysis_data.get('totales_acumulativos', {})
            
            # Generate model validation charts - CORREGIR ESTRUCTURA
            model_validation_charts = {}
            charts_context = {}
            
            try:
                # CORREGIR: Verificar que by_variable existe y tiene la estructura correcta
                by_variable = validation_results.get('basic_validation', {}).get('by_variable', {})
                if by_variable and all_variables_extracted and len(all_variables_extracted) > 0:
                    # Verificar que by_variable tiene datos válidos
                    valid_variables = {k: v for k, v in by_variable.items() 
                                    if v.get('status') != 'NO_DATA' and v.get('simulated_values_count', 0) > 0}
                    
                    if valid_variables:
                        validation_charts = chart_generator._generate_validation_charts_for_variables(
                            valid_variables,  # Usar valid_variables en lugar de by_variable
                            list(results_simulation),  # Convertir a lista
                            all_variables_extracted
                        )
                        model_validation_charts = validation_charts
                        charts_context = chart_generator.generate_validation_charts_context(
                            {'validation_charts': validation_charts}
                        )
            except Exception as e:
                logger.error(f"Error generating model validation charts: {e}")
                model_validation_charts = {}
                charts_context = {}
            
            # Generate endogenous variables charts - PROTEGER
            endogenous_charts = {}
            try:
                endogenous_charts = chart_generator.generate_endogenous_variables_charts(
                    all_variables_extracted,
                    totales_acumulativos
                )
            except Exception as e:
                logger.error(f"Error generating endogenous charts: {e}")
            
            # Generate additional analysis charts - PROTEGER
            additional_charts = {}
            try:
                additional_charts = chart_generator.generate_additional_analysis_charts(
                    all_variables_extracted,
                    totales_acumulativos
                )
            except Exception as e:
                logger.error(f"Error generating additional charts: {e}")
            
            # Prepare chart images safely
            chart_images = validation_chart_context.get('chart_images', {})
            
            # Add three-line validation chart if available
            if three_line_validation and three_line_validation.get('chart'):
                chart_images['three_line_validation'] = three_line_validation['chart']
            
            # Add additional charts to context safely
            for key, chart in additional_charts.items():
                if chart:  # Verificar que el chart no sea None
                    chart_images[f'additional_{key}'] = chart
            
            return {
                'validation_charts': validation_chart_context.get('charts', {}),
                'validation_chart_images': chart_images,
                'model_validation_charts': model_validation_charts,
                'charts_context': charts_context,
                'endogenous_charts': endogenous_charts,
                'additional_charts': additional_charts
            }
            
        except Exception as e:
            logger.error(f"Error adding validation charts: {e}")
            return {
                'validation_charts': {},
                'validation_chart_images': {},
                'model_validation_charts': {},
                'charts_context': {},
                'endogenous_charts': {},
                'additional_charts': {}
            }

    def _log_context_summary(self, context):
        """Log summary information about the generated context"""
        # Log final context keys for debugging
        chart_keys = [k for k in context.keys() if k.startswith('image_data')]
        logger.info(f"Chart keys in context: {chart_keys}")
        
        # Log variable extraction info
        all_variables = context.get('all_variables_extracted', [])
        logger.info(f"all_variables_extracted type: {type(all_variables)}")
        if all_variables:
            first_item = all_variables[0] if all_variables else None
            logger.info(f"First item structure: {first_item.keys() if isinstance(first_item, dict) else 'Not a dict'}")
        
        # Log chart generation summary
        validation_charts = context.get('model_validation_charts', {})
        endogenous_charts = context.get('endogenous_charts', {})
        additional_charts = context.get('additional_charts', {})
        logger.info(f"Generated {len(validation_charts)} validation chart types")
        logger.info(f"Generated {len(endogenous_charts)} endogenous variable charts")
        logger.info(f"Generated {len(additional_charts)} additional analysis charts")
    
    
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
    
    def _get_simulation_with_relations(self, simulation_id: int) -> Simulation:
        """Get simulation with all necessary relations"""
        return get_object_or_404(
            Simulation.objects.select_related(
                'fk_questionary_result__fk_questionary__fk_product__fk_business',
                'fk_fdp'
            ).prefetch_related(
                'results',
                'fk_questionary_result__fk_question_result_answer__fk_question__fk_variable'
            ),
            pk=simulation_id
        )
    
    def _user_can_view_simulation(self, user, simulation: Simulation) -> bool:
        """Check if user has permission to view simulation"""
        business = simulation.fk_questionary_result.fk_questionary.fk_product.fk_business
        return business.fk_user == user
    
    def _get_paginated_results(self, request, simulation_id):
        """Get paginated simulation results"""
        results = ResultSimulation.objects.filter(
            is_active=True,
            fk_simulation_id=simulation_id
        ).order_by('date')
        
        paginator = Paginator(results, 365)  # 50 results per page
        page = request.GET.get('page', 1)
        
        try:
            return paginator.page(page)
        except PageNotAnInteger:
            return paginator.page(1)
        except EmptyPage:
            return paginator.page(paginator.num_pages)
    
    def _extract_historical_demand(self, simulation: Simulation) -> List[float]:
        """Extract historical demand data"""
        try:
            # Try from simulation first
            if simulation.demand_history:
                return self.data_parser.parse_demand_history(simulation.demand_history)
            
            # Try from questionnaire
            answers = simulation.fk_questionary_result.fk_question_result_answer.all()
            for answer in answers:
                if 'históric' in answer.fk_question.question.lower() and 'demanda' in answer.fk_question.question.lower():
                    if answer.answer:
                        return self.data_parser.parse_demand_history(answer.answer)
            
            return []
        except Exception as e:
            logger.error(f"Error extracting historical demand: {str(e)}")
            return []
    
    def _extract_real_values_from_questionnaire(self, simulation: Simulation) -> Dict[str, float]:
        """Extract real values from questionnaire for validation"""
        real_values = {}
        
        try:
            answers = simulation.fk_questionary_result.fk_question_result_answer.select_related(
                'fk_question__fk_variable'
            ).all()
            
            for answer in answers:
                if answer.fk_question.fk_variable and answer.answer:
                    var_initials = answer.fk_question.fk_variable.initials
                    value = self.data_parser.parse_numeric_answer(answer.answer)
                    
                    if value is not None:
                        real_values[var_initials] = value
            
            # Calculate derived values
            real_values = self._calculate_derived_real_values(real_values)
            
            logger.info(f"Extracted {len(real_values)} real values from questionnaire")
            
        except Exception as e:
            logger.error(f"Error extracting real values: {str(e)}")
        
        return real_values
    
    def _calculate_derived_real_values(self, real_values: Dict[str, float]) -> Dict[str, float]:
        """Calculate derived values that aren't directly in questionnaire"""
        # Total income
        if 'IT' not in real_values and all(k in real_values for k in ['TPV', 'PVP']):
            real_values['IT'] = real_values['TPV'] * real_values['PVP']
        
        # Total expenses
        if 'TG' not in real_values and 'GO' in real_values:
            real_values['TG'] = real_values['GO'] * 1.2  # Estimate
        
        # Total profit
        if 'GT' not in real_values and all(k in real_values for k in ['IT', 'TG']):
            real_values['GT'] = real_values['IT'] - real_values['TG']
        
        # Production capacity
        if 'CPROD' not in real_values and 'QPL' in real_values:
            real_values['CPROD'] = real_values['QPL'] * 1.2  # 20% headroom
        
        # Average demand
        if 'DPH' not in real_values and 'DH' in real_values:
            if isinstance(real_values['DH'], list):
                real_values['DPH'] = np.mean(real_values['DH'])
            else:
                real_values['DPH'] = real_values['DH']
        
        return real_values
    
    def _generate_daily_comparisons(self, results: List[ResultSimulation],
                                  real_values: Dict[str, float],
                                  historical_demand: List[float]) -> List[Dict[str, Any]]:
        """Generate daily comparison data for analysis"""
        comparisons = []
        
        for idx, result in enumerate(results):
            day_comparison = {
                'day': idx + 1,
                'date': result.date,
                'simulated_demand': float(result.demand_mean),
                'variables': {}
            }
            
            # Add historical demand if available
            if historical_demand and idx < len(historical_demand):
                day_comparison['historical_demand'] = historical_demand[idx]
                day_comparison['demand_deviation'] = (
                    (day_comparison['simulated_demand'] - historical_demand[idx]) / 
                    historical_demand[idx] * 100 if historical_demand[idx] > 0 else 0
                )
            
            # Compare key variables
            if hasattr(result, 'variables') and result.variables:
                for var_name, sim_value in result.variables.items():
                    if var_name in real_values and not var_name.startswith('_'):
                        real_value = real_values[var_name]
                        day_comparison['variables'][var_name] = {
                            'simulated': float(sim_value) if isinstance(sim_value, (int, float)) else 0,
                            'real': real_value,
                            'deviation': self._calculate_deviation(sim_value, real_value),
                            'status': self._determine_status(sim_value, real_value, var_name)
                        }
            
            comparisons.append(day_comparison)
        
        return comparisons
    
    def _calculate_deviation(self, simulated: Any, real: float) -> float:
        """Calculate percentage deviation"""
        try:
            sim_value = float(simulated) if isinstance(simulated, (int, float)) else 0
            if real == 0:
                return 100.0 if sim_value != 0 else 0.0
            return ((sim_value - real) / abs(real)) * 100
        except:
            return 0.0
    
    def _determine_status(self, simulated: Any, real: float, var_name: str) -> str:
        """Determine comparison status"""
        deviation = abs(self._calculate_deviation(simulated, real))
        
        # Variable-specific thresholds
        strict_vars = ['PVP', 'CPROD', 'NEPP', 'CFD']
        flexible_vars = ['DPH', 'TPV', 'GT', 'IPF']
        
        if var_name in strict_vars:
            threshold = 5  # 5% tolerance
        elif var_name in flexible_vars:
            threshold = 20  # 20% tolerance
        else:
            threshold = 10  # 10% default
        
        if deviation <= threshold:
            return 'success'
        elif deviation <= threshold * 2:
            return 'warning'
        else:
            return 'danger'
    
    def _calculate_summary_statistics(self, results: List[ResultSimulation],
                                    historical_demand: List[float],
                                    validation_results: Dict) -> Dict[str, Any]:
        """Calculate comprehensive summary statistics"""
        summary = {
            'simulation_metrics': {},
            'demand_analysis': {},
            'performance_indicators': {},
            'validation_metrics': {}
        }
        
        # Extract demand values
        simulated_demands = [float(r.demand_mean) for r in results]
        
        # Simulation metrics
        summary['simulation_metrics'] = {
            'total_days': len(results),
            'start_date': results[0].date if results else None,
            'end_date': results[-1].date if results else None,
        }
        
        # Demand analysis
        if simulated_demands:
            summary['demand_analysis'] = {
                'simulated': {
                    'mean': np.mean(simulated_demands),
                    'std': np.std(simulated_demands),
                    'min': np.min(simulated_demands),
                    'max': np.max(simulated_demands),
                    'cv': np.std(simulated_demands) / np.mean(simulated_demands) if np.mean(simulated_demands) > 0 else 0
                }
            }
            
            if historical_demand:
                summary['demand_analysis']['historical'] = {
                    'mean': np.mean(historical_demand),
                    'std': np.std(historical_demand),
                    'min': np.min(historical_demand),
                    'max': np.max(historical_demand),
                    'cv': np.std(historical_demand) / np.mean(historical_demand) if np.mean(historical_demand) > 0 else 0
                }
                
                # Comparison
                summary['demand_analysis']['comparison'] = {
                    'mean_deviation': ((summary['demand_analysis']['simulated']['mean'] - 
                                      summary['demand_analysis']['historical']['mean']) / 
                                     summary['demand_analysis']['historical']['mean'] * 100),
                    'cv_change': (summary['demand_analysis']['simulated']['cv'] - 
                                 summary['demand_analysis']['historical']['cv'])
                }
        
        # Performance indicators
        if results:
            # Extract key metrics from last result
            last_result = results[-1]
            if hasattr(last_result, 'variables') and last_result.variables:
                vars = last_result.variables
                summary['performance_indicators'] = {
                    'final_profit': float(vars.get('GT', 0)),
                    'final_margin': float(vars.get('NR', 0)) * 100,
                    'service_level': float(vars.get('NSC', 0)) * 100,
                    'efficiency': float(vars.get('EOG', 0)) * 100,
                    'roi': float(vars.get('RI', 0)) * 100
                }
        
        # Validation metrics
        if validation_results.get('summary'):
            summary['validation_metrics'] = {
                'overall_accuracy': validation_results['summary'].get('overall_accuracy', 0),
                'success_rate': validation_results['summary'].get('success_rate', 0),
                'variables_validated': validation_results['summary'].get('total_days', 0)
            }
        
        return summary
    
    def _extract_all_variables(self, results: List[ResultSimulation]) -> List[Dict[str, Any]]:
        """Extract all variables from results for analysis - CORREGIDO"""
        all_variables = []
        
        for idx, result in enumerate(results):
            try:
                day_data = {
                    'day': idx + 1,
                    'date': result.date.isoformat() if hasattr(result, 'date') and result.date else None,
                    'demand_mean': float(result.demand_mean) if hasattr(result, 'demand_mean') else 0.0,
                    'demand_std': float(result.demand_std_deviation) if hasattr(result, 'demand_std_deviation') else 0.0
                }
                
                # CORRECCIÓN: Acceder a las variables correctamente
                if hasattr(result, 'variables') and result.variables:
                    # Si variables es un string JSON, parsearlo
                    if isinstance(result.variables, str):
                        try:
                            variables_dict = json.loads(result.variables)
                            for key, value in variables_dict.items():
                                if not key.startswith('_'):
                                    try:
                                        day_data[key] = float(value) if isinstance(value, (int, float, str)) and str(value).replace('.','').replace('-','').isdigit() else value
                                    except (ValueError, TypeError):
                                        day_data[key] = value
                        except (json.JSONDecodeError, TypeError) as e:
                            logger.warning(f"Could not parse variables JSON for result {result.id}: {e}")
                            variables_dict = {}
                    
                    # Si variables es un diccionario
                    elif isinstance(result.variables, dict):
                        for key, value in result.variables.items():
                            if not key.startswith('_'):
                                try:
                                    day_data[key] = float(value) if isinstance(value, (int, float)) else value
                                except (ValueError, TypeError):
                                    day_data[key] = value
                
                # Si no hay variables, intentar calcular básicas
                else:
                    try:
                        calculated_vars = self.math_engine.calculate_basic_variables(
                            demand=day_data['demand_mean'],
                            day=day_data['day']
                        )
                        day_data.update(calculated_vars)
                    except Exception as e:
                        logger.warning(f"Could not calculate variables for day {idx + 1}: {e}")
                
                all_variables.append(day_data)
                
            except Exception as e:
                logger.error(f"Error processing result {idx}: {e}")
                # Agregar datos mínimos en caso de error
                all_variables.append({
                    'day': idx + 1,
                    'date': None,
                    'demand_mean': 0.0,
                    'demand_std': 0.0
                })
        
        return all_variables
    
    def _generate_demand_comparison_chart(self, historical_demand: List[float],
                                        results: List[ResultSimulation]) -> Optional[str]:
        """Generate demand comparison chart"""
        try:
            if not historical_demand or not results:
                return None
            
            return self.chart_generator.generate_demand_comparison_chart(
                list(range(1, len(results) + 1)),
                self._extract_all_variables(results),
                historical_demand
            )
        except Exception as e:
            logger.error(f"Error generating comparison chart: {str(e)}")
            return None
    
    def _group_alerts_by_type(self, alerts: List[Dict]) -> Dict[str, List[Dict]]:
        """Group alerts by type for display"""
        grouped = {}
        
        for alert in alerts:
            alert_type = alert.get('type', 'OTHER')
            if alert_type not in grouped:
                grouped[alert_type] = []
            grouped[alert_type].append(alert)
        
        # Sort alerts within each group by severity
        severity_order = {'ERROR': 0, 'WARNING': 1, 'INFO': 2}
        for alert_type in grouped:
            grouped[alert_type].sort(
                key=lambda x: severity_order.get(x.get('severity', 'INFO'), 3)
            )
        
        return grouped
    
    def _calculate_model_performance(self, results: List[ResultSimulation],
                                   real_values: Dict[str, float],
                                   historical_demand: List[float]) -> Dict[str, Any]:
        """Calculate overall model performance metrics"""
        performance = {
            'demand_forecast_accuracy': 0,
            'variable_accuracy': {},
            'overall_score': 0,
            'strengths': [],
            'weaknesses': []
        }
        
        # Demand forecast accuracy
        if historical_demand and results:
            simulated_demands = [float(r.demand_mean) for r in results[:len(historical_demand)]]
            if simulated_demands:
                mape = self._calculate_mape(historical_demand[:len(simulated_demands)], simulated_demands)
                performance['demand_forecast_accuracy'] = max(0, 100 - mape)
        
        # Variable accuracy
        variable_scores = []
        for var_name, real_value in real_values.items():
            if var_name.startswith('_'):
                continue
            
            # Get average simulated value
            sim_values = []
            for result in results:
                if hasattr(result, 'variables') and result.variables:
                    if var_name in result.variables:
                        try:
                            sim_values.append(float(result.variables[var_name]))
                        except:
                            pass
            
            if sim_values:
                avg_sim = np.mean(sim_values)
                accuracy = max(0, 100 - abs(self._calculate_deviation(avg_sim, real_value)))
                performance['variable_accuracy'][var_name] = accuracy
                variable_scores.append(accuracy)
                
                # Identify strengths and weaknesses
                if accuracy >= 90:
                    performance['strengths'].append(f"{var_name}: {accuracy:.1f}% accuracy")
                elif accuracy < 70:
                    performance['weaknesses'].append(f"{var_name}: {accuracy:.1f}% accuracy")
        
        # Overall score
        all_scores = []
        if performance['demand_forecast_accuracy'] > 0:
            all_scores.append(performance['demand_forecast_accuracy'])
        all_scores.extend(variable_scores)
        
        if all_scores:
            performance['overall_score'] = np.mean(all_scores)
        
        return performance
    
    def _calculate_mape(self, actual: List[float], predicted: List[float]) -> float:
        """Calculate Mean Absolute Percentage Error"""
        if len(actual) != len(predicted) or not actual:
            return 100.0
        
        errors = []
        for a, p in zip(actual, predicted):
            if a != 0:
                errors.append(abs((a - p) / a) * 100)
        
        return np.mean(errors) if errors else 100.0
    
    def _get_comparable_simulations(self, current_simulation: Simulation) -> List[Simulation]:
        """Get other simulations for the same product for comparison"""
        try:
            return Simulation.objects.filter(
                fk_questionary_result__fk_questionary__fk_product=current_simulation.fk_questionary_result.fk_questionary.fk_product,
                is_active=True
            ).exclude(
                id=current_simulation.id
            ).order_by('-date_created')[:5]  # Last 5 simulations
        except:
            return []
    
    def _rank_simulation_performance(self, current_id: int,
                                   other_simulations: List[Simulation]) -> Dict[str, Any]:
        """Rank current simulation against others"""
        all_simulations = list(other_simulations) + [
            Simulation.objects.get(id=current_id)
        ]
        
        rankings = []
        for sim in all_simulations:
            # Get summary metrics
            try:
                results = ResultSimulation.objects.filter(
                    fk_simulation=sim,
                    is_active=True
                ).order_by('-date').first()
                
                if results and hasattr(results, 'variables') and results.variables:
                    vars = results.variables
                    score = (
                        float(vars.get('NR', 0)) * 100 +  # Net margin weight
                        float(vars.get('NSC', 0)) * 50 +  # Service level weight
                        float(vars.get('EOG', 0)) * 30    # Efficiency weight
                    )
                    rankings.append({
                        'id': sim.id,
                        'date': sim.date_created,
                        'score': score,
                        'metrics': {
                            'profit_margin': float(vars.get('NR', 0)) * 100,
                            'service_level': float(vars.get('NSC', 0)) * 100,
                            'efficiency': float(vars.get('EOG', 0)) * 100
                        }
                    })
            except:
                continue
        
        # Sort by score
        rankings.sort(key=lambda x: x['score'], reverse=True)
        
        # Find current simulation rank
        current_rank = None
        for idx, rank in enumerate(rankings):
            if rank['id'] == current_id:
                current_rank = idx + 1
                break
        
        return {
            'current_rank': current_rank,
            'total_simulations': len(rankings),
            'rankings': rankings[:5],  # Top 5
            'is_best': current_rank == 1 if current_rank else False
        }
        
    def _calculate_complete_demand_stats(self, historical_demand, results_simulation):
        """
        Calcula estadísticas completas de demanda incluyendo percentiles, mediana, etc.
        """
        try:
            demand_stats = {
                'historical': {},
                'simulated': {},
                'comparison': {}
            }
            
            # Extraer demandas simuladas
            simulated_demands = []
            for result in results_simulation:
                if hasattr(result, 'demand_mean') and result.demand_mean is not None:
                    simulated_demands.append(float(result.demand_mean))
            
            # Calcular estadísticas históricas
            if historical_demand:
                demand_stats['historical'] = self._calculate_detailed_statistics(historical_demand)
            
            # Calcular estadísticas simuladas
            if simulated_demands:
                demand_stats['simulated'] = self._calculate_detailed_statistics(simulated_demands)
            
            # Calcular comparación si ambas están disponibles
            if historical_demand and simulated_demands:
                demand_stats['comparison'] = self._calculate_comparison_metrics(
                    historical_demand, simulated_demands
                )
            
            logger.info("Complete demand statistics calculated successfully")
            return demand_stats
            
        except Exception as e:
            logger.error(f"Error calculating complete demand stats: {str(e)}")
            return {'historical': {}, 'simulated': {}, 'comparison': {}}

    def _calculate_detailed_statistics(self, data):
        """Calcular estadísticas detalladas para un conjunto de datos"""
        try:
            if not data:
                return {}
            
            data_array = np.array(data)
            
            stats = {
                'mean': float(np.mean(data_array)),
                'std': float(np.std(data_array)),
                'min': float(np.min(data_array)),
                'max': float(np.max(data_array)),
                'median': float(np.median(data_array)),
                'q25': float(np.percentile(data_array, 25)),
                'q75': float(np.percentile(data_array, 75)),
                'count': len(data),
                'sum': float(np.sum(data_array))
            }
            
            # Coeficiente de variación
            stats['cv'] = stats['std'] / stats['mean'] if stats['mean'] != 0 else 0
            
            # Rango intercuartílico
            stats['iqr'] = stats['q75'] - stats['q25']
            
            # Skewness y Kurtosis
            if len(data) >= 3:
                stats['skewness'] = float(scipy.stats.skew(data_array))
                stats['kurtosis'] = float(scipy.stats.kurtosis(data_array))
            else:
                stats['skewness'] = 0
                stats['kurtosis'] = 0
            
            # Percentiles adicionales
            stats['p10'] = float(np.percentile(data_array, 10))
            stats['p90'] = float(np.percentile(data_array, 90))
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating detailed statistics: {str(e)}")
            return {}

    def _calculate_comparison_metrics(self, historical_data, simulated_data):
        """Calcular métricas de comparación entre datos históricos y simulados"""
        try:
            comparison = {}
            
            # Convertir a arrays numpy
            hist_array = np.array(historical_data)
            sim_array = np.array(simulated_data)
            
            # Ajustar longitudes para comparación
            min_length = min(len(hist_array), len(sim_array))
            hist_trimmed = hist_array[:min_length]
            sim_trimmed = sim_array[:min_length]
            
            # Diferencias básicas
            mean_diff = np.mean(sim_trimmed) - np.mean(hist_trimmed)
            comparison['mean_diff'] = float(mean_diff)
            comparison['mean_diff_pct'] = float((mean_diff / np.mean(hist_trimmed)) * 100) if np.mean(hist_trimmed) != 0 else 0
            
            # Diferencia en variabilidad
            hist_cv = np.std(hist_trimmed) / np.mean(hist_trimmed) if np.mean(hist_trimmed) != 0 else 0
            sim_cv = np.std(sim_trimmed) / np.mean(sim_trimmed) if np.mean(sim_trimmed) != 0 else 0
            comparison['cv_diff'] = float(sim_cv - hist_cv)
            
            # Correlación
            if len(hist_trimmed) > 1 and len(sim_trimmed) > 1:
                correlation = np.corrcoef(hist_trimmed, sim_trimmed)[0, 1]
                comparison['correlation'] = float(correlation) if not np.isnan(correlation) else 0
            else:
                comparison['correlation'] = 0
            
            # Métricas de error
            comparison['mape'] = self._calculate_mape(hist_trimmed, sim_trimmed)
            comparison['rmse'] = self._calculate_rmse(hist_trimmed, sim_trimmed)
            comparison['mae'] = self._calculate_mae(hist_trimmed, sim_trimmed)
            
            # R² (coeficiente de determinación)
            if len(hist_trimmed) > 1:
                ss_res = np.sum((hist_trimmed - sim_trimmed) ** 2)
                ss_tot = np.sum((hist_trimmed - np.mean(hist_trimmed)) ** 2)
                comparison['r_squared'] = float(1 - (ss_res / ss_tot)) if ss_tot != 0 else 0
            else:
                comparison['r_squared'] = 0
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error calculating comparison metrics: {str(e)}")
            return {}

    def _calculate_mape(self, actual, predicted):
        """Calcular Mean Absolute Percentage Error"""
        try:
            if len(actual) == 0:
                return 100.0
            
            mask = actual != 0
            if not np.any(mask):
                return 100.0
            
            mape = np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100
            return float(mape)
        except:
            return 100.0

    def _calculate_rmse(self, actual, predicted):
        """Calcular Root Mean Square Error"""
        try:
            return float(np.sqrt(np.mean((actual - predicted) ** 2)))
        except:
            return 0.0

    def _calculate_mae(self, actual, predicted):
        """Calcular Mean Absolute Error"""
        try:
            return float(np.mean(np.abs(actual - predicted)))
        except:
            return 0.0
    
    
    def _calculate_enhanced_totales_acumulativos(self, all_variables_extracted):
        """
        Calcula totales acumulativos con estadísticas completas - CORREGIDO
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

    def _get_variable_unit(self, var_name):
        """Get unit for variable"""
        units = {
            'PVP': 'Bs./L', 'TPV': 'L', 'IT': 'Bs.', 'TG': 'Bs.', 'GT': 'Bs.',
            'NR': '%', 'NSC': '%', 'EOG': '%', 'CFD': 'Bs.', 'CVU': 'Bs./L',
            'DPH': 'L/día', 'CPROD': 'L/día', 'NEPP': 'Personas', 'RI': '%', 'IPF': 'L'
        }
        return units.get(var_name, '')

    def _collect_enhanced_variable_data(self, all_variables_extracted, var_name):
        """Recopilar datos mejorados para una variable específica - CORREGIDO"""
        try:
            values = []
            
            logger.debug(f"Collecting data for variable {var_name} from {len(all_variables_extracted)} days")
            
            for day_idx, day_data in enumerate(all_variables_extracted):
                if var_name in day_data and day_data[var_name] is not None:
                    try:
                        # MEJORADO: Mejor validación y conversión de valores
                        raw_value = day_data[var_name]
                        
                        if isinstance(raw_value, (int, float)):
                            value = float(raw_value)
                        elif isinstance(raw_value, str):
                            # Limpiar string antes de convertir
                            cleaned_value = raw_value.strip().replace(',', '.')
                            if cleaned_value.replace('.','').replace('-','').replace('e','').replace('E','').isdigit():
                                value = float(cleaned_value)
                            else:
                                logger.debug(f"Skipping non-numeric string value for {var_name} on day {day_idx}: {raw_value}")
                                continue
                        else:
                            logger.debug(f"Skipping non-numeric value for {var_name} on day {day_idx}: {raw_value} (type: {type(raw_value)})")
                            continue
                        
                        # Validar que el valor sea razonable
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

    def _calculate_trend_analysis(self, values):
        """Calcular análisis de tendencia detallado - CORREGIDO"""
        try:
            if len(values) < 3:
                return {'direction': 'stable', 'strength': 0}
            
            # Usar regresión lineal para determinar tendencia
            x = np.arange(len(values))
            slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(x, values)  # CORREGIDO: scipy.stats
            
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

    def _enhanced_validation_analysis(self, simulation_instance, results_simulation, historical_demand, all_variables_extracted):
        """Análisis de validación mejorado"""
        try:
            validation_data = {}
            
            # 1. Validación básica del modelo
            basic_validation = self.validation_service.validate_simulation(simulation_instance.id)
            validation_data['basic_validation'] = basic_validation
            
            # 2. Validación por variables
            if all_variables_extracted:
                variable_validation = self.validation_service._validate_individual_variables(
                    simulation_instance, all_variables_extracted
                )
                validation_data['variable_validation'] = variable_validation
            
            # 3. Validación temporal (por días)
            temporal_validation = self.validation_service._validate_temporal_consistency(
                results_simulation, historical_demand
            )
            validation_data['temporal_validation'] = temporal_validation
            
            # 4. Métricas de confiabilidad
            reliability_metrics = self.validation_service._calculate_reliability_metrics(
                historical_demand, results_simulation
            )
            validation_data['reliability_metrics'] = reliability_metrics
            
            # 5. Intervalos de confianza
            if historical_demand:
                confidence_intervals = self.validation_service._calculate_confidence_intervals(
                    historical_demand, [float(r.demand_mean) for r in results_simulation]
                )
                validation_data['confidence_intervals'] = confidence_intervals
            
            return validation_data
            
        except Exception as e:
            logger.error(f"Error in enhanced validation analysis: {e}")
            return {}
    
    
    def _analyze_trends(self, data):
        """Analizar tendencias en los datos - CORREGIDO"""
        try:
            if len(data) < 3:
                return {}
            
            data_array = np.array(data)
            x = np.arange(len(data_array))
            
            # Regresión lineal
            slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(x, data_array)  # CORREGIDO: scipy.stats
            
            # Prueba de Mann-Kendall para tendencia
            try:
                tau, tau_p = scipy.stats.kendalltau(x, data_array)  # CORREGIDO: scipy.stats
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
            
            # Usar el chart_generator existente
            chart_generator = ChartGenerator()
            
            # 1. Histograma y distribución
            try:
                charts['histogram'] = chart_generator._generate_histogram_chart(simulated_demands)
            except Exception as e:
                logger.warning(f"Error generating histogram: {e}")
            
            # 2. Box plot comparativo
            if historical_demand:
                try:
                    charts['boxplot'] = chart_generator._generate_comparative_boxplot(
                        historical_demand, simulated_demands
                    )
                except Exception as e:
                    logger.warning(f"Error generating boxplot: {e}")
            
            # 3. Scatter plot (si hay datos históricos)
            if historical_demand:
                try:
                    charts['scatter'] = chart_generator._generate_scatter_plot(
                        historical_demand, simulated_demands
                    )
                except Exception as e:
                    logger.warning(f"Error generating scatter plot: {e}")
            
            # 4. Gráfico de residuos
            if historical_demand:
                try:
                    charts['residuals'] = chart_generator._generate_residuals_plot(
                        historical_demand, simulated_demands
                    )
                except Exception as e:
                    logger.warning(f"Error generating residuals plot: {e}")
            
            # 5. QQ plot para normalidad
            try:
                charts['qq_plot'] = chart_generator._generate_qq_plot(simulated_demands)
            except Exception as e:
                logger.warning(f"Error generating QQ plot: {e}")
            
            return charts
            
        except Exception as e:
            logger.error(f"Error generating statistical charts: {e}")
            return {}
    
    
    def _analyze_variable_correlations(self, all_variables_extracted):
        """Analizar correlaciones entre variables endógenas - CORREGIDO"""
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
                                corr_coef, p_value = scipy.stats.pearsonr(  # CORREGIDO: scipy.stats
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
    
    def _analyze_distribution(self, data):
        """Analizar distribución de los datos - CORREGIDO"""
        try:
            if len(data) < 3:
                return {}
            
            data_array = np.array(data)
            
            analysis = {
                'basic_stats': {
                    'mean': float(np.mean(data_array)),
                    'std': float(np.std(data_array)),
                    'variance': float(np.var(data_array)),
                    'skewness': float(scipy.stats.skew(data_array)),  # CORREGIDO: scipy.stats
                    'kurtosis': float(scipy.stats.kurtosis(data_array)),  # CORREGIDO: scipy.stats
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
            if len(data_array) <= 5000:  # Shapiro-Wilk es válido para n <= 5000
                try:
                    stat, p_value = scipy.stats.shapiro(data_array)  # CORREGIDO: scipy.stats
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
                    scipy.stats.norm,      # CORREGIDO: scipy.stats
                    scipy.stats.lognorm,   # CORREGIDO: scipy.stats
                    scipy.stats.expon,     # CORREGIDO: scipy.stats
                    scipy.stats.gamma      # CORREGIDO: scipy.stats
                ]
                best_dist = None
                best_fit = -np.inf
                best_params = {}
                
                for dist in distributions:
                    try:
                        params = dist.fit(data_array)
                        # Prueba de Kolmogorov-Smirnov
                        ks_stat, ks_p = scipy.stats.kstest(  # CORREGIDO: scipy.stats
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
        """Realizar pruebas estadísticas comparativas - CORREGIDO"""
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
                t_stat, t_p = scipy.stats.ttest_ind(hist_trimmed, sim_trimmed)  # CORREGIDO: scipy.stats
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
                    scipy.stats.f.cdf(f_stat, len(hist_trimmed)-1, len(sim_trimmed)-1),  # CORREGIDO: scipy.stats
                    1 - scipy.stats.f.cdf(f_stat, len(hist_trimmed)-1, len(sim_trimmed)-1)  # CORREGIDO: scipy.stats
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
                ks_stat, ks_p = scipy.stats.ks_2samp(hist_trimmed, sim_trimmed)  # CORREGIDO: scipy.stats
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
                corr_coef, corr_p = scipy.stats.pearsonr(hist_trimmed, sim_trimmed)  # CORREGIDO: scipy.stats
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
                    'interpretation': f'Correlación {tests.get("correlation", {}).get("strength", "débil").lower()} entre histórico y simulado'
                }
            except Exception as e:
                logger.warning(f"Error in correlation test: {e}")
            
            return tests
            
        except Exception as e:
            logger.error(f"Error performing statistical tests: {e}")
            return {}

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


    # AGREGAR ESTE NUEVO MÉTODO AL FINAL DE LA CLASE SimulateResultView:

    def _perform_ks_validation(self, simulation_instance, results_simulation, all_variables_extracted):
        """
        Realizar validación específica con pruebas Kolmogorov-Smirnov
        """
        try:
            logger.info("Starting Kolmogorov-Smirnov validation of simulation results")
            
            # Usar el servicio de validación para realizar pruebas KS
            ks_validation = self.validation_service.validate_distribution_consistency(
                simulation_instance, 
                results_simulation, 
                distribution_params=None
            )
            
            # Generar gráficos de validación KS
            ks_charts = self._generate_ks_validation_charts(ks_validation, all_variables_extracted)
            ks_validation['ks_charts'] = ks_charts
            
            # Log resultados importantes
            summary = ks_validation.get('summary', {})
            logger.info(f"KS Validation Summary: {summary.get('passed_tests', 0)}/{summary.get('total_tests', 0)} tests passed")
            logger.info(f"Overall validity: {summary.get('overall_validity', False)}")
            
            return ks_validation
            
        except Exception as e:
            logger.error(f"Error in KS validation: {str(e)}")
            return {
                'summary': {'total_tests': 0, 'passed_tests': 0, 'overall_validity': False},
                'alerts': [{'type': 'ERROR', 'message': f'Error en validación KS: {str(e)}'}],
                'ks_tests': {},
                'confidence_intervals': {},
                'reliability_report': {},
                'distribution_analysis': {}
            }

    def _generate_ks_validation_charts(self, ks_validation, all_variables_extracted):
        """
        Generar gráficos específicos para la validación KS
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            import numpy as np
            from scipy import stats
            import base64
            from io import BytesIO
            
            charts = {}
            
            # 1. Gráfico Q-Q plot para distribuciones
            ks_tests = ks_validation.get('ks_tests', {})
            
            if 'demand' in ks_tests:
                demand_chart = self._create_distribution_comparison_chart(ks_tests['demand'])
                if demand_chart:
                    charts['demand_distribution'] = demand_chart
            
            # 2. Gráfico de intervalos de confianza
            confidence_intervals = ks_validation.get('confidence_intervals', {})
            if confidence_intervals:
                ci_chart = self._create_confidence_intervals_chart(confidence_intervals)
                if ci_chart:
                    charts['confidence_intervals'] = ci_chart
            
            # 3. Gráfico de consistencia temporal
            distribution_analysis = ks_validation.get('distribution_analysis', {})
            if distribution_analysis.get('temporal_stability'):
                temporal_chart = self._create_temporal_stability_chart(distribution_analysis)
                if temporal_chart:
                    charts['temporal_stability'] = temporal_chart
            
            # 4. Dashboard de validación KS
            reliability_chart = self._create_reliability_dashboard(ks_validation)
            if reliability_chart:
                charts['reliability_dashboard'] = reliability_chart
            
            logger.info(f"Generated {len(charts)} KS validation charts")
            return charts
            
        except Exception as e:
            logger.error(f"Error generating KS validation charts: {str(e)}")
            return {}

    def _create_distribution_comparison_chart(self, demand_ks_test):
        """Crear gráfico de comparación de distribuciones - CORREGIDO"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            from scipy import stats as scipy_stats  # IMPORTACIÓN LOCAL EXPLÍCITA
            import base64
            from io import BytesIO
            
            distributions_tested = demand_ks_test.get('distributions_tested', {})
            if not distributions_tested:
                return None
            
            # Crear figura con subplots
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('Validación de Distribuciones - Prueba Kolmogorov-Smirnov', fontsize=16, fontweight='bold')
            
            # Datos de muestra (simulados)
            sample_data = np.random.normal(100, 20, 1000)  # Placeholder - usar datos reales
            
            # Subplot 1: Histograma con distribuciones ajustadas
            ax1.hist(sample_data, bins=30, density=True, alpha=0.7, color='lightblue', edgecolor='black')
            
            x = np.linspace(sample_data.min(), sample_data.max(), 100)
            colors = ['red', 'green', 'orange', 'purple']
            
            for i, (dist_name, dist_info) in enumerate(distributions_tested.items()):
                if 'params' in dist_info and dist_info['passes_test']:
                    if dist_name == 'normal':
                        y = scipy_stats.norm.pdf(x, loc=dist_info['params'][0], scale=dist_info['params'][1])  # CORREGIDO
                        ax1.plot(x, y, color=colors[i % len(colors)], linewidth=2, 
                                label=f"{dist_name.title()} (p={dist_info['p_value']:.3f})")
            
            ax1.set_title('Distribuciones Ajustadas vs Datos Observados')
            ax1.set_xlabel('Valor')
            ax1.set_ylabel('Densidad')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Subplot 2: P-values de pruebas KS
            dist_names = list(distributions_tested.keys())
            p_values = [distributions_tested[name]['p_value'] for name in dist_names]
            colors_bar = ['green' if p > 0.05 else 'orange' if p > 0.01 else 'red' for p in p_values]
            
            bars = ax2.bar(dist_names, p_values, color=colors_bar, alpha=0.7, edgecolor='black')
            ax2.axhline(y=0.05, color='red', linestyle='--', label='Umbral α=0.05')
            ax2.set_title('P-values de Pruebas Kolmogorov-Smirnov')
            ax2.set_ylabel('P-value')
            ax2.set_xlabel('Distribución')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # Agregar valores en las barras
            for bar, p_val in zip(bars, p_values):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + 0.005,
                        f'{p_val:.3f}', ha='center', va='bottom', fontweight='bold')
            
            # Subplot 3: Q-Q plot para mejor distribución
            best_dist = max(distributions_tested.items(), key=lambda x: x[1]['p_value'])[0]
            best_info = distributions_tested[best_dist]
            
            if best_dist == 'normal' and 'params' in best_info:
                theoretical_quantiles = scipy_stats.norm.ppf(  # CORREGIDO
                    np.linspace(0.01, 0.99, len(sample_data)), 
                    loc=best_info['params'][0], 
                    scale=best_info['params'][1]
                )
                sample_quantiles = np.sort(sample_data)
                
                ax3.scatter(theoretical_quantiles, sample_quantiles, alpha=0.6, color='blue', s=20)
                min_val = min(theoretical_quantiles.min(), sample_quantiles.min())
                max_val = max(theoretical_quantiles.max(), sample_quantiles.max())
                ax3.plot([min_val, max_val], [min_val, max_val], 'r-', linewidth=2, label='Línea ideal')
                
                ax3.set_title(f'Q-Q Plot: {best_dist.title()} (Mejor Ajuste)')
                ax3.set_xlabel('Cuantiles Teóricos')
                ax3.set_ylabel('Cuantiles Observados')
                ax3.legend()
                ax3.grid(True, alpha=0.3)
            
            # Subplot 4: Resumen de validación
            ax4.axis('off')
            
            # Crear tabla de resumen
            summary_data = []
            for dist_name, dist_info in distributions_tested.items():
                status = "✓ Pasa" if dist_info['passes_test'] else "✗ Falla"
                summary_data.append([
                    dist_name.title(),
                    f"{dist_info['p_value']:.4f}",
                    status
                ])
            
            table = ax4.table(cellText=summary_data,
                             colLabels=['Distribución', 'P-value', 'Estado'],
                             cellLoc='center',
                             loc='center',
                             bbox=[0.1, 0.3, 0.8, 0.6])
            
            table.auto_set_font_size(False)
            table.set_fontsize(12)
            table.scale(1, 2)
            
            # Colorear filas según resultado
            for i, (_, dist_info) in enumerate(distributions_tested.items()):
                if dist_info['passes_test']:
                    table[(i+1, 2)].set_facecolor('#90EE90')  # Verde claro
                else:
                    table[(i+1, 2)].set_facecolor('#FFB6C1')  # Rosa claro
            
            ax4.set_title('Resumen de Validación KS', fontsize=14, fontweight='bold', pad=20)
            
            plt.tight_layout()
            
            # Convertir a base64
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            return chart_base64
            
        except Exception as e:
            logger.error(f"Error creating distribution comparison chart: {str(e)}")
            return None

    def _create_confidence_intervals_chart(self, confidence_intervals):
        """Crear gráfico de intervalos de confianza"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            import base64
            from io import BytesIO
            
            # Filtrar intervalos de demanda
            demand_intervals = {k: v for k, v in confidence_intervals.items() if 'demand' in k}
            variable_intervals = {k: v for k, v in confidence_intervals.items() if 'demand' not in k}
            
            if not demand_intervals and not variable_intervals:
                return None
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
            fig.suptitle('Intervalos de Confianza para Proyecciones', fontsize=16, fontweight='bold')
            
            # Subplot 1: Intervalos de confianza para demanda
            if demand_intervals:
                conf_levels = []
                means = []
                lower_bounds = []
                upper_bounds = []
                margins = []
                
                for key, interval in demand_intervals.items():
                    conf_level = int(key.split('_')[1])
                    conf_levels.append(f"{conf_level}%")
                    means.append(interval['mean'])
                    lower_bounds.append(interval['lower_bound'])
                    upper_bounds.append(interval['upper_bound'])
                    margins.append(interval['margin_error'])
                
                x_pos = np.arange(len(conf_levels))
                
                # Gráfico de barras de error
                ax1.errorbar(x_pos, means, yerr=margins, fmt='o', linewidth=2, markersize=8, 
                           capsize=5, capthick=2, ecolor='red', markerfacecolor='blue', 
                           markeredgecolor='darkblue', markeredgewidth=2)
                
                # Agregar área sombreada para intervalos
                for i, (mean, lower, upper) in enumerate(zip(means, lower_bounds, upper_bounds)):
                    ax1.fill_between([i-0.2, i+0.2], [lower, lower], [upper, upper], 
                                   alpha=0.3, color='lightblue')
                
                ax1.set_xticks(x_pos)
                ax1.set_xticklabels(conf_levels)
                ax1.set_title('Intervalos de Confianza - Demanda Promedio')
                ax1.set_xlabel('Nivel de Confianza')
                ax1.set_ylabel('Demanda (L)')
                ax1.grid(True, alpha=0.3)
                
                # Agregar valores en el gráfico
                for i, (mean, margin) in enumerate(zip(means, margins)):
                    ax1.text(i, mean + margin + (max(means) * 0.02), 
                           f'{mean:.1f} ± {margin:.1f}', 
                           ha='center', va='bottom', fontweight='bold')
            
            # Subplot 2: Intervalos para variables clave
            if variable_intervals:
                var_names = []
                var_means = []
                var_margins = []
                
                for key, interval in variable_intervals.items():
                    if '95' in key:  # Solo intervalos de 95%
                        var_name = interval.get('variable', key.split('_')[0])
                        var_names.append(var_name)
                        var_means.append(interval['mean'])
                        var_margins.append(interval['margin_error'])
                
                if var_names:
                    x_pos = np.arange(len(var_names))
                    
                    bars = ax2.bar(x_pos, var_means, yerr=var_margins, capsize=5, 
                                 alpha=0.7, color='lightgreen', edgecolor='darkgreen', 
                                 linewidth=1.5, error_kw={'elinewidth': 2, 'ecolor': 'red'})
                    
                    ax2.set_xticks(x_pos)
                    ax2.set_xticklabels(var_names, rotation=45, ha='right')
                    ax2.set_title('Intervalos de Confianza (95%) - Variables Clave')
                    ax2.set_xlabel('Variable')
                    ax2.set_ylabel('Valor')
                    ax2.grid(True, alpha=0.3, axis='y')
                    
                    # Agregar valores en las barras
                    for i, (bar, mean, margin) in enumerate(zip(bars, var_means, var_margins)):
                        height = bar.get_height()
                        ax2.text(bar.get_x() + bar.get_width()/2., height + margin + (max(var_means) * 0.02),
                               f'{mean:.1f}', ha='center', va='bottom', fontweight='bold')
            
            plt.tight_layout()
            
            # Convertir a base64
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            return chart_base64
            
        except Exception as e:
            logger.error(f"Error creating confidence intervals chart: {str(e)}")
            return None

    def _create_temporal_stability_chart(self, distribution_analysis):
        """Crear gráfico de estabilidad temporal"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            import base64
            from io import BytesIO
            
            temporal_stability = distribution_analysis.get('temporal_stability', {})
            distribution_drift = distribution_analysis.get('distribution_drift', {})
            
            if not temporal_stability:
                return None
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            fig.suptitle('Análisis de Estabilidad Temporal de Distribuciones', fontsize=16, fontweight='bold')
            
            # Subplot 1: P-values de comparaciones temporales
            comparisons = list(temporal_stability.keys())
            p_values = [temporal_stability[comp]['p_value'] for comp in comparisons]
            similarity = [temporal_stability[comp]['distributions_similar'] for comp in comparisons]
            
            colors = ['green' if sim else 'red' for sim in similarity]
            
            bars = ax1.bar(range(len(comparisons)), p_values, color=colors, alpha=0.7, edgecolor='black')
            ax1.axhline(y=0.05, color='red', linestyle='--', linewidth=2, label='Umbral α=0.05')
            
            ax1.set_xticks(range(len(comparisons)))
            ax1.set_xticklabels([comp.replace('window_', 'W').replace('_vs_', ' vs W') 
                               for comp in comparisons], rotation=45, ha='right')
            ax1.set_title('Comparaciones de Estabilidad Temporal (KS Test)')
            ax1.set_xlabel('Ventanas Comparadas')
            ax1.set_ylabel('P-value')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Agregar valores en las barras
            for bar, p_val in zip(bars, p_values):
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                        f'{p_val:.3f}', ha='center', va='bottom', fontweight='bold')
            
            # Subplot 2: Drift de distribución
            if distribution_drift:
                initial_mean = distribution_drift.get('initial_mean', 0)
                final_mean = distribution_drift.get('final_mean', 0)
                drift_pct = distribution_drift.get('relative_drift_pct', 0)
                
                # Crear gráfico de drift
                periods = ['Período Inicial', 'Período Final']
                means = [initial_mean, final_mean]
                
                bars = ax2.bar(periods, means, color=['lightblue', 'lightcoral'], 
                             alpha=0.7, edgecolor='black', linewidth=1.5)
                
                # Agregar flecha indicando drift
                if abs(drift_pct) > 1:  # Solo si hay drift significativo
                    arrow_props = dict(arrowstyle='->', connectionstyle='arc3', 
                                     color='red' if drift_pct > 0 else 'green', linewidth=2)
                    ax2.annotate('', xy=(1, final_mean), xytext=(0, initial_mean), arrowprops=arrow_props)
                    
                    # Agregar texto del drift
                    mid_y = (initial_mean + final_mean) / 2
                    ax2.text(0.5, mid_y, f'Drift: {drift_pct:+.1f}%', 
                           ha='center', va='center', fontweight='bold', 
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
                
                ax2.set_title('Drift de la Media Temporal')
                ax2.set_ylabel('Media de la Distribución')
                ax2.grid(True, alpha=0.3, axis='y')
                
                # Agregar valores en las barras
                for bar, mean in zip(bars, means):
                    height = bar.get_height()
                    ax2.text(bar.get_x() + bar.get_width()/2., height + (max(means) * 0.02),
                           f'{mean:.1f}', ha='center', va='bottom', fontweight='bold')
            
            plt.tight_layout()
            
            # Convertir a base64
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            return chart_base64
            
        except Exception as e:
            logger.error(f"Error creating temporal stability chart: {str(e)}")
            return None

    def _create_reliability_dashboard(self, ks_validation):
        """Crear dashboard de confiabilidad"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            import base64
            from io import BytesIO
            
            summary = ks_validation.get('summary', {})
            reliability_report = ks_validation.get('reliability_report', {})
            
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle('Dashboard de Confiabilidad - Validación Kolmogorov-Smirnov', 
                        fontsize=18, fontweight='bold')
            
            # Subplot 1: Score de confiabilidad (gauge)
            reliability_score = reliability_report.get('reliability_score', 0)
            
            # Crear gauge chart
            theta = np.linspace(0, np.pi, 100)
            r = np.ones_like(theta)
            
            # Colores por nivel de confiabilidad
            if reliability_score >= 90:
                color = 'green'
            elif reliability_score >= 75:
                color = 'orange'
            else:
                color = 'red'
            
            ax1 = plt.subplot(2, 2, 1, projection='polar')
            ax1.fill_between(theta, 0, r, alpha=0.3, color='lightgray')
            
            # Llenar según el score
            score_theta = np.linspace(0, np.pi * (reliability_score / 100), 50)
            score_r = np.ones_like(score_theta)
            ax1.fill_between(score_theta, 0, score_r, alpha=0.7, color=color)
            
            ax1.set_theta_zero_location('W')
            ax1.set_theta_direction(1)
            ax1.set_thetagrids([0, 45, 90, 135, 180], ['100%', '75%', '50%', '25%', '0%'])
            ax1.set_ylim(0, 1)
            ax1.set_rticks([])
            ax1.set_title(f'Score de Confiabilidad\n{reliability_score:.1f}%', 
                         fontsize=14, fontweight='bold', pad=20)
            
            # Subplot 2: Resumen de tests
            ax2 = plt.subplot(2, 2, 2)
            
            total_tests = summary.get('total_tests', 0)
            passed_tests = summary.get('passed_tests', 0)
            failed_tests = total_tests - passed_tests
            
            if total_tests > 0:
                sizes = [passed_tests, failed_tests]
                labels = [f'Pasaron ({passed_tests})', f'Fallaron ({failed_tests})']
                colors = ['green', 'red']
                explode = (0.05, 0.05)
                
                wedges, texts, autotexts = ax2.pie(sizes, labels=labels, colors=colors, 
                                                  autopct='%1.1f%%', explode=explode,
                                                  shadow=True, startangle=90)
                
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
            else:
                ax2.text(0.5, 0.5, 'Sin datos de tests', ha='center', va='center', 
                        transform=ax2.transAxes, fontsize=14)
            
            ax2.set_title('Distribución de Tests KS', fontsize=14, fontweight='bold')
            
            # Subplot 3: Nivel de certificación
            ax3 = plt.subplot(2, 2, 3)
            ax3.axis('off')
            
            certification_status = reliability_report.get('certification_status', 'NOT_CERTIFIED')
            reliability_level = reliability_report.get('reliability_level', 'Desconocido')
            
            # Crear "certificado"
            cert_colors = {
                'CERTIFIED': '#90EE90',
                'CONDITIONAL': '#FFD700', 
                'NOT_CERTIFIED': '#FFB6C1'
            }
            
            cert_color = cert_colors.get(certification_status, '#FFFFFF')
            
            # Crear rectángulo del certificado
            rect = plt.Rectangle((0.1, 0.2), 0.8, 0.6, facecolor=cert_color, 
                               edgecolor='black', linewidth=2)
            ax3.add_patch(rect)
            
            # Texto del certificado
            ax3.text(0.5, 0.7, 'CERTIFICACIÓN DE', ha='center', va='center', 
                    fontsize=12, fontweight='bold', transform=ax3.transAxes)
            ax3.text(0.5, 0.6, 'CONFIABILIDAD', ha='center', va='center', 
                    fontsize=14, fontweight='bold', transform=ax3.transAxes)
            ax3.text(0.5, 0.45, certification_status.replace('_', ' '), ha='center', va='center', 
                    fontsize=16, fontweight='bold', transform=ax3.transAxes)
            ax3.text(0.5, 0.35, f'Nivel: {reliability_level}', ha='center', va='center', 
                    fontsize=12, transform=ax3.transAxes)
            ax3.text(0.5, 0.25, f'Score: {reliability_score:.1f}/100', ha='center', va='center', 
                    fontsize=12, transform=ax3.transAxes)
            
            # Subplot 4: Componentes analizados
            ax4 = plt.subplot(2, 2, 4)
            
            component_analysis = reliability_report.get('component_analysis', {})
            if component_analysis:
                components = list(component_analysis.keys())
                reliabilities = []
                
                for comp_key, comp_data in component_analysis.items():
                    rel = comp_data.get('reliability', 'unknown')
                    if rel == 'high':
                        reliabilities.append(3)
                    elif rel == 'medium':
                        reliabilities.append(2)
                    elif rel == 'low':
                        reliabilities.append(1)
                    else:
                        reliabilities.append(0)
                
                colors_comp = ['green' if r == 3 else 'orange' if r == 2 else 'red' if r == 1 else 'gray' 
                              for r in reliabilities]
                
                bars = ax4.barh(components, reliabilities, color=colors_comp, alpha=0.7, edgecolor='black')
                
                ax4.set_xlim(0, 3)
                ax4.set_xticks([0, 1, 2, 3])
                ax4.set_xticklabels(['N/A', 'Baja', 'Media', 'Alta'])
                ax4.set_title('Confiabilidad por Componente')
                ax4.set_xlabel('Nivel de Confiabilidad')
                ax4.grid(True, alpha=0.3, axis='x')
                
                # Agregar etiquetas
                for i, (bar, rel) in enumerate(zip(bars, reliabilities)):
                    width = bar.get_width()
                    label = ['N/A', 'Baja', 'Media', 'Alta'][rel]
                    ax4.text(width + 0.05, bar.get_y() + bar.get_height()/2, 
                           label, ha='left', va='center', fontweight='bold')
            else:
                ax4.text(0.5, 0.5, 'Sin análisis de componentes', ha='center', va='center', 
                        transform=ax4.transAxes)
                ax4.set_title('Análisis de Componentes')
            
            plt.tight_layout()
            
            # Convertir a base64
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            return chart_base64
            
        except Exception as e:
            logger.error(f"Error creating reliability dashboard: {str(e)}")
            return None



def simulate_result_simulation_view(request, simulation_id):
    """Function-based view wrapper for compatibility"""
    view = SimulateResultView.as_view()
    return view(request, simulation_id=simulation_id)