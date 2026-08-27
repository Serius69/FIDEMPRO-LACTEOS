"""Vocabulario de procedencia y frescura — la regla que no se negocia.

Un valor **construido** (interpolado, imputado, anual repartido en meses, último
bueno conocido) nunca se presenta como observación. Findempro siembra
simulaciones de PyME con estos números: costos de importación, márgenes y
precios salen de aquí. Si un valor curado de 2025 entra como si fuera una
medición de hoy, toda la simulación miente sin que nada lo diga.

Este módulo es deliberadamente puro: sin Django, sin red, sin estado. Lo importa
tanto el consumidor de eventos (que escribe la etiqueta) como
``business.data.bolivia_industries`` y la API (que la leen). Que ambos lados
usen el mismo vocabulario es lo que hace que la etiqueta sea comprobable.

Contrato de migración §5.
"""
from __future__ import annotations

# ── Procedencia de un valor ──────────────────────────────────────────────────
OBSERVED_REAL = "OBSERVED_REAL"   # la plataforma lo midió; provenance='observed'
INTERPOLATED = "INTERPOLATED"     # rellenado entre dos puntos reales
IMPUTED = "IMPUTED"               # estimado por un modelo
STALE = "STALE"                   # observación real, pero vieja para su SLA
FALLBACK = "FALLBACK"             # valor curado / último bueno conocido
UNAVAILABLE = "UNAVAILABLE"       # no hay valor que ofrecer

PROVENANCE = (OBSERVED_REAL, INTERPOLATED, IMPUTED, STALE, FALLBACK, UNAVAILABLE)

#: Las únicas etiquetas que un modelo puede consumir como medición.
#: STALE queda fuera a propósito: es real, pero no es "ahora", y quien la use
#: tiene que decidirlo mirando su edad, no heredarla por descuido.
OBSERVATIONS = frozenset({OBSERVED_REAL})

#: Las que NO son una medición de la realidad presente.
CONSTRUCTED = frozenset({INTERPOLATED, IMPUTED, FALLBACK, UNAVAILABLE})

# ── Frescura del estado del consumidor ───────────────────────────────────────
FRESH = "FRESH"
DEGRADED = "DEGRADED"
FRESHNESS_STALE = "STALE"
SOURCE_DOWN = "SOURCE_DOWN"
REPLAYING = "REPLAYING"

FRESHNESS = (FRESH, DEGRADED, FRESHNESS_STALE, SOURCE_DOWN, REPLAYING)

#: De mejor a peor. `worst_freshness` lo usa para resumir varias claves en una.
_FRESHNESS_ORDER = {FRESH: 0, REPLAYING: 1, FRESHNESS_STALE: 2,
                    DEGRADED: 3, SOURCE_DOWN: 4}


def is_observation(label: str | None) -> bool:
    """¿Se puede tratar este valor como una medición de la realidad?

    Cualquier cosa que no sea exactamente OBSERVED_REAL es un "no": una etiqueta
    desconocida, ausente o mal escrita se trata como no-observación. El fallo
    seguro aquí es negar, porque el coste de aceptar un curado como medición es
    una simulación entera calculada sobre un número inventado.
    """
    return label in OBSERVATIONS


def is_constructed(label: str | None) -> bool:
    """¿Este valor lo construyó alguien en vez de medirlo?"""
    return label in CONSTRUCTED


def worst_freshness(labels) -> str:
    """El peor estado de un conjunto. Un consumidor no está más fresco que su
    peor ancla: si el oficial está caído, decir FRESH porque la inflación llegó
    sería exactamente el fallo silencioso que esto existe para impedir."""
    peor = FRESH
    for lab in labels:
        if _FRESHNESS_ORDER.get(lab, 4) > _FRESHNESS_ORDER.get(peor, 0):
            peor = lab if lab in _FRESHNESS_ORDER else SOURCE_DOWN
    return peor


def provenance_of(context: dict, key: str) -> str:
    """Etiqueta de una clave macro dentro de un contexto ya cargado.

    Sin etiqueta explícita **no** se asume observación: se devuelve FALLBACK,
    que es lo que un valor sin procedencia es en el mejor de los casos.
    """
    return (context.get("provenance") or {}).get(key, FALLBACK)


def observed_value(context: dict, key: str):
    """El valor de `key` **sólo si** es una observación real; si no, ``None``.

    Este es el camino que usa quien no puede permitirse un valor construido. El
    que sí puede, lee ``context[key]`` y mira la etiqueta con `provenance_of`.
    """
    if not is_observation(provenance_of(context, key)):
        return None
    return context.get(key)


def describe(context: dict, key: str) -> dict:
    """Todo lo que hay que saber de una clave para poder mostrarla honestamente."""
    freshness = (context.get("freshness") or {}).get(key) or {}
    label = provenance_of(context, key)
    return {
        "key": key,
        "value": context.get(key),
        "provenance": label,
        "is_observation": is_observation(label),
        "source": freshness.get("source") or (context.get("sources") or {}).get(key),
        "data_timestamp": freshness.get("data_timestamp"),
        "freshness_status": freshness.get("freshness_status", SOURCE_DOWN),
        "age_seconds": freshness.get("age_seconds"),
    }
