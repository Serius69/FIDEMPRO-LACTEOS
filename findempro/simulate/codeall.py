# Standard library imports
from datetime import datetime, timedelta
from http.client import HTTPResponse
from io import BytesIO
import base64
import json
import re
import math
import os
import pkg_resources
import statistics
import random
import numpy as np
import openai
from scipy import stats
from scipy.stats import kstest, norm, expon, lognorm
from scipy.optimize import minimize
from sympy import symbols, Eq, solve, SympifyError
from scipy.stats import gaussian_kde
# Third-party imports
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.http import *
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.urls import reverse
import matplotlib
import matplotlib.pyplot as plt
# Local application imports
from .forms import SimulationForm
from .models import ProbabilisticDensityFunction
from .utils import get_results_for_simulation
from business.models import Business
from dashboards.models import Chart
from finance.models import FinanceRecommendation,FinanceRecommendationSimulation
from finance.utils import analyze_simulation_results, decision_support
from product.models import Product, Area
from questionary.models import QuestionaryResult, Questionary, Answer, Question
from simulate.models import Simulation, ResultSimulation, Demand, DemandBehavior
from variable.models import Variable, Equation, EquationResult
import sympy as sp
from django.core.exceptions import *
import seaborn as sns

# Set matplotlib to non-interactive mode to avoid error in web environments
matplotlib.use('Agg')

# Set OpenAI API key
openai.api_key = settings.OPENAI_API_KEY
class AppsView(LoginRequiredMixin, TemplateView):
    pass

def plot_scatter_and_pdf(data, pdf, distribution_label, confidence_interval=0.95):
    fig, ax = plt.subplots(figsize=(10, 6))  # Aumentar el tamaño del gráfico


    # Scatter plot en lugar de histograma con ejes x e y intercambiados
    ax.scatter(np.arange(1, len(data) + 1), data, alpha=0.5, label='Demanda Historica', marker='o', edgecolor='none')  # Intercambio de ejes x e y

    # Configuración del gráfico
    ax.legend()
    ax.set_xlabel('Número de datos')  # Etiqueta en el eje x
    ax.set_ylabel('Demanda [Litros]')  # Etiqueta en el eje y
    ax.set_title('Demanda historica')

    # Guarda el gráfico en un BytesIO buffer
    buffer = BytesIO()
    fig.savefig(buffer, format='png')

    plt.grid(True)
    plt.close(fig)

    # Codifica el buffer en base64 para pasarlo al template
    buffer.seek(0)
    image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return image_data

def plot_histogram_and_pdf(data, pdf, distribution_label):
    fig, ax = plt.subplots(figsize=(10, 6))

    # Histograma
    ax.hist(data, bins=20, density=True, alpha=0.5, label='Demanda Historica', edgecolor='none')

    # Plot de la Función de Densidad de Probabilidad (FDP)
    if pdf is not None:
        ax.plot(data, pdf, label=f'Función de densidad de probabilidad ({distribution_label})')

    # Configuración del gráfico
    ax.legend()
    ax.set_xlabel('Demanda [Litros]')
    ax.set_ylabel('Densidad de probabilidad')
    ax.set_title('Demanda historica VS Funcion de Densidad de Probabilidad (FDP)')

    # Guarda el gráfico en un BytesIO buffer
    buffer = BytesIO()
    fig.savefig(buffer, format='png')

    # Cerrar la figura para liberar recursos
    plt.close(fig)

    # Codifica el buffer en base64 para pasarlo al template
    buffer.seek(0)
    image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return image_data

