"""
manage.py scrape_bolivia_data
=============================
Recolecta datos reales del mercado boliviano por web scraping y los consolida en
``business/data/bolivia_market_data.json``, que el sembrado (``seed_bolivia``)
usa para anclar precios y variables macro.

Fuentes:
  · BCB  (bcb.gob.bo) — tipo de cambio oficial USD/BOB.
  · INE  (ine.gob.bo) — inflación / IPC.
El scraping es **best-effort**: si una fuente no responde o cambia su HTML, se
conserva el valor curado de referencia (``MARKET_CONTEXT``) y se marca la fuente
como ``fallback``. Así el pipeline nunca se rompe por un sitio caído.

Ejemplos:
    python manage.py scrape_bolivia_data            # scrapea y escribe el JSON
    python manage.py scrape_bolivia_data --dry-run  # muestra sin escribir
    python manage.py scrape_bolivia_data --timeout 20
"""
import json
import logging
import re
from pathlib import Path

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

OUTPUT_PATH = Path(__file__).resolve().parents[2] / "data" / "bolivia_market_data.json"

BCB_URL = "https://www.bcb.gob.bo/"
BCB_TC_URL = "https://www.bcb.gob.bo/?q=cotizaciones_tc"
INE_URL = "https://www.ine.gob.bo/"

# Anclas curadas (fuente: INE/BCB/prensa 2024-2025) usadas como fallback.
CURATED = {
    "min_wage_month_bs": 2750.0,
    "inflation_annual_pct": 10.0,
    "fx_usd_bob_official": 6.96,
    "fx_usd_bob_parallel": 13.0,
}

# Precios minoristas ancla por producto (Bs) — refrescables manualmente o por
# ampliaciones futuras del scraper. Reflejan cifras de mercado 2025.
CURATED_PRICES = {
    "leche_litro": 7.50, "queso_kg": 42.0, "yogur_litro": 17.0,
    "pan_unidad": 0.60, "empanada_unidad": 6.0,
    "carne_res_kg": 60.0, "pollo_kg": 25.0,
    "papa_kg": 4.30, "tomate_kg": 5.20, "arroz_kg": 13.0, "azucar_kg": 7.50,
    "almuerzo": 16.0, "consulta_medica": 150.0,
    "cemento_bolsa": 60.0, "ladrillo_unidad": 1.40,
    "pasaje_urbano": 2.30, "colegio_privado_mes": 900.0, "curso": 200.0,
}


