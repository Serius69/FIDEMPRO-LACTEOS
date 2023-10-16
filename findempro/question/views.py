from pyexpat.errors import messages
from django.shortcuts import render, get_object_or_404, redirect
from variable.models import Variable
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.conf import settings
from django.http import JsonResponse
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from django.http import HttpResponseForbidden
import openai
import logging

openai.api_key = settings.OPENAI_API_KEY
# Create question
class AppsView(LoginRequiredMixin,TemplateView):
    pass
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
