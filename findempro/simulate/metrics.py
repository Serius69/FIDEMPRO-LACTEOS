"""
simulate/metrics.py
====================
Métricas Prometheus para el motor de simulación Monte Carlo.

Prometheus no-op stubs: si prometheus_client no está disponible (test runners,
entornos sin soporte), todas las clases se vuelven no-op para no romper el pipeline.

Métricas expuestas:
    simulation_duration_seconds  (Histogram): duración total del pipeline por sector
    simulation_total             (Counter):   éxito/fallo por sector y distribución
    simulation_active            (Gauge):     simulaciones en ejecución activa

Integración en simulation_service.py::

    from simulate.metrics import SIMULATION_DURATION, SIMULATION_COUNTER, ACTIVE_SIMULATIONS
    import time

    with ACTIVE_SIMULATIONS.labels(sector='lacteo').track_inprogress():
        t0 = time.perf_counter()
        result = run_pipeline(...)
        SIMULATION_DURATION.labels(sector='lacteo', n_scenarios_bucket='1k').observe(
            time.perf_counter() - t0
        )
        SIMULATION_COUNTER.labels(
            sector='lacteo', distribution_type='normal', status='success'
        ).inc()

PromQL ejemplos:
    # p95 de duración por sector (ventana 5 min):
    histogram_quantile(0.95,
        sum(rate(simulation_duration_seconds_bucket[5m])) by (le, sector)
    )

    # Tasa de fallos por sector (último minuto):
    sum(rate(simulation_total{status="failure"}[1m])) by (sector)

    # Simulaciones activas en tiempo real:
    simulation_active
"""

import logging

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Stubs no-op
# ─────────────────────────────────────────────────────────────────────────────

class _NoOpMetric:
    """Stub que implementa la interfaz de prometheus_client sin efecto."""
    def labels(self, **kwargs):
        return self
    def observe(self, value):
        pass
    def inc(self, amount=1):
        pass
    def dec(self, amount=1):
        pass
    def set(self, value):
        pass
    def track_inprogress(self):
        return _NoOpContext()


class _NoOpContext:
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Registro de métricas reales
# ─────────────────────────────────────────────────────────────────────────────

def _make_histogram(name, description, labels, buckets=None):
    try:
        from prometheus_client import Histogram
        kwargs = dict(name=name, documentation=description, labelnames=labels)
        if buckets:
            kwargs['buckets'] = buckets
        return Histogram(**kwargs)
    except Exception as exc:
        logger.debug('prometheus_client no disponible para %s: %s', name, exc)
        return _NoOpMetric()


def _make_counter(name, description, labels):
    try:
        from prometheus_client import Counter
        return Counter(name=name, documentation=description, labelnames=labels)
    except Exception as exc:
        logger.debug('prometheus_client no disponible para %s: %s', name, exc)
        return _NoOpMetric()


def _make_gauge(name, description, labels):
    try:
        from prometheus_client import Gauge
        return Gauge(name=name, documentation=description, labelnames=labels)
    except Exception as exc:
        logger.debug('prometheus_client no disponible para %s: %s', name, exc)
        return _NoOpMetric()


# ─────────────────────────────────────────────────────────────────────────────
# Instancias públicas
# ─────────────────────────────────────────────────────────────────────────────

SIMULATION_DURATION = _make_histogram(
    name='simulation_duration_seconds',
    description='Duración del pipeline completo de simulación Monte Carlo en segundos',
    labels=['sector', 'n_scenarios_bucket'],
    buckets=(0.5, 1, 2, 5, 10, 30, 60, 120, 300),
)

SIMULATION_COUNTER = _make_counter(
    name='simulation_total',
    description='Total de simulaciones ejecutadas por sector, distribución y estado',
    labels=['sector', 'distribution_type', 'status'],
)

ACTIVE_SIMULATIONS = _make_gauge(
    name='simulation_active',
    description='Número de simulaciones activas en ejecución simultánea',
    labels=['sector'],
)


# ─────────────────────────────────────────────────────────────────────────────
# Helper: categorizar n_scenarios
# ─────────────────────────────────────────────────────────────────────────────

def scenarios_bucket(n: int) -> str:
    """Clasifica n_scenarios en un bucket legible para etiquetas Prometheus."""
    if n <= 500:
        return '<=500'
    if n <= 1_000:
        return '1k'
    if n <= 5_000:
        return '5k'
    if n <= 10_000:
        return '10k'
    return '>10k'
