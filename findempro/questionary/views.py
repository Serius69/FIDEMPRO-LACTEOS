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
        try:
            selected_questionary_id = int(selected_questionary_id)
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
            
            paginator = Paginator(questions, 10)
            page = request.GET.get('page', 1)
            try:
                questions = paginator.page(page)
            except PageNotAnInteger:
                questions = paginator.page(1)
            except EmptyPage:
                questions = paginator.page(paginator.num_pages)
            
            context = {
                'selected_questionary_id': selected_questionary_id,
                'questionary_result_id': questionary_result_id,
                'started_questionary': started_questionary,
                'questions': questions,
                'questionnaires': questionnaires,
            }
            return render(request, 'questionary/questionary-main.html', context)
        except (ValueError, TypeError):
            messages.error(request, "ID de cuestionario inválido.")
            return redirect('questionary:questionary.main')
    
    # Handle questionnaire start
    if request.method == 'POST' and 'start' in request.POST:
        # Obtener el ID desde POST o desde session
        selected_questionary_id = request.POST.get('selected_questionary_id') or request.session.get('selected_questionary_id')
        
        if not selected_questionary_id:
            messages.error(request, "Debe seleccionar un cuestionario primero.")
            return redirect('questionary:questionary.main')
        
        try:
            # Convertir a entero y actualizar session
            selected_questionary_id = int(selected_questionary_id)
            request.session['selected_questionary_id'] = selected_questionary_id
            
            questionary_selected = Questionary.objects.get(
                pk=selected_questionary_id,
                is_active=True,
                fk_product__fk_business__fk_user=request.user
            )
            
            # Create new questionary result
            questionary_result = QuestionaryResult.objects.create(
                fk_questionary=questionary_selected
            )
            
            # Update session
            request.session['started_questionary'] = True
            request.session['questionary_result_id'] = questionary_result.id
            
            messages.success(request, f"Cuestionario '{questionary_selected.questionary}' iniciado correctamente.")
            return redirect('questionary:questionary.main')
            
        except (ValueError, TypeError):
            messages.error(request, "ID de cuestionario inválido.")
            return redirect('questionary:questionary.main')
        except Questionary.DoesNotExist:
            messages.error(request, "El cuestionario seleccionado no existe o no tiene permisos para acceder.")
            return redirect('questionary:questionary.main')
        except Exception as e:
            messages.error(request, f"Error al iniciar el cuestionario: {str(e)}")
            return redirect('questionary:questionary.main')

    # Handle answer saving
    if request.method == 'POST' and 'save' in request.POST:
        selected_questionary_id = request.session.get('selected_questionary_id')
        questionary_result_id = request.session.get('questionary_result_id')
        
        if not questionary_result_id:
            messages.error(request, "No hay un cuestionario activo.")
            return redirect('questionary:questionary.main')
        
        saved_count = 0
        
        try:
            # Save answers for type 3 questions (historical data)
            for key, value in request.POST.items():
                if key.startswith('historicalData_'):
                    question_id = int(key.split('_')[1])
                    historical_data = value
                    
                    if historical_data.strip():  # Only save if data exists
                        question_instance = get_object_or_404(
                            Question, 
                            pk=question_id,
                            fk_questionary__fk_product__fk_business__fk_user=request.user
                        )
                        
                        # Validate historical data
                        try:
                            data_values = [float(x.strip()) for x in historical_data.split(',') if x.strip()]
                            if len(data_values) < 30:
                                messages.warning(request, f"Datos históricos insuficientes para la pregunta {question_id}. Se requieren al menos 30 valores.")
                                continue
                        except ValueError:
                            messages.warning(request, f"Formato inválido en datos históricos para la pregunta {question_id}.")
                            continue
                        
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
                        saved_count += 1
            
            # Save other types of answers
            for key, value in request.POST.items():
                if key.startswith('question_') and not key.startswith('question_type_'):
                    question_id = int(value)
                    answer_key = f'answer_{question_id}'
                    answer = request.POST.get(answer_key)
                    
                    if answer and answer.strip():  # Only save if answer is provided
                        try:
                            question_instance = get_object_or_404(
                                Question, 
                                pk=question_id,
                                fk_questionary__fk_product__fk_business__fk_user=request.user
                            )
                            
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
                            saved_count += 1
                        except Exception as e:
                            messages.warning(request, f"Error al guardar respuesta para pregunta {question_id}: {str(e)}")
            
            # Update questionary result timestamp
            if questionary_result_id:
                questionary_result = QuestionaryResult.objects.get(pk=questionary_result_id)
                questionary_result.last_updated = timezone.now()
                questionary_result.save()
            
            if saved_count > 0:
                messages.success(request, f"Se guardaron {saved_count} respuestas correctamente.")
            else:
                messages.warning(request, "No se encontraron respuestas válidas para guardar.")
            
            # Handle pagination
            page_number = request.POST.get('current_page', 1)
            try:
                page_number = int(page_number)
            except:
                page_number = 1
                
            # Check if it's the last page
            if 'finish' in request.POST:
                request.session['started_questionary'] = False
                messages.success(request, "Cuestionario finalizado correctamente.")
                return redirect('questionary:questionary.result', pk=questionary_result_id)
            else:
                next_page = page_number + 1
                return redirect(reverse('questionary:questionary.main') + f'?page={next_page}')
                
        except Exception as e:
            messages.error(request, f"Error al guardar respuestas: {str(e)}")
            return redirect('questionary:questionary.main')
    
    # Handle questionnaire cancellation
    if request.method == 'POST' and 'cancel' in request.POST:
        questionary_result_id = request.session.get('questionary_result_id')
        
        # Mark questionary as inactive instead of deleting
        if questionary_result_id:
            try:
                questionary_result = QuestionaryResult.objects.get(pk=questionary_result_id)
                questionary_result.is_active = False
                questionary_result.save()
                
                # Also deactivate related answers
                Answer.objects.filter(fk_questionary_result_id=questionary_result_id).update(is_active=False)
                
                messages.info(request, "Cuestionario cancelado. Los datos se han guardado como borrador.")
            except QuestionaryResult.DoesNotExist:
                pass
        
        # Clear session
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
            
            if questions.exists():
                paginator = Paginator(questions, 10)
                page = request.GET.get('page', 1)
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
            show_questionary = Questionary.objects.get(
                pk=selected_questionary_id,
                fk_product__fk_business__fk_user=request.user
            )
        except ObjectDoesNotExist:
            messages.error(request, "El cuestionario no existe.")
            request.session['started_questionary'] = False
            return redirect('questionary:questionary.main')
            
        questions_to_answer = Question.objects.order_by('id').filter(
            is_active=True, 
            fk_questionary__fk_product__fk_business__fk_user=request.user, 
            fk_questionary_id=selected_questionary_id
        )
        
        if not questions_to_answer.exists():
            messages.warning(request, "Este cuestionario no tiene preguntas configuradas.")
            request.session['started_questionary'] = False
            return redirect('questionary:questionary.main')
        
        questionnaires = Questionary.objects.order_by('id').filter(
            is_active=True, 
            fk_product__in=products, 
            fk_product__fk_business__fk_user=request.user
        )
        
        # Get existing answers as dictionary for template
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
    try:
        data = json.loads(request.body)
        new_answer = data.get('new_answer')

        # Verify permissions
        answer_instance = get_object_or_404(
            Answer, 
            id=answer_id, 
            fk_questionary_result_id=result_id,
            fk_questionary_result__fk_questionary__fk_product__fk_business__fk_user=request.user
        )
        answer_result_instance = get_object_or_404(
            QuestionaryResult, 
            id=result_id,
            fk_questionary__fk_product__fk_business__fk_user=request.user
        )
        
        # Validate new answer
        if not new_answer or not str(new_answer).strip():
            return JsonResponse({'success': False, 'message': 'La respuesta no puede estar vacía.'})
        
        # Update answer
        answer_instance.answer = str(new_answer).strip()
        answer_instance.last_updated = timezone.now()
        answer_instance.save()
        
        # Update result timestamp
        answer_result_instance.last_updated = timezone.now()
        answer_result_instance.save()

        return JsonResponse({
            'success': True, 
            'message': 'Respuesta actualizada exitosamente!',
            'answer': answer_instance.answer,
            'last_updated': answer_instance.last_updated.strftime('%d/%m/%Y %H:%M')
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Formato de datos inválido.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error al actualizar la respuesta: {str(e)}'})

def process_answer(answer):
    """Process historical data answer"""
    if answer.fk_question.question == 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).':
        try:
            data_str = re.sub(r'<br\s*/?>', '\n', answer.answer)
            data_str = data_str.replace("[", "").replace("]", "").replace("'", "").replace(",", " ")
            data_list = [float(value) for value in data_str.split() if value.strip()]
            return data_list
        except (ValueError, AttributeError):
            return None
    return None

@login_required
def find_answer(request, answer_id):
    try:
        answer = get_object_or_404(
            Answer, 
            id=answer_id,
            fk_questionary_result__fk_questionary__fk_product__fk_business__fk_user=request.user
        )
        processed_answer = process_answer(answer)

        if processed_answer:
            return JsonResponse({
                'success': True, 
                'message': 'Respuesta encontrada',
                'data': processed_answer,
                'count': len(processed_answer)
            })
        else:
            return JsonResponse({'success': False, 'message': 'Respuesta no encontrada para la pregunta específica'})
    except Answer.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Respuesta no encontrada'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error al buscar la respuesta: {str(e)}'})

