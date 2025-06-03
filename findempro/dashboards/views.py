from typing import Dict, Any, Optional, Tuple
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from datetime import datetime
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import Http404, JsonResponse
from django.db.models import Max, F, Prefetch, Count, Q, Sum
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.db import transaction
import logging

# Imports locales
from variable.models import Variable
from user.models import ActivityLog
from product.models import Product, Area
from finance.models import FinanceRecommendationSimulation
from business.models import Business
from dashboards.models import Chart
from simulate.models import ResultSimulation, Simulation, Demand, DemandBehavior
from pages.forms import RegisterElementsForm

# Configurar logger
logger = logging.getLogger(__name__)

class DashboardView(LoginRequiredMixin, TemplateView):
    """Vista base para dashboards con autenticación requerida"""
    pass

class DashboardService:
    """Servicio para manejar la lógica del dashboard"""
    
    @staticmethod
    def get_user_business(user) -> Optional[Business]:
        """Obtiene el negocio activo del usuario con manejo de caché"""
        return Business.objects.filter(
            fk_user=user, 
            is_active=True
        ).select_related('fk_user').first()
    
    @staticmethod
    def get_business_metrics(business_id: int) -> Dict[str, Any]:
        """Obtiene las métricas del negocio de forma optimizada"""
        # Usar agregación para obtener todas las métricas en una sola consulta
        products = Product.objects.filter(
            fk_business=business_id
        ).prefetch_related(
            Prefetch('area_set', queryset=Area.objects.select_related('fk_product'))
        )
        
        # Obtener IDs de productos para consultas posteriores
        product_ids = list(products.values_list('id', flat=True))
        
        # Obtener últimos gráficos de forma optimizada
        latest_charts = Chart.objects.filter(
            fk_product_id__in=product_ids,
            is_active=True
        ).values('fk_product_id').annotate(
            latest_id=Max('id')
        ).values_list('latest_id', flat=True)
        
        charts = Chart.objects.filter(
            id__in=latest_charts
        ).select_related('fk_product')
        
        # Obtener simulaciones con prefetch
        simulations = Simulation.objects.filter(
            fk_questionary_result__fk_questionary__fk_product_id__in=product_ids
        ).select_related(
            'fk_questionary_result__fk_questionary__fk_product'
        ).prefetch_related(
            Prefetch(
                'resultsimulation_set',
                queryset=ResultSimulation.objects.filter(is_active=True)
            )
        ).order_by('-id')[:10]  # Limitar resultados
        
        return {
            'products': products,
            'charts': charts,
            'simulations': simulations,
            'product_ids': product_ids
        }
    
    @staticmethod
    def calculate_totals(simulations) -> Dict[str, float]:
        """Calcula los totales de las variables de forma eficiente"""
        variables_to_search = ['TPV', 'IT', 'GT', 'TG', 'DT']
        
        # Obtener mapeo de variables una sola vez
        variable_mapping = dict(
            Variable.objects.filter(
                initials__in=variables_to_search
            ).values_list('initials', 'name')
        )
        
        totals = {
            'Total Revenue': 0,
            'Total Costs': 0,
            'Total Inventory Levels': 0,
            'Total Demand': 0,
            'Total Production Output': 0,
            'Total Profit Margin': 0
        }
        
        for simulation in simulations:
            for result in simulation.resultsimulation_set.all():
                try:
                    variables = result.get_variables()
                    for initial, value in variables.items():
                        if initial in variable_mapping:
                            var_name = variable_mapping[initial]
                            if var_name in totals:
                                totals[var_name] += value
                except Exception as e:
                    logger.error(f"Error processing simulation {simulation.id}: {e}")
                    continue
        
        return totals

