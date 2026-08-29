from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from .models import (
    Organization,
    OrganizationMembership,
    ResourceUsage,
    Subscription,
    UsageEvent,
)

CAPABILITIES = {
    "basic_results",
    "basic_visualization",
    "advanced_distributions",
    "large_datasets",
    "scenario_comparison",
    "advanced_simulation",
    "batch_runs",
    "advanced_reports",
    "exports",
    "api_access",
    "ai_analysis",
    "collaboration",
}

# Launch defaults are deliberately configuration, not capacity claims. They reuse
# measured product safety bounds already present in the codebase (10/100 runs,
# 10k rows/import, 2 MiB/import) and can be changed without branching on plan names.
DEFAULT_PLAN_CATALOG = {
    "FREE": {
        "entitlements": {"basic_results", "basic_visualization", "exports"},
        "quotas": {"active_projects": 1, "datasets": 1, "dataset_rows": 10_000,
                   "simulation_runs": 10, "exports": 1, "members": 1},
    },
    "STARTER": {
        "entitlements": {"basic_results", "basic_visualization", "exports", "collaboration"},
        "quotas": {"active_projects": 5, "datasets": 5, "dataset_rows": 10_000,
                   "simulation_runs": 100, "exports": 30, "members": 3},
    },
    "GROWTH": {
        "entitlements": {"basic_results", "basic_visualization", "advanced_distributions",
                         "large_datasets", "scenario_comparison", "advanced_reports", "exports",
                         "collaboration"},
        "quotas": {"active_projects": 20, "datasets": 25, "dataset_rows": 10_000,
                   "simulation_runs": 500, "exports": 150, "members": 10},
    },
    "PRO": {
        "entitlements": {"basic_results", "basic_visualization", "advanced_distributions",
                         "large_datasets", "scenario_comparison", "advanced_simulation",
                         "batch_runs", "advanced_reports", "exports", "api_access", "ai_analysis",
                         "collaboration"},
        "quotas": {"active_projects": 100, "datasets": 100, "dataset_rows": 10_000,
                   "simulation_runs": 2_000, "exports": 500, "members": 25},
    },
    "BUSINESS": {
        "entitlements": set(CAPABILITIES),
        "quotas": {"active_projects": None, "datasets": None, "dataset_rows": 10_000,
                   "simulation_runs": None, "exports": None, "members": None},
    },
}


class QuotaExceeded(PermissionDenied):
    def __init__(self, capability, used, limit):
        self.capability = capability
        self.used = used
        self.limit = limit
        super().__init__(f"Quota exceeded for {capability}: {used}/{limit}")


def plan_catalog():
    configured = getattr(settings, "FINDEMPRO_PLAN_CATALOG", None)
    return configured or DEFAULT_PLAN_CATALOG


@transaction.atomic
def ensure_default_organization(user):
    membership = (
        OrganizationMembership.objects.select_related("organization")
        .filter(user=user, is_active=True, organization__is_active=True)
        .order_by("created_at")
        .first()
    )
    if membership:
        Subscription.objects.get_or_create(organization=membership.organization)
        return membership.organization
    label = user.get_full_name().strip() if hasattr(user, "get_full_name") else ""
    organization = Organization.objects.create(
        name=label or f"{user.get_username()} Organization", created_by=user
    )
    OrganizationMembership.objects.create(
        organization=organization, user=user, role=OrganizationMembership.Role.OWNER
    )
    Subscription.objects.create(organization=organization, plan=Subscription.Plan.FREE)
    return organization


def get_user_organization(user, organization_id=None):
    if not getattr(user, "is_authenticated", False):
        raise PermissionDenied("Authentication required")
    qs = Organization.objects.filter(
        is_active=True,
        memberships__user=user,
        memberships__is_active=True,
    ).distinct()
    if organization_id:
        organization = qs.filter(id=organization_id).first()
        if not organization:
            raise PermissionDenied("Organization is not available to this user")
        return organization
    organization = qs.order_by("memberships__created_at").first()
    return organization or ensure_default_organization(user)


def get_request_organization(request):
    organization = getattr(request, "organization", None)
    if organization:
        return organization
    return get_user_organization(request.user, request.headers.get("X-Organization-ID"))


def membership_for(user, organization):
    return OrganizationMembership.objects.filter(
        user=user, organization=organization, is_active=True
    ).first()


def require_role(user, organization, roles):
    membership = membership_for(user, organization)
    if not membership or membership.role not in set(roles):
        raise PermissionDenied("The organization role does not allow this action")
    return membership


def require_write(user, organization):
    return require_role(
        user,
        organization,
        {OrganizationMembership.Role.OWNER, OrganizationMembership.Role.ADMIN,
         OrganizationMembership.Role.MEMBER},
    )


