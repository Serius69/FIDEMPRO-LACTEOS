from django.urls import path, include
from .views import(
    # generate_questions_for_variables,
    questionnaire_list_view,
    questionnaire_save_view
)
app_name = 'questionary'

urlpatterns = [
    # Questions
    path('questionary/', view=questionnaire_list_view, name='question.list'),
    path('save/', view=questionnaire_save_view, name='questionary.save'),
    # path('report/overview', view=generate_questions_for_variables, name='report.overview'),

]