def simulate_show_view(request):
    started = request.session.get('started', False)
    form = SimulationForm(request.POST)
    # questionnaires_result = QuestionaryResult.objects.filter(is_active=True,).order_by('-id')
    questionnaires_result = None
    simulation_instance = None    
    selected_questionary_result_id = None
    questionary_result_instance = None
    areas = None
    businessess = Business.objects.filter(is_active=True, fk_user=request.user)
    products = Product.objects.filter(is_active=True,fk_business__in=businessess, fk_business__fk_user=request.user)
    
    if request.method == 'GET' and 'select' in request.GET:
        selected_questionary_result_id = request.GET.get('selected_questionary_result', 0)
        selected_quantity_time = request.GET.get('selected_quantity_time', 0)
        selected_unit_time = request.GET.get('selected_unit_time', 0)
        request.session['selected_questionary_result_id'] = selected_questionary_result_id
        answers = Answer.objects.order_by('id').filter(is_active=True, fk_questionary_result_id=selected_questionary_result_id)
        equations_to_use = Question.objects.order_by('id').filter(is_active=True, fk_questionary__fk_product__fk_business__fk_user=request.user, fk_questionary_id=selected_questionary_result_id)
        questionnaires_result = QuestionaryResult.objects.filter(is_active=True,fk_questionary__fk_product__in=products  , fk_questionary__fk_product__fk_business__fk_user=request.user).order_by('-id')
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
        demand_history = Answer.objects.filter(
            fk_question__question='Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).',
            fk_questionary_result_id=selected_questionary_result_id
        ).first()
        
        print("demanda historica")
        print(demand_history.answer)   
        # solo para prober
        # numbers = np.round(np.random.normal(loc=2500.0, scale=10.0, size=30)).astype(int)
        
        # Ajuste inicial de la FDP a los datos históricos
        
        # numbers = np.array(eval(demand_history.answer))
        cadena_numerica = demand_history.answer
        cadena_numerica = cadena_numerica.strip('[]')
        subcadenas = cadena_numerica.split()
        # Convierte las subcadenas en números
        numbers = np.array([float(subcadena) for subcadena in subcadenas])
        # numbers = np.array(json.loads(demand_history.answer))

        # Calcula la media
        media = np.mean(numbers)
            
        mean, std_dev = norm.fit(numbers)
        # Suavizado de datos con KDE
        kde = gaussian_kde(numbers)
        smoothed_data = kde(numbers)
        # Ajuste suave de parámetros de FDP teórica
        def loss_function(parameters):
            theoretical_pdf = norm.pdf(smoothed_data, loc=parameters[0], scale=parameters[1])
            loss = np.sum((smoothed_data - theoretical_pdf)**2)
            return loss
        initial_parameters = [mean, std_dev]
        result = minimize(loss_function, initial_parameters, method='L-BFGS-B')
        optimized_mean, optimized_std_dev = result.x
        results = []
        # segundo mandar esa demanda a la prueba de kolmogorov smirnov
        distributions = ProbabilisticDensityFunction.objects.filter(is_active=True, fk_business__fk_user=request.user).order_by('-id')
        demand_mean = statistics.mean(numbers)
        demand_mean_array = np.array([demand_mean])
        # Inicializa variables para el seguimiento del mejor ajuste
        best_distribution = None
        best_ks_statistic = float('inf')  # Inicializado a infinito para que cualquier valor lo mejore
        best_ks_p_value = 0.0  # Inicializado a 0 para que cualquier valor lo mejore
        data = numbers
        # Itera sobre las distribuciones almacenadas
        for distribution in distributions:
            if distribution.distribution_type == 1:  # Normal distribution
                theoretical_distribution = norm(loc=optimized_mean, scale=optimized_std_dev)
            elif distribution.distribution_type == 2:  # Exponential distribution
                theoretical_distribution = expon(scale=1/distribution.lambda_param)
            elif distribution.distribution_type == 3:  # Log-Normal distribution
                theoretical_distribution = lognorm(s=optimized_std_dev, scale=np.exp(optimized_mean))

            # Realiza la prueba de Kolmogorov-Smirnov
            ks_statistic, ks_p_value = kstest(demand_mean_array, theoretical_distribution.cdf)
            # Almacenar resultados en una estructura serializable
            result_data = {
                'distribution_type': distribution.get_distribution_type_display(),
                'ks_statistic': ks_statistic,
                'ks_p_value': ks_p_value,
                'mean_param': distribution.mean_param,
                'std_dev_param': distribution.std_dev_param,
                'lambda_param': distribution.lambda_param,
                # Agrega otros atributos que desees serializar
            }
            results.append(result_data)
            # Actualiza el mejor ajuste si el valor p es más alto
            if ks_p_value > best_ks_p_value:
                best_ks_statistic = ks_statistic
                best_ks_p_value = ks_p_value
                best_distribution = distribution

        # Imprime el resultado
        if best_distribution:            
            # Utiliza la mejor distribución encontrada para generar la PDF
            if best_distribution.get_distribution_type_display() == "Normal":  # Normal distribution
                mean = best_distribution.mean_param
                std_dev = best_distribution.std_dev_param
                if std_dev is not None:
                    pdf = norm.pdf(data, loc=mean, scale=std_dev)
                    distribution_label = 'Distribución normal'
                    print("se encontro una distribucion normal")
                else:
                    pdf = np.zeros_like(data)
                    distribution_label = 'Distribución desconocida'
            elif best_distribution.get_distribution_type_display() == "Exponential":  # Exponential distribution
                lambda_param = best_distribution.lambda_param
                pdf = expon.pdf(data, scale=1 / lambda_param)
                distribution_label = 'Distribución exponencial'
                print("se encontro una distribucion exponencial")
            elif best_distribution.get_distribution_type_display() == "Log-Norm":  # Logarithmic distribution
                s = best_distribution.std_dev_param
                scale = np.exp(best_distribution.mean_param)
                pdf = lognorm.pdf(data, s=s, scale=scale)
                distribution_label = 'Distribución logarítmica'
                print("se encontro una distribucion logaritmica")
            else:
                pdf = None
        else:
            print('No se encontró una distribución adecuada.')
        
        image_data = plot_scatter_and_pdf(data, pdf, distribution_label)
        image_data_histogram = plot_histogram_and_pdf(data, pdf, distribution_label)
        print("Se selecciono el cuestionario " + str(selected_questionary_result_id))
        print("aqui se setea la variable selected_questionary_result_id " + str(selected_questionary_result_id))
        print("Started: " + str(started))
        print(areas)

        data_str = re.sub(r'<br\s*/?>', '\n', demand_history.answer)
        data_str = data_str.replace("[", "").replace("]", "").replace("'", "").replace(",", "")
        data_list = [float(value) for value in data_str.split()]     
        best_ks_p_value_floor = math.floor(best_ks_p_value * 100) / 100   
        best_best_ks_statistic_floor = math.floor(best_ks_statistic * 100) / 100
        context = {
            'areas': areas,
            'answers': answers,
            'image_data':image_data,
            'image_data_histogram':image_data_histogram,
            'selected_fdp': best_distribution.id,
            'demand_mean': demand_mean,
            'form': form,
            'demand_history': data_list,
            'equations_to_use': equations_to_use,
            'questionnaires_result': questionnaires_result,
            'questionary_result_instance_id': questionary_result_instance.id,
            'questionary_result_instance': questionary_result_instance,
            'selected_unit_time': selected_unit_time,
            'selected_quantity_time': selected_quantity_time,
            'best_distribution': best_distribution.get_distribution_type_display(),
            'best_ks_p_value': best_ks_p_value_floor,
            'best_ks_statistic': best_best_ks_statistic_floor,            
        }
        return render(request, 'simulate/simulate-init.html', context)
    
    if request.method == 'POST' and 'start' in request.POST:
        print("se comenzara la simulacion ")
        request.session['started'] = True 
        # Obtén los datos del formulario
        fk_questionary_result = request.POST.get('fk_questionary_result')
        quantity_time = request.POST.get('quantity_time')
        unit_time = request.POST.get('unit_time')
        demand_history = request.POST.get('demand_history')
        fk_fdp_id = request.POST.get('fk_fdp')
        fk_fdp_instance = get_object_or_404(ProbabilisticDensityFunction, id=fk_fdp_id)
        fk_questionary_result_instance = get_object_or_404(QuestionaryResult, id=fk_questionary_result)
        # Puedes realizar la lógica de validación aquí si es necesario

        # arreglar como se guarda demadn_history
        # Crea una nueva instancia de Simulation y almacena los datos
        simulation_instance = Simulation.objects.create(
            fk_questionary_result=fk_questionary_result_instance,
            quantity_time=quantity_time,
            unit_time=unit_time,
            demand_history=demand_history,
            fk_fdp=fk_fdp_instance,
            is_active=True
        )

        # Calcula la media de la demanda y crea una instancia de Demand
        cleaned_demand_history = demand_history.replace('[', '').replace(']', '').replace('\r\n', '').split()
        demand_history_list = [float(item) for item in cleaned_demand_history if item.isdigit()]
        demand_mean = statistics.mean(demand_history_list)
        product_instance = get_object_or_404(Product, pk=simulation_instance.fk_questionary_result.fk_questionary.fk_product.id)
        Demand.objects.create(
            quantity=demand_mean,
            fk_simulation=simulation_instance,
            fk_product=product_instance,
            is_predicted=False
        )

        # Almacena el ID de la simulación en la sesión
        request.session['simulation_started_id'] = simulation_instance.id

        # Redirige a la página deseada
        return redirect(reverse('simulate:simulate.show'))
    
    if request.method == 'POST' and 'cancel' in request.POST:
        request.session['selected'] = False 
        print("Se cancelo la simulacion")
        return redirect('simulate:simulate.show')
    
    if not started:
        try:
            if selected_questionary_result_id is None:
                questionnaires_result = QuestionaryResult.objects.filter(is_active=True, fk_questionary__fk_product__in=products ,fk_questionary__fk_product__fk_business__fk_user=request.user).order_by('-id')
            else:
                equations_to_use = Question.objects.order_by('id').filter(is_active=True, fk_questionary__fk_product__fk_business__fk_user=request.user, fk_questionary_id=selected_questionary_result_id)
                questionnaires_result = QuestionaryResult.objects.filter(is_active=True,fk_questionary__fk_product__in=products   ,fk_questionary__fk_product__fk_business__fk_user=request.user).order_by('-id')
                        
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
        except ObjectDoesNotExist:
            return HttpResponseNotFound("Object not found")
    else:
        print("La simulación ha comenzado")
        simulation_instance = get_object_or_404(Simulation, pk=request.session['simulation_started_id'])
        nmd = int(simulation_instance.quantity_time)
        endogenous_results = {}
        areas = Area.objects.filter(is_active=True, fk_product=simulation_instance.fk_questionary_result.fk_questionary.fk_product).order_by('id')
        for i in range(nmd):         
            product_instance = get_object_or_404(Product, pk=simulation_instance.fk_questionary_result.fk_questionary.fk_product.id)
            equations = Equation.objects.filter(is_active=True, fk_area__in=areas).order_by('fk_area_id')
            variables = Variable.objects.filter(is_active=True, fk_product=product_instance)
            questionary_result = simulation_instance.fk_questionary_result
            answers = Answer.objects.filter(fk_questionary_result=questionary_result)

            variable_initials_dict = {}
            demand_total = 0
            answer_dict = {str(answer.fk_question.id): answer for answer in answers}
            print("diccionario de respuestas " + str(answer_dict))
            for answer in answers:
                question_id = str(answer.fk_question.id)
                question = get_object_or_404(Question, pk=question_id)
                variable_name = f"{question.fk_variable.initials}"
                print(f"entra aca {variable_name}")

                if variable_name == "DH":
                    print(answer.answer)
                    if variable_name not in variable_initials_dict:
                        variable_initials_dict[variable_name] = []
                    try:
                        # Extract values between square brackets and convert to floats
                        values = [float(val) for val in answer.answer.strip('[]').split()]
                        answer_array = np.array(values)
                        print("answer_array")
                        print(answer_array)
                        variable_initials_dict[variable_name].extend(answer_array)
                    except Exception as e:
                        print(f"Error appending to {variable_name}: {e}")
                        continue
                else:
                    if answer.answer == "Sí":
                        variable_initials_dict[variable_name] = 1.0
                    elif answer.answer == "No":
                        variable_initials_dict[variable_name] = 0.5
                    else:
                        variable_initials_dict[variable_name] = float(answer.answer)

            print("diccionario de variables", variable_initials_dict)
            
            if "DH" in variable_initials_dict:
                demand_mean = round(np.mean(variable_initials_dict["DH"]), 2)
                print("media de la DH", demand_mean)
                variable_initials_dict["DH"] = demand_mean
            else:
                demand_mean = None
                print("DH: No demand mean available")
                
            if "NMD" in variable_initials_dict:
                variable_initials_dict["NMD"] = nmd
                        
            pending_equations = []  # List to store equations that are not ready to be solved
            for equation in equations:
                variables_to_use = [var.initials for var in [equation.fk_variable1, equation.fk_variable2, equation.fk_variable3, equation.fk_variable4, equation.fk_variable5] if var is not None]

                substituted_expression = equation.expression
                for var in variables_to_use:
                    if var in variable_initials_dict:
                        substituted_expression = substituted_expression.replace(var, str(variable_initials_dict.get(var)))

                lhs, rhs = substituted_expression.split('=')

                if rhs is not None:
                    rhs = rhs.replace('∑', '')  # Puedes considerar si realmente necesitas este reemplazo
                    try:
                        symbol = symbols(rhs.strip())
                        result = solve(Eq(sp.sympify(rhs.strip()), 0), symbol)

                        if result:
                            endogenous_results[variables_to_use[-1]] = result[0]
                        else:
                            pending_equations.append((lhs, rhs))
                    except Exception as e:
                        print(f"Error: Unable to solve equation {lhs}. Reason: {str(e)}")
                        pending_equations.append((lhs, rhs))

            print("ecuaciones pendientes " + str(pending_equations))          
            # pending_equations = process_pending_equations(pending_equations, variable_initials_dict, endogenous_results)
            
            demand_total = convert_to_float(demand_total)
            demand_history_numeric = convert_to_numeric_list(simulation_instance.demand_history)
            demand_std_dev = calculate_std_dev(demand_history_numeric + [demand_total])
            serializable_endogenous_results = serialize_endogenous_results(endogenous_results)
            solved_results = solve_endogenous_results(endogenous_results)
            print ("resultados solucionados " + str(solved_results))
            print("resultados endogenos " + str(serializable_endogenous_results))
            json_data = json.dumps(serializable_endogenous_results)
            new_result_simulation = create_result_simulation(simulation_instance, demand_total, demand_std_dev, i, json_data)
            new_result_simulation.save()
            print("dia de la simulacion " + str(i))

        request.session['started'] = False 
        return render(request, 'simulate/simulate-result.html', {
            'simulation_instance_id': simulation_instance,
        })              