class Command(BaseCommand):
    help = "Scrapea datos macro/precios de Bolivia (BCB/INE) a bolivia_market_data.json."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="No escribe el archivo.")
        parser.add_argument("--timeout", type=int, default=15, help="Timeout HTTP en segundos.")

    def handle(self, *args, **opts):
        timeout = opts["timeout"]
        sources = {}
        macro = dict(CURATED)

        # 1) Tipo de cambio oficial (BCB).
        fx, fx_src = self._scrape_fx(timeout)
        if fx is not None:
            macro["fx_usd_bob_official"] = fx
        sources["fx_usd_bob_official"] = fx_src

        # 1b) Paralelo (libro P2P observado vía KDP). El valor curado de 13,0
        # quedó de 2025; el libro real se mueve todas las semanas.
        try:
            from business import kdp_source
            par, par_src = kdp_source.fetch_paralelo()
            macro["fx_usd_bob_parallel"] = par
            sources["fx_usd_bob_parallel"] = par_src
        except Exception as exc:  # noqa: BLE001
            logger.warning("KDP no dio el paralelo (%s) — se conserva el curado", exc)
            sources["fx_usd_bob_parallel"] = "fallback-curado"

        # 2) Inflación (INE).
        infl, infl_src, ipc = self._scrape_inflation(timeout)
        if infl is not None:
            macro["inflation_annual_pct"] = infl
        sources["inflation_annual_pct"] = infl_src

        payload = {
            "macro": macro,
            "prices_bs": CURATED_PRICES,
            "meta": {
                "sources": sources,
                "generated_by": "manage.py scrape_bolivia_data",
                "note": "best-effort scraping con fallback curado (INE/BCB/prensa 2024-2025)",
            },
        }
        if ipc:
            payload["meta"]["ipc"] = ipc

        self.stdout.write(self.style.MIGRATE_HEADING("Datos macro recolectados:"))
        for k, v in macro.items():
            src = sources.get(k, "curado")
            self.stdout.write(f"  {k:26} = {v:<10} [{src}]")

        if opts["dry_run"]:
            self.stdout.write(self.style.WARNING("--dry-run: no se escribió el archivo."))
            self.stdout.write(json.dumps(payload, indent=2, ensure_ascii=False))
            return

        OUTPUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Escrito: {OUTPUT_PATH}"))

    # ── scrapers best-effort ─────────────────────────────────────────────────
    def _fetch(self, url, timeout):
        import requests
        headers = {"User-Agent": "Mozilla/5.0 (FindemproAI market data collector)"}
        resp = requests.get(url, headers=headers, timeout=timeout, verify=False)
        resp.raise_for_status()
        return resp.text

    def _scrape_fx(self, timeout):
        """Tipo de cambio oficial Bs/USD.

        Orden: KDP (observado) → scraping del BCB → valor curado.

        El scraping de abajo sólo acepta 6,5–7,5 porque se escribió cuando
        Bolivia sostenía Bs 6,96. Con el oficial en 11,50 ese filtro descarta el
        valor real, así que dejó de poder observar nada: por eso KDP va primero.
        """
        try:
            from business import kdp_source
            return kdp_source.fetch_fx_oficial()
        except Exception as exc:  # noqa: BLE001
            logger.warning("KDP no dio el oficial (%s) — se intenta el scraping", exc)

        for url in (BCB_TC_URL, BCB_URL):
            try:
                html = self._fetch(url, timeout)
                # Busca patrones tipo "6,96" cercanos a 'dólar'/'venta'.
                candidates = re.findall(r"\b(6[.,]9\d)\b", html)
                for c in candidates:
                    val = float(c.replace(",", "."))
                    if 6.5 <= val <= 7.5:
                        return round(val, 2), "bcb-scraped"
            except Exception as exc:  # noqa: BLE001
                logger.warning("Scrape FX falló en %s: %s", url, exc)
        return None, "fallback-curado"

    def _scrape_inflation(self, timeout):
        """Lee la inflación *interanual* real del INE; fallback al valor curado.

        Devuelve ``(valor, fuente, ipc_detalle | None)``.

        Vía preferida: la nota de prensa mensual del IPC por **WP REST API**
        (misma lógica que ``ingest_ine_series``) — trae el nivel a 12 meses de
        forma estructurada y fiable. Si no está disponible, cae al regex legacy
        sobre la home (que exige contexto anual para no confundir la variación
        mensual ~2 % con la anual) y, en última instancia, al valor curado.
        """
        # 0) KDP — serie mensual real del BCB, la única observada de las tres.
        try:
            from business import kdp_source
            val, src = kdp_source.fetch_inflacion_anual()
            return val, src, None
        except Exception as exc:  # noqa: BLE001
            logger.warning("KDP no dio la inflación (%s) — se intenta INE", exc)

        # 1) Nota de prensa mensual del IPC (WP REST) — fuente estable.
        try:
            from business.management.commands.ingest_ine_series import (
                Command as IneSeriesCommand,
            )
            ipc = IneSeriesCommand()._fetch_ipc_wp(timeout)
            if ipc and ipc.get("annual_pct") is not None:
                return ipc["annual_pct"], "ine-wp-rest", ipc
        except Exception as exc:  # noqa: BLE001
            logger.warning("IPC vía WP REST no disponible: %s", exc)

        # 2) Legacy: regex sobre la home del INE.
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
        return None, "fallback-curado", None
