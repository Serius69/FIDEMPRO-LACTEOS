from django.urls import path
from finance.views import (
    finance_list_view,
    create_or_update_finance_view,
    delete_finance_decision_view,
    get_finance_decision_details_view
)
app_name = 'finance'
urlpatterns = [
    path("list", view=finance_list_view, name="finance.list"),
    path("create/", view=create_or_update_finance_view, name='finance.create'),
    path("update/<int:pk>/", view=create_or_update_finance_view, name='finance.edit'),
    path("delete/<int:pk>/", view=delete_finance_decision_view, name='finance.delete'),
    path('get_finance_details/<int:pk>/', get_finance_decision_details_view, name='finance.get_finance_details'),
]


