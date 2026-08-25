"""Todo throttle con scope propio tiene tasa declarada — en TODOS los entornos.

Cada módulo de settings reemplaza `REST_FRAMEWORK` entero en vez de extenderlo,
así que un scope declarado en `base.py` no llega a producción. Cuando falta,
DRF no "no limita": levanta `ImproperlyConfigured` al instanciar el throttle y
la vista devuelve 500.

Así estaba producción: `simulate`, `report_pdf` y `export` no figuraban, y con
ellos caían `/simulate/api/v1/simulate/`, `/simulate/async/`, `/forecast/` y
`/full-pipeline/` — justo lo que llama la SPA de `/app/`.

────────────────────────────────────────────────────────────────────────────
Por qué este archivo puede importar los settings de otros entornos
────────────────────────────────────────────────────────────────────────────
Este test es la única red que protege de esa regresión, y para tenderla tiene
que leer la configuración de entornos que no son el suyo. Dos condiciones lo
hacen posible sin mentirle a nadie:

1. `production` (y `staging`, que hereda de él) abortan al importarse si faltan
   SECRET_KEY o DJANGO_ALLOWED_HOSTS. Es una garantía deliberada de producción
   y NO se relaja: el test le entrega exactamente lo que producción exige, y
   `test_produccion_sigue_abortando_sin_allowed_hosts` comprueba que la
   garantía sigue en pie. (Antes el test no le entregaba nada, reventaba en el
   import y jamás llegó a auditar producción: la red estaba caída.)

2. Ningún módulo de entorno puede mutar in situ los contenedores heredados de
   `base`. `from .base import *` re-liga los MISMOS objetos, no copias, así que
   un `MIDDLEWARE.insert(...)` reescribía la configuración viva del proceso.
   Ver `test_importar_otro_entorno_no_toca_los_settings_vivos`.
"""
import contextlib
import copy
import importlib
import os
import sys

import pytest
from django.conf import settings as settings_vivos

from findempro import throttles as throttles_module

# Todo módulo de settings con vida propia. `e2e` hereda de `testing`, `staging`
# de `production` y `vercel` de `base`: se auditan igual, porque heredar no es
# garantía de nada si mañana alguno redefine `REST_FRAMEWORK`.
ENTORNOS = (
    'base',
    'development',
    'testing',
    'e2e',
    'production',
    'staging',
    'vercel',
)

# Lo que producción exige de verdad para arrancar. No es una excepción para el
# test: es su contrato, y el test lo respeta en vez de esquivarlo.
_ENV_DE_PRODUCCION = {
    'SECRET_KEY': 'clave-solo-para-auditar-settings-en-el-test',
    'DJANGO_ALLOWED_HOSTS': 'findempro.example.com',
    # `staging` inicializa Sentry si encuentra DSN; auditar settings no debe
    # abrir un cliente contra un servicio real.
    'SENTRY_DSN': '',
}

_ENTORNOS_QUE_EXIGEN_ENV = ('production', 'staging')


@contextlib.contextmanager
def _con_entorno(extra):
    """Fija variables de entorno y las restituye tal como estaban."""
    previo = {clave: os.environ.get(clave) for clave in extra}
    os.environ.update(extra)
    try:
        yield
    finally:
        for clave, valor in previo.items():
            if valor is None:
                os.environ.pop(clave, None)
            else:
                os.environ[clave] = valor


def _importar_settings(entorno):
    extra = _ENV_DE_PRODUCCION if entorno in _ENTORNOS_QUE_EXIGEN_ENV else {}
    with _con_entorno(extra):
        return importlib.import_module(f'findempro.settings.{entorno}')


def _clases_throttle():
    """Los throttles propios del proyecto (los de DRF ya traen tasa)."""
    from rest_framework.throttling import SimpleRateThrottle

    clases = []
    for nombre in dir(throttles_module):
        obj = getattr(throttles_module, nombre)
        if (isinstance(obj, type) and issubclass(obj, SimpleRateThrottle)
                and obj.__module__ == throttles_module.__name__
                and getattr(obj, 'scope', None)):
            clases.append(obj)
    return clases


def _scopes_declarados():
    return {clase.scope for clase in _clases_throttle()}


def test_hay_throttles_propios_que_revisar():
    assert _scopes_declarados(), 'no se detectó ningún throttle propio'


@pytest.mark.parametrize('entorno', ENTORNOS)
def test_cada_entorno_declara_todas_las_tasas(entorno):
    mod = _importar_settings(entorno)
    rest = getattr(mod, 'REST_FRAMEWORK', None)
    assert rest is not None, f'{entorno} no define REST_FRAMEWORK'

    tasas = rest.get('DEFAULT_THROTTLE_RATES') or {}
    faltantes = sorted(_scopes_declarados() - set(tasas))
    assert not faltantes, (
        f'{entorno}.py no declara tasa para {faltantes}: las vistas que usan '
        f'esos throttles responderán 500, no 429.'
    )


