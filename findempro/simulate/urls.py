from django.urls import path
from simulate.views import(
    simulate_show_view,
    simulate_result_simulation_view    
)
app_name = 'simulate'

urlpatterns = [
    path("init", view=simulate_show_view, name="simulate.show"),
    path("result/<int:simulation_id>/", view=simulate_result_simulation_view, name="simulate.result"),
]
