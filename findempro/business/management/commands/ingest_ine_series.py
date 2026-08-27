"""
manage.py ingest_ine_series
===========================
Consolida los **perfiles estacionales mensuales por sector** (forma real de la
demanda por rubro boliviano) en ``business/data/bolivia_sector_series.json``,
que la calibración del generador de demanda usa para dar estacionalidad real a
las simulaciones (en vez de ruido gaussiano plano).

Clasificación frente a KDP (contrato de migración §4.7)
------------------------------------------------------
Esto es una ingesta entera y paralela a la plataforma, así que hay que decir qué
pasa con cada trozo:

· Perfiles estacionales por sector (`BUSINESS_TYPE_SEASONALITY`) → **UNRELATED**.
  Son un núcleo curado del producto (Alasitas, Carnaval, aguinaldo, cosecha
  altiplánica). KDP no publica estacionalidad sectorial boliviana y no está en
  su registro de fuentes: no hay nada que migrar.
· IPC por WP REST del INE (`_fetch_ipc_wp`) → **RETAINED_FOR_RECONCILIATION**.
  KDP sí ingiere `ine-bo-wp` (`registry/sources.yaml`), pero su colector
  (`kdp/collectors/ine.py`) publica **una sola serie**:
  `ine.publicaciones.count`, el número de publicaciones por mes. Dice
  explícitamente que no inventa series numéricas que no ha parseado, y la nota
  del IPC —con su variación mensual, interanual, acumulada y **por ciudad**— no
  la parsea nadie. La desagregación regional no existe en la plataforma, así que
  borrar esto perdería un dato que KDP no tiene. Cuando KDP publique el IPC del
  INE, este camino pasa a REMOVED_AS_PRIMARY_PATH.
· Ping de alcanzabilidad al BCB (`_refresh_live`) → **REMOVED_AS_PRIMARY_PATH**.
  Comprobar si bcb.gob.bo responde es duplicar el trabajo del colector de KDP y
  no aporta ningún dato; queda como señal informativa en `meta`, nunca como vía
  de frescura.

El contexto macro (oficial, paralelo, inflación) **no** se toma de aquí: lo
refresca la tarea Celery `business.consume_kdp_events`.

Fuentes:
  · INE (ine.gob.bo) — IPC (variación mensual/interanual), señal de actividad.
  · BCB (bcb.gob.bo) — tipo de cambio (contexto macro).
El refresco en vivo es **best-effort**: los perfiles por sector
(``business.data.bolivia_sector_series.BUSINESS_TYPE_SEASONALITY``, anclados a la
estacionalidad económica boliviana documentada) se conservan siempre como núcleo
curado; lo que INE aporta en vivo es una señal de frescura/contexto que se anota
en ``meta``. Así el pipeline nunca se rompe por un sitio caído o un cambio de HTML.

Ejemplos:
    python manage.py ingest_ine_series             # refresca y escribe el JSON
    python manage.py ingest_ine_series --dry-run    # muestra sin escribir
    python manage.py ingest_ine_series --offline     # sólo curado, sin red
    python manage.py ingest_ine_series --timeout 20
"""
import json
import logging
import re
from pathlib import Path

from django.core.management.base import BaseCommand

from business.data.bolivia_sector_series import (
    BUSINESS_TYPE_SEASONALITY, month_labels, peak_months,
)

logger = logging.getLogger(__name__)

OUTPUT_PATH = Path(__file__).resolve().parents[2] / "data" / "bolivia_sector_series.json"

INE_URL = "https://www.ine.gob.bo/"
# WP REST API del INE (WordPress): fuente estable para las notas de prensa del IPC.
INE_WP_POSTS = "https://www.ine.gob.bo/index.php/wp-json/wp/v2/posts"
BCB_URL = "https://www.bcb.gob.bo/"

# Etiquetas de BusinessType (para legibilidad del JSON).
TYPE_NAMES = {
    1: "Lácteos", 2: "Agricultura", 3: "Bienes de Consumo", 4: "Panadería",
    5: "Carnicería", 6: "Verdulería/Minimarket", 7: "Otros",
    8: "Manufactura Alimentaria", 9: "Manufactura General", 10: "Retail/Comercio",
    11: "Mayorista", 12: "Servicios Generales", 13: "Salud", 14: "Educación",
    15: "Logística/Transporte", 16: "Hotelería/Restaurantes", 17: "Tecnología/Software",
    18: "Construcción", 19: "Servicios Financieros",
}


