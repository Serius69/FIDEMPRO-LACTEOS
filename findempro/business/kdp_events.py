"""Consumo por eventos del dataset ``findempro_sector_bo`` — modo CURSOR_STREAM.

Qué cambia respecto de antes
----------------------------
Hasta ahora el contexto macro de Findempro sólo se refrescaba si una persona
tecleaba ``manage.py scrape_bolivia_data``. No había cron, ni entrada de beat, ni
timer: el dato tenía la frescura del último día que alguien se acordó. Este
módulo es el consumidor real, y lo dispara el beat de Celery
(``business.consume_kdp_events``, cada 10 min por ``CELERY_BEAT_SCHEDULE``).

Por qué CURSOR_STREAM y no webhook ni SSE
-----------------------------------------
Findempro tiene worker, así que el webhook era posible; pero exigiría exponer una
ruta pública y custodiar un secreto HMAC para un dataset que se mueve una vez por
semana (BCB) o una vez al año (World Bank). El cursor no exige nada del producto
salvo guardar un número, y sobre un batch que arranca y muere da exactamente la
misma garantía de no perder nada. Contrato §3.

Las tres garantías que no son opcionales (§4)
---------------------------------------------
1. **Cursor persistente.** ``Checkpoint`` en ``settings.KDP_STATE_DIR``. Reanudar
   desde "ahora" perdería en silencio lo ocurrido durante una caída.
2. **Idempotencia por ``event_id``.** La entrega es at-least-once. El
   ``EventConsumer`` descarta repetidos dentro de un proceso; como aquí el
   proceso arranca y muere, la ventana de ``event_id`` vistos también se
   **persiste**, o un replay tras un reinicio volvería a aplicar lo aplicado.
3. **Orden por ``partition_key``.** Un evento con ``event_time`` anterior al
   último aplicado para esa serie no retrocede el estado: se cuenta y se
   descarta. Este dataset mezcla series anuales del World Bank con series
   semanales del BCB en un mismo cursor, así que el desorden entre particiones
   es lo normal, no la excepción.

Y la que importa más aquí (§5)
------------------------------
El riesgo de Findempro no es la antigüedad — World Bank publica una vez al año y
la política lo admite (``max_age_s`` = 2 años, ``on_stale=WARN``). El riesgo es
**un valor curado presentado como observación**. Todo lo que este módulo escribe
lleva su etiqueta de ``business.provenance``, y el curado se distingue del
observado sin tener que adivinar.
"""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from business import provenance as prov
from business.data.curated_market import CURATED, CURATED_PRICES, CURATED_SOURCE

logger = logging.getLogger(__name__)

#: Dónde vive el JSON que lee el resto del producto.
MARKET_DATA_PATH = Path(__file__).resolve().parent / "data" / "bolivia_market_data.json"

#: Serie del dataset → ancla macro de Findempro.
#: `findempro_sector_bo` trae 1368 series (World Bank WDI de 7 países + BCB
#: semanal). Sólo una alimenta hoy una constante de simulación; el resto se
#: guarda como último valor por serie para calibración y reconciliación, sin
#: proyectarse a `macro`, porque inventar un ancla a partir de una serie que
#: nadie pidió sería peor que no tenerla.
SERIES_TO_MACRO = {
    "bcb.inflacion_total_variacion_a_doce_meses": "inflation_annual_pct",
}

#: Cuánto tiempo puede pasar sin ver un evento antes de decir que vamos viejos.
#: No es el SLA del dato (ese lo fija la política, 2 años): es el SLA del
#: consumidor, "¿hace cuánto que no hablo con la plataforma?".
CONSUMER_SILENCE_WARN_S = 24 * 3600

#: Cuántos `event_id` recordar entre corridas.
REMEMBER_EVENTS = 5000


# ────────────────────────────────────────────────────────────── configuración
def _conf(name: str, default=None):
    try:
        from django.conf import settings
        if settings.configured:
            return getattr(settings, name, os.environ.get(name, default))
    except Exception:  # noqa: BLE001
        pass
    return os.environ.get(name, default)


