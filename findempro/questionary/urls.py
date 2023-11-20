from django.urls import path, include
from .views import(
    # generate_questions_for_variables,
    questionnaire_list_view,
    questionnaire_save_view
)
app_name = 'questionary'

urlpatterns = [
    # Questions
    path('list/', view=questionnaire_list_view, name='questionary.list'),
    path('question/', view=questionnaire_save_view, name='question.save'),
    # path('report/overview', view=generate_questions_for_variables, name='report.overview'),

]
