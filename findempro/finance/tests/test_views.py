"""
Tests de vistas de la app finance.

La app quedó cableada en ROOT_URLCONF (`path('finance/', include('finance.urls'))`)
y se corrigió un bug: `finance_list_view` renderizaba un template inexistente
(`financial-decision-list.html`) → 500; ahora usa `finance-list.html`.

Los tests reflejan el comportamiento REAL de las vistas:
  · Todas las vistas son `@login_required` → anónimo obtiene 302 (redirect a login),
    no 403.
  · `create` redirige (302) a la lista tras un POST (válido o inválido, salvo AJAX).
  · `list` renderiza 200 con contexto `financial_decisions` + `businesses`.
"""
import pytest
from django.urls import reverse
from django.test import Client
from django.contrib.auth.models import User

from finance.models import FinancialDecision, FinanceRecommendation
from business.models import Business


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="finuser", password="password-123-xyz")


@pytest.fixture
def business(db, user):
    return Business.objects.create(
        name="Empresa Finance", type=1, location="La Paz",
        description="desc", fk_user=user, is_active=True,
    )


@pytest.fixture
def financial_decision(db, business):
    return FinancialDecision.objects.create(
        name="Decisión Test", description="Descripción",
        fk_business=business, is_active=True,
    )


@pytest.fixture
def finance_recommendation(db, business):
    return FinanceRecommendation.objects.create(
        name="Recomendación Test",
        recommendation="Texto de recomendación suficientemente largo.",
        description="Descripción de la recomendación",
        fk_business=business,
    )


# ─────────────────────────────────────────────
# list view
# ─────────────────────────────────────────────
@pytest.mark.django_db
def test_finance_list_view_authenticated(client, user, financial_decision, business):
    client.login(username="finuser", password="password-123-xyz")
    response = client.get(reverse("finance:finance.list"))
    assert response.status_code == 200
    assert "financial_decisions" in response.context
    assert "businesses" in response.context


@pytest.mark.django_db
def test_finance_list_view_anonymous_redirects_to_login(client):
    response = client.get(reverse("finance:finance.list"))
    assert response.status_code == 302
    assert "login" in response.url.lower() or "account" in response.url.lower()


# ─────────────────────────────────────────────
# create view
# ─────────────────────────────────────────────
@pytest.mark.django_db
def test_create_finance_view_valid_redirects_and_persists(client, user, business):
    client.login(username="finuser", password="password-123-xyz")
    data = {
        "name": "Nueva Decisión", "description": "desc",
        "category": "otro", "priority": "media", "status": "pendiente",
        "fk_business": business.id, "is_active": True,
    }
    response = client.post(reverse("finance:finance.create"), data)
    assert response.status_code == 302  # redirect a la lista
    assert FinancialDecision.objects.filter(name="Nueva Decisión").exists()


@pytest.mark.django_db
def test_create_finance_view_get_redirects(client, user):
    client.login(username="finuser", password="password-123-xyz")
    response = client.get(reverse("finance:finance.create"))
    assert response.status_code == 302


@pytest.mark.django_db
def test_create_finance_view_anonymous_redirects_to_login(client):
    response = client.post(reverse("finance:finance.create"), {"name": "X"})
    assert response.status_code == 302
    assert "login" in response.url.lower() or "account" in response.url.lower()


@pytest.mark.django_db
def test_create_finance_view_invalid_ajax_returns_errors(client, user):
    client.login(username="finuser", password="password-123-xyz")
    response = client.post(
        reverse("finance:finance.create"),
        {"name": "", "description": ""},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert "errors" in body


# ─────────────────────────────────────────────
# update / delete view
# ─────────────────────────────────────────────
@pytest.mark.django_db
def test_update_finance_view_valid(client, user, financial_decision, business):
    client.login(username="finuser", password="password-123-xyz")
    data = {
        "name": "Decisión Actualizada", "description": "desc",
        "category": "otro", "priority": "media", "status": "pendiente",
        "fk_business": business.id, "is_active": True,
    }
    response = client.post(
        reverse("finance:finance.update", args=[financial_decision.id]), data)
    assert response.status_code == 302
    financial_decision.refresh_from_db()
    assert financial_decision.name == "Decisión Actualizada"


@pytest.mark.django_db
def test_delete_finance_view_soft_deletes(client, user, financial_decision):
    client.login(username="finuser", password="password-123-xyz")
    response = client.post(
        reverse("finance:finance.delete", args=[financial_decision.id]))
    assert response.status_code == 302
    financial_decision.refresh_from_db()
    assert financial_decision.is_active is False


# ─────────────────────────────────────────────
# details (JSON)
# ─────────────────────────────────────────────
@pytest.mark.django_db
def test_finance_decision_details_returns_json(client, user, financial_decision):
    client.login(username="finuser", password="password-123-xyz")
    response = client.get(
        reverse("finance:finance.details", args=[financial_decision.id]))
    assert response.status_code == 200
    assert response.json()["data"]["name"] == financial_decision.name


@pytest.mark.django_db
def test_recommendation_details_returns_json(client, user, finance_recommendation):
    client.login(username="finuser", password="password-123-xyz")
    response = client.get(
        reverse("finance:finance.recommendation_details", args=[finance_recommendation.id]))
    assert response.status_code == 200
    assert response.json()["data"]["name"] == finance_recommendation.name


# ─────────────────────────────────────────────
# Aislamiento por dueño (IDOR)
# ─────────────────────────────────────────────
@pytest.fixture
def other_user(db):
    return User.objects.create_user(username="intruso", password="otherpass-123")


@pytest.mark.django_db
def test_decision_details_isolation_returns_404_for_non_owner(
    client, other_user, financial_decision
):
    """El intruso NO puede ver la decisión de otro usuario -> 404."""
    client.login(username="intruso", password="otherpass-123")
    response = client.get(
        reverse("finance:finance.details", args=[financial_decision.id]))
    assert response.status_code == 404
    assert response.json()["success"] is False


@pytest.mark.django_db
def test_finance_list_excludes_other_users_decisions(
    client, other_user, financial_decision
):
    """La lista del intruso no incluye la decisión ajena."""
    client.login(username="intruso", password="otherpass-123")
    response = client.get(reverse("finance:finance.list"))
    assert response.status_code == 200
    assert financial_decision not in list(response.context["financial_decisions"])
    assert response.context["total_count"] == 0
