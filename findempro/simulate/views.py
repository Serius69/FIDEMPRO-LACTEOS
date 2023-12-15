# Standard library imports
from datetime import datetime, timedelta
from http.client import HTTPResponse
from io import BytesIO
import base64
import json
import re
import os
import pkg_resources
import statistics
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

# Set matplotlib to non-interactive mode to avoid error in web environments
matplotlib.use('Agg')

# Set OpenAI API key
openai.api_key = settings.OPENAI_API_KEY
class AppsView(LoginRequiredMixin, TemplateView):
    pass

def plot_histogram_and_pdf(data, pdf, distribution_label):
    fig, ax = plt.subplots()

    # Histograma
    ax.hist(data, bins=20, density=True, alpha=0.5, label='Demanda Historica')

    # Plot de la Función de Densidad de Probabilidad (FDP)
    if pdf is not None:
        ax.plot(data, pdf, label=f'Función de densidad de probabilidad ({distribution_label})')

    # Configuración del gráfico
    ax.legend()
    ax.set_xlabel('Valor')
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
            print(f'Mejor ajuste: {best_distribution.get_distribution_type_display()}')
            print(f'KS Statistic: {best_ks_statistic}')
            print(f'KS P-Value: {best_ks_p_value}')
            
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
        
        image_data = plot_histogram_and_pdf(data, pdf, distribution_label)
        print("Se selecciono el cuestionario " + str(selected_questionary_result_id))
        print("aqui se setea la variable selected_questionary_result_id " + str(selected_questionary_result_id))
        print("Started: " + str(started))
        print(areas)
        # este era el error de que no se guardaba el cuestionario seleccionado
        # request.session['selected_fdp'] = best_distribution
        # Convierte el array de números a una lista de enteros
        numbers_list = numbers.tolist()

        # Convierte la lista de enteros a formato JSON
        json_numbers_data = json.dumps(numbers_list)
        context = {
            'areas': areas,
            'answers': answers,
            'image_data':image_data,
            'selected_fdp': best_distribution.id,
            'demand_mean': demand_mean,
            'form': form,
            # 'demand_history': demand_history.answer,
            'demand_history': json_numbers_data,
            'equations_to_use': equations_to_use,
            'questionnaires_result': questionnaires_result,
            'questionary_result_instance_id': questionary_result_instance.id,
            'questionary_result_instance': questionary_result_instance,
            'selected_unit_time': selected_unit_time,
            'selected_quantity_time': selected_quantity_time,
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
    # analysis_results = analyze_simulation_results(results)
    # decision = decision_support(analysis_results)
    results_simulation = ResultSimulation.objects.filter(is_active=True, fk_simulation_id=simulation_id)
    iniciales_a_buscar = ['CTR', 'CTAI', 'TPV', 'TPPRO', 'DI', 'VPC', 'IT', 'GT', 'TCA', 'NR', 'GO', 'GG', 'GT', 'CTTL', 'CPP', 'CPV', 'CPI', 'CPMO', 'CUP', 'PVR', 'FU', 'TG', 'IB', 'MB', 'RI', 'RTI', 'RTC', 'PM', 'PE', 'HO', 'CHO', 'CA']
    # Crear una lista para almacenar todas las variables extraídas
    all_variables_extracted = []

    for result_simulation in results_simulation:
        variables_extracted = result_simulation.get_variables()

        # Filtrar variables que coinciden con las iniciales
        variables_filtradas = Variable.objects.filter(initials__in=iniciales_a_buscar).values('name', 'initials')
        iniciales_a_nombres = {variable['initials']: variable['name'] for variable in variables_filtradas}
        # en lugar de mostrar las iniciales compararlas con la base de datos de varaibles y mostrar el nombre de la variable
        # Calcular la suma total por variable
        totales_por_variable = {}
        for inicial, value in variables_extracted.items():
            if inicial in iniciales_a_nombres:
                nombre_variable = iniciales_a_nombres[inicial]
                if nombre_variable not in totales_por_variable:
                    totales_por_variable[nombre_variable] = 0
                totales_por_variable[nombre_variable] += value

        # Agregar las variables filtradas a la lista
        all_variables_extracted.append({'result_simulation': result_simulation, 'totales_por_variable': totales_por_variable})
    
    # Crear un objeto Paginator
    paginator_all_variables_extracted = Paginator(all_variables_extracted, 1)
    # Obtener el número de página desde la solicitud GET
    page_all_variables_extracte = request.GET.get('page')
    try:
        # Obtener la página solicitada
        all_variables_extracted = paginator_all_variables_extracted.page(page_all_variables_extracte)
    except PageNotAnInteger:
        # Si la página no es un número entero, mostrar la primera página
        all_variables_extracted = paginator_all_variables_extracted.page(1)
    except EmptyPage:
        # Si la página está fuera de rango (por ejemplo, 9999), mostrar la última página
        all_variables_extracted = paginator_all_variables_extracted.page(paginator_all_variables_extracted.num_pages)
        
    totales_acumulativos = {}    
    # Obtén todas las variables desde la base de datos
    variables_db = Variable.objects.all()
    # Crea un diccionario de mapeo entre iniciales y nombres completos de variables
    nombre_variables = {variable.initials: {'name': variable.name, 'unit': variable.unit} for variable in variables_db}
    for result_simulation in results_simulation:
        variables_extracted = result_simulation.get_variables()

        # Filtrar variables que coinciden con las iniciales
        variables_filtradas = {nombre_variables[inicial]['name']: {'value': value, 'unit': nombre_variables[inicial]['unit']} for inicial, value in variables_extracted.items() if inicial in iniciales_a_buscar}

        # Calcular la suma total por variable
        for nombre_variable, info_variable in variables_filtradas.items():
            if nombre_variable not in totales_acumulativos:
                totales_acumulativos[nombre_variable] = {'total': 0, 'unit': info_variable['unit']}
            totales_acumulativos[nombre_variable]['total'] += info_variable['value']
    
    
    print(totales_acumulativos )
    
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
        'values': all_values,
        'x_label': 'Resultado',
        'y_label': 'Demanda',
    }
    image_data = None
    if len(all_labels) == len(all_values):
        try:
            # Crear una nueva figura antes de cada gráfico
            plt.figure()

            plt.plot(chart_data['labels'], chart_data['values'], marker='o', label='Demanda')
            for value in all_values:
                plt.axhline(y=value, linestyle='--', color='gray', alpha=0.5)

            for label in all_labels:
                plt.axvline(x=label, linestyle='--', color='gray', alpha=0.5)

            coefficients = np.polyfit(chart_data['labels'], chart_data['values'], 1)
            polynomial = np.poly1d(coefficients)
            trendline_values = polynomial(chart_data['labels'])
            plt.plot(chart_data['labels'], trendline_values, label=f'Línea de tendencia: {coefficients[0]:.2f}x + {coefficients[1]:.2f}', linestyle='--')

            plt.legend()
            plt.xlabel(chart_data['x_label'])
            plt.ylabel(chart_data['y_label'])
            plt.title(f'Comportamiento de la demanda promedio para la simulación {simulation_id}')

            with BytesIO() as buffer:
                plt.savefig(buffer, format='png')
                buffer.seek(0)
                image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

            # Check if a Chart object for this simulation already exists
            chart = Chart.objects.filter(fk_simulation_id=simulation_id).first()
            if chart:
                # Update the existing Chart object
                chart.title = f'Comportamiento de la demanda promedio para la simulación {simulation_id}'
                chart.chart_type = 'line'
                chart.chart_data = chart_data
            else:
                # Create a new Chart object
                chart = Chart.objects.create(
                    title=f'Comportamiento de la demanda promedio para la simulación {simulation_id}',
                    chart_type='line',
                    chart_data=chart_data,
                    fk_product=result_simulations[0].fk_simulation.fk_questionary_result.fk_questionary.fk_product,
                )

            chart.save_chart_image()
            chart.save()
            plt.close()

        except Exception as e:
            print(f"Error generating chart or creating Chart object: {e}")
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
    
    demand_initial = get_object_or_404(Demand, fk_simulation_id=simulation_id, is_predicted=False)
    demand_predicted = get_object_or_404(Demand, fk_simulation_id=simulation_id, is_predicted=
                                         True)
    growth_rate = ((demand_predicted.quantity / demand_initial.quantity) ** (1 / 1) - 1) * 100
    growth_rate = round(growth_rate, 2)
    

    financial_recommendations = FinanceRecommendation.objects.filter(
        is_active=True,
        fk_business=business_instance
    )
    financial_recommendations_to_show = []
    # Analizar resultados y comparar con umbrales o criterios
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
    
    paginator2 = Paginator(financial_recommendations_to_show, 10)  # Show 10 results per page.
    page_number2 = request.GET.get('page')
    page_obj2 = paginator2.get_page(page_number2)
    counter_start = (page_obj.number - 1) * paginator.per_page + 1
    
    # return render(request, 'your_template.html', {'page_obj': page_obj})
    context = {
        'demand_initial':demand_initial,
        'demand_predicted':demand_predicted,
        'growth_rate':growth_rate,
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
        'financial_recommendations_to_show':financial_recommendations_to_show,
        'all_variables_extracted':all_variables_extracted,
        'totales_acumulativos': totales_acumulativos
    }

    return render(request, 'simulate/simulate-result.html',context)

