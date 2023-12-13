from django.shortcuts import render
from django.views.generic import TemplateView
from .forms import RegisterElementsForm
from user.models import UserProfile
from business.models import Business
from product.models import Product,Area
from variable.models import Variable,Equation
from questionary.models import Questionary,Question,QuestionaryResult,Answer
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from simulate.models import Simulation, ResultSimulation, Demand, DemandBehavior
from django.contrib.auth.decorators import login_required
from product.products_data import products_data
from product.areas_data import areas_data
from questionary.questionary_data import questionary_data,question_data
from questionary.questionary_result_data import questionary_result_data,answer_data
from variable.variables_data import variables_data
from variable.equations_data import equations_data
from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import MultipleObjectsReturned
from django.http import Http404
import random
import numpy as np
from datetime import datetime, timedelta
class PagesView(TemplateView):
    pass
@login_required
def register_elements(request):
    if request.method == 'POST':
        form = RegisterElementsForm(request.POST)
        if form.is_valid():
            create_and_save_business(request.user, created=True)
            return redirect("dashboard:index")  # Redirigir a la página de inicio después de procesar

    else:
        form = RegisterElementsForm()

    return render(request, 'pages/register_elements.html', {'form': form})

def create_and_save_business(instance, created, **kwargs):
    if created:
        user = User.objects.get(pk=instance.pk)
        business = Business.objects.create(
            name="Pyme Lactea",
            type=1,  
            location="La Paz",
            image_src=f"/images/business/Pyme Lactea.jpg",
            fk_user_id=user.id,
        )
        business.is_active = instance.is_active
        business.save()
        create_and_save_product(business,created=True)
    print('Se creo el negocio')
def create_and_save_product(instance, created, **kwargs):
    if created:
        business = Business.objects.get(pk=instance.pk)
        for data in products_data:
            product = Product.objects.create(
                name=data['name'],                    
                description=data['description'],
                image_src=f"/images/product/{data.get('name')}.jpg",
                type= data['type'],
                is_active= True,
                fk_business_id=business.id,
            )
            product.is_active = instance.is_active
            product.save()
            create_and_save_area(product, created=True)
            create_variables(product, created=True)
            create_and_save_questionary(product, created=True)
    print('Se crearon los productos')
def create_and_save_area(instance, created, **kwargs):
    if created:
        product = Product.objects.get(pk=instance.pk)
        for data in areas_data:
            area = Area.objects.create(
                name=data['name'],                    
                description=data['description'],
                params= data['params'],
                image_src=f"/images/area/{data.get('name')}.jpg",
                is_active= True,
                fk_product_id=product.id,
            )
            area.is_active = instance.is_active
            area.save()
    print('Se crearon las áreas')
def create_variables(instance, created, **kwargs):
    if created:
        product = Product.objects.get(pk=instance.pk)
        for data in variables_data:
            variable= Variable.objects.create(
                name=data.get('name'),
                initials=data.get('initials'),
                type=data.get('type'),
                unit=data.get('unit'),
                image_src=f"/images/variable/{data.get('name')}.jpg",
                description=data.get('description'),
                fk_product_id=product.id,
                is_active=True
            )
            variable.is_active = instance.is_active
            variable.save()
            
        def create_and_save_equations(instance):
            for data in equations_data:
                def get_variable(variable_name, product_id):
                    try:
                        if variable_name == None:
                            return None
                        return Variable.objects.get(initials=variable_name, fk_product_id=product_id)
                    except Variable.DoesNotExist:
                        raise Http404(f"Variable with initials '{variable_name}' associated with product id '{product_id}' does not exist.")
                    except Variable.MultipleObjectsReturned:
                        return Variable.objects.filter(initials=variable_name, fk_product_id=product_id).first() 
                def get_area(area_name, product_id):
                    try:
                        return Area.objects.get(name=area_name, fk_product_id=product_id)
                    except Area.DoesNotExist:
                        raise Http404(f"Area with name '{area_name}' associated with product id '{product_id}' does not exist.")
                    except Area.MultipleObjectsReturned:
                        return Area.objects.filter(name=area_name, fk_product_id=product_id).first()
                    
                product_id = product.id  
                variable1 = get_variable(data['variable1'], product_id)
                variable2 = get_variable(data['variable2'], product_id)
                variable3 = get_variable(data.get('variable3', None), product_id)
                variable4 = get_variable(data.get('variable4', None), product_id)
                variable5 = get_variable(data.get('variable5', None), product_id)
                area = get_area(data['area'], product_id)
                equation = Equation.objects.create(
                    name=data['name'],
                    description=data.get('description', 'Descripcion predeterminada'),
                    expression=data['expression'],
                    fk_variable1=variable1,
                    fk_variable2=variable2,
                    fk_variable3=variable3,
                    fk_variable4=variable4,
                    fk_variable5=variable5,
                    fk_area=area,                            
                    is_active=True
                )
                equation.is_active = instance.is_active
                equation.save()
                
        variables_created = Variable.objects.filter(fk_product_id=product.id).count()
        total_variables_expected = len(variables_data)

        if variables_created == total_variables_expected:
            print(f"Todas las variables se han creado correctamente para el producto {product.id}.")
            create_and_save_equations(instance)
        else:
            print(f"No se han creado todas las variables para el producto {product.id}.")
        
