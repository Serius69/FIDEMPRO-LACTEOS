"""
Django settings — FINDEMPRO
Base compartida entre development, staging y production.
Los valores sensibles SIEMPRE vienen de variables de entorno.
"""
import os
import sys
from pathlib import Path
from django.contrib.messages import constants as messages
from dotenv import load_dotenv

# ─────────────────────────────────────────────
# Rutas base
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Cargar .env según el entorno activo — NUNCA forzar .env.development en producción
_ENV = os.getenv('DJANGO_ENV', 'development')
_env_file = os.path.join(BASE_DIR, f'.env.{_ENV}')
if _ENV not in ('test', 'testing'):
    if os.path.exists(_env_file):
        load_dotenv(_env_file, override=False)
    elif os.path.exists(os.path.join(BASE_DIR, '.env')):
        load_dotenv(os.path.join(BASE_DIR, '.env'), override=False)

# ─────────────────────────────────────────────
# Seguridad — NUNCA hardcodear en código
# ─────────────────────────────────────────────
SECRET_KEY = os.getenv('SECRET_KEY')  # fail-fast si falta — sin fallback inseguro
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY env var es obligatoria. Genera una con: python -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\"")
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')
ALLOWED_HOSTS = [h.strip() for h in os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]

# ─────────────────────────────────────────────
# Aplicaciones
# ─────────────────────────────────────────────
DEFAULT_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',
]

LOCAL_APPS = [
    "dashboards",
    "pages",
    "product",
    "variable",
    "business",
    "finance",
    "simulate",
    "user",
    "report",
    "questionary",
    "modeling",
]

THIRDPARTY_APPS = [
    "crispy_forms",
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'multiselectfield',
    'social_django',
    'django_extensions',
    'rest_framework',
    'drf_yasg',
    'corsheaders',
    'django_celery_beat',
    'django_prometheus',
    'axes',  # Protección de fuerza bruta en el login (debe ir al final).
]

INSTALLED_APPS = DEFAULT_APPS + LOCAL_APPS + THIRDPARTY_APPS

# ─────────────────────────────────────────────
# Middleware
# ─────────────────────────────────────────────
MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'user.middleware.ActivityLogMiddleware',
    'hub_auth.middleware.HubAuthMiddleware',
    'findempro.security_headers.SecurityHeadersMiddleware',
    # AxesMiddleware debe ir al final, tras AuthenticationMiddleware.
    'axes.middleware.AxesMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

# Kapitalya Hub SSO
HUB_JWT_SECRET = os.getenv('HUB_JWT_SECRET', '')
HUB_URL = os.getenv('HUB_URL', 'https://kapitalya.com.bo')
HUB_UPGRADE_URL = os.getenv('HUB_UPGRADE_URL', '')

# Límites de uso por plan. Desactivados por defecto para preservar el flujo
# existente durante el rollout.
PLAN_GATES_ENABLED = os.getenv('PLAN_GATES_ENABLED', 'False').lower() in ('true', '1', 'yes')
PLAN_SIM_LIMITS = {
    'basico': 10,
    'pro': 100,
    'empresa': None,
}

# ─────────────────────────────────────────────
# URLs / Templates / WSGI
# ─────────────────────────────────────────────
ROOT_URLCONF = 'findempro.urls'
WSGI_APPLICATION = 'findempro.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
            ],
        },
    },
]

# ─────────────────────────────────────────────
# Autenticación
# ─────────────────────────────────────────────
AUTHENTICATION_BACKENDS = [
    # AxesStandaloneBackend debe ir PRIMERO para bloquear tras N intentos fallidos.
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
    'social_core.backends.google.GoogleOAuth2',
]

# ─────────────────────────────────────────────
# django-axes — protección de fuerza bruta
# ─────────────────────────────────────────────
AXES_ENABLED = os.getenv('AXES_ENABLED', 'True').lower() in ('true', '1', 'yes')
AXES_FAILURE_LIMIT = int(os.getenv('AXES_FAILURE_LIMIT', '5'))
AXES_COOLOFF_TIME = float(os.getenv('AXES_COOLOFF_HOURS', '1'))  # horas de bloqueo
AXES_LOCKOUT_PARAMETERS = ['ip_address', 'username']
AXES_RESET_ON_SUCCESS = True
AXES_BEHIND_REVERSE_PROXY = True  # tras Nginx/Cloudflare — usar X-Forwarded-For
AXES_IPWARE_PROXY_COUNT = 1

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 12}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "account_login"
ACCOUNT_LOGOUT_ON_GET = os.getenv('ACCOUNT_LOGOUT_ON_GET', 'True').lower() in ('true', '1')
# Reemplaza a ACCOUNT_EMAIL_REQUIRED, deprecado en django-allauth 65. Declara los
# mismos campos que regían antes: email y usuario obligatorios en el registro.
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
ACCOUNT_AUTHENTICATED_LOGIN_REDIRECTS = True
ACCOUNT_EMAIL_VERIFICATION = os.getenv('ACCOUNT_EMAIL_VERIFICATION', 'optional')
ACCOUNT_RATE_LIMITS = {
    'login_failed': '5/5m',
}

