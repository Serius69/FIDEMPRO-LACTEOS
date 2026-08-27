"""
manage.py consume_kdp_events
============================
Drena el cursor de KDP (dataset ``findempro_sector_bo``, modo CURSOR_STREAM) y
reescribe ``business/data/bolivia_market_data.json`` con la procedencia de cada
ancla puesta.

**Este comando NO es el camino primario.** El camino primario es la tarea de
Celery ``business.consume_kdp_events``, programada en ``CELERY_BEAT_SCHEDULE`` y
disparada por el contenedor ``findempro_celery_beat`` sin que nadie teclee nada.
Esto de aquí es la misma función por la puerta de servicio: para depurar, para
un arranque en frío, y para poder mirar el informe con los ojos.

Ejemplos:
    python manage.py consume_kdp_events
    python manage.py consume_kdp_events --dry-run     # no escribe el JSON
    python manage.py consume_kdp_events --status      # sólo dice dónde va el cursor
"""
import json

from django.core.management.base import BaseCommand

from business import kdp_events, provenance as prov


class Command(BaseCommand):
    help = ("Drena los eventos de KDP y refresca el contexto macro. El camino "
            "programado es la tarea Celery business.consume_kdp_events.")

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true",
                            help="Drena y acusa recibo, pero no escribe el JSON.")
        parser.add_argument("--status", action="store_true",
                            help="No drena: muestra el cursor y el estado guardado.")
        parser.add_argument("--json", action="store_true",
                            help="Emite el informe completo en JSON.")
        parser.add_argument("--no-point-reads", action="store_true",
                            help="Sólo eventos; no lee /v1/latest (oficial y paralelo).")

    def handle(self, *args, **opts):
        if opts["status"]:
            return self._status(opts)

        informe = kdp_events.consume(
            write=not opts["dry_run"],
            apply_point_reads=not opts["no_point_reads"],
        )

        if opts["json"]:
            self.stdout.write(json.dumps(informe, indent=2, ensure_ascii=False, default=str))
            return

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"KDP · {informe['consumer']} · {informe['dataset_id']} · {informe['mode']}"))
        self.stdout.write(
            f"  cursor {informe['cursor_before']} → {informe['cursor_after']} · "
            f"aplicados {informe['events_applied']} · "
            f"duplicados {informe['events_duplicate']} · "
            f"fuera de orden {informe['events_out_of_order']} · "
            f"lag {informe['lag_events']}")
        if informe.get("degraded_reason"):
            self.stdout.write(self.style.WARNING(
                f"  DEGRADADO: {informe['degraded_reason']}"))

        for nombre in ("kdp_to_consumer_ms", "end_to_end_ms"):
            muestras = informe.get(nombre) or []
            if muestras:
                orden = sorted(muestras)
                self.stdout.write(
                    f"  {nombre.upper():18} n={len(orden)} "
                    f"p50={orden[len(orden)//2]:.1f} max={max(orden):.1f}")

        datos = informe.get("market_data")
        if datos:
            meta = datos["meta"]
            self.stdout.write(self.style.MIGRATE_HEADING(
                f"Contexto macro [{meta['freshness_status']}]:"))
            for k, v in datos["macro"].items():
                etiqueta = meta["provenance"][k]
                marca = " " if prov.is_observation(etiqueta) else "!"
                estilo = self.style.SUCCESS if prov.is_observation(etiqueta) else self.style.WARNING
                self.stdout.write(estilo(
                    f" {marca} {k:26} = {v:<10} [{etiqueta}] {meta['sources'][k]}"))
        if opts["dry_run"]:
            self.stdout.write(self.style.WARNING("--dry-run: no se escribió el JSON."))

    def _status(self, opts):
        estado = kdp_events.ConsumerState(kdp_events.state_dir() / "consumer_state.json")
        consumidor, cp = kdp_events.build_consumer()
        self.stdout.write(f"  estado en      : {kdp_events.state_dir()}")
        self.stdout.write(f"  cursor local   : {consumidor.position()}")
        self.stdout.write(f"  último drenado : {estado.last_drain_at}")
        self.stdout.write(f"  series vistas  : {len(estado.series_latest)}")
        self.stdout.write(f"  event_id en memoria: {len(estado.seen_events)}")
        ctx = kdp_events.load_market_context()
        self.stdout.write(f"  frescura       : {ctx.get('freshness_status')}")
        for k in ("fx_usd_bob_official", "fx_usd_bob_parallel", "inflation_annual_pct",
                  "min_wage_month_bs"):
            self.stdout.write("   " + json.dumps(prov.describe(ctx, k), ensure_ascii=False))
