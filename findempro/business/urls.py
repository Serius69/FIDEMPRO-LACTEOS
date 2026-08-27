from django.urls import path
from django.views.decorators.cache import cache_page

from business import views

app_name = 'business'

urlpatterns = [
    # Lista de negocios
    path(
        "list/", 
        views.business_list_view, 
        name="business.list"
    ),
    
    # Ver detalle de un negocio específico
    path(
        "overview/<int:pk>/", 
        views.read_business_view, 
        name="business.overview"
    ),
    
    # Crear nuevo negocio
    path(
        'create/', 
        views.create_or_update_business_view, 
        name='business.create'
    ),
    
    # Actualizar negocio existente
    path(
        '<int:pk>/update/', 
        views.create_or_update_business_view, 
        name='business.update'
    ),
    
    # Eliminar negocio
    path(
        "<int:pk>/delete/", 
        views.delete_business_view, 
        name='business.delete'
    ),
    
    # API: contexto macro con procedencia y frescura (contrato KDP §4.6).
    # Sin cache_page a propósito: cachear frescura es servir una frescura vieja.
    path(
        'api/market-context/',
        views.market_context_view,
        name='business.market_context'
    ),

    # API: Obtener detalles de negocio (para AJAX)
    path(
        'api/details/<int:pk>/', 
        cache_page(60 * 5)(views.get_business_details_view), 
        name='business.get_business_details_view'
    ),
]