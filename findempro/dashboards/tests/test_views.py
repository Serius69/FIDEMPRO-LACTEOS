import itertools

import pytest
from django.urls import reverse

from business.models import Business

# Nombres de URL reales (dashboards/urls.py, app_name='dashboard')
URL_INDEX = "dashboard:index"
URL_ADMIN = "dashboard:dashboard.admin"
URL_USER = "dashboard:dashboard.user"
URL_BUSINESS_LIST = "business:business.list"
URL_LOGIN = "account_login"  # settings.LOGIN_URL = "account_login" (allauth)

_counter = itertools.count(1)


def _make_business(user, active=True):
    """Crea un Business valido con nombre unico (UNIQUE name+fk_user activos)."""
    n = next(_counter)
    return Business.objects.create(
        name=f"Negocio {n}",
        type=1,
        location="La Paz",
        description="Negocio de prueba",
        fk_user=user,
        is_active=active,
    )


# UNIT TESTS

@pytest.mark.django_db
def test_index_view_authenticated_user(client, django_user_model):
    django_user_model.objects.create_user(username="testuser", password="password")
    client.login(username="testuser", password="password")
    url = reverse(URL_INDEX)
    response = client.get(url)
    assert response.status_code == 200
    assert "form" in response.context


@pytest.mark.django_db
def test_index_view_post_valid_form(client, django_user_model):
    django_user_model.objects.create_user(username="testuser", password="password")
    client.login(username="testuser", password="password")
    url = reverse(URL_INDEX)
    # RegisterElementsForm solo exige accept_terms; con eso es valido -> redirect
    data = {"accept_terms": "on"}
    response = client.post(url, data)
    assert response.status_code == 302  # Redirect tras submit valido


@pytest.mark.django_db
def test_dashboard_admin_view(client, django_user_model):
    django_user_model.objects.create_user(username="adminuser", password="password")
    client.login(username="adminuser", password="password")
    url = reverse(URL_ADMIN)
    response = client.get(url)
    assert response.status_code == 200
    # El contexto expone estadisticas de usuarios con estas claves reales
    assert "users_count" in response.context
    assert "new_users_last_month" in response.context


@pytest.mark.django_db
def test_dashboard_user_view(client, django_user_model):
    user = django_user_model.objects.create_user(username="testuser", password="password")
    business = _make_business(user)
    client.login(username="testuser", password="password")
    session = client.session
    session["business_id"] = business.id
    session.save()
    url = reverse(URL_USER)
    response = client.get(url)
    assert response.status_code == 200
    assert "greeting" in response.context
    assert "business" in response.context
    assert response.context["roi_available"] is False
    assert b"Falta inversi" in response.content


@pytest.mark.django_db
def test_dashboard_user_view_no_business(client, django_user_model):
    django_user_model.objects.create_user(username="testuser", password="password")
    client.login(username="testuser", password="password")
    url = reverse(URL_USER)
    response = client.get(url)
    assert response.status_code == 302  # Redirect a lista de negocios


# REGRESSION TESTS
@pytest.mark.django_db
def test_dashboard_user_authenticated_with_business(client, django_user_model):
    user = django_user_model.objects.create_user(username="testuser", password="password")
    business = _make_business(user)
    client.login(username="testuser", password="password")
    session = client.session
    session["business_id"] = business.id
    session.save()
    url = reverse(URL_USER)
    response = client.get(url)
    assert response.status_code == 200
    assert "greeting" in response.context
    assert "business" in response.context
    assert response.context["business"].id == business.id


@pytest.mark.django_db
def test_dashboard_user_authenticated_no_business(client, django_user_model):
    django_user_model.objects.create_user(username="testuser", password="password")
    client.login(username="testuser", password="password")
    url = reverse(URL_USER)
    response = client.get(url)
    assert response.status_code == 302  # Redirect a lista de negocios
    assert response.url == reverse(URL_BUSINESS_LIST)


@pytest.mark.django_db
def test_dashboard_user_unauthenticated(client):
    url = reverse(URL_USER)
    response = client.get(url)
    assert response.status_code == 302  # Redirect a login
    assert response.url.startswith(reverse(URL_LOGIN))


@pytest.mark.django_db
def test_dashboard_user_invalid_business_id_in_session(client, django_user_model):
    django_user_model.objects.create_user(username="testuser", password="password")
    client.login(username="testuser", password="password")
    session = client.session
    session["business_id"] = "invalid_id"
    session.save()
    url = reverse(URL_USER)
    response = client.get(url)
    assert response.status_code == 302  # Redirect a lista de negocios
    assert response.url == reverse(URL_BUSINESS_LIST)


@pytest.mark.django_db
def test_dashboard_user_multiple_businesses(client, django_user_model):
    user = django_user_model.objects.create_user(username="testuser", password="password")
    _make_business(user)
    _make_business(user)
    client.login(username="testuser", password="password")
    # Sin business_id en sesion -> redirect a lista de negocios
    url = reverse(URL_USER)
    response = client.get(url)
    assert response.status_code == 302
    assert response.url == reverse(URL_BUSINESS_LIST)

# INTEGRATION TESTS
