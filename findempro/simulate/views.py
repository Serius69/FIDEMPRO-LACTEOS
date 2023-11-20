from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
import pkg_resources  # Import pkg_resources
from .forms import SimulationForm  # Replace with your actual form import
from scipy import stats  # Import scipy for KS test
from .models import DataPoint, FDP
from variable.models import Variable
from product.models import Product
from business.models import Business
from simulate.models import Simulation,SimulationScenario,ResultSimulation
from questionary.models import QuestionaryResult
from sympy import Eq, sympify
import openai
openai.api_key = settings.OPENAI_API_KEY
from django.http import JsonResponse
class AppsView(LoginRequiredMixin, TemplateView):
    pass
def extract_demand_historic():
    try:
        demand_historic_variable = Variable.objects.get(name="demand_historic")
        return demand_historic_variable.values_list('value', flat=True)
    except Variable.DoesNotExist:
        return []

def ks_test_view(request, variable_name):
    try: 
        demand_historic = extract_demand_historic()
        if not demand_historic:
            raise Variable.DoesNotExist('Variable not found.')
        variable = Variable.objects.get(name=variable_name)
        data_points = DataPoint.objects.values_list('value', flat=True)
        fdp = variable.fdp
        if isinstance(fdp, FDP):
            distribution_type = 'norm'
            distribution_args = (fdp.mean, fdp.std_deviation)
        elif isinstance(fdp, FDP):
            distribution_type = 'expon'
            distribution_args = (0, 1 / fdp.lambda_param)
        elif isinstance(fdp, FDP):
            distribution_type = 'lognorm'
            distribution_args = (fdp.mean, fdp.std_deviation)
        _, p_value = stats.kstest(data_points, distribution_type, args=distribution_args)
        if p_value < 0.05:
            result = "Reject null hypothesis: Data does not fit the FDP."
        else:
            result = "Fail to reject null hypothesis: Data fits the FDP."
        context = {
            'result': result,
        }
    except Variable.DoesNotExist:
        context = {
            'error_message': 'Variable not found.',
        }
    return JsonResponse(context)
def simulate_init(request):
    simulation_started = request.session.get('simulation_started', False)

    if not simulation_started:
        businesses = Business.objects.filter(fk_user=request.user).order_by('-id')
        selected_simulation_id = request.GET.get('simulation_id')

        products = Product.objects.filter(
            is_active=True,
            fk_business__fk_user=request.user,
            simulation_id=selected_simulation_id
        ).order_by('-id')

        questionnaires_result = QuestionaryResult.objects.filter(
            is_active=True,
            fk_business__fk_user=request.user,
            simulation_id=selected_simulation_id
        ).order_by('-id')

        if request.method == "POST":
            form = SimulationForm(request.POST, request.FILES)
            if form.is_valid():
                simulation_instance = form.save(commit=False)
                simulation_instance.save()
                request.session['simulation_started'] = True
                request.session['simulation_id'] = simulation_instance.id

                chart_data = [...]  # Replace with actual chart data
                table_data = [...]  # Replace with actual table data 
                response_data = {
                    'chartData': chart_data,
                    'tableData': table_data,
                }
                context = {
                    'products': products,
                    'businesses': businesses,
                    'questionnaires_result': questionnaires_result,
                    'response_data': response_data,
                }
                return redirect('simulate:simulate.init')  # Redirect to the next step in the simulation
            else:
                messages.error(request, "Form validation failed. Please check your inputs.")
        else:
            form = SimulationForm()

        context = {
            'products': products,
            'businesses': businesses,
            'questionnaires_result': questionnaires_result,
            'form': form,
        }

        return render(request, 'simulate/simulate-init.html', context)
    else:
        simulation_id = request.session.get('simulation_id')
        simulation_instance = SimulationScenario.objects.get(pk=simulation_id)

        chart_data = [...]  # Replace with actual chart data
        table_data = [...]  # Replace with actual table data 
        response_data = {
            'chartData': chart_data,
            'tableData': table_data,
        }

        # Logic to fetch data for the current step of the simulation
        # ...

        context = {
            'products': products,
            'businesses': businesses,
            'questionnaires_result': questionnaires_result,
            'response_data': response_data,
            'simulation_instance': simulation_instance,
            'started': simulation_started,
        }

        return render(request, 'simulate/simulate-init.html', context)
