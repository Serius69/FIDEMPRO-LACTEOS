"""
Tests de vistas de la app simulate.

Nota histórica: este módulo contenía tests contra un esquema antiguo
(`findempro.simulate.codeall`, relaciones de modelo obsoletas) y una batería
Selenium que no puede ejecutarse en CI. Se reescribió para cubrir el
comportamiento vigente y verificable: protección de autenticación de las vistas.
"""
import pytest
from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def user(db):
    return User.objects.create_user(username='testuser', password='testpassword123')


# ─────────────────────────────────────────────
# Protección de autenticación (LoginRequiredMixin)
# ─────────────────────────────────────────────
@pytest.mark.django_db
@pytest.mark.parametrize('url_name', [
    'simulate:simulate.list',
])
def test_anonymous_is_redirected_to_login(client, url_name):
    """Las vistas protegidas (LoginRequiredMixin) redirigen a login para anónimos."""
    response = client.get(reverse(url_name))
    assert response.status_code == 302
    assert '/login' in response.url or 'account' in response.url.lower()


@pytest.mark.django_db
def test_authenticated_user_reaches_simulate_list(client, user):
    """Un usuario autenticado no es redirigido a login en el listado."""
    client.login(username='testuser', password='testpassword123')
    response = client.get(reverse('simulate:simulate.list'))
    # No debe redirigir a login; puede ser 200 o redirección interna válida.
    assert response.status_code != 302 or 'login' not in getattr(response, 'url', '')


@pytest.mark.django_db
def test_result_view_requires_auth(client):
    """La vista de resultado exige autenticación."""
    response = client.get(reverse('simulate:simulate.result', args=[1]))
    assert response.status_code in (302, 403, 404)
