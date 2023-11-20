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
    started = request.session.get('started', False)
    selected_questionary_id = request.GET.get('questionary_id')
    
    if request.method == 'GET' and 'select' in request.GET:
        selected_questionary_id = request.GET.get('selected_questionary', 0)
        context = {
            'selected_questionary_id':selected_questionary_id,
        }
        return render(request,'questionary/questionary-list.html',context)
    
    if request.method == 'POST' and 'start' in request.POST:
        request.session['started'] = True
        return redirect('questionary:questionary.list')
    
    if request.method == 'POST' and 'cancel' in request.POST:
        request.session['started'] = False
        return redirect('questionary:questionary.list')
    
    if not started:
        if selected_questionary_id == 0: 
            questions = Question.objects.order_by('id').filter(is_active=True, fk_questionary__fk_business__fk_user=request.user)
            questionnaires = Questionary.objects.order_by('id').filter(is_active=True, fk_business__fk_user=request.user)   
        else:
            questions = Question.objects.order_by('id').filter(is_active=True, fk_questionary__fk_business__fk_user=request.user, fk_questionary_id=selected_questionary_id)
            questionnaires = Questionary.objects.order_by('id').filter(is_active=True, fk_business__fk_user=request.user)
        paginator = Paginator(questions, 10) 
        page = request.GET.get('page')
        try:
            questions = paginator.page(page)
        except PageNotAnInteger:
            questions = paginator.page(1)
        except EmptyPage:
            questions = paginator.page(paginator.num_pages)
        context = {
            'selected_questionary_id':selected_questionary_id,
            'started': started,
            'questions': questions,
            'questionnaires': questionnaires,
        }
        return render(request,'questionary/questionary-list.html',context)
    else:
        questions_to_answer = Question.objects.order_by('-id').filter(is_active=True,fk_questionary_id=selected_questionary_id)
        questionnaires = Questionary.objects.order_by('-id').filter(is_active=True, fk_business__fk_user=request.user)
        paginator = Paginator(questions_to_answer, 5) 
        page = request.GET.get('page')
        try:
            questions_to_answer = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            questions_to_answer = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            questions_to_answer = paginator.page(paginator.num_pages)

        context = {
            'selected_questionary_id':selected_questionary_id,
            'started': started,
            'questions_to_answer': questions_to_answer,
            'questionnaires': questionnaires,
        }

        return render(request, 'questionary/questionary-list.html', context)

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




