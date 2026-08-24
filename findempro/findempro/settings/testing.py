"""
Django settings — TESTING
Optimizado para ejecución rápida de tests: SQLite local, sin Redis, sin email real.
"""
import os

# Debe definirse antes de importar base: base.py omite por completo la carga de
# archivos ``.env`` en test y nunca toma configuración de development.
os.environ["DJANGO_ENV"] = "testing"
os.environ.setdefault("SECRET_KEY", "django-insecure-testing-key-not-for-production")

from .base import *

DEBUG = True
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-testing-key-not-for-production')
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        'DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver'
    ).split(',')
    if host.strip()
]

# ─────────────────────────────────────────────
# Base de datos — SQLite aislada en memoria localmente, PostgreSQL opt-in en CI.
# Por defecto SIEMPRE SQLite: ninguna corrida local puede reutilizar una BD real.
# CI puede activar PostgreSQL explícitamente con USE_POSTGRES_TESTS=1.
# ─────────────────────────────────────────────
_use_postgres = os.getenv('USE_POSTGRES_TESTS', '0').lower() in ('1', 'true', 'yes')
_db_engine = os.getenv('DB_ENGINE', 'django.db.backends.sqlite3')
if not _use_postgres or _db_engine == 'django.db.backends.sqlite3':
    _db_engine = 'django.db.backends.sqlite3'
if _db_engine == 'django.db.backends.sqlite3':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': _db_engine,
            'NAME': os.getenv('DB_NAME', 'findempro_test'),
            'USER': os.getenv('DB_USER', 'findempro'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'TEST': {'NAME': os.getenv('DB_NAME', 'findempro_test')},
        }
    }

# ─────────────────────────────────────────────
# Cache — memoria local (sin Redis)
# ─────────────────────────────────────────────
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'findempro-test',
        'TIMEOUT': 60,
    }
}

# ─────────────────────────────────────────────
# Sesión en DB (sin Redis)
# ─────────────────────────────────────────────
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_SECURE = False

# ─────────────────────────────────────────────
# Email — descartado silenciosamente
# ─────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

# ─────────────────────────────────────────────
# Password hashers rápidos (tests corren más rápido)
# ─────────────────────────────────────────────
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# ─────────────────────────────────────────────
# Validación de contraseñas — deshabilitada en tests
# ─────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = []

# ─────────────────────────────────────────────
# AllAuth — sin verificación de email
# ─────────────────────────────────────────────
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_LOGOUT_ON_GET = True

# ─────────────────────────────────────────────
# Celery — síncrono (no requiere broker)
# El app Celery usa namespace='CELERY' (django.conf:settings), por lo que los
# nombres modernos (task_always_eager, …) son los que realmente surten efecto;
# se conservan los nombres legacy por compatibilidad.
# ─────────────────────────────────────────────
CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
# Guardar el retorno de las tareas eager en el backend, para poder recuperarlo
# vía AsyncResult(task_id) desde el endpoint de status (flujo async stateless).
CELERY_TASK_STORE_EAGER_RESULT = True
CELERY_RESULT_BACKEND = 'cache+memory://'

# ─────────────────────────────────────────────
# REST Framework — permisivo para tests
# ─────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    # Los throttles con scope propio (SimulateThrottle, etc.) exigen una tasa
    # declarada aunque las vistas los referencien vía throttle_classes; sin
    # esto DRF lanza ImproperlyConfigured. Tasas holgadas para no interferir.
    'DEFAULT_THROTTLE_RATES': {
        'simulate': '1000/hour',
        'report_pdf': '1000/hour',
        'export': '1000/hour',
        'public_simulate': '1000/hour',
    },
}

# ─────────────────────────────────────────────
# CORS — permisivo
# ─────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = True

# ─────────────────────────────────────────────
# Logging — mínimo (no ensuciar la salida de pytest)
# ─────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

# ─────────────────────────────────────────────
# django-axes — deshabilitado en tests (el backend Axes exige `request` en
# authenticate(); client.login() pasa request=None y rompería los tests).
# ─────────────────────────────────────────────
AXES_ENABLED = False

# ─────────────────────────────────────────────
# Dashboard — sin cache
# ─────────────────────────────────────────────
DASHBOARD_CONFIG['ENABLE_CHART_CACHING'] = False
