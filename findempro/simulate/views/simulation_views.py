# views/simulation_views.py
from datetime import datetime, timedelta
import json
import statistics
import numpy as np

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import TemplateView

from ..forms import SimulationForm
from ..models import Simulation, ResultSimulation, Demand
from ..services.simulation_service import SimulationService
from ..services.statistical_service import StatisticalService
from ..utils.chart_generators import ChartGenerator
from ..validators.simulation_validators import SimulationValidator

from business.models import Business
from finance.models import FinanceRecommendation, FinanceRecommendationSimulation
from product.models import Product, Area
from questionary.models import QuestionaryResult, Questionary, Answer, Question
from variable.models import Variable, Equation, EquationResult


class AppsView(LoginRequiredMixin, TemplateView):
    pass


def simulate_show_view(request):
    """Main simulation view handling both GET and POST requests"""
    started = request.session.get('started', False)
    form = SimulationForm(request.POST)
    simulation_instance = None    
    selected_questionary_result_id = None
    questionary_result_instance = None
    areas = None
    
    businessess = Business.objects.filter(is_active=True, fk_user=request.user)
    products = Product.objects.filter(
        is_active=True,
        fk_business__in=businessess, 
        fk_business__fk_user=request.user
    )
    
    if request.method == 'GET' and 'select' in request.GET:
        return _handle_questionary_selection(request, form, products)
    
    if request.method == 'POST' and 'start' in request.POST:
        return _handle_simulation_start(request)
    
    if request.method == 'POST' and 'cancel' in request.POST:
        return _handle_simulation_cancel(request)
    
    if not started:
        return _handle_initial_view(request, form, products, selected_questionary_result_id)
    else:
        return _handle_simulation_execution(request)


def _handle_questionary_selection(request, form, products):
    """Handle questionary selection and statistical analysis"""
    selected_questionary_result_id = request.GET.get('selected_questionary_result', 0)
    selected_quantity_time = request.GET.get('selected_quantity_time', 0)
    selected_unit_time = request.GET.get('selected_unit_time', 0)
    
    request.session['selected_questionary_result_id'] = selected_questionary_result_id
    
    # Get questionary data
    questionary_result_instance = get_object_or_404(
        QuestionaryResult, 
        pk=selected_questionary_result_id
    )
    
    # Get related data
    answers = Answer.objects.order_by('id').filter(
        is_active=True, 
        fk_questionary_result_id=selected_questionary_result_id
    )
    
    equations_to_use = Question.objects.order_by('id').filter(
        is_active=True, 
        fk_questionary__fk_product__fk_business__fk_user=request.user, 
        fk_questionary_id=selected_questionary_result_id
    )
    
    questionnaires_result = QuestionaryResult.objects.filter(
        is_active=True,
        fk_questionary__fk_product__in=products,
        fk_questionary__fk_product__fk_business__fk_user=request.user
    ).order_by('-id')
    
    # Get product and areas
    product_instance = get_object_or_404(
        Product, 
        pk=questionary_result_instance.fk_questionary.fk_product.id
    )
    
    areas = Area.objects.order_by('id').filter(
        is_active=True, 
        fk_product__fk_business__fk_user=request.user,
        fk_product_id=product_instance.id
    )
    
    # Perform statistical analysis
    statistical_service = StatisticalService()
    analysis_results = statistical_service.analyze_demand_history(
        selected_questionary_result_id, request.user
    )
    
    context = {
        'areas': areas,
        'answers': answers,
        'image_data': analysis_results['scatter_image'],
        'image_data_histogram': analysis_results['histogram_image'],
        'selected_fdp': analysis_results['best_distribution'].id,
        'demand_mean': analysis_results['demand_mean'],
        'form': form,
        'demand_history': analysis_results['data_list'],
        'equations_to_use': equations_to_use,
        'questionnaires_result': questionnaires_result,
        'questionary_result_instance_id': questionary_result_instance.id,
        'questionary_result_instance': questionary_result_instance,
        'selected_unit_time': selected_unit_time,
        'selected_quantity_time': selected_quantity_time,
        'best_distribution': analysis_results['best_distribution'].get_distribution_type_display(),
        'best_ks_p_value': analysis_results['best_ks_p_value_floor'],
        'best_ks_statistic': analysis_results['best_ks_statistic_floor'],
    }
    
    return render(request, 'simulate/simulate-init.html', context)


def _handle_simulation_start(request):
    """Handle simulation start"""
    request.session['started'] = True
    
    # Get form data
    form_data = {
        'fk_questionary_result': request.POST.get('fk_questionary_result'),
        'quantity_time': request.POST.get('quantity_time'),
        'unit_time': request.POST.get('unit_time'),
        'demand_history': request.POST.get('demand_history'),
        'fk_fdp_id': request.POST.get('fk_fdp'),
    }
    
    # Create simulation instance
    simulation_service = SimulationService()
    simulation_instance = simulation_service.create_simulation(form_data)
    
    # Store simulation ID in session
    request.session['simulation_started_id'] = simulation_instance.id
    
    return redirect(reverse('simulate:simulate.show'))