@pytest.mark.parametrize('entorno', ENTORNOS)
def test_cada_entorno_instancia_todos_los_throttles(entorno, monkeypatch):
    """Que la clave exista no basta: la tasa tiene que ser usable.

    DRF parsea la tasa al instanciar el throttle, y ahí es donde revienta. Una
    tasa mal escrita (`'20'` sin periodo, `'veinte/hour'`, `'20/año'`) pasa la
    comprobación de claves de arriba y vuelve a dar 500 en la misma vista.
    Aquí se instancian de verdad, que es lo que hace DRF al atender la
    petición.

    (Ojo con el alcance real: DRF sólo mira la PRIMERA letra del periodo, así
    que `'20/hora'` sí le sirve y lo interpreta como por hora. Esto verifica
    que la tasa es utilizable, no que esté escrita en inglés.)
    """
    from rest_framework.throttling import SimpleRateThrottle

    mod = _importar_settings(entorno)
    tasas = mod.REST_FRAMEWORK.get('DEFAULT_THROTTLE_RATES') or {}

    # DRF congela `THROTTLE_RATES` como atributo de clase al importarse, así que
    # `override_settings` no lo alcanza: para auditar OTRO entorno hay que
    # apuntarlo a las tasas de ese entorno.
    monkeypatch.setattr(SimpleRateThrottle, 'THROTTLE_RATES', tasas)

    for clase in _clases_throttle():
        throttle = clase()  # DRF lanza ImproperlyConfigured si la tasa no sirve
        assert throttle.num_requests and throttle.duration, (
            f'{entorno}.py: la tasa de {clase.__name__} '
            f'({tasas.get(clase.scope)!r}) no define un límite utilizable.'
        )


def test_produccion_sigue_abortando_sin_allowed_hosts():
    """Darle el entorno a producción no relajó su garantía de arranque.

    Los tests de arriba importan `production` con SECRET_KEY y
    DJANGO_ALLOWED_HOSTS porque producción las exige. Esto comprueba que
    seguirlas exigiendo es cierto: sin hosts, el módulo no se importa.
    """
    previo = sys.modules.pop('findempro.settings.production', None)
    try:
        with _con_entorno({'SECRET_KEY': 'x', 'DJANGO_ALLOWED_HOSTS': ''}):
            with pytest.raises(ValueError, match='DJANGO_ALLOWED_HOSTS'):
                importlib.import_module('findempro.settings.production')
    finally:
        sys.modules.pop('findempro.settings.production', None)
        if previo is not None:
            sys.modules['findempro.settings.production'] = previo


def test_importar_otro_entorno_no_toca_los_settings_vivos():
    """Auditar un entorno no puede reconfigurar el proceso que lo audita.

    `from .base import *` re-liga los mismos objetos que `base`, no copias.
    Cuando `production.py` hacía `MIDDLEWARE.insert(...)`, importarlo desde
    aquí metía WhiteNoise en el MIDDLEWARE vivo de la corrida de tests; lo
    mismo `development` con `INSTALLED_APPS += [...]` y todos con
    `DASHBOARD_CONFIG[...] = ...`. Copiar antes de mutar es la condición que
    hace auditables los settings de los demás entornos.
    """
    antes = {
        'MIDDLEWARE': list(settings_vivos.MIDDLEWARE),
        'INSTALLED_APPS': list(settings_vivos.INSTALLED_APPS),
        'DASHBOARD_CONFIG': copy.deepcopy(settings_vivos.DASHBOARD_CONFIG),
    }

    # Los módulos que mutan y no son el entorno vivo. Hay que importarlos sin
    # la caché de `sys.modules`, o el test se aprobaría solo.
    a_reimportar = ('production', 'staging', 'development', 'vercel')
    guardados = {
        f'findempro.settings.{e}': sys.modules.pop(f'findempro.settings.{e}', None)
        for e in a_reimportar
    }
    try:
        for entorno in a_reimportar:
            _importar_settings(entorno)
    finally:
        for nombre, modulo in guardados.items():
            if modulo is not None:
                sys.modules[nombre] = modulo
            else:
                sys.modules.pop(nombre, None)

    assert list(settings_vivos.MIDDLEWARE) == antes['MIDDLEWARE'], (
        'importar los settings de otro entorno alteró MIDDLEWARE en curso'
    )
    assert list(settings_vivos.INSTALLED_APPS) == antes['INSTALLED_APPS'], (
        'importar los settings de otro entorno alteró INSTALLED_APPS en curso'
    )
    assert settings_vivos.DASHBOARD_CONFIG == antes['DASHBOARD_CONFIG'], (
        'importar los settings de otro entorno alteró DASHBOARD_CONFIG en curso'
    )
