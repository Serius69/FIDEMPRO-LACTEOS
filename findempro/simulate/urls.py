# urls.py
from django.urls import path
from .views.simulation_views import (
    SimulateListView,
    simulate_show_view,
    simulate_result_simulation_view,
    simulate_add_view,
    AppsView
)

app_name = 'simulate'

urlpatterns = [
    # Main simulation views
    path("", view=AppsView.as_view(), name="simulate.index"),
    path("init/", view=simulate_show_view, name="simulate.show"),
    path("add/", view=simulate_add_view, name="simulate.add"),
    path("result/<int:simulation_id>/", view=simulate_result_simulation_view, name="simulate.result"),
    path("result/<int:simulation_id>/edit/", view=simulate_add_view, name="simulate.edit"),
    path("result/<int:simulation_id>/delete/", view=simulate_add_view, name="simulate.delete"),
    path("result/<int:simulation_id>/view/", view=simulate_result_simulation_view, name="simulate.view"),
    path("list/", view=SimulateListView.as_view(), name="simulate.list"),
    # Additional endpoints for future expansion
    # path("api/validate/", view=validate_simulation_data, name="simulate.validate"),
    # path("api/charts/<int:simulation_id>/", view=get_simulation_charts, name="simulate.charts"),
    # path("export/<int:simulation_id>/", view=export_simulation_results, name="simulate.export"),
]