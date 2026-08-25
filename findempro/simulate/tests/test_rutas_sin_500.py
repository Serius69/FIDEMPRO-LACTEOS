"""Ninguna ruta autenticada conocida puede responder 5xx.

Origen concreto: `/simulate/` —la raíz de la app, detrás de login— estaba servida por un
`TemplateView` cuya plantilla (`simulate/apps.html`) nunca existió. Cualquier usuario con
sesión que la visitara recibía `TemplateDoesNotExist`, o sea 500. Nada la enlazaba, así que
ningún test la tocaba y ningún menú la exponía; sólo aparecía si alguien escribía la URL o
tenía el marcador.

Esa clase de defecto no se detecta probando lo que la UI enlaza. Se detecta recorriendo las
rutas registradas y exigiendo que ninguna reviente.
"""
from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse


@pytest.fixture
def usuario(db):
    User = get_user_model()
    return User.objects.create_user(
        username='ruta-test', email='ruta-test@findempro.test', password='clave-desechable-1234')


@pytest.fixture
def cliente_autenticado(usuario):
    c = Client()
    c.force_login(usuario)
    return c


# Rutas GET sin parámetros que un usuario con sesión puede alcanzar escribiéndolas.
# Se afirma "no 5xx", no un status concreto: 200, 302 (redirect o login) y 404 son
# respuestas legítimas; 5xx nunca lo es.
RUTAS_GET_SIN_PARAMETROS = [
    'simulate:simulate.index',
    'simulate:simulate.show',
    'simulate:simulate.list',
    'simulate:simulate.add',
]


@pytest.mark.parametrize('nombre', RUTAS_GET_SIN_PARAMETROS)
def test_ruta_autenticada_no_responde_5xx(cliente_autenticado, nombre):
    respuesta = cliente_autenticado.get(reverse(nombre), follow=False)
    assert respuesta.status_code < 500, (
        f'{nombre} respondió {respuesta.status_code}; una ruta alcanzable no puede dar 5xx'
    )


@pytest.mark.parametrize('nombre', RUTAS_GET_SIN_PARAMETROS)
def test_ruta_sin_sesion_no_responde_5xx(client, nombre):
    """Sin sesión tampoco: lo esperable es un redirect al login, nunca un error de servidor."""
    respuesta = client.get(reverse(nombre), follow=False)
    assert respuesta.status_code < 500, f'{nombre} respondió {respuesta.status_code} sin sesión'


def test_simulate_index_lleva_a_la_pantalla_real(cliente_autenticado):
    """`/simulate/` es la raíz de la app: tiene que dejar al usuario en la pantalla que sirve.

    Este es el test que habría fallado antes del arreglo — con la plantilla inexistente esto
    era 500, no 302.
    """
    respuesta = cliente_autenticado.get(reverse('simulate:simulate.index'), follow=False)
    assert respuesta.status_code == 302, f'se esperaba redirect, llegó {respuesta.status_code}'
    assert respuesta['Location'] == reverse('simulate:simulate.show')


def test_simulate_index_sin_sesion_pide_login(client):
    """El redirect no puede saltarse el login: la vista sigue detrás de LoginRequiredMixin."""
    respuesta = client.get(reverse('simulate:simulate.index'), follow=False)
    assert respuesta.status_code == 302
    assert reverse('simulate:simulate.show') not in respuesta['Location']
    assert 'login' in respuesta['Location'].lower()
