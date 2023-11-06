from django.urls import path, include
from .views import(
    generate_questions_for_variables
)
app_name = 'questionary'

urlpatterns = [
    # Questions
    path('questionary/', view=generate_questions_for_variables, name='question.list'),
    path('report/overview', view=generate_questions_for_variables, name='report.overview'),

]
