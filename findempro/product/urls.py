from django.urls import path
from . import views

app_name = 'product'  # Define un espacio de nombres para evitar conflictos

urlpatterns = [
    # URL para listar todos los productos o agregar uno nuevo
    path('list', views.product_list, name='product-list'),

    # URL para actualizar y eliminar un producto específico
    path('detail/<int:id>/', views.product_detail, name='product-detail'),
]
