from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.
class DashboardView(LoginRequiredMixin,TemplateView):
    pass
    
dashboard_view = DashboardView.as_view(template_name="dashboards/index.html")
dashboard_admin = DashboardView.as_view(template_name="dashboards/dashboard-admin.html")
dashboard_finance_status = DashboardView.as_view(template_name="dashboards/dashboard-financestatus.html")
dashboard_products= DashboardView.as_view(template_name="dashboards/dashboard-products.html")
dashboard_variables = DashboardView.as_view(template_name="dashboards/dashboard-variables.html")



