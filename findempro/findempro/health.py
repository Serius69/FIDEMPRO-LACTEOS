# findempro/health.py
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import redis
from django.conf import settings

def health_check(request):
    """Endpoint para verificar el estado de la aplicación"""
    
    health_status = {
        'status': 'healthy',
        'checks': {}
    }
    
    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['checks']['database'] = 'ok'
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = str(e)
    
    # Check cache
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            health_status['checks']['cache'] = 'ok'
        else:
            raise Exception("Cache read/write failed")
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['cache'] = str(e)
    
    # Check Redis
    try:
        r = redis.from_url(settings.CELERY_BROKER_URL)
        r.ping()
        health_status['checks']['redis'] = 'ok'
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['redis'] = str(e)
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return JsonResponse(health_status, status=status_code)

# Agregar a urls.py
# path('health/', health_check, name='health_check'),