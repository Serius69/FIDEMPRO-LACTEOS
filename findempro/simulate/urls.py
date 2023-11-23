from django.urls import path
from simulate.views import(
    simulate_init_view,
    simulate_result_simulation_view    
)
app_name = 'simulate'

urlpatterns = [
    path("init", view=simulate_init_view, name="simulate.init"),
    path("result", view=simulate_result_simulation_view, name="simulate.result"),
]
