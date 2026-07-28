"""Límites mensuales de simulaciones según el plan del usuario."""

from django.conf import settings
from django.utils import timezone

from .models import Simulation


DEFAULT_PLAN_SIM_LIMITS = {
    "basico": 10,
    "pro": 100,
    "empresa": None,
}


def verificar_limite(user, plan):
    """Devuelve ``(permitido, usadas, limite)`` para el mes calendario actual."""
    if not getattr(settings, "PLAN_GATES_ENABLED", False):
        return True, 0, None

    limits = getattr(settings, "PLAN_SIM_LIMITS", DEFAULT_PLAN_SIM_LIMITS)
    effective_plan = "empresa" if (
        getattr(user, "is_staff", False) or getattr(user, "is_superuser", False)
    ) else plan
    if effective_plan not in DEFAULT_PLAN_SIM_LIMITS:
        effective_plan = "basico"

    limite = limits.get(effective_plan, DEFAULT_PLAN_SIM_LIMITS[effective_plan])
    now = timezone.localtime()
    usadas = Simulation.objects.filter(
        fk_questionary_result__fk_questionary__fk_product__fk_business__fk_user=user,
        date_created__year=now.year,
        date_created__month=now.month,
    ).count()

    return limite is None or usadas < limite, usadas, limite
