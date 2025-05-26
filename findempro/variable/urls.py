from django.urls import path
from variable.views import (
    variable_list,
    variable_overview,
    create_or_update_variable_view,
    delete_variable_view,
    get_variable_details_view,
    create_or_update_equation_view,
    delete_equation_view,
    get_equation_details,
    solve_equation,
    generate_questions_for_variables
)

app_name = 'variable'

urlpatterns = [
    # Variables
    path("list/", view=variable_list, name="variable.list"),
    path("overview/<int:pk>/", view=variable_overview, name="variable.overview"),
    path("create/", create_or_update_variable_view, name='variable.create'),
    path("<int:pk>/update/", view=create_or_update_variable_view, name='variable.edit'),
    path("delete/<int:pk>/", view=delete_variable_view, name='variable.delete'),
    path('get_details/<int:pk>/', view=get_variable_details_view, name='variable.get_details'),
    
    # Equations
    path("equation/create/", create_or_update_equation_view, name='equation.create'),
    path("equation/<int:pk>/update/", view=create_or_update_equation_view, name='equation.edit'),
    path("equation/delete/<int:pk>/", view=delete_equation_view, name='equation.delete'),
    path("equation/get_details/<int:pk>/", view=get_equation_details, name='equation.get_details'),
    
    # Additional features
    path("solve/", view=solve_equation, name='equation.solve'),
    path("questions/", view=generate_questions_for_variables, name='variable.questions'),
]