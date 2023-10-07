from django.urls import path
from . import views

urlpatterns = [
     # Variables
    path("variables/list", view=apps_variables_list, name="variables.list"),
    path("variables/overview/<int:pk>", view=apps_variables_overview, name="variables.overview"),
    ]
