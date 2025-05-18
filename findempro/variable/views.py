from django.shortcuts import render, get_object_or_404, redirect
from .models import Variable, Equation, EquationResult
from product.models import Product
from business.models import Business
from .forms import VariableForm
from pages.models import Instructions
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.conf import settings
import openai
from django.http import JsonResponse
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import ObjectDoesNotExist
from sympy import symbols, Eq, solve
openai.api_key = settings.OPENAI_API_KEY
from .forms import EquationForm
from django.db.models import Q
class AppsView(LoginRequiredMixin, TemplateView):
    pass
VARIABLES_PER_PAGE2 = 24
def variable_list(request):
    try:
        product_id = request.GET.get('product_id', 'All')
        businesses = Business.objects.filter(is_active=True, fk_user=request.user).order_by('-id')
        
        products = Product.objects.filter(is_active=True,fk_business__in=businesses, fk_business__fk_user=request.user).order_by('-id')
        variables_conditions = Q(is_active=True, fk_product__in=products, fk_product__fk_business__fk_user=request.user)
        
        if product_id != 'All':
            variables_conditions &= Q(fk_product_id=product_id)
            
        variables = Variable.objects.filter(variables_conditions).order_by('-id')
            
        paginator = Paginator(variables, VARIABLES_PER_PAGE2)
        page = request.GET.get('page')

        try:
            variables = paginator.page(page)
        except PageNotAnInteger:
            variables = paginator.page(1)
        except EmptyPage:
            variables = paginator.page(paginator.num_pages)

        context = {
            'variables': variables, 
            'products': products,
            'instructions': Instructions.objects.filter(is_active=True).order_by('-id')
        }
        return render(request, 'variable/variable-list.html', context)
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)
VARIABLES_PER_PAGE = 4
def variable_overview(request, pk):
    try:
        variable = get_object_or_404(Variable, pk=pk)
        product_id = variable.fk_product.id
        variable_id = variable.id

        variables_related = Variable.objects.filter(
            is_active=True, 
            fk_product_id=product_id
        ).order_by('-id')

        equation_conditions = Q(
            is_active=True,
            fk_variable1__fk_product_id=product_id,
            fk_variable1_id=variable_id
        ) 
        equations = Equation.objects.filter(equation_conditions).order_by('-id')
        
        # Paginate the variables
        paginator = Paginator(variables_related, VARIABLES_PER_PAGE)
        page = request.GET.get('page')

        try:
            variables_related = paginator.page(page)
        except PageNotAnInteger:
            variables_related = paginator.page(1)
        except EmptyPage:
            variables_related = paginator.page(paginator.num_pages)
            
        return render(request, "variable/variable-overview.html", {
            'variable': variable, 
            'variables_related': variables_related,
            'equations': equations
        })
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)
def create_or_update_variable_view(request, pk=None):
    variable = None
    if pk:
        variable = get_object_or_404(Variable, pk=pk)
    if request.method == 'POST':
        form = VariableForm(request.POST, request.FILES, instance=variable)
        try:
            if form.is_valid():
                if pk is None:
                    variable_name = form.cleaned_data.get('name')
                    initial_prompt = f"Generate the initials of the variable, but only use 4 characters. Do not include additional advertisements or instructions. Provide the initials for the next variable: {variable_name}"

                    response = openai.Completion.create(
                        engine="text-davinci-002",
                        prompt=initial_prompt,
                        max_tokens=5,
                        stop=None
                    )
                    initials = response.choices[0].text.strip()

                    form.instance.initials = initials

                variable = form.save()
                messages.success(request, 'Variable created successfully' if pk is None else 'Variable updated successfully')
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'errors': form.errors})
        except Exception as e:
            print(e)
            return JsonResponse({'success': False, 'error': 'An error occurred while saving the variable'})
    else:
        form = VariableForm(instance=variable)
    return render(request, 'variable/variable-form.html', {'form': form})
