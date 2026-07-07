"""
health.py — Endpoint de health check para producción.
Usado por Docker HEALTHCHECK, Nginx upstream y load balancers.

GET /health/         — Check completo (DB + Cache + Redis)
GET /health/ready/   — Solo DB (readiness probe para K8s)
GET /health/live/    — Siempre 200 (liveness probe)
"""
import time
import logging
from django.http import JsonResponse
from django.db import connection, OperationalError
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


def _check_database() -> tuple[bool, str]:
    """Verifica la conexión a la base de datos."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return True, "ok"
    except OperationalError as e:
        logger.error(f"[health] DB error: {e}")
        return False, f"database error: {type(e).__name__}"
    except Exception as e:
        logger.error(f"[health] DB unexpected error: {e}")
        return False, f"unexpected: {type(e).__name__}"


def _check_cache() -> tuple[bool, str]:
    """Verifica lectura/escritura en cache."""
    try:
        key = "health:probe"
        cache.set(key, "ok", timeout=10)
        val = cache.get(key)
        if val == "ok":
            return True, "ok"
        return False, "cache read/write mismatch"
    except Exception as e:
        # Cache falla silenciosamente — no debe bajar el servicio
        logger.warning(f"[health] Cache warning: {e}")
        return True, f"degraded: {type(e).__name__}"  # warning, no crítico


def _check_redis() -> tuple[bool, str]:
    """Verifica la conexión a Redis (broker Celery)."""
    try:
        import redis as redis_lib
        broker_url = getattr(settings, 'CELERY_BROKER_URL', 'redis://localhost:6379/0')
        r = redis_lib.from_url(broker_url, socket_connect_timeout=2, socket_timeout=2)
        r.ping()
        return True, "ok"
    except Exception as e:
        logger.warning(f"[health] Redis warning: {e}")
        return True, f"degraded: {type(e).__name__}"  # warning, no crítico


def health_check(request):
    """
    Health check completo.
    Retorna 200 si el sistema es saludable, 503 si hay fallos críticos.
    Solo DB es crítico — cache y Redis son degraded pero no bloquean.
    """
    start = time.monotonic()

    db_ok, db_status = _check_database()
    cache_ok, cache_status = _check_cache()
    redis_ok, redis_status = _check_redis()

    is_healthy = db_ok  # Solo DB es crítico para el servicio

    elapsed = round((time.monotonic() - start) * 1000, 2)

    data = {
        "status": "healthy" if is_healthy else "unhealthy",
        "checks": {
            "database": db_status,
            "cache": cache_status,
            "redis": redis_status,
        },
        "response_time_ms": elapsed,
    }

    # No logear en producción para evitar spam de logs
    if not is_healthy:
        logger.error(f"[health] UNHEALTHY: {data}")

    return JsonResponse(data, status=200 if is_healthy else 503)


def health_ready(request):
    """
    Readiness probe — solo verifica que la DB esté disponible.
    Usado por Kubernetes/orquestadores para saber si el pod puede recibir tráfico.
    """
    db_ok, db_status = _check_database()
    if db_ok:
        return JsonResponse({"status": "ready", "database": db_status})
    return JsonResponse({"status": "not ready", "database": db_status}, status=503)


def health_live(request):
    """
    Liveness probe — siempre 200 si el proceso está vivo.
    Kubernetes lo usa para saber si debe reiniciar el pod.
    """
    return JsonResponse({"status": "alive"})
