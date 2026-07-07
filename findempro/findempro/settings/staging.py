"""
Configuración para STAGING (pre-producción)
"""
from .production import *

# Sobrescribir configuraciones específicas de staging
ALLOWED_HOSTS = ['staging.findempro.com', 'test.findempro.com']

# Email - Usar servicio de prueba
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/tmp/app-messages'

# Menos restricciones de seguridad que producción
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Logging más detallado
LOGGING['root']['level'] = 'DEBUG'

# Sentry - Entorno staging
_STAGING_SENTRY_DSN = os.getenv('SENTRY_DSN', '')
if _STAGING_SENTRY_DSN:
    import sentry_sdk
    sentry_sdk.init(
        dsn=_STAGING_SENTRY_DSN,
        environment='staging'
    )

print("🧪 RUNNING IN STAGING MODE 🧪")