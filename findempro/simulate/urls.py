# urls.py
from django.urls import path
from .views.simulation_views import (
    SimulateListView,
    simulate_show_view,
    simulate_result_simulation_view,
    simulate_add_view,
    AppsView
)
from .views.api_views import (
    SimulationProgressView,
    SimulationRetryView,
    SimulationDuplicateView,
    SimulationStartView,
    SimulationDeleteView
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
    
    # API endpoints
    path("api/progress/<int:simulation_id>/", view=SimulationProgressView.as_view(), name="api.progress"),
    path("api/retry/<int:simulation_id>/", view=SimulationRetryView.as_view(), name="api.retry"),
    path("api/duplicate/<int:simulation_id>/", view=SimulationDuplicateView.as_view(), name="api.duplicate"),
    path("api/start/<int:simulation_id>/", view=SimulationStartView.as_view(), name="api.start"),
    path("api/delete/<int:simulation_id>/", view=SimulationDeleteView.as_view(), name="api.delete"),
]