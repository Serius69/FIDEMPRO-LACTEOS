from django.urls import path
from simulate.views import(
    simulate_init
)

urlpatterns = [
        # Simulate
    path("simulate/init", view=simulate_init, name="simulate.init"),
]