def state_dir() -> Path:
    d = Path(_conf("KDP_STATE_DIR") or (Path.cwd() / "var" / "kdp"))
    d.mkdir(parents=True, exist_ok=True)
    return d


# ─────────────────────────────────────────────────────── estado del consumidor
class ConsumerState:
    """Lo que el consumidor tiene que recordar entre una corrida y la siguiente.

    Vive en un fichero JSON, fuera de git, junto al checkpoint del cursor.
    Borrarlo no destruye nada: hace que se reprocese, y reprocesar es inocuo
    justo porque lo de abajo existe.
    """

    def __init__(self, path: Path):
        self.path = path
        raw = {}
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
        #: partition_key → event_time ISO del último evento APLICADO
        self.last_event_time: dict = dict(raw.get("last_event_time") or {})
        #: event_id ya aplicados, en orden de llegada (ventana acotada)
        self.seen_events: list = list(raw.get("seen_events") or [])
        #: series_key → último valor observado (contexto sectorial completo)
        self.series_latest: dict = dict(raw.get("series_latest") or {})
        self.last_drain_at: str | None = raw.get("last_drain_at")
        self._seen_index = set(self.seen_events)

    # -- idempotencia ------------------------------------------------------
    def already_applied(self, event_id: str) -> bool:
        return event_id in self._seen_index

    def remember(self, event_id: str) -> None:
        if event_id in self._seen_index:
            return
        self.seen_events.append(event_id)
        self._seen_index.add(event_id)
        if len(self.seen_events) > REMEMBER_EVENTS:
            sobran = len(self.seen_events) - REMEMBER_EVENTS
            for old in self.seen_events[:sobran]:
                self._seen_index.discard(old)
            del self.seen_events[:sobran]

    # -- orden -------------------------------------------------------------
    def is_out_of_order(self, partition_key: str, event_time: str | None) -> bool:
        """¿Este evento retrocedería el estado de su partición?

        Sin `event_time` no se puede decidir, y lo que no se puede decidir no se
        aplica a ciegas sobre un valor más nuevo: se considera desordenado.
        """
        previo = self.last_event_time.get(partition_key)
        if previo is None:
            return False
        if not event_time:
            return True
        return _parse(event_time) < _parse(previo)

    def mark_applied(self, partition_key: str, event_time: str | None) -> None:
        if event_time:
            self.last_event_time[partition_key] = event_time

    # -- persistencia ------------------------------------------------------
    def save(self) -> None:
        payload = {
            "last_event_time": self.last_event_time,
            "seen_events": self.seen_events,
            "series_latest": self.series_latest,
            "last_drain_at": self.last_drain_at,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Atómico: un corte a mitad de escritura dejaría un JSON truncado, que
        # se lee como "estado vacío" y haría reprocesar creyendo empezar de cero.
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)


def _parse(ts: str | None) -> datetime:
    if not ts:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        d = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ──────────────────────────────────────────────────────────────── el consumidor
def build_consumer(client=None):
    """Devuelve ``(EventConsumer, Checkpoint)`` ya configurados.

    El cliente es el vendorizado de la plataforma (`kdp_consumer`), no una
    reimplementación: un segundo cliente sería una segunda forma de equivocarse
    con la idempotencia.
    """
    from kdp_consumer import Checkpoint, EventConsumer, KdpClient

    if client is None:
        token = _conf("KDP_API_TOKEN") or None
        client = KdpClient(base_url=_conf("KDP_API_URL", "http://127.0.0.1:8099"),
                           timeout=int(float(_conf("KDP_TIMEOUT", 20))),
                           token=token)
    cp = Checkpoint(state_dir() / "cursor.json")
    # `remember=0` apaga la ventana de idempotencia EN MEMORIA del cliente, y no
    # es un descuido: este consumidor arranca y muere en cada tick del beat, así
    # que una ventana de proceso no protegería de nada tras el reinicio. La
    # idempotencia la lleva `ConsumerState`, que la persiste. Con las dos
    # activas el duplicado se descartaba antes de llegar al handler y el informe
    # decía cero duplicados: una defensa que funciona pero no se puede medir es
    # indistinguible de una que no está.
    ec = EventConsumer(client, _conf("KDP_CONSUMER_ID", "Findempro"),
                       _conf("KDP_DATASET_ID", "findempro_sector_bo"),
                       checkpoint=cp, remember=0)
    return ec, cp