class Command(BaseCommand):
    help = ("Consolida perfiles estacionales por sector (INE/BCB best-effort) a "
            "bolivia_sector_series.json para calibrar la demanda simulada.")

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="No escribe el archivo.")
        parser.add_argument("--offline", action="store_true", help="No intenta la red; sólo curado.")
        parser.add_argument("--timeout", type=int, default=15, help="Timeout HTTP en segundos.")

    def handle(self, *args, **opts):
        timeout = opts["timeout"]
        live = {"ine_reachable": False, "bcb_reachable": False, "ipc": None}

        if not opts["offline"]:
            self._refresh_live(timeout, live)

        # Perfiles por sector (núcleo curado, siempre presente).
        sectors = {}
        for bt, factors in sorted(BUSINESS_TYPE_SEASONALITY.items()):
            sectors[str(bt)] = {
                "name": TYPE_NAMES.get(bt, f"tipo {bt}"),
                "monthly_factors": factors,           # Ene..Dic, media 1.0
                "peak_months": peak_months(bt),
            }

        payload = {
            "months": month_labels(),
            "sectors": sectors,
            "live_signal": live,
            "meta": {
                "generated_by": "manage.py ingest_ine_series",
                "profiles_source": "curado (estacionalidad económica boliviana, anclada a INE)",
                "note": ("perfiles curados como núcleo; INE/BCB aportan señal de "
                         "frescura best-effort. Factores mensuales con media ≈ 1.0."),
            },
        }

        # Reporte.
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Perfiles estacionales: {len(sectors)} sectores"))
        status = (f"INE {'✓' if live['ine_reachable'] else '✗'} · "
                  f"BCB {'✓' if live['bcb_reachable'] else '✗'}")
        ipc = live.get("ipc")
        if ipc:
            status += f" · IPC {ipc['period']}: mensual {ipc['monthly_pct']}%"
            if ipc.get("annual_pct") is not None:
                status += f", interanual {ipc['annual_pct']}%"
            if ipc.get("regional"):
                status += f" · {len(ipc['regional'])} ciudades"
        self.stdout.write(f"  Señal en vivo: {status}")
        # Muestra un par de perfiles ilustrativos.
        for bt in (10, 14, 18):  # retail, educación, construcción
            s = sectors[str(bt)]
            self.stdout.write(f"  {s['name']:24} picos={s['peak_months']}")

        if opts["dry_run"]:
            self.stdout.write(self.style.WARNING("--dry-run: no se escribió el archivo."))
            self.stdout.write(json.dumps(payload, indent=2, ensure_ascii=False)[:1200] + "\n  ...")
            return

        OUTPUT_PATH.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Escrito: {OUTPUT_PATH}"))

    # ── refresco en vivo best-effort ─────────────────────────────────────────
    def _fetch(self, url, timeout):
        import requests
        headers = {"User-Agent": "Mozilla/5.0 (FindemproAI sector series collector)"}
        resp = requests.get(url, headers=headers, timeout=timeout, verify=False)
        resp.raise_for_status()
        return resp.text

    def _refresh_live(self, timeout, live):
        # BCB alcanzable.
        try:
            self._fetch(BCB_URL, timeout)
            live["bcb_reachable"] = True
        except Exception as exc:  # noqa: BLE001
            logger.warning("BCB no alcanzable: %s", exc)

        # INE: nota de prensa mensual del IPC vía WP REST (fuente estable).
        try:
            live["ipc"] = self._fetch_ipc_wp(timeout)
            live["ine_reachable"] = True
        except Exception as exc:  # noqa: BLE001
            logger.warning("IPC vía WP REST no disponible: %s", exc)

    def _fetch_ipc_wp(self, timeout):
        """
        Trae la última nota de prensa del IPC (WordPress REST API del INE) y
        extrae variación mensual, interanual, acumulada y variación por ciudad.

        Es la fuente fiable: el número por división vive en gráficos amCharts /
        Excel (JS, no parseable); la nota mensual sí trae los niveles y regiones
        en HTML legible. Devuelve None si no hay una nota de IPC reciente.
        """
        import json as _json
        import requests

        headers = {"User-Agent": "Mozilla/5.0 (FindemproAI IPC collector)"}
        params = {"search": "índice de precios al consumidor", "per_page": 10,
                  "_fields": "id,date,slug,title,link"}
        r = requests.get(INE_WP_POSTS, params=params, headers=headers,
                         timeout=timeout, verify=False)
        r.raise_for_status()
        posts = r.json()

        # Elegir la nota de IPC (excluye IPM, IPP, "Precios Productor/al por Mayor").
        def is_ipc(p):
            t = re.sub(r"<[^>]+>", "", p["title"]["rendered"]).lower()
            return ("índice de precios al consumidor" in t and "variaci" in t
                    and "por mayor" not in t and "productor" not in t)

        cands = sorted((p for p in posts if is_ipc(p)),
                       key=lambda p: p["date"], reverse=True)
        if not cands:
            return None
        post = cands[0]

        # Contenido de la nota.
        rc = requests.get(INE_WP_POSTS, params={"slug": post["slug"], "_fields": "content"},
                          headers=headers, timeout=timeout, verify=False)
        rc.raise_for_status()
        content = rc.json()
        html = content[0]["content"]["rendered"] if content else ""
        title = re.sub(r"<[^>]+>", "", post["title"]["rendered"])
        return self._parse_ipc_note(title, html, post["date"][:10], post["link"])

    @classmethod
    def _parse_ipc_note(cls, title, html, date, link):
        """
        Parsea una nota de prensa del IPC (título + HTML) a niveles estructurados.
        Puro (sin red) → testeable con un fixture del artículo real.
        """
        text = re.sub(r"\[[^\]]+\]", " ", html)      # quita shortcodes [vc_...]
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return {
            "period": cls._extract_period(title, text),
            "date": date,
            "monthly_pct": cls._pct(text, r"variaci[oó]n mensual[^%]{0,40}?", lo=-6, hi=8)
                           or cls._pct(title, r"variaci[oó]n\s+\w+\s+de\s+", lo=-6, hi=8),
            "annual_pct": cls._pct(text, r"(?:a doce meses|a 12 meses|interanual)[^%]{0,40}?",
                                   lo=0, hi=60),
            "accumulated_pct": cls._pct(text, r"acumulad[ao][^%]{0,60}?", lo=-5, hi=60),
            "regional": cls._extract_regional(text),
            "post": link,
            "source": "ine-wp-rest",
        }

    @staticmethod
    def _pct(text, ctx, *, lo, hi):
        """Extrae el % que sigue a un contexto textual; None si no es plausible."""
        m = re.search(ctx + r"(-?\d{1,2}[.,]\d{1,2})\s*%", text, re.IGNORECASE)
        if not m:
            return None
        try:
            val = float(m.group(1).replace(",", "."))
        except ValueError:
            return None
        return round(val, 2) if lo <= val <= hi else None

    @staticmethod
    def _extract_period(title, text):
        m = re.search(r"en\s+(\w+\s+de\s+20\d{2})", title, re.IGNORECASE) or \
            re.search(r"en\s+(\w+\s+de\s+20\d{2})", text, re.IGNORECASE)
        return m.group(1).lower() if m else None

    @staticmethod
    def _extract_regional(text):
        """Variación por ciudad (p.ej. 'Oruro 3,86%')."""
        m = re.search(r"mayores variaciones.{0,600}", text, re.IGNORECASE)
        window = m.group(0) if m else text
        out = {}
        for city, val in re.findall(
                r"([A-ZÁÉÍÓÚ][\wáéíóúñ ]{2,28}?)\s+(-?\d{1,2}[.,]\d{1,2})\s*%?", window):
            city = city.strip()
            try:
                v = float(val.replace(",", "."))
            except ValueError:
                continue
            if 0 <= v <= 30 and 3 <= len(city) <= 28:
                out[city] = round(v, 2)
        return out or None
