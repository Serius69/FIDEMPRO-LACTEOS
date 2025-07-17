"""
Enhanced Dashboard Views - Vistas mejoradas manteniendo las URLs existentes
Compatible con: index, dashboard_admin, dashboard_user, update_business_metrics, dashboard_api
"""

from typing import Dict, Any, Optional
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods
from django.db import transaction
import logging
import json

# Imports locales
from variable.models import Variable
from user.models import ActivityLog
from product.models import Product, Area
from finance.models import FinanceRecommendation, FinanceRecommendationSimulation
from business.models import Business
from dashboards.models import Chart
from simulate.models import ResultSimulation, Simulation, Demand, DemandBehavior
from pages.forms import RegisterElementsForm

# Import del servicio mejorado
from .services.dashboard_service import DashboardService

# Configurar logger
logger = logging.getLogger(__name__)

@login_required
def index(request):
    """
    Vista principal del dashboard - MEJORADA
    URL: '' (dashboard:index)
    """
    try:
        if request.method == 'POST':
            form = RegisterElementsForm(request.POST)
            if form.is_valid():
                messages.success(request, "Elementos registrados correctamente")
                return redirect('dashboard:index')
        else:
            form = RegisterElementsForm()

        # Obtener negocio activo del usuario usando el servicio mejorado
        business = DashboardService.get_user_business(request.user)
        
        if not business:
            context = {
                'form': form,
                'business': None,
                'business_count': 0,
                'products_count': 0,
                'simulations_count': 0,
                'charts_count': 0,
                'greeting': DashboardService.get_business_greeting(request.user),
                'system_status': 'no_business'
            }
            return render(request, 'dashboards/index.html', context)

        # Guardar business_id en sesión
        request.session['business_id'] = business.id

        # Obtener datos completos usando el servicio mejorado
        dashboard_data = DashboardService.get_complete_dashboard_data(business.id, request.user)
        
        # Obtener actividad reciente
        recent_activities = ActivityLog.objects.filter(
            user=request.user
        ).select_related('user').order_by('-timestamp')[:30]

        # Contexto mejorado
        context = {
            'form': form,
            'business': business,
            'greeting': DashboardService.get_business_greeting(request.user),
            
            # Estadísticas básicas
            'business_count': Business.objects.filter(fk_user=request.user, is_active=True).count(),
            'products_count': dashboard_data['business_stats']['products_count'],
            'simulations_count': dashboard_data['business_stats']['simulations_count'],
            'charts_count': dashboard_data['business_stats']['charts_count'],
            
            # Métricas destacadas para la vista index
            'total_revenue': dashboard_data['financial_metrics']['revenue'],
            'profit_margin': dashboard_data['financial_metrics']['profit_margin'],
            'efficiency_score': dashboard_data['business_kpis']['efficiency_score'],
            'financial_health': dashboard_data['business_kpis']['financial_health'],
            
            # Datos adicionales
            'recent_activities': recent_activities,
            'has_alerts': len(dashboard_data['business_alerts']) > 0,
            'critical_alerts_count': len([a for a in dashboard_data['business_alerts'] if a.get('priority') == 'high']),
            'system_status': dashboard_data['summary']['status'],
            'last_updated': dashboard_data['last_updated']
        }
        
        return render(request, 'dashboards/index.html', context)

    except Exception as e:
        logger.error(f"Error en index view: {e}")
        messages.error(request, 'Ocurrió un error inesperado. Por favor intenta nuevamente.')
        
        # Contexto de error
        error_context = {
            'form': RegisterElementsForm(),
            'business': None,
            'business_count': 0,
            'products_count': 0,
            'simulations_count': 0,
            'charts_count': 0,
            'greeting': DashboardService.get_business_greeting(request.user),
            'system_status': 'error',
            'error_message': str(e)
        }
        
        return render(request, 'dashboards/index.html', error_context)

