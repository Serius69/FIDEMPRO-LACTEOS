from typing import Dict, Any, Optional, Tuple
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import Http404, JsonResponse
from django.db.models import Max, F, Prefetch, Count, Q, Sum, Avg, Min, Subquery, OuterRef
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
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
        """Obtiene las métricas del negocio de forma optimizada para MySQL"""
        # Usar agregación para obtener todas las métricas en una sola consulta
        products = Product.objects.filter(
            fk_business=business_id
        ).prefetch_related(
            Prefetch('fk_product_area', queryset=Area.objects.select_related('fk_product'))
        )
        
        # Obtener IDs de productos para consultas posteriores
        product_ids = list(products.values_list('id', flat=True))
        
        # MYSQL OPTIMIZED: Obtener últimos gráficos usando subquery
        latest_chart_subquery = Chart.objects.filter(
            fk_product_id=OuterRef('fk_product_id'),
            is_active=True
        ).order_by('-id').values('id')[:1]
        
        charts = Chart.objects.filter(
            fk_product_id__in=product_ids,
            is_active=True,
            id__in=Subquery(latest_chart_subquery)
        ).select_related('fk_product')
        
        # MYSQL OPTIMIZED: Obtener simulaciones únicas usando GROUP BY
        simulations = Simulation.objects.filter(
            fk_questionary_result__fk_questionary__fk_product_id__in=product_ids
        ).select_related(
            'fk_questionary_result__fk_questionary__fk_product',
            'fk_fdp'
        ).prefetch_related(
            'results'
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
        try:
            variable_mapping = dict(
                Variable.objects.filter(
                    initials__in=variables_to_search
                ).values_list('initials', 'name')
            )
        except Exception:
            variable_mapping = {}
        
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
        
        # MYSQL OPTIMIZED: Usar set para evitar duplicados más eficientemente
        processed_simulations = set()
        
        try:
            for simulation in simulations:
                # Skip if already processed
                if simulation.id in processed_simulations:
                    continue
                processed_simulations.add(simulation.id)
                
                # Verificar si simulation tiene results
                try:
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
                                    try:
                                        variables = json.loads(result.variables) if isinstance(result.variables, str) else result.variables
                                    except (json.JSONDecodeError, TypeError):
                                        variables = {}
                            
                            if variables and isinstance(variables, dict):
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
                    logger.error(f"Error accessing results for simulation {simulation.id}: {e}")
                    continue
                        
        except Exception as e:
            logger.error(f"Error calculating totals: {e}")
            
        return totals
    
    @staticmethod
    def calculate_business_stats(business_id: int) -> Dict[str, int]:
        """Calcula estadísticas adicionales del negocio"""
        try:
            # MYSQL OPTIMIZED: Usar una sola consulta con COUNT
            stats = Business.objects.filter(
                id=business_id
            ).aggregate(
                products_count=Count('fk_business_product', distinct=True),
                simulations_count=Count(
                    'fk_business_product__fk_product_questionary__results__fk_simulation',
                    distinct=True
                ),
                charts_count=Count(
                    'fk_business_product__fk_product_chart',
                    filter=Q(fk_business_product__fk_product_chart__is_active=True),
                    distinct=True
                )
            )
            
            # Calcular areas por separado para evitar joins complejos
            areas_count = Area.objects.filter(fk_product__fk_business=business_id).count()
            
            return {
                'products_count': stats.get('products_count', 0),
                'areas_count': areas_count,
                'simulations_count': stats.get('simulations_count', 0),
                'charts_count': stats.get('charts_count', 0),
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
            
            # MYSQL OPTIMIZED: Obtener simulaciones del mes anterior con índices
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
                    changes[metric.replace('Total ', '').lower().replace(' ', '_') + '_change'] = round(change, 1)
                else:
                    # Si no hay datos del mes anterior, asumir crecimiento del 0%
                    changes[metric.replace('Total ', '').lower().replace(' ', '_') + '_change'] = 0.0
            
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
    def get_business_kpis(business_id: int) -> Dict[str, Any]:
        """Calcula KPIs clave del negocio"""
        try:
            metrics = DashboardService.get_business_metrics(business_id)
            totals = DashboardService.calculate_totals(metrics['simulations'])
            
            # Calcular KPIs
            revenue = totals.get('Total Revenue', 0)
            costs = totals.get('Total Costs', 0)
            profit_margin = ((revenue - costs) / revenue * 100) if revenue > 0 else 0
            roi = ((revenue - costs) / costs * 100) if costs > 0 else 0
            
            return {
                'profit_margin_percentage': round(profit_margin, 1),
                'roi_percentage': round(roi, 1),
                'total_products': metrics['products'].count(),
                'active_simulations': metrics['simulations'].count(),
                'efficiency_score': min(100, max(0, round((profit_margin + roi) / 2, 1))) if profit_margin > 0 or roi > 0 else 0,
            }
            
        except Exception as e:
            logger.error(f"Error calculating KPIs: {e}")
            return {
                'profit_margin_percentage': 0,
                'roi_percentage': 0,
                'total_products': 0,
                'active_simulations': 0,
                'efficiency_score': 0,
            }
    
    @staticmethod
    def _calculate_growth_rate(monthly_data: list) -> float:
        """Calcula la tasa de crecimiento promedio"""
        if len(monthly_data) < 2:
            return 0
        
        try:
            first_revenue = monthly_data[0]['revenue']
            last_revenue = monthly_data[-1]['revenue']
            
            if first_revenue > 0:
                growth_rate = ((last_revenue - first_revenue) / first_revenue) * 100
                return round(growth_rate, 1)
        except (KeyError, TypeError, ZeroDivisionError):
            pass
        
        return 0
    
    @staticmethod
    def get_performance_trends(business_id: int) -> Dict[str, Any]:
        """MYSQL OPTIMIZED: Obtiene tendencias de rendimiento usando agregaciones eficientes"""
        try:
            # Obtener datos de los últimos 6 meses
            today = timezone.now()
            six_months_ago = today - relativedelta(months=6)
            
            # MYSQL OPTIMIZED: Usar una sola consulta con GROUP BY para obtener datos mensuales
            monthly_simulations = Simulation.objects.filter(
                fk_questionary_result__fk_questionary__fk_product__fk_business=business_id,
                date_created__gte=six_months_ago
            ).extra(
                select={
                    'month': "DATE_FORMAT(date_created, '%%Y-%%m')",
                    'month_name': "DATE_FORMAT(date_created, '%%b %%Y')"
                }
            ).values('month', 'month_name').annotate(
                simulations_count=Count('id')
            ).order_by('month')
            
            # Procesar datos mensuales
            monthly_data = []
            month_simulation_map = {item['month']: item for item in monthly_simulations}
            
            for i in range(6):
                month_start = six_months_ago + relativedelta(months=i)
                month_key = month_start.strftime('%Y-%m')
                month_name = month_start.strftime('%b %Y')
                
                # Obtener simulaciones del mes específico
                month_sims = Simulation.objects.filter(
                    fk_questionary_result__fk_questionary__fk_product__fk_business=business_id,
                    date_created__year=month_start.year,
                    date_created__month=month_start.month
                )
                
                month_totals = DashboardService.calculate_totals(month_sims)
                sim_count = month_simulation_map.get(month_key, {}).get('simulations_count', 0)
                
                monthly_data.append({
                    'month': month_name,
                    'revenue': month_totals.get('Total Revenue', 0),
                    'costs': month_totals.get('Total Costs', 0),
                    'profit': month_totals.get('Total Profit Margin', 0),
                    'simulations_count': sim_count
                })
            
            return {
                'monthly_trends': monthly_data,
                'growth_rate': DashboardService._calculate_growth_rate(monthly_data),
            }
            
        except Exception as e:
            logger.error(f"Error getting performance trends: {e}")
            return {'monthly_trends': [], 'growth_rate': 0}
    
    @staticmethod
    def get_top_products(business_id: int) -> list:
        """MYSQL OPTIMIZED: Obtiene los productos con mejor rendimiento usando subqueries"""
        try:
            # MYSQL OPTIMIZED: Usar subquery para contar simulaciones
            products = Product.objects.filter(
                fk_business=business_id
            ).annotate(
                simulations_count=Count(
                    'fk_product_questionary__results__fk_simulation',
                    distinct=True
                ),
                latest_simulation_date=Max(
                    'fk_product_questionary__results__fk_simulation__date_created'
                )
            ).order_by('-simulations_count', '-latest_simulation_date')[:5]
            
            return list(products)
            
        except Exception as e:
            logger.error(f"Error getting top products: {e}")
            return []
    
    @staticmethod
    def get_business_recommendations_with_simulations(business_id: int):
        """
        MYSQL OPTIMIZED: Obtiene recomendaciones únicas usando GROUP BY
        """
        try:
            # MYSQL OPTIMIZED: Usar GROUP BY en lugar de DISTINCT ON
            recent_simulations = FinanceRecommendationSimulation.objects.filter(
                fk_simulation__fk_questionary_result__fk_questionary__fk_product__fk_business=business_id
            ).select_related(
                'fk_simulation__fk_questionary_result__fk_questionary__fk_product'
            ).values(
                'fk_simulation_id',
                'fk_simulation__date_created',
                'fk_simulation__fk_questionary_result__fk_questionary__fk_product__name'
            ).annotate(
                latest_id=Max('id'),
                data_value=Max('data')  # Asumiendo que quieres el último valor
            ).order_by('-fk_simulation__date_created')[:20]
            
            recommendations_data = []
            
            for sim_data in recent_simulations:
                try:
                    # Obtener el objeto completo para el último registro
                    sim = FinanceRecommendationSimulation.objects.get(id=sim_data['latest_id'])
                    
                    # Obtener datos seguros
                    data_value = sim_data.get('data_value') or getattr(sim, 'data', 0.5)
                    if data_value is None:
                        data_value = 0.5
                    data_percentage = float(data_value) * 100
                    
                    recommendations_data.append({
                        'id': sim.id,
                        'simulation_date': sim_data['fk_simulation__date_created'],
                        'product_name': sim_data['fk_simulation__fk_questionary_result__fk_questionary__fk_product__name'],
                        'data': data_value,
                        'data_percentage': data_percentage,
                        'variable_name': 'Análisis General',
                        'threshold_value': None,
                        'recommendation_text': f'Simulación realizada el {sim_data["fk_simulation__date_created"].strftime("%d/%m/%Y")}',
                        'simulation_id': sim_data['fk_simulation_id'],
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing simulation data: {e}")
                    continue
            
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
                messages.success(request, "Elementos registrados correctamente")
                return redirect('dashboard:index')
        else:
            form = RegisterElementsForm()

        business = DashboardService.get_user_business(request.user)
        
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

        request.session['business_id'] = business.id
        metrics = DashboardService.get_business_metrics(business.id)
        business_count = Business.objects.filter(fk_user=request.user, is_active=True).count()
        products_count = metrics['products'].count()
        simulations_count = metrics['simulations'].count()

        recent_activities = ActivityLog.objects.filter(
            user=request.user
        ).select_related('user').order_by('-timestamp')[:30]

        context = {
            'form': form,
            'business': business,
            'business_count': business_count,
            'products_count': products_count,
            'simulations_count': simulations_count,
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
    """Dashboard principal del usuario con todas las métricas del negocio - MYSQL OPTIMIZED"""
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
        
        # MYSQL OPTIMIZED: Obtener métricas del negocio
        metrics = DashboardService.get_business_metrics(business_id)
        
        # MYSQL OPTIMIZED: Obtener recomendaciones sin duplicados
        recommendations_data = DashboardService.get_business_recommendations_with_simulations(business_id)
        
        # Paginación para recomendaciones
        paginator = Paginator(recommendations_data, 10)
        page_obj = paginator.get_page(request.GET.get('page'))
        
        # Calcular totales directamente
        totals = DashboardService.calculate_totals(metrics['simulations'])
        
        # Obtener tendencias de rendimiento
        performance_trends = DashboardService.get_performance_trends(business_id)
        
        # Obtener productos top
        top_products = DashboardService.get_top_products(business_id)
        
        # Calcular KPIs del negocio
        business_kpis = DashboardService.get_business_kpis(business_id)
        
        # Obtener actividad reciente con más detalles
        recent_activity = ActivityLog.objects.filter(
            user=request.user
        ).select_related('user').order_by('-timestamp')[:10]
        
        # Obtener todos los negocios del usuario
        businesses = Business.objects.filter(
            fk_user=request.user,
            is_active=True
        ).order_by('-id')
        
        # Calcular estadísticas adicionales del negocio
        business_stats = DashboardService.calculate_business_stats(business_id)
        
        # Calcular cambios porcentuales
        percentage_changes = DashboardService.get_percentage_changes(business_id, totals)
        
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
            'charts': metrics['charts'],
            'page_obj': page_obj,
            'recent_activity': recent_activity,
            
            # Métricas financieras
            'total_revenue': totals.get('Total Revenue', 0),
            'total_costs': totals.get('Total Costs', 0),
            'total_inventory_levels': totals.get('Total Inventory Levels', 0),
            'total_demand': totals.get('Total Demand', 0),
            'total_production_output': totals.get('Total Production Output', 0),
            'total_profit_margin': totals.get('Total Profit Margin', 0),
            
            # KPIs del negocio
            'profit_margin_percentage': business_kpis['profit_margin_percentage'],
            'roi_percentage': business_kpis['roi_percentage'],
            'efficiency_score': business_kpis['efficiency_score'],
            
            # Contadores para las cards de estadísticas
            'business_count': businesses.count(),
            'products_count': business_stats['products_count'],
            'simulations_count': business_stats['simulations_count'],
            'charts_count': business_stats['charts_count'],
            
            # Cambios porcentuales
            'revenue_change': percentage_changes.get('revenue_change', 0.0),
            'costs_change': percentage_changes.get('costs_change', 0.0),
            'profit_change': percentage_changes.get('profit_margin_change', 0.0),
            'inventory_change': percentage_changes.get('inventory_levels_change', 0.0),
            'demand_change': percentage_changes.get('demand_change', 0.0),
            'production_change': percentage_changes.get('production_output_change', 0.0),
            
            # Nuevos datos para dashboard ejecutivo
            'performance_trends': performance_trends,
            'top_products': top_products,
            'monthly_trends_json': json.dumps(performance_trends['monthly_trends']),
            'growth_rate': performance_trends['growth_rate'],
            
            # Datos adicionales del negocio
            'business_type_display': business.get_type_display() if hasattr(business, 'get_type_display') else 'Otros',
            'business_location': getattr(business, 'location', 'No especificada'),
            'business_description': getattr(business, 'description', 'Sin descripción'),
            
            # URLs y configuraciones
            'can_export': True,
            'can_print': True,
        }
        
        # Debug para verificar datos
        logger.info(f"Dashboard context for user {request.user.id}: business={business.name}, products={metrics['products'].count()}, unique_recommendations={len(recommendations_data)}")
        
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