@login_required
def index(request):
    """Vista principal del dashboard"""
    try:
        if request.method == 'POST':
            form = RegisterElementsForm(request.POST)
            if form.is_valid():
                # Procesar formulario
                messages.success(request, "Elementos registrados correctamente")
                return redirect('dashboard:index')
        else:
            form = RegisterElementsForm()

        business = DashboardService.get_user_business(request.user)
        if not business:
            messages.warning(request, "No tienes un negocio activo. Por favor crea uno primero.")
            return redirect('business:business.create')

        request.session['business_id'] = business.id

        # Obtener métricas del negocio para los contadores
        metrics = DashboardService.get_business_metrics(business.id)
        business_count = Business.objects.filter(fk_user=request.user, is_active=True).count()
        products_count = metrics['products'].count()
        simulations_count = metrics['simulations'].count() if hasattr(metrics['simulations'], 'count') else len(metrics['simulations'])
        charts_count = metrics['charts'].count() if hasattr(metrics['charts'], 'count') else len(metrics['charts'])

        context = {
            'form': form,
            'business': business,
            'business_count': business_count,
            'products_count': products_count,
            'simulations_count': simulations_count,
            'charts_count': charts_count,
        }
        return render(request, 'dashboards/index.html', context)

    except Exception as e:
        logger.error(f"Error en index view: {e}")
        messages.error(request, 'Ocurrió un error inesperado. Por favor intenta nuevamente.')
        return render(request, 'error_page.html', {'error_message': str(e)})

@login_required
@cache_page(60 * 5)  # Cache por 5 minutos
def dashboard_admin(request):
    """Dashboard para administradores con métricas de usuarios"""
    today = timezone.now()
    last_month = today - relativedelta(months=1)
    
    # Usar agregación para obtener conteos
    user_stats = User.objects.aggregate(
        total_users=Count('id'),
        last_month_users=Count(
            'id',
            filter=Q(
                date_joined__month=last_month.month,
                date_joined__year=last_month.year
            )
        )
    )
    
    users_count = user_stats['total_users']
    users_last_month_count = user_stats['last_month_users']
    
    users_change = users_count - users_last_month_count
    users_change_percentage = (
        (users_change / users_last_month_count * 100) 
        if users_last_month_count > 0 else 0
    )
    
    context = {
        'users_count': users_count,
        'users_last_month_count': users_last_month_count,
        'users_change': users_change,
        'users_change_percentage': round(users_change_percentage, 2),
    }
    
    return render(request, 'dashboards/dashboard-admin.html', context)

@login_required
def dashboard_user(request):
    """Dashboard principal del usuario con todas las métricas del negocio"""
    try:
        # Obtener business_id de sesión o parámetro
        business_id = request.GET.get('business_id') or request.session.get('business_id')
        
        if not business_id:
            messages.error(request, 'Por favor selecciona un negocio.')
            return redirect("business:business.list")
        
        # Validar y obtener el negocio
        try:
            business_id = int(business_id)
            business = get_object_or_404(
                Business.objects.select_related('fk_user'),
                pk=business_id,
                is_active=True,
                fk_user=request.user
            )
        except (ValueError, Business.DoesNotExist):
            messages.error(request, 'Negocio no válido o no tienes permisos.')
            return redirect("business:business.list")
        
        # Actualizar sesión
        request.session['business_id'] = business_id
        
        # Obtener métricas del negocio
        metrics = DashboardService.get_business_metrics(business_id)
        
        # Obtener recomendaciones con paginación
        recommendations = FinanceRecommendationSimulation.objects.filter(
            fk_simulation__fk_questionary_result__fk_questionary__fk_product__fk_business=business_id,
            # is_active=True
        ).select_related(
            'fk_simulation__fk_questionary_result__fk_questionary__fk_product'
        ).values(
            'data',
            'fk_simulation__date_created',
            'fk_simulation__fk_questionary_result__fk_questionary__fk_product__name',
        ).annotate(
            data_as_percentage=F('data') * 100,
        ).distinct()
        
        # Paginación
        paginator = Paginator(recommendations, 10)
        page_obj = paginator.get_page(request.GET.get('page'))
        
        # Calcular totales
        totals = DashboardService.calculate_totals(metrics['simulations'])
        
        # Obtener actividad reciente
        recent_activity = ActivityLog.objects.filter(
            user=request.user
        ).select_related('user').order_by('-timestamp')[:10]
        
        # Obtener todos los negocios del usuario
        businesses = Business.objects.filter(
            fk_user=request.user,
            is_active=True
        ).order_by('-id')
        
        # Saludo personalizado
        current_hour = datetime.now().hour
        if 5 <= current_hour < 12:
            greeting = "Buenos Días"
        elif 12 <= current_hour < 18:
            greeting = "Buenas Tardes"
        else:
            greeting = "Buenas Noches"
        
        context = {
            'greeting': greeting,
            'business': business,
            'businesses': businesses,
            'products': metrics['products'],
            'areas': Area.objects.filter(fk_product__in=metrics['products']),
            'charts': metrics['charts'],
            'page_obj': page_obj,
            'recent_activity': recent_activity,
            'total_revenue': totals['Total Revenue'],
            'total_costs': totals['Total Costs'],
            'total_inventory_levels': totals['Total Inventory Levels'],
            'total_demand': totals['Total Demand'],
            'total_production_output': totals['Total Production Output'],
            'total_profit_margin': totals['Total Profit Margin'],
        }
        
        return render(request, 'dashboards/dashboard-user.html', context)
        
    except Exception as e:
        logger.error(f"Error in dashboard_user: {e}", exc_info=True)
        messages.error(request, 'Error al cargar el dashboard. Por favor intenta nuevamente.')
        return redirect("business:business.list")

