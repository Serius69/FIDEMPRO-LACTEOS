import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from django.test import Client
from business.models import Business
from product.models import Product
from pages.models import Instructions
from django.core.files.uploadedfile import SimpleUploadedFile

# UNIT TESTS
# BUSINESS VIEWS
@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="password")

@pytest.fixture
def client(user):
    client = Client()
    client.login(username="testuser", password="password")
    return client

@pytest.fixture
def business(user):
    return Business.objects.create(
        fk_user=user,
        name="Test Business",
        type="Retail",
        location="Test Location",
        is_active=True,
    )

@pytest.fixture
def product(business):
    return Product.objects.create(
        fk_business=business,
        name="Test Product",
        price=10.0,
        is_active=True,
    )

@pytest.fixture
def instructions(user):
    return Instructions.objects.create(
        fk_user=user,
        title="Test Instructions",
        content="Test Content",
        is_active=True,
    )

def test_business_list_view(client, business, instructions):
    url = reverse("business:business.list")
    response = client.get(url)
    assert response.status_code == 200
    assert "businesses" in response.context
    assert "instructions" in response.context

def test_read_business_view(client, business, product):
    url = reverse("business:business.read", args=[business.id])
    response = client.get(url)
    assert response.status_code == 200
    assert response.context["business"] == business
    assert "products" in response.context

def test_create_business_view(client):
    url = reverse("business:business.create_or_update")
    data = {
        "name": "New Business",
        "type": "Retail",
        "location": "New Location",
    }
    response = client.post(url, data)
    assert response.status_code == 200
    assert Business.objects.filter(name="New Business").exists()

def test_update_business_view(client, business):
    url = reverse("business:business.create_or_update", args=[business.id])
    data = {
        "name": "Updated Business",
        "type": "Retail",
        "location": "Updated Location",
    }
    response = client.post(url, data)
    assert response.status_code == 200
    business.refresh_from_db()
    assert business.name == "Updated Business"

def test_delete_business_view(client, business):
    url = reverse("business:business.delete", args=[business.id])
    response = client.post(url)
    assert response.status_code == 302
    business.refresh_from_db()
    assert not business.is_active

def test_get_business_details_view(client, business):
    url = reverse("business:business.details", args=[business.id])
    response = client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == business.id
    assert data["name"] == business.name

def test_get_business_details_view_not_found(client):
    url = reverse("business:business.details", args=[999])
    response = client.get(url)
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
  
# REGRESSION TESTS
@pytest.mark.django_db
def test_business_list_view_pagination(client, user):
    # Create multiple businesses to test pagination
    for i in range(15):
        Business.objects.create(
            fk_user=user,
            name=f"Business {i}",
            type="Retail",
            location=f"Location {i}",
            is_active=True,
        )
    url = reverse("business:business.list")
    response = client.get(url, {"page": 2})
    assert response.status_code == 200
    assert "businesses" in response.context
    assert response.context["businesses"].number == 2  # Ensure second page is loaded

def test_read_business_view_pagination(client, business):
    # Create multiple products to test pagination
    for i in range(15):
        Product.objects.create(
            fk_business=business,
            name=f"Product {i}",
            price=10.0,
            is_active=True,
        )
    url = reverse("business:business.read", args=[business.id])
    response = client.get(url, {"page": 2})
    assert response.status_code == 200
    assert "products" in response.context
    assert response.context["products"].number == 2  # Ensure second page is loaded

def test_create_business_view_invalid_data(client):
    url = reverse("business:business.create_or_update")
    data = {
        "name": "",  # Invalid data (name is required)
        "type": "Retail",
        "location": "New Location",
    }
    response = client.post(url, data)
    assert response.status_code == 400
    assert not Business.objects.filter(location="New Location").exists()

def test_update_business_view_invalid_data(client, business):
    url = reverse("business:business.create_or_update", args=[business.id])
    data = {
        "name": "",  # Invalid data (name is required)
        "type": "Retail",
        "location": "Updated Location",
    }
    response = client.post(url, data)
    assert response.status_code == 400
    business.refresh_from_db()
    assert business.location != "Updated Location"

def test_delete_business_view_invalid_method(client, business):
    url = reverse("business:business.delete", args=[business.id])
    response = client.get(url)  # Invalid method (GET instead of POST)
    assert response.status_code == 405
    business.refresh_from_db()
    assert business.is_active  # Ensure business is not deleted

def test_get_business_details_view_inactive_business(client, business):
    business.is_active = False
    business.save()
    url = reverse("business:business.details", args=[business.id])
    response = client.get(url)
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    

