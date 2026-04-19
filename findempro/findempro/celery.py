"""
Celery application configuration for FINDEMPRO.
"""
import os
from celery import Celery

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

app = Celery('findempro')

# Cargar config desde Django settings (CELERY_* keys)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-descubrir tasks en todas las apps instaladas
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Task de diagnóstico."""
    print(f'Request: {self.request!r}')
