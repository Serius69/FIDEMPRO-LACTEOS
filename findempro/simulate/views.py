from http.client import HTTPResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
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
from questionary.models import QuestionaryResult,Questionary,Answer,Question
from sympy import Eq, sympify
import openai
openai.api_key = settings.OPENAI_API_KEY
from django.http import JsonResponse
from scipy.stats import kstest
import numpy as np
class AppsView(LoginRequiredMixin, TemplateView):
    pass

def simulate_init_view(request):
    form = SimulationForm(request.POST or None, request.FILES or None)
    questionnaires_result = QuestionaryResult.objects.filter(is_active=True).order_by('-id')
    simulation_instance = None    
    selected_questionary_result_id = None
    started = request.session.get('started', False)
    selected = request.session.get('started', False)
    
    if request.method == 'GET' and 'select' in request.GET:
        request.session['selected'] = True 
        selected_questionary_result_id = request.GET.get('selected_questionary_result', 0)
        questionary_result = get_object_or_404(QuestionaryResult, pk=selected_questionary_result_id)
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
            # fk_variable1=questionary_result,
            )
        
        # aqui se tomaran las expressiones de las equaciones y se les asignaran los valores de las respuestas
        equations_with_values = []
        
        for equation in equations_to_use:
            answers = Answer.objects.filter(is_active=True).order_by('id').filter(
                Q(fk_question__fk_variable=equation.fk_variable2) | 
                Q(fk_question__fk_variable=equation.fk_variable3) | 
                Q(fk_question__fk_variable=equation.fk_variable4), 
                fk_questionary_result_id=selected_questionary_result_id)

            questions = Question.objects.filter(is_active=True).order_by('id').filter(
                Q(fk_variable=equation.fk_variable2) | 
                Q(fk_variable=equation.fk_variable3) | 
                Q(fk_variable=equation.fk_variable4), 
                fk_questionary_id=int(selected_questionary_result_id))

            try:
                answer = answers.filter(fk_question__fk_variable=equation.fk_variable2).first()
                if answer is not None:
                    equation.expression = equation.expression.replace('var2', str(answer.answer))
                else:
                    equation.expression = equation.expression.replace('var2', '0')  # Use a default value or handle as needed
            except Answer.DoesNotExist:
                equation.expression = equation.expression.replace('var2', '0')  # Use a default value or handle as needed

            try:
                answer = answers.filter(fk_question__fk_variable=equation.fk_variable3).first()
                if answer is not None:
                    equation.expression = equation.expression.replace('var3', str(answer.answer))
                else:
                    equation.expression = equation.expression.replace('var3', '0')  # Use a default value or handle as needed
            except Answer.DoesNotExist:
                equation.expression = equation.expression.replace('var3', '0')  # Use a default value or handle as needed
                
            equations_with_values.append(equation.expression)
        
        context = {
            'areas': areas,
            'answers': answers,
            'questionnaires': questionnaires,
            'started': started,
            'selected': selected,
            'equations_to_use': equations_to_use,
            'questionnaires_result': questionnaires_result,
            'equations_with_values': equations_with_values
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
        demand_historic = get_object_or_404(
            Answer, 
            fk_question_question='Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).',
            fk_questionary_result_id=simulation_instance.fk_questionary_result_id
            )
        DemandHistorical.objects.create(demand=demand_historic.answer)
        # segundo mandar esa demanda a la prueba de kolmogorov smirnov
        ProbabilisticDensityFunctionmanager.kolmovorov_smirnov_test(demand_historic.answer)
        print(demand_historic.answer)
                                                             
        # tercero tomar que tipo de distribucion toma
        fdp = ProbabilisticDensityFunctionmanager.get_fdp(demand_historic.fk_question.fk_variable.fk_fdp_id)
        
        new_simulation = Simulation(
            fk_product=simulation_instance.fk_product,
            fk_business=simulation_instance.fk_business,
            fk_questionary_result=simulation_instance.fk_questionary_result,
            fk_fdp=fdp,
            is_active=True
        )
        # aqui solamente hacermos el guardado de la simulacion
        new_simulation.save()        
        #cuarto hacer la simulacion
        print("se creo la simulacion")
        context = {
            'simulation_instance': simulation_instance,
            'data_demand_historic': demand_historic,
            'started': started,
            'selected': selected,
            'questionnaires_result': questionnaires_result,
        }
        return redirect('simulate:simulate.init')  # Redirect to the next step in the simulation

    if form.errors:
        messages.error(request, "Form validation failed. Please check your inputs.")

    print("salida normal")
    context = {
        'simulation_instance': simulation_instance,
        'started': started,
        'selected': selected,
        'questionnaires_result': questionnaires_result,
        'form': form,
    }
    return render(request, 'simulate/simulate-init.html', context)
    
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

            if isinstance(fdp, fdp.NormalDistribution):
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


# aqui se le manda el Simulate object que se creo en la vista de arriba
def simulate_result_simulation_view(request):
    
    
    
    
    
    
    
    data = {
            'demanda_inicial': 100,
            'tasa_crecimiento': 5,
            'horizonte': 12,
            'utilidad_neta': 2000,
            'flujo_caja': 5000,
            'simulate': {
                'date': '2023-11-23',
                'variable': 'Variable 1',
                'unit': 'Unit 1',
                'unittime': 'Month',
                'result': 'Result 1'
            },
            'demand_data': [100, 105, 110, 115, 120, 125, 130, 135, 140, 145, 150, 155],
            }
    return render(request, 'simulate/simulate-result.html',data)

    