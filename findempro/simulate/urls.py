from django.urls import path
from simulate.views import(
    simulate_show_form,
    simulate_init
)
app_name = 'simulate'

urlpatterns = [
        # Simulate
    path("init", view=simulate_show_form, name="simulate.show"),
    path("show", view=simulate_init, name="simulate.init"),
]
