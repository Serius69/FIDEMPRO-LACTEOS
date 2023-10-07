from django.urls import path, include
from variable.views import(
    variable_list,
    variable_overview,
)

urlpatterns = [
    # Companies
    path("company/list", view=variable_list, name="company.list"),
    path("company/overview/<int:pk>", view=variable_overview, name="company.overview"),

]
