# views/simulation_views.py
from datetime import datetime, timedelta
import json
import logging
import statistics
from typing import Dict, List, Optional, Any

import numpy as np
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.db.models import Prefetch, Q, Count, Avg, Sum, Exists, OuterRef
from django.http import HttpResponseRedirect, HttpResponseNotFound, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView, View

from ..forms import SimulationForm
from ..models import Simulation, ResultSimulation, Demand
from ..services.simulation_service import SimulationService
from ..services.statistical_service import StatisticalService
from ..utils.chart_generators import ChartGenerator
from ..validators.simulation_validators import SimulationValidator
# from ..tasks import execute_simulation_async  # Comentado si no usas Celery

from business.models import Business
from finance.models import FinanceRecommendation, FinanceRecommendationSimulation
from product.models import Product, Area
from questionary.models import QuestionaryResult, Questionary, Answer, Question
from variable.models import Variable, Equation, EquationResult

logger = logging.getLogger(__name__)


class AppsView(LoginRequiredMixin, TemplateView):
    """Base view for simulation app"""
    template_name = 'simulate/apps.html'


class SimulateShowView(LoginRequiredMixin, View):
    """Main simulation configuration and execution view"""
    
    def get(self, request, *args, **kwargs):
        """Handle GET requests for simulation setup"""
        started = request.session.get('started', False)
        
        # Check if questionary parameters are present instead of 'select'
        if 'selected_questionary_result' in request.GET:
            return self._handle_questionary_selection(request)
        
        if not started:
            return self._handle_initial_view(request)
        else:
            return self._handle_simulation_execution(request)
    
    def post(self, request, *args, **kwargs):
        """Handle POST requests for simulation actions"""
        if 'start' in request.POST:
            return self._handle_simulation_start(request)
        elif 'cancel' in request.POST:
            return self._handle_simulation_cancel(request)
        
        return redirect('simulate:simulate.show')
    
    def _get_user_data(self, request):
        """Get user's businesses and products with optimized queries"""
        cache_key = f"user_data_{request.user.id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        businesses = Business.objects.filter(
            is_active=True,
            fk_user=request.user
        ).prefetch_related('fk_business_product')
        
        products = Product.objects.filter(
            is_active=True,
            fk_business__in=businesses
        ).select_related('fk_business')
        
        data = {
            'businesses': businesses,
            'products': products
        }
        
        cache.set(cache_key, data, 300)  # Cache for 5 minutes
        return data
    
    def _handle_questionary_selection(self, request):
        """Handle questionary selection and statistical analysis"""
        try:
            # Get form data
            selected_questionary_result_id = request.GET.get('selected_questionary_result', 0)
            selected_quantity_time = request.GET.get('selected_quantity_time', 0)
            selected_unit_time = request.GET.get('selected_unit_time', 0)
            
            # Validate inputs
            if not selected_questionary_result_id:
                messages.error(request, "Por favor seleccione un cuestionario válido.")
                return redirect('simulate:simulate.show')
            
            # Store in session
            request.session['selected_questionary_result_id'] = selected_questionary_result_id
            
            # Get questionary with optimized query
            questionary_result_instance = get_object_or_404(
                QuestionaryResult.objects.select_related(
                    'fk_questionary__fk_product__fk_business'
                ).prefetch_related(
                    Prefetch(
                        'fk_question_result_answer',
                        queryset=Answer.objects.select_related('fk_question__fk_variable')
                    )
                ),
                pk=selected_questionary_result_id
            )
            
            # Get related data
            context_data = self._prepare_questionary_context(
                request, questionary_result_instance,
                selected_quantity_time, selected_unit_time
            )
            
            return render(request, 'simulate/simulate-init.html', context_data)
            
        except Exception as e:
            logger.error(f"Error in questionary selection: {str(e)}")
            messages.error(request, "Error al procesar el cuestionario. Por favor intente nuevamente.")
            return redirect('simulate:simulate.show')
    
    def _prepare_questionary_context(self, request, questionary_result_instance,
                               selected_quantity_time, selected_unit_time):
        """Prepare context data for questionary view"""
        user_data = self._get_user_data(request)
        product_instance = questionary_result_instance.fk_questionary.fk_product
        
        # Get areas with prefetch
        areas = Area.objects.filter(
            is_active=True,
            fk_product=product_instance
        ).prefetch_related(
            Prefetch(
                'area_equation',
                queryset=Equation.objects.filter(is_active=True).select_related(
                    'fk_variable1', 'fk_variable2', 'fk_variable3'
                )
            )
        ).order_by('id')
        
        # Get questionnaires
        questionnaires_result = QuestionaryResult.objects.filter(
            is_active=True,
            fk_questionary__fk_product__in=user_data['products']
        ).select_related(
            'fk_questionary__fk_product'
        ).order_by('-date_created')[:50]
        
        # Perform statistical analysis
        statistical_service = StatisticalService()
        analysis_results = statistical_service.analyze_demand_history(
            questionary_result_instance.id, request.user
        )
        
        # Get demand data with better error handling
        demand_data = analysis_results.get('demand_data', [])
        
        # Initialize chart generator
        chart_generator = ChartGenerator()
        
        # Generate charts only if we have valid data
        scatter_plot = None
        histogram_plot = None
        qq_plot = None
        
        if demand_data and len(demand_data) > 0:
            # Filter out None/invalid values
            clean_demand_data = [x for x in demand_data if x is not None and not np.isnan(float(x))]
            
            if clean_demand_data:
                labels = list(range(1, len(clean_demand_data) + 1))
                
                # Create chart data structure
                chart_data = {
                    'labels': labels,
                    'datasets': [{'label': 'Demanda Histórica', 'values': clean_demand_data}],
                    'x_label': 'Período',
                    'y_label': 'Demanda (Litros)'
                }
                
                try:
                    # Generate scatter plot
                    scatter_plot = chart_generator._generate_single_chart(
                        chart_data, 'scatter', 0, None, [], 
                        'Análisis de Dispersión de Demanda Histórica',
                        f'Distribución de {len(clean_demand_data)} puntos de demanda en el tiempo'
                    )
                except Exception as e:
                    logger.error(f"Error generating scatter plot: {str(e)}")
                
                try:
                    # Generate histogram
                    histogram_plot = chart_generator._generate_single_chart(
                        chart_data, 'histogram', 0, None, [], 
                        'Distribución de Frecuencias de Demanda',
                        'Análisis estadístico de la demanda histórica'
                    )
                except Exception as e:
                    logger.error(f"Error generating histogram: {str(e)}")
                
                # Generate Q-Q plot for distribution validation
                try:
                    best_distribution = analysis_results.get('best_distribution', 'normal')
                    distribution_params = analysis_results.get('distribution_params', {})
                    
                    if best_distribution and distribution_params:
                        qq_plot = chart_generator.generate_statistical_validation_chart(
                            clean_demand_data, 
                            best_distribution,
                            distribution_params
                        )
                except Exception as e:
                    logger.error(f"Error generating Q-Q plot: {str(e)}")
        
        # Prepare financial recommendations if available
        financial_recommendations = []
        if hasattr(questionary_result_instance, 'finance_recommendations'):
            financial_recommendations = questionary_result_instance.finance_recommendations.all()[:5]
        
        context = {
            'areas': areas,
            'form': SimulationForm(),
            'questionnaires_result': questionnaires_result,
            'questionary_result_instance': questionary_result_instance,
            'questionary_result_instance_id': questionary_result_instance.id,
            'selected_unit_time': selected_unit_time,
            'selected_quantity_time': selected_quantity_time,
            'image_data': scatter_plot,  # Scatter plot
            'image_data_histogram': histogram_plot,  # Histogram
            'image_data_qq': qq_plot,  # Q-Q plot
            'demand_history': clean_demand_data if 'clean_demand_data' in locals() else [],
            'financial_recommendations': financial_recommendations,
            **analysis_results  # Spread analysis results
        }
        
        # Add demand statistics if available
        if 'clean_demand_data' in locals() and clean_demand_data:
            context['demand_stats'] = {
                'count': len(clean_demand_data),
                'mean': np.mean(clean_demand_data),
                'std': np.std(clean_demand_data),
                'min': np.min(clean_demand_data),
                'max': np.max(clean_demand_data),
                'cv': np.std(clean_demand_data) / np.mean(clean_demand_data) if np.mean(clean_demand_data) > 0 else 0
            }
        
        return context
    
    def _handle_simulation_start(self, request): 
        """Handle simulation start"""
        try:
            # Get form data
            questionary_result_id = request.POST.get('fk_questionary_result')
            
            # Get demand history from questionary
            questionary_result = QuestionaryResult.objects.select_related(
                'fk_questionary'
            ).prefetch_related(
                'fk_question_result_answer__fk_question__fk_variable'
            ).get(id=questionary_result_id)

            # Find answer with historical demand
            demand_history = None
            for answer in questionary_result.all():
                if answer.fk_question_id.question == 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).':
                    demand_history = answer.value
                    break

            # Prepare form data
            form_data = {
                'fk_questionary_result': questionary_result_id,
                'quantity_time': request.POST.get('quantity_time'),
                'unit_time': request.POST.get('unit_time'),
                'demand_history': demand_history,
                'fk_fdp_id': request.POST.get('fk_fdp'),
            }
            print(f"Form data: {form_data}")  # Debugging line
            
            # Create simulation
            simulation_service = SimulationService()
            simulation_instance = simulation_service.create_simulation(form_data)
            
            # Store in session
            request.session['started'] = True
            request.session['simulation_started_id'] = simulation_instance.id
            
            messages.success(request, "Simulación iniciada correctamente.")
            
            # For async processing (if using Celery)
            # execute_simulation_async.delay(simulation_instance.id)
            
            return redirect(reverse('simulate:simulate.show'))
            
        except Exception as e:
            logger.error(f"Error starting simulation: {str(e)}")
            messages.error(request, f"Error al iniciar simulación: {str(e)}")
            return redirect('simulate:simulate.show')
    
    def _handle_simulation_cancel(self, request):
        """Handle simulation cancellation"""
        request.session['started'] = False
        request.session.pop('simulation_started_id', None)
        messages.info(request, "Simulación cancelada.")
        return redirect('simulate:simulate.show')
    
    def _handle_initial_view(self, request):
        """Handle initial view before simulation starts"""
        user_data = self._get_user_data(request)
        
        # Get recent questionnaires
        questionnaires_result = QuestionaryResult.objects.filter(
            is_active=True,
            fk_questionary__fk_product__in=user_data['products']
        ).select_related(
            'fk_questionary__fk_product'
        ).order_by('-date_created')[:20]
        
        context = {
            'started': False,
            'form': SimulationForm(),
            'questionnaires_result': questionnaires_result,
        }
        
        return render(request, 'simulate/simulate-init.html', context)
    
    def _handle_simulation_execution(self, request):
        """Handle the main simulation execution"""
        try:
            simulation_id = request.session.get('simulation_started_id')
            if not simulation_id:
                messages.error(request, "No se encontró simulación activa.")
                return redirect('simulate:simulate.show')
            
            simulation_instance = get_object_or_404(Simulation, pk=simulation_id)
            
            # Execute simulation
            simulation_service = SimulationService()
            simulation_service.execute_simulation(simulation_instance)
            
            # Clear session
            request.session['started'] = False
            
            messages.success(request, "Simulación completada exitosamente.")
            
            # Redirect to results
            return redirect('simulate:simulate.result', simulation_id=simulation_instance.id)
            
        except Exception as e:
            logger.error(f"Error executing simulation: {str(e)}")
            messages.error(request, "Error al ejecutar la simulación.")
            request.session['started'] = False
            return redirect('simulate:simulate.show')


