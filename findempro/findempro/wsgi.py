"""
WSGI config for findempro project.
Selecciona el settings correcto según DJANGO_ENV.
"""
import os
from django.core.wsgi import get_wsgi_application

_env = os.getenv('DJANGO_ENV', 'development')
_settings_map = {
    'production': 'findempro.settings.production',
    'staging': 'findempro.settings.staging',
    'development': 'findempro.settings.development',
}
os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    _settings_map.get(_env, 'findempro.settings.production')
)

application = get_wsgi_application()