@login_required
def questionnaire_result_view(request, pk):
    try:
        questionary_result = get_object_or_404(
            QuestionaryResult, 
            pk=pk,
            fk_questionary__fk_product__fk_business__fk_user=request.user
        )
        answers = Answer.objects.filter(
            fk_questionary_result=questionary_result, 
            is_active=True,
        ).select_related('fk_question', 'fk_question__fk_variable').order_by('fk_question__id')
        
        paginator = Paginator(answers, 40)
        page = request.GET.get('page')
        answers = paginator.get_page(page)

        processed_answers = []
        for answer in answers:
            if 'datos históricos' in answer.fk_question.question.lower() or \
               answer.fk_question.question == 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).':
                processed_data = process_answer(answer)
                if processed_data:
                    # Calculate statistics
                    data_sum = sum(processed_data)
                    data_avg = data_sum / len(processed_data) if processed_data else 0
                    data_min = min(processed_data) if processed_data else 0
                    data_max = max(processed_data) if processed_data else 0
                    
                    processed_answers.append({
                        'answer_id': answer.id,
                        'data': processed_data,
                        'statistics': {
                            'count': len(processed_data),
                            'sum': data_sum,
                            'average': data_avg,
                            'min': data_min,
                            'max': data_max,
                            'range': data_max - data_min
                        }
                    })

        context = {
            'questionary_result': questionary_result, 
            'answers': answers, 
            'processed_answers': processed_answers
        }
        return render(request, 'questionary/questionary-result.html', context)
    except Exception as e:
        messages.error(request, f"Error al cargar el resultado: {str(e)}")
        return redirect('questionary:questionary.list')

