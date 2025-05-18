from django.urls import path, include
from .views import(
    questionnaire_main_view,
    questionnaire_update_view,
    questionnaire_result_view,
    questionary_list_view
)
app_name = 'questionary'

urlpatterns = [
    # Questions
    path('main/', view=questionnaire_main_view, name='questionary.main'),
    path('result/<int:result_id>/questionary/update_question_view/<int:answer_id>/', questionnaire_update_view, name='questionary.update'),
    path('list/', view=questionary_list_view, name='questionary.list'),

    path('/update_question_view/', view=questionnaire_update_view, name='questionary.save'),
    path('result/<int:pk>/', view=questionnaire_result_view, name='questionary.result'),

]
