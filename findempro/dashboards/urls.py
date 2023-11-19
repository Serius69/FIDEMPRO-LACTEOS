from django.urls import path
from dashboards.views import (
    index,
    dashboard_admin,
    dashboard_user,
)
app_name = 'dashboard'
urlpatterns = [
    path('',view =index,name="index"),
    path('admin',view =dashboard_admin,name="dashboard.admin"),
    path('user', view =dashboard_user,name="dashboard.user"),
]


