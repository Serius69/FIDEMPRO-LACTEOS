from django.urls import path, include
from variable.views import(
    variable_list,
    variable_overview
)
app_name = 'variable'

urlpatterns = [
    # Companies
    path("list", view=variable_list, name="variable.list"),
    path("overview/<int:pk>", view=variable_overview, name="variable.overview"),

]
