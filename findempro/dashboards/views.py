from typing import Dict, Any
from django.contrib.auth.models import User
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from dateutil.relativedelta import relativedelta

# Create your views here.
class DashboardView(LoginRequiredMixin,TemplateView):
    pass
    
dashboard_view = DashboardView.as_view(template_name="dashboards/index.html")

def dashboard_admin(request):
    # Obtén la fecha de hoy
    today = timezone.now()
    
    # Calcula la fecha del mes anterior
    last_month = today - relativedelta(months=1)
    
    # Obtén la cantidad de usuarios del mes actual y del mes anterior
    users = User.objects.all()
    users_last_month = User.objects.filter(date_joined__month=last_month.month, date_joined__year=last_month.year)
    
    # Calcula la diferencia y el porcentaje de cambio
    users_count = users.count()
    users_last_month_count = users_last_month.count()
    users_change = users_count - users_last_month_count
    users_change_percentage = (users_change / users_last_month_count * 100) if users_last_month_count > 0 else 0
    
    context = {
        'users': users,
        'users_last_month': users_last_month,
        'users_count': users_count,
        'users_last_month_count': users_last_month_count,
        'users_change': users_change,
        'users_change_percentage': users_change_percentage,
    }
    
    return render(request, 'dashboards/dashboard-admin.html', context)


def dashboard_user(request) -> str:
    """
    Renders a dashboard template for a user, displaying user-related information.

    Args:
        request (object): The HTTP request object.

    Returns:
        str: The rendered HTML template as the response.
    """
    today = timezone.now()
    last_month = today - relativedelta(months=1)

    users = User.objects.all()
    users_last_month = User.objects.filter(date_joined__month=last_month.month, date_joined__year=last_month.year)

    users_count = users.count()
    users_last_month_count = users_last_month.count()
    users_change = users_count - users_last_month_count
    users_change_percentage = (users_change / users_last_month_count * 100) if users_last_month_count > 0 else 0

    context: Dict[str, Any] = {
        'users': users,
        'users_last_month': users_last_month,
        'users_count': users_count,
        'users_last_month_count': users_last_month_count,
        'users_change': users_change,
        'users_change_percentage': users_change_percentage,
    }

    return render(request, 'dashboards/dashboard-tdd.html', context)




