from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseServerError
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
import json

from simulate.models import ResultSimulation
from .models import FinancialDecision, FinanceRecommendation
from business.models import Business
from .forms import FinancialDecisionForm


class AppsView(LoginRequiredMixin, TemplateView):
    template_name = 'finance/apps.html'


@login_required
def finance_list_view(request):
    """
    Vista para listar decisiones financieras con funcionalidad de búsqueda y paginación
    """
    try:
        # Obtener parámetros de búsqueda
        search_query = request.GET.get('search', '')
        date_filter = request.GET.get('date_filter', '')
        status_filter = request.GET.get('status_filter', '')
        
        # Filtrar decisiones financieras
        financial_decisions = FinancialDecision.objects.select_related('fk_business').order_by('-id')
        
        if search_query:
            financial_decisions = financial_decisions.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(fk_business__name__icontains=search_query)
            )
        
        if status_filter:
            is_active = status_filter.lower() == 'active'
            financial_decisions = financial_decisions.filter(is_active=is_active)
        
        # Paginación
        paginator = Paginator(financial_decisions, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Obtener businesses para el formulario
        businesses = Business.objects.filter(is_active=True).order_by('name')
        
        context = {
            'financial_decisions': page_obj,
            'businesses': businesses,
            'search_query': search_query,
            'status_filter': status_filter,
            'total_count': paginator.count,
        }
        
        return render(request, 'finance/financial-decision-list.html', context)
        
    except Exception as e:
        messages.error(request, f"Error al cargar la página: {str(e)}")
        return HttpResponseServerError("Ocurrió un error al cargar la página.")


@login_required
def create_financial_decision_view(request):
    """
    Vista para crear una nueva decisión financiera
    """
    if request.method == 'POST':
        try:
            form = FinancialDecisionForm(request.POST, request.FILES)
            if form.is_valid():
                financial_decision = form.save()
                messages.success(request, 'Decisión financiera creada exitosamente!')
                
                # Respuesta AJAX
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Decisión financiera creada exitosamente!',
                        'redirect_url': request.build_absolute_uri('/finance/list')
                    })
                
                return redirect('finance:finance.list')
            else:
                # Errores del formulario
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'errors': form.errors
                    })
                
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
                        
        except Exception as e:
            error_message = f"Error al crear la decisión financiera: {str(e)}"
            messages.error(request, error_message)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': error_message
                })
    
    return redirect('finance:finance.list')


@login_required
def update_financial_decision_view(request, pk):
    """
    Vista para actualizar una decisión financiera existente
    """
    try:
        financial_decision = get_object_or_404(FinancialDecision, pk=pk)
        
        if request.method == 'POST':
            form = FinancialDecisionForm(
                request.POST, 
                request.FILES, 
                instance=financial_decision
            )
            
            if form.is_valid():
                form.save()
                messages.success(request, 'Decisión financiera actualizada exitosamente!')
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Decisión financiera actualizada exitosamente!'
                    })
                
                return redirect('finance:finance.list')
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'errors': form.errors
                    })
                
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
        
        # GET request - devolver datos del objeto
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'data': {
                    'id': financial_decision.id,
                    'name': financial_decision.name,
                    'description': financial_decision.description,
                    'amount': str(financial_decision.amount) if hasattr(financial_decision, 'amount') else '',
                    'business_id': financial_decision.fk_business.id if financial_decision.fk_business else '',
                    'is_active': financial_decision.is_active,
                }
            })
            
    except Exception as e:
        error_message = f"Error al actualizar la decisión financiera: {str(e)}"
        messages.error(request, error_message)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': error_message
            })
    
    return redirect('finance:finance.list')


@login_required
def delete_financial_decision_view(request, pk):
    """
    Vista para eliminar (desactivar) una decisión financiera
    """
    try:
        financial_decision = get_object_or_404(FinancialDecision, pk=pk)
        
        if request.method in ['POST', 'DELETE']:
            # Soft delete - solo desactivar
            financial_decision.is_active = False
            financial_decision.save()
            
            messages.success(request, "Decisión financiera eliminada exitosamente!")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Decisión financiera eliminada exitosamente!'
                })
            
            return redirect("finance:finance.list")
            
    except Exception as e:
        error_message = f"Error al eliminar la decisión financiera: {str(e)}"
        messages.error(request, error_message)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': error_message
            })
    
    return HttpResponseForbidden("Método no permitido")


@login_required
def get_financial_decision_details_view(request, pk):
    """
    Vista para obtener detalles de una decisión financiera específica
    """
    try:
        if request.method == 'GET':
            financial_decision = get_object_or_404(FinancialDecision, pk=pk)
            
            decision_details = {
                'id': financial_decision.id,
                'name': financial_decision.name,
                'description': financial_decision.description,
                'amount': str(financial_decision.amount) if hasattr(financial_decision, 'amount') else '',
                'business_name': financial_decision.fk_business.name if financial_decision.fk_business else '',
                'business_id': financial_decision.fk_business.id if financial_decision.fk_business else '',
                'is_active': financial_decision.is_active,
                'date_created': financial_decision.date_created.strftime('%d/%m/%Y %H:%M') if financial_decision.date_created else '',
                'last_updated': financial_decision.last_updated.strftime('%d/%m/%Y %H:%M') if financial_decision.last_updated else '',
            }
            
            return JsonResponse({
                'success': True,
                'data': decision_details
            })
            
    except FinancialDecision.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Decisión financiera no encontrada'
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener los detalles: {str(e)}'
        }, status=500)


@login_required
def get_finance_recommendation_details_view(request, pk):
    """
    Vista para obtener detalles de una recomendación financiera
    """
    try:
        if request.method == 'GET':
            recommendation = get_object_or_404(FinanceRecommendation, pk=pk)
            
            recommendation_details = {
                'id': recommendation.id,
                'name': recommendation.name,
                'recommendation': recommendation.recommendation,
                'description': recommendation.description if hasattr(recommendation, 'description') else '',
                'variable_name': recommendation.variable_name,
                'threshold_value': str(recommendation.threshold_value) if recommendation.threshold_value else '',
                'business_name': recommendation.fk_business.name if recommendation.fk_business else '',
                'is_active': recommendation.is_active,
            }
            
            return JsonResponse({
                'success': True,
                'data': recommendation_details
            })
            
    except FinanceRecommendation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Recomendación financiera no encontrada'
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener los detalles: {str(e)}'
        }, status=500)


@login_required
def bulk_delete_financial_decisions_view(request):
    """
    Vista para eliminar múltiples decisiones financieras
    """
    if request.method == 'POST':
        try:
            decision_ids = request.POST.getlist('decision_ids[]')
            if decision_ids:
                FinancialDecision.objects.filter(
                    id__in=decision_ids
                ).update(is_active=False)
                
                messages.success(
                    request, 
                    f'{len(decision_ids)} decisiones financieras eliminadas exitosamente!'
                )
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': f'{len(decision_ids)} decisiones eliminadas exitosamente!'
                    })
            else:
                messages.warning(request, 'No se seleccionaron decisiones para eliminar.')
                
        except Exception as e:
            error_message = f"Error al eliminar las decisiones: {str(e)}"
            messages.error(request, error_message)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': error_message
                })
    
    return redirect('finance:finance.list')