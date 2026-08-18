"""
Django settings — PRODUCCIÓN
Hereda de base.py y sobreescribe todo lo necesario para producción real.
"""
from .base import *
import logging

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Seguridad obligatoria
# ─────────────────────────────────────────────
DEBUG = False

_secret = os.getenv('SECRET_KEY')
if not _secret:
    raise ValueError("[PRODUCCION] SECRET_KEY no está configurada. Defínela en el .env")
SECRET_KEY = _secret

_hosts_raw = os.getenv('DJANGO_ALLOWED_HOSTS', '')
ALLOWED_HOSTS = [h.strip() for h in _hosts_raw.split(',') if h.strip()]
if not ALLOWED_HOSTS:
    raise ValueError("[PRODUCCION] DJANGO_ALLOWED_HOSTS no está configurada.")

# ─────────────────────────────────────────────
# Apps adicionales de producción
# ─────────────────────────────────────────────
# Nota: django_prometheus ya está en THIRDPARTY_APPS (base.py). NO re-agregar
# aquí o Django falla con "Application labels aren't unique".

# ─────────────────────────────────────────────
# Middleware de producción (orden importa)
# ─────────────────────────────────────────────
# WhiteNoise debe ir inmediatamente DESPUÉS de SecurityMiddleware.
# Los middlewares de Prometheus (Before/After) ya están en base.py.
_sec_idx = MIDDLEWARE.index('django.middleware.security.SecurityMiddleware')
MIDDLEWARE.insert(_sec_idx + 1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# ─────────────────────────────────────────────
# Base de datos PostgreSQL con pool
# ─────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'findempro'),
        'USER': os.getenv('DB_USER', 'findempro'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'db'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': int(os.getenv('DB_CONN_MAX_AGE', '600')),
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c default_transaction_isolation=read\\ committed',
        },
    }
}

# ─────────────────────────────────────────────
# Cache Redis (producción)
# ─────────────────────────────────────────────
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/1')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': True,
        },
        'TIMEOUT': 300,
    }
}

# ─────────────────────────────────────────────
# Session en Redis
# ─────────────────────────────────────────────
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# ─────────────────────────────────────────────
# Seguridad HTTPS
# SSL solo se fuerza si está habilitado explícitamente
# (útil cuando hay load balancer / proxy que termina SSL)
# ─────────────────────────────────────────────
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# El gateway Nginx termina SSL y reenvía X-Forwarded-Proto: https.
# SECURE_SSL_REDIRECT desactivado para evitar redirect loop detrás del proxy.
SECURE_SSL_REDIRECT = False
# Las cookies siempre deben ser Secure: el proxy garantiza que el cliente
# llegó por HTTPS aunque el tráfico interno sea HTTP.
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
# Django documenta que HttpOnly en la cookie CSRF no aporta protección práctica:
# el token sólo defiende de ataques cross-domain, y quien puede leer la cookie por
# JavaScript ya está en el mismo origen. A cambio rompe algo real — el JS del
# producto (simulate-list, report-list, user-list, finance-list, profile-settings)
# arma `X-CSRFToken` con `getCookie('csrftoken')` sobre `document.cookie`, que con
# HttpOnly llega vacío y devuelve 403 en cada POST. Verificado con el E2E de
# navegador: crear un modelo desde plantilla daba 403 hasta quitarlo.
CSRF_COOKIE_HTTPONLY = False

# ─────────────────────────────────────────────
# CSRF confiable (necesario para frontend separado)
# ─────────────────────────────────────────────
_csrf_raw = os.getenv('CSRF_TRUSTED_ORIGINS', '')
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_raw.split(',') if o.strip()]

# ─────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────
_cors_raw = os.getenv('CORS_ALLOWED_ORIGINS', '')
CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors_raw.split(',') if o.strip()]
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True

# ─────────────────────────────────────────────
# Static files — WhiteNoise con compresión
# ─────────────────────────────────────────────
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# ─────────────────────────────────────────────
# REST Framework — producción (solo JSON, auth requerida)
# ─────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.openapi.AutoSchema',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
}

# ─────────────────────────────────────────────
# Password validation estricta
# ─────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 12}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─────────────────────────────────────────────
# AllAuth — producción
# ─────────────────────────────────────────────
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_LOGOUT_ON_GET = False
ACCOUNT_SESSION_REMEMBER = None

# ─────────────────────────────────────────────
# Email SMTP real
# ─────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# ─────────────────────────────────────────────
# Celery
# ─────────────────────────────────────────────
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
CELERY_ALWAYS_EAGER = False

# ─────────────────────────────────────────────
# Sentry (opcional)
# ─────────────────────────────────────────────
_SENTRY_DSN = os.getenv('SENTRY_DSN', '')
if _SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        from sentry_sdk.integrations.celery import CeleryIntegration
        from sentry_sdk.integrations.redis import RedisIntegration

        _SENSITIVE_FIELDS = frozenset({
            'password', 'password_confirmation', 'token',
            'access_token', 'refresh_token', 'secret',
        })

        def _sentry_before_send(event, hint):
            req = event.get('request', {})
            for key in ('data', 'cookies'):
                if isinstance(req.get(key), dict):
                    for field in _SENSITIVE_FIELDS:
                        if field in req[key]:
                            req[key][field] = '[FILTERED]'
            return event

        sentry_sdk.init(
            dsn=_SENTRY_DSN,
            integrations=[
                DjangoIntegration(transaction_style='url'),
                CeleryIntegration(monitor_beat_tasks=True),
                RedisIntegration(),
            ],
            traces_sample_rate=float(os.getenv('SENTRY_TRACES_RATE', '0.1')),
            profiles_sample_rate=float(os.getenv('SENTRY_PROFILES_RATE', '0.05')),
            send_default_pii=False,
            environment='production',
            release=os.getenv('GIT_COMMIT', 'unknown'),
            before_send=_sentry_before_send,
        )
    except ImportError:
        pass

# ─────────────────────────────────────────────
# Logging producción — rotación, sin emojis
# ─────────────────────────────────────────────
LOG_DIR = os.getenv('LOG_DIR', os.path.join(BASE_DIR, 'logs'))
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
            'rename_fields': {'asctime': 'timestamp', 'name': 'logger', 'levelname': 'level'},
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'app.log'),
            'maxBytes': 1024 * 1024 * 15,  # 15 MB
            'backupCount': 10,
            'formatter': 'json',
        },
        'security': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'security.log'),
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 5,
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'findempro': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'simulate': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        # Silenciar librerías ruidosas
        'matplotlib': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
        'urllib3':    {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
        'PIL':        {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
    },
}

# ─────────────────────────────────────────────
# Dashboard caching activo
# ─────────────────────────────────────────────
DASHBOARD_CONFIG['ENABLE_CHART_CACHING'] = True
DASHBOARD_CONFIG['CHART_CACHE_TIMEOUT'] = 3600
