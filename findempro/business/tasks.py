"""Tareas programadas de `business`.

Esta es la pieza que quita a la persona del camino. Antes, el contexto macro de
Findempro (oficial, paralelo, inflación) sólo se movía si alguien tecleaba
``manage.py scrape_bolivia_data``: no había cron, ni entrada de beat, ni timer.
La tarea de abajo la dispara ``CELERY_BEAT_SCHEDULE['business.consume-kdp-events']``
cada 10 minutos, servida por el contenedor ``findempro_celery_beat``
(``--scheduler django_celery_beat.schedulers:DatabaseScheduler``) que ya está en
``docker-compose.dev.yml`` y ``docker-compose.prod.yml``.
"""
from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="business.consume_kdp_events", ignore_result=False)
def consume_kdp_events() -> dict:
    """Drena el cursor de ``findempro_sector_bo`` y reescribe el contexto macro.

    No levanta cuando KDP no responde: la política declarada de Findempro es
    ``on_unavailable=DEGRADE`` con ``allow_lkg=true``. Reintentar cada 10 minutos
    contra una plataforma caída sólo llenaría la cola de fallos; lo que sí hace
    es dejar el motivo escrito en el JSON y en el log, para que la degradación
    sea visible en vez de silenciosa.
    """
    from business import kdp_events

    informe = kdp_events.consume()
    resumen = {k: v for k, v in informe.items()
               if k not in ("market_data", "kdp_to_consumer_ms", "end_to_end_ms")}
    if informe.get("degraded_reason"):
        logger.warning("KDP degradado: %s", informe["degraded_reason"])
    else:
        logger.info("KDP: %d eventos aplicados, cursor %s → %s",
                    informe["events_applied"], informe["cursor_before"],
                    informe["cursor_after"])
    return resumen
