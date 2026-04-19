"""
Django settings — DESARROLLO
Hereda de base.py con configuración relajada para desarrollo local.
"""
from .base import *

# ─────────────────────────────────────────────
# Desarrollo
# ─────────────────────────────────────────────
DEBUG = True
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-dev-only-key-j%^*y0krq5^-#3lggoecxw')
ALLOWED_HOSTS = ['*', 'localhost', '127.0.0.1', '.ngrok.io', '.ngrok-free.app']

# ─────────────────────────────────────────────
# Apps adicionales solo en desarrollo
# ─────────────────────────────────────────────
try:
    import debug_toolbar
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1', 'localhost']
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
    }
except ImportError:
    pass

# ─────────────────────────────────────────────
# Base de datos — soporta MySQL o PostgreSQL local
# ─────────────────────────────────────────────
_db_engine = os.getenv('DB_ENGINE', 'django.db.backends.postgresql')
DATABASES = {
    'default': {
        'ENGINE': _db_engine,
        'NAME': os.getenv('DB_NAME', 'findempro_dev'),
        'USER': os.getenv('DB_USER', 'findempro'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 0,
    }
}

# ─────────────────────────────────────────────
# Cache — memoria local (sin necesidad de Redis)
# ─────────────────────────────────────────────
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'findempro-dev',
        'TIMEOUT': 300,
        'OPTIONS': {'MAX_ENTRIES': 1000},
    }
}

# ─────────────────────────────────────────────
# Sesión en DB (no requiere Redis)
# ─────────────────────────────────────────────
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_SECURE = False

# ─────────────────────────────────────────────
# Email — consola
# ─────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ─────────────────────────────────────────────
# Password validation relajada
# ─────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 6}},
]

# ─────────────────────────────────────────────
# AllAuth — sin verificación de email
# ─────────────────────────────────────────────
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_LOGOUT_ON_GET = True
SOCIALACCOUNT_LOGIN_ON_GET = True

# ─────────────────────────────────────────────
# REST Framework — interfaz navegable
# ─────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
}

# ─────────────────────────────────────────────
# CORS — permisivo en desarrollo
# ─────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = True

# ─────────────────────────────────────────────
# Celery — síncrono en desarrollo
# ─────────────────────────────────────────────
CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

# ─────────────────────────────────────────────
# Logging — detallado
# ─────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'dev': {
            'format': '[{levelname}] {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'dev',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',  # cambiar a DEBUG para ver SQL queries
            'propagate': False,
        },
    },
}

# ─────────────────────────────────────────────
# Dashboard — sin cache en desarrollo
# ─────────────────────────────────────────────
DASHBOARD_CONFIG['ENABLE_CHART_CACHING'] = False
