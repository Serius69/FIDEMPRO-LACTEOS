from django.urls import path
from . import views

urlpatterns = [
    # URL para listar todos los productos o agregar uno nuevo
    path('api/products/', views.product_list, name='product-list'),

    # URL para actualizar y eliminar un producto específico
    path('api/products/<int:id>/', views.product_detail, name='product-detail'),
]
