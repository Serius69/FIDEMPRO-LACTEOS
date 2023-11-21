from http.client import HTTPResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
import pkg_resources  # Import pkg_resources
from .forms import SimulationForm  # Replace with your actual form import
from scipy import stats  # Import scipy for KS test
from .models import DataPoint, ProbabilisticDensityFunction
from variable.models import Variable, Equation, EquationResult
from product.models import Product, Area
from business.models import Business
from simulate.models import Simulation,ResultSimulation,HistoricalDemand
from questionary.models import QuestionaryResult,Questionary,Answer
from sympy import Eq, sympify
import openai
openai.api_key = settings.OPENAI_API_KEY
from django.http import JsonResponse
class AppsView(LoginRequiredMixin, TemplateView):
    pass

def simulate_init(request):
    simulation_started = request.session.get('simulation_started', False)

    if request.method == 'GET' and 'selected_questionary_result' in request.GET:
        selected_questionary_id = request.GET.get('selected_questionary_result', 0)
        areas = Area.objects.order_by('id').filter(
            is_active=True, fk_product__fk_business__fk_user=request.user, 
            fk_questionary_id=selected_questionary_id)

        answers = Answer.objects.order_by('id').filter(
            is_ready=True, fk_questionary_result_id=selected_questionary_id)
        
        questionnaires = Questionary.objects.order_by('id').filter(
            is_active=True, fk_business__fk_user=request.user)
        
        context = {
            'areas': areas,
            'answers': answers,
            'questionnaires': questionnaires,
        }
        
        return render(request, 'simulate/simulate-init.html', context)

    if not simulation_started:
        # Si la simulacion no está iniciada
        businesses = Business.objects.filter(fk_user=request.user).order_by('-id')
        products = Product.objects.filter(
            is_active=True,
            fk_business__fk_user=request.user,
        ).order_by('-id')

        questionnaires_result = QuestionaryResult.objects.filter(
            is_active=True,
            fk_product__fk_business__fk_user=request.user,
        ).order_by('-id')

        if request.method == "POST":
            # Aqui se hara lo que no se vera por pantalla mandando los datos a la clase AreaManager, EquationManager, ProbabilisticDensityFunctionmanager
            form = SimulationForm(request.POST, request.FILES)
            if form.is_valid():
                simulation_instance = form.save(commit=False)
                # simulation_instance.save()
                request.session['simulation_started'] = True
                # Aqui se hacen los querys para tomar datos necesarios para mandar y generar la simulacion
                answers = Answer.objects.order_by('id').filter(
                    fk_questionary_result_id=simulation_instance.fk_questionary_result_id)
                areas = Area.objects.order_by('id').filter(fk_product_id=simulation_instance.fk_product_id)
                #Aqui se mandara el valor de la demanda historica a ProbabilisticDensityFunctionManager para hacer el test KS y con eso saber que distribucion sigue
                uploaded_file = request.FILES['file']
                
                # Procesar el archivo y extraer la información
                historical_demand_data = []
                for line in uploaded_file:
                    month, demand = map(int, line.strip().split(','))
                    historical_demand_data.append((month, demand))

                # Puedes guardar la información en el modelo si es necesario
                for month, demand in historical_demand_data:
                    HistoricalDemand.objects.create(month=month, demand=demand)

                # Almacenar la información en una variable si es necesario
                data_demand_historic = historical_demand_data
                
                # Aqui se analizara que distribucion sigue la demanda historica
                ProbabilisticDensityFunctionmanager.kolmovorov_smirnov_test(data_demand_historic)
                
                #aqui se mandara los datos a la clase para armar las ecuaciones
                EquationManager.associate_answers_with_equation(answers)

                # aqui se recogeran los resultados de las ecuaciones por area
                AreaManager.associate_areas_with_equation(areas)

                equations = []  # Define equations here

                equation_results = []  # Define equation_results here

                Simulatemanager.simulate(form, equations, areas, answers, equation_results)

                # aqui se cargaran los datos
                chart_data = [...]  # Replace with actual chart data
                table_data = [...]  # Replace with actual table data 
                response_data = {
                    'chartData': chart_data,
                    'tableData': table_data,
                }

                
                context = {
                    'simulation_instance': simulation_instance,
                    'started': simulation_started,
                    'data_demand_historic': data_demand_historic,
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
        # Aqui solo se armara lo que se vera en pantalla
        # Si la simulación está iniciada
        simulation_id = request.session.get('simulation_id')
        simulation_instance = Simulation.objects.get(pk=simulation_id)

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

class Simulatemanager:
    @classmethod
    def get_simulation(cls, simulation_id):
        return Simulation.objects.get(pk=simulation_id)

class Simulatemanager:
    @classmethod
    def simulate(cls, form, equations, areas, answers, equation_results):
        # Logic to perform the simulation using the provided data
        # ...

        # Here, you can access the form data using `form.cleaned_data`
        # You can access the equations, areas, answers, and equation_results as parameters

        # Example simulation logic:
        simulation_data = {
            'form_data': form.cleaned_data,
            'equations': equations,
            'areas': areas,
            'answers': answers,
            'equation_results': equation_results,
        }

        # Perform the simulation calculations
        # ...

        # Return the simulation results
        return simulation_data

class ProbabilisticDensityFunctionmanager:
    @classmethod
    def get_fdp(cls, fdp_id):
        return ProbabilisticDensityFunction.objects.get(pk=fdp_id)
    @classmethod
    def kolmogorov_smirnov_test(cls, data_demand_historic):
        try:
            if not data_demand_historic:
                raise Variable.DoesNotExist('Variable not found.')

            data_points = DataPoint.objects.values_list('value', flat=True)
            fdp = data_demand_historic.fdp

            if isinstance(fdp, NormalDistribution):
                distribution_type = 'norm'
                distribution_args = (fdp.mean, fdp.std_deviation)
            elif isinstance(fdp, ExponentialDistribution):
                distribution_type = 'expon'
                distribution_args = (0, 1 / fdp.lambda_param)
            elif isinstance(fdp, LogNormalDistribution):
                distribution_type = 'lognorm'
                distribution_args = (fdp.mean, fdp.std_deviation)
            else:
                return JsonResponse({'error_message': 'Invalid distribution type.'})

            p_value = stats.kstest(data_points, distribution_type, args=distribution_args)

            if p_value < 0.05:
                result = "Reject null hypothesis: Data does not fit the distribution."
            else:
                result = "Fail to reject null hypothesis: Data fits the distribution."

            return HTTPResponse(result)

        except Variable.DoesNotExist:
            return JsonResponse({'error_message': 'Variable not found.'})
class AreaManager: 
    @classmethod
    def get_area(cls, area_id):
        return Area.objects.get(pk=area_id)
    
    @classmethod
    def associate_areas_with_equation(cls, areas):
        for area in areas:
            cls.associate_area_with_equation(area)
            
    @classmethod    
    def associate_area_with_equation(cls, area):
        #Obtener la ecuacion asociada al area
        equation = Equation.objects.get(fk_area=area)
        equation.save()
    
    @classmethod
    def resolve_equations_from_area(cls, equation):
        # Obtener las variables de la ecuación
        variables = ['var1', 'var2', 'var3', 'var4', 'var5']
        # Sustituir las variables en la expresión con los valores de las respuestas
        for var in variables:
            if var in expression:
                expression = expression.replace(var, str(getattr(answer, var)))

        return expression

class EquationManager:
    @classmethod
    def associate_answers_with_equation(cls, answers):
        for answer in answers:
            cls.associate_answer_with_equation(answer)
    @classmethod
    def associate_answer_with_equation(cls, answer, area):
        # Obtener la ecuación asociada a la pregunta de la respuesta
        question = answer.fk_question
        # se toma su ecuacion y de ahi se saca la expresion
         # # Obtener la ecuación asociada a la pregunta de la respuesta
        equation = Equation.objects.get(
            fk_area=question.fk_area)

        equation_result = EquationResult(
            fk_equation=equation,
            result=result,
            is_active=True  # Puedes ajustar este valor según tus necesidades
        )
        equation_result.save()
        # # Actualizar la ecuación con la información de la respuesta
        # updated_expression = cls.update_equation_expression(equation.expression, answer)

        # # Guardar la ecuación actualizada en la base de datos
        # equation.expression = updated_expression
        equation.save()

    @staticmethod
    def update_equation_expression(expression, answer):
        # Obtener las variables de la ecuación
        variables = ['var1', 'var2', 'var3', 'var4', 'var5']

        # Sustituir las variables en la expresión con los valores de las respuestas
        for var in variables:
            if var in expression:
                expression = expression.replace(var, str(getattr(answer, var)))

        return expression