import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache

from tenancy.services import change_plan, ensure_default_organization
from variable.views import (
    _fallback_initials,
    _generate_with_claude,
    _normalise_initials,
)


def test_claude_missing_key_uses_clean_fallback(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    assert _generate_with_claude("prompt", max_tokens=10) is None
    assert _fallback_initials("Costo total mensual") == "CTMX"
    assert _normalise_initials('"ctm!"', "Costo total mensual") == "CTMX"


@pytest.mark.django_db
def test_claude_uses_sonnet_and_prompt_cache(monkeypatch):
    user = get_user_model().objects.create_user(username="claude-contract")
    organization = ensure_default_organization(user)
    change_plan(organization, "PRO")
    cache.clear()
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    create = Mock(return_value=SimpleNamespace(
        content=[SimpleNamespace(type="text", text="¿Cuál es el costo?")],
        usage=SimpleNamespace(input_tokens=5, output_tokens=4),
    ))
    client = Mock()
    client.messages.create = create
    anthropic_module = SimpleNamespace(Anthropic=Mock(return_value=client))
    monkeypatch.setitem(sys.modules, "anthropic", anthropic_module)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    result = _generate_with_claude(
        "prompt estable", max_tokens=100,
        organization=organization, actor_id=user.pk,
    )

    assert result == "¿Cuál es el costo?"
    anthropic_module.Anthropic.assert_called_once_with(api_key="test-key")
    assert create.call_args.kwargs["model"] == "claude-sonnet-5"
    assert create.call_args.kwargs["cache_control"] == {"type": "ephemeral"}
