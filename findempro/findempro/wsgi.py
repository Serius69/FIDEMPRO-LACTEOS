"""
WSGI config for findempro project.
Selecciona el settings correcto según DJANGO_ENV.
"""
import os
from django.core.wsgi import get_wsgi_application

# Bug latente (mismo hallazgo que asgi.py/check_setup.py): pasar
# default='development' a os.getenv anulaba el fallback seguro de abajo, ya
# que la clave 'development' existe en el mapa y el .get() la resolvía antes
# de llegar al valor por defecto -- sin DJANGO_ENV, esto SIEMPRE terminaba en
# development (DEBUG=True) pese a la intención de caer a producción.
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

application = get_wsgi_application()
