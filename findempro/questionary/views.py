from pyexpat.errors import messages
from django.shortcuts import render, get_object_or_404, redirect
from variable.models import Variable
from questionary.models import Questionary,Question
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.conf import settings
from django.http import JsonResponse
from django.contrib import messages
from django.http import HttpResponse,Http404
from django.utils import timezone
from django.http import HttpResponseForbidden
import openai
import logging
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

openai.api_key = settings.OPENAI_API_KEY
class AppsView(LoginRequiredMixin,TemplateView):
    pass
def questionnaire_list_view(request):
    """
    View function for displaying the questionnaire list.
    """
    if not request.session.get('started', False):
        # Show start button
        if request.method == 'POST' and 'start' in request.POST:
            request.session['started'] = True
            return redirect('first_question')
        else:
            return render(request, 'questionary/questionary-list.html')
    else:
        try:
            questions = Question.objects.order_by('-created_at')
            paginator = Paginator(questions, settings.QUESTIONS_PER_PAGE)
            page = request.GET.get('page')
            questions = paginator.get_page(page)

            context = {
                'started': request.session.get('started', False),
                'questions': questions
            }
        except Exception as e:
            context = {'error': str(e)}

        return render(request, 'questionary/questionary-list.html', context)

# def questionnaire_list_view(request):
#     try:
#         if request.method == 'POST' and 'start' in request.POST:
#             # Redirigir a primera pregunta
#             return redirect('first_question') 
#         elif not request.session.get('started', False):
#             # Mostrar botón de comenzar
#             request.session['started'] = True
#             return render(request, 'questions.html')
#         else:
#             # Mostrar preguntas
#             questions = Question.objects.order_by('-id')
#             per_page = 10 
#             paginator = Paginator(questions, per_page)
#             page = request.GET.get('page')
#             try:
#                 questions = paginator.page(page)
#             except PageNotAnInteger:
#                 questions = paginator.page(1)
#             except EmptyPage:
#                 questions = paginator.page(paginator.num_pages)
#             questionnaires = Questionary.objects.order_by('-id')
#             context = {'questions': questions, 'questionnaires': questionnaires}
#     except Exception as e:
#         error_message = str(e)
#         context = {'error_message': error_message}
#     return render(request, 'questionary/questionary-list.html', context)


def show_question(request, pk):
  try:
    question = Question.objects.get(pk=pk)
  except Question.DoesNotExist:
    raise Http404("Pregunta no encontrada")
  context = {
    'question': question
  }

  if request.method == 'POST':
    # Aquí puedes guardar la respuesta
    # Y luego redirigir a la siguiente pregunta
     return render(request, 'question.html', context)

def questionnaire_save_view(request):
    try:
        questions = Question.objects.order_by('-id')
        per_page = 10 
        paginator = Paginator(questions, per_page)
        page = request.GET.get('page')
        try:
            questions = paginator.page(page)
        except PageNotAnInteger:
            questions = paginator.page(1)
        except EmptyPage:
            questions = paginator.page(paginator.num_pages)
        questionnaires = Questionary.objects.order_by('-id')
        context = {'questions': questions, 'questionnaires': questionnaires}
    except Exception as e:
        error_message = str(e)
        context = {'error_message': error_message}
    return render(request, 'questionary/questionary-result.html', context)
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
# def generate_questions_for_variables(request):
#     # Retrieve all Variable objects from the database
#     variables = Variable.objects.all()

#     # Initialize an empty list to store generated questions for each variable
#     generated_questions_list = []

#     # Generate questions for each variable
#     for variable in variables:
#         generated_questions = generate_variable_questions(request, variable)
#         generated_questions_list.append((variable, generated_questions))

#     # Render a template with the generated questions
#     return render(
#         request,
#         "questionary/questionary-list.html", 
#         {"generated_questions_list": generated_questions_list},
#     )