@login_required
@cache_page(60 * 5)  # Cache por 5 minutos
def dashboard_admin(request):
    """
    Dashboard para administradores - MEJORADO
    URL: 'admin/' (dashboard:dashboard.admin)
    """
    try:
        # Obtener estadísticas usando el servicio mejorado
        admin_stats = DashboardService.get_admin_statistics()
        
        # Obtener datos adicionales para admin
        recent_businesses = Business.objects.filter(
            is_active=True
        ).select_related('fk_user').order_by('-date_created')[:10]
        
        recent_simulations = Simulation.objects.select_related(
            'fk_questionary_result__fk_questionary__fk_product__fk_business'
        ).order_by('-date_created')[:15]
        
        # Calcular métricas del sistema
        system_metrics = {
            'avg_simulations_per_business': (
                admin_stats['total_simulations'] / max(admin_stats['active_businesses'], 1)
            ),
            'user_engagement_rate': (
                admin_stats['active_users'] / max(admin_stats['users_count'], 1) * 100
            ),
            'business_activation_rate': (
                admin_stats['active_businesses'] / max(admin_stats['total_businesses'], 1) * 100
            )
        }
        
        context = {
            # Estadísticas básicas mejoradas
            'users_count': admin_stats['users_count'],
            'active_users': admin_stats['active_users'],
            'new_users_last_month': admin_stats['new_users_last_month'],
            'users_change': admin_stats['users_change'],
            'users_change_percentage': admin_stats['users_change_percentage'],
            
            # Estadísticas de negocios
            'total_businesses': admin_stats['total_businesses'],
            'active_businesses': admin_stats['active_businesses'],
            'new_businesses_last_month': admin_stats['new_businesses_last_month'],
            
            # Estadísticas de simulaciones
            'total_simulations': admin_stats['total_simulations'],
            'last_month_simulations': admin_stats['last_month_simulations'],
            
            # Métricas del sistema
            'system_health': admin_stats['system_health'],
            'system_metrics': system_metrics,
            
            # Datos recientes
            'recent_businesses': recent_businesses,
            'recent_simulations': recent_simulations,
            
            # Información del sistema
            'report_date': timezone.now(),
            'cache_status': 'active',
            'performance_status': 'optimal'
        }
        
        return render(request, 'dashboards/dashboard-admin.html', context)
        
    except Exception as e:
        logger.error(f"Error in dashboard_admin: {e}")
        messages.error(request, 'Error al cargar el dashboard administrativo.')
        
        # Contexto de fallback
        fallback_context = {
            'users_count': 0,
            'active_users': 0,
            'new_users_last_month': 0,
            'users_change': 0,
            'users_change_percentage': 0,
            'total_businesses': 0,
            'active_businesses': 0,
            'total_simulations': 0,
            'system_health': 'error',
            'error_message': str(e)
        }
        
        return render(request, 'dashboards/dashboard-admin.html', fallback_context)

