"""
manage.py seed_bolivia
======================
Siembra negocios demo para los 19 tipos de empresa de Bolivia, cada uno con
productos, variables, ecuaciones, cuestionario y respuestas (incluido histórico
de demanda) listos para simular.

Reutiliza el motor de simulación validado (181 variables / 91 ecuaciones) y
parametriza los valores con datos reales del mercado boliviano
(``business.data.bolivia_industries``, refrescables por ``scrape_bolivia_data``).

Ejemplos:
    python manage.py seed_bolivia                     # todos los tipos, usuario demo
    python manage.py seed_bolivia --types 4,5,16      # sólo panadería, carnicería, restaurante
    python manage.py seed_bolivia --user sergio        # asignar a un usuario existente
    python manage.py seed_bolivia --run-sim            # además ejecuta 1 simulación por negocio
    python manage.py seed_bolivia --force              # recrea aunque ya existan
"""
import logging

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction

from business.data.bolivia_industries import INDUSTRIES, MARKET_CONTEXT
from business.services.seed_service import IndustrySeeder

logger = logging.getLogger(__name__)

DEMO_USERNAME = "demo_bolivia"


class Command(BaseCommand):
    help = "Siembra los 19 tipos de empresa boliviana con datos listos para simular."

    def add_arguments(self, parser):
        parser.add_argument("--types", type=str, default="",
                            help="Lista de BusinessType a sembrar, separados por coma (default: todos).")
        parser.add_argument("--user", type=str, default=DEMO_USERNAME,
                            help=f"Username dueño de los negocios (default: {DEMO_USERNAME}, se crea si no existe).")
        parser.add_argument("--run-sim", action="store_true",
                            help="Ejecuta una simulación Monte Carlo por negocio tras sembrar.")
        parser.add_argument("--mc-scenarios", type=int, default=200,
                            help="Escenarios Monte Carlo si se usa --run-sim (default: 200).")
        parser.add_argument("--force", action="store_true",
                            help="Recrea el negocio aunque ya exista para ese usuario/tipo.")

    def handle(self, *args, **opts):
        user = self._get_or_create_user(opts["user"])

        if opts["types"].strip():
            try:
                wanted = [int(t) for t in opts["types"].split(",") if t.strip()]
            except ValueError:
                raise CommandError("--types debe ser una lista de enteros separados por coma.")
        else:
            wanted = sorted(INDUSTRIES.keys())

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Contexto macro: salario mín. Bs {MARKET_CONTEXT['min_wage_month_bs']:.0f}/mes · "
            f"inflación {MARKET_CONTEXT['inflation_annual_pct']:.0f}% · "
            f"FX {MARKET_CONTEXT['fx_usd_bob_official']} oficial "
            f"(fuente: {MARKET_CONTEXT['source']})"
        ))

        seeder = IndustrySeeder(user)
        seeded, skipped, failed = [], [], []

        for bt in wanted:
            spec = INDUSTRIES.get(bt)
            if spec is None:
                self.stderr.write(self.style.WARNING(f"  tipo {bt}: sin catálogo, se omite"))
                continue
            try:
                before = user.businesses.filter(type=bt, is_active=True).exists()
                business = seeder.seed_business(spec, force=opts["force"])
                if business is None:
                    failed.append(bt)
                    continue
                if before and not opts["force"]:
                    skipped.append((bt, spec.business_name))
                    self.stdout.write(f"  · tipo {bt:2} {spec.business_name:32} ya existía (omitido)")
                else:
                    seeded.append((bt, spec.business_name, business.id))
                    n_prod = business.products.count()
                    self.stdout.write(self.style.SUCCESS(
                        f"  ✓ tipo {bt:2} {spec.business_name:32} id={business.id}  productos={n_prod}"
                    ))
            except Exception as exc:  # noqa: BLE001
                logger.exception("Fallo al sembrar tipo %s", bt)
                failed.append(bt)
                self.stderr.write(self.style.ERROR(f"  ✗ tipo {bt}: {exc}"))

        if opts["run_sim"]:
            self._run_simulations(user, [s[2] for s in seeded], opts["mc_scenarios"])

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Listo. Sembrados: {len(seeded)} · Omitidos: {len(skipped)} · Fallidos: {len(failed)}"
        ))
        if failed:
            self.stdout.write(self.style.WARNING(f"Tipos fallidos: {failed}"))

    # ── helpers ──────────────────────────────────────────────────────────────
    def _get_or_create_user(self, username: str) -> User:
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": f"{username}@findempro.demo", "is_active": True},
        )
        if created:
            user.set_unusable_password()
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Usuario '{username}' creado."))
        return user

    def _run_simulations(self, user, business_ids, mc_scenarios):
        from business.models import Business
        from questionary.models import QuestionaryResult
        from simulate.models import Simulation, ProbabilisticDensityFunction
        from simulate.services.simulation_service import SimulationService

        svc = SimulationService()
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Ejecutando 1 simulación por negocio (n={mc_scenarios})…"))

        for bid in business_ids:
            try:
                business = Business.objects.get(id=bid)
                qr = QuestionaryResult.objects.filter(
                    fk_questionary__fk_product__fk_business=business, is_active=True
                ).first()
                fdp = ProbabilisticDensityFunction.objects.filter(fk_business=business).first()
                if not (qr and fdp):
                    self.stderr.write(self.style.WARNING(f"  tipo {business.type}: sin qresult/fdp, se omite"))
                    continue

                # Histórico de demanda desde la respuesta DH.
                from questionary.models import Answer
                import ast
                dh_answer = Answer.objects.filter(
                    fk_questionary_result=qr, fk_question__fk_variable__initials="DH"
                ).first()
                try:
                    demand_history = ast.literal_eval(dh_answer.answer) if dh_answer else []
                except (ValueError, SyntaxError):
                    demand_history = []

                with transaction.atomic():
                    sim = Simulation.objects.create(
                        quantity_time=30, unit_time="days", fk_fdp=fdp,
                        demand_history=demand_history, fk_questionary_result=qr,
                        confidence_level=0.95, random_seed=42, is_active=True,
                    )
                res = svc.run_full_pipeline(sim, n_monte_carlo=mc_scenarios)
                periods = res.get("period_results") or []
                first = periods[0] if periods else {}
                self.stdout.write(self.style.SUCCESS(
                    f"  ✓ tipo {business.type:2} sim={sim.id} períodos={len(periods)} "
                    f"ingreso≈Bs {first.get('revenue_mean', 0):,.0f}/día "
                    f"utilidad≈Bs {first.get('profit_mean', 0):,.0f}/día"
                ))
            except Exception as exc:  # noqa: BLE001
                logger.exception("Fallo simulación negocio %s", bid)
                self.stderr.write(self.style.ERROR(f"  ✗ negocio {bid}: {exc}"))
