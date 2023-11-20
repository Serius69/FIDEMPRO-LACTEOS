from django.urls import path
from simulate.views import(
    simulate_init
)
app_name = 'simulate'

urlpatterns = [
    path("init", view=simulate_init, name="simulate.init"),
]