@login_required
def dashboard_user(request):
    """
    Dashboard principal del usuario - MEJORADO SIGNIFICATIVAMENTE
    URL: 'user/' (dashboard:dashboard.user)
    """
    try:
        # Obtener business_id de sesión o parámetro
        business_id = request.GET.get('business_id') or request.session.get('business_id')
        
        if not business_id:
            messages.error(request, 'Por favor selecciona un negocio.')
            return redirect("business:business.list")
        
        # Validar business_id
        try:
            business_id = int(business_id)
        except (ValueError, TypeError):
            messages.error(request, 'ID de negocio no válido.')
            return redirect("business:business.list")
        
        # Actualizar sesión
        request.session['business_id'] = business_id
        
        # Obtener todos los datos del dashboard usando el servicio mejorado
        dashboard_data = DashboardService.get_complete_dashboard_data(business_id, request.user)
        
        # Verificar si se encontró el negocio
        if not dashboard_data['business']:
            messages.error(request, 'Negocio no encontrado o no tienes permisos.')
            return redirect("business:business.list")
        
        # Obtener todos los negocios del usuario para el selector
        businesses = Business.objects.filter(
            fk_user=request.user,
            is_active=True
        ).order_by('-id')
        
        # Paginación para recomendaciones
        paginator = Paginator(dashboard_data['recommendations'], 10)
        page_obj = paginator.get_page(request.GET.get('page'))
        
        # Preparar datos para gráficos
        monthly_trends_json = json.dumps(dashboard_data['performance_trends']['monthly_trends'])
        
        # Contexto completo mejorado
        context = {
            # Información básica
            'greeting': DashboardService.get_business_greeting(request.user),
            'business': dashboard_data['business'],
            'businesses': businesses,
            'products': dashboard_data['products'],
            'charts': dashboard_data['charts'],
            'page_obj': page_obj,
            'recent_activity': dashboard_data['recent_activity'],
            
            # Métricas financieras principales
            'total_revenue': dashboard_data['financial_metrics']['revenue'],
            'total_costs': dashboard_data['financial_metrics']['costs'],
            'total_inventory_levels': dashboard_data['financial_metrics']['inventory'],
            'total_demand': dashboard_data['financial_metrics']['demand'],
            'total_production_output': dashboard_data['financial_metrics']['production'],
            'total_profit_margin': dashboard_data['financial_metrics']['profit'],
            
            # KPIs mejorados
            'profit_margin_percentage': dashboard_data['financial_metrics']['profit_margin'],
            'roi_percentage': dashboard_data['financial_metrics']['roi'],
            'efficiency_score': dashboard_data['business_kpis']['efficiency_score'],
            'financial_health': dashboard_data['business_kpis']['financial_health'],
            'net_profit': dashboard_data['business_kpis']['net_profit'],
            'cost_ratio': dashboard_data['business_kpis']['cost_ratio'],
            
            # KPIs adicionales
            'revenue_per_product': dashboard_data['business_kpis']['revenue_per_product'],
            'demand_fulfillment': dashboard_data['business_kpis']['demand_fulfillment'],
            'operational_efficiency': dashboard_data['business_kpis']['operational_efficiency'],
            
            # Contadores para las cards de estadísticas
            'business_count': businesses.count(),
            'products_count': dashboard_data['business_stats']['products_count'],
            'active_products_count': dashboard_data['business_stats']['active_products_count'],
            'simulations_count': dashboard_data['business_stats']['simulations_count'],
            'recent_simulations_count': dashboard_data['business_stats']['recent_simulations_count'],
            'charts_count': dashboard_data['business_stats']['charts_count'],
            'areas_count': dashboard_data['business_stats']['areas_count'],
            
            # Cambios porcentuales
            'revenue_change': dashboard_data['percentage_changes']['revenue_change'],
            'costs_change': dashboard_data['percentage_changes']['costs_change'],
            'profit_change': dashboard_data['percentage_changes']['profit_change'],
            'profit_margin_change': dashboard_data['percentage_changes']['profit_margin_change'],
            'inventory_change': dashboard_data['percentage_changes']['inventory_change'],
            'demand_change': dashboard_data['percentage_changes']['demand_change'],
            'production_change': dashboard_data['percentage_changes']['production_change'],
            
            # Datos para dashboard ejecutivo
            'performance_trends': dashboard_data['performance_trends'],
            'top_products': dashboard_data['top_products'],
            'monthly_trends_json': monthly_trends_json,
            'growth_rate': dashboard_data['performance_trends']['growth_rate'],
            'has_trend_data': dashboard_data['performance_trends']['has_data'],
            
            # Alertas y resumen mejorados
            'business_alerts': dashboard_data['business_alerts'],
            'critical_alerts': [a for a in dashboard_data['business_alerts'] if a.get('priority') == 'high'],
            'dashboard_summary': dashboard_data['summary'],
            'health_score': dashboard_data['summary']['health_score'],
            
            # Datos adicionales del negocio
            'business_type_display': dashboard_data['business'].get_type_display() if hasattr(dashboard_data['business'], 'get_type_display') else 'Otros',
            'business_location': getattr(dashboard_data['business'], 'location', 'No especificada'),
            'business_description': getattr(dashboard_data['business'], 'description', 'Sin descripción'),
            
            # Estado del sistema y configuraciones
            'system_status': dashboard_data['summary']['status'],
            'last_updated': dashboard_data['last_updated'],
            'can_export': True,
            'can_print': True,
            'auto_refresh': request.session.get('auto_refresh', False),
            
            # Datos para JavaScript y gráficos
            'chart_data_available': len(dashboard_data['charts']) > 0,
            'recommendations_count': len(dashboard_data['recommendations']),
            'alerts_count': len(dashboard_data['business_alerts']),
        }
        
        # Log de información para debugging
        logger.info(f"Enhanced dashboard loaded for user {request.user.id}: "
                   f"business={dashboard_data['business'].name}, "
                   f"health_score={dashboard_data['summary']['health_score']}, "
                   f"products={dashboard_data['business_stats']['products_count']}, "
                   f"simulations={dashboard_data['business_stats']['simulations_count']}")
        
        return render(request, 'dashboards/dashboard-user.html', context)
        
    except Exception as e:
        logger.error(f"Error in enhanced dashboard_user: {e}", exc_info=True)
        messages.error(request, 'Error al cargar el dashboard. Por favor intenta nuevamente.')
        return redirect("business:business.list")

