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
from .utils import get_results_for_simulation, analyze_simulation_results, decision_support
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

class AppsView(LoginRequiredMixin, TemplateView):
    pass
def simulate_show_view(request):
    started = request.session.get('started', False)
    form = SimulationForm(request.POST or None, request.FILES or None)
    # questionnaires_result = QuestionaryResult.objects.filter(is_active=True,).order_by('-id')
    questionnaires_result = None
    simulation_instance = None    
    selected_questionary_result_id = None
    questionary_result_instance = None
    areas = None
    
    if request.method == 'GET' and 'select' in request.GET:
        selected_questionary_result_id = request.GET.get('selected_questionary_result', 0)
        request.session['selected_questionary_result_id'] = selected_questionary_result_id
        answers = Answer.objects.order_by('id').filter(is_active=True, fk_questionary_result_id=selected_questionary_result_id)
        equations_to_use = Question.objects.order_by('id').filter(is_active=True, fk_questionary__fk_product__fk_business__fk_user=request.user, fk_questionary_id=selected_questionary_result_id)
        questionnaires_result = QuestionaryResult.objects.filter(is_active=True, 
                                                                 fk_questionary__fk_product__fk_business__fk_user=request.user).order_by('-id')
                    
        questionary_result_instance = get_object_or_404(QuestionaryResult, pk=selected_questionary_result_id)
            
        print(questionary_result_instance.fk_questionary.fk_product)
        product_instance = get_object_or_404(Product, pk=questionary_result_instance.fk_questionary.fk_product.id)
        print(product_instance.id)
        areas = Area.objects.order_by('id').filter(
            is_active=True, 
            fk_product__fk_business__fk_user=request.user,
            fk_product_id=product_instance.id
        )
        questionary_result_instance= get_object_or_404(QuestionaryResult, pk=selected_questionary_result_id)
        print("Se selecciono el cuestionario " + str(selected_questionary_result_id))
        print("aqui se setea la variable selected_questionary_result_id " + str(selected_questionary_result_id))
        print("Started: " + str(started))
        print(areas)
        context = {
            'areas': areas,
            'answers': answers,
            'equations_to_use': equations_to_use,
            'questionnaires_result': questionnaires_result,
            'questionary_result_instance': questionary_result_instance,
        }
        return render(request, 'simulate/simulate-init.html', context)
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
        print("se comenzara con la simulacion")
        print("Started: " + str(started))
        context = {
            'areas': areas,
            'simulation_instance': simulation_instance,
            'data_demand_historic': demand_historic,
            'started': started,            
            'questionnaires_result': questionnaires_result,
            'questionary_result_instance': questionary_result_instance,
        }
        return redirect('simulate:simulate.show')  # Redirect to the next step in the simulation
    if request.method == 'POST' and 'cancel' in request.POST:
        request.session['selected'] = False 
        print("Se cancelo el cuestionario")
        return redirect('simulate:simulate.show')
    
    if not started:
        if selected_questionary_result_id == None:
            questionnaires_result = QuestionaryResult.objects.filter(is_active=True,fk_questionary__fk_product__fk_business__fk_user=request.user).order_by('-id')
        else:
            equations_to_use = Question.objects.order_by('id').filter(is_active=True, fk_questionary__fk_product__fk_business__fk_user=request.user, fk_questionary_id=selected_questionary_result_id)
            questionnaires_result = QuestionaryResult.objects.filter(is_active=True,fk_questionary__fk_product__fk_business__fk_user=request.user).order_by('-id')
                    
            questionary_result_instance = get_object_or_404(QuestionaryResult, pk=selected_questionary_result_id)
            
            questionary_instance = get_object_or_404(Questionary, )
            print(questionary_result_instance.fk_questionary.fk_product)
            product_instance = get_object_or_404(Product, pk=questionary_result_instance.fk_questionary.fk_product)
            
            
            areas = Area.objects.order_by('id').filter(
                is_active=True, 
                fk_product__fk_business__fk_user=request.user,
                fk_product=product_instance
            )
            paginator = Paginator(equations_to_use, 10) 
            page = request.GET.get('page')
            try:
                equations_to_use = paginator.page(page)
            except PageNotAnInteger:
                equations_to_use = paginator.page(1)
            except EmptyPage:
                equations_to_use = paginator.page(paginator.num_pages)
        print("no se inicio la simulacion")
        print("Started: " + str(started))
        context = {
            'selected_questionary_result_id':selected_questionary_result_id,
            'started': started,
            'form': form,
            'areas': areas,
            'questionnaires_result': questionnaires_result,
            'questionary_result_instance': questionary_result_instance,
        }
        return render(request, 'simulate/simulate-init.html', context)
    else:
        
        print("se inicio la simulacion")
        print("Started: " + str(started))
        context = {
            'simulation_instance': simulation_instance,
            'started': started,
            'questionnaires_result': questionnaires_result,
            'questionary_result_instance': questionary_result_instance,
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
    results = get_results_for_simulation(simulation_id)
    analysis_results = analyze_simulation_results(results)
    decision = decision_support(analysis_results)
    
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

    