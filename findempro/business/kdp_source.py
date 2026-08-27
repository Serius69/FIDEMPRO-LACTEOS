"""Fuente KDP para el contexto macro con el que Findempro siembra simulaciones.

Por qué existe
--------------
``scrape_bolivia_data._scrape_fx`` buscaba el tipo de cambio oficial con el regex
``\\b(6[.,]9\\d)\\b`` y sólo aceptaba valores entre 6,5 y 7,5. Bolivia sostuvo
Bs 6,96 por dólar desde 2011, así que la regla era correcta cuando se escribió;
hoy el oficial está en 11,50 y **el scraper no podía encontrarlo aunque el BCB lo
publicara**: lo descartaba por fuera de rango. El resultado era que siempre
devolvía ``fallback-curado`` y ``bolivia_market_data.json`` quedaba anclado en
6,96. Toda simulación de PyME parte de ahí.

Qué cubre este módulo
---------------------
Las **lecturas puntuales**: el oficial y el paralelo, que viven en
``/v1/latest/...`` y no pertenecen al dataset con suscripción
(``findempro_sector_bo``). La inflación y el resto del contexto sectorial llegan
por eventos, en ``business.kdp_events``.

Autenticación (2026-08-27)
--------------------------
La API pasó a exigir token en **todos** los ``/v1/*``: sin cabecera responde 401.
Este módulo enviaba las peticiones sin credencial, así que desde ese cambio cada
lectura levantaba ``KdpUnavailable`` y el llamador caía al curado **en
silencio** — el JSON quedó con los valores del 25 de agosto y una etiqueta que
decía ``kdp:``. Ahora manda ``settings.KDP_API_TOKEN`` y, si no hay token, lo
dice con un mensaje que nombra la variable que falta en vez de fingir una caída
de red.

Cada lectura vuelve con su procedencia puesta (``business.provenance``): un
valor no se puede leer de aquí sin saber si es una medición o un curado.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone

import requests

from business import provenance as prov

logger = logging.getLogger(__name__)


def _conf(name: str, default):
    """Settings de Django si hay, entorno si no. Este módulo se usa también
    desde tests puros y desde scripts sin Django arrancado."""
    try:
        from django.conf import settings
        if settings.configured:
            return getattr(settings, name, os.environ.get(name, default))
    except Exception:  # noqa: BLE001 — Django ausente o a medio configurar
        pass
    return os.environ.get(name, default)


# Compatibilidad: había módulos y tests leyendo estas constantes.
KDP_API_URL = os.environ.get("KDP_API_URL", "http://127.0.0.1:8099")
KDP_TIMEOUT = float(os.environ.get("KDP_TIMEOUT", "20"))

# Bandas de plausibilidad amplias a propósito: acotar el rango al valor vigente
# es exactamente el error que este módulo corrige.
FX_BAND = (1.0, 100.0)
INFLATION_BAND = (-20.0, 200.0)


class KdpUnavailable(RuntimeError):
    """KDP no respondió, o respondió algo que no se puede consumir.

    El llamador degrada según la política de Findempro (`on_unavailable=DEGRADE`,
    `allow_lkg=true`): conserva el último bueno conocido y **lo etiqueta**.
    """


@dataclass
class Reading:
    """Una lectura puntual con todo lo que hace falta para mostrarla honestamente."""
    key: str
    value: float
    source: str
    provenance: str
    data_timestamp: str | None = None
    freshness_status: str = prov.FRESH
    age_seconds: float | None = None
    detail: dict = field(default_factory=dict)

    @property
    def is_observation(self) -> bool:
        return prov.is_observation(self.provenance)

    def as_tuple(self) -> tuple[float, str]:
        return self.value, self.source


def _headers() -> dict:
    token = _conf("KDP_API_TOKEN", "") or os.environ.get("KDP_API_TOKEN", "")
    if not token:
        # No hay modo anónimo: la API sirve datos clasificados y responde 401.
        # Fallar aquí con el nombre de la variable es la señal de que falta
        # configurar; devolver "no disponible" sin más lo haría parecer un corte.
        raise KdpUnavailable(
            "falta KDP_API_TOKEN: la API de KDP exige el token propio de "
            "Findempro (KDP_TOKEN_FINDEMPRO en consumers.dev.env)")
    return {"Authorization": f"Bearer {token}"}


def _get(path: str, **params) -> dict:
    base = _conf("KDP_API_URL", KDP_API_URL)
    timeout = float(_conf("KDP_TIMEOUT", KDP_TIMEOUT))
    try:
        resp = requests.get(f"{base}{path}", params=params or None,
                            timeout=timeout, headers=_headers())
        if resp.status_code in (401, 403):
            raise KdpUnavailable(
                f"KDP rechazó las credenciales ({resp.status_code}) en {path}: "
                + ("el token de Findempro no alcanza este dato"
                   if resp.status_code == 403 else "token ausente o inválido"))
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        raise KdpUnavailable(f"KDP no disponible ({path}): {exc}") from exc


def _age_seconds(observed_at: str | None) -> float | None:
    if not observed_at:
        return None
    try:
        d = datetime.fromisoformat(observed_at)
    except ValueError:
        return None
    if not d.tzinfo:
        d = d.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - d).total_seconds()


def _latest_reading(key: str, path: str, band: tuple[float, float],
                    default_slug: str) -> Reading:
    """Lee un ``/v1/latest/...`` y lo devuelve con su etiqueta puesta.

    `is_stale` de la plataforma NO descarta el valor: la política de Findempro
    es `on_stale=WARN`. Lo que sí hace es cambiar la etiqueta a STALE, para que
    nadie lo consuma como una medición de ahora mismo sin haberlo decidido.
    """
    payload = _get(path)
    if payload.get("provenance") != "observed":
        raise KdpUnavailable(
            f"KDP devolvió provenance={payload.get('provenance')!r} para {key}")
    if payload.get("quality") == "rejected":
        raise KdpUnavailable(f"KDP marcó {key} como rechazado")
    v = float(payload["value"])
    if not (band[0] < v < band[1]):
        raise KdpUnavailable(f"{key} fuera de banda: {v}")

    observed_at = payload.get("observed_at")
    stale = bool(payload.get("is_stale"))
    return Reading(
        key=key,
        value=round(v, 2),
        source=f"kdp:{payload.get('source_slug', default_slug)}",
        provenance=prov.STALE if stale else prov.OBSERVED_REAL,
        data_timestamp=observed_at,
        freshness_status=prov.FRESHNESS_STALE if stale else prov.FRESH,
        age_seconds=_age_seconds(observed_at),
        detail={"expected_max_lag_s": payload.get("expected_max_lag_s"),
                "unit": payload.get("unit")},
    )


def read_fx_oficial() -> Reading:
    """Tipo de cambio oficial USD/BOB observado, con procedencia."""
    r = _latest_reading("fx_usd_bob_official",
                        "/v1/latest/dolarapi.bo.oficial.usd_bob.venta",
                        FX_BAND, "dolarapi-bo")
    logger.info("KDP oficial USD/BOB = %.2f (%s, %s)", r.value, r.data_timestamp,
                r.provenance)
    return r


def read_paralelo() -> Reading:
    """Referencia del paralelo USDT/BOB, del libro P2P observado."""
    r = _latest_reading("fx_usd_bob_parallel",
                        "/v1/latest/criptoya.usdt_bob.binancep2p.ask",
                        FX_BAND, "criptoya-bo")
    logger.info("KDP paralelo USDT/BOB = %.2f (%s, %s)", r.value, r.data_timestamp,
                r.provenance)
    return r


def read_inflacion_anual() -> Reading:
    """Inflación a doce meses del BCB, serie mensual real.

    Camino de reconciliación: la vía primaria de la inflación es el evento de
    ``findempro_sector_bo`` (`bcb.inflacion_total_variacion_a_doce_meses`). Esta
    lectura puntual queda para el arranque en frío — cuando aún no se ha drenado
    un solo evento y el cursor está en cero.

    OJO (verificado 2026-08-27): ese endpoint es la superficie de **Insights**, y
    el token de Findempro recibe **403** sobre él. Es decir: este camino no puede
    funcionar con esta credencial, y no es un fallo a arreglar aflojando el
    alcance del token — un token que llega a los datos de otro producto deja de
    ser una credencial. En la práctica no se nota porque `consume()` drena antes
    de proyectar, así que el valor sale del evento; si aun así no hubiera
    ninguno, esto levanta y el ancla sale etiquetada FALLBACK, que es lo
    correcto.
    """
    payload = _get("/v1/products/insights/series/inflacion_doce_meses")
    if payload.get("provenance") != "observed":
        raise KdpUnavailable(
            f"KDP devolvió provenance={payload.get('provenance')!r} para inflación")
    obs = payload.get("observations") or []
    if not obs:
        raise KdpUnavailable("KDP no tiene observaciones de inflación")
    last = obs[-1]
    v = float(last["valor"])
    if not (INFLATION_BAND[0] < v < INFLATION_BAND[1]):
        raise KdpUnavailable(f"inflación fuera de banda: {v}")
    logger.info("KDP inflación 12m = %.2f%% (%s)", v, last["fecha"])
    return Reading(
        key="inflation_annual_pct",
        value=round(v, 2),
        source=f"kdp:{last.get('source', 'bcb-semanal-bulk')}",
        provenance=prov.OBSERVED_REAL,
        data_timestamp=last.get("fecha"),
        freshness_status=prov.FRESH,
        age_seconds=_age_seconds(last.get("fecha")),
    )


# ── API histórica (tupla). Se conserva: hay llamadores y tests que la usan. ──
def fetch_fx_oficial() -> tuple[float, str]:
    return read_fx_oficial().as_tuple()


def fetch_inflacion_anual() -> tuple[float, str]:
    return read_inflacion_anual().as_tuple()


def fetch_paralelo() -> tuple[float, str]:
    return read_paralelo().as_tuple()


def available() -> bool:
    """¿Responde la plataforma? `/health` no exige token a propósito."""
    base = _conf("KDP_API_URL", KDP_API_URL)
    try:
        resp = requests.get(f"{base}/health",
                            timeout=float(_conf("KDP_TIMEOUT", KDP_TIMEOUT)))
        resp.raise_for_status()
        return True
    except requests.RequestException:
        return False
