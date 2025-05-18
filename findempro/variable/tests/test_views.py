import pytest
from django.urls import reverse
from django.test import Client
from django.contrib.auth.models import User
from variable.models import Variable, Equation
from product.models import Product
from business.models import Business
from pages.models import Instructions

@pytest.fixture
def client():
    return Client()

@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="password")

@pytest.fixture
def business(user):
    return Business.objects.create(name="Test Business", is_active=True, fk_user=user)

@pytest.fixture
def product(business):
    return Product.objects.create(name="Test Product", is_active=True, fk_business=business)

@pytest.fixture
def variable(product):
    return Variable.objects.create(name="Test Variable", is_active=True, fk_product=product)

@pytest.fixture
def equation(variable):
    return Equation.objects.create(name="Test Equation", is_active=True, fk_variable1=variable)

def test_variable_list_view(client, user, business, product, variable):
    client.login(username="testuser", password="password")
    url = reverse("variable:variable.list")
    response = client.get(url)
    assert response.status_code == 200
    assert "variables" in response.context
    assert "products" in response.context

def test_variable_overview_view(client, user, variable):
    client.login(username="testuser", password="password")
    url = reverse("variable:variable.overview", args=[variable.id])
    response = client.get(url)
    assert response.status_code == 200
    assert "variable" in response.context
    assert "variables_related" in response.context
    assert "equations" in response.context

def test_create_variable_view(client, user, product):
    client.login(username="testuser", password="password")
    url = reverse("variable:variable.create")
    data = {
        "name": "New Variable",
        "type": "Integer",
        "fk_product": product.id,
    }
    response = client.post(url, data)
    assert response.status_code == 200
    assert Variable.objects.filter(name="New Variable").exists()

def test_update_variable_view(client, user, variable):
    client.login(username="testuser", password="password")
    url = reverse("variable:variable.update", args=[variable.id])
    data = {
        "name": "Updated Variable",
        "type": variable.type,
        "fk_product": variable.fk_product.id,
    }
    response = client.post(url, data)
    assert response.status_code == 200
    variable.refresh_from_db()
    assert variable.name == "Updated Variable"

def test_delete_variable_view(client, user, variable):
    client.login(username="testuser", password="password")
    url = reverse("variable:variable.delete", args=[variable.id])
    response = client.post(url)
    assert response.status_code == 302
    variable.refresh_from_db()
    assert not variable.is_active

def test_get_variable_details_view(client, user, variable):
    client.login(username="testuser", password="password")
    url = reverse("variable:variable.details", args=[variable.id])
    response = client.get(url)
    assert response.status_code == 200
    assert response.json()["name"] == variable.name

def test_create_equation_view(client, user, variable):
    client.login(username="testuser", password="password")
    url = reverse("variable:equation.create")
    data = {
        "name": "New Equation",
        "fk_variable1": variable.id,
        "expression": "x + 2 = 0",
    }
    response = client.post(url, data)
    assert response.status_code == 200
    assert Equation.objects.filter(name="New Equation").exists()

def test_delete_equation_view(client, user, equation):
    client.login(username="testuser", password="password")
    url = reverse("variable:equation.delete", args=[equation.id])
    response = client.post(url)
    assert response.status_code == 302
    equation.refresh_from_db()
    assert not equation.is_active

def test_solve_equation_view(client, user):
    client.login(username="testuser", password="password")
    url = reverse("variable:equation.solve")
    data = {"equation": "x**2 - 4"}
    response = client.post(url, data)
    assert response.status_code == 200
    assert "solution" in response.context