SOCIAL_AUTH_URL_NAMESPACE = 'social'
SOCIALACCOUNT_QUERY_EMAIL = True

# Google OAuth2 — siempre desde env
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.getenv('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', '')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.getenv('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', '')

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
    }
}

ACCOUNT_FORMS = {
    "login": "findempro.forms.UserLoginForm",
    "signup": "findempro.forms.UserRegistrationForm",
    "change_password": "findempro.forms.PasswordChangeForm",
    "set_password": "findempro.forms.PasswordSetForm",
    "reset_password": "findempro.forms.PasswordResetForm",
    "reset_password_from_key": "findempro.forms.PasswordResetKeyForm",
}

SITE_ID = int(os.getenv('SITE_ID', '1'))

# ─────────────────────────────────────────────
# Base de datos (override en cada settings/*.py)
# ─────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'findempro'),
        'USER': os.getenv('DB_USER', 'findempro'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': int(os.getenv('DB_CONN_MAX_AGE', '600')),
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}

# ─────────────────────────────────────────────
# Cache — Redis
# ─────────────────────────────────────────────
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/1')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': True,
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 20,
                'retry_on_timeout': True,
            },
        },
        'TIMEOUT': 300,
    }
}

# ─────────────────────────────────────────────
# Celery
# ─────────────────────────────────────────────
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/La_Paz'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 min
CELERY_ALWAYS_EAGER = os.getenv('CELERY_ALWAYS_EAGER', 'False').lower() in ('true', '1')

# ─────────────────────────────────────────────
# KDP — Kapitalya Data Platform (consumidor de eventos)
# ─────────────────────────────────────────────
# Findempro consume el dataset `findempro_sector_bo` en modo CURSOR_STREAM: no
# mantiene una conexión abierta, guarda un número (el `seq`) y aplica sólo lo
# nuevo. La política declarada en la plataforma
# (`registry/consumer_policies.yaml`) es on_stale=WARN, on_unavailable=DEGRADE,
# allow_lkg=true, require_provenance=true, max_age_s=63072000.
#
# El token es de Findempro y sólo alcanza sus datasets: NUNCA va al código.
KDP_API_URL = os.getenv('KDP_API_URL', 'http://127.0.0.1:8099')
KDP_API_TOKEN = os.getenv('KDP_API_TOKEN', '')
KDP_TIMEOUT = float(os.getenv('KDP_TIMEOUT', '20'))
KDP_CONSUMER_ID = os.getenv('KDP_CONSUMER_ID', 'Findempro')
KDP_DATASET_ID = os.getenv('KDP_DATASET_ID', 'findempro_sector_bo')
KDP_EXPECT_SCHEMA = os.getenv('KDP_EXPECT_SCHEMA', '1.x')
# World Bank publica una vez al año: dos años de tolerancia es la política, no
# un descuido. Lo que no se tolera es un valor curado disfrazado de observación.
KDP_MAX_AGE_S = int(os.getenv('KDP_MAX_AGE_S', str(63072000)))
# Estado local del consumidor: cursor + última `event_time` por partition_key.
# Fuera de git y fuera del árbol de datos versionado; se recrea solo si falta,
# pero borrarlo hace que el consumidor reprocese (idempotente, no destructivo).
KDP_STATE_DIR = os.getenv('KDP_STATE_DIR', os.path.join(BASE_DIR, 'var', 'kdp'))

# Programación. Esto es lo que sustituye a "alguien teclea el comando": el
# beat de Celery (django_celery_beat.schedulers:DatabaseScheduler, ya desplegado
# en docker-compose.dev.yml y docker-compose.prod.yml) sincroniza este dict a la
# base al arrancar y dispara la tarea sin intervención humana.
CELERY_BEAT_SCHEDULE = {
    'business.consume-kdp-events': {
        'task': 'business.consume_kdp_events',
        # Cada 10 minutos. El dataset se mueve poco (BCB semanal, World Bank
        # anual), pero el coste de un drain vacío es una petición HTTP: la
        # cadencia la fija el tiempo que se tolera ir atrasado, no el volumen.
        'schedule': float(os.getenv('KDP_CONSUME_INTERVAL_S', '600')),
        'options': {'expires': 540},
    },
}

# ─────────────────────────────────────────────
# Internacionalización
# ─────────────────────────────────────────────
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/La_Paz'
USE_I18N = True
# USE_L10N se eliminó en Django 5.0: la localización de formatos es incondicional.
USE_TZ = True