def create_and_save_questionary(instance, created, **kwargs):
    if created:
        for data in questionary_data:  # Assuming questionary_data is defined somewhere
            questionary = Questionary.objects.create(
                questionary=f"{data['questionary']} {instance.name}",
                fk_product=instance,
                is_active=True
            )
            questionary.is_active = instance.is_active
            questionary.save()
        
        create_and_save_question(questionary, created=True)

def create_and_save_question(instance, created, **kwargs):
    if created:
        for data in question_data:
            try:
                variable = Variable.objects.get(initials=data['initials_variable'])
            except MultipleObjectsReturned:
                variable = Variable.objects.filter(initials=data['initials_variable']).first()

            if data['type'] == 1:
                possible_answers = None  # Default value if 'possible_answers' is not present
            else:
                possible_answers = data.get('possible_answers')
                
            question = Question.objects.create(
                question=data['question'],
                type=data['type'],
                fk_questionary_id=instance.id,
                fk_variable_id=variable.id,
                possible_answers=possible_answers,
                is_active=True
            )
            question.is_active = instance.is_active
            question.save()

@login_required
def register_elements_simulation(request):
    if request.method == 'POST':
        form = RegisterElementsForm(request.POST)
        if form.is_valid():
            questionaries = Questionary.objects.filter(is_active=True, fk_product__fk_business__fk_user=request.user)
            
            if questionaries.exists():
                for questionary in questionaries:
                    create_and_save_questionary_result(questionary, created=True)
                
                return redirect("dashboard:index")  # Redirect to the dashboard after processing

    else:
        form = RegisterElementsForm()

    return render(request, 'pages/register_elements.html', {'form': form})
def create_and_save_questionary_result(instance, created, **kwargs):
    if not created:
        return

    questionary_result, created = QuestionaryResult.objects.get_or_create(
        fk_questionary=instance,
        defaults={'is_active': instance.is_active}
    )

    if not created and questionary_result.is_active != instance.is_active:
        # Si existe, pero el estado ha cambiado, actualizar el estado
        questionary_result.is_active = instance.is_active
        questionary_result.save()    

    create_and_save_answer(questionary_result)
    create_and_save_simulation(questionary_result, created=True)

def create_and_save_answer(instance):
    for data in answer_data:
        def get_question(question):
            if question is None:
                return None
            try:
                return Question.objects.get(question=question)
            except Question.DoesNotExist:
                raise Http404(f"Question with question '{question}' does not exist.")
            except Question.MultipleObjectsReturned:
                return Question.objects.filter(question=question).first()

        question = get_question(data['question'])
        answer, created = Answer.objects.get_or_create(
            answer=data['answer'],
            fk_question=question,
            fk_questionary_result=instance,
            defaults={'is_active': True}
        )

        if not created and answer.is_active != instance.is_active:
            # Si existe, pero el estado ha cambiado, actualizar el estado
            answer.is_active = instance.is_active
            answer.save()