def _drain_with_retry(consumer, handler, *, attempts: int = 3,
                      backoff_s: float = 1.0) -> int:
    """Drena reintentando con espera creciente.

    Un corte de red a mitad de un lote es rutina: un proxy, un despliegue, una
    red que parpadea. Como el cursor sólo avanza sobre lo confirmado, reintentar
    reanuda donde se quedó en vez de volver a empezar — que es la diferencia
    entre reconectar y reprocesar.
    """
    import requests

    ultimo = None
    for intento in range(1, attempts + 1):
        try:
            return consumer.drain(handler)
        except requests.RequestException as exc:
            ultimo = exc
            if intento == attempts:
                break
            espera = backoff_s * (2 ** (intento - 1))
            logger.warning("KDP: corte drenando (%s), reintento %d/%d en %.1fs",
                           exc, intento + 1, attempts, espera)
            time.sleep(espera)
    raise ultimo  # noqa: RSE102 — se propaga la última, ya con contexto en el log


def consume(*, client=None, write: bool = True, apply_point_reads: bool = True,
            path: Path | None = None) -> dict:
    """Drena el cursor, aplica lo nuevo y reescribe el contexto macro.

    Devuelve un informe con las métricas del contrato §7. No levanta si KDP no
    responde: la política de Findempro es ``on_unavailable=DEGRADE`` con
    ``allow_lkg=true``, así que conserva el último bueno conocido **y lo dice**.
    """
    t0 = time.monotonic()
    estado = ConsumerState(state_dir() / "consumer_state.json")
    informe = {
        "mode": "CURSOR_STREAM",
        "consumer": _conf("KDP_CONSUMER_ID", "Findempro"),
        "dataset_id": _conf("KDP_DATASET_ID", "findempro_sector_bo"),
        "cursor_before": None, "cursor_after": None,
        "events_applied": 0, "events_duplicate": 0, "events_out_of_order": 0,
        "lag_events": None, "schema_version": None,
        "kdp_available": False, "degraded_reason": None,
        "kdp_to_consumer_ms": [], "end_to_end_ms": [],
    }

    aplicados: list = []

    def handler(ev: dict) -> None:
        recibido = _now()
        eid = ev.get("event_id")
        pkey = ev.get("partition_key") or ev.get("data", {}).get("series_key") or eid
        etime = ev.get("event_time")

        # 1) Idempotencia entre corridas: el EventConsumer sólo recuerda dentro
        #    de un proceso, y este proceso muere en cada tick del beat.
        if eid and estado.already_applied(eid):
            informe["events_duplicate"] += 1
            return
        # 2) Orden dentro de la partición: nunca hacia atrás.
        if estado.is_out_of_order(pkey, etime):
            informe["events_out_of_order"] += 1
            logger.info("KDP: evento fuera de orden en %s (%s < %s), descartado",
                        pkey, etime, estado.last_event_time.get(pkey))
            if eid:
                estado.remember(eid)
            return

        data = ev.get("data") or {}
        valor = data.get("value")
        if valor is not None:
            estado.series_latest[pkey] = {
                "value": valor,
                "unit": data.get("unit"),
                "observed_at": data.get("observed_at") or etime,
                "source": ev.get("source") or data.get("source"),
                "geography": data.get("geography"),
                "quality": data.get("quality"),
                "seq": ev.get("seq"),
            }
        estado.mark_applied(pkey, etime)
        if eid:
            estado.remember(eid)
        informe["events_applied"] += 1
        informe["schema_version"] = ev.get("schema_version") or informe["schema_version"]

        pub = _parse(ev.get("published_at"))
        if pub.year > 1:
            informe["kdp_to_consumer_ms"].append(
                (recibido - pub).total_seconds() * 1000.0)
        src_ts = _parse(ev.get("source_timestamp") or etime)
        if src_ts.year > 1:
            informe["end_to_end_ms"].append((recibido - src_ts).total_seconds() * 1000.0)
        aplicados.append(ev)

    # ── drenado ──────────────────────────────────────────────────────────────
    try:
        consumidor, _cp = build_consumer(client)
        informe["cursor_before"] = consumidor.position()
        _drain_with_retry(consumidor, handler)
        informe["cursor_after"] = consumidor.position()
        informe["kdp_available"] = True
        try:
            informe["lag_events"] = consumidor.poll(limit=1).get("lag_events")
        except Exception:  # noqa: BLE001 — el lag es informativo, no bloquea
            pass
        estado.last_drain_at = _now().isoformat()
    except Exception as exc:  # noqa: BLE001
        # DEGRADE con la etiqueta puesta. No se cae con la plataforma, pero
        # tampoco finge estar fresco: `degraded_reason` viaja hasta el JSON.
        informe["degraded_reason"] = f"{type(exc).__name__}: {exc}"
        informe["cursor_after"] = informe["cursor_before"]
        logger.warning("KDP no disponible drenando eventos: %s", exc)

    estado.save()

    if write:
        informe["market_data"] = write_market_context(
            estado, informe, apply_point_reads=apply_point_reads, path=path)

    informe["duration_ms"] = round((time.monotonic() - t0) * 1000.0, 1)
    return informe


