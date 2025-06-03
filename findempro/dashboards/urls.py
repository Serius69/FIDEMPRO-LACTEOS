from datetime import timezone
from pyexpat.errors import messages
from venv import logger
from django.urls import path
from django.views.decorators.cache import cache_page
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from dashboards.views import (
    DashboardService,
    index,
    dashboard_admin,
    dashboard_user,
    get_chart_data,
    update_business_metrics,
    # # Nuevas vistas agregadas
    export_recommendations,
    dashboard_api,
    chart_builder,
    analytics_report,
)

app_name = 'dashboard'

urlpatterns = [
    # Vistas principales
    path('', index, name='index'),
    path('admin/', dashboard_admin, name='dashboard.admin'),
    path('user/', dashboard_user, name='dashboard.user'),
    
    # API endpoints
    path('api/chart/<int:chart_id>/', get_chart_data, name='get_chart_data'),
    path('api/update-metrics/', update_business_metrics, name='update_metrics'),
    path('api/dashboard-data/', dashboard_api, name='dashboard_api'),
    
    # # Exportación y reportes
    path('export/recommendations/', export_recommendations, name='export_recommendations'),
    path('analytics/report/', analytics_report, name='analytics_report'),
    
    # # Chart builder
    path('charts/builder/', chart_builder, name='chart_builder'),
    
    # URLs con caché para mejorar rendimiento
    path('cached/user/', 
         cache_page(60 * 5)(dashboard_user), 
         name='dashboard.user.cached'),
]

