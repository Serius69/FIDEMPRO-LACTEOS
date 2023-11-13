from django.urls import path, include
from .views import(
    # generate_questions_for_variables,
    questionnaire_list
)
app_name = 'questionary'

urlpatterns = [
    # Questions
    path('questionary/', view=questionnaire_list, name='question.list'),
    # path('report/overview', view=generate_questions_for_variables, name='report.overview'),

]