def create_and_save_simulation(instance, created, **kwargs):
    fdp_instance = instance.fk_questionary.fk_product.fk_business.fk_business_fdp.first()
    if fdp_instance is not None:
        demand = [random.randint(1000, 5000) for _ in range(30)]
        simulation, created = Simulation.objects.get_or_create(
            unit_time='day',
            fk_fdp=fdp_instance,
            demand_history=demand,
            quantity_time=30,
            fk_questionary_result=instance,
            defaults={'is_active': True}
        )
        if created:
            create_random_result_simulations(simulation, created=True)

def create_random_result_simulations(instance, created, **kwargs):
    # Obtén la fecha inicial de la instancia de Simulation
    current_date = instance.date_created
    fk_simulation_instance = instance
    result_simulation = None
    print(f'Number of ResultSimulation instances to be created by the Simulate: {instance.quantity_time}')
    # por que se esta creando 4 veces ResultSimulation por Simulation
    for _ in range(int(instance.quantity_time)):
        demand_mean = 0
        demand = [random.uniform(1000, 5000) for _ in range(10)]
        demand_std_deviation = random.uniform(5, 20)
        
        variables = {
            "CTR": [random.uniform(1000, 5000) for _ in range(10)],
            "CTAI": [random.uniform(5000, 20000) for _ in range(10)],
            "TPV": [random.uniform(1000, 5000) for _ in range(10)],
            "TPPRO": [random.uniform(800, 4000) for _ in range(10)],
            "DI": [random.uniform(50, 200) for _ in range(10)],
            "VPC": [random.uniform(500, 1500) for _ in range(10)],
            "IT": [random.uniform(5000, 20000) for _ in range(10)],
            "GT": [random.uniform(3000, 12000) for _ in range(10)],
            "TCA": [random.uniform(500, 2000) for _ in range(10)],
            "NR": [random.uniform(0.1, 0.5) for _ in range(10)],
            "GO": [random.uniform(1000, 5000) for _ in range(10)],
            "GG": [random.uniform(1000, 5000) for _ in range(10)],
            "GT": [random.uniform(2000, 8000) for _ in range(10)],
            "CTTL": [random.uniform(1000, 5000) for _ in range(10)],
            "CPP": [random.uniform(500, 2000) for _ in range(10)],
            "CPV": [random.uniform(500, 2000) for _ in range(10)],
            "CPI": [random.uniform(500, 2000) for _ in range(10)],
            "CPMO": [random.uniform(500, 2000) for _ in range(10)],
            "CUP": [random.uniform(500, 2000) for _ in range(10)],
            "FU": [random.uniform(0.1, 0.5) for _ in range(10)],
            "TG": [random.uniform(2000, 8000) for _ in range(10)],
            "IB": [random.uniform(3000, 12000) for _ in range(10)],
            "MB": [random.uniform(2000, 8000) for _ in range(10)],
            "RI": [random.uniform(1000, 5000) for _ in range(10)],
            "RTI": [random.uniform(1000, 5000) for _ in range(10)],
            "RTC": [random.uniform(0.1, 0.5) for _ in range(10)],
            "PM": [random.uniform(500, 1500) for _ in range(10)],
            "PE": [random.uniform(1000, 5000) for _ in range(10)],
            "HO": [random.uniform(10, 50) for _ in range(10)],
            "CHO": [random.uniform(1000, 5000) for _ in range(10)],
            "CA": [random.uniform(1000, 5000) for _ in range(10)],
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

    # Verifica si ya existe una instancia de demand_instance
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
            quantity=demand_mean,  # Puedes ajustar esto según tus necesidades
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

def pages_faqs(request):
    template_name = "pages/faqs.html"
    return render(request, template_name)
pages_maintenance= PagesView.as_view(template_name="pages/maintenance.html")
pages_coming_soon= PagesView.as_view(template_name="pages/coming-soon.html")
pages_privacy_policy= PagesView.as_view(template_name="pages/privacy-policy.html")
pages_terms_conditions= PagesView.as_view(template_name="pages/term-conditions.html")
def pagina_error_404(request, exception):
    return render(request, 'pages/404.html', status=404)
