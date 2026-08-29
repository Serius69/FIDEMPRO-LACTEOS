from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from tenancy.models import OrganizationMembership, Subscription, UsageEvent
from tenancy.services import (
    cancel_subscription,
    change_plan,
    ensure_default_organization,
    get_quota,
    has_entitlement,
    record_usage,
    require_write,
    start_trial,
    subscription_for,
)

pytestmark = pytest.mark.django_db


def user(name):
    return get_user_model().objects.create_user(username=name, password="test-password")


def test_signup_provisions_organization_owner_and_free_subscription():
    account = user("new-account")
    organization = ensure_default_organization(account)

    membership = OrganizationMembership.objects.get(organization=organization, user=account)
    subscription = Subscription.objects.get(organization=organization)

    assert membership.role == OrganizationMembership.Role.OWNER
    assert subscription.effective_plan == Subscription.Plan.FREE
    assert get_quota(organization, "active_projects") == 1
    assert has_entitlement(organization, "basic_results") is True


def test_rbac_read_only_cannot_mutate_but_member_can():
    owner = user("owner")
    member = user("member")
    reader = user("reader")
    organization = ensure_default_organization(owner)
    OrganizationMembership.objects.create(organization=organization, user=member, role="MEMBER")
    OrganizationMembership.objects.create(organization=organization, user=reader, role="READ_ONLY")

    assert require_write(member, organization).role == "MEMBER"
    with pytest.raises(PermissionDenied):
        require_write(reader, organization)


def test_trial_expiry_downgrades_to_free_without_deleting_state():
    owner = user("trial-owner")
    organization = ensure_default_organization(owner)
    subscription = start_trial(organization, Subscription.Plan.PRO, duration_days=14)
    assert subscription.effective_plan == Subscription.Plan.PRO

    subscription.trial_ends_at = timezone.now() - timedelta(seconds=1)
    subscription.save(update_fields=["trial_ends_at"])
    expired = subscription_for(organization)

    assert expired.effective_plan == Subscription.Plan.FREE
    assert expired.trial_plan is None
    assert expired.trial_consumed_at is not None
    assert organization.is_active is True
    with pytest.raises(ValidationError, match="already been consumed"):
        start_trial(organization, Subscription.Plan.PRO, duration_days=14)


def test_upgrade_downgrade_and_cancellation_preserve_organization():
    owner = user("billing-owner")
    organization = ensure_default_organization(owner)

    assert change_plan(organization, "PRO").effective_plan == "PRO"
    assert has_entitlement(organization, "advanced_simulation") is True
    assert change_plan(organization, "FREE").effective_plan == "FREE"
    cancelled = cancel_subscription(organization)

    assert cancelled.status == "CANCELLED"
    assert cancelled.effective_plan == "FREE"
    assert organization.pk is not None


def test_usage_ledger_is_idempotent_and_append_only():
    owner = user("meter-owner")
    organization = ensure_default_organization(owner)

    first, created_first = record_usage(
        organization, UsageEvent.Metric.SIMULATION_RUN, 1, "test", "run-1"
    )
    second, created_second = record_usage(
        organization, UsageEvent.Metric.SIMULATION_RUN, 1, "test", "run-1"
    )

    assert created_first is True
    assert created_second is False
    assert first.pk == second.pk
    first.quantity = 2
    with pytest.raises(ValidationError, match="append-only"):
        first.save()
    with pytest.raises(ValidationError, match="append-only"):
        first.delete()
    with pytest.raises(ValidationError, match="append-only"):
        UsageEvent.objects.filter(pk=first.pk).update(quantity=2)