def solve_endogenous_results(endogenous_results):
    solved_results = {}

    for key, expression in endogenous_results.items():
        coefficient, operator, term = expression
        symbol = sp.symbols(key)
        solved_value = None
        if operator == '+':
            solved_value = sp.solve(coefficient + symbol - term, symbol)
        elif operator == '-':
            solved_value = sp.solve(coefficient - symbol - term, symbol)
        elif operator == '*':
            solved_value = sp.solve(coefficient * symbol - term, symbol)
        elif operator == '/':
            solved_value = sp.solve(coefficient / symbol - term, symbol)
        else:
            # Handle other operators as needed
            pass

        if solved_value:
            solved_results[key] = solved_value[0]

    return solved_results

def process_pending_equations(pending_equations, variable_initials_dict, endogenous_results):
    while pending_equations:
        pending_equations = try_to_solve_pending_equations(pending_equations, variable_initials_dict, endogenous_results)
    return pending_equations

def convert_to_float(value):
    try:
        return float(value)
    except ValueError:
        return None

def convert_to_numeric_list(json_string):
    try:
        list_values = json.loads(json_string)
        return [convert_to_float(value) for value in list_values]
    except json.JSONDecodeError:
        return []

def calculate_std_dev(numeric_list):
    return np.std(numeric_list) if numeric_list else None

def serialize_endogenous_results(endogenous_results):
    return {k: float(v) if isinstance(v, np.float64) else v for k, v in endogenous_results.items()}

def create_result_simulation(simulation_instance, demand_total, demand_std_dev, i, serializable_endogenous_results):
    return ResultSimulation(
        fk_simulation=simulation_instance,
        demand_mean=demand_total,
        demand_std_deviation=demand_std_dev,
        date=simulation_instance.date_created + timedelta(days=i),
        variables=serializable_endogenous_results,
    )
