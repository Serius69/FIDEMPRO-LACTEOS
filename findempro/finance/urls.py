from django.urls import path
from finance.views import (
    finance_list_view,
    create_financial_decision_view,
    update_financial_decision_view,
    delete_financial_decision_view,
    get_financial_decision_details_view,
    get_finance_recommendation_details_view,
    bulk_delete_financial_decisions_view
)

app_name = 'finance'

urlpatterns = [
    # Lista principal
    path("list/", view=finance_list_view, name="finance.list"),
    
    # CRUD de decisiones financieras
    path("create/", view=create_financial_decision_view, name='finance.create'),
    path("update/<int:pk>/", view=update_financial_decision_view, name='finance.update'),
    path("delete/<int:pk>/", view=delete_financial_decision_view, name='finance.delete'),
    path("bulk-delete/", view=bulk_delete_financial_decisions_view, name='finance.bulk_delete'),
    
    # Detalles y API endpoints
    path('details/<int:pk>/', get_financial_decision_details_view, name='finance.details'),
    path('recommendation-details/<int:pk>/', get_finance_recommendation_details_view, name='finance.recommendation_details'),
]