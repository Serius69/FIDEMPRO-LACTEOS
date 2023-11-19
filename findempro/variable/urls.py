from django.urls import path
from variable.views import(
    variable_list,
    variable_overview,
    create_variable_view,
    update_variable_view,
    delete_variable_view,
    get_variable_details
)
app_name = 'variable'

urlpatterns = [
    # Companies
    path("list", view=variable_list, name="variable.list"),
    path("overview/<int:pk>", view=variable_overview, name="variable.overview"),
    path("create/", create_variable_view, name='variable.create'),
    path("update/<int:pk>/", view=update_variable_view, name='variable.edit'),
    path("delete/<int:pk>/", view=delete_variable_view, name='variable.delete'),
    path('get_variable_details/<int:pk>/', get_variable_details, name='variable.get_variable_details'),
]