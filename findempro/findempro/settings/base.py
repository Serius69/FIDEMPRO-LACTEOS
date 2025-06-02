"""
Django settings for findempro project - DESARROLLO
"""
import os
from pathlib import Path
from django.contrib.messages import constants as messages
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-j%^*y0krq5^-#3lggoecxw!d7ad_gqkab3t5w17&0w06+qf8+8'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*', 'localhost', '127.0.0.1']

# Application definition
DEFAULT_APPS = [    
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
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
    "questionary"
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
]

INSTALLED_APPS = DEFAULT_APPS + LOCAL_APPS + THIRDPARTY_APPS

MIDDLEWARE = [
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
]

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',  # Para desarrollo
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Para desarrollo
    ],
}

ROOT_URLCONF = 'findempro.urls'

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

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
    'social_core.backends.google.GoogleOAuth2',
]

CRISPY_TEMPLATE_PACK = 'bootstrap4'
WSGI_APPLICATION = 'findempro.wsgi.application'

# Database - Desarrollo
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv("MYSQL_DATABASE", "findempro2"),
        'USER': os.getenv("MYSQL_USER", "mysql"),
        'PASSWORD': os.getenv("MYSQL_PASSWORD", "mysql"),
        'HOST': os.getenv("DB_HOST", "localhost"),
        'PORT': os.getenv("DB_PORT", "3306"),
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}


# Internationalization
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/La_Paz'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

# Media files
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Messages customize
MESSAGE_TAGS = {
    messages.DEBUG: "alert-info",
    messages.INFO: "alert-info",
    messages.SUCCESS: "alert-success",
    messages.WARNING: "alert-warning",
    messages.ERROR: "alert-danger",
}

# Para usar Gmail en desarrollo (opcional)
# EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
# EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
# EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
# EMAIL_USE_TLS = True
# EMAIL_USE_SSL = False
# EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
# EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")

# Authentication settings
LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "account_login"
ACCOUNT_LOGOUT_ON_GET = True  # Más conveniente para desarrollo
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATED_LOGIN_REDIRECTS = True
SOCIAL_AUTH_URL_NAMESPACE = 'social'

# All Auth Forms Customization 
ACCOUNT_FORMS = {
    "login": "findempro.forms.UserLoginForm",
    "signup": "findempro.forms.UserRegistrationForm",
    "change_password": "findempro.forms.PasswordChangeForm",
    "set_password": "findempro.forms.PasswordSetForm",
    "reset_password": "findempro.forms.PasswordResetForm",
    "reset_password_from_key": "findempro.forms.PasswordResetKeyForm",
}

SOCIALACCOUNT_QUERY_EMAIL = True

# Social auth google key and secret key
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.getenv("SOCIAL_AUTH_GOOGLE_OAUTH2_KEY")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.getenv("SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET")

SITE_ID = 2

# Provider Configurations
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Base de datos en desarrollo
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # 2 weeks
SESSION_SAVE_EVERY_REQUEST = False  # No necesario en desarrollo

# Celery Configuration - Opcional para desarrollo
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
CELERY_ALWAYS_EAGER = True  # Ejecutar tareas síncronamente en desarrollo
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

# Logging simplificado para desarrollo
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
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
            'formatter': 'verbose'
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'debug.log'),
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
        'findempro': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Dashboard Configuration
DASHBOARD_CONFIG = {
    'CHART_TYPES': [
        ('line', 'Línea'),
        ('bar', 'Barras'),
        ('pie', 'Circular'),
        ('donut', 'Dona'),
        ('area', 'Área'),
        ('scatter', 'Dispersión'),
        ('heatmap', 'Mapa de calor'),
        ('candlestick', 'Velas'),
    ],
    'MAX_CHARTS_PER_PRODUCT': 10,
    'CHART_IMAGE_QUALITY': 95,
    'CHART_DPI': 150,
    'DEFAULT_CHART_WIDTH': 10,
    'DEFAULT_CHART_HEIGHT': 6,
    'ENABLE_CHART_CACHING': False,  # Desactivar caché en desarrollo
}

# Matplotlib backend
import matplotlib
matplotlib.use('Agg')

# Create necessary directories
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

if not os.path.exists(MEDIA_ROOT):
    os.makedirs(MEDIA_ROOT)
    os.makedirs(os.path.join(MEDIA_ROOT, 'chart_images'))

# Shell Plus para desarrollo
SHELL_PLUS_PRE_IMPORTS = [
    ('django.db', ['connection', 'reset_queries']),
    ('datetime', ['datetime', 'timedelta']),
    ('json', ['loads', 'dumps']),
]

# Django Extensions Graph Models
GRAPH_MODELS = {
    'all_applications': True,
    'group_models': True,
}