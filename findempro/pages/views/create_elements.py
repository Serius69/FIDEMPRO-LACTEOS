"""
views/create_elements.py - Lógica para crear elementos del negocio
"""
import logging
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.db import transaction
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from .business_creator import create_and_save_business
from .simulation_creator import register_elements_simulation, create_probability_density_functions

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST"])
@csrf_protect
@transaction.atomic
def register_elements_create(request):
    """
    Realiza la creación de los elementos del negocio para el usuario actual.
    Solo acepta métodos POST y requiere confirmación.
    """
    # Verificar que se envió la confirmación
    if not request.POST.get('confirm_setup'):
        messages.error(request, _('Solicitud inválida. Por favor, intente nuevamente.'))
        return redirect("dashboard:index")
    
    try:
        # Verificar si el usuario ya tiene un negocio configurado
        if hasattr(request.user, 'business') and request.user.business.exists():
            messages.warning(request, _('Ya tiene una configuración de negocio existente.'))
            return redirect("dashboard:index")
        
        # Crear el negocio y sus elementos
        logger.info(f"Iniciando creación de negocio para usuario {request.user.id}")
        
        business = create_and_save_business(request.user)
        logger.info(f"Negocio creado con ID: {business.id}")
        
        # Crear funciones de densidad probabilística
        create_probability_density_functions(business)
        
        # Registrar elementos de simulación
        simulations_created = register_elements_simulation(request, request.user)
        logger.info(f"Elementos de simulación registrados: {simulations_created} para usuario {request.user.id}")
        
        messages.success(
            request, 
            _(
                'Configuración creada exitosamente. '
                'Su negocio lácteo ha sido configurado con todos los elementos iniciales. '
                'Puede personalizar la información desde el panel de control.'
            )
        )
        
    except Exception as e:
        logger.error(f"Error creating business for user {request.user.id}: {str(e)}")
        messages.error(
            request, 
            _(
                'Error al crear la configuración del negocio. '
                'Por favor, contacte al soporte técnico si el problema persiste.'
            )
        )
        return redirect("dashboard:index")
    
    return redirect("dashboard:index")