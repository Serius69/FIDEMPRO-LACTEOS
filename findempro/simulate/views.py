from django.shortcuts import render
from django.contrib import messages
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
import pkg_resources  # Import pkg_resources
from .forms import SimulationForm  # Replace with your actual form import
from scipy import stats  # Import scipy for KS test
from .models import DataPoint, NormalFDP, ExponentialFDP, LogarithmicFDP
from variable.models import Variable
from product.models import Product
from business.models import Business, BusinessProduct
from sympy import Eq, sympify
import openai

# Set the OpenAI API key
openai.api_key = settings.OPENAI_API_KEY

class AppsView(LoginRequiredMixin, TemplateView):
    pass

def ks_test_view(request, variable_name):
    try:
        # Retrieve the variable by name
        variable = Variable.objects.get(name=variable_name)

        # Retrieve the dataset and FDP parameters
        data_points = DataPoint.objects.values_list('value', flat=True)
        fdp = variable.fdp  # Get the associated FDP from the variable

        # Define distribution type based on the FDP subclass
        if isinstance(fdp, NormalFDP):
            distribution_type = 'norm'
            distribution_args = (fdp.mean, fdp.std_deviation)
        elif isinstance(fdp, ExponentialFDP):
            distribution_type = 'expon'
            distribution_args = (0, 1 / fdp.lambda_param)
        elif isinstance(fdp, LogarithmicFDP):
            distribution_type = 'lognorm'
            distribution_args = (fdp.mean, fdp.std_deviation)

        # Calculate the KS statistic and p-value
        ks_statistic, p_value = stats.kstest(data_points, distribution_type, args=distribution_args)

        # Interpret the results
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

    return render(request, 'ks_test_template.html', context)

# Define a view for equation analysis
def equation_analysis_view(request):
    try:
        # Sample equation (you can replace this with your input)
        equation_str = "x + y = 10"
        equation = Eq(sympify(equation_str), 10)

        # Extract variable names
        variables = list(equation.free_symbols)

        # Create a dependency graph (you may need to implement this)
        # It seems like you're missing the 'create_dependency_graph' function

        # Resolve dependencies and query the database
        variable_data = []
        for variable in variables:
            # Replace 'query_database_for_variable_values' and 'evaluate_expression' with your actual logic
            dependencies = []  # You need to define the dependencies
            values = query_database_for_variable_values(dependencies)
            variable_value = evaluate_expression(equation, values)
            variable_data.append({"name": variable, "value": variable_value})

        # Render a template with the variable data
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

# Define a view to create equations
def create_simulation_equations(request):
    try:
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
        context = {
            "equations": equations,
        }

    except Exception as e:
        context = {
            'error_message': str(e),
        }

    return render(
        request,
        "simulation/equations.html",  # Replace with your actual template file
        context,
    )

# Define a function to generate equations for variables using OpenAI
def generate_equation_from_variable(variable):
    try:
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

    except Exception as e:
        return str(e)

# Define a view to extract the demand_historic variable
def extract_demand_historic(request):
    try:
        demand_historic_variable = Variable.objects.get(name="demand_historic")
        context = {
            'demand_historic_variable': demand_historic_variable,
        }

    except Variable.DoesNotExist:
        context = {
            'error_message': 'Variable not found.',
        }

    return context

# Define a view for initializing simulation
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
        context = {'product': products, 'business': businesses}

    except Business.DoesNotExist:
        context = {
            'error_message': 'No business found.',
        }

    return render(request, 'simulate/simulate-init.html', context)