def try_to_solve_pending_equations(pending_equations, variable_initials_dict, endogenous_results):
    new_pending_equations = []
    for lhs, rhs in pending_equations:
        lhs_symbols = sp.symbols(lhs.strip())

        # Verificar que cada símbolo en lhs_symbols esté en variable_initials_dict
        lhs_symbols = sp.symbols(lhs)
        if isinstance(lhs_symbols, sp.Symbol):
            lhs_symbols = [lhs_symbols]

        if all(var in variable_initials_dict or (isinstance(var, sp.Symbol) and var.is_number) for var in lhs_symbols):
            print("simbolo " + str(lhs_symbols))

            try:
                # Attempt to solve the equation
                result = sp.solve(sp.Eq(rhs, 0), lhs_symbols)
                print(f"Debug: lhs={lhs}, expresion_evaluated={rhs}, result={result}")

                if result:
                    # The equation has a solution
                    for symbol in lhs_symbols:
                        endogenous_results[variable_initials_dict[symbol]] = result[0]  # Use index 0 if there's only one solution
                else:
                    # The equation has no solution, add it to new_pending_equations
                    print(f"Info: Equation {lhs} has no solution.")
                    new_pending_equations.append((lhs, rhs))
            except Exception as e:
                print(f"Error: Unable to solve equation {lhs}. Reason: {str(e)}")
                new_pending_equations.append((lhs, rhs))
        else:
            # Some symbol in lhs_symbols is not in variable_initials_dict, add it to new_pending_equations
            print(f"Info: Equation {lhs} is waiting for complete data.")
            new_pending_equations.append((lhs, rhs))
    return new_pending_equations
  
