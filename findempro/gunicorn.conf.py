"""
gunicorn.conf.py — Configuración de Gunicorn para FINDEMPRO en producción.
Uso: gunicorn -c gunicorn.conf.py findempro.wsgi:application
"""
import multiprocessing
import os

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
worker_class = os.getenv('GUNICORN_WORKER_CLASS', 'sync')
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

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
accesslog = os.getenv('GUNICORN_ACCESS_LOG', '-')   # stdout
errorlog = os.getenv('GUNICORN_ERROR_LOG', '-')     # stderr
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sμs'

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
