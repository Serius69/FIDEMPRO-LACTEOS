import pytest
from django.urls import reverse
from django.test import Client
from django.contrib.auth.models import User
from finance.models import FinancialDecision, FinanceRecommendation
from business.models import Business
from finance.forms import FinancialDecisionForm


# UNIT TESTS
@pytest.fixture
def client():
    return Client()

@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="password")

@pytest.fixture
def financial_decision(db):
    return FinancialDecision.objects.create(name="Test Decision", description="Test Description")

@pytest.fixture
def finance_recommendation(db):
    return FinanceRecommendation.objects.create(
        name="Test Recommendation",
        recommendation="Test Recommendation Text",
        description="Test Recommendation Description"
    )

@pytest.fixture
def business(db):
    return Business.objects.create(name="Test Business")

@pytest.mark.django_db
def test_finance_list_view(client, user, financial_decision, business):
    client.login(username="testuser", password="password")
    url = reverse("finance:finance.list")
    response = client.get(url)
    assert response.status_code == 200
    assert "FinancialDecisions" in response.context
    assert "businesses" in response.context

@pytest.mark.django_db
def test_create_finance_view(client, user):
    client.login(username="testuser", password="password")
    url = reverse("finance:finance.create")
    data = {"name": "New Decision", "description": "New Description"}
    response = client.post(url, data)
    assert response.status_code == 200
    assert FinancialDecision.objects.filter(name="New Decision").exists()

@pytest.mark.django_db
def test_update_finance_view(client, user, financial_decision):
    client.login(username="testuser", password="password")
    url = reverse("finance:finance.update", args=[financial_decision.id])
    data = {"name": "Updated Decision", "description": "Updated Description"}
    response = client.post(url, data)
    assert response.status_code == 302
    financial_decision.refresh_from_db()
    assert financial_decision.name == "Updated Decision"

@pytest.mark.django_db
def test_delete_finance_decision_view(client, user, financial_decision):
    client.login(username="testuser", password="password")
    url = reverse("finance:finance.delete", args=[financial_decision.id])
    response = client.patch(url)
    assert response.status_code == 302
    financial_decision.refresh_from_db()
    assert not financial_decision.is_active

@pytest.mark.django_db
def test_get_finance_decision_details_view(client, user, finance_recommendation):
    client.login(username="testuser", password="password")
    url = reverse("finance:finance.details", args=[finance_recommendation.id])
    response = client.get(url)
    assert response.status_code == 200
    assert response.json() == {
        "name": finance_recommendation.name,
        "recommendation": finance_recommendation.recommendation,
        "description": finance_recommendation.description,
    }
    
# REGRESSION TESTS
@pytest.mark.django_db
def test_create_finance_view_authenticated(client, user):
    client.login(username="testuser", password="password")
    url = reverse("finance:finance.create")
    data = {"name": "Test Decision", "description": "Test Description"}
    response = client.post(url, data)
    assert response.status_code == 200
    assert FinancialDecision.objects.filter(name="Test Decision").exists()

@pytest.mark.django_db
def test_create_finance_view_unauthenticated(client):
    url = reverse("finance:finance.create")
    data = {"name": "Test Decision", "description": "Test Description"}
    response = client.post(url, data)
    assert response.status_code == 403  # Expecting forbidden for unauthenticated users

@pytest.mark.django_db
def test_update_finance_view_authenticated(client, user, financial_decision):
    client.login(username="testuser", password="password")
    url = reverse("finance:finance.update", args=[financial_decision.id])
    data = {"name": "Updated Decision", "description": "Updated Description"}
    response = client.post(url, data)
    assert response.status_code == 200
    financial_decision.refresh_from_db()
    assert financial_decision.name == "Updated Decision"

@pytest.mark.django_db
def test_update_finance_view_unauthenticated(client, financial_decision):
    url = reverse("finance:finance.update", args=[financial_decision.id])
    data = {"name": "Updated Decision", "description": "Updated Description"}
    response = client.post(url, data)
    assert response.status_code == 403  # Expecting forbidden for unauthenticated users

@pytest.mark.django_db
def test_create_finance_view_invalid_data(client, user):
    client.login(username="testuser", password="password")
    url = reverse("finance:finance.create")
    data = {"name": "", "description": ""}  # Invalid data
    response = client.post(url, data)
    assert response.status_code == 200
    assert not FinancialDecision.objects.filter(name="").exists()
    assert "This field is required" in response.content.decode()

@pytest.mark.django_db
def test_update_finance_view_invalid_data(client, user, financial_decision):
    client.login(username="testuser", password="password")
    url = reverse("finance:finance.update", args=[financial_decision.id])
    data = {"name": "", "description": ""}  # Invalid data
    response = client.post(url, data)
    assert response.status_code == 200
    financial_decision.refresh_from_db()
    assert financial_decision.name != ""  # Ensure the name was not updated to invalid data

