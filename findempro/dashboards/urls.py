from django.urls import path
from django.views.decorators.cache import cache_page
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from dashboards.services.dashboard_service import DashboardService
from dashboards.views import (
    index,
    dashboard_admin,
    dashboard_user,
    update_business_metrics,
    dashboard_api,
    dashboard_summary_api,
)

app_name = 'dashboard'

urlpatterns = [
    # Vistas principales
    path('', index, name='index'),
    # 'dashboard-admin/' en vez de 'admin/': montado en la raiz, 'admin/'
    # colisionaba con Django admin (declarado antes) y dejaba esta vista inaccesible.
    path('dashboard-admin/', dashboard_admin, name='dashboard.admin'),
    path('user/', dashboard_user, name='dashboard.user'),
    path('api/update-metrics/', update_business_metrics, name='update_metrics'),
    path('api/dashboard-data/', dashboard_api, name='dashboard_api'),
    path('api/summary/', dashboard_summary_api, name='summary_api'),

]