def delete_variable_view(request, pk):
    try:
        if request.method == 'POST':
            variable = get_object_or_404(Variable, pk=pk)
            variable.is_active = False
            variable.save()
            messages.success(request, "Variable eliminado con éxito!")
            return redirect("variable:variable.list")
        else:
            messages.error(request, "Invalid request method. Only POST is allowed.")
            return HttpResponse("Invalid request method. Only POST is allowed.", status=405)  # Method Not Allowed
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)
def get_variable_details_view(request, pk):
    try:
        if request.method == 'GET':
            variable = Variable.objects.get(id=pk)
            variable_details = {
                "name": variable.name,
                "type": variable.type,
                "fk_product": variable.fk_product.name,
                "unit": variable.unit,
                "image_src": str(variable.image_src),
                "initials": variable.initials,
                "description": variable.description,
            }
            return JsonResponse(variable_details)
    except ObjectDoesNotExist:
        return JsonResponse({"error": "El negocio no existe"}, status=404)
def create_or_update_equation_view(request, pk=None):
    equation = None
    if pk:
        equation = get_object_or_404(Variable, pk=pk)
    if request.method in ['POST', 'PUT']:
        form = EquationForm(request.POST, request.FILES, instance=equation)
        try:
            if form.is_valid():
                equation = form.save()
                messages.success(request, 'Equation created successfully' if pk is None else 'Equation updated successfully')
                return JsonResponse({'success': True}) if pk is None else redirect("variable:variable.overview", pk=pk)
            else:
                return JsonResponse({'success': False, 'errors': form.errors}) if pk is None else render(request, "variable/variable-form.html", {'form': form})
        except Exception as e:
            print(e)
            return JsonResponse({'success': False, 'error': 'An error occurred while saving the equation'}) if pk is None else HttpResponse(status=500)
    else:
        form = EquationForm(instance=equation)
    return render(request, 'variable/variable-form.html', {'form': form})
def delete_equation_view(request, pk):
    try:
        equation = get_object_or_404(Equation, pk=pk)
        equation.is_active=False
        equation.save()
        messages.success(request, "Variable deleted successfully!")
        return redirect("product:area.overview")
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)  
def get_equation_details(request, pk):
    try:
        if request.method == 'GET':
            equation = Equation.objects.get(id=pk)
            equation_details = {
                "name": equation.name,
                "expression": equation.expression,
                "fk_area": equation.fk_area.name,
                "fk_variable1": equation.fk_variable1.name if equation.fk_variable1 else None,
                "fk_variable2": equation.fk_variable2.name if equation.fk_variable2 else None,
                "fk_variable3": equation.fk_variable3.name if equation.fk_variable3 else None,
                "fk_variable4": equation.fk_variable4.name if equation.fk_variable4 else None,
                "fk_variable5": equation.fk_variable5.name if equation.fk_variable5 else None,
                "description": equation.description,
            }

            return JsonResponse(equation_details)
    except ObjectDoesNotExist:
        return JsonResponse({"error": "La ecuacion no existe"}, status=404)

def solve_equation(request):
    if request.method == 'POST':
        equation_str = request.POST.get('equation', '')
        x = symbols('x')
        
        try:
            equation = Eq(eval(equation_str), 0)
            solution = solve(equation, x)
        except Exception as e:
            # Manejar errores en la entrada de la ecuación
            error_message = str(e)
            return render(request, 'error_template.html', {'error_message': error_message})

        return render(request, 'result_template.html', {'solution': solution})

    return render(request, 'input_template.html')
def generate_variable_questions(request, variable):
    django_variable = f"{variable.name} = models.{variable.type}Field({variable.get_type_display()}, {variable.get_parameters_display()})"
    prompt = f"Create a question to gather and add precise data to a financial test form for the company's Variable:\n\n{django_variable}\n\nQuestion:"
    response = openai.Completion.create(
        engine="text-davinci-002",  # Choose the appropriate engine
        prompt=prompt,
        max_tokens=100,  # Adjust the max tokens as needed
        n=1,  # Number of questions to generate
        stop=None,  # Stop generating questions at a specific token (e.g., "?")
    )
    question = [choice['text'].strip() for choice in response.choices]
    return question
# THe view to show the questions generate for each variable
def generate_questions_for_variables(request):
    variables = Variable.objects.all()
    generated_questions_list = []
    for variable in variables:
        generated_questions = generate_variable_questions(request, variable)
        generated_questions_list.append((variable, generated_questions))
    return render(
        request,
        "questionary/questionary-main.html", 
        {"generated_questions_list": generated_questions_list},
    )
