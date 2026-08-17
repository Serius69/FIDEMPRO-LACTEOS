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
        # Tipo de empresa elegido en el onboarding (opcional). Si es un tipo con
        # catálogo de datos bolivianos, se usa el sembrado multi-industria; si no,
        # se cae al camino lácteo legacy (retrocompatible).
        spec = _resolve_industry_spec(request.POST.get('business_type'))

        logger.info(f"Iniciando creación de negocio para usuario {request.user.id}")

        if spec is not None:
            from business.models import Business
            from business.services.seed_service import IndustrySeeder

            business = IndustrySeeder(request.user).seed_business(spec)
            logger.info(f"Negocio '{spec.business_name}' (tipo {spec.business_type}) creado con ID: {business.id}")

            label = dict(Business.BusinessType.choices).get(spec.business_type, spec.business_name)
            messages.success(
                request,
                _(
                    'Configuración creada exitosamente. Su negocio "%(name)s" (%(label)s) '
                    'ha sido configurado con una plantilla sintética editable. '
                    'Revise y confirme los datos antes de simular.'
                ) % {'name': spec.business_name, 'label': str(label)}
            )
        else:
            # Camino lácteo legacy (sin tipo elegido o tipo sin catálogo).
            business = create_and_save_business(request.user)
            logger.info(f"Negocio lácteo (legacy) creado con ID: {business.id}")

            create_probability_density_functions(business)
            simulations_created = register_elements_simulation(request, request.user)
            logger.info(f"Elementos de simulación registrados: {simulations_created} para usuario {request.user.id}")

            messages.success(
                request,
                _(
                    'Configuración creada exitosamente. '
                    'Su negocio lácteo tiene una estructura inicial. Complete y confirme '
                    'los datos empresariales antes de simular.'
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


def _resolve_industry_spec(business_type_raw):
    """
    Traduce el valor 'business_type' del POST a un IndustrySpec del catálogo
    boliviano. Devuelve None si no se envió o no es un tipo válido (→ camino
    lácteo legacy).
    """
    if not business_type_raw:
        return None
    try:
        from business.data.bolivia_industries import get_spec
        return get_spec(int(business_type_raw))
    except (ValueError, TypeError):
        logger.warning("business_type inválido en onboarding: %r", business_type_raw)
        return None
