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
    update_business_metrics,
    dashboard_api,
)

app_name = 'dashboard'

urlpatterns = [
    # Vistas principales
    path('', index, name='index'),
    path('admin/', dashboard_admin, name='dashboard.admin'),
    path('user/', dashboard_user, name='dashboard.user'),
    path('api/update-metrics/', update_business_metrics, name='update_metrics'),
    path('api/dashboard-data/', dashboard_api, name='dashboard_api'),

]

