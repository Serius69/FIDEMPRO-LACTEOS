import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from django.test import Client
from business.models import Business
from finance.models import FinanceRecommendationSimulation
from product.models import Product, Area
from dashboards.models import Chart
from simulate.models import Simulation, ResultSimulation
from user.models import ActivityLog
from variable.models import Variable
from django.utils import timezone
from datetime import datetime
from dateutil.relativedelta import relativedelta

# UNIT TESTS

@pytest.mark.django_db
def test_index_view_authenticated_user(client, django_user_model):
    user = django_user_model.objects.create_user(username="testuser", password="password")
    client.login(username="testuser", password="password")
    url = reverse("index")
    response = client.get(url)
    assert response.status_code == 200
    assert "form" in response.context

@pytest.mark.django_db
def test_index_view_post_valid_form(client, django_user_model):
    user = django_user_model.objects.create_user(username="testuser", password="password")
    client.login(username="testuser", password="password")
    url = reverse("index")
    data = {"field_name": "value"}  # Replace with actual form data
    response = client.post(url, data)
    assert response.status_code == 302  # Redirect after successful form submission

@pytest.mark.django_db
def test_dashboard_admin_view(client, django_user_model):
    user = django_user_model.objects.create_user(username="adminuser", password="password")
    client.login(username="adminuser", password="password")
    url = reverse("dashboard_admin")
    response = client.get(url)
    assert response.status_code == 200
    assert "users" in response.context
    assert "users_last_month" in response.context

@pytest.mark.django_db
def test_dashboard_user_view(client, django_user_model):
    user = django_user_model.objects.create_user(username="testuser", password="password")
    business = Business.objects.create(fk_user=user, is_active=True)
    client.login(username="testuser", password="password")
    session = client.session
    session["business_id"] = business.id
    session.save()
    url = reverse("dashboard_user")
    response = client.get(url)
    assert response.status_code == 200
    assert "greeting" in response.context
    assert "business" in response.context

@pytest.mark.django_db
def test_dashboard_user_view_no_business(client, django_user_model):
    user = django_user_model.objects.create_user(username="testuser", password="password")
    client.login(username="testuser", password="password")
    url = reverse("dashboard_user")
    response = client.get(url)
    assert response.status_code == 302  # Redirect to business list


# REGRESSION TESTS
@pytest.mark.django_db
def test_dashboard_user_authenticated_with_business(client, django_user_model):
    user = django_user_model.objects.create_user(username="testuser", password="password")
    business = Business.objects.create(fk_user=user, is_active=True)
    client.login(username="testuser", password="password")
    session = client.session
    session["business_id"] = business.id
    session.save()
    url = reverse("dashboard_user")
    response = client.get(url)
    assert response.status_code == 200
    assert "greeting" in response.context
    assert "business" in response.context
    assert response.context["business"].id == business.id

@pytest.mark.django_db
def test_dashboard_user_authenticated_no_business(client, django_user_model):
    user = django_user_model.objects.create_user(username="testuser", password="password")
    client.login(username="testuser", password="password")
    url = reverse("dashboard_user")
    response = client.get(url)
    assert response.status_code == 302  # Redirect to business list
    assert response.url == reverse("business:business.list")

@pytest.mark.django_db
def test_dashboard_user_unauthenticated(client):
    url = reverse("dashboard_user")
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login
    assert response.url.startswith(reverse("login"))

@pytest.mark.django_db
def test_dashboard_user_invalid_business_id_in_session(client, django_user_model):
    user = django_user_model.objects.create_user(username="testuser", password="password")
    client.login(username="testuser", password="password")
    session = client.session
    session["business_id"] = "invalid_id"
    session.save()
    url = reverse("dashboard_user")
    response = client.get(url)
    assert response.status_code == 302  # Redirect to business list
    assert response.url == reverse("business:business.list")

@pytest.mark.django_db
def test_dashboard_user_multiple_businesses(client, django_user_model):
    user = django_user_model.objects.create_user(username="testuser", password="password")
    Business.objects.create(fk_user=user, is_active=True)
    Business.objects.create(fk_user=user, is_active=True)
    client.login(username="testuser", password="password")
    url = reverse("dashboard_user")
    response = client.get(url)
    assert response.status_code == 302  # Redirect due to multiple businesses
    assert response.url == reverse("business:business.list")

# INTEGRATION TESTS







