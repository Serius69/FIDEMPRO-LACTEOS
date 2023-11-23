from django.urls import path, include
from .views import(
    # generate_questions_for_variables,
    questionnaire_list_view,
    questionnaire_save_view,questionnaire_result_view
)
app_name = 'questionary'

urlpatterns = [
    # Questions
    path('list/', view=questionnaire_list_view, name='questionary.list'),
    path('question/', view=questionnaire_save_view, name='questionary.save'),
    path('result/<int:pk>/', view=questionnaire_result_view, name='questionary.result'),
    # path('report/overview', view=generate_questions_for_variables, name='report.overview'),

]