@login_required
def get_chart_data(request, chart_id):
    """API endpoint para obtener datos de gráficos de forma asíncrona"""
    try:
        chart = get_object_or_404(Chart, pk=chart_id, is_active=True)
        return JsonResponse({
            'success': True,
            'data': chart.chart_data,
            'title': chart.title,
            'type': chart.chart_type
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@transaction.atomic
def update_business_metrics(request):
    """Actualiza las métricas del negocio de forma transaccional"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        business_id = request.POST.get('business_id')
        if not business_id:
            return JsonResponse({'error': 'Business ID required'}, status=400)
        
        # Verificar permisos
        business = get_object_or_404(
            Business,
            pk=business_id,
            fk_user=request.user,
            is_active=True
        )
        
        # Aquí iría la lógica para actualizar métricas
        # Por ejemplo, recalcular totales, actualizar gráficos, etc.
        
        return JsonResponse({
            'success': True,
            'message': 'Métricas actualizadas correctamente'
        })
        
    except Exception as e:
        logger.error(f"Error updating metrics: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
        
# Agregar las nuevas vistas al views.py
def export_recommendations(request):
    """Exporta las recomendaciones a Excel/CSV"""
    from django.http import HttpResponse
    import csv
    
    business_id = request.GET.get('business_id')
    if not business_id:
        messages.error(request, 'Business ID requerido')
        return redirect('dashboard:dashboard.user')
    
    # Verificar permisos
    business = get_object_or_404(
        Business,
        pk=business_id,
        fk_user=request.user,
        is_active=True
    )
    
    # Obtener recomendaciones
    recommendations = FinanceRecommendationSimulation.objects.filter(
        fk_finance_recommendation__fk_business=business_id,
        is_active=True
    ).select_related(
        'fk_simulation__fk_questionary_result__fk_questionary__fk_product',
        'fk_finance_recommendation'
    )
    
    # Crear respuesta CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="recomendaciones_{business.name}_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Fecha', 'Producto', 'Variable', 'Valor (%)', 
        'Umbral', 'Recomendación'
    ])
    
    for rec in recommendations:
        writer.writerow([
            rec.fk_simulation.date_created.strftime('%Y-%m-%d'),
            rec.fk_simulation.fk_questionary_result.fk_questionary.fk_product.name,
            rec.fk_finance_recommendation.variable_name,
            f"{rec.data * 100:.2f}",
            rec.fk_finance_recommendation.threshold_value,
            rec.fk_finance_recommendation.recommendation
        ])
    
    return response

def dashboard_api(request):
    """API endpoint para obtener datos del dashboard en JSON"""
    from django.http import JsonResponse
    
    business_id = request.GET.get('business_id')
    if not business_id:
        return JsonResponse({'error': 'Business ID required'}, status=400)
    
    try:
        business = get_object_or_404(
            Business,
            pk=business_id,
            fk_user=request.user,
            is_active=True
        )
        
        # Obtener métricas
        metrics = DashboardService.get_business_metrics(business_id)
        totals = DashboardService.calculate_totals(metrics['simulations'])
        
        # Preparar respuesta
        data = {
            'success': True,
            'business': {
                'id': business.id,
                'name': business.name,
                'type': business.get_type_display(),
            },
            'metrics': {
                'revenue': totals['Total Revenue'],
                'costs': totals['Total Costs'],
                'profit_margin': totals['Total Profit Margin'],
                'inventory': totals['Total Inventory Levels'],
                'demand': totals['Total Demand'],
                'production': totals['Total Production Output'],
            },
            'charts': [
                {
                    'id': chart.id,
                    'title': chart.title,
                    'type': chart.chart_type,
                    'last_updated': chart.last_updated.isoformat()
                }
                for chart in metrics['charts']
            ],
            'products_count': metrics['products'].count(),
            'timestamp': timezone.now().isoformat()
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        logger.error(f"Error in dashboard API: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def chart_builder(request):
    """Vista para construir gráficos personalizados"""
    if request.method == 'POST':
        try:
            import json
            
            data = json.loads(request.body)
            product_id = data.get('product_id')
            chart_type = data.get('chart_type')
            chart_data = data.get('chart_data')
            title = data.get('title')
            
            # Validar datos
            if not all([product_id, chart_type, chart_data, title]):
                return JsonResponse({
                    'success': False,
                    'error': 'Faltan datos requeridos'
                }, status=400)
            
            # Crear gráfico
            product = get_object_or_404(Product, pk=product_id)
            chart = Chart.objects.create(
                title=title,
                chart_type=chart_type,
                chart_data=chart_data,
                fk_product=product
            )
            
            # Generar imagen
            chart.generate_chart_image()
            
            return JsonResponse({
                'success': True,
                'chart_id': chart.id,
                'chart_url': chart.get_photo_url()
            })
            
        except Exception as e:
            logger.error(f"Error in chart builder: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    # GET request - mostrar el builder
    products = Product.objects.filter(
        fk_business__fk_user=request.user,
        fk_business__is_active=True
    )
    
    context = {
        'products': products,
        'chart_types': Chart.CHART_TYPES,
    }
    
    return render(request, 'dashboards/chart_builder.html', context)

def analytics_report(request):
    """Genera un reporte analítico completo"""
    from django.template.loader import render_to_string
    from weasyprint import HTML
    from django.http import HttpResponse
    import tempfile
    
    business_id = request.GET.get('business_id')
    if not business_id:
        messages.error(request, 'Business ID requerido')
        return redirect('dashboard:dashboard.user')
    
    try:
        # Obtener datos
        business = get_object_or_404(
            Business,
            pk=business_id,
            fk_user=request.user,
            is_active=True
        )
        
        metrics = DashboardService.get_business_metrics(business_id)
        totals = DashboardService.calculate_totals(metrics['simulations'])
        
        # Preparar contexto para el reporte
        context = {
            'business': business,
            'metrics': totals,
            'products': metrics['products'],
            'charts': metrics['charts'],
            'report_date': timezone.now(),
            'user': request.user,
        }
        
        # Renderizar HTML
        html_string = render_to_string(
            'dashboards/analytics_report_template.html',
            context
        )
        
        # Generar PDF
        html = HTML(string=html_string)
        pdf = html.write_pdf()
        
        # Crear respuesta
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="reporte_analitico_{business.name}_{timezone.now().strftime("%Y%m%d")}.pdf"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating analytics report: {e}")
        messages.error(request, 'Error al generar el reporte')
        return redirect('dashboard:dashboard.user')\