@login_required
@transaction.atomic
@require_http_methods(["POST"])
def update_business_metrics(request):
    """
    Actualiza las métricas del negocio - MEJORADO SIGNIFICATIVAMENTE
    URL: 'api/update-metrics/' (dashboard:update_metrics)
    """
    try:
        business_id = request.POST.get('business_id')
        
        if not business_id:
            return JsonResponse({
                'success': False,
                'error': 'Business ID requerido'
            }, status=400)
        
        try:
            business_id = int(business_id)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'Business ID inválido'
            }, status=400)
        
        # Actualizar métricas usando el servicio mejorado
        result = DashboardService.update_business_metrics_enhanced(business_id, request.user)
        
        if result['success']:
            # Obtener estado de salud del dashboard
            health_status = DashboardService.get_dashboard_health_status(business_id, request.user)
            
            # Enriquecer respuesta con datos adicionales
            result.update({
                'health_status': health_status,
                'cache_cleared': True,
                'data_freshness': 'updated',
                'performance': {
                    'update_time': timezone.now().isoformat(),
                    'data_completeness': health_status.get('data_completeness', 0),
                    'metrics_count': len(result.get('metrics', {}))
                }
            })
        
        # Log de la actualización
        logger.info(f"Metrics update for business {business_id} by user {request.user.id}: "
                   f"success={result['success']}")
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error updating enhanced business metrics: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor',
            'error_code': 'METRICS_UPDATE_FAILED',
            'timestamp': timezone.now().isoformat()
        }, status=500)

