from django.shortcuts import render
from django.contrib import messages
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings

import pkg_resources  # Import pkg_resources

from scipy import stats  # Import scipy for KS test

from .models import DataPoint, FDP, SimulationScenario
from .forms import YourForm  # Replace with your actual form import
from variable.models import Variable
from product.models import Product
from business.models import Business, BusinessProduct

from sympy import Eq, sympify

import openai
# Create your variable views here.
# 
openai.api_key = settings.OPENAI_API_KEY
class AppsView(LoginRequiredMixin, TemplateView):
    # Add methods or attributes specific to this view if needed
    template_name = 'your_template.html'  # Replace with your template name

def ks_test_view(request):
    # Retrieve the dataset and FDP parameters
    data_points = DataPoint.objects.values_list('value', flat=True)
    fdp = FDP.objects.get(pk=1)  # You need to specify the FDP you want to test against

    # Calculate the KS statistic and p-value
    ks_statistic, p_value = stats.kstest(data_points, 'expon', args=(0, 1/fdp.lambda_param))

    # Interpret the results (you can customize this part)
    if p_value < 0.05:
        result = "Reject null hypothesis: Data does not fit the FDP."
    else:
        result = "Fail to reject null hypothesis: Data fits the FDP."

    context = {
        'ks_statistic': ks_statistic,
        'p_value': p_value,
        'result': result,
    }

    return (context)

def simulate_init(request):
    businesses = SimulationScenario.objects.all().order_by('-id')
    business = businesses.first()  # Retrieve the first object if it exists

    if ks_test_view == 1:
        result = "Reject null hypothesis: Data does not fit the FDP."

    context = {'simulate': business}
    return render(request, 'simulate/simulate-init.html', context)

def equation_analysis_view(request):
    # Sample equation (you can replace this with your input)
    equation_str = "x + y = 10"
    equation = Eq(sympify(equation_str), 10)

    # Extract variable names
    variables = list(equation.free_symbols)

    # Create a dependency graph (you may need to implement this)
    dependency_graph = create_dependency_graph(equation)

    # Resolve dependencies and query the database
    variable_data = []
    for variable in variables:
        dependencies = dependency_graph.get_dependencies(variable)
        values = query_database_for_variable_values(dependencies)
        variable_value = evaluate_expression(equation, values)
        variable_data.append({"name": variable, "value": variable_value})

    # Render a template with the variable data
    return render(
        request,
        "equation_analysis.html",  # Replace with the actual template name
        {"equation_str": equation_str, "variable_data": variable_data},
    )

#  Create equations
def create_simulation_equations(request):
    # Retrieve all Variable objects from the database
    variables = Variable.objects.all()

    # Initialize an empty list to store equations
    equations = []

    # Loop through each variable and create equations
    for variable in variables:
        # You can define your equation creation logic here
        # For example, create equations based on variable properties like type, name, parameters, etc.
        equation = generate_equation_from_variable(variable)

        # Append the equation to the list
        equations.append(equation)

    # Render a template with the list of equations
    return render(
        request,
        "simulation/equations.html",  # Replace with your actual template file
        {"equations": equations},
    )

def generate_equation_from_variable(variable):
    # Define a prompt for OpenAI to generate an equation
    prompt = f"Generate an equation for the variable {variable.name} with type {variable.get_type_display()} and parameters {variable.parameters}."

    # Generate the equation using GPT-3 from OpenAI
    response = openai.Completion.create(
        engine="text-davinci-002",  # Choose the appropriate engine
        prompt=prompt,
        max_tokens=50,  # Adjust the max tokens as needed
        n=1,  # Number of equations to generate
        stop=None,  # Stop generating equations at a specific token (e.g., "?")
    )

    # Extract and return the generated equation
    equation = response.choices[0].text.strip()
    return equation

