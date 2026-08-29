"""Compatibility adapter for the legacy Django simulation flow.

The subscription authority is the Organization. ``plan`` remains in the
signature because old Hub callers still send it; it never selects the
commercial plan.
"""

from django.conf import settings
from django.utils import timezone

from tenancy.models import UsageEvent
from tenancy.services import ensure_default_organization, get_quota, usage_total

from .models import Simulation


def verificar_limite(user, plan=None):
    """Return ``(allowed, used, limit)`` from the organization subscription.

    Historical v1 rows predate the ledger. The greater of the organization-
    scoped legacy count and ledger total avoids both lost history and double
    counting for new executions, which are represented in both sources.
    """
    if not getattr(settings, "PLAN_GATES_ENABLED", False):
        return True, 0, None

    organization = ensure_default_organization(user)
    limite = get_quota(organization, "simulation_runs")
    now = timezone.localtime()
    legacy_used = Simulation.objects.filter(
        fk_questionary_result__fk_questionary__fk_product__fk_business__organization=organization,
        date_created__year=now.year,
        date_created__month=now.month,
    ).count()
    ledger_used = int(usage_total(organization, UsageEvent.Metric.SIMULATION_RUN))
    usadas = max(legacy_used, ledger_used)

    return limite is None or usadas < limite, usadas, limite