# ─────────────────────────────────────────────── proyección al contexto macro
def _fallback(key: str, motivo: str) -> dict:
    """Un ancla que NO se pudo observar. Va con FALLBACK, siempre."""
    return {
        "value": CURATED[key],
        "source": CURATED_SOURCE,
        "provenance": prov.FALLBACK,
        "data_timestamp": None,
        "freshness_status": prov.SOURCE_DOWN,
        "age_seconds": None,
        "note": motivo,
    }


def _from_events(estado: ConsumerState, series_key: str, macro_key: str) -> dict | None:
    fila = estado.series_latest.get(series_key)
    if not fila or fila.get("value") is None:
        return None
    observed_at = fila.get("observed_at")
    edad = (_now() - _parse(observed_at)).total_seconds() if observed_at else None
    # `max_age_s` de la política (2 años). on_stale=WARN: se conserva el valor,
    # cambia la etiqueta. Un dato viejo mostrado como actual es el fallo que
    # esto existe para impedir; un dato viejo mostrado como viejo es honesto.
    limite = float(_conf("KDP_MAX_AGE_S", 63072000))
    viejo = edad is not None and edad > limite
    if fila.get("quality") == "rejected":
        return None
    return {
        "value": round(float(fila["value"]), 2),
        "source": f"kdp-event:{fila.get('source') or 'desconocida'}",
        "provenance": prov.STALE if viejo else prov.OBSERVED_REAL,
        "data_timestamp": observed_at,
        "freshness_status": prov.FRESHNESS_STALE if viejo else prov.FRESH,
        "age_seconds": round(edad, 1) if edad is not None else None,
        "series_key": series_key,
        "seq": fila.get("seq"),
    }


def _from_point_read(reader, key: str) -> dict:
    """Lectura puntual de `/v1/latest/...`, o el curado etiquetado si falla."""
    from business.kdp_source import KdpUnavailable

    try:
        r = reader()
    except KdpUnavailable as exc:
        logger.warning("KDP no dio %s (%s) — se conserva el curado, etiquetado", key, exc)
        return _fallback(key, str(exc))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Fallo inesperado leyendo %s: %s", key, exc)
        return _fallback(key, f"{type(exc).__name__}: {exc}")
    return {
        "value": r.value,
        "source": r.source,
        "provenance": r.provenance,
        "data_timestamp": r.data_timestamp,
        "freshness_status": r.freshness_status,
        "age_seconds": round(r.age_seconds, 1) if r.age_seconds is not None else None,
    }


