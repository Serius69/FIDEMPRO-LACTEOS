"""
Configuración para DESARROLLO
"""
from .base import *

# SEGURIDAD
DEBUG = True
SECRET_KEY = 'django-insecure-development-key-j%^*y0krq5^-#3lggoecxw!d7ad'
ALLOWED_HOSTS = ['*', 'localhost', '127.0.0.1', '.ngrok.io']

# APPS DE DESARROLLO
INSTALLED_APPS += [
    'debug_toolbar',
]

# MIDDLEWARE DE DESARROLLO
MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

# DATABASE - Local
DATABASES['default'].update({
    'OPTIONS': {
        'charset': 'utf8mb4',
    },
})

# DEBUG TOOLBAR
INTERNAL_IPS = ['127.0.0.1', 'localhost']
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: True,
}

# EMAIL - Consola
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CACHE - Local Memory
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,  # 5 minutos
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

# STATIC FILES
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

# MEDIA FILES
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# PASSWORD VALIDATION - Relajado
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 6}
    },
]

# ALLAUTH - Configuración de desarrollo
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_LOGOUT_ON_GET = True
SOCIALACCOUNT_LOGIN_ON_GET = True

# REST FRAMEWORK - Con interfaz navegable
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
}

# CORS - Permitir todo
CORS_ALLOW_ALL_ORIGINS = True

# CELERY - Sincrónico para desarrollo
CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

# LOGGING - Detallado
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}

# DASHBOARD
DASHBOARD_CONFIG['ENABLE_CHART_CACHING'] = False

print("🚀 RUNNING IN DEVELOPMENT MODE 🚀")