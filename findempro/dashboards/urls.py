from django.urls import path
from dashboards.views import (
    dashboard_view,
    dashboard_admin,
    dashboard_user,
)

app_name = 'dashboards'

urlpatterns = [
    path('',view =dashboard_view,name="index"),
    path('admin',view =dashboard_admin,name="dashboard.admin"),
    path('tdd', view =dashboard_user,name="dashboard.tdd"),
]


