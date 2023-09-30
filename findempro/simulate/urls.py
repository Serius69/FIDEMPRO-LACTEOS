from django.urls import path
from . import views

urlpatterns = [
    # URL para listar todos los productos o agregar uno nuevo
    path('simulate/', views.ks_test_view, name='simulate')
]