def subscription_for(organization):
    subscription, _ = Subscription.objects.get_or_create(organization=organization)
    if subscription.trial_ends_at and not subscription.trial_is_active and subscription.trial_plan:
        subscription.plan = Subscription.Plan.FREE
        subscription.trial_started_at = None
        subscription.trial_ends_at = None
        subscription.trial_plan = None
        subscription.save(update_fields=["plan", "trial_started_at", "trial_ends_at", "trial_plan", "updated_at"])
    return subscription


def has_entitlement(organization, capability):
    if capability not in CAPABILITIES:
        raise ValidationError(f"Unknown capability: {capability}")
    plan = subscription_for(organization).effective_plan
    return capability in plan_catalog()[plan]["entitlements"]


def require_entitlement(organization, capability, source="commercial_gate", correlation_id="check"):
    allowed = has_entitlement(organization, capability)
    if allowed:
        return True
    mode = getattr(settings, "FINDEMPRO_COMMERCIAL_GATES_MODE", "enforce")
    if mode == "shadow":
        record_usage(
            organization,
            UsageEvent.Metric.API_REQUEST,
            1,
            source,
            correlation_id,
            {"gate": capability, "decision": "would_deny"},
        )
        return True
    raise PermissionDenied(f"Upgrade required for {capability}")


def get_quota(organization, capability):
    plan = subscription_for(organization).effective_plan
    quotas = plan_catalog()[plan]["quotas"]
    if capability not in quotas:
        raise ValidationError(f"Unknown quota: {capability}")
    return quotas[capability]


def current_month_bounds(now=None):
    now = now or timezone.now()
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end = (start + timedelta(days=32)).replace(day=1)
    return start, end


def usage_total(organization, metric, start=None, end=None):
    qs = UsageEvent.objects.filter(organization=organization, metric=metric)
    if start:
        qs = qs.filter(timestamp__gte=start)
    if end:
        qs = qs.filter(timestamp__lt=end)
    return qs.aggregate(total=Sum("quantity"))["total"] or Decimal(0)


def enforce_quota(organization, capability, used, requested=1):
    limit = get_quota(organization, capability)
    if limit is not None and Decimal(str(used)) + Decimal(str(requested)) > Decimal(str(limit)):
        raise QuotaExceeded(capability, used, limit)
    return limit


def enforce_monthly_usage(organization, capability, metric, requested=1):
    start, end = current_month_bounds()
    used = usage_total(organization, metric, start, end)
    return enforce_quota(organization, capability, used, requested), used


def record_usage(organization, metric, quantity, source, correlation_id, metadata=None):
    event, created = UsageEvent.objects.get_or_create(
        organization=organization,
        metric=metric,
        source=source,
        correlation_id=str(correlation_id),
        defaults={"quantity": Decimal(str(quantity)), "metadata": metadata or {}},
    )
    return event, created


def record_resource_usage(organization, resource, quantity, unit, source, correlation_id, metadata=None):
    event, created = ResourceUsage.objects.get_or_create(
        organization=organization,
        resource=resource,
        unit=unit,
        source=source,
        correlation_id=str(correlation_id),
        defaults={"quantity": Decimal(str(quantity)), "metadata": metadata or {}},
    )
    return event, created


@transaction.atomic
def start_trial(organization, plan=Subscription.Plan.PRO, duration_days=14):
    if plan == Subscription.Plan.FREE:
        raise ValidationError("A trial must target a premium plan")
    subscription = subscription_for(organization)
    if subscription.trial_consumed_at:
        raise ValidationError("The organization trial has already been consumed")
    now = timezone.now()
    subscription.status = Subscription.Status.ACTIVE
    subscription.trial_started_at = now
    subscription.trial_ends_at = now + timedelta(days=duration_days)
    subscription.trial_plan = plan
    subscription.trial_consumed_at = now
    subscription.cancelled_at = None
    subscription.full_clean()
    subscription.save()
    return subscription


@transaction.atomic
def change_plan(organization, plan):
    valid = {value for value, _ in Subscription.Plan.choices}
    if plan not in valid:
        raise ValidationError("Unknown plan")
    subscription = subscription_for(organization)
    subscription.plan = plan
    subscription.status = Subscription.Status.ACTIVE
    subscription.cancelled_at = None
    subscription.trial_started_at = None
    subscription.trial_ends_at = None
    subscription.trial_plan = None
    subscription.save()
    return subscription


@transaction.atomic
def cancel_subscription(organization):
    subscription = subscription_for(organization)
    subscription.plan = Subscription.Plan.FREE
    subscription.status = Subscription.Status.CANCELLED
    subscription.cancelled_at = timezone.now()
    subscription.trial_started_at = None
    subscription.trial_ends_at = None
    subscription.trial_plan = None
    subscription.save()
    return subscription
