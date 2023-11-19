from typing import Dict, Any
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from datetime import datetime
from product.models import Product,Area
from business.models import Business

# Create your views here.
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
        
    businesses = Business.objects.all()
    today = timezone.now()
    last_month = today - relativedelta(months=1)
    users = User.objects.all()
    users_last_month = User.objects.filter(date_joined__month=last_month.month, date_joined__year=last_month.year)
    users_count = users.count()
    users_last_month_count = users_last_month.count()
    users_change = users_count - users_last_month_count
    users_change_percentage = (users_change / users_last_month_count * 100) if users_last_month_count > 0 else 0
    current_time = datetime.now().time()
    if current_time >= datetime(1900, 1, 1, 5, 0).time() and current_time < datetime(1900, 1, 1, 12, 0).time():
        greeting = "Good Morning"
    elif current_time >= datetime(1900, 1, 1, 12, 0).time() and current_time < datetime(1900, 1, 1, 18, 0).time():
        greeting = "Good Afternoon"
    else:
        greeting = "Good Evening"
    products = Product.objects.filter(fk_business=business.id)
    areas = Area.objects.filter(fk_product__fk_business=business.id)
    products_ready = 0
    products_no_ready = 0
    for product in products:
        if product.is_ready == True:
            products_ready += 1
        else:
            products_no_ready += 1
    total_revenue = sum(product.earnings or 0 for product in products)
    total_costs = sum(product.costs or 0 for product in products)
    total_inventory_levels = sum(product.inventory_levels or 0 for product in products)
    total_production_output = sum(product.production_output or 0 for product in products)
    total_profit_margin = sum(product.profit_margin or 0 for product in products)

    context: Dict[str, Any] = {
        'users': users,
        'users_last_month': users_last_month,
        'users_count': users_count,
        'users_last_month_count': users_last_month_count,
        'users_change': users_change,
        'users_change_percentage': users_change_percentage,
        'greeting': greeting,
        'products': products,
        'areas': areas,
        'business': business,
        'businesses': businesses,
        'total_revenue': total_revenue,
        'total_costs': total_costs,
        'total_inventory_levels': total_inventory_levels,
        'total_production_output': total_production_output,
        'total_profit_margin': total_profit_margin,
        'products_ready': products_ready,
        'products_no_ready': products_no_ready,
        'total_products': products_ready+products_no_ready,
    }

    return render(request, 'dashboards/dashboard-user.html', context)






