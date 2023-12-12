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
from sympy import Eq, sympify, solve, symbols,Sum,sp
from scipy.stats import gaussian_kde
# Third-party imports
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.http import JsonResponse
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
        demand_history = get_object_or_404(
            Answer, 
            fk_question__question='Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).',
            fk_questionary_result_id=selected_questionary_result_id
            )
        print(demand_history.answer)   
        # solo para prober
        numbers = np.round(np.random.normal(loc=2500.0, scale=10.0, size=30)).astype(int)
        
        # Ajuste inicial de la FDP a los datos históricos
        
        # numbers = json.loads(demand_history.answer)
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
            elif best_distribution.get_distribution_type_display() == "Log-NOrm":  # Logarithmic distribution
                s = best_distribution.std_dev_param
                scale = np.exp(best_distribution.mean_param)
                pdf = lognorm.pdf(data, s=s, scale=scale)
                distribution_label = 'Distribución logarítmica'
                print("se encontro una distribucion logaritmica")
            else:
                pdf = None
        else:
            print('No se encontró una distribución adecuada.')
        
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
        if selected_questionary_result_id == None:
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
    else:
        # aqui ya tomar los datos de la simulacion que se creo en start
        simulation_instance = get_object_or_404(Simulation, pk=request.session['simulation_started_id'])
        nmd = int(simulation_instance.quantity_time)
        # Iterar sobre cada día de la simulación
        endogenous_results = {}
        for i in range(nmd):         
            areas = Area.objects.filter(is_active=True, fk_product=simulation_instance.fk_questionary_result.fk_questionary.fk_product)
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

            # Calculate the mean for "DH"
            if "DH" in variable_initials_dict:
                demand_mean = round(np.mean(variable_initials_dict["DH"]), 2)
                print("media de la DH", demand_mean)
                variable_initials_dict["DH"] = demand_mean
            else:
                demand_mean = None
                print("DH: No demand mean available")
            
            
            pending_equations = []  # List to store equations that are not ready to be solved

            for equation in equations:
                print("ecuacion " + str(equation.expression))
                variables_to_use = []

                for var in [equation.fk_variable1, equation.fk_variable2, equation.fk_variable3, equation.fk_variable4, equation.fk_variable5]:
                    if var is not None:
                        variables_to_use.append(var.initials)

                substituted_expression = equation.expression
                for var in variables_to_use:
                    if var in variable_initials_dict:
                        substituted_expression = substituted_expression.replace(var, str(variable_initials_dict.get(var)))

                lhs, rhs = substituted_expression.split('=')
                print("ecuacion armada " + str(lhs.strip() + "=" + rhs.strip()))  # print()

                if rhs is not None:
                    # Replace '∑' with 'Sum'
                    if '∑' in rhs:
                        # Replace '∑' with the Sum function and adjust the syntax
                        # rhs = rhs.replace('∑', 'Sum(') + ')'
                        rhs = rhs.replace('∑', '')
                    expresion_evaluated = sp.sympify(rhs.strip())
                else:
                    # Handle the case where rhs is None
                    expresion_evaluated = None  # Adjust based on your requirements
                    continue

                if expresion_evaluated is not None:
                    symbol = sp.symbols(lhs.strip())

                    # Check if all symbols in the expression are defined
                    if all(var in variable_initials_dict for var in sp.symbols(lhs)):
                        try:
                            # Try to solve the equation
                            result = sp.solve(sp.Eq(expresion_evaluated, 0), symbol)
                            print(f"Debug: lhs={lhs}, expresion_evaluated={expresion_evaluated}, result={result}")

                            if result:
                                # Equation has a solution
                                endogenous_results[variables_to_use[-1]] = result[0]
                            else:
                                # Equation has no solution, add it to pending equations
                                print(f"Info: Equation {lhs} has no solution.")
                                pending_equations.append((lhs, rhs))
                        except Exception as e:
                            print(f"Error: Unable to solve equation {lhs}. Reason: {str(e)}")
                            pending_equations.append((lhs, rhs))
                    else:
                        # Equation is not ready, add it to pending equations
                        print(f"Info: Equation {lhs} is waiting for complete data.")
                        pending_equations.append((lhs, rhs))

            # At this point, pending_equations contains equations waiting for complete data
            # You can later attempt to solve the pending equations when more data is available.
            # For example, when new data comes in:
            pending_equations = [(lhs, rhs) for lhs, rhs in pending_equations if all(variable in endogenous_results for variable in variables_to_use)]

            # Convert demand_total to a numeric type (assuming it's a string)
            demand_total = float(demand_total)
            # Parse demand_history JSON string into a list
            demand_history_list = json.loads(simulation_instance.demand_history)
            # Convert the elements in demand_history to a numeric type
            demand_history_numeric = [float(value) for value in demand_history_list]
            # Calculate the standard deviation
            demand_std_dev = np.std(demand_history_numeric + [demand_total])
            # demand_std_dev = np.std(list(simulation_instance.demand_history) + [demand_total])
            # Add this before the serialization
            print("Before serialization:", endogenous_results)

            # Convert non-serializable parts of endogenous_results to serializable types
            serializable_endogenous_results = {k: float(v) if isinstance(v, np.float64) else v for k, v in endogenous_results.items()}

            # Add this after the serialization
            print("After serialization:", serializable_endogenous_results)
            new_result_simulation = ResultSimulation(
                fk_simulation=simulation_instance,
                demand_mean=demand_total,
                demand_std_deviation=demand_std_dev,
                date=simulation_instance.date_created + timedelta(days=i),
                variables=serializable_endogenous_results,
                # end_date=simulation_instance.date_created + timedelta(days=i+1),
            )
            new_result_simulation.save()

        print("La simulación ha comenzado")
        print("dia de la simulacion " + str(i))
        return render(request, 'simulate/simulate-result.html', {
            'simulation_instance_id': simulation_instance,
        })
                    
  
