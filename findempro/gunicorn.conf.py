"""
gunicorn.conf.py — Configuración de Gunicorn para FINDEMPRO en producción.
Uso: gunicorn -c gunicorn.conf.py findempro.wsgi:application
"""
import multiprocessing
import os
import re

from gunicorn import glogging

# ─────────────────────────────────────────────
# Binding
# ─────────────────────────────────────────────
bind = os.getenv('GUNICORN_BIND', '0.0.0.0:8000')

# ─────────────────────────────────────────────
# Workers
# Fórmula recomendada: (2 × CPUs) + 1
# Para sistemas con cálculo matemático intensivo (scipy/numpy),
# no subir workers demasiado para evitar OOM.
# ─────────────────────────────────────────────
_cpu_count = multiprocessing.cpu_count()
workers = int(os.getenv('GUNICORN_WORKERS', min(_cpu_count * 2 + 1, 9)))
worker_class = os.getenv('GUNICORN_WORKER_CLASS', 'gthread')
worker_connections = 1000
threads = int(os.getenv('GUNICORN_THREADS', '2'))

# ─────────────────────────────────────────────
# Timeouts
# Simulaciones Monte Carlo pueden tardar — timeout generoso
# ─────────────────────────────────────────────
timeout = int(os.getenv('GUNICORN_TIMEOUT', '120'))
graceful_timeout = int(os.getenv('GUNICORN_GRACEFUL_TIMEOUT', '30'))
keepalive = int(os.getenv('GUNICORN_KEEPALIVE', '5'))

# ─────────────────────────────────────────────
# Límites de memoria (prevenir memory leaks)
# ─────────────────────────────────────────────
max_requests = int(os.getenv('GUNICORN_MAX_REQUESTS', '1000'))
max_requests_jitter = int(os.getenv('GUNICORN_MAX_REQUESTS_JITTER', '100'))
preload_app = os.getenv('GUNICORN_PRELOAD_APP', 'true').lower() in ('true', '1')

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
accesslog = os.getenv('GUNICORN_ACCESS_LOG', '-')   # stdout
errorlog = os.getenv('GUNICORN_ERROR_LOG', '-')     # stderr
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sμs'

# ─────────────────────────────────────────────
# Redacción de secretos del SSO en el access log
#
# El callback del Hub viaja como GET: `/hub/callback/?hub_token=<JWT>&state=<…>`.
# `%(r)s` es la línea de petición COMPLETA y `%(f)s` el Referer, así que sin esto
# el project_token se escribe en claro en stdout → `docker logs`, el driver de
# logging del contenedor y cualquier agregador. Ese JWT sigue siendo canjeable
# hasta que expire, y el `state` es lo que liga el canje a un navegador.
#
# Se redacta el VALOR y se deja el nombre del parámetro: la línea sigue diciendo
# qué ruta se pidió y con qué parámetros, que es para lo que se lee un access log.
# ─────────────────────────────────────────────
_PARAMS_SECRETOS = re.compile(r'(?i)\b(hub_token|state)=[^&\s"]*')


def _redactar(valor):
    if isinstance(valor, str) and ('hub_token' in valor or 'state=' in valor):
        return _PARAMS_SECRETOS.sub(r'\1=[redactado]', valor)
    return valor


class RedactingLogger(glogging.Logger):
    """Access logger que tacha `hub_token`/`state` en todos los átomos.

    Se sanean los átomos ya construidos, no solo `%(r)s`: `%(q)s` (query),
    `%(f)s` (Referer) y los `%({header}i)s` transportan el mismo secreto, y el
    formato del log es configurable por entorno.
    """

    def atoms(self, resp, req, environ, request_time):
        return {
            clave: _redactar(valor)
            for clave, valor in super().atoms(resp, req, environ, request_time).items()
        }


logger_class = RedactingLogger

# ─────────────────────────────────────────────
# Process naming
# ─────────────────────────────────────────────
proc_name = 'findempro'

# ─────────────────────────────────────────────
# Seguridad
# ─────────────────────────────────────────────
forwarded_allow_ips = os.getenv('GUNICORN_FORWARDED_ALLOW_IPS', '127.0.0.1,nginx')
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# ─────────────────────────────────────────────
# Hooks
# ─────────────────────────────────────────────
def on_starting(server):
    server.log.info("Iniciando FINDEMPRO con %d workers", workers)

def worker_exit(server, worker):
    server.log.info("Worker %d finalizado", worker.pid)

def post_fork(server, worker):
    """Después del fork — re-seed numpy para simulaciones Monte Carlo."""
    import numpy as np
    np.random.seed()
