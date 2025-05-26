import json
from django.shortcuts import render, get_object_or_404, redirect
from variable.models import Variable
from django.contrib.auth.decorators import login_required
from product.models import Product
from questionary.models import Questionary, Question, Answer, QuestionaryResult
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.conf import settings
from django.http import JsonResponse
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.utils import timezone
from django.http import HttpResponseForbidden
import logging
from business.models import Business
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse
from django.shortcuts import render, redirect
from .models import Answer
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
import re
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

class AppsView(LoginRequiredMixin, TemplateView):
    pass

@login_required
def questionnaire_main_view(request):
    started_questionary = request.session.get('started_questionary', False)
    selected_questionary_id = request.session.get('selected_questionary_id', None)
    questionary_result_id = request.session.get('questionary_result_id', None)
    questions = None
    questionnaires = None
    paginator = None
    
    businessess = Business.objects.filter(is_active=True, fk_user=request.user)
    products = Product.objects.filter(is_active=True, fk_business__in=businessess, fk_business__fk_user=request.user)
    
    # Handle questionnaire selection
    if request.method == 'GET' and 'select' in request.GET:
        selected_questionary_id = request.GET.get('selected_questionary_id', 0)
        request.session['selected_questionary_id'] = selected_questionary_id
        
        questions = Question.objects.order_by('id').filter(
            is_active=True, 
            fk_questionary__fk_product__fk_business__fk_user=request.user, 
            fk_questionary_id=selected_questionary_id
        )
        questionnaires = Questionary.objects.order_by('id').filter(
            is_active=True, 
            fk_product__in=products,
            fk_product__fk_business__fk_user=request.user
        )
        
        context = {
            'selected_questionary_id': selected_questionary_id,
            'questionary_result_id': questionary_result_id,
            'started_questionary': started_questionary,
            'questions': questions,
            'questionnaires': questionnaires,
        }
        return render(request, 'questionary/questionary-main.html', context)
    
    # Handle questionnaire start
    if request.method == 'POST' and 'start' in request.POST:
        request.session['started_questionary'] = True
        selected_questionary_id = request.session.get('selected_questionary_id')
        
        questionary_selected = Questionary.objects.get(pk=selected_questionary_id)
        questionary_result = QuestionaryResult.objects.create(
            fk_questionary=questionary_selected
        )
        questionary_result_id = questionary_result.id      
        request.session['questionary_result_id'] = questionary_result_id
        
        return redirect(reverse('questionary:questionary.main'))

    # Handle answer saving
    if request.method == 'POST' and 'save' in request.POST:
        selected_questionary_id = request.session.get('selected_questionary_id')
        questionary_result_id = request.session.get('questionary_result_id')
        
        # Save answers for type 3 questions (historical data)
        for key, value in request.POST.items():
            if key.startswith('historicalData_'):
                question_id = int(key.split('_')[1])
                historical_data = value
                
                question_instance = get_object_or_404(Question, pk=question_id)
                
                # Check if answer already exists
                existing_answer = Answer.objects.filter(
                    fk_question=question_instance,
                    fk_questionary_result_id=questionary_result_id
                ).first()
                
                if existing_answer:
                    existing_answer.answer = historical_data
                    existing_answer.last_updated = timezone.now()
                    existing_answer.save()
                else:
                    Answer.objects.create(
                        fk_question=question_instance,
                        answer=historical_data,
                        fk_questionary_result_id=questionary_result_id
                    )
        
        # Save other types of answers
        for key, value in request.POST.items():
            if key.startswith('question_') and not key.startswith('question_type_'):
                question_id = int(value)
                answer = request.POST.get(f'answer_{question_id}')
                
                if answer:  # Only save if answer is provided
                    question_instance = get_object_or_404(Question, pk=question_id)
                    
                    # Check if answer already exists
                    existing_answer = Answer.objects.filter(
                        fk_question=question_instance,
                        fk_questionary_result_id=questionary_result_id
                    ).first()
                    
                    if existing_answer:
                        existing_answer.answer = answer
                        existing_answer.last_updated = timezone.now()
                        existing_answer.save()
                    else:
                        Answer.objects.create(
                            fk_question=question_instance,
                            answer=answer,
                            fk_questionary_result_id=questionary_result_id
                        )
        
        # Handle pagination
        page_number = request.POST.get('current_page', 1)
        try:
            page_number = int(page_number)
        except:
            page_number = 1
            
        # Check if it's the last page
        if 'finish' in request.POST:
            request.session['started_questionary'] = False
            return redirect('questionary:questionary.result', pk=questionary_result_id)
        else:
            next_page = page_number + 1
            return redirect(reverse('questionary:questionary.main') + f'?page={next_page}')
    
    # Handle questionnaire cancellation
    if request.method == 'POST' and 'cancel' in request.POST:
        request.session['started_questionary'] = False
        request.session.pop('questionary_result_id', None)
        return redirect('questionary:questionary.main')
    
    # Display questionnaire
    if not started_questionary:
        questionnaires = Questionary.objects.order_by('id').filter(
            is_active=True, 
            fk_product__in=products, 
            fk_product__fk_business__fk_user=request.user
        )
        
        if selected_questionary_id:
            questions = Question.objects.order_by('id').filter(
                is_active=True, 
                fk_questionary__fk_product__fk_business__fk_user=request.user, 
                fk_questionary_id=selected_questionary_id
            )
            paginator = Paginator(questions, 10)
            page = request.GET.get('page')
            try:
                questions = paginator.page(page)
            except PageNotAnInteger:
                questions = paginator.page(1)
            except EmptyPage:
                questions = paginator.page(paginator.num_pages)
        
        context = {
            'selected_questionary_id': selected_questionary_id,
            'started_questionary': started_questionary,
            'questions': questions,
            'questionnaires': questionnaires,
        }
        return render(request, 'questionary/questionary-main.html', context)
    else:
        # Started questionnaire mode
        questionary_result_id = request.session.get('questionary_result_id')
        selected_questionary_id = request.session.get('selected_questionary_id')
        
        try:
            show_questionary = Questionary.objects.get(pk=selected_questionary_id)
        except ObjectDoesNotExist:
            show_questionary = None
            
        questions_to_answer = Question.objects.order_by('id').filter(
            is_active=True, 
            fk_questionary__fk_product__fk_business__fk_user=request.user, 
            fk_questionary_id=selected_questionary_id
        )
        
        questionnaires = Questionary.objects.order_by('id').filter(
            is_active=True, 
            fk_product__in=products, 
            fk_product__fk_business__fk_user=request.user
        )
        
        # Get existing answers
        existing_answers = {}
        if questionary_result_id:
            answers = Answer.objects.filter(
                fk_questionary_result_id=questionary_result_id,
                is_active=True
            )
            for answer in answers:
                existing_answers[answer.fk_question_id] = answer.answer
        
        paginator = Paginator(questions_to_answer, 5)
        page = request.GET.get('page', 1)
        
        try:
            questions_to_answer = paginator.page(page)
        except PageNotAnInteger:
            questions_to_answer = paginator.page(1)
        except EmptyPage:
            questions_to_answer = paginator.page(paginator.num_pages)

        context = {
            'selected_questionary_id': selected_questionary_id,
            'started_questionary': started_questionary,
            'questions_to_answer': questions_to_answer,
            'questionnaires': questionnaires,
            'show_questionary': show_questionary,
            'existing_answers': existing_answers,
            'questionary_result_id': questionary_result_id
        }   
        return render(request, 'questionary/questionary-main.html', context)

