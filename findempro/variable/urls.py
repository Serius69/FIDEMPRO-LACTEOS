from django.urls import path, include
from variable.views import(
    variable_list,
    variable_overview,
    generate_questions
)
app_name = 'variable'

urlpatterns = [
    # Companies
    path("list", view=variable_list, name="variable.list"),
    path("overview/<int:pk>", view=variable_overview, name="variable.overview"),
    path('generate-questions/', views=generate_questions, name='generate_questions'),

]