class SimulateResultView(LoginRequiredMixin, View):
    """Display simulation results with charts and analysis"""
    
    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    def get(self, request, simulation_id, *args, **kwargs):
        """Display simulation results"""
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
            
            # Generate analysis data with historical demand
            context = self._prepare_results_context(
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
            # Find the answer with historical demand data
            for answer in simulation_instance.fk_questionary_result.fk_question_result_answer.all():
                if answer.fk_question.question == 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).':
                    # Parse the historical demand data
                    if answer.answer:
                        # Try to parse as JSON first
                        try:
                            import json
                            demand_data = json.loads(answer.answer)
                            if isinstance(demand_data, list):
                                return [float(x) for x in demand_data if x is not None]
                        except:
                            # Try to parse as comma-separated values
                            demand_str = answer.answer.strip()
                            if ',' in demand_str:
                                return [float(x.strip()) for x in demand_str.split(',') if x.strip()]
                            # Try space-separated
                            elif ' ' in demand_str:
                                return [float(x) for x in demand_str.split() if x]
                            # Try newline-separated
                            elif '\n' in demand_str:
                                return [float(x.strip()) for x in demand_str.split('\n') if x.strip()]
            
            return []
        except Exception as e:
            logger.error(f"Error extracting historical demand: {str(e)}")
            return []
    
    def _prepare_results_context(self, simulation_id, simulation_instance, 
                               results_simulation, historical_demand):
        """Prepare context data for results view"""
        # Generate charts and analysis with historical demand
        chart_generator = ChartGenerator()
        analysis_data = chart_generator.generate_all_charts(
            simulation_id, simulation_instance, list(results_simulation), historical_demand
        )
        
        # Get financial analysis
        simulation_service = SimulationService()
        financial_results = simulation_service.analyze_financial_results(
            simulation_id, analysis_data['totales_acumulativos']
        )
        
        # Calculate demand statistics
        demand_stats = self._calculate_demand_statistics(historical_demand, results_simulation)
        
        # Get related instances
        product_instance = simulation_instance.fk_questionary_result.fk_questionary.fk_product
        business_instance = product_instance.fk_business
        
        # Generate additional specialized charts
        if historical_demand and len(list(results_simulation)) > 0:
            simulated_demand = [float(r.demand_mean) for r in results_simulation]
            additional_charts = chart_generator.generate_demand_analysis_charts(
                historical_demand, simulated_demand
            )
        else:
            additional_charts = {}
        
        # Prepare context
        context = {
            'simulation_instance': simulation_instance,
            'results_simulation': results_simulation,
            'results': results_simulation,  # For compatibility
            'product_instance': product_instance,
            'business_instance': business_instance,
            'all_variables_extracted': analysis_data['all_variables_extracted'],
            'totales_acumulativos': analysis_data['totales_acumulativos'],
            'historical_demand': historical_demand,
            'demand_stats': demand_stats,
            **analysis_data['chart_images'],
            **additional_charts,
            **financial_results,
        }
        
        return context
    
    def _calculate_demand_statistics(self, historical_demand, results_simulation):
        """Calculate comprehensive demand statistics"""
        stats = {
            'historical': {},
            'simulated': {},
            'comparison': {}
        }
        
        # Historical demand statistics
        if historical_demand:
            stats['historical'] = {
                'mean': np.mean(historical_demand),
                'std': np.std(historical_demand),
                'min': np.min(historical_demand),
                'max': np.max(historical_demand),
                'median': np.median(historical_demand),
                'cv': np.std(historical_demand) / np.mean(historical_demand) if np.mean(historical_demand) > 0 else 0
            }
        
        # Simulated demand statistics
        simulated_values = [float(r.demand_mean) for r in results_simulation]
        if simulated_values:
            stats['simulated'] = {
                'mean': np.mean(simulated_values),
                'std': np.std(simulated_values),
                'min': np.min(simulated_values),
                'max': np.max(simulated_values),
                'median': np.median(simulated_values),
                'cv': np.std(simulated_values) / np.mean(simulated_values) if np.mean(simulated_values) > 0 else 0
            }
            
            # Comparison statistics
            if historical_demand:
                stats['comparison'] = {
                    'mean_diff': stats['simulated']['mean'] - stats['historical']['mean'],
                    'mean_diff_pct': ((stats['simulated']['mean'] - stats['historical']['mean']) / 
                                     stats['historical']['mean'] * 100) if stats['historical']['mean'] > 0 else 0,
                    'std_diff': stats['simulated']['std'] - stats['historical']['std'],
                    'cv_diff': stats['simulated']['cv'] - stats['historical']['cv']
                }
        
        return stats
    """Display simulation results with charts and analysis"""
    
    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    def get(self, request, simulation_id, *args, **kwargs):
        """Display simulation results"""
        try:
            # Get simulation with optimized queries
            simulation_instance = get_object_or_404(
                Simulation.objects.select_related(
                    'fk_questionary_result__fk_questionary__fk_product__fk_business',
                    'fk_fdp'
                ),
                pk=simulation_id
            )
            
            # Check permissions
            if not self._user_can_view_simulation(request.user, simulation_instance):
                messages.error(request, "No tiene permisos para ver esta simulación.")
                return redirect('simulate:simulate.show')
            
            # Get results with pagination
            results_simulation = self._get_paginated_results(request, simulation_id)
            
            # Generate analysis data
            context = self._prepare_results_context(
                simulation_id, simulation_instance, results_simulation
            )
            
            return render(request, 'simulate/simulate-result.html', context)
            
        except Exception as e:
            logger.error(f"Error displaying results: {str(e)}")
            messages.error(request, "Error al mostrar los resultados.")
            return redirect('simulate:simulate.show')
    
    def _user_can_view_simulation(self, user, simulation_instance):
        """Check if user has permission to view simulation"""
        business = simulation_instance.fk_questionary_result.fk_questionary.fk_product.fk_business
        return business.fk_user == user
    
    def _get_paginated_results(self, request, simulation_id):
        """Get paginated simulation results"""
        # Get page from request
        page = request.GET.get('page', 1)
        per_page = 50
        
        # Get results
        results = ResultSimulation.objects.filter(
            is_active=True,
            fk_simulation_id=simulation_id
        ).order_by('date')
        
        # Paginate
        paginator = Paginator(results, per_page)
        
        try:
            results_page = paginator.page(page)
        except PageNotAnInteger:
            results_page = paginator.page(1)
        except EmptyPage:
            results_page = paginator.page(paginator.num_pages)
        
        return results_page
    
    def _prepare_results_context(self, simulation_id, simulation_instance, results_simulation):
        """Prepare context data for results view"""
        # Generate charts and analysis
        chart_generator = ChartGenerator()
        analysis_data = chart_generator.generate_all_charts(
            simulation_id, simulation_instance, list(results_simulation)
        )
        
        # Get financial analysis
        simulation_service = SimulationService()
        financial_results = simulation_service.analyze_financial_results(
            simulation_id, analysis_data['totales_acumulativos']
        )
        
        # Get related instances
        product_instance = simulation_instance.fk_questionary_result.fk_questionary.fk_product
        business_instance = product_instance.fk_business
        
        # Prepare context
        context = {
            'simulation_instance': simulation_instance,
            'results_simulation': results_simulation,
            'results': results_simulation,  # For compatibility
            'product_instance': product_instance,
            'business_instance': business_instance,
            'all_variables_extracted': analysis_data['all_variables_extracted'],
            'totales_acumulativos': analysis_data['totales_acumulativos'],
            **analysis_data['chart_images'],
            **financial_results,
        }
        
        return context


