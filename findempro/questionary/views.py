from pyexpat.errors import messages
from django.shortcuts import render, get_object_or_404, redirect
from variable.models import Variable
from product.models import Product
from questionary.models import Questionary,Question,Answer,QuestionaryResult
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.conf import settings
from django.http import JsonResponse
from django.contrib import messages
from django.http import HttpResponse,Http404
from django.utils import timezone
from django.http import HttpResponseForbidden
import logging
from business.models import Business
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse
from django.shortcuts import render, redirect
from .models import Answer
from django.core.exceptions import ObjectDoesNotExist
class AppsView(LoginRequiredMixin,TemplateView):
    pass
def questionnaire_list_view(request):
    started_questionary = request.session.get('started_questionary', False)
    selected_questionary_id = None
    questionary_result_id = None
    questions = None
    questionnaires = None
    paginator = None
    businessess = Business.objects.filter(is_active=True, fk_user=request.user)
    products = Product.objects.filter(is_active=True,fk_business__in=businessess, fk_business__fk_user=request.user)
    if request.method == 'GET' and 'select' in request.GET:
        selected_questionary_id = request.GET.get('selected_questionary_id', 0)
        print("Se selecciono un cuestionario " + str(selected_questionary_id))
        # Set the session variable
        request.session['selected_questionary_id'] = selected_questionary_id
        print("Se seteo la variable selected_questionary_id " + str(selected_questionary_id))
        questions = Question.objects.order_by('id').filter(
            is_active=True, 
            fk_questionary__fk_product__fk_business__fk_user=request.user, 
            fk_questionary_id=selected_questionary_id)
        questionnaires = Questionary.objects.order_by('id').filter(is_active=True, fk_product__in=products,fk_product__fk_business__fk_user=request.user)
        context = {
            'selected_questionary_id': selected_questionary_id,
            'questionary_result_id': questionary_result_id,
            'started_questionary': started_questionary,
            'questions': questions,
            'questionnaires': questionnaires,
        }
        return render(request,'questionary/questionary-list.html',context)
    
    if request.method == 'POST' and 'start' in request.POST:
        request.session['started_questionary'] = True
        selected_questionary_id = request.session.get('selected_questionary_id')
        print("Se comenzará con el cuestionario" +str(selected_questionary_id))
        questionary_selected = Questionary.objects.get(pk=selected_questionary_id)
        questionary_result = QuestionaryResult.objects.create(
            fk_questionary=questionary_selected
        )
        questionary_result_id = questionary_result.id      
        request.session['questionary_result_id'] = questionary_result_id
        print("Se seteo la variable questionary_result_id " + str(questionary_result_id))
        return redirect(reverse('questionary:questionary.list'))

    if request.method == 'POST' and 'save' in request.POST:
        selected_questionary_id = request.session.get('selected_questionary_id')
        questionary_result_id = request.session.get('questionary_result_id')
        # post_data = {k: v for k, v in request.POST.items() if not k.startswith('csrf')}
        for key, value in request.POST.items():
            # aqui esta mostranto solo quietion id en texto tiene que mostrar el numero de la pregunta no esto
            if key.startswith('question_'):
                question_id = int(value)
                answer = request.POST.get(f'answer_{question_id}')
                print(f'Question ID: {question_id}, Answer: {answer}')

                question_instance = get_object_or_404(Question, pk=question_id)
                print(f'Saving answer for question {question_instance.id}: {answer} in questionnaire result {selected_questionary_id}')

                answer_instance = Answer.objects.create(
                    fk_question=question_instance,
                    answer=answer,
                    fk_questionary_result_id=questionary_result_id
                )
                answer_instance.save()
                # Check if 'page' parameter is present in the reques
        print("Se guardaran las respuestas en el questionary_result: " + str(questionary_result_id))
        selected_questionary_id = request.session.get('selected_questionary_id')
        print("Se comenzó el cuestionario seleccionado" + str(selected_questionary_id))
        try:
            show_questionary = Questionary.objects.get(pk=selected_questionary_id)
        except ObjectDoesNotExist:
            show_questionary = None
        if selected_questionary_id == None: 
            questions_to_answer = Question.objects.order_by('id').filter(is_active=True, fk_questionary__fk_product__fk_business__fk_user=request.user)
            
            questionnaires = Questionary.objects.order_by('id').filter(is_active=True, fk_product__in=products , fk_product__fk_business__fk_user=request.user) 
        else:
            questions_to_answer = Question.objects.order_by('id').filter(is_active=True, fk_questionary__fk_product__fk_business__fk_user=request.user, fk_questionary_id=selected_questionary_id)
            
            questionnaires = Questionary.objects.order_by('id').filter(is_active=True, fk_product__in=products, fk_product__fk_business__fk_user=request.user)
        paginator = Paginator(questions_to_answer, 5) 
              
        page_number = request.GET.get('page', 1)
        try:
            # Attempt to get the requested page
            next_page = paginator.page(page_number)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            next_page = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            next_page = paginator.page(paginator.num_pages)
        request.session['questionary_result_id'] = questionary_result_id
        return redirect(reverse('questionary:questionary.list') + f'?page={next_page.number}')
        # return redirect(reverse('questionary:questionary.list'))
    
    if request.method == 'POST' and 'cancel' in request.POST:
        request.session['started_questionary'] = False
        print("Se cancelo el cuestionario")        
        return redirect('questionary:questionary.list')
       
    if not started_questionary:
        if selected_questionary_id == None: 
            questionnaires = Questionary.objects.order_by('id').filter(is_active=True, fk_product__fk_business__fk_user=request.user)   
            questions = Question.objects.order_by('id').filter(is_active=True, fk_questionary__fk_product__fk_business__fk_user=request.user, fk_questionary_id=selected_questionary_id)
            questionnaires = Questionary.objects.order_by('id').filter(is_active=True, fk_product__in=products, fk_product__fk_business__fk_user=request.user)
            paginator = Paginator(questions, 10) 
            page = request.GET.get('page')
            try:
                questions = paginator.page(page)
            except PageNotAnInteger:
                questions = paginator.page(1)
            except EmptyPage:
                questions = paginator.page(paginator.num_pages)
        else:
            questions = Question.objects.order_by('id').filter(is_active=True, fk_questionary__fk_product__fk_business__fk_user=request.user, fk_questionary_id=selected_questionary_id)
            questionnaires = Questionary.objects.order_by('id').filter(is_active=True, fk_product__in=products, fk_product__fk_business__fk_user=request.user)
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
            'started_questionary': started_questionary,
            'questions': questions,
            'questionnaires': questionnaires,
        }
        return render(request,'questionary/questionary-list.html',context)
    else:
        questionary_result_id = request.session.get('questionary_result_id')
        print("Se guardaran las respuestas en el questionary_result: " + str(questionary_result_id))
        selected_questionary_id = request.session.get('selected_questionary_id')
        print("Se comenzó el cuestionario seleccionado" + str(selected_questionary_id))
        try:
            show_questionary = Questionary.objects.get(pk=selected_questionary_id)
        except ObjectDoesNotExist:
            show_questionary = None
        if selected_questionary_id == None: 
            questions_to_answer = Question.objects.order_by('id').filter(is_active=True, fk_questionary__fk_product__fk_business__fk_user=request.user)
            questionnaires = Questionary.objects.order_by('id').filter(is_active=True, fk_product__in=products, fk_product__fk_business__fk_user=request.user) 
        else:
            questions_to_answer = Question.objects.order_by('id').filter(is_active=True, fk_questionary__fk_product__fk_business__fk_user=request.user, fk_questionary_id=selected_questionary_id)
            questionnaires = Questionary.objects.order_by('id').filter(is_active=True, fk_product__in=products, fk_product__fk_business__fk_user=request.user)
        paginator = Paginator(questions_to_answer, 5) 
        
        page = request.GET.get('page')
        try:
            questions_to_answer = paginator.page(page)
        except PageNotAnInteger:
            questions_to_answer = paginator.page(1)
        except EmptyPage:
            questions_to_answer = paginator.page(paginator.num_pages)

        context = {
            'selected_questionary_id':selected_questionary_id,
            'started_questionary': started_questionary,
            'questions_to_answer': questions_to_answer,
            'questionnaires': questionnaires,
            'show_questionary': show_questionary
        }   
        return render(request, 'questionary/questionary-list.html', context)
                                
