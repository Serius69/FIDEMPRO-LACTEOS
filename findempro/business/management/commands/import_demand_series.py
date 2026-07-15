"""
manage.py import_demand_series
==============================
Importa series históricas de demanda **reales** (CSV/Excel) y las persiste como
la respuesta de demanda del cuestionario (``DH``) de cada producto, que es de
donde el motor de simulación toma la serie. Reemplaza la demanda sintética que
genera ``seed_bolivia``.

Formato esperado (CSV "tidy" / largo, por defecto)::

    product,date,demand
    Leche,2025-01-01,2450
    Leche,2025-01-02,2510
    Queso Fresco,2025-01-01,175
    ...

* ``product``  nombre del producto (case-insensitive; debe existir ya).
* ``demand``   valor de demanda/venta del período.
* ``date``     (opcional) ordena la serie; si falta, se respeta el orden del archivo.
* ``business`` (opcional) desambigua productos homónimos de distintos negocios.

Archivo de una sola serie (sin columna de producto)::

    python manage.py import_demand_series ventas_leche.csv --product "Leche"

Ejemplos::

    python manage.py import_demand_series demanda.csv --user demo_bolivia
    python manage.py import_demand_series demanda.xlsx --sheet Ventas
    python manage.py import_demand_series demanda.csv --sep ';' --decimal ','   # formato boliviano
    python manage.py import_demand_series demanda.csv --append                  # añade a la serie previa
    python manage.py import_demand_series demanda.csv --dry-run                 # valida sin escribir
    python manage.py import_demand_series demanda.csv --strict                  # omite series < mínimo
"""
import logging

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from business.services import demand_import as di

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = ("Importa series de demanda reales (CSV/Excel) a la respuesta de "
            "demanda histórica de cada producto (la que consume la simulación).")

    def add_arguments(self, parser):
        parser.add_argument("path", type=str, help="Ruta al archivo CSV o Excel.")
        parser.add_argument("--user", type=str, default="",
                            help="Username dueño de los productos (acota la resolución de nombres).")
        parser.add_argument("--business", type=str, default="",
                            help="Nombre de negocio para desambiguar productos homónimos.")
        parser.add_argument("--product", type=str, default="",
                            help="Producto destino para archivos de una sola serie (sin columna de producto).")
        # Nombres de columnas.
        parser.add_argument("--product-col", type=str, default="product")
        parser.add_argument("--demand-col", type=str, default="demand")
        parser.add_argument("--date-col", type=str, default="date")
        parser.add_argument("--business-col", type=str, default="business")
        # Parsing del archivo.
        parser.add_argument("--sep", type=str, default=",", help="Separador CSV (default ',').")
        parser.add_argument("--decimal", type=str, default=".", help="Separador decimal (default '.').")
        parser.add_argument("--sheet", type=str, default="0", help="Hoja de Excel (nombre o índice).")
        # Comportamiento.
        parser.add_argument("--append", action="store_true",
                            help="Añade a la serie previa en vez de reemplazarla.")
        parser.add_argument("--strict", action="store_true",
                            help=f"Omite productos con menos de {di.MIN_POINTS_RECOMMENDED} puntos válidos.")
        parser.add_argument("--dry-run", action="store_true",
                            help="Valida y reporta sin escribir en la base de datos.")

    def handle(self, *args, **opts):
        path = opts["path"]
        dry = opts["dry_run"]
        replace = not opts["append"]

        # Resolver usuario (opcional).
        user = None
        if opts["user"]:
            try:
                user = User.objects.get(username=opts["user"])
            except User.DoesNotExist:
                raise CommandError(f"El usuario '{opts['user']}' no existe.")

        # Hoja de Excel: índice si es numérica, si no nombre.
        sheet = opts["sheet"]
        try:
            sheet = int(sheet)
        except (TypeError, ValueError):
            pass

        # 1) Cargar y agrupar.
        try:
            df = di.load_dataframe(path, sep=opts["sep"], decimal=opts["decimal"], sheet=sheet)
        except FileNotFoundError:
            raise CommandError(f"No se encontró el archivo: {path}")
        except Exception as e:
            raise CommandError(f"No se pudo leer '{path}': {e}")

        try:
            grouped = di.group_series(
                df,
                product_col=opts["product_col"],
                demand_col=opts["demand_col"],
                date_col=opts["date_col"],
                business_col=opts["business_col"],
                single_product=opts["product"] or None,
            )
        except KeyError as e:
            raise CommandError(str(e))

        if not grouped:
            raise CommandError("El archivo no contiene series de demanda.")

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Importando {len(grouped)} serie(s) desde {path}"
            + (" [DRY-RUN]" if dry else "")))

        imported = skipped = errored = 0

        for (prod_name, biz_name), raw_values in grouped.items():
            business = biz_name or (opts["business"] or None)

            # Resolver producto.
            try:
                product = di.resolve_product(prod_name, user=user, business=business)
            except LookupError as e:
                errored += 1
                self.stdout.write(self.style.ERROR(f"  ✗ {prod_name}: {e}"))
                continue

            # Limpiar la serie.
            series, dropped = di.clean_series(raw_values)
            warns = di.sample_warnings(len(series))

            if len(series) < di.MIN_POINTS_HARD:
                skipped += 1
                self.stdout.write(self.style.WARNING(
                    f"  ⚠ {prod_name}: solo {len(series)} punto(s) válido(s) "
                    f"(mínimo {di.MIN_POINTS_HARD}) — omitido"))
                continue

            if opts["strict"] and len(series) < di.MIN_POINTS_RECOMMENDED:
                skipped += 1
                self.stdout.write(self.style.WARNING(
                    f"  ⚠ {prod_name}: {len(series)} < {di.MIN_POINTS_RECOMMENDED} "
                    f"puntos y --strict — omitido"))
                continue

            # Escribir.
            try:
                res = di.write_series(product, series, replace=replace, dry_run=dry)
            except Exception as e:
                errored += 1
                self.stdout.write(self.style.ERROR(f"  ✗ {prod_name}: {e}"))
                logger.exception("Error importando serie de %s", prod_name)
                continue

            if res.status == 'error':
                errored += 1
                self.stdout.write(self.style.ERROR(f"  ✗ {prod_name}: {res.message}"))
                continue

            imported += 1
            biz = f" [{res.business}]" if res.business else ""
            action = "añadidos a" if res.appended else "escritos en"
            detail = (f"{len(series)} puntos {action} {res.results_updated} "
                      f"resultado(s); {dropped} descartado(s); "
                      f"{res.n_previous_deleted} previo(s) eliminado(s)")
            self.stdout.write(self.style.SUCCESS(f"  ✓ {prod_name}{biz}: {detail}"))
            for w in warns:
                self.stdout.write(self.style.WARNING(f"      · {w}"))

        # Resumen.
        self.stdout.write("")
        summary = f"Importadas: {imported} · Omitidas: {skipped} · Errores: {errored}"
        style = self.style.SUCCESS if errored == 0 else self.style.WARNING
        self.stdout.write(style(summary))
        if dry:
            self.stdout.write(self.style.NOTICE("DRY-RUN: no se escribió nada."))