# aqui se le manda el Simulate object que se creo en la vista de arriba
def simulate_result_simulation_view(request, simulation_id):
    results = get_results_for_simulation(simulation_id)
    results_simulation = ResultSimulation.objects.filter(is_active=True, fk_simulation_id=simulation_id)
    iniciales_a_buscar = ['CTR', 'CTAI', 'TPV', 'TPPRO', 'DI', 'VPC', 'IT', 'GT', 'TCA', 'NR', 'GO', 'GG', 'GT', 'CTTL', 'CPP', 'CPV', 'CPI', 'CPMO', 'CUP', 'PVR', 'TG', 'IB', 'MB', 'RI', 'RTI', 'RTC', 'PE', 'HO', 'CHO', 'CA']
    all_variables_extracted = []
    totales_acumulativos = {}    
    # Obtén todas las variables desde la base de datos
    variables_db = Variable.objects.all()
    # Crea un diccionario de mapeo entre iniciales y nombres completos de variables
    name_variables = {variable.initials: {'name': variable.name, 'unit': variable.unit} for variable in variables_db}
    for result_simulation in results_simulation:
        variables_extracted = result_simulation.get_variables()
        date_simulation = result_simulation.date
        # Filtrar variables que coinciden con las iniciales
        filtered_variables = Variable.objects.filter(initials__in=iniciales_a_buscar).values('name', 'initials')
        iniciales_a_nombres = {variable['initials']: variable['name'] for variable in filtered_variables}
        # en lugar de mostrar las iniciales compararlas con la base de datos de varaibles y mostrar el nombre de la variable
        # Calcular la suma total por variable
        totales_por_variable = {}
        for inicial, value in variables_extracted.items():
            if inicial in iniciales_a_nombres:
                name_variable = iniciales_a_nombres[inicial]
                if name_variable not in totales_por_variable:
                    totales_por_variable[name_variable] = {
                        'total': 0,
                        'unit': name_variables.get(inicial, {}).get('unit', None)
                    }
                totales_por_variable[name_variable]['total'] += value
                # Si `unit` está disponible en tus datos, asigna su valor a la clave 'unit'
                # de lo contrario, mantén el valor actual (o puedes manejarlo según tus necesidades)
                totales_por_variable[name_variable]['unit'] = name_variables.get(inicial, {}).get('unit', totales_por_variable[name_variable]['unit'])


        # Agregar las variables filtradas a la lista
        all_variables_extracted.append({'result_simulation': result_simulation, 'totales_por_variable': totales_por_variable, 'date_simulation': date_simulation})

        
    print(all_variables_extracted)
    variables_to_graph = []
    for result_simulation in results_simulation:
        variables_extracted = result_simulation.get_variables()
        filtered_variables = {
            name_variables[inicial]['name']: {
                'value': value, 
                'unit': name_variables[inicial]['unit']
                }
            for inicial, value in variables_extracted.items() if inicial in iniciales_a_buscar}
        variables_to_graph.append(filtered_variables)
        # Calcular la suma total por variable
        for name_variable, info_variable in filtered_variables.items():
            if name_variable not in totales_acumulativos:
                totales_acumulativos[name_variable] = {'total': 0, 'unit': info_variable['unit']}
            totales_acumulativos[name_variable]['total'] += info_variable['value']
    
    simulation_instance = get_object_or_404(Simulation, pk=simulation_id)
    questionary_result_instance = get_object_or_404(QuestionaryResult, pk=simulation_instance.fk_questionary_result.id)
    product_instance = get_object_or_404(Product, pk=questionary_result_instance.fk_questionary.fk_product.id)
    business_instance = get_object_or_404(Business, pk=product_instance.fk_business.id)
    areas = Area.objects.filter(is_active=True, fk_product=product_instance)

    result_simulations = ResultSimulation.objects.filter(is_active=True, 
                                                         fk_simulation_id=simulation_id)
    all_labels = []
    all_values = []
    for i, result_simulation in enumerate(result_simulations):
        data = result_simulation.get_average_demand_by_date()
        if data:
            for entry in data:
                all_labels.append(i + 1)
                all_values.append(entry['average_demand'])

    sorted_data = sorted(zip(all_labels, all_values), key=lambda x: x[0])
    if sorted_data:
        all_labels, all_values = zip(*sorted_data)
    else:
        all_labels = []
        all_values = []

    chart_data = {
        'labels': all_labels,
        'datasets': [
            {'label': 'Demanda Simulada', 'values': all_values},
        ],
        'x_label': 'Dias',
        'y_label': 'Demanda (Litros)',
    }
    image_data_line = None
    image_data_bar = None
    image_data_candlestick = None
    image_data_histogram = None
    image_data_0 = None
    image_data_1 = None
    image_data_2 = None
    image_data_3 = None
    image_data_4 = None
    image_data_5 = None
    image_data_6 = None
    image_data_7 = None
    image_data_8 = None
    if len(all_labels) == len(all_values):
        try:
            image_data_line = plot_and_save_chart(chart_data, 'linedemand', simulation_id, product_instance, result_simulations, 
                                                  'Grafico Lineal', 
                                                  'Este grafico muestra como es el comportamiento de la demanda en los dias de simulacion.')
            image_data_bar = plot_and_save_chart(chart_data, 'bar', simulation_id, product_instance, result_simulations,
                                                 'Gráfico de Barras' , 
                                                 'Este gráfico de dispersión muestra la relación entre diferentes variables para el producto.')
            image_data_candlestick = plot_and_save_chart(chart_data, 'scatter', simulation_id, product_instance, result_simulations, 
                                                         'Gráfico Lineal', 
                                                         'Este gráfico de dispersión muestra la relación entre diferentes variables para el producto.')
            image_data_histogram = plot_and_save_chart(chart_data, 'histogram', simulation_id, product_instance, result_simulations, 
                                                       'Gráfico Lineal', 
                                                       'Este gráfico de dispersión muestra la relación entre diferentes variables para el producto.')
        except Exception as e:
            print(f"Error generating chart or creating Chart object: {e}")
    else:
        print("Las listas tienen diferentes longitudes, no se puede trazar el gráfico correctamente.")
   
    results_dict = analyze_financial_results(
        simulation_id,
        totales_acumulativos,
        business_instance,
        simulation_instance
    )
    # print(filtered_variables)
    chart_data_cost_variables = {
        'labels': all_labels,
        'datasets': [
            {'label': 'Ingresos totales', 'values': get_variable_values('INGRESOS TOTALES', variables_to_graph)},
            {'label': 'Gastos Operativos', 'values': get_variable_values('GANANCIAS TOTALES', variables_to_graph)},
        ],
        'x_label': 'Dias',
        'y_label': 'Pesos Bolivianos',
    }
    chart_data_cost_variables_0 = {
        'labels': all_labels,
        'datasets': [
            {'label': 'Ventas por cliente', 'values': get_variable_values('VENTAS POR CLIENTE', variables_to_graph)},
            {'label': 'Demanda Insatisfecha', 'values': get_variable_values('DEMANDA INSATISFECHA', variables_to_graph)},
        ],
        'x_label': 'Dias',
        'y_label': 'Pesos Bolivianos',
    }
    chart_data_cost_variables_1 = {
        'labels': all_labels,
        'datasets': [
            {'label': 'Gastos Generales', 'values': get_variable_values('GASTOS GENERALES', variables_to_graph)},
            {'label': 'Gastos Operativos', 'values': get_variable_values('GASTOS OPERATIVOS', variables_to_graph)},
            {'label': 'Total Gastos', 'values': get_variable_values('Total Gastos', variables_to_graph)},
        ],
        'values': all_labels,
        'x_label': 'Dias',
        'y_label': 'Pesos Bolivianos',
    }
    chart_data_cost_variables_2 = {
        'labels': all_labels,
        'datasets': [
            {'label': 'Costo Unitario Producción', 'values': get_variable_values('Costo Unitario Producción', variables_to_graph)},
            {'label': 'Margen bruto', 'values': get_variable_values('Ingreso Bruto', variables_to_graph)},
        ],
        'x_label': 'Dias',
        'y_label': 'Pesos Bolivianos',
    }
    chart_data_cost_variables_3 = {
        'labels': all_labels,
        'datasets': [
            {'label': 'Rotación de clientes', 'values': get_variable_values('Ingreso Bruto', variables_to_graph)},
            {'label': 'Participación de mercado', 'values': get_variable_values('INGRESOS TOTALES', variables_to_graph)},
        ],
        'x_label': 'Dias',
        'y_label': 'Pesos Bolivianos',
    }
    chart_data_cost_variables_4 = {
        'labels': all_labels,
        'datasets': [
            {'label': 'Costo Total Transporte', 'values': get_variable_values('COSTO TOTAL TRANSPORTE', variables_to_graph)},
            {'label': 'Costo Total Empleados', 'values': get_variable_values('Costo Promedio Mano Obra', variables_to_graph)},
            {'label': 'Costo Total Almacenamiento', 'values': get_variable_values('Costo Almacenamiento', variables_to_graph)},
            {'label': 'Costo Total Insumos', 'values': get_variable_values('COSTO TOTAL ADQUISICIÓN INSUMOS', variables_to_graph)},
        ],
        'x_label': 'Dias',
        'y_label': 'Pesos Bolivianos',
    }
    chart_data_cost_variables_5 = {
        'labels': all_labels,
        'datasets': [
            {'label': 'Total productos producidos', 'values': get_variable_values('TOTAL PRODUCTOS PRODUCIDOS', variables_to_graph)},
            {'label': 'Total producto vendidos', 'values': get_variable_values('TOTAL PRODUCTOS VENDIDOS', variables_to_graph)},
        ],
        'x_label': 'Dias',
        'y_label': 'Pesos Bolivianos',
    }
    chart_data_cost_variables_6 = {
        'labels': all_labels,
        'datasets': [
            {'label': 'Costo promedio de producción', 'values': get_variable_values('COSTO PROMEDIO PRODUCCION', variables_to_graph)},
            {'label': 'Costo promedio de venta', 'values': get_variable_values('COSTO PROMEDIO VENTA', variables_to_graph)},
        ],
        'x_label': 'Dias',
        'y_label': 'Pesos Bolivianos',
    }
    chart_data_cost_variables_7 = {
        'labels': all_labels,
        'datasets': [
            {'label': 'Retorno de la inversión', 'values': get_variable_values('Retorno Inversión', variables_to_graph)},
            {'label': 'Ganancias Totales', 'values': get_variable_values('GANANCIAS TOTALES', variables_to_graph)},
        ],
        'x_label': 'Dias',
        'y_label': 'Pesos Bolivianos',
    }
    # print (chart_data_cost_variables)

    description_0 = 'Este gráfico de barras muestra la relación entre diferentes variables para el producto.'
    image_data_0 = plot_and_save_chart(chart_data_cost_variables, 'barApilate', simulation_id, product_instance, result_simulations, 'Grafico de Barras', description_0)
    image_data_1 = plot_and_save_chart(chart_data_cost_variables_0, 'bar', simulation_id, product_instance, result_simulations, 'Gráfico de Barras', 'Este gráfico de dispersión muestra la relación entre diferentes variables para el producto.')
    image_data_2 = plot_and_save_chart(chart_data_cost_variables_1, 'line', simulation_id, product_instance, result_simulations, 'Gráfico Lineal', 'Este gráfico de dispersión muestra la relación entre diferentes variables para el producto.')
    image_data_3 = plot_and_save_chart(chart_data_cost_variables_2, 'bar', simulation_id, product_instance, result_simulations, 'Gráfico de Barras', 'Este gráfico de dispersión muestra la relación entre diferentes variables para el producto.')
    image_data_4 = plot_and_save_chart(chart_data_cost_variables_3, 'line', simulation_id, product_instance, result_simulations, 'Gráfico Lineal', 'Este gráfico de dispersión muestra la relación entre diferentes variables para el producto.')
    image_data_5 = plot_and_save_chart(chart_data_cost_variables_4, 'line', simulation_id, product_instance, result_simulations, 'Gráfico de Barras', 'Este gráfico de dispersión muestra la relación entre diferentes variables para el producto.')
    image_data_6 = plot_and_save_chart(chart_data_cost_variables_5, 'line', simulation_id, product_instance, result_simulations, 'Gráfico Lineal', 'Este gráfico de dispersión muestra la relación entre diferentes variables para el producto.')
    image_data_7 = plot_and_save_chart(chart_data_cost_variables_6, 'line', simulation_id, product_instance, result_simulations, 'Gráfico Lineal', 'Este gráfico de dispersión muestra la relación entre diferentes variables para el producto.')
    image_data_8 = plot_and_save_chart(chart_data_cost_variables_7, 'line', simulation_id, product_instance, result_simulations, 'Gráfico Lineal', 'Este gráfico de dispersión muestra la relación entre diferentes variables para el producto.')
            
    context = {
        'image_data_0':image_data_0,
        'image_data_1':image_data_1,
        'image_data_2':image_data_2,
        'image_data_3':image_data_3,
        'image_data_4':image_data_4,
        'image_data_5':image_data_5,
        'image_data_6':image_data_6,
        'image_data_7':image_data_7,
        'image_data_8':image_data_8,
        'demand_initial':results_dict['demand_initial'],
        'demand_predicted':results_dict['demand_predicted'],
        'growth_rate':results_dict['growth_rate'],
        'error_permisible':results_dict['error_permisible'],
        'simulation_instance': simulation_instance,
        'results_simulation': results_simulation,
        'results': results,
        'financial_recommendations_to_show': results_dict['financial_recommendations_to_show'],
        'questionary_result_instance': questionary_result_instance,
        'product_instance': product_instance,
        'business_instance': business_instance,
        'areas': areas,
        'image_data_line': image_data_line,
        'image_data_bar': image_data_bar,
        'image_data_candlestick': image_data_candlestick,
        'image_data_histogram': image_data_histogram,
        'all_variables_extracted':all_variables_extracted,
        'totales_acumulativos': totales_acumulativos
    }
    return render(request, 'simulate/simulate-result.html',context)

