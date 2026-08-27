"""kdp_consumer — the client a Kapitalya product uses to read platform data safely.

It is deliberately small and dependency-light (requests only) so any product can
vendor it. Its job is to make the unsafe things impossible rather than documented:

    client = KdpClient(base_url="http://127.0.0.1:8099")   # KDP_API_TOKEN en el entorno
    ds = client.dataset("forexerp_fx_daily", expect_schema="1.x", max_age_s=36*3600)

`dataset()` raises before returning a single row if the contract says the data is
fallback-tainted, rejected, from the future, schema-incompatible, or stale.

Y para no tener que preguntar cuándo cambió algo, que es lo que dejaba a cada
producto con su propio reloj:

    ec = EventConsumer(client, "ForexERP-pricing", "p2p_market_consensus",
                       checkpoint=Checkpoint("var/kdp.checkpoint.json"))
    for ev in ec.stream_events():          # SSE: la plataforma avisa, no se encuesta
        aplicar(ev["data"])
        ec.ack(ev["seq"])

`drain()` hace lo mismo por lectura desde cursor, para un proceso que no puede
mantener una conexión abierta. `verify_webhook()` es para el que prefiere recibir.
"""
from .client import (Checkpoint, Dataset, EventConsumer, KdpAuthError, KdpClient,
                     KdpContractError, KdpFallbackError, KdpFutureDataError,
                     KdpRejectedDataError, KdpSchemaError, KdpStaleError,
                     verify_webhook)

__all__ = ["KdpClient", "Dataset", "KdpContractError", "KdpSchemaError",
           "KdpStaleError", "KdpFallbackError", "KdpRejectedDataError",
           "KdpFutureDataError", "KdpAuthError",
           "EventConsumer", "Checkpoint", "verify_webhook"]
__version__ = "2.0.0"
