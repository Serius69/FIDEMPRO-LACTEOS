import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from .models import OrganizationMembership, Subscription, UsageEvent
from .services import (
    QuotaExceeded,
    cancel_subscription,
    change_plan,
    get_request_organization,
    membership_for,
    plan_catalog,
    require_role,
    start_trial,
    subscription_for,
)


def _body(request):
    try:
        value = json.loads(request.body or "{}")
    except json.JSONDecodeError as exc:
        raise ValidationError("Invalid JSON") from exc
    if not isinstance(value, dict):
        raise ValidationError("JSON body must be an object")
    return value


@login_required
@require_GET
def context(request):
    organization = get_request_organization(request)
    membership = membership_for(request.user, organization)
    subscription = subscription_for(organization)
    catalog = plan_catalog()[subscription.effective_plan]
    return JsonResponse({
        "organization": {"id": str(organization.id), "name": organization.name, "slug": organization.slug},
        "membership": {"role": membership.role},
        "subscription": {
            "plan": subscription.plan,
            "effective_plan": subscription.effective_plan,
            "status": subscription.status,
            "trial_started_at": subscription.trial_started_at,
            "trial_ends_at": subscription.trial_ends_at,
            "trial_plan": subscription.trial_plan,
        },
        "entitlements": sorted(catalog["entitlements"]),
        "quotas": catalog["quotas"],
        "upgrade_url": getattr(settings, "HUB_UPGRADE_URL", ""),
    })


def permission_denied(request, exception=None):
    if isinstance(exception, QuotaExceeded):
        return JsonResponse({
            "error": "quota_exceeded",
            "capability": exception.capability,
            "used": str(exception.used),
            "limit": exception.limit,
            "message": "Alcanzaste el límite de tu plan. Tus datos se preservan; mejora el plan para crear más.",
            "upgrade_url": getattr(settings, "HUB_UPGRADE_URL", ""),
        }, status=403)
    return JsonResponse({
        "error": "upgrade_required" if exception and "Upgrade required" in str(exception) else "forbidden",
        "message": str(exception or "No tienes permiso para esta acción."),
        "upgrade_url": getattr(settings, "HUB_UPGRADE_URL", ""),
    }, status=403)


def _billing_role(request, organization):
    return require_role(
        request.user, organization,
        {OrganizationMembership.Role.OWNER, OrganizationMembership.Role.ADMIN},
    )


def _internal_subscription_operator(request):
    if not request.user.is_staff:
        raise PermissionDenied("Subscription changes require an internal operator")


@login_required
@require_POST
def plan_change(request):
    organization = get_request_organization(request)
    _billing_role(request, organization)
    _internal_subscription_operator(request)
    try:
        subscription = change_plan(organization, str(_body(request).get("plan", "")).upper())
    except ValidationError as exc:
        return JsonResponse({"error": "invalid_plan", "message": str(exc)}, status=400)
    return JsonResponse({"plan": subscription.plan, "effective_plan": subscription.effective_plan})


@login_required
@require_POST
def trial_start(request):
    organization = get_request_organization(request)
    _billing_role(request, organization)
    _internal_subscription_operator(request)
    body = _body(request)
    try:
        subscription = start_trial(
            organization,
            str(body.get("plan", Subscription.Plan.PRO)).upper(),
            int(body.get("duration_days", 14)),
        )
    except (ValidationError, ValueError) as exc:
        return JsonResponse({"error": "invalid_trial", "message": str(exc)}, status=400)
    return JsonResponse({"effective_plan": subscription.effective_plan, "trial_ends_at": subscription.trial_ends_at})


@login_required
@require_POST
def subscription_cancel(request):
    organization = get_request_organization(request)
    _billing_role(request, organization)
    subscription = cancel_subscription(organization)
    return JsonResponse({"plan": subscription.plan, "status": subscription.status})


@login_required
@require_GET
def usage(request):
    organization = get_request_organization(request)
    events = UsageEvent.objects.filter(organization=organization)[:100]
    return JsonResponse({"events": [{
        "metric": item.metric, "quantity": str(item.quantity), "timestamp": item.timestamp,
        "source": item.source, "correlation_id": item.correlation_id,
    } for item in events]})
