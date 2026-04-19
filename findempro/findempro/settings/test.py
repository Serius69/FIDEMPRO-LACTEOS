"""
Django settings — TEST / CI
Optimizados para velocidad: PostgreSQL real (como en prod), sin Redis, sin email.
Usado por pytest y el pipeline de GitHub Actions.
"""
from .base import *

# ─────────────────────────────────────────────
# Seguridad básica para tests
# ─────────────────────────────────────────────
DEBUG = False
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "ci-test-only-key-not-for-production-9f2j4k8x1q",
)
ALLOWED_HOSTS = ["*", "localhost", "127.0.0.1", "testserver"]

# ─────────────────────────────────────────────
# Base de datos — PostgreSQL igual que producción
# Las variables de entorno las inyecta el CI (GitHub Actions)
# ─────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "findempro_test"),
        "USER": os.getenv("DB_USER", "findempro_ci"),
        "PASSWORD": os.getenv("DB_PASSWORD", "ci_password_2024"),
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "CONN_MAX_AGE": 0,
        "TEST": {
            "NAME": os.getenv("DB_NAME", "findempro_test"),
        },
    }
}

# ─────────────────────────────────────────────
# Cache — memoria local (sin Redis en CI)
# ─────────────────────────────────────────────
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-cache",
    }
}

# ─────────────────────────────────────────────
# Sesión en DB (sin Redis)
# ─────────────────────────────────────────────
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_SECURE = False

# ─────────────────────────────────────────────
# Email — suprimir en tests
# ─────────────────────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# ─────────────────────────────────────────────
# Passwords — hasher rápido para acelerar tests
# MD5Passwordhasher es ~10x más rápido en tests
# ─────────────────────────────────────────────
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# ─────────────────────────────────────────────
# Archivos estáticos y media
# ─────────────────────────────────────────────
STATIC_URL = "/static/"
MEDIA_URL = "/media/"
MEDIA_ROOT = "/tmp/findempro_test_media/"

# WhiteNoise — desactivar en tests para evitar collectstatic
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# ─────────────────────────────────────────────
# Celery — síncrono en tests (sin broker real)
# ─────────────────────────────────────────────
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# ─────────────────────────────────────────────
# AllAuth — sin verificación de email
# ─────────────────────────────────────────────
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_LOGOUT_ON_GET = True

# ─────────────────────────────────────────────
# Logging — solo errores en CI para no ensuciar output
# ─────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "null": {"class": "logging.NullHandler"},
    },
    "root": {
        "handlers": ["null"],
        "level": "CRITICAL",
    },
}

# ─────────────────────────────────────────────
# Dashboard — sin cache
# ─────────────────────────────────────────────
if "DASHBOARD_CONFIG" in dir():
    DASHBOARD_CONFIG["ENABLE_CHART_CACHING"] = False

# ─────────────────────────────────────────────
# REST Framework — solo JSON en tests
# ─────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}