# aqui se le manda el Simulate object que se creo en la vista de arriba
def simulate_result_simulation_view(request, simulation_id):
    results = get_results_for_simulation(simulation_id)
    # analysis_results = analyze_simulation_results(results)
    # decision = decision_support(analysis_results)
    results_simulation = ResultSimulation.objects.filter(is_active=True, fk_simulation_id=simulation_id)
    iniciales_a_buscar = ['CTR', 'CTAI', 'TPV', 'TPPRO', 'DI', 'VPC', 'IT', 'GT', 'TCA', 'NR', 'GO', 'GG', 'GT', 'CTT', 'CPP', 'CPV', 'CPI', 'CPMO', 'CUP', 'PVR', 'FU', 'TG', 'IB', 'MB', 'RI', 'RTI', 'RTC', 'PM', 'PE', 'HO', 'CHO', 'CA']
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
    
    # demand_initial = get_object_or_404(Demand, pk=1)
     # Obtén datos de la base de datos
    result_simulations = ResultSimulation.objects.filter(is_active=True, 
                                                         fk_simulation_id=simulation_id)

    # Recopila todos los datos fuera del bucle
    all_labels = []
    all_values = []

    for i, result_simulation in enumerate(result_simulations):
        data = result_simulation.get_average_demand_by_date()
        if data:
            for entry in data:
                all_labels.append(i + 1)
                all_values.append(entry['average_demand'])

    # Asegúrate de que las fechas estén ordenadas correctamente
    sorted_data = sorted(zip(all_labels, all_values), key=lambda x: x[0])
    if sorted_data:
        all_labels, all_values = zip(*sorted_data)
    else:
        # Handle the case when sorted_data is empty
        # You might want to provide default values or handle it according to your application logic
        all_labels = []
        all_values = []

    chart_data = {
        'labels': all_labels,
        'values': all_values,
        'x_label': 'Resultado',
        'y_label': 'Demanda',
    }

    # Crea el objeto Chart
    chart = Chart.objects.create(
        title=f'Comportamiendo de la demanda promedio para la simulación {simulation_id}',
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
        plt.plot(chart_data['labels'], chart_data['values'], marker='o', label='Demanda')
        # Agrega líneas horizontales y verticales
        for value in all_values:
            plt.axhline(y=value, linestyle='--', color='gray', alpha=0.5)

        for label in all_labels:
            plt.axvline(x=label, linestyle='--', color='gray', alpha=0.5)
            
        # Agrega una línea de tendencia
        coefficients = np.polyfit(chart_data['labels'], chart_data['values'], 1)
        polynomial = np.poly1d(coefficients)
        trendline_values = polynomial(chart_data['labels'])
        plt.plot(chart_data['labels'], trendline_values, label=f'Línea de tendencia: {coefficients[0]:.2f}x + {coefficients[1]:.2f}', linestyle='--')

        # Añade leyenda
        plt.legend()
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
        variable_name = recommendation_instance.variable_name  # Asegúrate de tener este campo en tu modelo FinanceRecommendation
        threshold_value = recommendation_instance.threshold_value  # Asegúrate de tener este campo en tu modelo FinanceRecommendation

        # Obtener el valor correspondiente desde totales_acumulativos
        if variable_name in totales_acumulativos:
            variable_value = totales_acumulativos[variable_name]

            # Comparar con el umbral y tomar decisiones
            if threshold_value is not None and variable_value > threshold_value:
                # La variable supera el umbral, mostrar recomendación
                recommendation_data = {
                    'name': name,
                    'recommendation': recommendation_instance.recommendation,
                    'description': recommendation_instance.description,
                    'variable_value': variable_value
                }
                financial_recommendations_to_show.append(recommendation_data)
    
    
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

    