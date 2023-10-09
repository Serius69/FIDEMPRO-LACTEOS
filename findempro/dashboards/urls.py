from django.urls import path
from dashboards.views import (
    dashboard_view,
    dashboard_admin,
    dashboard_finance_status,
    dashboard_products,
    dashboard_variables,
)

app_name = 'dashboards'

urlpatterns = [
    path('',view =dashboard_view,name="index"),
    path('dashboard-admin',view =dashboard_admin,name="dashboard_admin"),
    path('dashboard-finance', view =dashboard_finance_status,name="dashboard_finance_status"),
    path('dashboard-products', view =dashboard_products,name="dashboard_products"),
    path('dashboard-variables', view =dashboard_variables,name="dashboard_variables"),
]


