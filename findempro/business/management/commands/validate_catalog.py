"""
manage.py validate_catalog
==========================
Smoke de simulación del catálogo COMPLETO: corre el pipeline Monte Carlo real
(``SimulationService.run_full_pipeline``) sobre **cada producto activo** del
usuario y reporta ✓/✗ por producto. Valida la promesa central del proyecto
("todos los tipos de PYME bolivianas, simulables") sobre datos reales de la DB
— cosa que ``seed_bolivia --run-sim`` no hace (solo simula 1 producto por
negocio y únicamente los recién sembrados).

Las simulaciones creadas son de humo: se **eliminan** al final (usa ``--keep``
para conservarlas). Sale con error si algún producto no simula, para poder
usarlo como gate en CI.

Ejemplos:
    python manage.py validate_catalog --user admin
    python manage.py validate_catalog --user admin --types 12,16 --mc-scenarios 50
    python manage.py validate_catalog --user admin --keep
"""
import ast
import logging
import time

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = ("Simula cada producto activo del catálogo (Monte Carlo real) y "
            "reporta ✓/✗ por producto.")

    def add_arguments(self, parser):
        parser.add_argument("--user", type=str, required=True,
                            help="Username dueño de los negocios a validar.")
        parser.add_argument("--types", type=str, default="",
                            help="Filtrar BusinessType, separados por coma (default: todos).")
        parser.add_argument("--mc-scenarios", type=int, default=100,
                            help="Escenarios Monte Carlo por producto (default: 100).")
        parser.add_argument("--periods", type=int, default=30,
                            help="Períodos (días) a simular (default: 30).")
        parser.add_argument("--keep", action="store_true",
                            help="Conserva las simulaciones de humo en la DB.")

    def handle(self, *args, **opts):
        from product.models import Product
        from questionary.models import QuestionaryResult, Answer
        from simulate.models import Simulation, ProbabilisticDensityFunction
        from simulate.services.simulation_service import SimulationService

        try:
            user = User.objects.get(username=opts["user"])
        except User.DoesNotExist:
            raise CommandError(f"no existe el usuario '{opts['user']}'")

        products = Product.objects.filter(
            fk_business__fk_user=user, is_active=True, fk_business__is_active=True,
        ).select_related("fk_business").order_by("fk_business__type", "name")
        if opts["types"].strip():
            try:
                wanted = [int(t) for t in opts["types"].split(",") if t.strip()]
            except ValueError:
                raise CommandError("--types debe ser una lista de enteros separados por coma.")
            products = products.filter(fk_business__type__in=wanted)
        if not products.exists():
            raise CommandError("no hay productos activos que validar (¿corriste seed_bolivia?)")

        svc = SimulationService()
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Validando {products.count()} productos "
            f"(n={opts['mc_scenarios']}, {opts['periods']} períodos)…"))

        ok, failures, sim_ids = [], [], []
        for product in products:
            label = f"tipo {product.fk_business.type:2} · {product.name}"
            t0 = time.monotonic()
            try:
                status = self._simulate_product(
                    product, svc, QuestionaryResult, Answer, Simulation,
                    ProbabilisticDensityFunction, opts, sim_ids)
                elapsed = time.monotonic() - t0
                ok.append(product.name)
                self.stdout.write(self.style.SUCCESS(
                    f"  ✓ {label:48} {status} ({elapsed:.1f}s)"))
            except Exception as exc:  # noqa: BLE001
                logger.exception("Fallo simulando '%s'", product.name)
                failures.append((label, str(exc)))
                self.stdout.write(self.style.ERROR(f"  ✗ {label:48} {exc}"))

        if not opts["keep"] and sim_ids:
            Simulation.objects.filter(id__in=sim_ids).delete()

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Catálogo: {len(ok)} productos simulan ✓ · {len(failures)} fallan ✗"
            + ("" if opts["keep"] else " · simulaciones de humo eliminadas")))
        if failures:
            for label, msg in failures:
                self.stdout.write(self.style.ERROR(f"  ✗ {label}: {msg}"))
            raise CommandError(f"{len(failures)} producto(s) no simulan")

    # ── internos ─────────────────────────────────────────────────────────────
    def _simulate_product(self, product, svc, QuestionaryResult, Answer,
                          Simulation, PDF, opts, sim_ids):
        """Corre el pipeline sobre un producto; devuelve un resumen de 1 línea."""
        import math

        qr = QuestionaryResult.objects.filter(
            fk_questionary__fk_product=product, is_active=True).first()
        if qr is None:
            raise RuntimeError("sin QuestionaryResult activo")
        fdp = PDF.objects.filter(
            fk_business=product.fk_business, is_active=True).first()
        if fdp is None:
            raise RuntimeError("el negocio no tiene ProbabilisticDensityFunction")

        dh_answer = Answer.objects.filter(
            fk_questionary_result=qr, fk_question__fk_variable__initials="DH",
        ).first()
        try:
            demand_history = ast.literal_eval(dh_answer.answer) if dh_answer else []
        except (ValueError, SyntaxError):
            demand_history = []
        if not demand_history:
            raise RuntimeError("sin demanda histórica (DH) parseable")

        with transaction.atomic():
            sim = Simulation.objects.create(
                quantity_time=opts["periods"], unit_time="days", fk_fdp=fdp,
                demand_history=demand_history, fk_questionary_result=qr,
                confidence_level=0.95, random_seed=42, is_active=True,
            )
        sim_ids.append(sim.id)

        res = svc.run_full_pipeline(sim, n_monte_carlo=opts["mc_scenarios"])
        periods = res.get("period_results") or []
        if len(periods) != opts["periods"]:
            raise RuntimeError(
                f"pipeline devolvió {len(periods)} períodos (esperaba {opts['periods']})")
        first = periods[0]
        revenue = first.get("revenue_mean", 0)
        profit = first.get("profit_mean", 0)
        for name, val in (("revenue_mean", revenue), ("profit_mean", profit)):
            if val is None or (isinstance(val, float) and not math.isfinite(val)):
                raise RuntimeError(f"{name} no finito: {val!r}")
        note = "" if profit >= 0 else "  ⚠ utilidad negativa"
        return (f"DH={len(demand_history)} pts · ingreso Bs {revenue:,.0f}/día · "
                f"utilidad Bs {profit:,.0f}/día{note}")
