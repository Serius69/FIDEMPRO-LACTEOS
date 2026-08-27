"""
manage.py scrape_bolivia_data
=============================
Refresca ``business/data/bolivia_market_data.json``, que el sembrado
(``seed_bolivia``) usa para anclar precios y variables macro.

Qué era y qué es ahora
----------------------
Era el **único** camino de frescura de Findempro, y no lo disparaba nada: sin
cron, sin entrada de beat, sin timer. El oficial, el paralelo y la inflación
tenían la frescura del último día que alguien se acordó de teclear esto.

Desde la migración a eventos (2026-08-27) el camino primario es la tarea de
Celery ``business.consume_kdp_events``, programada en ``CELERY_BEAT_SCHEDULE``.
Este comando queda como **red de seguridad declarada**: hace lo mismo (delega en
``business.kdp_events.consume``, que a su vez usa ``business.kdp_source`` para
las lecturas puntuales) y, sólo si KDP no pudo dar la inflación, intenta la nota
de prensa del INE antes de resignarse al valor curado.

Clasificación de los caminos antiguos (contrato §4.7)
-----------------------------------------------------
· ``_scrape_fx`` (regex 6,5–7,5 sobre bcb.gob.bo)  → REMOVED_AS_PRIMARY_PATH.
  Retirado del path activo el 2026-08-25 y eliminado aquí: una banda anclada al
  peg 2011-2025 no puede observar 11,50, así que no era un respaldo sino una
  ruta que sólo podía acertar bajo un régimen que ya no existe.
· IPC por WP REST del INE                          → RETAINED_AS_SAFETY_NET.
  KDP ingiere `ine-bo-wp`, pero su colector publica **sólo**
  `ine.publicaciones.count`: no parsea la nota del IPC. Mientras eso siga así,
  este camino es la única vía cuando la serie del BCB no llega.
· regex de inflación sobre la home del INE          → REMOVED_AS_PRIMARY_PATH.
  Tercer eslabón detrás de dos que ya cubren el caso; se conserva sólo detrás de
  ellos y nunca como vía de frescura.

Ejemplos:
    python manage.py scrape_bolivia_data            # refresca y escribe el JSON
    python manage.py scrape_bolivia_data --dry-run  # muestra sin escribir
"""
import logging
import re

from django.core.management.base import BaseCommand

from business import kdp_events, provenance as prov
from business.data.curated_market import (
    CURATED, CURATED_PRICES, CURATED_SOURCE,  # noqa: F401 — reexport histórico
)

logger = logging.getLogger(__name__)

OUTPUT_PATH = kdp_events.MARKET_DATA_PATH

# Home del INE: sólo la usa el regex legacy, que es el último eslabón.
INE_URL = "https://www.ine.gob.bo/"


class Command(BaseCommand):
    help = ("Red de seguridad del contexto macro. El camino programado es la "
            "tarea Celery business.consume_kdp_events.")

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="No escribe el archivo.")
        parser.add_argument("--timeout", type=int, default=15, help="Timeout HTTP en segundos.")

    def handle(self, *args, **opts):
        self.stdout.write(self.style.WARNING(
            "Este comando no es el camino primario: lo es la tarea Celery "
            "'business.consume_kdp_events' (CELERY_BEAT_SCHEDULE, cada 10 min)."))

        informe = kdp_events.consume(write=not opts["dry_run"])
        datos = informe.get("market_data") or {}
        meta = datos.get("meta", {})
        procedencia = dict(meta.get("provenance") or {})

        # Red de seguridad: sólo si la inflación acabó siendo un curado.
        if (not opts["dry_run"]
                and procedencia.get("inflation_annual_pct") == prov.FALLBACK):
            ipc = self._inflacion_desde_ine(opts["timeout"])
            if ipc:
                valor, fuente, sello = ipc
                datos = kdp_events.override_field(
                    "inflation_annual_pct", value=valor, source=fuente,
                    provenance=prov.OBSERVED_REAL, data_timestamp=sello,
                    freshness_status=prov.DEGRADED,
                    note=("red de seguridad: publicado por el INE, NO pasó por "
                          "KDP ni por sus controles de calidad"))
                meta = datos["meta"]
            else:
                logger.warning("Ni KDP ni el INE dieron la inflación — "
                               "se conserva el curado (fallback-curado)")

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Datos macro [{meta.get('freshness_status', '?')}]:"))
        for k, v in (datos.get("macro") or {}).items():
            etiqueta = (meta.get("provenance") or {}).get(k, prov.FALLBACK)
            fuente = (meta.get("sources") or {}).get(k, CURATED_SOURCE)
            estilo = (self.style.SUCCESS if prov.is_observation(etiqueta)
                      else self.style.WARNING)
            self.stdout.write(estilo(f"  {k:26} = {v:<10} [{etiqueta}] {fuente}"))

        if opts["dry_run"]:
            self.stdout.write(self.style.WARNING("--dry-run: no se escribió el archivo."))
            return
        self.stdout.write(self.style.SUCCESS(f"Escrito: {OUTPUT_PATH}"))

    # ── red de seguridad ─────────────────────────────────────────────────────
    def _fetch(self, url, timeout):
        import requests
        headers = {"User-Agent": "Mozilla/5.0 (FindemproAI market data collector)"}
        resp = requests.get(url, headers=headers, timeout=timeout, verify=False)
        resp.raise_for_status()
        return resp.text

    def _inflacion_desde_ine(self, timeout):
        """Inflación interanual del INE. Devuelve ``(valor, fuente, fecha)`` o None.

        RETAINED_AS_SAFETY_NET: sólo corre cuando KDP no pudo dar la serie del
        BCB. El número que devuelve es real —lo publica el INE— pero no pasó por
        la plataforma, así que viaja con su propia fuente (``ine-wp-rest``,
        nunca ``kdp:``) para que se pueda distinguir de una observación curada
        por KDP.
        """
        # 1) Nota de prensa mensual del IPC (WP REST) — fuente estable.
        try:
            from business.management.commands.ingest_ine_series import (
                Command as IneSeriesCommand,
            )
            ipc = IneSeriesCommand()._fetch_ipc_wp(timeout)
            if ipc and ipc.get("annual_pct") is not None:
                return ipc["annual_pct"], "ine-wp-rest", ipc.get("date")
        except Exception as exc:  # noqa: BLE001
            logger.warning("IPC vía WP REST no disponible: %s", exc)

        # 2) Legacy: regex sobre la home del INE. Exige contexto anual para no
        #    confundir la variación mensual (~2 %) con la interanual.
        annual_ctx = r"(?:acumulad|doce meses|a 12 meses|interanual|anual)"
        try:
            html = self._fetch(INE_URL, timeout)
            patterns = [
                rf"{annual_ctx}.{{0,60}}?(\d{{1,2}}[.,]\d{{1,2}})\s*%",
                rf"(\d{{1,2}}[.,]\d{{1,2}})\s*%.{{0,60}}?{annual_ctx}",
            ]
            for pat in patterns:
                m = re.search(pat, html, re.IGNORECASE | re.DOTALL)
                if m:
                    val = float(m.group(1).replace(",", "."))
                    if 3 <= val < 60:  # rango plausible para inflación anual boliviana
                        return round(val, 2), "ine-scraped", None
        except Exception as exc:  # noqa: BLE001
            logger.warning("Scrape inflación falló: %s", exc)
        return None
