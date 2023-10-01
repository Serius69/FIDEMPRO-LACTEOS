from django.urls import path
from . import views

urlpatterns = [
    path('api/variables/', views.variable_list, name='variable-list'),
    path('api/variables/<int:id>/', views.variable_detail, name='variable-detail'),
]
