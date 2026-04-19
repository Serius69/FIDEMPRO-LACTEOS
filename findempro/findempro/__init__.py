# Exponer la app Celery para que Django la use automáticamente
from .celery import app as celery_app

__all__ = ('celery_app',)
