from django.urls import path
from . import views

urlpatterns = [
    path('api/variables/', views.VariableList, name='variable-list'),
    path('api/variables/<int:id>/', views.VariableDetail, name='variable-detail'),
]