@login_required
def dashboard_api(request):
    """
    API endpoint para obtener datos del dashboard - MEJORADO SIGNIFICATIVAMENTE
    URL: 'api/dashboard-data/' (dashboard:dashboard_api)
    """
    try:
        business_id = request.GET.get('business_id')
        
        if not business_id:
            return JsonResponse({
                'success': False,
                'error': 'Business ID requerido',
                'error_code': 'MISSING_BUSINESS_ID'
            }, status=400)
        
        try:
            business_id = int(business_id)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'Business ID inválido',
                'error_code': 'INVALID_BUSINESS_ID'
            }, status=400)
        
        # Parámetros opcionales
        include_trends = request.GET.get('include_trends', 'true').lower() == 'true'
        include_recommendations = request.GET.get('include_recommendations', 'true').lower() == 'true'
        include_alerts = request.GET.get('include_alerts', 'true').lower() == 'true'
        format_type = request.GET.get('format', 'full')  # full, summary, minimal
        
        # Obtener datos usando el servicio mejorado
        api_data = DashboardService.get_dashboard_api_data_enhanced(business_id, request.user)
        
        if not api_data['success']:
            return JsonResponse(api_data, status=403)
        
        # Personalizar respuesta según parámetros
        if format_type == 'summary':
            # Respuesta resumida
            summary_data = {
                'success': True,
                'business': api_data['business'],
                'key_metrics': {
                    'revenue': api_data['metrics']['revenue'],
                    'profit_margin': api_data['metrics']['profit_margin'],
                    'roi': api_data['metrics']['roi'],
                    'efficiency_score': api_data['kpis']['efficiency_score']
                },
                'health_indicators': api_data['performance_indicators'],
                'alerts_summary': {
                    'total': api_data['alerts']['total_count'],
                    'critical': api_data['alerts']['critical_count']
                },
                'last_updated': api_data['last_updated']
            }
            return JsonResponse(summary_data)
        
        elif format_type == 'minimal':
            # Respuesta mínima
            minimal_data = {
                'success': True,
                'business_name': api_data['business']['name'],
                'health_score': api_data['performance_indicators']['health_score'],
                'revenue': api_data['metrics']['revenue'],
                'profit_margin': api_data['metrics']['profit_margin'],
                'status': api_data['summary']['status'],
                'timestamp': api_data['timestamp']
            }
            return JsonResponse(minimal_data)
        
        # Respuesta completa (personalizada según parámetros)
        if not include_trends:
            api_data.pop('trends', None)
        
        if not include_recommendations:
            api_data['alerts'].pop('recent_alerts', None)
        
        if not include_alerts:
            api_data.pop('alerts', None)
        
        # Agregar metadatos de la API
        api_data.update({
            'api_version': '2.0',
            'request_params': {
                'include_trends': include_trends,
                'include_recommendations': include_recommendations,
                'include_alerts': include_alerts,
                'format': format_type
            },
            'cache_info': {
                'cached': hasattr(request, '_cached_response'),
                'cache_age': 'fresh'  # Se podría calcular realmente
            }
        })
        
        # Log de acceso a la API
        logger.info(f"Dashboard API accessed: user={request.user.id}, "
                   f"business={business_id}, format={format_type}")
        
        return JsonResponse(api_data)
        
    except Exception as e:
        logger.error(f"Error in enhanced dashboard API: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor',
            'error_code': 'API_ERROR',
            'timestamp': timezone.now().isoformat()
        }, status=500)

# === FUNCIONES AUXILIARES PARA LAS VISTAS ===

@login_required
def get_chart_data(request, chart_id):
    """
    Obtiene datos de un gráfico específico - FUNCIÓN AUXILIAR MEJORADA
    Esta función puede ser llamada desde JavaScript en las vistas principales
    """
    try:
        chart = get_object_or_404(Chart, pk=chart_id, is_active=True)
        
        # Verificar permisos (el gráfico debe pertenecer al usuario)
        if chart.fk_product.fk_business.fk_user != request.user:
            return JsonResponse({
                'success': False,
                'error': 'Sin permisos para acceder a este gráfico'
            }, status=403)
        
        return JsonResponse({
            'success': True,
            'data': chart.chart_data,
            'title': chart.title,
            'type': chart.chart_type,
            'product_name': chart.fk_product.name,
            'last_updated': chart.date_created.isoformat() if hasattr(chart, 'date_created') else None,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting chart data: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def dashboard_health_check(request):
    """
    Endpoint de verificación de salud del dashboard - FUNCIÓN AUXILIAR
    """
    try:
        business_id = request.GET.get('business_id') or request.session.get('business_id')
        
        if not business_id:
            return JsonResponse({
                'status': 'error',
                'error': 'No business selected',
                'timestamp': timezone.now().isoformat()
            })
        
        # Obtener estado de salud usando el servicio
        health_status = DashboardService.get_dashboard_health_status(int(business_id), request.user)
        
        return JsonResponse(health_status)
        
    except Exception as e:
        logger.error(f"Error in dashboard health check: {e}")
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)

@login_required
def clear_dashboard_cache_view(request):
    """
    Limpia la caché del dashboard - FUNCIÓN AUXILIAR
    """
    try:
        business_id = request.GET.get('business_id') or request.session.get('business_id')
        
        if business_id:
            DashboardService.clear_dashboard_cache(int(business_id), request.user.id)
            message = f'Caché limpiada para el negocio {business_id}'
        else:
            DashboardService.clear_dashboard_cache()
            message = 'Caché general limpiada'
        
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'success': True,
                'message': message,
                'timestamp': timezone.now().isoformat()
            })
        
        messages.success(request, 'Caché del dashboard limpiada correctamente.')
        return redirect('dashboard:dashboard.user')
        
    except Exception as e:
        logger.error(f"Error clearing dashboard cache: {e}")
        
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
        
        messages.error(request, 'Error al limpiar la caché.')
        return redirect('dashboard:dashboard.user')

