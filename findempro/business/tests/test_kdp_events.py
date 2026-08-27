"""Tests obligatorios del consumidor de eventos de KDP (contrato §6).

Los nombres de arriba de cada test son los del contrato, a propósito: la lista
de garantías y la lista de pruebas tienen que poder leerse en paralelo.

Los que no tocan la red usan un cliente falso que implementa exactamente los dos
métodos que `EventConsumer` llama (`_get` y `_post`). No se sustituye el
`EventConsumer` ni el `Checkpoint`: si el cursor o la idempotencia se rompieran,
estos tests lo verían. Un mock que reemplaza lo que se quiere probar no es un
test.

`test_dataset_allowed_...`, `test_authentication_...` y
`test_reconnect_contra_api_real` van contra la API real de DEV en
127.0.0.1:8099 y se saltan sólo si no hay token en el entorno.
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import requests

from business import kdp_events, provenance as prov

KDP_URL = os.environ.get("KDP_API_URL", "http://127.0.0.1:8099")
KDP_TOKEN = os.environ.get("KDP_API_TOKEN", "")
DATASET = "findempro_sector_bo"
CONSUMER = "Findempro"

#: El token de relleno de settings/testing.py no vale contra la API real.
_TOKEN_REAL = KDP_TOKEN and not KDP_TOKEN.startswith("kdpt_testing")


def _kdp_vivo() -> bool:
    try:
        return requests.get(f"{KDP_URL}/health", timeout=3).ok
    except requests.RequestException:
        return False


requiere_api_real = pytest.mark.skipif(
    not (_TOKEN_REAL and _kdp_vivo()),
    reason=("necesita la API real de KDP en DEV y KDP_API_TOKEN "
            "(KDP_TOKEN_FINDEMPRO de consumers.dev.env)"))


# ─────────────────────────────────────────────────────────── plataforma falsa
def _evento(seq: int, *, serie="bcb.inflacion_total_variacion_a_doce_meses",
            valor=4.93, event_time=None, event_id=None, schema="1.0.0",
            published_at=None, source="bcb-semanal-bulk"):
    et = event_time or "2026-07-31T00:00:00+00:00"
    return {
        "event_id": event_id or str(uuid.uuid4()),
        "seq": seq,
        "dataset_id": DATASET,
        "event_type": "dataset.updated",
        "stream": "live",
        "partition_key": serie,
        "schema_version": schema,
        "source": source,
        "source_timestamp": et,
        "event_time": et,
        "published_at": published_at or datetime.now(timezone.utc).isoformat(),
        "data": {"series_key": serie, "value": valor, "unit": "percent",
                 "observed_at": et, "source": source, "quality": "ok",
                 "geography": "BO", "dataset_id": DATASET},
    }


class ClienteFalso:
    """La plataforma, reducida a lo que `EventConsumer` realmente le pide."""

    def __init__(self, eventos, *, fallos_get=0):
        self.eventos = list(eventos)
        self.acks: list = []
        self.entregas = 0
        self.fallos_get = fallos_get
        self.base = "http://kdp.falso"
        self.session = None

    def _get(self, path, **params):
        if path == "/v1/events":
            if self.fallos_get > 0:
                self.fallos_get -= 1
                raise requests.ConnectionError("corte simulado")
            after = int(params.get("after_seq") or 0)
            limite = int(params.get("limit") or 200)
            pendientes = [e for e in self.eventos if e["seq"] > after]
            lote = pendientes[:limite]
            self.entregas += len(lote)
            return {"dataset_id": DATASET, "events": lote,
                    "head_seq": max((e["seq"] for e in self.eventos), default=0),
                    "lag_events": len(pendientes) - len(lote)}
        raise AssertionError(f"path inesperado: {path}")

    def _post(self, path, **params):
        assert path == "/v1/events/ack"
        self.acks.append(int(params["seq"]))
        return {"ok": True}


@pytest.fixture
def estado_aislado(tmp_path, settings):
    """Cursor y estado en un directorio propio: un test no puede mover el real."""
    settings.KDP_STATE_DIR = str(tmp_path / "kdp")
    settings.KDP_CONSUMER_ID = CONSUMER
    settings.KDP_DATASET_ID = DATASET
    settings.KDP_MAX_AGE_S = 63072000
    return tmp_path


def _consumir(cliente, tmp_path, **kw):
    kw.setdefault("apply_point_reads", False)
    kw.setdefault("path", tmp_path / "market.json")
    return kdp_events.consume(client=cliente, **kw)


# ═══════════════════════════════════════════════ SCHEMA_VERSION_COMPATIBLE
def test_schema_version_compatible_acepta_el_menor_y_rechaza_el_mayor():
    """Un 2.x sobre un consumidor que fijó 1.x tiene que fallar en DEV.

    La comprobación vive en el cliente vendorizado (`check_contract`), que es
    justamente el punto donde no se puede olvidar por producto.
    """
    from kdp_consumer import KdpClient, KdpSchemaError

    cli = KdpClient(base_url=KDP_URL, token="irrelevante")
    base = {"dataset_id": DATASET, "row_count": 10, "provenance": {"observed": 10},
            "quality": {"ok": 10}, "staleness": {"age_seconds": 1, "sla_seconds": 10 ** 9}}

    cli.check_contract({**base, "schema_version": "1.4.2"}, expect_schema="1.x")

    with pytest.raises(KdpSchemaError, match="incompatible major version"):
        cli.check_contract({**base, "schema_version": "2.0.0"}, expect_schema="1.x")


@requiere_api_real
def test_schema_version_compatible_contra_api_real():
    """Lo que la plataforma sirve HOY tiene que seguir siendo 1.x para Findempro."""
    from kdp_consumer import KdpClient

    cli = KdpClient(base_url=KDP_URL, token=KDP_TOKEN)
    contrato = cli.contract(DATASET)
    cli.check_contract(contrato, expect_schema="1.x",
                       max_age_s=63072000)
    assert contrato["schema_version"].startswith("1.")


# ═══════════════════════════════════════════════════════════ DATASET_ALLOWED
@requiere_api_real
def test_dataset_allowed_el_token_no_alcanza_datasets_ajenos():
    """El token de Findempro tiene que dar 403 sobre un dataset de otro producto.

    Si diera 200, no sería una credencial: sería una llave maestra con copias, y
    una filtración de la de Findempro sería la filtración de todas.
    """
    from kdp_consumer import KdpAuthError, KdpClient

    cli = KdpClient(base_url=KDP_URL, token=KDP_TOKEN)
    cli.contract(DATASET)                       # el propio: pasa

    with pytest.raises(KdpAuthError) as exc:
        cli.contract("bi_business_ledger")      # el ajeno: 403
    assert "403" in str(exc.value)

    # Y tampoco por la puerta de los eventos.
    with pytest.raises(KdpAuthError) as exc2:
        cli._get("/v1/events", dataset_id="bi_business_ledger", after_seq=0, limit=1)
    assert "403" in str(exc2.value)


# ═════════════════════════════════════════════════════════════ AUTHENTICATION
@requiere_api_real
def test_authentication_sin_token_es_401():
    """Sin credencial no se sirve un solo dato, ni contrato ni eventos."""
    from kdp_consumer import KdpAuthError, KdpClient

    anon = KdpClient(base_url=KDP_URL, token="")
    anon.session.headers.pop("Authorization", None)
    with pytest.raises(KdpAuthError) as exc:
        anon.contract(DATASET)
    assert "401" in str(exc.value)

    r = requests.get(f"{KDP_URL}/v1/events",
                     params={"dataset_id": DATASET, "after_seq": 0, "limit": 1},
                     timeout=10)
    assert r.status_code == 401


@requiere_api_real
def test_authentication_kdp_source_manda_el_token():
    """La regresión concreta: `kdp_source` salía sin cabecera y comía 401.

    El síntoma no era un error, era peor: el producto caía al valor curado en
    silencio y seguía escribiendo la etiqueta `kdp:` en el JSON.
    """
    from business import kdp_source

    lectura = kdp_source.read_fx_oficial()
    assert lectura.value > 1.0
    assert lectura.source.startswith("kdp:")
    assert lectura.provenance in (prov.OBSERVED_REAL, prov.STALE)


# ══════════════════════════════════════════════════════════════ CURSOR_RESUME
def test_cursor_resume_una_segunda_corrida_no_reprocesa(estado_aislado):
    """Reiniciar reanuda desde el checkpoint, no desde cero.

    Este es el test que separa un consumidor de un sondeo: el proceso muere
    entre corridas y aun así no vuelve a aplicar lo que ya confirmó.
    """
    eventos = [_evento(1, serie="a", event_time="2026-01-01T00:00:00+00:00"),
               _evento(2, serie="b", event_time="2026-01-02T00:00:00+00:00"),
               _evento(3, serie="c", event_time="2026-01-03T00:00:00+00:00")]

    c1 = ClienteFalso(eventos)
    r1 = _consumir(c1, estado_aislado)
    assert r1["events_applied"] == 3
    assert r1["cursor_before"] == 0 and r1["cursor_after"] == 3
    assert c1.acks == [1, 2, 3]

    # Segundo arranque: cliente nuevo, proceso nuevo, mismo estado en disco.
    c2 = ClienteFalso(eventos)
    r2 = _consumir(c2, estado_aislado)
    assert r2["cursor_before"] == 3, "el cursor no sobrevivió al reinicio"
    assert r2["events_applied"] == 0
    assert c2.entregas == 0, "la plataforma volvió a entregar lo ya confirmado"

    # Y lo nuevo sí entra.
    c3 = ClienteFalso(eventos + [_evento(4, serie="d",
                                         event_time="2026-01-04T00:00:00+00:00")])
    r3 = _consumir(c3, estado_aislado)
    assert r3["events_applied"] == 1 and r3["cursor_after"] == 4


def test_cursor_resume_no_avanza_mas_alla_de_lo_aplicado(estado_aislado, monkeypatch):
    """Si el handler revienta, el cursor se queda: lo no aplicado se reentrega."""
    eventos = [_evento(i, serie=f"s{i}",
                       event_time=f"2026-01-0{i}T00:00:00+00:00") for i in (1, 2, 3)]
    cliente = ClienteFalso(eventos)

    original = kdp_events.ConsumerState.mark_applied
    llamadas = {"n": 0}

    def explota(self, pkey, etime):
        llamadas["n"] += 1
        if llamadas["n"] == 3:
            raise RuntimeError("fallo aplicando el tercero")
        return original(self, pkey, etime)

    monkeypatch.setattr(kdp_events.ConsumerState, "mark_applied", explota)
    informe = _consumir(cliente, estado_aislado)
    assert informe["degraded_reason"], "un fallo del handler tiene que verse"
    assert max(cliente.acks, default=0) < 3, "se confirmó un evento no aplicado"


# ═════════════════════════════════════════════════════════════ DUPLICATE_EVENT
def test_duplicate_event_el_mismo_event_id_dos_veces_es_un_solo_efecto(estado_aislado):
    """La entrega es at-least-once: el repetido va a llegar, y no puede contar dos veces."""
    eid = "11111111-2222-3333-4444-555555555555"
    e1 = _evento(1, serie="s", valor=4.93, event_id=eid,
                 event_time="2026-07-31T00:00:00+00:00")
    # Misma identidad, otro seq y OTRO valor: si se aplicara, el estado cambiaría.
    e2 = dict(e1, seq=2, data=dict(e1["data"], value=99.0))

    informe = _consumir(ClienteFalso([e1, e2]), estado_aislado)
    assert informe["events_applied"] == 1
    assert informe["events_duplicate"] == 1

    estado = kdp_events.ConsumerState(kdp_events.state_dir() / "consumer_state.json")
    assert estado.series_latest["s"]["value"] == 4.93, "el duplicado movió el estado"


def test_duplicate_event_sobrevive_al_reinicio(estado_aislado):
    """El descarte por event_id tiene que persistir, no vivir sólo en memoria.

    El consumidor arranca y muere en cada tick del beat. Si la ventana de
    `event_id` fuera sólo de proceso, un replay tras el reinicio volvería a
    aplicar lo aplicado — y el cursor no lo impediría, porque un replay es
    justamente la reentrega de seq ya vistos.
    """
    eid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    primero = _evento(1, serie="s", valor=4.93, event_id=eid,
                      event_time="2026-07-31T00:00:00+00:00")
    _consumir(ClienteFalso([primero]), estado_aislado)

    # Replay: mismo event_id, seq mayor (el cursor no lo filtra), valor distinto.
    replay = dict(primero, seq=7, data=dict(primero["data"], value=99.0))
    informe = _consumir(ClienteFalso([primero, replay]), estado_aislado)
    assert informe["events_applied"] == 0
    assert informe["events_duplicate"] == 1

    estado = kdp_events.ConsumerState(kdp_events.state_dir() / "consumer_state.json")
    assert estado.series_latest["s"]["value"] == 4.93


# ══════════════════════════════════════════════════════════ OUT_OF_ORDER_EVENT
def test_out_of_order_event_no_retrocede_el_estado(estado_aislado):
    """Un `event_time` anterior al último aplicado de esa serie no se aplica encima."""
    nuevo = _evento(1, serie="bcb.x", valor=4.93,
                    event_time="2026-07-31T00:00:00+00:00")
    viejo = _evento(2, serie="bcb.x", valor=1.11,
                    event_time="2024-01-31T00:00:00+00:00")

    informe = _consumir(ClienteFalso([nuevo, viejo]), estado_aislado)
    assert informe["events_applied"] == 1
    assert informe["events_out_of_order"] == 1

    estado = kdp_events.ConsumerState(kdp_events.state_dir() / "consumer_state.json")
    assert estado.series_latest["bcb.x"]["value"] == 4.93
    # Y el cursor SÍ avanzó: el evento se descartó, no se perdió ni se reintenta.
    assert informe["cursor_after"] == 2


def test_out_of_order_event_es_por_particion_no_global(estado_aislado):
    """El orden se respeta DENTRO de una serie; entre series el desorden es normal.

    `findempro_sector_bo` mezcla series anuales del World Bank con semanales del
    BCB en un mismo cursor. Si el guardia fuera global, la primera serie anual
    bloquearía todo lo demás.
    """
    eventos = [
        _evento(1, serie="bcb.semanal", valor=4.93,
                event_time="2026-07-31T00:00:00+00:00"),
        _evento(2, serie="wb.anual", valor=7.7,
                event_time="2025-12-31T00:00:00+00:00"),   # anterior, otra serie
    ]
    informe = _consumir(ClienteFalso(eventos), estado_aislado)
    assert informe["events_applied"] == 2
    assert informe["events_out_of_order"] == 0


# ══════════════════════════════════════════════════════════════════ RECONNECT
def test_reconnect_un_corte_no_pierde_ni_reprocesa(estado_aislado):
    """Un corte a mitad de camino se reintenta con backoff y reanuda por cursor."""
    eventos = [_evento(i, serie=f"s{i}", event_time=f"2026-01-0{i}T00:00:00+00:00")
               for i in (1, 2, 3)]
    cliente = ClienteFalso(eventos, fallos_get=2)   # dos cortes antes de responder

    informe = _consumir(cliente, estado_aislado)
    assert informe["events_applied"] == 3
    assert informe["cursor_after"] == 3
    assert cliente.acks == [1, 2, 3]


def test_reconnect_se_rinde_y_degrada_en_vez_de_caerse(estado_aislado):
    """Si el corte no se acaba, el producto NO se cae con la plataforma: degrada."""
    cliente = ClienteFalso([_evento(1)], fallos_get=99)
    informe = _consumir(cliente, estado_aislado)
    assert informe["kdp_available"] is False
    assert "ConnectionError" in informe["degraded_reason"]
    assert informe["events_applied"] == 0


@requiere_api_real
def test_reconnect_contra_api_real(estado_aislado):
    """Contra la API de DEV: drenar, cortar, volver y no repetir ni perder.

    El corte se simula tirando la sesión HTTP entre dos drenados, que es lo que
    de verdad pasa cuando un proxy cierra o se despliega algo por debajo.
    """
    from kdp_consumer import KdpClient

    cli = KdpClient(base_url=KDP_URL, token=KDP_TOKEN)
    r1 = kdp_events.consume(client=cli, write=False, apply_point_reads=False)
    assert r1["kdp_available"] is True
    assert r1["events_applied"] > 0, "el dataset de DEV tenía que traer algo pendiente"
    cursor = r1["cursor_after"]

    cli.session.close()                     # el corte
    cli2 = KdpClient(base_url=KDP_URL, token=KDP_TOKEN)
    r2 = kdp_events.consume(client=cli2, write=False, apply_point_reads=False)
    assert r2["cursor_before"] == cursor, "no se reanudó desde el checkpoint"
    assert r2["cursor_after"] >= cursor, "el cursor retrocedió"
    assert r2["events_duplicate"] == 0, "reprocesó lo que ya había confirmado"


# ═══════════════════════════════════════════════════════════ STALE_DETECTION
def test_stale_detection_un_dato_viejo_se_marca_viejo(estado_aislado, settings):
    """Con `on_stale=WARN` el valor se conserva, pero deja de decir OBSERVED_REAL."""
    settings.KDP_MAX_AGE_S = 3600           # una hora, para forzar el caso
    viejo = (datetime.now(timezone.utc) - timedelta(days=400)).isoformat()
    eventos = [_evento(1, serie="bcb.inflacion_total_variacion_a_doce_meses",
                       valor=4.93, event_time=viejo)]

    informe = _consumir(ClienteFalso(eventos), estado_aislado)
    meta = informe["market_data"]["meta"]

    assert informe["market_data"]["macro"]["inflation_annual_pct"] == 4.93
    assert meta["provenance"]["inflation_annual_pct"] == prov.STALE
    assert meta["freshness"]["inflation_annual_pct"]["freshness_status"] == "STALE"
    assert meta["freshness"]["inflation_annual_pct"]["age_seconds"] > 3600
    assert not prov.is_observation(meta["provenance"]["inflation_annual_pct"])


def test_stale_detection_dentro_del_sla_es_observacion(estado_aislado, settings):
    """Y cuando NO es viejo, tiene que poder decirlo: la etiqueta discrimina."""
    settings.KDP_MAX_AGE_S = 63072000       # la política real: dos años
    reciente = (datetime.now(timezone.utc) - timedelta(days=20)).isoformat()
    eventos = [_evento(1, serie="bcb.inflacion_total_variacion_a_doce_meses",
                       valor=4.93, event_time=reciente)]

    informe = _consumir(ClienteFalso(eventos), estado_aislado)
    meta = informe["market_data"]["meta"]
    assert meta["provenance"]["inflation_annual_pct"] == prov.OBSERVED_REAL
    assert prov.is_observation(meta["provenance"]["inflation_annual_pct"])


def test_stale_detection_llega_hasta_la_api(client, django_user_model,
                                            estado_aislado, monkeypatch):
    """El estado y el `data_timestamp` tienen que salir por la API (§4.6)."""
    destino = estado_aislado / "market.json"
    monkeypatch.setattr(kdp_events, "MARKET_DATA_PATH", destino)
    viejo = (datetime.now(timezone.utc) - timedelta(days=400)).isoformat()
    _consumir(ClienteFalso([_evento(1, serie="bcb.inflacion_total_variacion_a_doce_meses",
                                    valor=4.93, event_time=viejo)]),
              estado_aislado, path=destino)

    usuario = django_user_model.objects.create_user(username="u1", password="x" * 12)
    client.force_login(usuario)
    resp = client.get("/business/api/market-context/")
    assert resp.status_code == 200
    cuerpo = resp.json()
    assert cuerpo["freshness_status"] in prov.FRESHNESS
    assert cuerpo["anchors"]["inflation_annual_pct"]["data_timestamp"]
    assert cuerpo["anchors"]["inflation_annual_pct"]["provenance"]
    # Lo que la API deja consumir como medición nunca incluye un curado.
    for clave in cuerpo["observations"]:
        assert cuerpo["anchors"][clave]["is_observation"] is True


# ══════════════════════════ PROCEDENCIA — la regla que no se negocia (§5)
def test_un_fallback_nunca_se_puede_leer_como_observacion(estado_aislado):
    """El test que justifica todo lo demás.

    Findempro cae al valor curado cuando KDP no responde — su política lo
    permite (`allow_lkg=true`). Lo que no se permite es que ese valor vuelva a
    salir indistinguible de una medición. Aquí se comprueba en las dos
    direcciones: por lo que el JSON dice, y por lo que el lector devuelve.
    """
    # KDP caído del todo, y sin lecturas puntuales: todo tiene que ser curado.
    destino = estado_aislado / "market.json"
    informe = kdp_events.consume(client=ClienteFalso([], fallos_get=99),
                                 apply_point_reads=False, path=destino)
    datos = json.loads(destino.read_text(encoding="utf-8"))
    meta = datos["meta"]

    for clave, valor in datos["macro"].items():
        etiqueta = meta["provenance"][clave]
        assert etiqueta == prov.FALLBACK, f"{clave} salió como {etiqueta}"
        assert meta["sources"][clave] == "fallback-curado"
        assert not prov.is_observation(etiqueta)

    assert meta["freshness_status"] == prov.SOURCE_DOWN
    assert informe["degraded_reason"], "degradó sin decir por qué"

    # Y el lector: pedir "sólo mediciones" no puede devolver ni una.
    ctx = kdp_events.load_market_context(destino)
    for clave in datos["macro"]:
        assert prov.observed_value(ctx, clave) is None, (
            f"{clave} se pudo leer como observación siendo un curado")
        assert prov.describe(ctx, clave)["is_observation"] is False


def test_una_clave_sin_etiqueta_se_trata_como_curado(estado_aislado):
    """El fallo seguro es negar: sin procedencia, no es una medición.

    Un JSON viejo —o escrito por una versión anterior— no lleva `provenance`. Si
    la ausencia se interpretara como "observado", bastaría con un fichero de
    antes de esta migración para que el peg de 2011 volviera a entrar como dato.
    """
    ctx = {"fx_usd_bob_official": 6.96}      # sin `provenance`
    assert prov.provenance_of(ctx, "fx_usd_bob_official") == prov.FALLBACK
    assert prov.observed_value(ctx, "fx_usd_bob_official") is None


def test_el_curado_y_la_observacion_conviven_sin_mezclarse(estado_aislado):
    """Caso realista: la inflación llega por evento, el resto sigue curado."""
    destino = estado_aislado / "market.json"
    reciente = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    kdp_events.consume(
        client=ClienteFalso([_evento(1, serie="bcb.inflacion_total_variacion_a_doce_meses",
                                     valor=4.93, event_time=reciente)]),
        apply_point_reads=False, path=destino)

    ctx = kdp_events.load_market_context(destino)
    assert prov.observed_value(ctx, "inflation_annual_pct") == 4.93
    # El salario mínimo es un decreto: KDP no lo publica y nunca es observación.
    assert prov.observed_value(ctx, "min_wage_month_bs") is None
    assert prov.provenance_of(ctx, "min_wage_month_bs") == prov.FALLBACK


def test_market_context_de_bolivia_industries_lleva_la_etiqueta(estado_aislado):
    """La etiqueta tiene que sobrevivir el salto del JSON a MARKET_CONTEXT.

    Es el punto donde se rompía: el overlay copiaba los cuatro números y dejaba
    la procedencia dentro del fichero, así que tres capas más arriba el peg
    curado y una medición del BCB eran el mismo `float`.
    """
    destino = estado_aislado / "market.json"
    reciente = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    kdp_events.consume(
        client=ClienteFalso([_evento(1, serie="bcb.inflacion_total_variacion_a_doce_meses",
                                     valor=4.93, event_time=reciente)]),
        apply_point_reads=False, path=destino)

    from business.data import bolivia_industries as bi

    bi._overlay_scraped_context(destino)
    assert bi.MARKET_CONTEXT["inflation_annual_pct"] == 4.93
    assert bi.MARKET_CONTEXT["provenance"]["inflation_annual_pct"] == prov.OBSERVED_REAL
    assert bi.MARKET_CONTEXT["provenance"]["fx_usd_bob_official"] == prov.FALLBACK
    assert bi.MARKET_CONTEXT["freshness_status"] in prov.FRESHNESS


def test_la_schema_version_sobrevive_una_corrida_sin_eventos(estado_aislado):
    """Una corrida vacía no puede borrar contra qué esquema se está trabajando.

    El beat corre cada 10 minutos y este dataset se mueve una vez por semana:
    casi todas las corridas son vacías. Si la versión se recalculara sólo desde
    los eventos del momento, el JSON publicaría `null` la mayor parte del tiempo.
    """
    reciente = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    _consumir(ClienteFalso([_evento(1, serie="s", event_time=reciente,
                                    schema="1.0.0")]), estado_aislado)
    vacia = _consumir(ClienteFalso([]), estado_aislado)
    assert vacia["events_applied"] == 0
    assert vacia["market_data"]["meta"]["kdp"]["schema_version"] == "1.0.0"


def test_un_curado_permanente_no_deja_el_semaforo_en_ambar(estado_aislado, settings):
    """El salario mínimo es un decreto: KDP no lo publica ni lo va a publicar.

    Contarlo en el agregado dejaría `freshness_status` en DEGRADED para siempre,
    y un semáforo que está siempre en ámbar deja de mirarse. Su etiqueta
    individual sigue siendo FALLBACK: no se esconde, se saca del promedio.
    """
    settings.KDP_MAX_AGE_S = 63072000
    reciente = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    informe = _consumir(
        ClienteFalso([_evento(1, serie="bcb.inflacion_total_variacion_a_doce_meses",
                              valor=4.93, event_time=reciente)]),
        estado_aislado)
    meta = informe["market_data"]["meta"]
    assert meta["provenance"]["min_wage_month_bs"] == prov.FALLBACK
    assert meta["freshness"]["min_wage_month_bs"]["permanent_fallback"] is True
    # Las lecturas puntuales están apagadas, así que el oficial y el paralelo
    # sí degradan y el agregado lo refleja — pero por ellos, no por el decreto.
    assert meta["freshness_status"] == prov.SOURCE_DOWN
    assert prov.observed_value(
        kdp_events.load_market_context(estado_aislado / "market.json"),
        "min_wage_month_bs") is None


# ══════════════════════════════════════════════════ programación sin humanos
def test_la_tarea_esta_registrada_y_programada(settings):
    """Nadie tiene que teclear nada: el beat la dispara.

    Si esta entrada desapareciera, Findempro volvería a la situación que motivó
    la migración —refresco sólo cuando alguien se acuerda— y nada más fallaría.
    """
    from business.tasks import consume_kdp_events

    assert consume_kdp_events.name == "business.consume_kdp_events"
    entrada = settings.CELERY_BEAT_SCHEDULE["business.consume-kdp-events"]
    assert entrada["task"] == "business.consume_kdp_events"
    assert 0 < float(entrada["schedule"]) <= 3600
