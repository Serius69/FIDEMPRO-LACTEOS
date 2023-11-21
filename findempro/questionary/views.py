from pyexpat.errors import messages
from django.shortcuts import render, get_object_or_404, redirect
from variable.models import Variable
from questionary.models import Questionary,Question,Answer,QuestionaryResult
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
        questions = Question.objects.order_by('id').filter(is_active=True, fk_questionary__fk_business__fk_user=request.user, fk_questionary_id=selected_questionary_id)
        questionnaires = Questionary.objects.order_by('id').filter(is_active=True, fk_business__fk_user=request.user)
        context = {
            'selected_questionary_id':selected_questionary_id,
            'questionary_result_id':questionary_result_id,
            'started': started,
            'questions': questions,
            'questionnaires': questionnaires,
        }
        return render(request,'questionary/questionary-list.html',context)
    
    if request.method == 'POST' and 'start' in request.POST:
        request.session['started'] = True
        question_result = QuestionaryResult.objects.create(fk_business=request.user.fk_business)
        return redirect('questionary:questionary.list', question_result_id=question_result.id)
    
    if request.method == 'POST' and 'cancel' in request.POST:
        request.session['started'] = False
        return redirect('questionary:questionary.list')
    
    if request.method == 'POST' and 'next' in request.POST:
        question_id = request.POST.get('question_id')
        questionary_result_id = request.GET.get('question_result_id')
        answer = request.POST.get('answer')
        # Check if the selected_answer is valid (you might want to add more validation)
        if answer is not None:
            answer_instance = Answer.objects.create(
                answer=answer, fk_question_id=question_id, fk_questionary_result=questionary_result_id)
            # You might want to associate the answer with the user or session here
            answer_instance.save()
            messages.success(request, 'Response for the question saved successfully!')
        else:
            messages.error(request, 'Ocurred an error!')
        return redirect('questionary:questionary.list')
    
    if not started:
        if selected_questionary_id == None: 
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
        if selected_questionary_id == None: 
            questions_to_answer = Question.objects.order_by('id').filter(is_active=True, fk_questionary__fk_business__fk_user=request.user)
            questionnaires = Questionary.objects.order_by('id').filter(is_active=True, fk_business__fk_user=request.user)   
        else:
            questions_to_answer = Question.objects.order_by('id').filter(is_active=True, fk_questionary__fk_business__fk_user=request.user, fk_questionary_id=selected_questionary_id)
            questionnaires = Questionary.objects.order_by('id').filter(is_active=True, fk_business__fk_user=request.user)
        paginator = Paginator(questions_to_answer, 1) 
        page = request.GET.get('page')
        try:
            questions_to_answer = paginator.page(page)
        except PageNotAnInteger:
            questions_to_answer = paginator.page(1)
        except EmptyPage:
            questions_to_answer = paginator.page(paginator.num_pages)

        context = {
            'selected_questionary_id':selected_questionary_id,
            'started': started,
            'questions_to_answer': questions_to_answer,
            'questionnaires': questionnaires,
        }

        return render(request, 'questionary/questionary-list.html', context)



def questionnaire_save_view(request):
    if request.method == 'POST':
        # Extract answers from the form
        for key, value in request.POST.items():
            if key.startswith('question_'):
                question_id = key.replace('question_', '')
                question = Question.objects.get(pk=question_id)
                answer = Answer.objects.create(question=question, selected_answer=value)
                # You might want to associate the answer with the user or session here

        messages.success(request, 'Questionnaire results saved successfully!')
        return redirect('home')  # Redirect to the home page or another appropriate page after saving results

    return render(request, 'questionary/questionary-result.html')




