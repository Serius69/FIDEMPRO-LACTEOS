"""
Django settings — E2E de navegador.

Idéntico a `testing`, salvo que la base SQLite vive en un archivo en vez de en
memoria: `runserver` atiende cada petición en un hilo distinto y una base
`:memory:` no sobreviviría entre ellas.

Sigue siendo un entorno desechable y aislado: la ruta sale de `E2E_SQLITE_PATH`
y por defecto apunta a un temporal. **Nunca** toca una base real — igual que
`testing`, no lee `.env` ni acepta PostgreSQL.

    E2E_SQLITE_PATH=/tmp/e2e.sqlite3 \
    DJANGO_SETTINGS_MODULE=findempro.settings.e2e python manage.py migrate
"""
import os
import tempfile
from pathlib import Path

from .testing import *

_sqlite_path = os.getenv(
    'E2E_SQLITE_PATH',
    str(Path(tempfile.gettempdir()) / 'findempro-e2e.sqlite3'),
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': _sqlite_path,
    }
}

# `runserver` sirve los estáticos de las apps sólo con DEBUG; los charts y el JS
# del flujo crítico deben cargar para que el E2E signifique algo.
DEBUG = True

# El E2E ejerce el flujo completo, incluida la simulación: sin ejecución síncrona
# de Celery el navegador se quedaría esperando un worker que no existe.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
task_always_eager = True
task_eager_propagates = True

# The capacity harness can replace eager execution with a disposable local
# filesystem broker and a real Celery worker.  This is DEV-only and never reads
# Redis/PostgreSQL credentials or external runtime configuration.
if os.getenv('FINDEMPRO_LOAD_ASYNC') == '1':
    _broker_root = Path(os.environ['FINDEMPRO_LOAD_BROKER_DIR'])
    CELERY_TASK_ALWAYS_EAGER = False
    CELERY_TASK_EAGER_PROPAGATES = False
    CELERY_BROKER_URL = 'filesystem://'
    CELERY_BROKER_TRANSPORT_OPTIONS = {
        'data_folder_in': str(_broker_root / 'queue'),
        'data_folder_out': str(_broker_root / 'queue'),
        'data_folder_processed': str(_broker_root / 'processed'),
        'control_folder': str(_broker_root / 'control'),
    }
    task_always_eager = False
    task_eager_propagates = False

if os.getenv('FINDEMPRO_LOAD_METRICS') == '1':
    MIDDLEWARE = [*MIDDLEWARE, 'tenancy.load_metrics.LoadMetricsMiddleware']
    FINDEMPRO_COMMERCIAL_GATES_MODE = os.getenv(
        'FINDEMPRO_COMMERCIAL_GATES_MODE', FINDEMPRO_COMMERCIAL_GATES_MODE
    )

# El navegador del E2E entra por el dev-server de Vite (127.0.0.1:5188), que
# proxya a Django. El origen que ve el navegador y el host que ve Django son
# distintos, así que sin declararlo Django rechaza por CSRF todo POST de un
# usuario con sesión: el login de allauth y, detrás, `/simulate/api/v1/…`.
# Sólo aplica a este entorno desechable; producción sigue leyendo su propia
# lista desde CSRF_TRUSTED_ORIGINS.
CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        'E2E_CSRF_TRUSTED_ORIGINS',
        'http://127.0.0.1:5188,http://localhost:5188',
    ).split(',')
    if o.strip()
]
