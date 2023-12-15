from django.urls import path
from simulate.views import(
    simulate_show_view,
    simulate_result_simulation_view   , simulate_add_view
)
app_name = 'simulate'

urlpatterns = [
    path("init", view=simulate_show_view, name="simulate.show"),
    path("add", view=simulate_add_view, name="simulate.add"),
    path("result/<int:simulation_id>/", view=simulate_result_simulation_view, name="simulate.result"),
]