@login_required
def questionary_list_view(request):
    try:
        businessess = Business.objects.filter(is_active=True, fk_user=request.user)
        products = Product.objects.filter(
            is_active=True,
            fk_business__in=businessess, 
            fk_business__fk_user=request.user
        )
        
        # Get search and filter parameters
        search_query = request.GET.get('search', '').strip()
        status_filter = request.GET.get('status', 'all')
        
        questionary_results = QuestionaryResult.objects.filter(
            fk_questionary__fk_product__in=products, 
            fk_questionary__fk_product__fk_business__fk_user=request.user
        ).select_related('fk_questionary', 'fk_questionary__fk_product')
        
        # Apply status filter
        if status_filter == 'active':
            questionary_results = questionary_results.filter(is_active=True)
        elif status_filter == 'inactive':
            questionary_results = questionary_results.filter(is_active=False)
        
        # Apply search filter
        if search_query:
            questionary_results = questionary_results.filter(
                fk_questionary__questionary__icontains=search_query
            ) | questionary_results.filter(
                fk_questionary__fk_product__name__icontains=search_query
            )
        
        questionary_results = questionary_results.order_by('-last_updated')
        
        paginator = Paginator(questionary_results, 20)
        page = request.GET.get('page')
        questionary_results = paginator.get_page(page)
        
        context = {
            'questionary_results': questionary_results,
            'search_query': search_query,
            'status_filter': status_filter
        }
        return render(request, 'questionary/questionary-list.html', context)
    except Exception as e:
        messages.error(request, f"Error al cargar la lista: {str(e)}")
        return HttpResponse(status=500)

