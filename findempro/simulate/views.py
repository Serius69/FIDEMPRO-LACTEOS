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
from simulate.models import Simulation,ResultSimulation,DemandHistorical
from questionary.models import QuestionaryResult,Questionary,Answer
from sympy import Eq, sympify
import openai
openai.api_key = settings.OPENAI_API_KEY
from django.http import JsonResponse
class AppsView(LoginRequiredMixin, TemplateView):
    pass

def simulate_init_view(request):
    businesses = Business.objects.filter(fk_user=request.user).order_by('-id')
    products = Product.objects.filter(is_active=True, fk_business__fk_user=request.user).order_by('-id')
    questionnaires_result = QuestionaryResult.objects.filter(is_active=True).order_by('-id')
    simulation_instance = None
    form = SimulationForm(request.POST or None, request.FILES or None)
    started = request.session.get('started', False)
    selected = request.session.get('started', False)
    selected_questionary_result_id = None
    if request.method == 'GET' and 'select' in request.GET:
        request.session['selected'] = True 
        selected_questionary_result_id = request.GET.get('selected_questionary_result', 0)
        request.session['selected_questionary_result_id'] = selected_questionary_result_id
        print("aqui se setea la variable selected_questionary_result_id " + str(selected_questionary_result_id))
        areas = Area.objects.order_by('id').filter(
            is_active=True, 
            fk_product__fk_business__fk_user=request.user,
        )
        answers = Answer.objects.order_by('id').filter(is_active=True, fk_questionary_result_id=selected_questionary_result_id)
        questionnaires = Questionary.objects.order_by('id').filter(is_active=True, fk_product__fk_business__fk_user=request.user)
        questionnaires_result = QuestionaryResult.objects.filter(is_active=True).order_by('-id')
        
        equations_to_use = Equation.objects.order_by('id').filter(
            is_active=True, 
            fk_area__fk_product__fk_business__fk_user=request.user,
            # fk_variable=answers.fk_questionary.fk_variable,
            )
        context = {
            'areas': areas,
            'answers': answers,
            'questionnaires': questionnaires,
            'started': started,
            'selected': selected,
            'equations_to_use': equations_to_use,
            'questionnaires_result': questionnaires_result,
        }
        return render(request, 'simulate/simulate-init.html', context)
    if request.method == 'POST' and 'cancel' in request.POST:
        request.session['selected'] = False 
        selected_questionary_result_id = request.POST.get(None)
        print("Se cancelo el cuestionario")
        return redirect('simulate:simulate.init')

    if request.method == "POST" and form.is_valid() and 'start' in request.POST:
        request.session['started'] = True 
        simulation_instance = form.save(commit=False)
        answers = Answer.objects.order_by('id').filter(fk_questionary_result_id=simulation_instance.fk_questionary_result_id)
        areas = Area.objects.order_by('id').filter(fk_product_id=simulation_instance.fk_product_id)
        
        # primero buscar la demanda historica guardada en el resultado del cuestionario
        demanda_historica = get_object_or_404(
            Answer, 
            fk_question_question='Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).',
            fk_questionary_result_id=simulation_instance.fk_questionary_result_id
            )
        DemandHistorical.objects.create(demand=demanda_historica.answer)
        # segundo mandar esa demanda a la prueba de kolmogorov smirnov
        ProbabilisticDensityFunctionmanager.kolmovorov_smirnov_test(demanda_historica.answer)
        print(demanda_historica.answer)
                                                             
        # tercero tomar que tipo de distribucion toma
        fk_fdp = ProbabilisticDensityFunctionmanager.get_fdp(demanda_historica.fk_question.fk_variable.fk_fdp_id)
        
        # 
        equations_to_use = EquationManager.associate_answers_with_equation(answers)
        
        #cuarto hacer la simulacion
        

        ProbabilisticDensityFunctionmanager.kolmovorov_smirnov_test(historical_demand_data)
        EquationManager.associate_answers_with_equation(answers)
        AreaManager.associate_areas_with_equation(areas)
        Simulatemanager.simulate(form, [], areas, answers, [])
        
        
        
        context = {
            'simulation_instance': simulation_instance,
            'data_demand_historic': historical_demand_data,
            'products': products,
            'businesses': businesses,
            'started': started,
            'selected': selected,
            'questionnaires_result': questionnaires_result,
        }
        
        # aqui solamente hacermos el guardado de la simulacion
        return redirect('simulate:simulate.init')  # Redirect to the next step in the simulation

    if form.errors:
        messages.error(request, "Form validation failed. Please check your inputs.")

    context = {
        'simulation_instance': simulation_instance,
        'products': products,
        'started': started,
        'selected': selected,
        'questionnaires_result': questionnaires_result,
        'form': form,
    }
    return render(request, 'simulate/simulate-init.html', context)
    

class Simulatemanager:
    @classmethod
    def get_simulation(cls, simulation_id):
        return Simulation.objects.get(pk=simulation_id)

class Simulatemanager:
    @classmethod
    def simulate(cls, form, equations, areas, answers, equation_results):
        
        
        # primero 
        
        
        
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
        
        equations_with_answers    
        
        return equations_with_answers
    @classmethod
    def associate_answer_with_equation(cls, answer, area):
        # Obtener la ecuación asociada a la pregunta de la respuesta
        question = answer.fk_question
        # se toma su ecuacion y de ahi se saca la expresion
        # Obtener la ecuación asociada a la pregunta de la respuesta
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

def simulate_result_simulation_view(request):
    # Logic to fetch data for the current step of the simulation
    products = [...]  # Replace with actual data
    businesses = [...]  # Replace with actual data
    questionnaires_result = [...]  # Replace with actual data

    simulation_id = request.session.get('simulation_id')
    simulation_instance = Simulation.objects.get(pk=simulation_id)
    simulation_started = True  # Replace with actual logic to check if simulation is started

    response_data = {
            'chartData': self.get_chart_data(),
            'tableData': self.get_table_data(),
        }

    context = {
        'products': products,
        'businesses': businesses,
        'questionnaires_result': questionnaires_result,
        'response_data': response_data,
        'simulation_instance': simulation_instance,
        'started': simulation_started,
    }
    def get_chart_data(self):
            # Replace with actual chart data
            chart_data = [...]  
            return chart_data

    def get_table_data(self):
            # Replace with actual table data
            table_data = [...]  
            return table_data
    return render(request, 'simulate/simulate-init.html', context)

    