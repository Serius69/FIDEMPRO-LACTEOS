"""
manage.py import_forex_demand
=============================
Carga el dataset REAL de operaciones de casa de cambio (export anonimizado de
forex-erp) como demanda histórica del producto **Cambio de Divisas** (tipo 19,
Servicios Financieros) — el único rubro con serie real por-negocio disponible.

Reconstruye la serie diaria por desagregación (totales mensuales reales ×
forma semanal real; ver ``business.services.forex_adapter``) y la persiste
donde el motor la lee (answers ``DH``), vía ``demand_import.write_series``.

Ejemplos:
    python manage.py import_forex_demand ops.csv                    # ops/día
    python manage.py import_forex_demand ops.csv --metric bs        # Bs/día
    python manage.py import_forex_demand ops.csv --user admin --dry-run
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from business.services import forex_adapter
from business.services.demand_import import (
    clean_series, resolve_product, sample_warnings, write_series,
)

DEFAULT_PRODUCT = "Cambio de Divisas"


class Command(BaseCommand):
    help = ("Importa las operaciones reales de casa de cambio (forex-erp) como "
            "demanda del producto 'Cambio de Divisas'.")

    def add_arguments(self, parser):
        parser.add_argument("path", help="CSV de operaciones (export forex-erp).")
        parser.add_argument("--product", default=DEFAULT_PRODUCT,
                            help=f"Producto destino (default: '{DEFAULT_PRODUCT}').")
        parser.add_argument("--business", default=None,
                            help="Nombre del negocio, para desambiguar.")
        parser.add_argument("--user", default=None,
                            help="Username dueño del negocio, para desambiguar.")
        parser.add_argument("--metric", choices=("ops", "bs"), default="ops",
                            help="Demanda = operaciones/día (ops) o volumen Bs/día (bs).")
        parser.add_argument("--include-partial", action="store_true",
                            help="No excluye los meses de borde parciales.")
        parser.add_argument("--append", action="store_true",
                            help="Antepone la serie previa en vez de reemplazarla.")
        parser.add_argument("--dry-run", action="store_true",
                            help="Muestra qué haría sin escribir.")

    def handle(self, *args, **opts):
        try:
            df = forex_adapter.load_operations(opts["path"])
        except FileNotFoundError:
            raise CommandError(f"no existe el archivo: {opts['path']}")
        except ValueError as exc:
            raise CommandError(str(exc))

        daily = forex_adapter.build_daily_series(
            df, metric=opts["metric"], include_partial=opts["include_partial"])
        series, dropped = clean_series(daily.values)

        user = None
        if opts["user"]:
            try:
                user = User.objects.get(username=opts["user"])
            except User.DoesNotExist:
                raise CommandError(f"no existe el usuario '{opts['user']}'")

        try:
            product = resolve_product(
                opts["product"], user=user, business=opts["business"])
        except LookupError as exc:
            raise CommandError(
                f"{exc} — el arquetipo se crea con: manage.py seed_bolivia")

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Operaciones forex → demanda '{product.name}' "
            f"({product.fk_business.name})"))
        self.stdout.write(
            f"  {len(df)} operaciones · {len(daily.months_used)} meses completos "
            f"({daily.months_used[0]}…{daily.months_used[-1]}) · "
            f"métrica: {daily.metric}")
        if daily.months_dropped:
            self.stdout.write(self.style.WARNING(
                f"  ⚠ meses parciales excluidos: {', '.join(daily.months_dropped)} "
                f"(usa --include-partial para conservarlos)"))
        mean = sum(series) / len(series) if series else 0
        self.stdout.write(f"  Serie diaria: {len(series)} puntos · media {mean:.1f}"
                          + (f" · {dropped} descartados" if dropped else ""))
        for warn in sample_warnings(len(series)):
            self.stdout.write(self.style.WARNING(f"  ⚠ {warn}"))

        result = write_series(product, series,
                              replace=not opts["append"], dry_run=opts["dry_run"])
        if result.status == "error":
            raise CommandError(result.message)
        if opts["dry_run"]:
            self.stdout.write(self.style.WARNING(
                "--dry-run: no se escribió nada "
                f"(se actualizarían {result.results_updated} cuestionarios, "
                f"{result.n_previous_deleted} answers previas)"))
            return
        verb = "anexada a" if opts["append"] else "reemplaza"
        self.stdout.write(self.style.SUCCESS(
            f"✓ Serie real importada: {verb} {result.n_previous_deleted} answer(s) "
            f"DH previa(s) en {result.results_updated} cuestionario(s)."))