@login_required
@require_http_methods(["PUT"])
def questionnaire_update_view(request, result_id, answer_id):
    data = json.loads(request.body)
    new_answer = data.get('new_answer')

    try:
        answer_instance = get_object_or_404(Answer, id=answer_id, fk_questionary_result_id=result_id)
        answer_result_instance = get_object_or_404(QuestionaryResult, id=result_id)
        
        answer_result_instance.last_updated = timezone.now()
        answer_result_instance.save()
        
        answer_instance.answer = new_answer
        answer_instance.last_updated = timezone.now()
        answer_instance.save()

        return JsonResponse({'success': True, 'message': 'Respuesta actualizada exitosamente!'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'Error al actualizar la respuesta: ' + str(e)})

def process_answer(answer):
    if answer.fk_question.question == 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).':
        data_str = re.sub(r'<br\s*/?>', '\n', answer.answer)
        data_str = data_str.replace("[", "").replace("]", "").replace("'", "").replace(",", "")
        data_list = [float(value) for value in data_str.split() if value]
        return data_list
    return None

@login_required
def find_answer(request, answer_id):
    try:
        answer = Answer.objects.get(id=answer_id)
        processed_answer = process_answer(answer)

        if processed_answer:
            return JsonResponse({'success': True, 'message': 'Respuesta encontrada'})
        else:
            return JsonResponse({'success': False, 'message': 'Respuesta no encontrada para la pregunta específica'})
    except Answer.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Respuesta no encontrada'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'Error al buscar la respuesta: ' + str(e)})

