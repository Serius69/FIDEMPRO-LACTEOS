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
from scipy.stats import kstest,norm,expon,lognorm
import matplotlib.pyplot as plt
import numpy as np
from .utils import get_results_for_simulation, analyze_simulation_results, decision_support
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import json
import statistics
from io import BytesIO
import base64
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
        selected_quantity_time = request.GET.get('selected_quantity_time', 0)
        selected_unit_time = request.GET.get('selected_unit_time', 0)
        request.session['selected_questionary_result_id'] = selected_questionary_result_id
        answers = Answer.objects.order_by('id').filter(is_active=True, fk_questionary_result_id=selected_questionary_result_id)
        equations_to_use = Question.objects.order_by('id').filter(is_active=True, fk_questionary__fk_product__fk_business__fk_user=request.user, fk_questionary_id=selected_questionary_result_id)
        questionnaires_result = QuestionaryResult.objects.filter(is_active=True, 
                                                                 fk_questionary__fk_product__fk_business__fk_user=request.user).order_by('-id')
        # no tocar
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
        # hasta aqui no tocar
        
        # primero buscar la demanda historica guardada en el resultado del cuestionario
        demand_history = get_object_or_404(
            Answer, 
            fk_question__question='Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).',
            fk_questionary_result_id=selected_questionary_result_id
            )
        print(demand_history.answer)   
        # numbers = json.loads(demand_history.answer)
        # solo para probar
        numbers = json.loads('[513, 820, 648, 720, 649, 414, 704, 814, 647, 934, 483, 882, 220, 419, 254, 781, 674, 498, 518, 948, 983, 154, 649, 625, 865, 800, 848, 783, 218, 906]')
        demand_mean = statistics.mean(numbers)
        DemandHistorical.objects.create(demand=demand_mean)
             
        # segundo mandar esa demanda a la prueba de kolmogorov smirnov
        prob_density_function = ProbabilisticDensityFunction.objects.get(pk=1)  # Reemplaza 1 con el ID de tu objeto
        # La muestra de datos
        data = numbers
        # Genera la PDF basada en el tipo de distribución almacenada en el modelo
        if prob_density_function.distribution_type == 1:  # Normal distribution
            mean = prob_density_function.mean_param
            std_dev = prob_density_function.std_dev_param
            if std_dev is not None:
                pdf = norm.pdf(data, loc=mean, scale=std_dev)
            else:
                pdf = np.zeros_like(data)
        elif prob_density_function.distribution_type == 2:  # Exponential distribution
            lambda_param = prob_density_function.lambda_param
            pdf = expon.pdf(data, scale=1 / lambda_param)
        elif prob_density_function.distribution_type == 3:  # Logarithmic distribution
            s = prob_density_function.lognormal_shape_param
            scale = prob_density_function.lognormal_scale_param
            pdf = lognorm.pdf(data, s=s, scale=scale)
        else:
            pdf = None

        # Plotea la distribución de la muestra y la PDF generada
        plt.hist(data, bins=20, density=True, alpha=0.5, label='Sample Distribution')
        plt.plot(data, pdf, label='Probability Density Function (PDF)')
        plt.legend()
        plt.xlabel('Value')
        plt.ylabel('Probability Density')
        plt.title('Comparison of Sample Distribution and PDF')
        plt.show()
        
        # Guarda el gráfico en un BytesIO buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)

        # Codifica el buffer en base64 para pasarlo al template
        image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        

        print("Se selecciono el cuestionario " + str(selected_questionary_result_id))
        print("aqui se setea la variable selected_questionary_result_id " + str(selected_questionary_result_id))
        print("Started: " + str(started))
        print(areas)
        context = {
            'areas': areas,
            'answers': answers,
            'fdp': prob_density_function,
            'demand_history': demand_history,
            'equations_to_use': equations_to_use,
            'questionnaires_result': questionnaires_result,
            'questionary_result_instance': questionary_result_instance,
            'selected_unit_time': selected_unit_time,
            'selected_quantity_time': selected_quantity_time,
        }
        return render(request, 'simulate/simulate-init.html', context)
    
    if request.method == "POST" and form.is_valid() and 'start' in request.POST:
        # tomar los valores
        request.session['started'] = True     
        simulation_instance = form.save(commit=False)
        answers = Answer.objects.order_by('id').filter(fk_questionary_result_id=simulation_instance.fk_questionary_result_id)
        areas = Area.objects.order_by('id').filter(fk_product_id=simulation_instance.fk_product_id)
                                                             
        # tercero tomar que tipo de distribucion toma
        # Supongamos que tienes un objeto ProbabilisticDensityFunction
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
            # 'data_demand_historic': demand_historic,
            'started': started,            
            'questionnaires_result': questionnaires_result,
            'questionary_result_instance': questionary_result_instance,
            'image_data': image_data
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
  
# aqui se le manda el Simulate object que se creo en la vista de arriba
def simulate_result_simulation_view(request, simulation_id):
    results = get_results_for_simulation(simulation_id)
    analysis_results = analyze_simulation_results(results)
    decision = decision_support(analysis_results)
    

    return render(request, 'simulate/simulate-result.html')

    