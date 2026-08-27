from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

DEFAULT_BASE = os.environ.get("KDP_API_URL", "http://127.0.0.1:8099")
# how far into the future an observed_at may sit before it is not a measurement
FUTURE_TOLERANCE = timedelta(days=2)


class KdpContractError(RuntimeError):
    """Base: the platform's contract does not permit this data to be consumed."""


class KdpSchemaError(KdpContractError):
    """The dataset's schema_version is incompatible with what the consumer pinned."""


class KdpStaleError(KdpContractError):
    """The dataset is older than the consumer is willing to accept."""


class KdpFallbackError(KdpContractError):
    """A fallback/estimated point reached a dataset that must contain only observations."""


class KdpRejectedDataError(KdpContractError):
    """Rows the platform marked quality='rejected' reached the consumer."""


class KdpFutureDataError(KdpContractError):
    """An observation is dated in the future — no source can observe the future."""


def _parse(ts: str | None) -> datetime | None:
    if not ts:
        return None
    d = datetime.fromisoformat(ts)
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _major(v: str) -> str:
    return v.split(".", 1)[0]


@dataclass
class Dataset:
    contract: dict
    rows: list[dict]

    @property
    def cutoff(self) -> datetime | None:
        return _parse(self.contract.get("cutoff"))

    @property
    def schema_version(self) -> str:
        return self.contract["schema_version"]

    def __len__(self) -> int:
        return len(self.rows)


class KdpAuthError(RuntimeError):
    """La plataforma rechazó las credenciales, o no había ninguna que mandar."""


class KdpClient:
    def __init__(self, base_url: str = DEFAULT_BASE, timeout: int = 60,
                 token: str | None = None):
        self.base = base_url.rstrip("/")
        self.timeout = timeout
        # El token sale del entorno del consumidor. No hay valor por defecto ni
        # modo anónimo: la API sirve datos clasificados FINANCIAL_SENSITIVE, y un
        # cliente que "funciona sin token" sólo funciona contra una plataforma
        # mal configurada. Que falle aquí es la señal de que falta configurar.
        self.token = token or os.environ.get("KDP_API_TOKEN") or None
        self.session = requests.Session()
        if self.token:
            self.session.headers["Authorization"] = f"Bearer {self.token}"

    # -------------------------------------------------------------- raw access
    def _get(self, path: str, **params):
        r = self.session.get(f"{self.base}{path}", params=params or None,
                             timeout=self.timeout)
        if r.status_code in (401, 403):
            raise KdpAuthError(
                f"{r.status_code} en {path}: "
                + ("el token no alcanza este dataset" if r.status_code == 403
                   else "falta el token o no es válido — definí KDP_API_TOKEN")
                + f". Respuesta: {r.text[:200]}")
        r.raise_for_status()
        return r.json()

    def _post(self, path: str, **params):
        r = self.session.post(f"{self.base}{path}", params=params or None,
                              timeout=self.timeout)
        if r.status_code in (401, 403):
            raise KdpAuthError(f"{r.status_code} en {path}: {r.text[:200]}")
        r.raise_for_status()
        return r.json()

    def contract(self, dataset_id: str) -> dict:
        return self._get(f"/v1/contracts/{dataset_id}")

    def forecast_cutoff(self, series_key: str | None = None) -> dict:
        return self._get("/v1/forecast-cutoff",
                         **({"series_key": series_key} if series_key else {}))

    # -------------------------------------------------------------- guarded access
    def check_contract(self, contract: dict, *, expect_schema: str | None = None,
                       max_age_s: int | None = None, allow_stale: bool = False,
                       allow_suspect: bool = True) -> None:
        """Raise unless this contract is safe for a consumer to use.

        Called on its own by tests; called automatically by `dataset()`.
        """
        ds = contract.get("dataset_id", "?")

        if expect_schema:
            want = expect_schema.replace(".x", "").split(".")[0] if "x" in expect_schema \
                else _major(expect_schema)
            got = _major(contract["schema_version"])
            if want != got:
                raise KdpSchemaError(
                    f"{ds}: consumer pinned schema {expect_schema}, platform serves "
                    f"{contract['schema_version']} — incompatible major version")

        prov = contract.get("provenance") or {}
        bad_prov = {k: v for k, v in prov.items() if k != "observed" and v}
        if bad_prov:
            raise KdpFallbackError(
                f"{ds}: non-observed provenance reached the dataset: {bad_prov}")

        qual = contract.get("quality") or {}
        if qual.get("rejected"):
            raise KdpRejectedDataError(
                f"{ds}: {qual['rejected']} rows marked quality='rejected' are present")
        if not allow_suspect and qual.get("suspect"):
            raise KdpContractError(
                f"{ds}: {qual['suspect']} suspect rows present and allow_suspect=False")

        cutoff = _parse(contract.get("cutoff"))
        if cutoff and cutoff > datetime.now(timezone.utc) + FUTURE_TOLERANCE:
            raise KdpFutureDataError(f"{ds}: cutoff {cutoff.isoformat()} is in the future")

        if contract.get("row_count", 0) == 0:
            raise KdpContractError(f"{ds}: dataset is empty")

        stale_info = contract.get("staleness") or {}
        age = stale_info.get("age_seconds")
        limit = max_age_s if max_age_s is not None else stale_info.get("sla_seconds")
        if age is not None and limit is not None and age > limit and not allow_stale:
            raise KdpStaleError(
                f"{ds}: newest point is {age}s old, limit is {limit}s. "
                f"Pass allow_stale=True to consume it knowingly.")

    def dataset(self, dataset_id: str, *, expect_schema: str | None = None,
                series: str | None = None, start: str | None = None,
                limit: int = 500_000, max_age_s: int | None = None,
                allow_stale: bool = False, allow_suspect: bool = True) -> Dataset:
        contract = self.contract(dataset_id)
        self.check_contract(contract, expect_schema=expect_schema, max_age_s=max_age_s,
                            allow_stale=allow_stale, allow_suspect=allow_suspect)
        params = {"limit": limit}
        if series:
            params["series"] = series
        if start:
            params["start"] = start
        payload = self._get(f"/v1/datasets/{dataset_id}", **params)
        rows = payload["rows"]

        # Row-level defence: the contract is a summary, the rows are the truth.
        horizon = datetime.now(timezone.utc) + FUTURE_TOLERANCE
        for r in rows:
            if r.get("quality") == "rejected":
                raise KdpRejectedDataError(
                    f"{dataset_id}: rejected row served for {r['series_key']}")
            if _parse(r["observed_at"]) > horizon:
                raise KdpFutureDataError(
                    f"{dataset_id}: future row {r['observed_at']} for {r['series_key']}")
        return Dataset(contract=contract, rows=rows)


