import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from tenancy.models import Subscription
from tenancy.services import ensure_default_organization

pytestmark = pytest.mark.django_db


def test_owner_cannot_self_assign_plan_or_reissue_trial_but_can_cancel():
    owner = get_user_model().objects.create_user(username="billing-owner-api", password="password")
    organization = ensure_default_organization(owner)
    client = Client()
    client.force_login(owner)

    plan = client.post(
        "/api/subscription/change-plan/",
        data={"plan": "BUSINESS"},
        content_type="application/json",
    )
    trial = client.post(
        "/api/subscription/start-trial/",
        data={"plan": "BUSINESS"},
        content_type="application/json",
    )
    cancelled = client.post("/api/subscription/cancel/")

    assert plan.status_code == 403
    assert trial.status_code == 403
    assert cancelled.status_code == 200
    subscription = Subscription.objects.get(organization=organization)
    assert subscription.status == Subscription.Status.CANCELLED
    assert subscription.effective_plan == Subscription.Plan.FREE


def test_internal_operator_can_change_plan_for_own_selected_organization():
    operator = get_user_model().objects.create_user(
        username="billing-operator", password="password", is_staff=True
    )
    organization = ensure_default_organization(operator)
    client = Client()
    client.force_login(operator)

    response = client.post(
        "/api/subscription/change-plan/",
        data={"plan": "GROWTH"},
        content_type="application/json",
    )

    assert response.status_code == 200
    assert Subscription.objects.get(organization=organization).effective_plan == "GROWTH"
