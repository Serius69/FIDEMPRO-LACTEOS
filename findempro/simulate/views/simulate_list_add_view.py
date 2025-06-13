from django.views.generic import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q, Count, Avg, Exists, OuterRef
from django.http import HttpResponseRedirect
from django.urls import reverse

from ..models import Simulation, ResultSimulation
from ..services.simulation_core import SimulationCore

from business.models import Business
from product.models import Product
from questionary.models import QuestionaryResult

import logging
import json

logger = logging.getLogger(__name__)

class SimulateAddView(LoginRequiredMixin, View):
    """Add/create new simulation with enhanced validation"""
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """Create new simulation"""
        try:
            # Get questionary result
            questionary_result_id = request.POST.get('fk_questionary_result')
            if not questionary_result_id:
                messages.error(request, "Debe seleccionar un cuestionario.")
                return redirect('simulate:simulate.show')
            
            questionary_result = get_object_or_404(
                QuestionaryResult.objects.prefetch_related(
                    'fk_question_result_answer__fk_question__fk_variable'
                ),
                id=questionary_result_id
            )
            
            # Extract demand history
            demand_history = None
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
            
            # Prepare form data
            form_data = {
                'fk_questionary_result': questionary_result_id,
                'quantity_time': int(request.POST.get('quantity_time', 30)),
                'unit_time': request.POST.get('unit_time', 'days'),
                'demand_history': demand_history,
                'fk_fdp_id': int(request.POST.get('fk_fdp')),
            }
            
            # Create and execute simulation
            simulation_service = SimulationCore()
            simulation_instance = simulation_service.create_simulation(form_data)
            
            # Execute simulation
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

class SimulateListView(LoginRequiredMixin, View):
    """View to list all simulations with enhanced filtering"""
    
    def get(self, request, *args, **kwargs):
        try:
            # Get user's businesses and products
            businesses = Business.objects.filter(
                is_active=True, 
                fk_user=request.user
            )
            products = Product.objects.filter(
                is_active=True, 
                fk_business__in=businesses
            )
            
            # Base query with annotations
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
                ),
                results_count=Count(
                    'results',
                    filter=Q(results__is_active=True)
                )
            )
            
            # Apply filters
            filters = self._apply_filters(request, simulations)
            simulations = filters['queryset']
            
            # Order by date
            simulations = simulations.order_by('-date_created')
            
            # Calculate statistics
            stats = self._calculate_statistics(simulations)
            
            # Paginate
            paginator = Paginator(simulations, 20)
            page = request.GET.get('page', 1)
            
            try:
                simulations_page = paginator.page(page)
            except PageNotAnInteger:
                simulations_page = paginator.page(1)
            except EmptyPage:
                simulations_page = paginator.page(paginator.num_pages)
            
            # Add display properties
            for sim in simulations_page:
                sim.status = 'completed' if sim.has_results else 'pending'
                sim.status_class = 'success' if sim.has_results else 'warning'
                sim.status_display = 'Completada' if sim.has_results else 'Pendiente'
            
            context = {
                'simulations': simulations_page,
                'page_obj': simulations_page,
                'is_paginated': simulations_page.has_other_pages(),
                'products': products,
                'active_filters': filters['active'],
                **stats
            }
            
            return render(request, 'simulate/simulate-list.html', context)
            
        except Exception as e:
            logger.error(f"Error in simulation list view: {str(e)}")
            messages.error(request, "Error al cargar la lista de simulaciones.")
            return render(request, 'simulate/simulate-list.html', {
                'simulations': [],
                'total_simulations': 0,
                'completed_simulations': 0,
                'pending_simulations': 0
            })
    
    def _apply_filters(self, request, queryset):
        """Apply filters to simulation queryset"""
        active_filters = []
        
        # Product filter
        product_filter = request.GET.get('product')
        if product_filter:
            queryset = queryset.filter(
                fk_questionary_result__fk_questionary__fk_product_id=product_filter
            )
            product = Product.objects.filter(id=product_filter).first()
            if product:
                active_filters.append({
                    'label': 'Producto',
                    'value': product.name,
                    'param': 'product',
                    'remove_url': self._remove_filter_url(request, 'product')
                })
        
        # Status filter
        status_filter = request.GET.get('status')
        if status_filter:
            if status_filter == 'completed':
                queryset = queryset.filter(has_results=True)
                active_filters.append({
                    'label': 'Estado',
                    'value': 'Completadas',
                    'param': 'status',
                    'remove_url': self._remove_filter_url(request, 'status')
                })
            elif status_filter == 'pending':
                queryset = queryset.filter(has_results=False)
                active_filters.append({
                    'label': 'Estado',
                    'value': 'Pendientes',
                    'param': 'status',
                    'remove_url': self._remove_filter_url(request, 'status')
                })
        
        # Date filters
        date_from = request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(date_created__gte=date_from)
            active_filters.append({
                'label': 'Desde',
                'value': date_from,
                'param': 'date_from',
                'remove_url': self._remove_filter_url(request, 'date_from')
            })
        
        date_to = request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(date_created__lte=date_to)
            active_filters.append({
                'label': 'Hasta',
                'value': date_to,
                'param': 'date_to',
                'remove_url': self._remove_filter_url(request, 'date_to')
            })
        
        # Search filter
        search = request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(id__icontains=search) |
                Q(fk_questionary_result__fk_questionary__fk_product__name__icontains=search) |
                Q(fk_questionary_result__fk_questionary__fk_product__fk_business__name__icontains=search)
            )
            active_filters.append({
                'label': 'Búsqueda',
                'value': search,
                'param': 'search',
                'remove_url': self._remove_filter_url(request, 'search')
            })
        
        return {
            'queryset': queryset,
            'active': active_filters
        }
    
    def _calculate_statistics(self, queryset):
        """Calculate simulation statistics"""
        total = queryset.count()
        completed = queryset.filter(has_results=True).count()
        pending = total - completed
        
        # Average statistics
        avg_duration = queryset.aggregate(
            avg_duration=Avg('quantity_time')
        )['avg_duration'] or 0
        
        avg_results = queryset.filter(has_results=True).aggregate(
            avg_results=Avg('results_count')
        )['avg_results'] or 0
        
        return {
            'total_simulations': total,
            'completed_simulations': completed,
            'pending_simulations': pending,
            'completion_rate': (completed / total * 100) if total > 0 else 0,
            'avg_duration': round(avg_duration, 1),
            'avg_results_per_simulation': round(avg_results, 1)
        }
    
    def _remove_filter_url(self, request, param_to_remove):
        """Generate URL with specific parameter removed"""
        params = request.GET.copy()
        if param_to_remove in params:
            del params[param_to_remove]
        return f"{request.path}?{params.urlencode()}"

def simulate_add_view(request):
    view = SimulateAddView.as_view()
    return view(request)

def simulate_list_view(request):
    view = SimulateListView.as_view()
    return view(request)