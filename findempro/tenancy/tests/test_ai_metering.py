from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from variable.views import _generate_with_claude

from tenancy.models import ResourceUsage, UsageEvent
from tenancy.services import change_plan, ensure_default_organization

pytestmark = pytest.mark.django_db


def test_ai_provider_is_entitled_abuse_guarded_and_metered(monkeypatch):
    user = get_user_model().objects.create_user(username="ai-meter-owner", password="password")
    organization = ensure_default_organization(user)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-only-not-a-real-key")
    cache.clear()
    provider = SimpleNamespace(
        messages=SimpleNamespace(
            create=lambda **kwargs: SimpleNamespace(
                content=[SimpleNamespace(type="text", text="DEMO")],
                usage=SimpleNamespace(input_tokens=12, output_tokens=3),
            )
        )
    )

    with patch("anthropic.Anthropic", return_value=provider) as anthropic_client:
        assert _generate_with_claude(
            "prompt", 8, organization=organization, actor_id=user.pk
        ) is None
        anthropic_client.assert_not_called()

        change_plan(organization, "PRO")
        assert _generate_with_claude(
            "prompt", 8, organization=organization, actor_id=user.pk
        ) == "DEMO"

    event = UsageEvent.objects.get(
        organization=organization,
        metric=UsageEvent.Metric.AI_CALL,
    )
    assert event.metadata["provider"] == "anthropic"
    assert event.metadata["cost"] == "COST_UNKNOWN"
    resources = ResourceUsage.objects.filter(organization=organization)
    assert set(resources.values_list("resource", flat=True)) == {
        "AI_INPUT_TOKENS",
        "AI_OUTPUT_TOKENS",
    }
    assert all(resource.cost_amount is None for resource in resources)
