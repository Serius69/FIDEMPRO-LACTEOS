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
from simulate.models import Simulation
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
            
def create_and_save_questionary_result(sender, instance, created, **kwargs):
    if not created:
        return

    questionary_result = QuestionaryResult.objects.filter(fk_questionary=instance).first()

    if not questionary_result:
        questionary_result = QuestionaryResult.objects.create(
            fk_questionary=instance,
            is_active=instance.is_active
        )
    else:
        # Si existe, actualizar el estado
        questionary_result.is_active = instance.is_active
        questionary_result.save()    
def create_and_save_question(sender, instance, created, **kwargs):
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

        questions_created = Question.objects.filter(fk_questionary_id=instance.id).count()
        total_questions_expected = len(question_data)
        if questions_created == total_questions_expected:
            print(f"All questions have been correctly created for the product {instance.id}.")
            create_and_save_answer(instance)
        else:
            print(f"Not all questions have been created for the questionnaire {instance.id}.")          

def create_and_save_answer(instance):
    questionary_result = QuestionaryResult.objects.create(
        fk_questionary=instance,
        is_active=True
    )
    for data in answer_data:
        def get_question(question):
            try:
                if question == None:
                    return None
                return Question.objects.get(question=question)
            except Question.DoesNotExist:
                raise Http404(f"question with question '{question}' does not exist.")
            except Question.MultipleObjectsReturned:
                return Question.objects.filter(question=question).first()

        question = get_question(data['question'])
        answer = Answer.objects.create(
            answer=data['answer'],
            fk_question=question,
            fk_questionary_result=questionary_result,
            is_active=True
        )
        answer.is_active = instance.is_active
        answer.save()

def pages_faqs(request):
    template_name = "pages/faqs.html"
    return render(request, template_name)
pages_maintenance= PagesView.as_view(template_name="pages/maintenance.html")
pages_coming_soon= PagesView.as_view(template_name="pages/coming-soon.html")
pages_privacy_policy= PagesView.as_view(template_name="pages/privacy-policy.html")
pages_terms_conditions= PagesView.as_view(template_name="pages/term-conditions.html")
def pagina_error_404(request, exception):
    return render(request, 'pages/404.html', status=404)