# ─────────────────────────────────────────────
# Archivos estáticos y media
# ─────────────────────────────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─────────────────────────────────────────────
# Email
# ─────────────────────────────────────────────
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

# ─────────────────────────────────────────────
# Session
# ─────────────────────────────────────────────
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # 2 semanas
SESSION_SAVE_EVERY_REQUEST = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# ─────────────────────────────────────────────
# REST Framework
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
        'simulate': '20/hour',    # simulación Monte Carlo — costosa (numpy/CuPy)
        'public_simulate': '30/hour',  # simulador público anónimo, por IP
        'report_pdf': '10/hour',  # generación PDF async — costosa
        'export': '30/hour',      # exportación CSV/Excel
    },
}

# ─────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────
_cors_origins_raw = os.getenv('CORS_ALLOWED_ORIGINS', '')
CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors_origins_raw.split(',') if o.strip()]
CORS_ALLOW_CREDENTIALS = True

# ─────────────────────────────────────────────
# Seguridad base (producción lo sobreescribe)
# ─────────────────────────────────────────────
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

# Content-Security-Policy emitida por SecurityHeadersMiddleware en TODA respuesta
# Django (nginx no la emitía por la herencia rota de add_header). El allowlist
# La SPA React/Vite sólo carga assets propios. Los templates Django legacy aún
# contienen referencias a CDNs; quedan deliberadamente bloqueadas hasta que esos
# assets se vendorizen bajo /static. No se amplía la política global por rutas
# heredadas que no forman parte de la SPA.
CONTENT_SECURITY_POLICY = os.environ.get('CONTENT_SECURITY_POLICY', (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: blob:; "
    "font-src 'self' data:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; base-uri 'self'; object-src 'none'"
))
PERMISSIONS_POLICY = "camera=(), microphone=(), geolocation=(), interest-cohort=()"

# ─────────────────────────────────────────────
# Messages UI
# ─────────────────────────────────────────────
MESSAGE_TAGS = {
    messages.DEBUG: "alert-info",
    messages.INFO: "alert-info",
    messages.SUCCESS: "alert-success",
    messages.WARNING: "alert-warning",
    messages.ERROR: "alert-danger",
}

CRISPY_TEMPLATE_PACK = 'bootstrap4'

# ─────────────────────────────────────────────
# Claude / Terceros
# ─────────────────────────────────────────────
ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-5')

# Bounded execution and model compilation for the configurable business-model
# runner. Deployments may tune these guards without changing the model DSL.
MODELING_MAX_ACTIVE_RUNS = int(os.getenv('MODELING_MAX_ACTIVE_RUNS', '4'))
MODELING_MAX_MODEL_NODES = int(os.getenv('MODELING_MAX_MODEL_NODES', '1000'))
MODELING_MAX_MODEL_EDGES = int(os.getenv('MODELING_MAX_MODEL_EDGES', '5000'))
MODELING_MAX_EXPRESSION_LENGTH = int(os.getenv('MODELING_MAX_EXPRESSION_LENGTH', '500'))
MODELING_MAX_EXPRESSION_NODES = int(os.getenv('MODELING_MAX_EXPRESSION_NODES', '200'))
MODELING_MAX_EXPRESSION_DEPTH = int(os.getenv('MODELING_MAX_EXPRESSION_DEPTH', '40'))

# ─────────────────────────────────────────────
# Matplotlib (no-GUI)
# ─────────────────────────────────────────────
import matplotlib
matplotlib.use('Agg')

# ─────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────
DASHBOARD_CONFIG = {
    'CHART_TYPES': [
        ('line', 'Línea'), ('bar', 'Barras'), ('pie', 'Circular'),
        ('donut', 'Dona'), ('area', 'Área'), ('scatter', 'Dispersión'),
        ('heatmap', 'Mapa de calor'), ('candlestick', 'Velas'),
    ],
    'MAX_CHARTS_PER_PRODUCT': 10,
    'CHART_IMAGE_QUALITY': 95,
    'CHART_DPI': 150,
    'DEFAULT_CHART_WIDTH': 10,
    'DEFAULT_CHART_HEIGHT': 6,
    'ENABLE_CHART_CACHING': True,
    'CHART_CACHE_TIMEOUT': 3600,
}

# ─────────────────────────────────────────────
# Logging base (cada entorno puede extenderlo)
# ─────────────────────────────────────────────
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(MEDIA_ROOT, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {module}: {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'app.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'findempro': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'simulate': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ─────────────────────────────────────────────
# Django Extensions
# ─────────────────────────────────────────────
SHELL_PLUS_PRE_IMPORTS = [
    ('django.db', ['connection', 'reset_queries']),
    ('datetime', ['datetime', 'timedelta']),
    ('json', ['loads', 'dumps']),
]

GRAPH_MODELS = {
    'all_applications': True,
    'group_models': True,
}
