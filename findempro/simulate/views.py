# Standard library imports
from datetime import datetime
from http.client import HTTPResponse
from io import BytesIO
import base64
import json
import os
import pkg_resources
import statistics

# Third-party imports
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import openai
from scipy import stats
from scipy.stats import kstest, norm, expon, lognorm
from sympy import Eq, sympify

# Local application imports
from .forms import SimulationForm
from .models import ProbabilisticDensityFunction
from .utils import get_results_for_simulation
from business.models import Business
from dashboards.models import Chart
from finance.models import FinanceRecommendation
from finance.utils import analyze_simulation_results, decision_support
from product.models import Product, Area
from questionary.models import QuestionaryResult, Questionary, Answer, Question
from simulate.models import Simulation, ResultSimulation, Demand, DemandBehavior
from variable.models import Variable, Equation, EquationResult

# Set matplotlib to non-interactive mode to avoid error in web environments
matplotlib.use('Agg')

# Set OpenAI API key
openai.api_key = settings.OPENAI_API_KEY
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
        questionnaires_result = QuestionaryResult.objects.filter(is_active=True, fk_questionary__fk_product__fk_business__fk_user=request.user).order_by('-id')
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
        numbers = json.loads(demand_history.answer)
        # solo para probar
        # numbers = json.loads('[513, 820, 648, 720, 649, 414, 704, 814, 647, 934, 483, 882, 220, 419, 254, 781, 674, 498, 518, 948, 983, 154, 649, 625, 865, 800, 848, 783, 218, 906]')
        demand_mean = statistics.mean(numbers)
        # Demand.objects.create(
        #     quantity=demand_mean,
        #     fk_simulation=,
        #     fk_product=
        #     is_predicted=False)
             
        # segundo mandar esa demanda a la prueba de kolmogorov smirnov
        prob_density_function = ProbabilisticDensityFunction.objects.filter(
            fk_business__fk_user=questionary_result_instance.fk_questionary.fk_product.fk_business.fk_user
        ).first()        # La muestra de datos
        data = numbers
        # Genera la PDF basada en el tipo de distribución almacenada en el modelo
        if prob_density_function.distribution_type == 1:  # Normal distribution
            mean = prob_density_function.mean_param
            std_dev = prob_density_function.std_dev_param
            if std_dev is not None:
                pdf = norm.pdf(data, loc=mean, scale=std_dev)
                distribution_label = 'Distribución normal'
            else:
                pdf = np.zeros_like(data)
                distribution_label = 'Distribución desconocida'
        elif prob_density_function.distribution_type == 2:  # Exponential distribution
            lambda_param = prob_density_function.lambda_param
            pdf = expon.pdf(data, scale=1 / lambda_param)
            distribution_label = 'Distribución exponencial'
        elif prob_density_function.distribution_type == 3:  # Logarithmic distribution
            s = prob_density_function.lognormal_shape_param
            scale = prob_density_function.lognormal_scale_param
            pdf = lognorm.pdf(data, s=s, scale=scale)
            distribution_label = 'Distribución logarítmica'
        else:
            pdf = None

        # Plotea la distribución de la muestra y la PDF generada
        plt.hist(data, bins=20, density=True, alpha=0.5, label='Demanda Historica')
        plt.plot(data, pdf, label=f'Función de densidad de probabilidad ({distribution_label})')
        plt.legend()
        plt.xlabel('Valor')
        plt.ylabel('Densidad de probabilidad')
        plt.title('Demanda historica VS Funcion de Densidad de Probabilidad (FDP)')        
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
            'image_data':image_data,
            'fdp': prob_density_function,
            # esta parte cambiar luego soloes para pruebas
            'demand_history': demand_mean,
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
        request.session['simulation_started_id'] = new_simulation.id
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
        # aqui ya tomar los datos de la simulacion que se creo en start
        simulation_instance = get_object_or_404(Simulation, pk=request.session['simulation_started_id'])
        nmd = simulation_instance.quantity_time
        # tomar la fdp para poder hacer los randoms en base a esa distribucion
        fdp = simulation_instance.fk_fdp
        # tomar las respuestas del cuestionario con el que se creo la simulacion
        all_answers = simulation_instance.fk_questionary_result.fk_questionary.fk_answers.all()
        # esto dentro de un for hasta llegar al maximo de dias ()
        for i in range(nmd):          
            # tomar las areas
            areas = Area.objects.filter(is_active=True, fk_product=simulation_instance.fk_product)
            for area in areas:
            # de cada area tomar las ecuaciones que la componen
                equations = Equation.objects.filter(is_active=True, fk_area=area)            
                # de cada ecuacion tomar las expresiones y llenarlas con las variables que la componen
                for equation in equations:                
                    equation.expressions = equation.expressions.replace(" ", "")
                    
                # resolver las expresiones y guardarlas en un diccionario
                    
                    
                    
                    # tomar las variables que componen la ecuacion
                    
                    
                            # tomar en cuenta que las variables tipo 1 son exogenas 
                            # Tomar en cuenta que las variables tipo 2 son endogenar
                            # tomar en cuenta que las variables tipo 3 son de estado
                            
                            
                # los resultados de las variables endogenas guardarlas en ResultSimulation.variables
                
            
            # calcular los parametros totales que cada area tuvi ese dia o mes o semana
            
            # aumentar al siguiente dia
            
        
        
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
    # analysis_results = analyze_simulation_results(results)
    # decision = decision_support(analysis_results)
    results_simulation = ResultSimulation.objects.filter(is_active=True,fk_simulation_id=simulation_id)
    simulation_instance = get_object_or_404(Simulation, pk=simulation_id)
    questionary_result_instance = get_object_or_404(QuestionaryResult, pk=simulation_instance.fk_questionary_result.id)
    product_instance = get_object_or_404(Product, pk=questionary_result_instance.fk_questionary.fk_product.id)
    business_instance = get_object_or_404(Business, pk=product_instance.fk_business.id)
    areas = Area.objects.filter(is_active=True, fk_product=product_instance)
    
    # demand_initial = get_object_or_404(Demand, pk=1)
     # Obtén datos de la base de datos
    result_simulations = ResultSimulation.objects.filter(is_active=True, 
                                                         fk_simulation_id=simulation_id)

    # Recopila todos los datos fuera del bucle
    all_labels = []
    all_values = []

    for result_simulation in result_simulations:
        data = result_simulation.get_average_demand_by_date()
        list_formatted_date = [] 
        if data: 
            for entry in data:
                date_object = entry['date']
                formatted_date = date_object.strftime('%Y-%m-%d')
                list_formatted_date.append(formatted_date)
                all_values.append(entry['average_demand'])

    # Asegúrate de que todas las fechas sean únicas
    all_labels = sorted(set(list_formatted_date))

    # Ordena all_values de acuerdo con all_labels
    sorted_values = [value for label, value in sorted(zip(list_formatted_date, all_values), key=lambda x: x[0])]

    chart_data = {
        'labels': all_labels,
        'values': sorted_values,
        'x_label': 'Date',
        'y_label': 'Average Demand',
    }

    # Crea el objeto Chart
    chart = Chart.objects.create(
        title=f'Average Demand Chart - All Simulations',
        chart_type='line',  # Cambia 'line' por el tipo de gráfico que desees
        chart_data=chart_data,
        fk_product=result_simulations[0].fk_simulation.fk_questionary_result.fk_questionary.fk_product,
        # Agrega más campos según sea necesario
    )
    # No tocar
    image_data=None
    file_name = f'line_chart_all_simulations.png'
    print(len(all_labels))
    print(len(all_values))
    if len(all_labels) == len(all_values):
        plt.plot(chart_data['labels'], chart_data['values'], marker='o')
        plt.xlabel(chart_data['x_label'])
        plt.ylabel(chart_data['y_label'])
        plt.title(chart.title)
        plt.savefig(file_name)
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
    else:
        print("Las listas tienen diferentes longitudes, no se puede trazar el gráfico correctamente.")    
    
    paginator = Paginator(results_simulation, 10)  # Show 10 results per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    page = request.GET.get('page')
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    
    financial_recomnmendations=FinanceRecommendation.objects.filter(is_active=True,
                                                                      fk_business_id=business_instance.id)
    
    paginator2 = Paginator(financial_recomnmendations, 10)  # Show 10 results per page.
    page_number2 = request.GET.get('page')
    page_obj2 = paginator2.get_page(page_number2)
    counter_start = (page_obj.number - 1) * paginator.per_page + 1
    
    
    # return render(request, 'your_template.html', {'page_obj': page_obj})
    context = {
        # 'demand_initial':demand_initial,
        'simulation_instance': simulation_instance,
        'results_simulation': results_simulation,
        # 'analysis_results': analysis_results,
        # 'decision': decision,
        'questionary_result_instance': questionary_result_instance,
        'product_instance': product_instance,
        'business_instance': business_instance,
        'areas': areas,
        'image_data': image_data,
        'page_obj'  : page_obj,
        'counter_start': counter_start,
        'page_obj2'  : page_obj2,
        'financial_recomnmendations':financial_recomnmendations
    }

    return render(request, 'simulate/simulate-result.html',context)

    