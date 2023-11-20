from django.urls import path, include
from .views import(
    # generate_questions_for_variables,
    questionnaire_list_view,
    questionnaire_save_view,
    show_question
)
app_name = 'questionary'

urlpatterns = [
    # Questions
    path('questionary/', view=questionnaire_list_view, name='questionary.list'),
    path('save/', view=questionnaire_save_view, name='questionary.save'),
    path('question/<int:pk>/', view=show_question, name='question')
    # path('report/overview', view=generate_questions_for_variables, name='report.overview'),

]
