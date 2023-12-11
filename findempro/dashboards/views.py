from typing import Dict, Any
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from datetime import datetime
from variable.models import Variable
from user.models import ActivityLog
from product.models import Product,Area
from finance.models import FinanceRecommendationSimulation
from business.models import Business
from dashboards.models import Chart
from simulate.models import ResultSimulation,Simulation,Demand,DemandBehavior
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from pages.forms import RegisterElementsForm
from django.core.exceptions import MultipleObjectsReturned
from django.contrib import messages
from django.http import Http404
class DashboardView(LoginRequiredMixin,TemplateView):
    pass
    
def index(request):
    form = RegisterElementsForm(request.POST)
    return render(request, 'dashboards/index.html',{'form': form})
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
    business_id_instance = request.session.get('business_id')
    if business_id_instance:
        try:
            business_id_selected = str(business_id_instance)  # Convertir a cadena
            business_id = int(business_id_selected)
            business = get_object_or_404(Business, pk=business_id)
        except ValueError:
            messages.error(request, 'El valor de business_id no es un número válido.')
            return redirect("business:business.list")
    else:
        messages.error(request, 'El parámetro business_id no está presente en la solicitud.')
        return redirect("business:business.list")
    print(business_id_instance)
    try:
        if request.method == 'GET':
            business_id_selected = request.GET.get('business_id', business_id_instance)
            print(business_id_selected)
            # if not business_id_selected.isdigit():
            #     raise Http404("El parámetro business_id no es un número válido.")
            
            business = get_object_or_404(Business, pk=business_id_selected, is_active=True)
        else:
            business = Business.objects.filter(fk_user=request.user, is_active=True).first()

        if not business:
            messages.error(request, 'No se encontró un negocio asociado a tu usuario.')
            return redirect("business:business.list")

        recommendations = FinanceRecommendationSimulation.objects.filter(
            fk_finance_recommendation__fk_business=business.id, is_active=True
        )   
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
        print(product_ids)    

        charts = Chart.objects.filter(fk_product_id__in=product_ids, is_active=True ).order_by('-id')[:6]

        paginator = Paginator(recommendations, 10)  # Show 10 recommendations per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # buscar toda la ultima simulacion de cada producto
        simulations = Simulation.objects.filter(fk_questionary_result__fk_questionary__fk_product_id__in=product_ids).order_by('-id')
        print(simulations)
        all_variables_extracted = []
        for simulation in simulations:
            simulation_id = simulation.id
            print(simulation_id)
            results_simulation = ResultSimulation.objects.filter(is_active=True, fk_simulation_id=simulation_id)
            print(results_simulation)
            iniciales_a_buscar = ['TPV', 'IT', 'GT', 'TG','DT']
            
            for result_simulation in results_simulation:
                variables_extracted = result_simulation.get_variables()

                # Filtrar variables que coinciden con las iniciales
                variables_filtrates = Variable.objects.filter(initials__in=iniciales_a_buscar).values('name', 'initials')
                initials_a_nombres = {variable['initials']: variable['name'] for variable in variables_filtrates}
                # en lugar de mostrar las iniciales compararlas con la base de datos de varaibles y mostrar el nombre de la variable
                # Calcular la suma total por variable
                totals_por_variable = {}
                for initial, value in variables_extracted.items():
                    if initial in initials_a_nombres:
                        nombre_variable = initials_a_nombres[initial]
                        if nombre_variable not in totals_por_variable:
                            totals_por_variable[nombre_variable] = 0
                        totals_por_variable[nombre_variable] += value

                # Agregar las variables filtradas a la lista
                all_variables_extracted.append({'result_simulation': result_simulation, 'totales_por_variable': totals_por_variable})

        total_revenue=0
        total_costs=0
        total_inventory_levels=0
        total_demand=0
        total_production_output=0
        total_profit_margin=0
        print(all_variables_extracted)
        for variables_extracted in all_variables_extracted:
            totals_por_variable = variables_extracted['totales_por_variable']
            total_revenue += totals_por_variable.get('Total Revenue', 0)
            total_costs += totals_por_variable.get('Total Costs', 0)
            total_inventory_levels += totals_por_variable.get('Total Inventory Levels', 0)
            total_demand += totals_por_variable.get('Total Demand', 0)
            total_production_output += totals_por_variable.get('Total Production Output', 0)
            total_profit_margin += totals_por_variable.get('Total Profit Margin', 0)
            
        recent_activity = ActivityLog.objects.filter(user=request.user).order_by('-timestamp')[:10] 

        context: Dict[str, Any] = {
            'greeting': greeting,
            'recent_activity': recent_activity,
            'areas': areas,
            'business': business,
            'businesses': businesses,
            'total_revenue': total_revenue,
            'total_costs': total_costs,
            'total_demand': total_demand, # 'total_demand': total_demand,
            'total_inventory_levels': total_inventory_levels,
            'total_production_output': total_production_output,
            'total_profit_margin': total_profit_margin,
            'charts': charts,
            
            'page_obj': page_obj
        }

        return render(request, 'dashboards/dashboard-user.html', context)
    except Business.DoesNotExist:
        messages.error(request, 'El negocio asociado a tu usuario no existe.')
        return redirect("business:business.list")
    except Business.MultipleObjectsReturned:
        messages.error(request, 'Error: Múltiples negocios asociados a tu usuario.')
        return redirect("business:business.list")






