"""Todo throttle con scope propio tiene tasa declarada — en TODOS los entornos.

Cada módulo de settings reemplaza `REST_FRAMEWORK` entero en vez de extenderlo,
así que un scope declarado en `base.py` no llega a producción. Cuando falta,
DRF no "no limita": levanta `ImproperlyConfigured` al instanciar el throttle y
la vista devuelve 500.

Así estaba producción: `simulate`, `report_pdf` y `export` no figuraban, y con
ellos caían `/simulate/api/v1/simulate/`, `/simulate/async/`, `/forecast/` y
`/full-pipeline/` — justo lo que llama la SPA de `/app/`.
"""
import importlib

import pytest

from findempro import throttles as throttles_module

ENTORNOS = ('base', 'development', 'production', 'testing')


def _scopes_declarados():
    """Los scopes que usa cada throttle propio del proyecto."""
    from rest_framework.throttling import SimpleRateThrottle

    scopes = set()
    for nombre in dir(throttles_module):
        obj = getattr(throttles_module, nombre)
        if (isinstance(obj, type) and issubclass(obj, SimpleRateThrottle)
                and obj.__module__ == throttles_module.__name__):
            scope = getattr(obj, 'scope', None)
            if scope:
                scopes.add(scope)
    return scopes


def test_hay_throttles_propios_que_revisar():
    assert _scopes_declarados(), 'no se detectó ningún throttle propio'


@pytest.mark.parametrize('entorno', ENTORNOS)
def test_cada_entorno_declara_todas_las_tasas(entorno):
    mod = importlib.import_module(f'findempro.settings.{entorno}')
    rest = getattr(mod, 'REST_FRAMEWORK', None)
    assert rest is not None, f'{entorno} no define REST_FRAMEWORK'

    tasas = rest.get('DEFAULT_THROTTLE_RATES') or {}
    faltantes = sorted(_scopes_declarados() - set(tasas))
    assert not faltantes, (
        f'{entorno}.py no declara tasa para {faltantes}: las vistas que usan '
        f'esos throttles responderán 500, no 429.'
    )
