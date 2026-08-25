"""Fuente KDP para el contexto macro con el que Findempro siembra simulaciones.

Por qué existe
--------------
``scrape_bolivia_data._scrape_fx`` busca el tipo de cambio oficial con el regex
``\\b(6[.,]9\\d)\\b`` y sólo acepta valores entre 6,5 y 7,5. Bolivia sostuvo
Bs 6,96 por dólar desde 2011, así que la regla era correcta cuando se escribió;
hoy el oficial está en 11,50 y **el scraper no puede encontrarlo aunque el BCB lo
publique**: lo descartaría por fuera de rango. El resultado es que siempre
devuelve ``fallback-curado`` y ``bolivia_market_data.json`` queda anclado en 6,96.

Toda simulación de PyME parte de ahí: costos de importación, márgenes y precios
se calculan con un dólar oficial 65 % por debajo del real.

KDP publica el oficial observado y la inflación mensual real del BCB. Este módulo
los lee y deja dicho de dónde salió cada número.
"""
from __future__ import annotations

import logging
import os

import requests

logger = logging.getLogger(__name__)

KDP_API_URL = os.environ.get("KDP_API_URL", "http://127.0.0.1:8099")
KDP_TIMEOUT = float(os.environ.get("KDP_TIMEOUT", "20"))

# Bandas de plausibilidad amplias a propósito: acotar el rango al valor vigente
# es exactamente el error que este módulo corrige.
FX_BAND = (1.0, 100.0)
INFLATION_BAND = (-20.0, 200.0)


class KdpUnavailable(RuntimeError):
    """KDP no respondió. El llamador cae a su ruta previa, sin inventar nada."""


def _get(path: str, **params) -> dict:
    try:
        resp = requests.get(f"{KDP_API_URL}{path}", params=params or None,
                            timeout=KDP_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        raise KdpUnavailable(f"KDP no disponible ({path}): {exc}") from exc


def fetch_fx_oficial() -> tuple[float, str]:
    """Tipo de cambio oficial USD/BOB observado. Devuelve (valor, fuente)."""
    payload = _get("/v1/latest/dolarapi.bo.oficial.usd_bob.venta")
    if payload.get("provenance") != "observed":
        raise KdpUnavailable(
            f"KDP devolvió provenance={payload.get('provenance')!r} para el oficial")
    if payload.get("quality") == "rejected":
        raise KdpUnavailable("KDP marcó el oficial como rechazado")
    v = float(payload["value"])
    if not (FX_BAND[0] < v < FX_BAND[1]):
        raise KdpUnavailable(f"tipo de cambio fuera de banda: {v}")
    logger.info("KDP oficial USD/BOB = %.2f (observado %s)", v, payload.get("observed_at"))
    return round(v, 2), f"kdp:{payload.get('source_slug', 'dolarapi-bo')}"


def fetch_inflacion_anual() -> tuple[float, str]:
    """Inflación a doce meses del BCB, serie mensual real. Devuelve (valor, fuente)."""
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
    return round(v, 2), f"kdp:{last.get('source', 'bcb-semanal-bulk')}"


def fetch_paralelo() -> tuple[float, str]:
    """Referencia del paralelo USDT/BOB, del libro P2P observado."""
    payload = _get("/v1/latest/criptoya.usdt_bob.binancep2p.ask")
    if payload.get("provenance") != "observed":
        raise KdpUnavailable("provenance no observada para el paralelo")
    v = float(payload["value"])
    if not (FX_BAND[0] < v < FX_BAND[1]):
        raise KdpUnavailable(f"paralelo fuera de banda: {v}")
    return round(v, 2), f"kdp:{payload.get('source_slug', 'criptoya-bo')}"


def available() -> bool:
    try:
        _get("/health")
        return True
    except KdpUnavailable:
        return False