class SimulateAddView(LoginRequiredMixin, View):
    """Add/create new simulation"""
    
    # estes se usa para manejar tanto la creación como la edición de simulaciones
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """Create new simulation"""
        try:
            # Get form data
            # Get questionary result for demand history
            questionary_result = QuestionaryResult.objects.select_related(
                'fk_questionary'
            ).prefetch_related(
                'fk_question_result_answer__fk_question__fk_variable'
            ).get(id=request.POST.get('fk_questionary_result'))
            
            # Find answer with historical demand 
            demand_history = None
            for answer in questionary_result.fk_question_result_answer.all():
                if answer.fk_question.question == 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).':
                    demand_history = answer.answer # Try answer_text instead of value
                    break

            form_data = {
                'fk_questionary_result': request.POST.get('fk_questionary_result'),
                'quantity_time': request.POST.get('quantity_time'), 
                'unit_time': request.POST.get('unit_time'),
                'demand_history': demand_history,
                'fk_fdp_id': request.POST.get('fk_fdp'),
            }
            
            # Create simulation
            simulation_service = SimulationService()
            simulation_instance = simulation_service.create_simulation(form_data)
            
            # For testing purposes - create random results
            if request.POST.get('test_mode'):
                simulation_service.create_random_result_simulations(simulation_instance)
            else:
                # Execute real simulation
                simulation_service.execute_simulation(simulation_instance)
            
            messages.success(request, "Simulación creada y ejecutada exitosamente.")
            
            return HttpResponseRedirect(
                reverse('simulate:simulate.result', args=(simulation_instance.id,))
            )
            
        except Exception as e:
            logger.error(f"Error creating simulation in SimulateAddView: {str(e)}")
            messages.error(request, f"Error al crear simulación: {str(e)}")
            return redirect('simulate:simulate.show')
    
    def get(self, request, *args, **kwargs):
        """Redirect GET requests to main view"""
        return redirect('simulate:simulate.show')