@login_required
def questionnaire_edit_view(request, pk):
    """View to edit an existing questionnaire result"""
    try:
        questionary_result = get_object_or_404(
            QuestionaryResult, 
            pk=pk,
            fk_questionary__fk_product__fk_business__fk_user=request.user
        )
    except QuestionaryResult.DoesNotExist:
        messages.error(request, "El cuestionario no existe o no tiene permisos para editarlo.")
        return redirect('questionary:questionary.list')
    
    if request.method == 'POST':
        updated_count = 0
        try:
            # Update answers
            for key, value in request.POST.items():
                if key.startswith('answer_'):
                    answer_id = int(key.replace('answer_', ''))
                    try:
                        answer = Answer.objects.get(
                            id=answer_id, 
                            fk_questionary_result=questionary_result
                        )
                        if value.strip() and value.strip() != answer.answer:
                            answer.answer = value.strip()
                            answer.last_updated = timezone.now()
                            answer.save()
                            updated_count += 1
                    except Answer.DoesNotExist:
                        messages.warning(request, f"Respuesta con ID {answer_id} no encontrada.")
                        continue
            
            if updated_count > 0:
                questionary_result.last_updated = timezone.now()
                questionary_result.save()
                messages.success(request, f"Se actualizaron {updated_count} respuestas exitosamente.")
            else:
                messages.info(request, "No se detectaron cambios para guardar.")
            
            return redirect('questionary:questionary.result', pk=pk)
            
        except Exception as e:
            messages.error(request, f"Error al actualizar el cuestionario: {str(e)}")
    
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

@login_required
def questionnaire_delete_view(request, pk):
    """View to delete a questionnaire result"""
    try:
        questionary_result = get_object_or_404(
            QuestionaryResult, 
            pk=pk,
            fk_questionary__fk_product__fk_business__fk_user=request.user
        )
    except QuestionaryResult.DoesNotExist:
        messages.error(request, "El cuestionario no existe o no tiene permisos para eliminarlo.")
        return redirect('questionary:questionary.list')
    
    if request.method == 'POST':
        try:
            # Soft delete
            questionary_result.is_active = False
            questionary_result.last_updated = timezone.now()
            questionary_result.save()
            
            # Also soft delete related answers
            Answer.objects.filter(fk_questionary_result=questionary_result).update(
                is_active=False,
                last_updated=timezone.now()
            )
            
            messages.success(request, "Cuestionario eliminado exitosamente.")
            return redirect('questionary:questionary.list')
            
        except Exception as e:
            messages.error(request, f"Error al eliminar el cuestionario: {str(e)}")
    
    context = {
        'questionary_result': questionary_result
    }
    return render(request, 'questionary/questionary-delete-confirm.html', context)