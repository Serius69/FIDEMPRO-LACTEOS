"""
ASGI config for findempro project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# Selecciona el settings según DJANGO_ENV. Si la variable falta o trae un
# valor no reconocido, el fallback es PRODUCTION (fail-safe: DEBUG=False,
# CORS cerrado, permisos estrictos) -- nunca al paquete 'findempro.settings'
# a secas, que internamente cae en development (DEBUG=True, CORS abierto,
# AllowAny). OJO: 'os.getenv(\"DJANGO_ENV\", \"development\")' NO sirve para
# esto -- el default se resolvería a la clave 'development' del mapa antes de
# llegar al .get(), anulando el fallback seguro. Por eso NO se pasa default
# a os.getenv aquí.
_env = os.getenv('DJANGO_ENV')
_settings_map = {
    'production': 'findempro.settings.production',
    'staging': 'findempro.settings.staging',
    'testing': 'findempro.settings.testing',
    'test': 'findempro.settings.testing',
    'development': 'findempro.settings.development',
}
os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    _settings_map.get(_env, 'findempro.settings.production')
)

application = get_asgi_application()
