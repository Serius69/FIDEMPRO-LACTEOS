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
from django.db.models import Prefetch, Q, Count, Avg, Sum
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
from ..tasks import execute_simulation_async  # For async processing if using Celery

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
        
        if 'select' in request.GET:
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
        ).prefetch_related('products')
        
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
                        'answer_set',
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
        ).order_by('-date_created')[:50]  # Limit to last 50
        
        # Perform statistical analysis
        statistical_service = StatisticalService()
        analysis_results = statistical_service.analyze_demand_history(
            questionary_result_instance.id, request.user
        )
        
        context = {
            'areas': areas,
            'form': SimulationForm(),
            'questionnaires_result': questionnaires_result,
            'questionary_result_instance': questionary_result_instance,
            'questionary_result_instance_id': questionary_result_instance.id,
            'selected_unit_time': selected_unit_time,
            'selected_quantity_time': selected_quantity_time,
            **analysis_results  # Spread analysis results
        }
        
        return context
    
    def _handle_simulation_start(self, request):
        """Handle simulation start"""
        try:
            # Validate form data
            form_data = {
                'fk_questionary_result': request.POST.get('fk_questionary_result'),
                'quantity_time': request.POST.get('quantity_time'),
                'unit_time': request.POST.get('unit_time'),
                'demand_history': request.POST.get('demand_history'),
                'fk_fdp_id': request.POST.get('fk_fdp'),
            }
            
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
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """Create new simulation"""
        try:
            # Get form data
            form_data = {
                'fk_questionary_result': request.POST.get('fk_questionary_result'),
                'quantity_time': request.POST.get('quantity_time'),
                'unit_time': request.POST.get('unit_time'),
                'demand_history': request.POST.get('demand_history'),
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
            logger.error(f"Error creating simulation: {str(e)}")
            messages.error(request, f"Error al crear simulación: {str(e)}")
            return redirect('simulate:simulate.show')
    
    def get(self, request, *args, **kwargs):
        """Redirect GET requests to main view"""
        return redirect('simulate:simulate.show')


class SimulateExportView(LoginRequiredMixin, View):
    """Export simulation results"""
    
    def get(self, request, simulation_id, format='pdf', *args, **kwargs):
        """Export simulation results in specified format"""
        try:
            # Get simulation
            simulation_instance = get_object_or_404(
                Simulation.objects.select_related(
                    'fk_questionary_result__fk_questionary__fk_product__fk_business'
                ),
                pk=simulation_id
            )
            
            # Check permissions
            business = simulation_instance.fk_questionary_result.fk_questionary.fk_product.fk_business
            if business.fk_user != request.user:
                return JsonResponse({'error': 'Unauthorized'}, status=403)
            
            if format == 'pdf':
                return self._export_pdf(simulation_instance)
            elif format == 'excel':
                return self._export_excel(simulation_instance)
            else:
                return JsonResponse({'error': 'Invalid format'}, status=400)
                
        except Exception as e:
            logger.error(f"Error exporting simulation: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    def _export_pdf(self, simulation_instance):
        """Export simulation results as PDF"""
        # This would use a library like ReportLab or WeasyPrint
        # For now, return a placeholder response
        return JsonResponse({
            'message': 'PDF export functionality to be implemented',
            'simulation_id': simulation_instance.id
        })
    
    def _export_excel(self, simulation_instance):
        """Export simulation results as Excel"""
        # This would use openpyxl or xlsxwriter
        # For now, return a placeholder response
        return JsonResponse({
            'message': 'Excel export functionality to be implemented',
            'simulation_id': simulation_instance.id
        })


class SimulateValidateView(LoginRequiredMixin, View):
    """Validate simulation data via AJAX"""
    
    def post(self, request, *args, **kwargs):
        """Validate simulation parameters"""
        try:
            # Get data
            data = json.loads(request.body)
            
            # Validate
            validator = SimulationValidator()
            errors = validator.validate_simulation_parameters(data)
            
            if errors:
                return JsonResponse({
                    'valid': False,
                    'errors': errors
                })
            
            return JsonResponse({
                'valid': True,
                'message': 'Datos válidos'
            })
            
        except Exception as e:
            return JsonResponse({
                'valid': False,
                'errors': [str(e)]
            }, status=400)


class SimulateChartsView(LoginRequiredMixin, View):
    """Get simulation charts data via AJAX"""
    
    def get(self, request, simulation_id, *args, **kwargs):
        """Get charts data for simulation"""
        try:
            # Verify permissions
            simulation = get_object_or_404(Simulation, pk=simulation_id)
            business = simulation.fk_questionary_result.fk_questionary.fk_product.fk_business
            
            if business.fk_user != request.user:
                return JsonResponse({'error': 'Unauthorized'}, status=403)
            
            # Get chart type
            chart_type = request.GET.get('type', 'all')
            
            # Generate charts data
            chart_generator = ChartGenerator()
            results = ResultSimulation.objects.filter(
                fk_simulation_id=simulation_id
            ).order_by('date')
            
            if chart_type == 'demand':
                chart_data = chart_generator._create_demand_chart_data(results)
            elif chart_type == 'financial':
                # Get financial charts data
                chart_data = {
                    'income_expenses': chart_generator._get_income_expenses_data(results),
                    'roi': chart_generator._get_roi_data(results),
                }
            else:
                # Return all charts data
                chart_data = chart_generator.generate_all_charts(
                    simulation_id, simulation, results
                )
            
            return JsonResponse({
                'success': True,
                'data': chart_data
            })
            
        except Exception as e:
            logger.error(f"Error getting charts: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


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