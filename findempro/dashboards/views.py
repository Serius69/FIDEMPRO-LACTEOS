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
from finance.models import FinanceRecommendation, FinanceRecommendationSimulation
from business.models import Business
from dashboards.models import Chart
from simulate.models import ResultSimulation, Simulation, Demand, DemandBehavior
from pages.forms import RegisterElementsForm

# Configurar logger
logger = logging.getLogger(__name__)

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
            Prefetch('fk_product_area', queryset=Area.objects.select_related('fk_product'))
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
            'fk_questionary_result__fk_questionary__fk_product',
            'fk_fdp'
        ).prefetch_related(
            'results'  # Prefetch results para evitar N+1 queries
        ).order_by('-date_created')
                
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
        
        # Mapeo de iniciales a nombres descriptivos para el dashboard
        metric_mapping = {
            'TPV': 'Total Revenue',
            'IT': 'Total Costs', 
            'GT': 'Total Profit Margin',
            'TG': 'Total Inventory Levels',
            'DT': 'Total Demand'
        }
        
        totals = {
            'Total Revenue': 0,
            'Total Costs': 0,
            'Total Inventory Levels': 0,
            'Total Demand': 0,
            'Total Production Output': 0,
            'Total Profit Margin': 0
        }
        
        try:
            for simulation in simulations:
                # Verificar si simulation tiene results
                if hasattr(simulation, 'results'):
                    results = simulation.results.all()
                else:
                    # Fallback si no hay prefetch
                    results = ResultSimulation.objects.filter(fk_simulation=simulation)
                
                for result in results:
                    try:
                        # Verificar si result tiene el método get_variables
                        if hasattr(result, 'get_variables'):
                            variables = result.get_variables()
                        else:
                            # Fallback: intentar obtener variables directamente
                            variables = {}
                            if hasattr(result, 'variables') and result.variables:
                                import json
                                variables = json.loads(result.variables) if isinstance(result.variables, str) else result.variables
                        
                        for initial, value in variables.items():
                            if initial in metric_mapping:
                                metric_name = metric_mapping[initial]
                                if metric_name in totals:
                                    # Convertir value a float si es string
                                    try:
                                        numeric_value = float(value) if value is not None else 0
                                        totals[metric_name] += numeric_value
                                    except (ValueError, TypeError):
                                        logger.warning(f"Cannot convert value {value} to float for metric {initial}")
                                        continue
                                        
                    except Exception as e:
                        logger.error(f"Error processing result {result.id} from simulation {simulation.id}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error calculating totals: {e}")
            # Retornar totales con valores por defecto en caso de error
            
        return totals
    
    @staticmethod
    def calculate_business_stats(business_id: int) -> Dict[str, int]:
        """Calcula estadísticas adicionales del negocio"""
        try:
            # Obtener conteos de forma eficiente
            products_count = Product.objects.filter(fk_business=business_id).count()
            areas_count = Area.objects.filter(fk_product__fk_business=business_id).count()
            simulations_count = Simulation.objects.filter(
                fk_questionary_result__fk_questionary__fk_product__fk_business=business_id
            ).count()
            charts_count = Chart.objects.filter(
                fk_product__fk_business=business_id,
                is_active=True
            ).count()
            
            return {
                'products_count': products_count,
                'areas_count': areas_count,
                'simulations_count': simulations_count,
                'charts_count': charts_count,
            }
        except Exception as e:
            logger.error(f"Error calculating business stats: {e}")
            return {
                'products_count': 0,
                'areas_count': 0,
                'simulations_count': 0,
                'charts_count': 0,
            }
    
    @staticmethod
    def get_percentage_changes(business_id: int, current_totals: Dict[str, float]) -> Dict[str, float]:
        """Calcula los cambios porcentuales comparando con el mes anterior"""
        try:
            # Obtener fecha actual y mes anterior
            today = timezone.now()
            last_month = today - relativedelta(months=1)
            
            # Obtener simulaciones del mes anterior
            last_month_simulations = Simulation.objects.filter(
                fk_questionary_result__fk_questionary__fk_product__fk_business=business_id,
                date_created__year=last_month.year,
                date_created__month=last_month.month
            ).select_related(
                'fk_questionary_result__fk_questionary__fk_product'
            ).prefetch_related('results')
            
            # Calcular totales del mes anterior
            last_month_totals = DashboardService.calculate_totals(last_month_simulations)
            
            # Calcular cambios porcentuales
            changes = {}
            metrics = ['Total Revenue', 'Total Costs', 'Total Profit Margin', 
                      'Total Inventory Levels', 'Total Demand', 'Total Production Output']
            
            for metric in metrics:
                current = current_totals.get(metric, 0)
                previous = last_month_totals.get(metric, 0)
                
                if previous > 0:
                    change = ((current - previous) / previous) * 100
                    changes[metric.replace('Total ', '').lower() + '_change'] = round(change, 1)
                else:
                    # Si no hay datos del mes anterior, asumir crecimiento del 0%
                    changes[metric.replace('Total ', '').lower() + '_change'] = 0.0
            
            return changes
            
        except Exception as e:
            logger.error(f"Error calculating percentage changes: {e}")
            # Retornar cambios por defecto en caso de error
            return {
                'revenue_change': 0.0,
                'costs_change': 0.0,
                'profit_margin_change': 0.0,
                'inventory_levels_change': 0.0,
                'demand_change': 0.0,
                'production_output_change': 0.0,
            }

    @staticmethod
    def get_business_recommendations_with_simulations(business_id: int):
        """
        Obtiene las recomendaciones del negocio junto con sus simulaciones más recientes
        """
        try:
            # Obtener recomendaciones del negocio
            business_recommendations = FinanceRecommendation.objects.filter(
                fk_business_id=business_id,
                is_active=True
            ).prefetch_related('recommendation_simulations')
            
            # Obtener simulaciones recientes
            recent_simulations = FinanceRecommendationSimulation.objects.filter(
                fk_simulation__fk_questionary_result__fk_questionary__fk_product__fk_business=business_id
            ).select_related(
                'fk_simulation__fk_questionary_result__fk_questionary__fk_product'
            ).order_by('-fk_simulation__date_created')[:10]
            
            # Combinar datos para el template
            recommendations_data = []
            
            for sim in recent_simulations:
                # Intentar asociar con una recomendación existente del negocio
                recommendation = business_recommendations.first() if business_recommendations.exists() else None
                
                recommendations_data.append({
                    'id': sim.id,
                    'simulation_date': sim.fk_simulation.date_created,
                    'product_name': sim.fk_simulation.fk_questionary_result.fk_questionary.fk_product.name,
                    'data': sim.data,
                    'data_percentage': sim.data * 100,
                    'variable_name': recommendation.variable_name if recommendation else 'Análisis General',
                    'threshold_value': recommendation.threshold_value if recommendation else None,
                    'recommendation_text': recommendation.recommendation if recommendation else f'Simulación realizada el {sim.fk_simulation.date_created.strftime("%d/%m/%Y")}',
                })
            
            return recommendations_data
            
        except Exception as e:
            logger.error(f"Error getting business recommendations: {e}")
            return []
    
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
        
        # Si no hay negocio, mostrar valores por defecto
        if not business:
            context = {
                'form': form,
                'business': None,
                'business_count': 0,
                'products_count': 0,
                'simulations_count': 0,
                'charts_count': 0,
            }
            return render(request, 'dashboards/index.html', context)

        # Si hay negocio, continuar con la lógica normal
        request.session['business_id'] = business.id

        # Obtener métricas del negocio para los contadores
        metrics = DashboardService.get_business_metrics(business.id)
        business_count = Business.objects.filter(fk_user=request.user, is_active=True).count()
        products_count = metrics['products'].count()
        simulations_count = metrics['simulations'].count() if hasattr(metrics['simulations'], 'count') else len(metrics['simulations'])
        # charts_count = metrics['charts'].count() if hasattr(metrics['charts'], 'count') else len(metrics['charts'])

        # Get recent activities for the user
        recent_activities = ActivityLog.objects.filter(
            user=request.user
        ).select_related('user').order_by('-timestamp')[:30]

        context = {
            'form': form,
            'business': business,
            'business_count': business_count,
            'products_count': products_count,
            'simulations_count': simulations_count,
            # 'charts_count': charts_count,
            'recent_activities': recent_activities
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
        
        # Obtener recomendaciones con datos disponibles
        recommendations_query = FinanceRecommendationSimulation.objects.filter(
            fk_simulation__fk_questionary_result__fk_questionary__fk_product__fk_business=business_id,
        ).select_related(
            'fk_simulation__fk_questionary_result__fk_questionary__fk_product'
        ).annotate(
            product_name=F('fk_simulation__fk_questionary_result__fk_questionary__fk_product__name'),
            simulation_date=F('fk_simulation__date_created'),
            data_percentage=F('data') * 100
        ).order_by('-simulation_date')
        
        # Paginación
        paginator = Paginator(recommendations_query, 10)
        page_obj = paginator.get_page(request.GET.get('page'))
        
        # Calcular totales
        totals = DashboardService.calculate_totals(metrics['simulations'])
        
        # Obtener actividad reciente con más detalles
        recent_activity = ActivityLog.objects.filter(
            user=request.user
        ).select_related('user').order_by('-timestamp')[:10]
        
        # Obtener todos los negocios del usuario
        businesses = Business.objects.filter(
            fk_user=request.user,
            is_active=True
        ).order_by('-id')
        
        # Obtener productos y áreas del negocio actual
        products = metrics['products']
        areas = Area.objects.filter(
            fk_product__in=products
        ).select_related('fk_product')
        
        # Calcular estadísticas adicionales del negocio
        business_stats = DashboardService.calculate_business_stats(business_id)
        
        # Calcular cambios porcentuales comparando con el mes anterior
        percentage_changes = DashboardService.get_percentage_changes(business_id, totals)
        
        # Obtener gráficos con datos completos
        charts = metrics['charts']
        
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
            'products': products,
            'areas': areas,
            'charts': charts,
            'page_obj': page_obj,
            'recent_activity': recent_activity,
            
            # Métricas financieras
            'total_revenue': totals.get('Total Revenue', 0),
            'total_costs': totals.get('Total Costs', 0),
            'total_inventory_levels': totals.get('Total Inventory Levels', 0),
            'total_demand': totals.get('Total Demand', 0),
            'total_production_output': totals.get('Total Production Output', 0),
            'total_profit_margin': totals.get('Total Profit Margin', 0),
            
            # Contadores para las cards de estadísticas
            'business_count': businesses.count(),
            'products_count': business_stats['products_count'],
            'simulations_count': business_stats['simulations_count'],
            'charts_count': business_stats['charts_count'],
            
            # Cambios porcentuales (usando datos reales)
            'revenue_change': percentage_changes.get('revenue_change', 0.0),
            'costs_change': percentage_changes.get('costs_change', 0.0),
            'profit_change': percentage_changes.get('profit_margin_change', 0.0),
            'inventory_change': percentage_changes.get('inventory_levels_change', 0.0),
            'demand_change': percentage_changes.get('demand_change', 0.0),
            'production_change': percentage_changes.get('production_output_change', 0.0),
            
            # Datos adicionales del negocio
            'business_type_display': business.get_type_display() if hasattr(business, 'get_type_display') else 'Otros',
            'business_location': getattr(business, 'location', 'No especificada'),
            'business_description': getattr(business, 'description', 'Sin descripción'),
            
            # URLs y configuraciones
            'can_export': True,
            'can_print': True,
        }
        
        # Debug para verificar datos
        logger.info(f"Dashboard context for user {request.user.id}: business={business.name}, products={products.count()}, recommendations={page_obj.paginator.count}")
        
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
        finance_recommendation_simulations__fk_business=business_id,
        is_active=True
    ).select_related(
        'fk_simulation__fk_questionary_result__fk_questionary__fk_product',
        'finance_recommendation_simulations'
    )
    
    # Crear respuesta CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="recomendaciones_{business.name}_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Fecha', 'Producto', 'Variable', 'Valor (%)', 
        'Umbral', 'Recomendación'
    ])
    
    # for rec in recommendations:
    #     writer.writerow([
    #         rec.fk_simulation.date_created.strftime('%Y-%m-%d'),
    #         rec.fk_simulation.fk_questionary_result.fk_questionary.fk_product.name,
    #         rec.finance_recommendation_simulations.variable_name,
    #         f"{rec.data * 100:.2f}",
    #         rec.finance_recommendation_simulations.threshold_value,
    #         rec.finance_recommendation_simulations.recommendation
    #     ])
    
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

