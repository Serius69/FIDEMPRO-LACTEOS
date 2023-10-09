from django.urls import path, include
from question.views import(
    generate_questions_for_variables
)
app_name = 'question'

urlpatterns = [
    # Questions
    path('questionary/', view=generate_questions_for_variables, name='question.list'),

]