# def questionnaire_save_view(request):
#     if request.method == 'POST':
#         questions_to_answer = Question.objects.order_by('id').filter(is_active=True, fk_questionary__fk_product__fk_business__fk_user=request.user)
#         for question in questions_to_answer:
#             answer_text = request.POST.get('answer_' + str(question.id))
#             answer = Answer(answer=answer_text, fk_question=question)
#             answer.save()
#         return redirect('questionary:questionary.result')
#     else:
#         questions_to_answer = Question.objects.order_by('id').filter(is_active=True, fk_questionary__fk_product__fk_business__fk_user=request.user)
#         context = {
#             'questions_to_answer': questions_to_answer
#         }
#         return render(request, 'questionary/questionnaire_form.html', context)
#                # Add your code here to render the form
#         pass
def questionnaire_result_view(request, pk):
    try:
        questionary_result = get_object_or_404(QuestionaryResult, pk=pk)
        answers = Answer.objects.filter(
            fk_questionary_result=questionary_result, 
            is_active=True,
        )
        paginator = Paginator(answers, 100)
        page = request.GET.get('page')
        answers = paginator.get_page(page)
        context = {'questionary_result': questionary_result, 'answers': answers}
        return render(request, 'questionary/questionary-result.html', context)
    except Exception as e:
        messages.error(request, "An error occurred. Please check the server logs for more information: ", e)
        return HttpResponse(status=500)