# === FUNCIONES DE UTILIDAD ===

def get_user_dashboard_context(user, business_id: int = None) -> Dict[str, Any]:
    """
    Función auxiliar para obtener contexto básico del dashboard
    Útil para otras vistas que necesiten datos del dashboard
    """
    try:
        if not business_id:
            business = DashboardService.get_user_business(user)
            if not business:
                return {}
            business_id = business.id
        
        # Obtener datos básicos del dashboard
        dashboard_data = DashboardService.get_complete_dashboard_data(business_id, user)
        
        return {
            'business': dashboard_data['business'],
            'financial_metrics': dashboard_data['financial_metrics'],
            'business_kpis': dashboard_data['business_kpis'],
            'summary': dashboard_data['summary'],
            'greeting': DashboardService.get_business_greeting(user),
        }
        
    except Exception as e:
        logger.error(f"Error getting user dashboard context: {e}")
        return {}

def validate_business_access(user, business_id: int) -> bool:
    """
    Valida si el usuario tiene acceso al negocio
    """
    try:
        business = DashboardService._get_validated_business(business_id, user)
        return business is not None
    except Exception:
        return False

# === DECORADORES PERSONALIZADOS ===

from functools import wraps

def require_business_access(view_func):
    """Decorador para verificar acceso al negocio"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        business_id = (
            request.GET.get('business_id') or 
            request.POST.get('business_id') or 
            request.session.get('business_id') or
            kwargs.get('business_id')
        )
        
        if not business_id:
            if request.headers.get('Accept') == 'application/json':
                return JsonResponse({'error': 'Business ID required'}, status=400)
            messages.error(request, 'ID de negocio requerido')
            return redirect('dashboard:dashboard.user')
        
        try:
            if not validate_business_access(request.user, int(business_id)):
                if request.headers.get('Accept') == 'application/json':
                    return JsonResponse({'error': 'Access denied'}, status=403)
                messages.error(request, 'Acceso denegado')
                return redirect('dashboard:dashboard.user')
                
        except (ValueError, TypeError):
            if request.headers.get('Accept') == 'application/json':
                return JsonResponse({'error': 'Invalid business ID'}, status=400)
            messages.error(request, 'ID de negocio inválido')
            return redirect('dashboard:dashboard.user')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper

def log_dashboard_access(view_func):
    """Decorador para registrar accesos al dashboard"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            business_id = request.GET.get('business_id') or request.session.get('business_id')
            
            # Registrar acceso
            if request.user.is_authenticated and business_id:
                ActivityLog.objects.create(
                    user=request.user,
                    action=f"Dashboard access: {view_func.__name__}",
                    details=f"Accessed {view_func.__name__} for business {business_id}",
                    timestamp=timezone.now()
                )
        except Exception:
            pass  # No fallar si no se puede registrar
        
        return view_func(request, *args, **kwargs)
    
    return wrapper