def _handle_simulation_cancel(request):
    """Handle simulation cancellation"""
    request.session['selected'] = False
    return redirect('simulate:simulate.show')


def _handle_initial_view(request, form, products, selected_questionary_result_id):
    """Handle initial view before simulation starts"""
    try:
        if selected_questionary_result_id is None:
            questionnaires_result = QuestionaryResult.objects.filter(
                is_active=True, 
                fk_questionary__fk_product__in=products,
                fk_questionary__fk_product__fk_business__fk_user=request.user
            ).order_by('-id')
        else:
            # Handle pagination and other logic for selected questionary
            questionnaires_result, areas, questionary_result_instance = _get_questionary_data(
                request, products, selected_questionary_result_id
            )
        
        context = {
            'selected_questionary_result_id': selected_questionary_result_id,
            'started': False,
            'form': form,
            'areas': locals().get('areas'),
            'questionnaires_result': questionnaires_result,
            'questionary_result_instance': locals().get('questionary_result_instance'),
        }
        return render(request, 'simulate/simulate-init.html', context)
    
    except ObjectDoesNotExist:
        return HttpResponseNotFound("Object not found")


def _handle_simulation_execution(request):
    """Handle the main simulation execution"""
    simulation_instance = get_object_or_404(
        Simulation, 
        pk=request.session['simulation_started_id']
    )
    
    # Execute simulation
    simulation_service = SimulationService()
    simulation_service.execute_simulation(simulation_instance)
    
    request.session['started'] = False
    return render(request, 'simulate/simulate-result.html', {
        'simulation_instance_id': simulation_instance,
    })


def _get_questionary_data(request, products, selected_questionary_result_id):
    """Get questionary related data with pagination"""
    equations_to_use = Question.objects.order_by('id').filter(
        is_active=True, 
        fk_questionary__fk_product__fk_business__fk_user=request.user, 
        fk_questionary_id=selected_questionary_result_id
    )
    
    questionnaires_result = QuestionaryResult.objects.filter(
        is_active=True,
        fk_questionary__fk_product__in=products,
        fk_questionary__fk_product__fk_business__fk_user=request.user
    ).order_by('-id')
    
    questionary_result_instance = get_object_or_404(
        QuestionaryResult, 
        pk=selected_questionary_result_id
    )
    
    product_instance = get_object_or_404(
        Product, 
        pk=questionary_result_instance.fk_questionary.fk_product.id
    )
    
    areas = Area.objects.order_by('id').filter(
        is_active=True, 
        fk_product__fk_business__fk_user=request.user,
        fk_product=product_instance
    )
    
    # Pagination
    paginator = Paginator(equations_to_use, 10)
    page = request.GET.get('page')
    try:
        equations_to_use = paginator.page(page)
    except PageNotAnInteger:
        equations_to_use = paginator.page(1)
    except EmptyPage:
        equations_to_use = paginator.page(paginator.num_pages)
    
    return questionnaires_result, areas, questionary_result_instance


def simulate_result_simulation_view(request, simulation_id):
    """Display simulation results with charts and analysis"""
    # Get simulation data
    simulation_instance = get_object_or_404(Simulation, pk=simulation_id)
    results_simulation = ResultSimulation.objects.filter(
        is_active=True, 
        fk_simulation_id=simulation_id
    )
    
    # Generate charts and analysis
    chart_generator = ChartGenerator()
    analysis_data = chart_generator.generate_all_charts(
        simulation_id, simulation_instance, results_simulation
    )
    
    # Get financial analysis
    simulation_service = SimulationService()
    financial_results = simulation_service.analyze_financial_results(
        simulation_id, analysis_data['totales_acumulativos']
    )
    
    # Prepare context
    context = {
        **analysis_data['chart_images'],
        **financial_results,
        'simulation_instance': simulation_instance,
        'results_simulation': results_simulation,
        'all_variables_extracted': analysis_data['all_variables_extracted'],
        'totales_acumulativos': analysis_data['totales_acumulativos']
    }
    
    return render(request, 'simulate/simulate-result.html', context)


def simulate_add_view(request):
    """Add a new simulation (simplified version)"""
    if request.method == 'POST':
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
        
        # Create random results for testing
        simulation_service.create_random_result_simulations(simulation_instance)
        
        return HttpResponseRedirect(
            reverse('simulate:simulate.result', args=(simulation_instance.id,))
        )
    else:
        return render(request, 'simulate/simulate-init.html')