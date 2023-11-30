from typing import Dict, Any
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from datetime import datetime
from product.models import Product,Area
from finance.models import FinanceRecommendation
from business.models import Business
from dashboards.models import Chart,Demand,DemandBehavior
from simulate.models import ResultSimulation,Simulation
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
class DashboardView(LoginRequiredMixin,TemplateView):
    pass
    
def index(request):
    return render(request, 'dashboards/index.html')
def dashboard_admin(request):
    today = timezone.now()
    last_month = today - relativedelta(months=1)
    users = User.objects.all()
    users_last_month = User.objects.filter(date_joined__month=last_month.month, date_joined__year=last_month.year)
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
    try:
        business = get_object_or_404(Business, fk_user=request.user)
    except Business.DoesNotExist:
        return redirect("business:business_list")
    
    recommendations=FinanceRecommendation.objects.filter(fk_business=business.id)
        
    businesses = Business.objects.all().filter(fk_user=request.user, is_active=True).order_by('-id')
    today = timezone.now()
    last_month = today - relativedelta(months=1)
    
    current_time = datetime.now().time()
    if current_time >= datetime(1900, 1, 1, 5, 0).time() and current_time < datetime(1900, 1, 1, 12, 0).time():
        greeting = "Buenos Dias"
    elif current_time >= datetime(1900, 1, 1, 12, 0).time() and current_time < datetime(1900, 1, 1, 18, 0).time():
        greeting = "Buenas Tardes"
    else:
        greeting = "Buenas Noches"
    products = Product.objects.filter(fk_business=business.id)
    areas = Area.objects.filter(fk_product__fk_business=business.id)
    product_ids = [product.id for product in products]
        
    charts = Chart.objects.filter(fk_product_id__in=product_ids).order_by('-id')[:6]
    
    paginator = Paginator(recommendations, 10)  # Show 10 recommendations per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    total_revenue = sum(product.earnings or 0 for product in products)
    total_costs = sum(product.costs or 0 for product in products)
    total_inventory_levels = sum(product.inventory_levels or 0 for product in products)
    total_production_output = sum(product.production_output or 0 for product in products)
    total_profit_margin = sum(product.profit_margin or 0 for product in products)

    context: Dict[str, Any] = {
        'greeting': greeting,
        'areas': areas,
        'business': business,
        'businesses': businesses,
        'total_revenue': total_revenue,
        'total_costs': total_costs,
        'total_inventory_levels': total_inventory_levels,
        'total_production_output': total_production_output,
        'total_profit_margin': total_profit_margin,
        'charts': charts,
        
        'page_obj': page_obj
    }

    return render(request, 'dashboards/dashboard-user.html', context)