@login_required
def questionnaire_result_view(request, pk):
    try:
        questionary_result = get_object_or_404(QuestionaryResult, pk=pk)
        answers = Answer.objects.filter(
            fk_questionary_result=questionary_result, 
            is_active=True,
        ).select_related('fk_question', 'fk_question__fk_variable')
        
        paginator = Paginator(answers, 40)
        page = request.GET.get('page')
        answers = paginator.get_page(page)

        processed_answers = []
        for answer in answers:
            if answer.fk_question.question == 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).':
                processed_data = process_answer(answer)
                processed_answers.append({
                    'answer_id': answer.id,
                    'data': processed_data
                })

        context = {
            'questionary_result': questionary_result, 
            'answers': answers, 
            'processed_answers': processed_answers
        }
        return render(request, 'questionary/questionary-result.html', context)
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)

@login_required
def questionary_list_view(request):
    try:
        businessess = Business.objects.filter(is_active=True, fk_user=request.user)
        products = Product.objects.filter(
            is_active=True,
            fk_business__in=businessess, 
            fk_business__fk_user=request.user
        )
        questionary_results = QuestionaryResult.objects.filter(
            is_active=True,
            fk_questionary__fk_product__in=products, 
            fk_questionary__fk_product__fk_business__fk_user=request.user
        ).order_by('-id').select_related('fk_questionary', 'fk_questionary__fk_product')
        
        paginator = Paginator(questionary_results, 20)
        page = request.GET.get('page')
        questionary_results = paginator.get_page(page)
        
        context = {'questionary_results': questionary_results}
        return render(request, 'questionary/questionary-list.html', context)
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)

# NEW: Edit questionnaire result view
@login_required
def questionnaire_edit_view(request, pk):
    """View to edit an existing questionnaire result"""
    questionary_result = get_object_or_404(QuestionaryResult, pk=pk)
    
    # Verify user has permission to edit
    if questionary_result.fk_questionary.fk_product.fk_business.fk_user != request.user:
        return HttpResponseForbidden("No tienes permiso para editar este cuestionario.")
    
    if request.method == 'POST':
        # Update answers
        for key, value in request.POST.items():
            if key.startswith('answer_'):
                answer_id = int(key.replace('answer_', ''))
                try:
                    answer = Answer.objects.get(
                        id=answer_id, 
                        fk_questionary_result=questionary_result
                    )
                    answer.answer = value
                    answer.last_updated = timezone.now()
                    answer.save()
                except Answer.DoesNotExist:
                    pass
        
        questionary_result.last_updated = timezone.now()
        questionary_result.save()
        
        messages.success(request, "Cuestionario actualizado exitosamente.")
        return redirect('questionary:questionary.result', pk=pk)
    
    # GET request - show edit form
    answers = Answer.objects.filter(
        fk_questionary_result=questionary_result,
        is_active=True
    ).select_related('fk_question', 'fk_question__fk_variable').order_by('fk_question__id')
    
    context = {
        'questionary_result': questionary_result,
        'answers': answers
    }
    return render(request, 'questionary/questionary-edit.html', context)

# NEW: Delete questionnaire result view
@login_required
def questionnaire_delete_view(request, pk):
    """View to delete a questionnaire result"""
    questionary_result = get_object_or_404(QuestionaryResult, pk=pk)
    
    # Verify user has permission to delete
    if questionary_result.fk_questionary.fk_product.fk_business.fk_user != request.user:
        return HttpResponseForbidden("No tienes permiso para eliminar este cuestionario.")
    
    if request.method == 'POST':
        # Soft delete
        questionary_result.is_active = False
        questionary_result.save()
        
        # Also soft delete related answers
        Answer.objects.filter(fk_questionary_result=questionary_result).update(is_active=False)
        
        messages.success(request, "Cuestionario eliminado exitosamente.")
        return redirect('questionary:questionary.list')
    
    context = {
        'questionary_result': questionary_result
    }
    return render(request, 'questionary/questionary-delete-confirm.html', context)