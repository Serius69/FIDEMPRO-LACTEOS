from django.urls import path
from variable.views import(
    variable_list,
    variable_overview,
    create_variable_view,
    update_variable_view
)
app_name = 'variable'

urlpatterns = [
    # Companies
    path("list", view=variable_list, name="variable.list"),
    path("overview/<int:pk>", view=variable_overview, name="variable.overview"),
    path("new/", view=create_variable_view, name='variable.create'),
    path("edit/", view=update_variable_view, name='variable.edit'),
]
