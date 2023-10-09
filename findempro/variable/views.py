from pyexpat.errors import messages
from django.shortcuts import render, get_object_or_404, redirect
from .models import Variable
from product.models import Product
from .forms import VariableForm  # Create a Django form for Variable
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.conf import settings
import openai
# Create your variable views here.
# 
openai.api_key = settings.OPENAI_API_KEY
class AppsView(LoginRequiredMixin,TemplateView):
    pass
# List
def variable_list(request):
    variables = Variable.objects.all().order_by('-id')
    # if variables:
    #     variable = Variable.objects.get(pk=pk)
    context = {'variable': variables}
    return render(request, 'variable/variable-list.html', context)

# Detail
def variable_overview(request,pk):
    variables = Variable.objects.all().order_by('-id')
    if variables:
        variable = Variable.objects.get(pk=pk)
    
    return render(request,"variable/variable-overview.html",{'variable':variable,'variable':variable})

# Create
def create_variable_view(request):
    products = Product.objects.all().order_by('-id')
    variable = Variable.objects.all().order_by('-id')
    context = {'variable': variable, 'product': products}
    if request.method == "POST":
        form = VariableForm(request.POST or None,request.FILES or None)
        if form.is_valid():
            form.save()
            messages.success(request,"Variable inserted successfully!")
            return redirect("variable:variable.overview")
        else:
            messages.error(request,"Something went wrong!")
            return redirect("variable:variable.overview")
    return render(request,"variable/variable-list.html",context)

# Update
def update_variable_view(request,pk):
    variable = Variable.objects.get(pk=pk)
    if request.method == "POST":
        form = VariableForm(request.POST or None,request.FILES or None,instance=variable)
        if form.is_valid():
            form.save()
            messages.success(request,"Variable updated successfully!")
            return redirect("variable:variable.overview")
        else:
            messages.error(request,"Something went wrong!")
            return redirect("variable:variable.overview")
    return render(request,"variable/variable-list.html")

# Delete
def delete_variable_view(request,pk):
    variable = Variable.objects.get(pk=pk)
    variable.delete()
    messages.success(request,"Variable deleted successfully!")
    return redirect("variable:variable.list")

# Create question
def generate_variable_questions(request, variable):
    # Extract relevant information from the Variable object
    django_variable = f"{variable.name} = models.{variable.type}Field({variable.get_type_display()}, {variable.get_parameters_display()})"

    # Define a prompt to generate questions
    prompt = f"Create a question to gather and add precise data to a financial test form for the company's Variable:\n\n{django_variable}\n\nQuestion:"

    # Generate questions using GPT-3
    response = openai.Completion.create(
        engine="text-davinci-002",  # Choose the appropriate engine
        prompt=prompt,
        max_tokens=100,  # Adjust the max tokens as needed
        n=1,  # Number of questions to generate
        stop=None,  # Stop generating questions at a specific token (e.g., "?")
    )

    # Extract and return the generated questions
    question = [choice['text'].strip() for choice in response.choices]
    return question
# THe view to show the questions generate for each variable
def generate_questions_for_variables(request):
    # Retrieve all Variable objects from the database
    variables = Variable.objects.all()

    # Initialize an empty list to store generated questions for each variable
    generated_questions_list = []

    # Generate questions for each variable
    for variable in variables:
        generated_questions = generate_variable_questions(request, variable)
        generated_questions_list.append((variable, generated_questions))

    # Render a template with the generated questions
    return render(
        request,
        "questionary/questionary-list.html", 
        {"generated_questions_list": generated_questions_list},
    )