# ====================================================================== eventos
# Lo que sigue es la mitad que convierte a un producto en consumidor de verdad:
# deja de preguntar "¿hay algo nuevo?" y pasa a que se le avise.


class Checkpoint:
    """Dónde se quedó este consumidor. Un fichero, a propósito.

    El cursor autoritativo vive en KDP, pero un consumidor que se reinicia
    necesita saber por dónde iba ANTES de poder hablar con la plataforma. Un
    fichero local es suficiente y no añade una dependencia más al arranque.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def read(self, dataset_id: str) -> int:
        try:
            return int(json.loads(self.path.read_text()).get(dataset_id, 0))
        except (OSError, ValueError, AttributeError):
            return 0

    def write(self, dataset_id: str, seq: int) -> None:
        data = {}
        try:
            data = json.loads(self.path.read_text())
        except (OSError, ValueError):
            pass
        data[dataset_id] = int(seq)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Escritura atómica: un corte a mitad de un write deja el fichero
        # truncado, y un checkpoint truncado se lee como cero — el consumidor
        # reprocesaría todo el histórico creyendo que empieza de nuevo.
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, indent=2))
        tmp.replace(self.path)


class EventConsumer:
    """Consume eventos de un dataset, con confirmación e idempotencia.

    La entrega es at-least-once, así que el consumidor VA a ver un evento
    repetido alguna vez: un reintento, un reinicio a mitad de entrega, un
    replay. `seen` descarta por `event_id` los que ya se aplicaron. Sin eso, la
    reentrega —que es correcta y necesaria— se convertiría en un efecto
    duplicado sobre dinero real.
    """

    def __init__(self, client: KdpClient, consumer: str, dataset_id: str,
                 checkpoint: Checkpoint | None = None, remember: int = 10_000):
        self.client = client
        self.consumer = consumer
        self.dataset_id = dataset_id
        self.checkpoint = checkpoint
        self.remember = remember
        self._seen: dict[str, None] = {}

    # ------------------------------------------------------------ idempotencia
    def _already_applied(self, event_id: str) -> bool:
        if event_id in self._seen:
            return True
        self._seen[event_id] = None
        if len(self._seen) > self.remember:
            # Ventana acotada: recordar para siempre es una fuga de memoria, y
            # un duplicado separado por diez mil eventos no ocurre en la
            # práctica porque el cursor no retrocede tanto sin un replay.
            for k in list(self._seen)[: len(self._seen) - self.remember]:
                del self._seen[k]
        return False

    # ------------------------------------------------------------------ cursor
    def position(self) -> int:
        if self.checkpoint:
            return self.checkpoint.read(self.dataset_id)
        return 0

    def ack(self, seq: int) -> None:
        """Confirma en la plataforma Y en el checkpoint local, en ese orden.

        Si se cayera entre los dos, el local queda atrás y se reprocesa: eso lo
        absorbe la idempotencia. Al revés —local primero— un corte dejaría a la
        plataforma creyendo que falta entregar algo que ya se aplicó, y el
        cursor autoritativo mentiría.
        """
        self.client._post("/v1/events/ack", consumer=self.consumer,
                          dataset_id=self.dataset_id, seq=seq)
        if self.checkpoint:
            self.checkpoint.write(self.dataset_id, seq)

    # -------------------------------------------------------------------- pull
    def poll(self, after_seq: int | None = None, limit: int = 200,
             stream: str = "live") -> dict:
        after = self.position() if after_seq is None else after_seq
        return self.client._get("/v1/events", dataset_id=self.dataset_id,
                                after_seq=after, limit=limit, stream=stream)

    def drain(self, handler, *, limit: int = 200, stream: str = "live") -> int:
        """Aplica todo lo pendiente. Devuelve cuántos eventos se aplicaron.

        Un fallo del handler DETIENE el avance del cursor en ese punto: el
        evento que no se pudo aplicar se volverá a entregar. Saltárselo y seguir
        sería perderlo sin que nada lo dijera.
        """
        aplicados = 0
        while True:
            lote = self.poll(limit=limit, stream=stream)
            if not lote["events"]:
                return aplicados
            for ev in lote["events"]:
                if not self._already_applied(ev["event_id"]):
                    handler(ev)
                self.ack(ev["seq"])
                aplicados += 1
            if lote["lag_events"] <= 0:
                return aplicados

    # --------------------------------------------------------------------- SSE
    def stream_events(self, after_seq: int | None = None, stream: str = "live",
                      reconnect_s: float = 2.0):
        """Generador de eventos por SSE. Reconecta solo y reanuda por cursor.

        El corte de una conexión SSE es rutina, no excepción: un proxy con
        timeout, un despliegue, una red que parpadea. Lo que no puede ser rutina
        es perder lo ocurrido durante el corte, y por eso se reanuda desde el
        último `seq` visto y no desde "ahora".
        """
        cursor = self.position() if after_seq is None else after_seq
        while True:
            try:
                r = self.client.session.get(
                    f"{self.client.base}/v1/events/stream",
                    params={"dataset_id": self.dataset_id, "after_seq": cursor,
                            "stream": stream},
                    stream=True, timeout=(10, None),
                    headers={"Accept": "text/event-stream",
                             "Last-Event-ID": str(cursor)})
                if r.status_code in (401, 403):
                    raise KdpAuthError(f"{r.status_code} en /v1/events/stream")
                r.raise_for_status()
                datos = []
                for linea in r.iter_lines(decode_unicode=True):
                    if linea is None:
                        continue
                    if linea.startswith(":"):        # latido
                        continue
                    if linea.startswith("data:"):
                        datos.append(linea[5:].strip())
                        continue
                    if linea == "" and datos:
                        ev = json.loads("".join(datos))
                        datos = []
                        cursor = ev["seq"]
                        if not self._already_applied(ev["event_id"]):
                            yield ev
            except KdpAuthError:
                raise
            except (requests.RequestException, ValueError):
                time.sleep(reconnect_s)


# ---------------------------------------------------------------- webhooks
def verify_webhook(secret: str, headers, body: bytes, *,
                   tolerance_s: int = 300) -> dict:
    """Valida una entrega de KDP y devuelve el evento. Levanta si no cuadra.

    Un consumidor que expone un webhook expone un endpoint público: sin
    verificar la firma, cualquiera puede inyectarle un precio. Y sin la ventana
    de tiempo, una entrega legítima capturada hoy se puede reenviar mañana.
    """
    import hashlib
    import hmac

    firma = headers.get("X-KDP-Signature") or headers.get("x-kdp-signature")
    ts = headers.get("X-KDP-Timestamp") or headers.get("x-kdp-timestamp")
    if not firma or not ts:
        raise KdpAuthError("entrega sin firma o sin timestamp")
    try:
        ts_i = int(ts)
    except (TypeError, ValueError):
        raise KdpAuthError("timestamp de firma inválido")
    if abs(time.time() - ts_i) > tolerance_s:
        raise KdpAuthError(f"entrega fuera de la ventana de {tolerance_s}s")
    esperado = "v1=" + hmac.new(secret.encode(), f"{ts_i}.".encode() + body,
                                hashlib.sha256).hexdigest()
    if not hmac.compare_digest(esperado, firma):
        raise KdpAuthError("firma inválida")
    return json.loads(body)
