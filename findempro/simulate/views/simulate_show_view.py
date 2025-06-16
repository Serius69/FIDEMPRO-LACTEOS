from django.views.generic import View, TemplateView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.cache import cache
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch

from ..forms import SimulationForm
from ..models import Simulation
from ..utils.simulation_core_utils import SimulationCore
from ..services.statistical_service import StatisticalService
from ..utils.chart_demand_utils import ChartDemand

from business.models import Business
from product.models import Product, Area
from questionary.models import QuestionaryResult, Answer
from variable.models import Equation
from finance.models import FinanceRecommendation

import numpy as np
import json
import logging

logger = logging.getLogger(__name__)

class AppsView(TemplateView):
    template_name = 'simulate/apps.html'

class SimulateShowView(LoginRequiredMixin, View):
    """Main simulation configuration and execution view"""
    
    def get(self, request, *args, **kwargs):
        """Handle GET requests for simulation setup"""
        started = request.session.get('started', False)
        
        # Check if questionary parameters are present
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
        elif 'simulate' in request.POST:
            return self._handle_simulation_execution(request)
        
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
        ).prefetch_related('fk_user')
        
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
            selected_quantity_time = request.GET.get('selected_quantity_time', 30)
            selected_unit_time = request.GET.get('selected_unit_time', 'days')
            
            # Validate inputs
            if not selected_questionary_result_id:
                messages.error(request, "Por favor seleccione un cuestionario válido.")
                return redirect('simulate:simulate.show')
            
            # Store in session
            request.session['selected_questionary_result_id'] = selected_questionary_result_id
            request.session['selected_quantity_time'] = selected_quantity_time
            request.session['selected_unit_time'] = selected_unit_time
            
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
        """Prepare context data for questionary view with complete analysis"""
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
                    'fk_variable1', 'fk_variable2', 'fk_variable3',
                    'fk_variable4', 'fk_variable5'
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
        
        # Get probability density functions
        fdps = product_instance.fk_business.probability_distributions.filter(
            is_active=True
        ).order_by('distribution_type')
        
        # Extract historical demand from answers
        demand_data = []
        for answer in questionary_result_instance.fk_question_result_answer.all():
            if answer.fk_question.question == 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).':
                try:
                    # Parse demand data
                    demand_str = answer.answer
                    if isinstance(demand_str, str):
                        # Try JSON parse first
                        try:
                            demand_data = json.loads(demand_str)
                        except:
                            # Try other parsing methods
                            demand_str = demand_str.replace('[', '').replace(']', '').strip()
                            if ',' in demand_str:
                                demand_data = [float(x.strip()) for x in demand_str.split(',') if x.strip()]
                            else:
                                demand_data = [float(x) for x in demand_str.split() if x]
                except Exception as e:
                    logger.error(f"Error parsing demand data: {e}")
                break
        
        # Perform statistical analysis
        statistical_service = StatisticalService()
        analysis_results = statistical_service.analyze_demand_history(
            questionary_result_instance.id, request.user
        )
        
        # Use parsed demand data if analysis doesn't have it
        if not analysis_results.get('demand_data') and demand_data:
            analysis_results['demand_data'] = demand_data
        
        # Generate charts for visualization
        chart_generator = ChartDemand()
        scatter_plot = None
        histogram_plot = None
        qq_plot = None
        
        if demand_data:
            clean_demand_data = [float(x) for x in demand_data if x is not None]
            
            if clean_demand_data:
                # Generate demand analysis charts
                scatter_plot = chart_generator.generate_demand_scatter_plot(clean_demand_data)
                histogram_plot = chart_generator.generate_demand_histogram(clean_demand_data)
                
                # Generate additional statistical charts
                # demand_charts = chart_generator.generate_demand_analysis_charts(clean_demand_data)
                # if 'box_plot' in demand_charts:
                #     qq_plot = demand_charts['box_plot']
        
        # Prepare financial recommendations
        financial_recommendations = []
        business = product_instance.fk_business
        recommendations = FinanceRecommendation.objects.filter(
            fk_business=business,
            is_active=True
        ).order_by('threshold_value')[:10]
        
        context = {
            'areas': areas,
            'form': SimulationForm(),
            'questionnaires_result': questionnaires_result,
            'questionary_result_instance': questionary_result_instance,
            'questionary_result_instance_id': questionary_result_instance.id,
            'selected_unit_time': selected_unit_time,
            'selected_quantity_time': selected_quantity_time,
            'fdps': fdps,
            'image_data': scatter_plot,
            'image_data_histogram': histogram_plot,
            'image_data_qq': qq_plot,
            'demand_history': clean_demand_data if 'clean_demand_data' in locals() else [],
            'financial_recommendations': recommendations,
            **analysis_results
        }
        
        # Add demand statistics
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
        """Handle simulation start with complete validation"""
        try:
            # Get form data
            questionary_result_id = request.POST.get('fk_questionary_result')
            quantity_time = request.POST.get('quantity_time', 30)
            unit_time = request.POST.get('unit_time', 'days')
            fdp_id = request.POST.get('fk_fdp')
            
            if not all([questionary_result_id, quantity_time, unit_time, fdp_id]):
                messages.error(request, "Faltan datos requeridos para la simulación.")
                return redirect('simulate:simulate.show')
            
            # Get demand history from questionary
            questionary_result = get_object_or_404(
                QuestionaryResult.objects.prefetch_related(
                    'fk_question_result_answer__fk_question__fk_variable'
                ),
                id=questionary_result_id
            )
            
            # Extract demand history
            demand_history = []
            for answer in questionary_result.fk_question_result_answer.all():
                if answer.fk_question.question == 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).':
                    try:
                        demand_str = answer.answer
                        if isinstance(demand_str, str):
                            try:
                                demand_history = json.loads(demand_str)
                            except:
                                demand_str = demand_str.replace('[', '').replace(']', '').strip()
                                if ',' in demand_str:
                                    demand_history = [float(x.strip()) for x in demand_str.split(',') if x.strip()]
                                else:
                                    demand_history = [float(x) for x in demand_str.split() if x]
                    except Exception as e:
                        logger.error(f"Error parsing demand history: {e}")
                    break
            
            if not demand_history:
                messages.error(request, "No se encontraron datos históricos de demanda.")
                return redirect('simulate:simulate.show')
            
            # Prepare simulation data
            form_data = {
                'fk_questionary_result': questionary_result_id,
                'quantity_time': int(quantity_time),
                'unit_time': unit_time,
                'demand_history': demand_history,
                'fk_fdp_id': int(fdp_id),
            }
            
            # Create simulation
            simulation_service = SimulationCore()
            simulation_instance = simulation_service.create_simulation(form_data)
            
            # Store in session
            request.session['started'] = True
            request.session['simulation_started_id'] = simulation_instance.id
            
            messages.success(request, "Simulación iniciada correctamente.")
            return redirect('simulate:simulate.show')
            
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
            simulation_service = SimulationCore()
            simulation_service.execute_simulation(simulation_instance)
            
            # Clear session
            request.session['started'] = False
            request.session.pop('simulation_started_id', None)
            
            messages.success(request, "Simulación completada exitosamente.")
            
            # Redirect to results
            return redirect('simulate:simulate.result', simulation_id=simulation_instance.id)
            
        except Exception as e:
            logger.error(f"Error executing simulation: {str(e)}")
            messages.error(request, "Error al ejecutar la simulación.")
            request.session['started'] = False
            return redirect('simulate:simulate.show')

# Function-based view wrapper
def simulate_show_view(request):
    view = SimulateShowView.as_view()
    return view(request)