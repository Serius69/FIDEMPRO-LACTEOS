"""
Enhanced Dashboard Service - Servicio mejorado para las URLs existentes
Mantiene compatibilidad total con las funciones actuales
"""

import json
import logging
import statistics
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from dataclasses import dataclass, asdict

from django.db.models import (
    Count, Sum, Avg, Max, Min, F, Q, 
    Case, When, DecimalField, FloatField,
    Subquery, OuterRef, Value
)
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.core.cache import cache
from dateutil.relativedelta import relativedelta

# Imports de modelos
from variable.models import Variable
from user.models import ActivityLog
from product.models import Product, Area
from finance.models import FinanceRecommendation, FinanceRecommendationSimulation
from business.models import Business
from dashboards.models import Chart
from simulate.models import ResultSimulation, Simulation, Demand, DemandBehavior

# Configurar logger
logger = logging.getLogger(__name__)

@dataclass
class BusinessMetrics:
    """Métricas del negocio mejoradas"""
    revenue: float = 0.0
    costs: float = 0.0
    profit: float = 0.0
    profit_margin: float = 0.0
    roi: Optional[float] = None
    inventory: float = 0.0
    demand: float = 0.0
    production: float = 0.0
    efficiency_score: float = 0.0
    growth_rate: float = 0.0