import random
# from pages.views import create_and_save_simulation,create_random_result_simulations
def simulate_add_view(request):
    if request.method == 'POST':
        fk_questionary_result = request.POST.get('fk_questionary_result')
        quantity_time = request.POST.get('quantity_time')
        unit_time = request.POST.get('unit_time')
        demand_history = request.POST.get('demand_history')
        fk_fdp_id = request.POST.get('fk_fdp')
        print(demand_history)
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
        # demand = [media_demand] + [random.normalvariate(100, 500) for _ in range(10)]
        demand = [random.normalvariate(media_demand, 3000) for _ in range(10)]
        demand_mean = np.mean(demand)
        demand_std_deviation = np.std(demand)
        
        variables = {
            "CTR": [random.normalvariate(1000, 5000) for _ in range(10)],
            "CTAI": [random.normalvariate(5000, 20000) for _ in range(10)],
            "TPV": [random.normalvariate(1000, 5000) for _ in range(10)],
            "TPPRO": [random.normalvariate(800, 4000) for _ in range(10)],
            "DI": [random.normalvariate(50, 200) for _ in range(10)],
            "VPC": [random.normalvariate(500, 1500) for _ in range(10)],
            "IT": [random.normalvariate(5000, 20000) for _ in range(10)],
            "GT": [random.normalvariate(3000, 12000) for _ in range(10)],
            "TCA": [random.normalvariate(500, 2000) for _ in range(10)],
            "NR": [random.normalvariate(0.1, 0.5) for _ in range(10)],
            "GO": [random.normalvariate(1000, 5000) for _ in range(10)],
            "GG": [random.normalvariate(1000, 5000) for _ in range(10)],
            "GT": [random.normalvariate(2000, 8000) for _ in range(10)],
            "CTTL": [random.normalvariate(1000, 5000) for _ in range(10)],
            "CPP": [random.normalvariate(500, 2000) for _ in range(10)],
            "CPV": [random.normalvariate(500, 2000) for _ in range(10)],
            "CPI": [random.normalvariate(500, 2000) for _ in range(10)],
            "CPMO": [random.normalvariate(500, 2000) for _ in range(10)],
            "CUP": [random.normalvariate(500, 2000) for _ in range(10)],
            "FU": [random.normalvariate(0.1, 0.5) for _ in range(10)],
            "TG": [random.normalvariate(2000, 8000) for _ in range(10)],
            "IB": [random.normalvariate(3000, 12000) for _ in range(10)],
            "MB": [random.normalvariate(2000, 8000) for _ in range(10)],
            "RI": [random.normalvariate(1000, 5000) for _ in range(10)],
            "RTI": [random.normalvariate(1000, 5000) for _ in range(10)],
            "RTC": [random.normalvariate(0.1, 0.5) for _ in range(10)],
            "PM": [random.normalvariate(500, 1500) for _ in range(10)],
            "PE": [random.normalvariate(1000, 5000) for _ in range(10)],
            "HO": [random.normalvariate(10, 50) for _ in range(10)],
            "CHO": [random.normalvariate(1000, 5000) for _ in range(10)],
            "CA": [random.normalvariate(1000, 5000) for _ in range(10)],
        }
        demand_mean = np.mean(demand)
        means = {variable: np.mean(values) for variable, values in variables.items()}
        current_date += timedelta(days=1)
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
            