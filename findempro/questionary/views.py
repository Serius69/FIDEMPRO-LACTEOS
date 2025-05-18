import json
from pyexpat.errors import messages
from django.shortcuts import render, get_object_or_404, redirect
from variable.models import Variable
from django.contrib.auth.decorators import login_required
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
from django.utils import timezone
import re

"""
View function to handle the main questionnaire page.
This function manages the display and interaction with questionnaires, including:
- Selecting a questionnaire.
- Starting a questionnaire.
- Saving answers to questions.
- Cancelling a questionnaire.
It handles GET and POST requests to perform the following actions:
1. GET request with 'select' parameter:
    - Sets the selected questionnaire ID in the session.
    - Retrieves questions and questionnaires associated with the selected questionnaire.
    - Renders the main questionnaire page with the context.
2. POST request with 'start' parameter:
    - Marks the questionnaire as started in the session.
    - Creates a new `QuestionaryResult` instance for the selected questionnaire.
    - Redirects to the main questionnaire page.
3. POST request with 'save' parameter:
    - Saves answers to questions in the database.
    - Handles pagination for questions.
    - Redirects to the main questionnaire page with the current page number.
4. POST request with 'cancel' parameter:
    - Cancels the questionnaire and resets the session variable.
    - Redirects to the main questionnaire page.
5. Default behavior:
    - Displays the list of questionnaires and questions based on the user's session state.
    - Handles pagination for displaying questions.
Context variables passed to the template:
- `selected_questionary_id`: ID of the selected questionnaire.
- `started_questionary`: Boolean indicating if a questionnaire has been started.
- `questions`: List of questions for the selected questionnaire.
- `questionnaires`: List of available questionnaires.
- `questionary_result_id`: ID of the current questionnaire result (if applicable).
- `questions_to_answer`: Paginated list of questions to answer (if applicable).
- `show_questionary`: The selected questionnaire instance (if applicable).
Template:
- Renders the `questionary/questionary-main.html` template with the provided context.
Session Variables:
- `selected_questionary_id`: Stores the ID of the selected questionnaire.
- `started_questionary`: Indicates if a questionnaire has been started.
- `questionary_result_id`: Stores the ID of the current questionnaire result.
Exceptions:
- Handles `ObjectDoesNotExist` when retrieving a questionnaire that does not exist.
- Handles pagination errors such as `PageNotAnInteger` and `EmptyPage`.
Dependencies:
- `Business`, `Product`, `Question`, `Questionary`, `QuestionaryResult`, and `Answer` models.
- Django's `Paginator`, `get_object_or_404`, `redirect`, `reverse`, and `render` utilities.
"""
class AppsView(LoginRequiredMixin,TemplateView):
    pass
@login_required
def questionnaire_main_view(request):
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
        return render(request,'questionary/questionary-main.html',context)
    
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
        return redirect(reverse('questionary:questionary.main'))

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
        return redirect(reverse('questionary:questionary.main') + f'?page={next_page.number}')
        # return redirect(reverse('questionary:questionary.main'))
    
    if request.method == 'POST' and 'cancel' in request.POST:
        request.session['started_questionary'] = False
        print("Se cancelo el cuestionario")        
        return redirect('questionary:questionary.main')
       
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
        return render(request,'questionary/questionary-main.html',context)
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
        return render(request, 'questionary/questionary-main.html', context)

@login_required
def questionnaire_update_view(request):
    if request.method == 'PUT':
        data = json.loads(request.body)
        answer_id = data.get('answer_id')
        new_answer = data.get('new_answer')

        try:
            answer_instance = get_object_or_404(Answer, id=answer_id)
            answer_instance.answer = new_answer
            answer_instance.save()

            return JsonResponse({'success': True, 'message': 'Respuesta actualizada exitosamente!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'Error al actualizar la respuesta: ' + str(e)})

    return JsonResponse({'success': False, 'message': 'Método no permitido'})

def process_answer(answer):
    if answer.fk_question.question == 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).':
        data_str = re.sub(r'<br\s*/?>', '\n', answer.answer)
        data_str = data_str.replace("[", "").replace("]", "").replace("'", "").replace(",", "")
        data_list = [float(value) for value in data_str.split()]
        return data_list
    return None
def find_answer(request, answer_id):
    # try:
        answer = Answer.objects.get(id=answer_id)
        processed_answer = process_answer(answer)

        if processed_answer:
            return JsonResponse({'success': True, 'message': 'Respuesta encontrada'})
        else:
            return JsonResponse({'success': False, 'message': 'Respuesta no encontrada para la pregunta específica'})

    # except Answer.DoesNotExist:
    #     return JsonResponse({'success': False, 'message': 'Respuesta no encontrada'})
    # except Exception as e:
    #     return JsonResponse({'success': False, 'message': 'Error al buscar la respuesta: ' + str(e)})
@login_required
def questionnaire_result_view(request, pk):
    # try:
        questionary_result = get_object_or_404(QuestionaryResult, pk=pk)
        answers = Answer.objects.filter(
            fk_questionary_result=questionary_result, 
            is_active=True,
        )
        paginator = Paginator(answers, 40)
        page = request.GET.get('page')
        answers = paginator.get_page(page)

        processed_answers = [process_answer(answer) for answer in answers]

        context = {'questionary_result': questionary_result, 'answers': answers, 'processed_answers': processed_answers}
        return render(request, 'questionary/questionary-result.html', context)
        
    # except Exception as e:
    #     messages.error(request, "An error occurred. Please check the server logs for more information: " + str(e))
    #     return HttpResponse(status=500)


 
def questionnaire_update_view(request, result_id, answer_id):
    if request.method == 'PUT':
        data = json.loads(request.body)
        print('Data:', data)
        answer_id = data.get('answerId')
        result_id = data.get('resultId')
        new_answer = data.get('new_answer')

        try:
            answer_instance = get_object_or_404(Answer, id=answer_id, fk_questionary_result_id=result_id)
            print('Answer ID:', answer_id)
            print('New Answer:', new_answer)
            answer_result_instance = get_object_or_404(QuestionaryResult, id=result_id)
            answer_result_instance.last_updated = timezone.now()  # Update the last_updated field with the current time
            answer_instance.answer = new_answer
            answer_instance.last_updated = timezone.now()  # Update the last_updated field with the current time
            answer_instance.save()

            return JsonResponse({'success': True, 'message': 'Respuesta actualizada exitosamente!'})
        except Exception as e:
            print('Error:', e)
            return JsonResponse({'success': False, 'message': 'Error al actualizar la respuesta: ' + str(e)})

    return JsonResponse({'success': False, 'message': 'Método no permitido'})
def questionary_list_view(request):
    try:
        businessess = Business.objects.filter(is_active=True, fk_user=request.user)
        products = Product.objects.filter(is_active=True,fk_business__in=businessess, fk_business__fk_user=request.user)
        questionary_results = QuestionaryResult.objects.filter(is_active=True,fk_questionary__fk_product__in=products  , fk_questionary__fk_product__fk_business__fk_user=request.user).order_by('-id')
        
        context = {'questionary_results': questionary_results}
        return render(request, 'questionary/questionary-list.html', context)
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)