def get_variable_values(variable_to_search, data_list):
    values_for_variable = []
    # print("data_list")
    # print(data_list)
    # Iterar sobre cada diccionario en la lista
    for data in data_list:
        # Verificar si la variable existe en el diccionario actual
        if variable_to_search in data:
            # Verificar si el valor es un diccionario
            if isinstance(data[variable_to_search], dict):
                # Obtener el valor y agregarlo a la lista
                value_for_variable = data[variable_to_search]['value']
                values_for_variable.append(value_for_variable)
            else:
                print(f"Error: {variable_to_search} is not a dictionary.")
    return values_for_variable

def analyze_financial_results(simulation_id, totales_acumulativos, business_instance, simulation_instance):
    # Calculate growth rate
    demand_initial = get_object_or_404(Demand, fk_simulation_id=simulation_id, is_predicted=False)
    demand_predicted = get_object_or_404(Demand, fk_simulation_id=simulation_id, is_predicted=True)
    growth_rate = abs(((demand_predicted.quantity / demand_initial.quantity) ** (1 / 1) - 1) * 100)
    growth_rate = round(growth_rate, 2)

    error_permisible = abs(((demand_initial.quantity - demand_predicted.quantity)/demand_initial.quantity)*100)

    # Fetch financial recommendations
    financial_recommendations = FinanceRecommendation.objects.filter(
        is_active=True,
        fk_business=business_instance
    )
    financial_recommendations_to_show = []

    # Analyze results and compare with thresholds or criteria
    for recommendation_instance in financial_recommendations:
        name = recommendation_instance.name
        variable_name = recommendation_instance.variable_name
        threshold_value = recommendation_instance.threshold_value

        # Check if variable_name exists in totales_acumulativos
        if variable_name in totales_acumulativos:
            variable_value = totales_acumulativos[variable_name]['total']  # Get the numeric value

            # Check if threshold_value is not None and compare with variable_value
            if threshold_value is not None and variable_value is not None:
                if variable_value > threshold_value:
                    # The variable exceeds the threshold, show recommendation
                    recommendation_data = {
                        'name': name,
                        'recommendation': recommendation_instance.recommendation,
                        'variable_name': variable_name
                    }
                    financial_recommendations_to_show.append(recommendation_data)
                    finance_recommendation_instance = recommendation_instance
                    finance_recommendation_simulation = FinanceRecommendationSimulation.objects.create(
                        data=variable_value,
                        fk_simulation=simulation_instance,
                        fk_finance_recommendation=finance_recommendation_instance,
                    )
                    finance_recommendation_simulation.save()
        else:
            print(f"Variable name {variable_name} not found in totales_acumulativos.")

    # Return the results as a dictionary
    results_dict = {
        'demand_initial': demand_initial,
        'demand_predicted': demand_predicted,
        'growth_rate': growth_rate,
        'financial_recommendations_to_show': financial_recommendations_to_show,
        'error_permisible':error_permisible,
    }
    return results_dict

def save_plot_as_base64():
    with BytesIO() as buffer:
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

