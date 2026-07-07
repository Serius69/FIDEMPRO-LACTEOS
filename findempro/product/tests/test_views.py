import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from django.test import Client
from product.models import Product, Area
from business.models import Business


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="password")


@pytest.fixture
def authenticated_client(client, user):
    client.login(username="testuser", password="password")
    return client


@pytest.fixture
def business(user):
    return Business.objects.create(
        name="Test Business",
        type=1,
        location="La Paz",
        description="Negocio de prueba",
        fk_user=user,
        is_active=True,
    )


@pytest.fixture
def product(business):
    return Product.objects.create(
        name="Test Product",
        type=1,
        is_active=True,
        fk_business=business,
        description="Test Description",
    )


@pytest.fixture
def area(product):
    return Area.objects.create(
        name="Test Area",
        is_active=True,
        fk_product=product,
        description="Test Area Description",
    )


def test_product_list_view(authenticated_client, business, product):
    url = reverse("product:product.list")
    response = authenticated_client.get(url)
    assert response.status_code == 200
    assert "products" in response.context
    assert "businesses" in response.context


def test_read_product_view(authenticated_client, product):
    url = reverse("product:product.overview", args=[product.id])
    response = authenticated_client.get(url)
    assert response.status_code == 200
    assert response.context["product"] == product


def test_area_overview_view(authenticated_client, area):
    url = reverse("product:area.overview", args=[area.id])
    response = authenticated_client.get(url)
    assert response.status_code == 200
    assert response.context["area"] == area


def test_create_or_update_product_view(authenticated_client, business):
    url = reverse("product:product.create")
    data = {
        "name": "New Product",
        "type": 1,
        "fk_business": business.id,
        "description": "New Product Description",
    }
    response = authenticated_client.post(url, data)
    assert response.status_code == 200
    assert Product.objects.filter(name="New Product").exists()


def test_delete_product_view(authenticated_client, product):
    url = reverse("product:product.delete", args=[product.id])
    response = authenticated_client.post(url)
    product.refresh_from_db()
    assert response.status_code == 302
    assert not product.is_active


def test_get_product_details_view(authenticated_client, product):
    url = reverse("product:product.get_details", args=[product.id])
    response = authenticated_client.get(url)
    assert response.status_code == 200
    assert response.json()["name"] == product.name


def test_create_or_update_area_view(authenticated_client, product):
    url = reverse("product:area.create")
    data = {
        "name": "New Area",
        "fk_product": product.id,
        "description": "New Area Description",
    }
    response = authenticated_client.post(url, data)
    assert response.status_code == 200
    assert Area.objects.filter(name="New Area").exists()


def test_delete_area_view(authenticated_client, area):
    url = reverse("product:area.delete", args=[area.id])
    response = authenticated_client.post(url)
    area.refresh_from_db()
    assert response.status_code == 302
    assert not area.is_active


def test_get_area_details_view(authenticated_client, area):
    url = reverse("product:area.get_details", args=[area.id])
    response = authenticated_client.get(url)
    assert response.status_code == 200
    assert response.json()["name"] == area.name


# REGRESSION TESTS
@pytest.mark.django_db
def test_read_product_view_authenticated(authenticated_client, product):
    url = reverse("product:product.overview", args=[product.id])
    response = authenticated_client.get(url)
    assert response.status_code == 200
    assert "variables_product" in response.context
    assert "product" in response.context
    assert response.context["product"] == product
    assert "simulations" in response.context
    assert "reports" in response.context
    assert "areas" in response.context
    assert "demands" in response.context
    assert "products" in response.context


@pytest.mark.django_db
def test_read_product_view_unauthenticated(client, product):
    url = reverse("product:product.overview", args=[product.id])
    response = client.get(url)
    assert response.status_code == 302  # Redirect to login page
    assert response.url.startswith(reverse("account_login"))


@pytest.mark.django_db
def test_read_product_view_nonexistent_product(authenticated_client):
    url = reverse("product:product.overview", args=[9999])  # Non-existent product ID
    response = authenticated_client.get(url)
    # La vista captura el Http404 y redirige a la lista con un mensaje (comportamiento vigente)
    assert response.status_code == 302
    assert response.url == reverse("product:product.list")


@pytest.mark.django_db
def test_read_product_view_error_handling(authenticated_client, product, mocker):
    mocker.patch("product.views.get_object_or_404", side_effect=Exception("Test exception"))
    url = reverse("product:product.overview", args=[product.id])
    response = authenticated_client.get(url)
    # Cualquier excepción inesperada se captura y redirige a la lista (comportamiento vigente)
    assert response.status_code == 302
    assert response.url == reverse("product:product.list")


@pytest.mark.django_db
def test_read_product_view_context(authenticated_client, product):
    url = reverse("product:product.overview", args=[product.id])
    response = authenticated_client.get(url)
    assert response.status_code == 200
    assert "variables_product" in response.context
    assert "product" in response.context
    assert response.context["product"] == product
    assert "simulations" in response.context
    assert "reports" in response.context
    assert "areas" in response.context
    assert "demands" in response.context
    assert "products" in response.context


@pytest.mark.django_db
def test_read_product_view_pagination(authenticated_client, product, mocker):
    mock_paginate = mocker.patch(
        "product.views.paginate",
        side_effect=lambda request, queryset, per_page: queryset,
    )
    url = reverse("product:product.overview", args=[product.id])
    response = authenticated_client.get(url)
    assert response.status_code == 200
    assert mock_paginate.call_count == 2  # variables_product y simulations
