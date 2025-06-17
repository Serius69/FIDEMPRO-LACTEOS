# views/simulate_result_view.py
"""
Refactored simulation results view.
Focuses on daily comparisons and proper data visualization.
"""
import json
import logging
from typing import Dict, List, Any, Optional

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
        """Prepare comprehensive context data for results view"""
        
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
            # Create enhanced chart data with historical demand
            chart_data = chart_generator.create_enhanced_chart_data(
                list(results_simulation), historical_demand
            )
            
            # Generate main analysis charts
            analysis_data = chart_generator.generate_all_charts(
                simulation_id, simulation_instance, list(results_simulation), historical_demand
            )
            
            # Log what charts were generated
            logger.info(f"Charts generated: {list(analysis_data.get('chart_images', {}).keys())}")
            
            # Generate comparison chart: Historical vs Simulated
            comparison_chart = self._generate_comparison_chart(chart_demand, historical_demand, results_simulation)
            
            # Generate three-line validation chart
            three_line_validation = self._generate_three_line_validation_chart(
                historical_demand, results_simulation, simulation_instance
            )
            
            # Get financial analysis and recommendations
            financial_results = self._get_financial_analysis(
                financial_service, simulation_id, simulation_instance, analysis_data
            )
            
            # Calculate comprehensive statistics
            demand_stats = statistical_service._calculate_comprehensive_statistics(
                historical_demand, results_simulation
            )
            
            # Log accumulated totals for debugging
            logger.info(f"Accumulated totals variables: {list(analysis_data['totales_acumulativos'].keys())}")
            
            # Get validation results
            validation_results = self._get_validation_results(
                validation_service, simulation_id, simulation_instance, results_simulation, historical_demand
            )
            
            # Prepare base context
            context = self._build_base_context(
                simulation_instance, results_simulation, product_instance, business_instance,
                analysis_data, historical_demand, demand_stats, comparison_chart,
                financial_results, validation_results
            )
            
            # Add simulation_id to context
            context['simulation_id'] = simulation_id
            
            # Add chart_data to context
            context['chart_data'] = chart_data
            
            # Add three-line validation chart to context
            if three_line_validation:
                context['three_line_validation_chart'] = three_line_validation.get('chart')
                context['three_line_validation_metrics'] = three_line_validation.get('metrics', {})
                context['has_three_line_chart'] = True
            else:
                context['has_three_line_chart'] = False
            
            # Add realistic comparison statistics
            if historical_demand and results_simulation:
                comparison = statistical_service._calculate_realistic_comparison(historical_demand, results_simulation)
                context['realistic_comparison'] = comparison
            
            # Add model validation if variables are available
            if analysis_data.get('all_variables_extracted'):
                model_validation = self._add_model_validation(
                    validation_service, simulation_instance, results_simulation, analysis_data
                )
                context.update(model_validation)
            else:
                logger.warning("No extracted variables found for model validation")
                context['model_validation'] = None
            
            # Add daily validation
            daily_validation = self._add_daily_validation(
                validation_service, simulation_instance, results_simulation
            )
            context.update(daily_validation)
            
            # Add validation charts with three-line chart
            validation_charts = self._add_validation_charts(
                chart_generator, validation_results, results_simulation, analysis_data,
                three_line_validation
            )
            context.update(validation_charts)
            
            # Ensure all expected keys are present with default values
            context.setdefault('chart_images', {})
            context.setdefault('financial_recommendations', financial_results.get('financial_recommendations', []))
            context.setdefault('daily_validation_results', daily_validation.get('daily_validation_results', []))
            
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
                'three_line_validation_metrics': {}
            }

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
            financial_results = financial_service.analyze_financial_results(
                simulation_id, analysis_data['totales_acumulativos']
            )
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
        # Basic validation
        validation_results = validation_service.validate_simulation(simulation_id)
        
        # Model predictions validation
        prediction_validation_results = validation_service._validate_model_predictions(
            simulation_instance, results_simulation, historical_demand
        )
        
        # Combine validation results
        combined_validation = {
            'basic_validation': validation_results,
            'prediction_validation': prediction_validation_results
        }
        
        return combined_validation

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
            'validation_alerts': alerts_by_type,
            'validation_summary': basic_validation.get('summary', {}),
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
    
        # print(context)
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
        # Extract real values from questionnaire
        real_values = self._extract_real_values_from_questionnaire(simulation_instance)
        
        # Perform daily validation
        daily_validation_results = validation_service._validate_by_day(
            simulation_instance, list(results_simulation), real_values
        )
        
        # Generate daily validation charts
        daily_validation_charts = validation_service._generate_daily_validation_charts(
            daily_validation_results
        )
        
        # Calculate overall daily validation summary
        daily_validation_summary = validation_service._calculate_daily_validation_summary(
            daily_validation_results
        )
        
        return {
            'daily_validation_results': daily_validation_results,
            'daily_validation_charts': daily_validation_charts,
            'daily_validation_summary': daily_validation_summary
        }

    def _add_validation_charts(self, chart_generator, validation_results, results_simulation, 
                              analysis_data, three_line_validation=None):
        """Add validation charts to context including three-line chart"""
        validation_chart_context = {}
        
        # Generate basic validation charts
        basic_validation = validation_results.get('basic_validation', {})
        if basic_validation:
            validation_chart_context = chart_generator.generate_validation_charts_context(basic_validation)
        
        # Get variables for chart generation
        all_variables_extracted = analysis_data.get('all_variables_extracted', [])
        totales_acumulativos = analysis_data.get('totales_acumulativos', {})
        
        # Generate model validation charts if variables are available
        model_validation_charts = {}
        charts_context = {}
        
        # Generate validation charts with correct data
        if validation_results and 'by_variable' in validation_results:
            # Log for debug
            logger.info(f"all_variables_extracted type: {type(all_variables_extracted)}")
            if all_variables_extracted:
                logger.info(f"First item structure: {all_variables_extracted[0].keys()}")
            
            validation_charts = chart_generator._generate_validation_charts_for_variables(
                validation_results['by_variable'],
                results_simulation,
                all_variables_extracted
            )
            model_validation_charts = validation_charts
            charts_context = chart_generator.generate_validation_charts_context(
                {'validation_charts': validation_charts}
            )
        else:
            model_validation_charts = {}
            charts_context = {}
        
        # Generate endogenous variables charts
        endogenous_charts = chart_generator.generate_endogenous_variables_charts(
            all_variables_extracted,
            totales_acumulativos
        )
        
        # Generate additional analysis charts
        additional_charts = chart_generator.generate_additional_analysis_charts(
            all_variables_extracted,
            totales_acumulativos
        )
        
        # Prepare chart images including the three-line validation chart
        chart_images = validation_chart_context.get('chart_images', {})
        
        # Add three-line validation chart if available
        if three_line_validation and three_line_validation.get('chart'):
            chart_images['three_line_validation'] = three_line_validation['chart']
        
        # Add additional charts to context
        for key, chart in additional_charts.items():
            chart_images[f'additional_{key}'] = chart
        
        return {
            'validation_charts': validation_chart_context.get('charts', {}),
            'validation_chart_images': chart_images,
            'model_validation_charts': model_validation_charts,
            'charts_context': charts_context,
            'endogenous_charts': endogenous_charts,
            'additional_charts': additional_charts
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
        
        paginator = Paginator(results, 50)  # 50 results per page
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
        """Extract all variables from results for analysis"""
        all_variables = []
        
        for idx, result in enumerate(results):
            day_data = {
                'day': idx + 1,
                'date': result.date.isoformat() if result.date else None,
                'demand_mean': float(result.demand_mean),
                'demand_std': float(result.demand_std_deviation)
            }
            
            if hasattr(result, 'variables') and result.variables:
                for key, value in result.variables.items():
                    if not key.startswith('_'):
                        try:
                            day_data[key] = float(value) if isinstance(value, (int, float)) else value
                        except:
                            day_data[key] = 0.0
            
            all_variables.append(day_data)
        
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


def simulate_result_simulation_view(request, simulation_id):
    """Function-based view wrapper for compatibility"""
    view = SimulateResultView.as_view()
    return view(request, simulation_id=simulation_id)