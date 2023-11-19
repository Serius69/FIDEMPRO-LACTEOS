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
def equation_analysis_view(request):
    try:
        equation_str = "x + y = 10"
        equation = Eq(sympify(equation_str), 10)
        variables = list(equation.free_symbols)
        variable_data = []
        for variable in variables:
            # Replace 'query_database_for_variable_values' and 'evaluate_expression' with your actual logic
            dependencies = []  # You need to define the dependencies
            values = query_database_for_variable_values(dependencies)
            variable_value = evaluate_expression(equation, values)
            variable_data.append({"name": variable, "value": variable_value})
        context = {
            "equation_str": equation_str,
            "variable_data": variable_data,
        }

    except Exception as e:
        context = {
            'error_message': str(e),
        }

    return render(
        request,
        "equation_analysis.html",  # Replace with the actual template name
        context,
    )
def create_simulation_equations(request):
    try:
        variables = Variable.objects.all()
        equations = []
        for variable in variables:
            equation = generate_equation_from_variable(variable)
            equations.append(equation)
        context = {
            "equations": equations,
        }
    except Exception as e:
        context = {
            'error_message': str(e),
        }
    return render(
        request,
        "simulation/equations.html", 
        context,
    )
def generate_equation_from_variable(variable):
    try:
        prompt = f"Generate an equation for the variable {variable.name} with type {variable.get_type_display()} and parameters {variable.parameters}."
        response = openai.Completion.create(
            engine="text-davinci-002",  # Choose the appropriate engine
            prompt=prompt,
            max_tokens=50,  # Adjust the max tokens as needed
            n=1,  # Number of equations to generate
            stop=None,  # Stop generating equations at a specific token (e.g., "?")
        )
        equation = response.choices[0].text.strip()
        return equation
    except Exception as e:
        return str(e)

def questionnaire_info(request, questionnaire_id):
    questionnaire = get_object_or_404(QuestionaryResult, id=questionnaire_id)
    questionnaire_name = questionnaire.name
    questionnaire_description = questionnaire.description
    questions = questionnaire.question_set.all()
    
    context = {
        'questionnaire': questionnaire,
        'questionnaire_name': questionnaire_name,
        'questionnaire_description': questionnaire_description,
        'questions': questions,
        
    }
    return render(request, 'questionnaire_info_template.html', context)
def simulate_init(request):
    try:
        businesses = Business.objects.all().order_by('-id')
        products = Product.objects.all().order_by('-id')
        context = {'product': products, 'business': businesses}
        if request.method == "POST":
            form = SimulationForm (request.POST or None,request.FILES or None)
            if form.is_valid():
                form.save()
                messages.success(request,"Company inserted successfully!")
                return redirect("product:product.overview")
            else:
                messages.error(request,"Something went wrong!")
                return redirect("product:product.overview")
    except Business.DoesNotExist:
        context = {
            'error_message': 'Error with the simulation.',
        }
    return render(request, 'simulate/simulate-init.html', context)
def simulate_show_form(request):
    try:
        businesses = Business.objects.all().order_by('-id')
        products = Product.objects.all().order_by('-id')
        questionaries = QuestionaryResult.objects.all().order_by('-id')
        chart_data = [...]
        table_data = [...] 
        response_data = {
            'chartData': chart_data,
            'tableData': table_data,
        }
        context = {
            'products': products, 
            'businesses': businesses,
            'questionaries': questionaries,
            'response_data': response_data,
            }
    except Business.DoesNotExist:
        context = {
            'error_message': 'No business found.',
        }

    return render(request, 'simulate/simulate-init.html', context)