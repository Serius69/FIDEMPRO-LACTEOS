"""El worker de findempro_celery escucha exactamente 'default' y 'simulations'
(ver -Q en docker-compose.dev.yml/.prod.yml). Celery enruta CUALQUIER tarea sin
ruta explicita a su cola implicita 'celery' -- que el worker nunca escucho.

El sintoma es 100% silencioso: la API responde 202, el task_id existe, y el
mensaje se queda para siempre en la lista `celery` de Redis (36 encontrados en
PROD el 2026-08-25). Ver
ops/handoff/20260825-findempro-app/FINDING-celery-default-queue-mismatch-findempro.md.

Este archivo prueba la garantia real -- que NINGUNA tarea registrada resuelve a
una cola que el worker no escucha -- en vez de una lista de nombres que se
desactualiza en cuanto alguien agrega una tarea nueva y se olvida de esto.
"""
import importlib

import pytest

from findempro.celery import app as celery_app

# Colas que findempro_celery consume de verdad (docker-compose.*.yml, -Q).
WORKER_QUEUES = {'default', 'simulations'}

# Motor Monte Carlo / analisis pesado: cola dedicada 'simulations'.
# Todo lo demas (email, PDF, limpieza, alertas, estadisticas) cae en
# 'default' via CELERY_TASK_DEFAULT_QUEUE -- no necesita ruta explicita.
SIMULATION_QUEUE_TASKS = {
    'simulate.tasks.run_stateless_simulation',
    'simulate.tasks.execute_simulation_async',
    'simulate.tasks.run_sensitivity_async',
    'modeling.run_business_simulation',
}

# Los call sites importan las tareas de forma perezosa (dentro de la vista),
# asi que el registro de Celery esta incompleto hasta que se importan los
# modulos de tareas del proyecto explicitamente.
importlib.import_module('simulate.tasks')
importlib.import_module('modeling.tasks')
importlib.import_module('report.tasks')


def _tareas_propias():
    """Tareas del proyecto registradas en el app de Celery, sin las internas."""
    return sorted(n for n in celery_app.tasks if not n.startswith('celery.'))


def _cola_de(nombre):
    ruta = celery_app.amqp.router.route({}, nombre)
    cola = ruta['queue']
    return cola.name if hasattr(cola, 'name') else cola


def test_hay_tareas_registradas_que_auditar():
    assert _tareas_propias(), 'no se registro ninguna tarea propia -- ¿fallo el import?'


def test_default_queue_no_es_la_implicita_de_celery():
    """La cola por defecto es 'default', no la 'celery' implicita de la libreria."""
    assert celery_app.conf.task_default_queue == 'default'


@pytest.mark.parametrize('nombre', sorted(SIMULATION_QUEUE_TASKS))
def test_tareas_de_simulacion_van_a_su_cola_dedicada(nombre):
    assert nombre in celery_app.tasks, f'{nombre} no esta registrada (¿nombre incorrecto?)'
    cola = _cola_de(nombre)
    assert cola == 'simulations', f'{nombre} -> {cola!r}, se esperaba "simulations"'


def test_ninguna_tarea_propia_cae_en_la_cola_implicita_celery():
    """Regresion directa del hallazgo: nada puede resolver fuera de lo que el worker escucha."""
    fugadas = [(nombre, _cola_de(nombre)) for nombre in _tareas_propias()]
    fugadas = [(nombre, cola) for nombre, cola in fugadas if cola not in WORKER_QUEUES]
    assert not fugadas, (
        f'tareas enrutadas fuera de {WORKER_QUEUES} (quedarian atascadas para '
        f'siempre, como los 36 mensajes de PROD): {fugadas}'
    )


def test_worker_queues_documentadas_coinciden_con_docker_compose():
    """Si alguien cambia el -Q del worker sin tocar este set, este test lo grita."""
    import pathlib

    compose = pathlib.Path(__file__).resolve().parents[2] / 'docker-compose.prod.yml'
    contenido = compose.read_text()
    assert '-Q default,simulations' in contenido, (
        'docker-compose.prod.yml cambio las colas del worker; actualiza '
        'WORKER_QUEUES en este test para que siga probando lo que corre de verdad'
    )
