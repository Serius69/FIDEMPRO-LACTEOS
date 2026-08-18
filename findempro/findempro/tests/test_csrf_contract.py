"""
Contrato CSRF del producto.

El E2E de navegador destapó que ``CSRF_COOKIE_HTTPONLY = True`` rompía **todos**
los POST hechos por fetch: el JS arma la cabecera ``X-CSRFToken`` leyendo
``document.cookie``, y con HttpOnly esa lectura devuelve vacío, así que Django
respondía 403. El arreglo vive en los settings, y hasta ahora nada impedía
revertirlo: la única señal era un E2E que no corre en CI.

Estas pruebas fijan las dos mitades del contrato a la vez, que es lo que importa:
la cookie tiene que ser legible por JavaScript **y** la protección CSRF tiene que
seguir activa. Un cambio que rompa cualquiera de las dos falla aquí.
"""
import re
from pathlib import Path

import pytest
from django.conf import settings
from django.test import Client
from django.urls import reverse

BASE_DIR = Path(settings.BASE_DIR)

# Pantallas que arman X-CSRFToken leyendo la cookie desde JavaScript.
COOKIE_READER = re.compile(r"getCookie\(\s*['\"]csrftoken['\"]\s*\)")


def _javascript_sources():
    for root in (BASE_DIR / "static" / "js", BASE_DIR / "templates"):
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if path.suffix in {".js", ".html"} and path.is_file():
                yield path


@pytest.mark.django_db
def test_csrf_cookie_is_readable_by_javascript():
    """La cookie no puede llevar HttpOnly: el fetch del producto la lee."""
    client = Client()
    client.get(reverse("account_login"))
    cookie = client.cookies.get(settings.CSRF_COOKIE_NAME)
    assert cookie is not None, "la vista no emitió la cookie CSRF"
    assert not cookie["httponly"], (
        "la cookie CSRF volvió a emitirse con HttpOnly: el JavaScript del producto "
        "no puede leerla y todo POST por fetch responde 403"
    )
    assert settings.CSRF_COOKIE_HTTPONLY is False


def test_the_screens_that_read_the_cookie_still_exist():
    """Evita que la prueba de arriba quede vacía si el patrón cambia de forma."""
    readers = [p for p in _javascript_sources() if COOKIE_READER.search(p.read_text(
        encoding="utf-8", errors="ignore"))]
    assert readers, (
        "ningún archivo lee ya getCookie('csrftoken'); si el producto cambió de "
        "mecanismo, revisar si HttpOnly puede volver a activarse"
    )


@pytest.mark.django_db
def test_post_without_csrf_token_is_rejected():
    """La protección sigue activa: sin token, el POST no pasa."""
    client = Client(enforce_csrf_checks=True)
    response = client.post(reverse("account_login"),
                           {"login": "quien-sea", "password": "lo-que-sea"})
    assert response.status_code == 403


@pytest.mark.django_db
def test_post_with_the_cookie_token_is_accepted():
    """El camino legítimo —token de la cookie en la cabecera— no da 403."""
    client = Client(enforce_csrf_checks=True)
    client.get(reverse("account_login"))
    token = client.cookies[settings.CSRF_COOKIE_NAME].value
    response = client.post(
        reverse("account_login"),
        {"login": "quien-sea", "password": "lo-que-sea"},
        HTTP_X_CSRFTOKEN=token,
    )
    # Las credenciales son falsas a propósito: lo que se afirma es que el
    # rechazo no viene del CSRF.
    assert response.status_code != 403