class DashboardService:
    """
    Servicio de Dashboard mejorado - Compatible con URLs existentes
    Mantiene todas las funciones originales pero mejoradas
    """
    
    # Configuración
    CACHE_TIMEOUT = 300  # 5 minutos
    
    # Mapeo de variables mejorado
    VARIABLES_MAPPING = {
        'TPV': 'revenue',
        'IT': 'costs', 
        'GT': 'profit',
        'TG': 'inventory',
        'DT': 'demand',
        'Production': 'production'
    }

    @classmethod
    def get_user_business(cls, user) -> Optional[Business]:
        """Obtiene el negocio activo del usuario - MEJORADO"""
        cache_key = f"user_business_{user.id}"
        business = cache.get(cache_key)
        
        if not business:
            try:
                business = Business.objects.filter(
                    fk_user=user, 
                    is_active=True
                ).select_related('fk_user').first()
                
                if business:
                    cache.set(cache_key, business, cls.CACHE_TIMEOUT)
            except Exception as e:
                logger.error(f"Error getting user business: {e}")
                return None
                
        return business

    @classmethod
    def get_complete_dashboard_data(cls, business_id: int, user) -> Dict[str, Any]:
        """
        Obtiene todos los datos del dashboard de manera optimizada
        NUEVA FUNCIÓN PRINCIPAL que unifica todo
        """
        cache_key = f"dashboard_complete_{business_id}_{user.id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            # Validar negocio
            business = cls._get_validated_business(business_id, user)
            if not business:
                return cls._get_empty_dashboard_data()
            
            # Obtener datos base optimizados
            products = cls._get_business_products(business_id)
            simulations = cls._get_business_simulations(business_id)
            charts = cls._get_business_charts(business_id)
            
            # Calcular métricas mejoradas
            financial_metrics = cls._calculate_enhanced_metrics(simulations)
            
            # Obtener estadísticas del negocio
            business_stats = cls._get_enhanced_business_stats(business_id, products, simulations)
            
            # Calcular cambios porcentuales mejorados
            percentage_changes = cls._calculate_enhanced_percentage_changes(business_id, financial_metrics)
            
            # Obtener tendencias mejoradas
            performance_trends = cls._get_enhanced_performance_trends(business_id)
            
            # Obtener recomendaciones únicas sin duplicados
            recommendations = cls._get_enhanced_recommendations(business_id)
            
            # Obtener actividad reciente
            recent_activity = cls._get_recent_activity(user)
            
            # Calcular KPIs avanzados
            business_kpis = cls._calculate_enhanced_kpis(financial_metrics)
            
            # Generar alertas inteligentes
            business_alerts = cls._generate_enhanced_alerts(financial_metrics, percentage_changes, business_kpis)
            
            # Obtener top productos
            top_products = cls._get_enhanced_top_products(business_id)
            
            result = {
                'business': business,
                'products': products,
                'simulations': simulations,
                'charts': charts,
                'financial_metrics': asdict(financial_metrics),
                'business_stats': business_stats,
                'percentage_changes': percentage_changes,
                'performance_trends': performance_trends,
                'recommendations': recommendations,
                'recent_activity': recent_activity,
                'business_kpis': business_kpis,
                'business_alerts': business_alerts,
                'top_products': top_products,
                'summary': cls._generate_business_summary(financial_metrics, business_kpis),
                'last_updated': timezone.now().isoformat()
            }
            
            # Guardar en caché
            cache.set(cache_key, result, cls.CACHE_TIMEOUT)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting complete dashboard data: {e}")
            return cls._get_empty_dashboard_data()

    @classmethod
    def _get_validated_business(cls, business_id: int, user) -> Optional[Business]:
        """Valida y obtiene el negocio del usuario"""
        try:
            return Business.objects.select_related('fk_user').get(
                pk=business_id,
                is_active=True,
                fk_user=user
            )
        except Business.DoesNotExist:
            logger.warning(f"Business {business_id} not found for user {user.id}")
            return None

    @classmethod
    def _get_business_products(cls, business_id: int) -> List[Product]:
        """Obtiene productos del negocio optimizado"""
        return list(Product.objects.filter(
            fk_business=business_id, is_active=True
        ).select_related('fk_business').prefetch_related('fk_product_area'))

    @classmethod
    def _get_business_simulations(cls, business_id: int) -> List[Simulation]:
        """Obtiene simulaciones del negocio optimizado"""
        return list(Simulation.objects.filter(
            fk_questionary_result__fk_questionary__fk_product__fk_business=business_id
        ).select_related(
            'fk_questionary_result__fk_questionary__fk_product',
            'fk_fdp'
        ).prefetch_related('results').order_by('-date_created')[:100])  # Limitar para rendimiento

    @classmethod
    def _get_business_charts(cls, business_id: int) -> List[Chart]:
        """Obtiene gráficos del negocio optimizado"""
        try:
            return list(Chart.objects.filter(
                fk_product__fk_business=business_id,
                is_active=True
            ).select_related('fk_product').order_by('-id')[:20])  # Últimos 20 gráficos
        except Exception as e:
            logger.error(f"Error getting business charts: {e}")
            return []

    # Mapeo variable-de-simulación -> atributo acumulable de BusinessMetrics
    _METRIC_VAR_ATTRS = {
        'TPV': 'revenue',
        'IT': 'costs',
        'GT': 'profit',
        'TG': 'inventory',
        'DT': 'demand',
        'Production': 'production',
    }

    @classmethod
    def _calculate_enhanced_metrics(cls, simulations: List[Simulation]) -> BusinessMetrics:
        """Calcula métricas financieras mejoradas y robustas.

        CONTEXTO / ESCALA (fix de agregación):
        Cada ``ResultSimulation`` es UN período (día/semana/mes) de una simulación
        y guarda en ``variables`` los totales de ese período (TPV, IT, GT, ...).
        La versión anterior SUMABA esas variables sobre TODOS los períodos de TODAS
        las simulaciones recibidas (hasta 100), produciendo cifras infladas por un
        factor ~ (nº de simulaciones) x (nº de períodos) que no representan al negocio.

        Aquí calculamos una cifra representativa a escala de UNA simulación:
        se toma únicamente la simulación MÁS RECIENTE de la lista recibida (la más
        relevante para el estado actual del negocio) y se PROMEDIA cada variable a
        través de sus períodos, obteniendo el valor esperado por período. Así
        revenue/costs/profit quedan en la escala de un período de una simulación,
        independiente del nº de simulaciones y del horizonte, y los derivados
            (profit_margin y KPIs operativos) resultan interpretables. ROI solo
            puede existir cuando hay una base explícita de inversión.
        """
        metrics = BusinessMetrics()

        if not simulations:
            return metrics

        try:
            # Simulación más reciente del subconjunto recibido (representa el
            # estado actual; los callers ya suelen pasar listas por período/producto).
            simulation = max(
                simulations,
                key=lambda s: getattr(s, 'date_created', None) or timezone.now()
            )

            # Obtener resultados (períodos) de esa simulación
            if hasattr(simulation, 'results') and hasattr(simulation.results, 'all'):
                results = list(simulation.results.all())
            else:
                results = list(ResultSimulation.objects.filter(fk_simulation=simulation))

            # Acumular por variable y contar períodos para promediar
            totals = {attr: 0.0 for attr in cls._METRIC_VAR_ATTRS.values()}
            periods = 0

            for result in results:
                variables_data = cls._extract_variables_safely(result)
                if not variables_data:
                    continue
                periods += 1
                for var_key, value in variables_data.items():
                    attr = cls._METRIC_VAR_ATTRS.get(var_key)
                    if attr:
                        totals[attr] += cls._safe_float_conversion(value)

            if periods > 0:
                # Promedio por período => cifra representativa a escala de 1 simulación
                for attr, total in totals.items():
                    setattr(metrics, attr, total / periods)

        except Exception as e:
            logger.error(f"Error calculating enhanced metrics: {e}")

        # Calcular métricas derivadas
        metrics.profit_margin = cls._calculate_profit_margin(metrics.revenue, metrics.costs)
        metrics.roi = cls._calculate_roi(metrics.profit, investment=None)
        metrics.efficiency_score = cls._calculate_efficiency_score(metrics)

        # Redondear valores
        for field in metrics.__dataclass_fields__:
            value = getattr(metrics, field)
            if isinstance(value, (int, float)):
                setattr(metrics, field, round(value, 2))

        return metrics

    @classmethod
    def _extract_variables_safely(cls, result: ResultSimulation) -> Dict[str, Any]:
        """Extrae variables de manera segura y robusta"""
        try:
            # Intentar múltiples métodos de extracción
            if hasattr(result, 'get_variables') and callable(result.get_variables):
                variables = result.get_variables()
                if variables and isinstance(variables, dict):
                    return variables
            
            if hasattr(result, 'variables') and result.variables:
                if isinstance(result.variables, str):
                    try:
                        return json.loads(result.variables)
                    except json.JSONDecodeError:
                        pass
                elif isinstance(result.variables, dict):
                    return result.variables
            
            # Fallback: intentar extraer de campos del modelo
            variables = {}
            field_mapping = {
                'revenue': 'TPV',
                'costs': 'IT',
                'profit': 'GT',
                'inventory': 'TG',
                'demand': 'DT',
                'production': 'Production'
            }
            
            for field_name, var_key in field_mapping.items():
                if hasattr(result, field_name):
                    value = getattr(result, field_name)
                    if value is not None:
                        variables[var_key] = value
            
            return variables
            
        except Exception as e:
            logger.debug(f"Error extracting variables from result {getattr(result, 'id', 'unknown')}: {e}")
            return {}

    @classmethod
    def _safe_float_conversion(cls, value: Any) -> float:
        """Conversión segura y robusta a float"""
        if value is None:
            return 0.0
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, Decimal):
            return float(value)
        
        if isinstance(value, str):
            # Limpiar string y convertir
            cleaned = ''.join(c for c in value if c.isdigit() or c in '.-+')
            if cleaned and cleaned not in ['.', '-', '+']:
                try:
                    return float(cleaned)
                except ValueError:
                    pass
        
        return 0.0

    @classmethod
    def _calculate_profit_margin(cls, revenue: float, costs: float) -> float:
        """Calcula margen de beneficio"""
        if revenue > 0:
            return ((revenue - costs) / revenue) * 100
        return 0.0

    @classmethod
    def _calculate_roi(cls, profit: float, investment: Optional[float]) -> Optional[float]:
        """Calculate ROI only from an explicit invested-capital basis."""
        if investment is None or investment <= 0:
            return None
        return (profit / investment) * 100

    @classmethod
    def _calculate_efficiency_score(cls, metrics: BusinessMetrics) -> float:
        """Calcula score de eficiencia"""
        try:
            factors = []
            
            # Factor de margen
            if metrics.revenue > 0:
                margin_factor = min(100, max(0, metrics.profit_margin))
                factors.append(margin_factor)
            
            # Factor de productividad
            if metrics.costs > 0:
                productivity_factor = min(100, (metrics.revenue / metrics.costs) * 50)
                factors.append(productivity_factor)
            
            # Factor de rotación (simulado)
            if metrics.inventory > 0:
                turnover_factor = min(100, (metrics.revenue / metrics.inventory) * 10)
                factors.append(turnover_factor)
            
            return sum(factors) / len(factors) if factors else 0
            
        except Exception:
            return 0.0

    @classmethod
    def _get_enhanced_business_stats(cls, business_id: int, products: List[Product], simulations: List[Simulation]) -> Dict[str, int]:
        """Obtiene estadísticas mejoradas del negocio"""
        try:
            # Contar áreas de manera eficiente
            areas_count = Area.objects.filter(
                fk_product__fk_business=business_id,
                is_active=True,
                fk_product__is_active=True,
            ).count()
            
            # Contar gráficos activos
            charts_count = Chart.objects.filter(
                fk_product__fk_business=business_id,
                is_active=True
            ).count()
            
            # Estadísticas adicionales
            active_products = len([p for p in products if hasattr(p, 'is_active') and getattr(p, 'is_active', True)])
            recent_simulations = len([s for s in simulations if s.date_created >= timezone.now() - timedelta(days=30)])
            
            return {
                'products_count': len(products),
                'active_products_count': active_products,
                'areas_count': areas_count,
                'simulations_count': len(simulations),
                'recent_simulations_count': recent_simulations,
                'charts_count': charts_count,
            }
        except Exception as e:
            logger.error(f"Error calculating enhanced business stats: {e}")
            return {
                'products_count': 0,
                'active_products_count': 0,
                'areas_count': 0,
                'simulations_count': 0,
                'recent_simulations_count': 0,
                'charts_count': 0,
            }

    @classmethod
    def _calculate_enhanced_percentage_changes(cls, business_id: int, current_metrics: BusinessMetrics) -> Dict[str, float]:
        """Calcula cambios porcentuales mejorados"""
        try:
            # Obtener datos del mes anterior
            today = timezone.now()
            last_month = today - relativedelta(months=1)
            
            last_month_simulations = Simulation.objects.filter(
                fk_questionary_result__fk_questionary__fk_product__fk_business=business_id,
                date_created__year=last_month.year,
                date_created__month=last_month.month
            ).select_related(
                'fk_questionary_result__fk_questionary__fk_product'
            ).prefetch_related('results')
            
            last_month_metrics = cls._calculate_enhanced_metrics(list(last_month_simulations))
            
            # Calcular cambios
            changes = {}
            metrics_to_compare = [
                ('revenue', 'revenue_change'),
                ('costs', 'costs_change'),
                ('profit', 'profit_change'),
                ('profit_margin', 'profit_margin_change'),
                ('inventory', 'inventory_change'),
                ('demand', 'demand_change'),
                ('production', 'production_change')
            ]
            
            for current_attr, change_key in metrics_to_compare:
                current_value = getattr(current_metrics, current_attr)
                previous_value = getattr(last_month_metrics, current_attr)
                
                if previous_value > 0:
                    change = ((current_value - previous_value) / previous_value) * 100
                    changes[change_key] = round(change, 1)
                else:
                    changes[change_key] = 0.0
            
            return changes
            
        except Exception as e:
            logger.error(f"Error calculating enhanced percentage changes: {e}")
            return {
                'revenue_change': 0.0,
                'costs_change': 0.0,
                'profit_change': 0.0,
                'profit_margin_change': 0.0,
                'inventory_change': 0.0,
                'demand_change': 0.0,
                'production_change': 0.0,
            }

    @classmethod
    def _get_enhanced_performance_trends(cls, business_id: int) -> Dict[str, Any]:
        """Obtiene tendencias de rendimiento mejoradas (1 query en lugar de 6)."""
        try:
            today = timezone.now()
            six_months_ago = today - relativedelta(months=6)

            # Una sola query para todo el rango de 6 meses con prefetch de resultados
            all_simulations = list(
                Simulation.objects.filter(
                    fk_questionary_result__fk_questionary__fk_product__fk_business=business_id,
                    date_created__gte=six_months_ago,
                ).select_related(
                    'fk_questionary_result__fk_questionary__fk_product'
                ).prefetch_related('results')
                .order_by('date_created')
            )

            # Agrupar en Python por mes (O(n) sobre las simulaciones del período)
            from collections import defaultdict
            sims_by_month: Dict[str, list] = defaultdict(list)
            for sim in all_simulations:
                sims_by_month[sim.date_created.strftime('%b %Y')].append(sim)

            monthly_data = []
            for i in range(6):
                month_start = six_months_ago + relativedelta(months=i)
                month_key = month_start.strftime('%b %Y')
                month_sims = sims_by_month.get(month_key, [])
                month_metrics = cls._calculate_enhanced_metrics(month_sims)
                monthly_data.append({
                    'month': month_key,
                    'revenue': month_metrics.revenue,
                    'costs': month_metrics.costs,
                    'profit': month_metrics.profit,
                    'profit_margin': month_metrics.profit_margin,
                    'simulations_count': len(month_sims),
                })
            
            # Calcular tasa de crecimiento
            growth_rate = cls._calculate_growth_rate(monthly_data)
            
            return {
                'monthly_trends': monthly_data,
                'growth_rate': growth_rate,
                'has_data': len([m for m in monthly_data if m['simulations_count'] > 0]) > 0
            }
            
        except Exception as e:
            logger.error(f"Error getting enhanced performance trends: {e}")
            return {
                'monthly_trends': [],
                'growth_rate': 0,
                'has_data': False
            }

    @classmethod
    def _calculate_growth_rate(cls, monthly_data: List[Dict]) -> float:
        """Calcula tasa de crecimiento mejorada"""
        try:
            months_with_data = [m for m in monthly_data if m['simulations_count'] > 0]
            
            if len(months_with_data) < 2:
                return 0
            
            first_revenue = months_with_data[0]['revenue']
            last_revenue = months_with_data[-1]['revenue']
            
            if first_revenue > 0:
                growth_rate = ((last_revenue - first_revenue) / first_revenue) * 100
                return round(growth_rate, 1)
                
        except Exception:
            pass
        
        return 0

    @classmethod
    def _get_enhanced_recommendations(cls, business_id: int) -> List[Dict[str, Any]]:
        """Obtiene recomendaciones mejoradas sin duplicados"""
        try:
            # Usar GROUP BY para evitar duplicados
            recommendations_query = FinanceRecommendationSimulation.objects.filter(
                fk_simulation__fk_questionary_result__fk_questionary__fk_product__fk_business=business_id
            ).select_related(
                'fk_simulation__fk_questionary_result__fk_questionary__fk_product'
            ).values(
                'fk_simulation_id',
                'fk_simulation__date_created',
                'fk_simulation__fk_questionary_result__fk_questionary__fk_product__name'
            ).annotate(
                latest_id=Max('id'),
                # El campo 'data' fue eliminado en la migración
                # finance/0009_remove_financerecommendationsimulation_data.
                # 'metric_value' es su reemplazo canónico (el propio help_text
                # del campo 'data' decía "deprecado, usar metric_value").
                avg_metric=Avg('metric_value')
            ).order_by('-fk_simulation__date_created')[:20]

            recommendations = []

            for rec_data in recommendations_query:
                try:
                    data_value = rec_data.get('avg_metric') or 0.5
                    data_percentage = float(data_value) * 100
                    
                    recommendations.append({
                        'id': rec_data['latest_id'],
                        'simulation_id': rec_data['fk_simulation_id'],
                        'simulation_date': rec_data['fk_simulation__date_created'],
                        'product_name': rec_data['fk_simulation__fk_questionary_result__fk_questionary__fk_product__name'],
                        'data': data_value,
                        'data_percentage': round(data_percentage, 1),
                        'variable_name': 'Análisis General',
                        'status': cls._get_recommendation_status(data_percentage),
                        'recommendation_text': f'Simulación realizada el {rec_data["fk_simulation__date_created"].strftime("%d/%m/%Y")}'
                    })
                    
                except Exception as e:
                    logger.debug(f"Error processing recommendation: {e}")
                    continue
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting enhanced recommendations: {e}")
            return []

    @classmethod
    def _get_recommendation_status(cls, percentage: float) -> str:
        """Determina el estado de una recomendación"""
        if percentage >= 75:
            return 'Óptimo'
        elif percentage >= 50:
            return 'Regular'
        else:
            return 'Crítico'

    @classmethod
    def _get_recent_activity(cls, user) -> List[ActivityLog]:
        """Obtiene actividad reciente mejorada"""
        try:
            return list(ActivityLog.objects.filter(
                user=user
            ).select_related('user').order_by('-timestamp')[:15])
        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            return []

    @classmethod
    def _calculate_enhanced_kpis(cls, metrics: BusinessMetrics) -> Dict[str, Any]:
        """Calcula KPIs mejorados"""
        try:
            # KPIs básicos mejorados
            kpis = {
                'profit_margin_percentage': metrics.profit_margin,
                'roi_percentage': metrics.roi,
                'efficiency_score': metrics.efficiency_score,
                'net_profit': metrics.profit,
                'cost_ratio': (metrics.costs / metrics.revenue * 100) if metrics.revenue > 0 else 0
            }
            
            # KPIs adicionales
            kpis.update({
                'revenue_per_product': metrics.revenue / max(1, metrics.inventory) if metrics.inventory > 0 else 0,
                'demand_fulfillment': (metrics.production / metrics.demand * 100) if metrics.demand > 0 else 0,
                'operational_efficiency': metrics.efficiency_score,
                'financial_health': cls._calculate_financial_health_score(metrics)
            })
            
            # Redondear valores
            for key, value in kpis.items():
                if isinstance(value, (int, float)):
                    kpis[key] = round(value, 1)
            
            return kpis
            
        except Exception as e:
            logger.error(f"Error calculating enhanced KPIs: {e}")
            return {
                'profit_margin_percentage': 0,
                'roi_percentage': None,
                'efficiency_score': 0,
                'net_profit': 0,
                'cost_ratio': 0,
                'revenue_per_product': 0,
                'demand_fulfillment': 0,
                'operational_efficiency': 0,
                'financial_health': 0
            }

    @classmethod
    def _calculate_financial_health_score(cls, metrics: BusinessMetrics) -> float:
        """Calcula score de salud financiera"""
        try:
            scores = []
            
            # Score de rentabilidad
            if metrics.profit_margin > 20:
                scores.append(100)
            elif metrics.profit_margin > 10:
                scores.append(80)
            elif metrics.profit_margin > 5:
                scores.append(60)
            else:
                scores.append(30)
            
            # ROI is only scored when an explicit investment basis exists.
            if metrics.roi is not None:
                if metrics.roi > 25:
                    scores.append(100)
                elif metrics.roi > 15:
                    scores.append(80)
                elif metrics.roi > 5:
                    scores.append(60)
                else:
                    scores.append(30)
            
            # Score de eficiencia
            scores.append(min(100, metrics.efficiency_score))
            
            return sum(scores) / len(scores)
            
        except Exception:
            return 0

    @classmethod
    def _generate_enhanced_alerts(cls, metrics: BusinessMetrics, changes: Dict, kpis: Dict) -> List[Dict[str, str]]:
        """Genera alertas mejoradas e inteligentes"""
        alerts = []
        
        try:
            # Alertas críticas
            if metrics.profit_margin < 5:
                alerts.append({
                    'type': 'danger',
                    'title': 'Margen de Beneficio Crítico',
                    'message': f'Margen del {metrics.profit_margin:.1f}% requiere atención inmediata.',
                    'icon': 'ri-error-warning-line',
                    'priority': 'high'
                })
            
            # Alertas de ROI
            if metrics.roi is not None and metrics.roi < 0:
                alerts.append({
                    'type': 'danger',
                    'title': 'ROI Negativo',
                    'message': f'ROI del {metrics.roi:.1f}% indica pérdidas en inversión.',
                    'icon': 'ri-arrow-down-circle-line',
                    'priority': 'high'
                })
            
            # Alertas de cambios significativos
            revenue_change = changes.get('revenue_change', 0)
            if abs(revenue_change) > 20:
                alert_type = 'success' if revenue_change > 0 else 'warning'
                direction = 'aumentado' if revenue_change > 0 else 'disminuido'
                alerts.append({
                    'type': alert_type,
                    'title': f'Cambio Significativo en Ingresos',
                    'message': f'Los ingresos han {direction} {abs(revenue_change):.1f}% este mes.',
                    'icon': 'ri-line-chart-line',
                    'priority': 'medium'
                })
            
            # Alertas positivas
            if metrics.efficiency_score > 80:
                alerts.append({
                    'type': 'success',
                    'title': 'Excelente Eficiencia',
                    'message': f'Score de eficiencia del {metrics.efficiency_score:.1f}% es sobresaliente.',
                    'icon': 'ri-thumb-up-line',
                    'priority': 'info'
                })
            
        except Exception as e:
            logger.error(f"Error generating enhanced alerts: {e}")
        
        return alerts

    @classmethod
    def _get_enhanced_top_products(cls, business_id: int) -> List[Dict[str, Any]]:
        """Obtiene top productos mejorado"""
        try:
            from collections import defaultdict

            # NOTA: el lookup original ('fk_product_questionary__results__fk_simulation')
            # no correspondía a ninguna relación real (Questionary -> QuestionaryResult
            # es 'fk_questionary_questionary_result'; QuestionaryResult -> Simulation es
            # 'simulations') y Django lanzaba FieldError en cada llamada, atrapado por
            # el except de abajo -- por eso "top productos" devolvía [] siempre.
            products = list(Product.objects.filter(
                fk_business=business_id, is_active=True
            ).annotate(
                simulations_count=Count(
                    'fk_product_questionary__fk_questionary_questionary_result__simulations',
                    distinct=True),
                latest_simulation=Max(
                    'fk_product_questionary__fk_questionary_questionary_result__simulations__date_created')
            ).order_by('-simulations_count', '-latest_simulation')[:5])

            if not products:
                return []

            product_ids = [p.id for p in products]

            # Fetch all recent simulations for these products in a single query
            all_simulations = list(Simulation.objects.filter(
                fk_questionary_result__fk_questionary__fk_product__in=product_ids
            ).select_related(
                'fk_questionary_result__fk_questionary'
            ).prefetch_related('results').order_by('-date_created'))

            # Group simulations by product, keeping only the latest 10 per product
            sims_by_product: Dict[int, List] = defaultdict(list)
            for sim in all_simulations:
                pid = sim.fk_questionary_result.fk_questionary.fk_product_id
                if len(sims_by_product[pid]) < 10:
                    sims_by_product[pid].append(sim)

            enhanced_products = []
            for product in products:
                product_metrics = cls._calculate_enhanced_metrics(sims_by_product[product.id])
                enhanced_products.append({
                    'id': product.id,
                    'name': product.name,
                    'simulations_count': product.simulations_count or 0,
                    'latest_simulation': product.latest_simulation,
                    'revenue': product_metrics.revenue,
                    'profit_margin': product_metrics.profit_margin,
                    'performance_score': cls._calculate_product_performance_score(product_metrics),
                    'description': getattr(product, 'description', ''),
                })

            return enhanced_products

        except Exception as e:
            logger.error(f"Error getting enhanced top products: {e}")
            return []

    @classmethod
    def _calculate_product_performance_score(cls, metrics: BusinessMetrics) -> float:
        """Calcula score de rendimiento del producto"""
        try:
            factors = []
            
            # Factor de ingresos (normalizado)
            if metrics.revenue > 0:
                revenue_factor = min(100, metrics.revenue / 1000)  # Ajustar según escala
                factors.append(revenue_factor)
            
            # Factor de margen
            if metrics.profit_margin > 0:
                margin_factor = min(100, metrics.profit_margin * 2)
                factors.append(margin_factor)
            
            # Factor de eficiencia
            factors.append(metrics.efficiency_score)
            
            return sum(factors) / len(factors) if factors else 0
            
        except Exception:
            return 0

    @classmethod
    def _generate_business_summary(cls, metrics: BusinessMetrics, kpis: Dict) -> Dict[str, str]:
        """Genera resumen del negocio"""
        try:
            financial_health = kpis.get('financial_health', 0)
            
            if financial_health > 80:
                status = 'excellent'
                message = 'El negocio muestra un rendimiento excepcional en todos los indicadores.'
            elif financial_health > 65:
                status = 'good'
                message = 'El negocio tiene un buen rendimiento con oportunidades de optimización.'
            elif financial_health > 45:
                status = 'fair'
                message = 'El negocio muestra un rendimiento moderado con áreas que requieren atención.'
            else:
                status = 'poor'
                message = 'El negocio necesita mejoras significativas en múltiples áreas.'
            
            return {
                'status': status,
                'message': message,
                'health_score': round(financial_health, 1),
                'key_metric': f'Salud Financiera: {financial_health:.1f}/100'
            }
            
        except Exception as e:
            logger.error(f"Error generating business summary: {e}")
            return {
                'status': 'unknown',
                'message': 'No hay suficientes datos para generar un resumen.',
                'health_score': 0,
                'key_metric': 'Datos insuficientes'
            }

    @classmethod
    def _get_empty_dashboard_data(cls) -> Dict[str, Any]:
        """Retorna estructura vacía de datos del dashboard"""
        return {
            'business': None,
            'products': [],
            'simulations': [],
            'charts': [],
            'financial_metrics': asdict(BusinessMetrics()),
            'business_stats': {
                'products_count': 0,
                'active_products_count': 0,
                'areas_count': 0,
                'simulations_count': 0,
                'recent_simulations_count': 0,
                'charts_count': 0,
            },
            'percentage_changes': {
                'revenue_change': 0,
                'costs_change': 0,
                'profit_change': 0,
                'profit_margin_change': 0,
                'inventory_change': 0,
                'demand_change': 0,
                'production_change': 0,
            },
            'performance_trends': {
                'monthly_trends': [],
                'growth_rate': 0,
                'has_data': False
            },
            'recommendations': [],
            'recent_activity': [],
            'business_kpis': {
                'profit_margin_percentage': 0,
                'roi_percentage': None,
                'efficiency_score': 0,
                'net_profit': 0,
                'cost_ratio': 0,
                'revenue_per_product': 0,
                'demand_fulfillment': 0,
                'operational_efficiency': 0,
                'financial_health': 0
            },
            'business_alerts': [],
            'top_products': [],
            'summary': {
                'status': 'no_data',
                'message': 'No hay datos disponibles.',
                'health_score': 0,
                'key_metric': 'Sin información'
            },
            'last_updated': timezone.now().isoformat()
        }

    # === FUNCIONES PARA LAS URLs EXISTENTES ===

    @classmethod
    def get_admin_statistics(cls) -> Dict[str, Any]:
        """Obtiene estadísticas para dashboard admin - MEJORADO"""
        try:
            today = timezone.now()
            last_month = today - relativedelta(months=1)
            
            # Estadísticas de usuarios mejoradas
            user_stats = User.objects.aggregate(
                total_users=Count('id'),
                active_users=Count('id', filter=Q(last_login__gte=today - timedelta(days=30))),
                new_users_last_month=Count(
                    'id',
                    filter=Q(
                        date_joined__month=last_month.month,
                        date_joined__year=last_month.year
                    )
                )
            )
            
            # Estadísticas de negocios
            business_stats = Business.objects.aggregate(
                total_businesses=Count('id'),
                active_businesses=Count('id', filter=Q(is_active=True)),
                new_businesses_last_month=Count(
                    'id',
                    filter=Q(
                        date_created__month=last_month.month,
                        date_created__year=last_month.year
                    )
                )
            )
            
            # Estadísticas de simulaciones
            simulation_stats = Simulation.objects.aggregate(
                total_simulations=Count('id'),
                last_month_simulations=Count(
                    'id',
                    filter=Q(
                        date_created__month=last_month.month,
                        date_created__year=last_month.year
                    )
                )
            )
            
            # Calcular cambios porcentuales
            users_count = user_stats['total_users']
            users_last_month = user_stats['new_users_last_month']
            users_change = users_count - users_last_month
            users_change_percentage = (
                (users_change / users_last_month * 100) 
                if users_last_month > 0 else 0
            )
            
            return {
                'users_count': users_count,
                'active_users': user_stats['active_users'],
                'new_users_last_month': users_last_month,
                'users_change': users_change,
                'users_change_percentage': round(users_change_percentage, 2),
                'total_businesses': business_stats['total_businesses'],
                'active_businesses': business_stats['active_businesses'],
                'new_businesses_last_month': business_stats['new_businesses_last_month'],
                'total_simulations': simulation_stats['total_simulations'],
                'last_month_simulations': simulation_stats['last_month_simulations'],
                'system_health': cls._calculate_system_health(user_stats, business_stats, simulation_stats)
            }
            
        except Exception as e:
            logger.error(f"Error getting admin statistics: {e}")
            return {
                'users_count': 0,
                'active_users': 0,
                'new_users_last_month': 0,
                'users_change': 0,
                'users_change_percentage': 0,
                'total_businesses': 0,
                'active_businesses': 0,
                'new_businesses_last_month': 0,
                'total_simulations': 0,
                'last_month_simulations': 0,
                'system_health': 'unknown'
            }

    @classmethod
    def _calculate_system_health(cls, user_stats: Dict, business_stats: Dict, simulation_stats: Dict) -> str:
        """Calcula la salud general del sistema"""
        try:
            health_indicators = []
            
            # Indicador de actividad de usuarios
            total_users = user_stats.get('total_users', 0)
            active_users = user_stats.get('active_users', 0)
            if total_users > 0:
                user_activity_rate = (active_users / total_users) * 100
                health_indicators.append(user_activity_rate)
            
            # Indicador de negocios activos
            total_businesses = business_stats.get('total_businesses', 0)
            active_businesses = business_stats.get('active_businesses', 0)
            if total_businesses > 0:
                business_activity_rate = (active_businesses / total_businesses) * 100
                health_indicators.append(business_activity_rate)
            
            # Indicador de actividad de simulaciones
            total_simulations = simulation_stats.get('total_simulations', 0)
            recent_simulations = simulation_stats.get('last_month_simulations', 0)
            if total_simulations > 0 and recent_simulations > 0:
                simulation_activity = min(100, (recent_simulations / max(total_simulations * 0.1, 1)) * 100)
                health_indicators.append(simulation_activity)
            
            if health_indicators:
                avg_health = sum(health_indicators) / len(health_indicators)
                if avg_health > 75:
                    return 'excellent'
                elif avg_health > 50:
                    return 'good'
                elif avg_health > 25:
                    return 'fair'
                else:
                    return 'poor'
            
            return 'unknown'
            
        except Exception:
            return 'unknown'

    @classmethod
    def update_business_metrics_enhanced(cls, business_id: int, user) -> Dict[str, Any]:
        """Actualiza métricas del negocio - MEJORADO"""
        try:
            # Validar permisos
            business = cls._get_validated_business(business_id, user)
            if not business:
                return {'success': False, 'error': 'Business not found or access denied'}
            
            # Limpiar caché para forzar recálculo
            cache_key = f"dashboard_complete_{business_id}_{user.id}"
            cache.delete(cache_key)
            
            # Recalcular métricas
            dashboard_data = cls.get_complete_dashboard_data(business_id, user)
            
            # Registrar la actualización
            try:
                ActivityLog.objects.create(
                    user=user,
                    action="Dashboard metrics updated",
                    details=f"Métricas actualizadas para {business.name}",
                    timestamp=timezone.now()
                )
            except Exception:
                pass  # No fallar si no se puede registrar la actividad
            
            return {
                'success': True,
                'message': 'Métricas actualizadas correctamente',
                'updated_at': timezone.now().isoformat(),
                'metrics': dashboard_data['financial_metrics'],
                'kpis': dashboard_data['business_kpis'],
                'summary': dashboard_data['summary']
            }
            
        except Exception as e:
            logger.error(f"Error updating enhanced business metrics: {e}")
            return {'success': False, 'error': str(e)}

    @classmethod
    def get_dashboard_api_data_enhanced(cls, business_id: int, user) -> Dict[str, Any]:
        """Obtiene datos para API del dashboard - MEJORADO"""
        try:
            # Validar permisos
            business = cls._get_validated_business(business_id, user)
            if not business:
                return {'success': False, 'error': 'Business not found or access denied'}
            
            # Obtener datos completos
            dashboard_data = cls.get_complete_dashboard_data(business_id, user)
            
            # Preparar respuesta optimizada para API
            api_response = {
                'success': True,
                'business': {
                    'id': business.id,
                    'name': business.name,
                    'type': business.get_type_display() if hasattr(business, 'get_type_display') else 'Otros',
                    'location': getattr(business, 'location', 'No especificada'),
                },
                'metrics': dashboard_data['financial_metrics'],
                'kpis': dashboard_data['business_kpis'],
                'stats': dashboard_data['business_stats'],
                'trends': {
                    'growth_rate': dashboard_data['performance_trends']['growth_rate'],
                    'has_data': dashboard_data['performance_trends']['has_data'],
                    'monthly_count': len(dashboard_data['performance_trends']['monthly_trends'])
                },
                'alerts': {
                    'total_count': len(dashboard_data['business_alerts']),
                    'critical_count': len([a for a in dashboard_data['business_alerts'] if a.get('priority') == 'high']),
                    'recent_alerts': dashboard_data['business_alerts'][:5]  # Solo las 5 más recientes
                },
                'summary': dashboard_data['summary'],
                'performance_indicators': {
                    'health_score': dashboard_data['summary']['health_score'],
                    'efficiency_score': dashboard_data['business_kpis']['efficiency_score'],
                    'financial_health': dashboard_data['business_kpis']['financial_health']
                },
                'last_updated': dashboard_data['last_updated'],
                'timestamp': timezone.now().isoformat()
            }
            
            return api_response
            
        except Exception as e:
            logger.error(f"Error getting enhanced dashboard API data: {e}")
            return {'success': False, 'error': str(e)}

    # === FUNCIONES DE UTILIDAD ===

    @classmethod
    def get_business_greeting(cls, user) -> str:
        """Obtiene saludo personalizado"""
        current_hour = datetime.now().hour
        user_name = user.first_name or user.username
        
        if 5 <= current_hour < 12:
            return f"Buenos días, {user_name}"
        elif 12 <= current_hour < 18:
            return f"Buenas tardes, {user_name}"
        else:
            return f"Buenas noches, {user_name}"

    @classmethod
    def clear_dashboard_cache(cls, business_id: int = None, user_id: int = None):
        """Limpia la caché del dashboard"""
        try:
            if business_id and user_id:
                # Limpiar caché específico
                cache_key = f"dashboard_complete_{business_id}_{user_id}"
                cache.delete(cache_key)
                cache.delete(f"user_business_{user_id}")
            else:
                # Limpiar toda la caché relacionada con dashboards
                cache.clear()
            
            logger.info(f"Dashboard cache cleared for business_id={business_id}, user_id={user_id}")
            
        except Exception as e:
            logger.error(f"Error clearing dashboard cache: {e}")

    @classmethod
    def get_dashboard_health_status(cls, business_id: int, user) -> Dict[str, Any]:
        """Obtiene estado de salud del dashboard"""
        try:
            dashboard_data = cls.get_complete_dashboard_data(business_id, user)
            
            health_status = {
                'status': 'healthy',
                'business_found': dashboard_data['business'] is not None,
                'data_completeness': cls._calculate_data_completeness(dashboard_data),
                'last_simulation': cls._get_last_simulation_date(dashboard_data['simulations']),
                'metrics_calculated': len(dashboard_data['financial_metrics']) > 0,
                'recommendations_available': len(dashboard_data['recommendations']) > 0,
                'trends_available': dashboard_data['performance_trends']['has_data'],
                'system_performance': {
                    'cache_hit': cache.get(f"dashboard_complete_{business_id}_{user.id}") is not None,
                    'response_time': 'fast',  # Se podría medir realmente
                    'data_freshness': dashboard_data['last_updated']
                }
            }
            
            # Determinar estado general
            issues = []
            if not health_status['business_found']:
                issues.append('business_not_found')
            if health_status['data_completeness'] < 50:
                issues.append('insufficient_data')
            if not health_status['metrics_calculated']:
                issues.append('metrics_calculation_failed')
            
            if issues:
                health_status['status'] = 'degraded'
                health_status['issues'] = issues
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error getting dashboard health status: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }

    @classmethod
    def _calculate_data_completeness(cls, dashboard_data: Dict) -> float:
        """Calcula completitud de los datos"""
        try:
            total_checks = 7
            completed_checks = 0
            
            if dashboard_data['business']:
                completed_checks += 1
            if len(dashboard_data['products']) > 0:
                completed_checks += 1
            if len(dashboard_data['simulations']) > 0:
                completed_checks += 1
            if dashboard_data['financial_metrics']['revenue'] > 0:
                completed_checks += 1
            if len(dashboard_data['recommendations']) > 0:
                completed_checks += 1
            if dashboard_data['performance_trends']['has_data']:
                completed_checks += 1
            if len(dashboard_data['business_alerts']) > 0:
                completed_checks += 1
            
            return (completed_checks / total_checks) * 100
            
        except Exception:
            return 0

    @classmethod
    def _get_last_simulation_date(cls, simulations: List) -> Optional[str]:
        """Obtiene fecha de la última simulación"""
        try:
            if simulations:
                return simulations[0].date_created.isoformat()
            return None
        except Exception:
            return None