def plot_and_save_chart(chart_data, chart_type, simulation_id, product_instance, result_simulations, title, description):
    plt.figure(figsize=(10, 6))

    if chart_type == 'linedemand':
        labels = chart_data['labels']
        values = chart_data['datasets'][0]['values']
        label = chart_data['datasets'][0]['label']

        # Calcular la línea de regresión
        reg_line = np.polyfit(labels, values, 1)
        regression_values = np.polyval(reg_line, labels)

        # Plotear la línea de regresión
        plt.plot(labels, regression_values, label=f'{label} Regression Line', linestyle='--')

        # Plotear la línea de demanda simulada
        sns.lineplot(x=labels, y=values, marker='o', label='Demanda Simulada', palette='viridis')

        plt.grid(True)

        # Calcular y plotear la línea de tendencia
        coefficients = np.polyfit(labels, values, 1)
        polynomial = np.poly1d(coefficients)
        trendline_values = polynomial(labels)
        plt.plot(labels, trendline_values, label=f'Línea de tendencia: {coefficients[0]:.2f}x + {coefficients[1]:.2f}', linestyle='--')

        # Rellenar el área entre la línea de demanda y la línea de tendencia
        plt.fill_between(labels, values, trendline_values, color='skyblue', alpha=0.3)

    elif chart_type == 'line':
        labels = chart_data['labels']
        datasets = chart_data['datasets']
        custom_palette = sns.color_palette("husl", len(datasets))

        for i, dataset in enumerate(datasets):
            plt.plot(labels, dataset['values'], label=dataset['label'], color=custom_palette[i], linewidth=2)
            plt.fill_between(labels, dataset['values'], alpha=0.3, color=custom_palette[i])
        
        plt.grid(True)
    elif chart_type == 'bar':
        num_colors = len(chart_data['datasets'])
        color_palette = generate_random_color_palette(num_colors)

        for i, variable_data in enumerate(chart_data['datasets']):
            label = variable_data.get('label', f'Default Label {i+1}')
            values = variable_data['values']
            color = color_palette[i]
            sns.barplot(x=chart_data['labels'], y=values, label=label, color=color, alpha=0.7)

        plt.grid(True)
        plt.legend(loc='upper right')
        plt.show()
    elif chart_type == 'barh':
        for i, variable_data in enumerate(chart_data['datasets']):
            label = variable_data.get('label', f'Default Label {i+1}')
            values = variable_data['values']
            color = sns.color_palette('Set3', len(chart_data['labels']))[i]
            sns.barplot(x=chart_data['labels'], y=values, label=label, color=color, alpha=0.7)

    elif chart_type == 'scatter':
        for i, variable_data in enumerate(chart_data['datasets']):
            label = variable_data['label']
            values = variable_data['values']
            color = sns.color_palette('Set3', len(chart_data['labels']))[i]

            sns.scatterplot(x=chart_data['labels'], y=values, label=label, color=color, marker='o')

            # Puedes agregar líneas de regresión si es necesario
            reg_line = np.polyfit(chart_data['labels'], values, 1)
            plt.plot(chart_data['labels'], np.polyval(reg_line, chart_data['labels']), label=f'{label} Regression Line', linestyle='--')

    elif chart_type == 'histogram':
        for i, variable_data in enumerate(chart_data['datasets']):
            values = variable_data['values']
            color = sns.color_palette('Set3', len(chart_data['labels']))[i]

            sns.histplot(values, bins=20, color=color, alpha=0.7, kde=True)

            mean_value = np.mean(values)
            plt.axvline(x=mean_value, color='red', linestyle='--', label=f'Mean: {mean_value:.2f}')
            stats_text = f'Mean: {mean_value:.2f}\nStd Dev: {np.std(values):.2f}'
            plt.text(0.05, 0.95, stats_text, transform=plt.gca().transAxes, fontsize=8, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        title = f'Gráfico de barras horizontales del producto {product_instance.name}'
        description = f'Este gráfico de barras muestra la distribución para {chart_type} del producto.'
    elif chart_type == 'pie':       
        for i, variable_data in enumerate(chart_data['datasets']):
            labels = variable_data.get('labels', [])
            values = variable_data['values']
            explode = [0.1] * len(labels)  # Define el desplazamiento de las porciones del gráfico
            colors = sns.color_palette('Set3', len(labels))  # Define los colores de las porciones del gráfico
            plt.pie(values, labels=labels, explode=explode, colors=colors, autopct='%1.1f%%')
        title = f'Gráfico de barras horizontales del producto {product_instance.name}'
        description = f'Este gráfico de barras muestra la distribución para {chart_type} del producto.'
    elif chart_type == 'boxplot':
        for i, variable_data in enumerate(chart_data['datasets']):
            values = variable_data['values']
            sns.boxplot(data=values, palette='Set3', label=variable_data['label'])
        title = f'Gráfico de barras horizontales del producto {product_instance.name}'
        description = f'Este gráfico de barras muestra la distribución para {chart_type} del producto.'
    elif chart_type == 'barApilate':
        num_groups = len(chart_data['labels'])
        num_datasets = len(chart_data['datasets'])
        bar_width = 0.35
        x = np.arange(num_groups)

        bottom = np.zeros(num_groups)  # Variable para rastrear el punto de partida de cada barra

        for i, dataset in enumerate(chart_data['datasets']):
            values = dataset['values']
            label = dataset['label']
            color = sns.color_palette('Set1')[i]

            plt.bar(x, values, label=label, color=color, alpha=0.7, bottom=bottom)

            bottom += values
    elif chart_type == 'scatter3D':
        x = chart_data['x']
        y = chart_data['y']
        z = chart_data['z']

        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        for i, dataset in enumerate(chart_data['datasets']):
            label = dataset['label']
            values_x = dataset['x']
            values_y = dataset['y']
            values_z = dataset['z']
            color = sns.color_palette('Set3')[i]

            ax.scatter3D(values_x, values_y, values_z, label=label, c=color)

        ax.set_xlabel(chart_data['x_label'])
        ax.set_ylabel(chart_data['y_label'])
        ax.set_zlabel(chart_data['z_label'])
        ax.legend()
    else:
        plt.close()
        return None
    
    plt.subplots_adjust(bottom=0.2)
    plt.xticks(chart_data['labels'], rotation=90, ha='center')
    plt.xlabel(chart_data['x_label'])
    plt.ylabel(chart_data['y_label'])
    plt.legend()
    variable_names = [dataset['label'] for dataset in chart_data['datasets']]
    title += f' ({", ".join(variable_names)})'
    plt.title(title)
    plt.figtext(0.5, 0.01, description, ha='center', va='center')
    image_data = save_plot_as_base64()
    chart = Chart.objects.filter(fk_product_id=product_instance, chart_type=chart_type).first()
    if chart:
        chart.title = title
        chart.chart_data = chart_data
    else:
        chart = Chart.objects.create(
            title=title,
            chart_type=chart_type,
            chart_data=chart_data,
            fk_product=result_simulations[0].fk_simulation.fk_questionary_result.fk_questionary.fk_product,
        )
    chart.save_chart_image(image_data)
    chart.save()
    plt.tight_layout()
    plt.close()

    return image_data

def generate_random_color_palette(num_colors):
    return sns.color_palette("husl", num_colors)
import random
def simulate_add_view(request):
    if request.method == 'POST':
        fk_questionary_result = request.POST.get('fk_questionary_result')
        quantity_time = request.POST.get('quantity_time')
        unit_time = request.POST.get('unit_time')
        demand_history = request.POST.get('demand_history')
        fk_fdp_id = request.POST.get('fk_fdp')
        # print(demand_history)
        fk_fdp_instance = get_object_or_404(ProbabilisticDensityFunction, id=fk_fdp_id)
        fk_questionary_result_instance = get_object_or_404(QuestionaryResult, id=fk_questionary_result)
        # Convert demand_history to list of floats
        # demand_history = [float(x) for x in demand_history.split(',')]
        
        cleaned_demand_history = demand_history.replace('[', '').replace(']', '').replace('\r\n', '').split(',')
        demand_history_list = [float(item) for item in cleaned_demand_history if item.strip()]

        if demand_history_list:
            demand_mean = statistics.mean(demand_history_list)
            print(f"La media de demand_history es: {demand_mean}")
        else:
            print("La lista de demand_history está vacía.")
        
        simulation_instance = Simulation.objects.create(
            fk_questionary_result=fk_questionary_result_instance,
            quantity_time=quantity_time,
            unit_time=unit_time,
            demand_history=demand_history,
            fk_fdp=fk_fdp_instance,
            is_active=True
        )
        product_instance = get_object_or_404(Product, pk=simulation_instance.fk_questionary_result.fk_questionary.fk_product.id)
        simulation_instance.save()
        Demand.objects.create(
            quantity=demand_mean,
            fk_simulation=simulation_instance,
            fk_product=product_instance,
            is_predicted=False
        )
        simulation_id=simulation_instance.id
        create_random_result_simulations(simulation_instance, created=True)
        simulate_result_simulation_view(request, simulation_id)
        return HttpResponseRedirect(reverse('simulate:simulate.result', args=(simulation_instance.id,)))
        # return render(request, 'simulate/simulate-init.html')
    else:
        # Render the form page
        return render(request, 'simulate/simulate-init.html')

def create_random_result_simulations(instance, created, **kwargs):
    # Obtén la fecha inicial de la instancia de Simulation
    current_date = instance.date_created
    fk_simulation_instance = instance
    result_simulation = None
    print(f'Number of Result Simulation instances to be created by the Simulate: {instance.quantity_time}')
    # por que se esta creando 4 veces ResultSimulation por Simulation
    for _ in range(int(instance.quantity_time)):
        initial_demand = json.loads(instance.demand_history)
        media_demand = sum(initial_demand) / len(initial_demand) if initial_demand else 0
        demand_mean_historical = np.mean(initial_demand)
        demand_std_deviation_historical = np.std(initial_demand)
        demand_std_deviation = random.normalvariate(demand_std_deviation_historical, 20)
        demand = [random.normalvariate(demand_mean_historical, demand_std_deviation) for _ in range(10)]
        
        variables = {
            "CTR": [max(0, random.normalvariate(1000, 5000)) for _ in range(10)],
            "CTAI": [max(0, random.normalvariate(5000, 20000)) for _ in range(10)],
            "TPV": [max(0, random.normalvariate(1000, 5000)) for _ in range(10)],
            "TPPRO": [max(0, random.normalvariate(800, 4000)) for _ in range(10)],
            "DI": [max(0, random.normalvariate(50, 200)) for _ in range(10)],
            "VPC": [max(0, random.normalvariate(500, 1500)) for _ in range(10)],
            "IT": [max(0, random.normalvariate(5000, 20000)) for _ in range(10)],
            "GT": [max(0, random.normalvariate(3000, 12000)) for _ in range(10)],
            "TCA": [max(0, random.normalvariate(500, 2000)) for _ in range(10)],
            "NR": [max(0, random.normalvariate(0.1, 0.5)) for _ in range(10)],
            "GO": [max(0, random.normalvariate(1000, 5000)) for _ in range(10)],
            "GG": [max(0, random.normalvariate(1000, 5000)) for _ in range(10)],
            "GT": [max(0, random.normalvariate(2000, 8000)) for _ in range(10)],
            "CTTL": [max(0, random.normalvariate(1000, 5000)) for _ in range(10)],
            "CPP": [max(0, random.normalvariate(500, 2000)) for _ in range(10)],
            "CPV": [max(0, random.normalvariate(500, 2000)) for _ in range(10)],
            "CPI": [max(0, random.normalvariate(500, 2000)) for _ in range(10)],
            "CPMO": [max(0, random.normalvariate(500, 2000)) for _ in range(10)],
            "CUP": [max(0, random.normalvariate(500, 2000)) for _ in range(10)],
            "FU": [max(0, random.normalvariate(0.1, 0.5)) for _ in range(10)],
            "TG": [max(0, random.normalvariate(2000, 8000)) for _ in range(10)],
            "IB": [max(0, random.normalvariate(3000, 12000)) for _ in range(10)],
            "MB": [max(0, random.normalvariate(2000, 8000)) for _ in range(10)],
            "RI": [max(0, random.normalvariate(1000, 5000)) for _ in range(10)],
            "RTI": [max(0, random.normalvariate(1000, 5000)) for _ in range(10)],
            "RTC": [max(0, random.normalvariate(0.1, 0.5)) for _ in range(10)],
            "PM": [max(0, random.normalvariate(500, 1500)) for _ in range(10)],
            "PE": [max(0, random.normalvariate(1000, 5000)) for _ in range(10)],
            "HO": [max(0, random.normalvariate(10, 50)) for _ in range(10)],
            "CHO": [max(0, random.normalvariate(1000, 5000)) for _ in range(10)],
            "CA": [max(0, random.normalvariate(1000, 5000)) for _ in range(10)],
        }
        demand_mean = np.mean(demand)
        means = {variable: np.mean(values) for variable, values in variables.items()}
        current_date += timedelta(days=1)
        
        # demand_std_deviation_historical = np.std(initial_demand)
        # demand_std_deviation_random = np.std(demand)
        # std_deviation_difference = np.sqrt((demand_std_deviation_historical**2 + demand_std_deviation_random**2) / 2)
        # desviacion_std = np.std(std_deviation_difference)
        
        demand_std_deviation = random.normalvariate(5, 20)
        result_simulation = ResultSimulation(
            demand_mean=demand_mean,
            demand_std_deviation=demand_std_deviation,
            date=current_date,
            variables=means,
            fk_simulation=fk_simulation_instance,
            is_active=True
        )
        result_simulation.save()
        # aqui acaba el for 
    # Verifica si ya existe una instancia de demand_instance
    demand_instance = None
    demand_predicted_instance = None

    if not Demand.objects.filter(fk_simulation=fk_simulation_instance, is_predicted=False).exists():
        demand_instance = Demand(
            quantity=fk_simulation_instance.demand_history[0],
            is_predicted=False,
            fk_simulation=fk_simulation_instance,
            fk_product=fk_simulation_instance.fk_questionary_result.fk_questionary.fk_product,
            is_active=True
        )
        demand_instance.save()

    # Verifica si ya existe una instancia de demand_predicted_instance
    if not Demand.objects.filter(fk_simulation=fk_simulation_instance, is_predicted=True).exists():
        demand_predicted_instance = Demand(
            quantity=demand_mean,
            is_predicted=True,
            fk_simulation=fk_simulation_instance,
            fk_product=fk_simulation_instance.fk_questionary_result.fk_questionary.fk_product,
            is_active=True
        )
        demand_predicted_instance.save()

    # Verifica si tanto demand_instance como demand_predicted_instance tienen valores antes de crear DemandBehavior
    if demand_instance is not None and demand_predicted_instance is not None:
        # Verifica si ya existe una instancia de demand_behavior
        if not DemandBehavior.objects.filter(current_demand=demand_instance, predicted_demand=demand_predicted_instance).exists():
            demand_behavior = DemandBehavior(
                current_demand=demand_instance,
                predicted_demand=demand_predicted_instance,
                is_active=True
            )
            demand_behavior.save()
            