class SimulateListView(LoginRequiredMixin, View):
    """View to list all simulations for the current user"""

    def get(self, request, *args, **kwargs):
        # Get all businesses for the user
        businesses = Business.objects.filter(is_active=True, fk_user=request.user)
        
        # Get all products for those businesses
        products = Product.objects.filter(is_active=True, fk_business__in=businesses)
        
        # Get all simulations with filters
        simulations = Simulation.objects.filter(
            is_active=True,
            fk_questionary_result__fk_questionary__fk_product__in=products
        ).select_related(
            'fk_questionary_result__fk_questionary__fk_product__fk_business',
            'fk_fdp'
        ).annotate(
            has_results=Exists(
                ResultSimulation.objects.filter(
                    fk_simulation=OuterRef('pk'),
                    is_active=True
                )
            )
        )
        
        # Apply filters
        product_filter = request.GET.get('product')
        if product_filter:
            simulations = simulations.filter(
                fk_questionary_result__fk_questionary__fk_product_id=product_filter
            )
        
        status_filter = request.GET.get('status')
        if status_filter:
            if status_filter == 'completed':
                simulations = simulations.filter(has_results=True)
            elif status_filter == 'pending':
                simulations = simulations.filter(has_results=False)
        
        date_from = request.GET.get('date_from')
        if date_from:
            simulations = simulations.filter(date_created__gte=date_from)
        
        date_to = request.GET.get('date_to')
        if date_to:
            simulations = simulations.filter(date_created__lte=date_to)
        
        search = request.GET.get('search')
        if search:
            simulations = simulations.filter(
                Q(id__icontains=search) |
                Q(fk_questionary_result__fk_questionary__fk_product__name__icontains=search) |
                Q(fk_questionary_result__fk_questionary__fk_product__fk_business__name__icontains=search)
            )
        
        # Order by date
        simulations = simulations.order_by('-date_created')
        
        # Calculate statistics
        total_simulations = simulations.count()
        completed_simulations = simulations.filter(has_results=True).count()
        
        # Paginate results
        page = request.GET.get('page', 1)
        paginator = Paginator(simulations, 20)
        
        try:
            simulations_page = paginator.page(page)
        except PageNotAnInteger:
            simulations_page = paginator.page(1)
        except EmptyPage:
            simulations_page = paginator.page(paginator.num_pages)
        
        # Calculate average duration
        avg_duration = simulations.aggregate(
            avg_duration=Avg('quantity_time')
        )['avg_duration'] or 0
        
        # Add status to each simulation
        for sim in simulations_page:
            sim.status = 'completed' if sim.has_results else 'pending'
            sim.get_status_display = 'Completada' if sim.has_results else 'Pendiente'
        
        context = {
            'simulations': simulations_page,
            'page_obj': simulations_page,
            'is_paginated': simulations_page.has_other_pages(),
            'products': products,
            'total_simulations': total_simulations,
            'completed_simulations': completed_simulations,
            'processing_simulations': 0,  # Ya que no tenemos estado "processing"
            'avg_duration': avg_duration,
            'active_filters': self._get_active_filters(request),
        }
        
        return render(request, 'simulate/simulate-list.html', context)
    
    def _get_active_filters(self, request):
        """Get active filters for display"""
        filters = []
        
        if request.GET.get('product'):
            product = Product.objects.filter(id=request.GET.get('product')).first()
            if product:
                filters.append({
                    'label': 'Producto',
                    'value': product.name,
                    'remove_url': self._remove_filter_url(request, 'product')
                })
        
        if request.GET.get('status'):
            filters.append({
                'label': 'Estado',
                'value': request.GET.get('status'),
                'remove_url': self._remove_filter_url(request, 'status')
            })
        
        if request.GET.get('date_from'):
            filters.append({
                'label': 'Desde',
                'value': request.GET.get('date_from'),
                'remove_url': self._remove_filter_url(request, 'date_from')
            })
        
        if request.GET.get('date_to'):
            filters.append({
                'label': 'Hasta',
                'value': request.GET.get('date_to'),
                'remove_url': self._remove_filter_url(request, 'date_to')
            })
        
        return filters
    
    def _remove_filter_url(self, request, param_to_remove):
        """Generate URL with specific parameter removed"""
        params = request.GET.copy()
        if param_to_remove in params:
            del params[param_to_remove]
        return f"{request.path}?{params.urlencode()}"


# Helper view functions
def simulate_show_view(request):
    """Function-based view wrapper for compatibility"""
    view = SimulateShowView.as_view()
    return view(request)


def simulate_result_simulation_view(request, simulation_id):
    """Function-based view wrapper for compatibility"""
    view = SimulateResultView.as_view()
    return view(request, simulation_id=simulation_id)


def simulate_add_view(request):
    """Function-based view wrapper for compatibility"""
    view = SimulateAddView.as_view()
    return view(request)