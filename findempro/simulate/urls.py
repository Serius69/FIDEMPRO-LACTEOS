from django.urls import path
from . import views

urlpatterns = [
        # Simualte
    path("simulate/init", view=apps_simulate_init, name="simulate.init"),
]
