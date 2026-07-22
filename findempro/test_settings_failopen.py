"""
[P1] Settings fail-open a development.

findempro/asgi.py y check_setup.py hacían
``os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'findempro.settings')`` --
y ``findempro/settings/__init__.py`` resuelve ``DJANGO_ENV`` no seteada como
``'development'`` (DEBUG=True, CORS abierto, permisos AllowAny). Si en
producción faltara la variable de entorno ``DJANGO_ENV`` (p.ej. un ConfigMap
mal aplicado), el proceso ASGI arrancaría silenciosamente con settings de
desarrollo inseguros en vez de fallar o caer a producción.

El fix replica el patrón ya usado en ``findempro/wsgi.py``: un mapeo
explícito con fallback a ``findempro.settings.production`` cuando
``DJANGO_ENV`` falta o no se reconoce.

Nota de entorno: este venv de desarrollo no tiene psycopg2 instalado, así que
``django.setup()`` con settings de producción (backend postgresql) revienta
más adelante (ImproperlyConfigured) -- eso es una limitación del venv local,
no del fix. Por eso los tests corren el archivo real vía ``runpy`` tolerando
esa excepción, y verifican lo que realmente nos importa: a qué
``DJANGO_SETTINGS_MODULE`` resolvió *antes* de ese punto, y que
``settings.DEBUG`` (que sí puede leerse sin poblar el registro de apps) sea
``False``.
"""
import os
import subprocess
import sys

import pytest

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

_PROBE = """
import os, runpy
try:
    runpy.run_path({target!r}, run_name="__main__")
except BaseException:
    pass
print("SETTINGS_MODULE=" + os.environ.get("DJANGO_SETTINGS_MODULE", ""))
try:
    from django.conf import settings
    print("DEBUG=" + str(settings.DEBUG))
except Exception as e:
    print("DEBUG_ERROR=" + str(e))
"""


def _clean_env(**extra):
    env = os.environ.copy()
    env.pop('DJANGO_ENV', None)
    env.pop('DJANGO_SETTINGS_MODULE', None)
    # Requeridos por production.py para que el módulo de settings cargue sin
    # reventar (SECRET_KEY/ALLOWED_HOSTS son validados al importar el módulo;
    # no hace falta psycopg2 ni conexión real a la base para esto).
    env.setdefault('SECRET_KEY', 'test-secret-key-not-real')
    env.setdefault('DJANGO_ALLOWED_HOSTS', 'testserver')
    env.update(extra)
    return env


def _run_probe(target):
    result = subprocess.run(
        [sys.executable, "-c", _PROBE.format(target=target)],
        cwd=BASE_DIR, env=_clean_env(), capture_output=True, text=True, timeout=60,
    )
    lines = result.stdout.strip().splitlines()
    values = dict(line.split("=", 1) for line in lines if "=" in line)
    return values, result


def test_asgi_without_django_env_resolves_to_production():
    values, result = _run_probe("findempro/asgi.py")
    assert values.get("SETTINGS_MODULE") == "findempro.settings.production", result.stdout
    assert values.get("SETTINGS_MODULE") != "findempro.settings"   # el paquete a secas cae en development
    assert values.get("DEBUG") == "False", result.stdout


def test_check_setup_without_django_env_resolves_to_production():
    values, result = _run_probe("check_setup.py")
    assert values.get("SETTINGS_MODULE") == "findempro.settings.production", result.stdout
    assert values.get("SETTINGS_MODULE") != "findempro.settings"
    assert values.get("DEBUG") == "False", result.stdout


def test_wsgi_reference_behavior_unchanged():
    """wsgi.py ya tenía el patrón correcto -- verifica que sigue igual."""
    values, result = _run_probe("findempro/wsgi.py")
    assert values.get("SETTINGS_MODULE") == "findempro.settings.production", result.stdout
    assert values.get("DEBUG") == "False", result.stdout