def build_market_context(estado: ConsumerState, informe: dict,
                         *, apply_point_reads: bool = True) -> dict:
    """Arma el payload de ``bolivia_market_data.json`` con procedencia por clave."""
    campos: dict = {}

    # Inflación: vía primaria = evento. Si aún no llegó ninguno (cursor en cero),
    # se intenta la lectura puntual, y sólo entonces el curado.
    infl = None
    for serie, macro_key in SERIES_TO_MACRO.items():
        if macro_key != "inflation_annual_pct":
            continue
        infl = _from_events(estado, serie, macro_key)
    if infl is None and apply_point_reads:
        from business import kdp_source
        infl = _from_point_read(kdp_source.read_inflacion_anual, "inflation_annual_pct")
    campos["inflation_annual_pct"] = infl or _fallback(
        "inflation_annual_pct", "sin evento ni lectura puntual")

    # Oficial y paralelo: no pertenecen a `findempro_sector_bo`, viven en
    # `/v1/latest/...`. Se leen a la vez que se drena, en el mismo tick del beat.
    if apply_point_reads:
        from business import kdp_source
        campos["fx_usd_bob_official"] = _from_point_read(
            kdp_source.read_fx_oficial, "fx_usd_bob_official")
        campos["fx_usd_bob_parallel"] = _from_point_read(
            kdp_source.read_paralelo, "fx_usd_bob_parallel")
    else:
        campos["fx_usd_bob_official"] = _fallback("fx_usd_bob_official",
                                                  "lecturas puntuales desactivadas")
        campos["fx_usd_bob_parallel"] = _fallback("fx_usd_bob_parallel",
                                                  "lecturas puntuales desactivadas")

    # El salario mínimo es un decreto, no una serie: KDP no lo publica y
    # probablemente nunca lo haga. Curado permanente, etiquetado como tal.
    campos["min_wage_month_bs"] = {
        "value": CURATED["min_wage_month_bs"],
        "source": CURATED_SOURCE,
        "provenance": prov.FALLBACK,
        "data_timestamp": None,
        "freshness_status": prov.DEGRADED,
        "age_seconds": None,
        "note": "DS 5383 (2025); KDP no publica el salario mínimo",
    }

    macro = {k: v["value"] for k, v in campos.items()}
    fuentes = {k: v["source"] for k, v in campos.items()}
    procedencia = {k: v["provenance"] for k, v in campos.items()}
    frescura = {
        k: {kk: vv for kk, vv in v.items() if kk != "value"}
        for k, v in campos.items()
    }

    estados = [v["freshness_status"] for v in campos.values()]
    if informe.get("degraded_reason"):
        estados.append(prov.SOURCE_DOWN)
    global_freshness = prov.worst_freshness(estados)
    sellos = [v["data_timestamp"] for v in campos.values() if v.get("data_timestamp")]

    kdp_meta = {
        "mode": informe.get("mode", "CURSOR_STREAM"),
        "consumer": informe.get("consumer"),
        "dataset_id": informe.get("dataset_id"),
        "cursor_seq": informe.get("cursor_after"),
        "events_applied": informe.get("events_applied"),
        "events_duplicate": informe.get("events_duplicate"),
        "events_out_of_order": informe.get("events_out_of_order"),
        "lag_events": informe.get("lag_events"),
        "schema_version": informe.get("schema_version"),
        "available": informe.get("kdp_available"),
        "degraded_reason": informe.get("degraded_reason"),
        "drained_at": _now().isoformat(),
        "series_tracked": len(estado.series_latest),
    }
    for nombre, muestras in (("kdp_to_consumer_ms", informe.get("kdp_to_consumer_ms")),
                             ("end_to_end_ms", informe.get("end_to_end_ms"))):
        if muestras:
            kdp_meta[nombre] = {"n": len(muestras),
                                "p50": round(sorted(muestras)[len(muestras) // 2], 1),
                                "max": round(max(muestras), 1)}

    return {
        "macro": macro,
        "prices_bs": dict(CURATED_PRICES),
        "meta": {
            # `sources` se conserva con el mismo nombre y el mismo literal
            # `fallback-curado` de 2025: hay consumidores que lo comparan.
            "sources": fuentes,
            # Lo nuevo: la etiqueta legible, por clave. Ver business.provenance.
            "provenance": procedencia,
            "freshness": frescura,
            "freshness_status": global_freshness,
            "data_timestamp": max(sellos) if sellos else None,
            # Los precios minoristas nunca fueron observados por nadie: KDP no
            # publica precios de retail boliviano. Decirlo aquí evita que un
            # consumidor los lea como si vinieran de la plataforma.
            "prices_provenance": prov.FALLBACK,
            "kdp": kdp_meta,
            "generated_by": "celery beat · business.consume_kdp_events",
            "generated_at": _now().isoformat(),
            "note": ("Consumo por cursor de KDP. Cada ancla lleva su procedencia: "
                     "OBSERVED_REAL es medición, FALLBACK es el curado de respaldo. "
                     "Nunca se presentan como lo mismo."),
        },
    }


def write_market_context(estado: ConsumerState, informe: dict,
                         *, apply_point_reads: bool = True,
                         path: Path | None = None) -> dict:
    payload = build_market_context(estado, informe, apply_point_reads=apply_point_reads)
    destino = path or MARKET_DATA_PATH
    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(destino)
    return payload


# ──────────────────────────────────────────────────────── lectura para la API
def load_market_context(path: Path | None = None) -> dict:
    """Carga el contexto en la forma plana que espera ``business.provenance``.

    Devuelve ``{clave: valor, 'provenance': {...}, 'freshness': {...}, ...}`` para
    que `provenance.observed_value(ctx, clave)` funcione sin que el llamador
    tenga que saber cómo está anidado el JSON.
    """
    destino = path or MARKET_DATA_PATH
    try:
        data = json.loads(destino.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"provenance": {}, "freshness": {}, "sources": {},
                "freshness_status": prov.SOURCE_DOWN, "data_timestamp": None}
    meta = data.get("meta") or {}
    ctx = dict(data.get("macro") or {})
    ctx["provenance"] = meta.get("provenance") or {}
    ctx["freshness"] = meta.get("freshness") or {}
    ctx["sources"] = meta.get("sources") or {}
    ctx["freshness_status"] = meta.get("freshness_status", prov.SOURCE_DOWN)
    ctx["data_timestamp"] = meta.get("data_timestamp")
    ctx["kdp"] = meta.get("kdp") or {}
    return ctx


def override_field(key: str, *, value, source: str, provenance: str,
                   data_timestamp: str | None = None,
                   freshness_status: str | None = None,
                   note: str | None = None, path: Path | None = None) -> dict:
    """Sustituye UNA clave macro en el JSON ya escrito, con su etiqueta.

    Existe para la red de seguridad: cuando KDP no dio la inflación y el INE sí,
    el valor del INE entra por aquí — con su propia fuente (`ine-wp-rest`, no
    `kdp:`), para que quede claro que ese número no pasó por la plataforma ni por
    sus controles de calidad.
    """
    destino = path or MARKET_DATA_PATH
    data = json.loads(destino.read_text(encoding="utf-8"))
    meta = data.setdefault("meta", {})
    data.setdefault("macro", {})[key] = value
    meta.setdefault("sources", {})[key] = source
    meta.setdefault("provenance", {})[key] = provenance
    frescura = meta.setdefault("freshness", {})
    frescura[key] = {
        "source": source,
        "provenance": provenance,
        "data_timestamp": data_timestamp,
        "freshness_status": freshness_status or (
            prov.FRESH if prov.is_observation(provenance) else prov.DEGRADED),
        "age_seconds": None,
        "note": note,
    }
    meta["freshness_status"] = prov.worst_freshness(
        [v.get("freshness_status") for v in frescura.values()])
    sellos = [v.get("data_timestamp") for v in frescura.values() if v.get("data_timestamp")]
    meta["data_timestamp"] = max(sellos) if sellos else None
    tmp = destino.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(destino)
    return data
