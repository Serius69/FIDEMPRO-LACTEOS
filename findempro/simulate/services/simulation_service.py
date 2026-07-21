"""
simulation_service.py
=====================
Capa de servicios que orquesta los tres módulos core:
  1. monte_carlo      →  genera escenarios probabilísticos
  2. discrete_engine  →  simula operaciones por escenario
  3. decision_engine  →  analiza resultados y genera recomendaciones
"""

import hashlib
import json
import logging
import os
import time

import numpy as np
from django.core.cache import cache

from simulate.metrics import (
    ACTIVE_SIMULATIONS,
    SIMULATION_COUNTER,
    SIMULATION_DURATION,
    scenarios_bucket,
)
from simulate.core import (
    MonteCarloConfig, ScenarioGenerator, aggregate_results,
    CompanyConfig, DiscreteEventEngine, build_config_from_profile,
    DecisionEngine, DecisionReport, analizar_decision,
)
from simulate.exceptions import (
    SimulationError, InvalidModelError, InsufficientDataError,
)
from simulate.utils.simulation_core_utils import SimulationCore
from simulate.utils.simulation_financial_utils import SimulationFinancialAnalyzer
from simulate.services.statistical_service import StatisticalService
from simulate.services.validation_service import SimulationValidationService
from simulate.validators.simulation_validators import SimulationValidator

logger = logging.getLogger(__name__)


def _use_vectorized_engine() -> bool:
    """
    Flag del motor Monte Carlo vectorizado (CPU/GPU). Activo por defecto.

    Desactivar con ``FINDEMPRO_MC_ENGINE=scalar`` para forzar el motor escalar
    clásico (p. ej. depuración o comparación). La selección CPU vs GPU la maneja
    ``FINDEMPRO_GPU`` (auto|on|off) en ``simulate.core.gpu_backend``.
    """
    return os.environ.get("FINDEMPRO_MC_ENGINE", "vectorized").strip().lower() != "scalar"


class SimulationService:
    """
    Servicio unificado que coordina todas las operaciones de simulación.

    Mantiene la API existente (prepare_simulation_analysis, etc.) y agrega
    run_full_pipeline() que usa los nuevos módulos core.
    """

    def __init__(self):
        self.core = SimulationCore()
        self.validator = SimulationValidator()
        self.statistical = StatisticalService()
        self.financial = SimulationFinancialAnalyzer()
        self.validation = SimulationValidationService()

    # ── API existente (compatible con vistas actuales) ────────────────────────

    def prepare_simulation_analysis(self, questionary_id, user, quantity_time, unit_time):
        """Prepara todos los datos necesarios para configurar una simulación."""
        questionary_result = self._get_questionary_with_data(questionary_id)

        demand_history = self._extract_demand_history(questionary_result)
        if not demand_history:
            raise InsufficientDataError(
                f"No se encontraron datos históricos de demanda para el cuestionario {questionary_id}"
            )

        analysis_results = self.statistical.analyze_demand_history(
            questionary_result.id, user
        )

        product = questionary_result.fk_questionary.fk_product
        areas = self._get_product_areas(product)
        fdps = self._get_available_fdps(product.fk_business)
        charts = self._generate_analysis_charts(demand_history, analysis_results)

        return {
            'questionary_result_instance': questionary_result,
            'areas': areas,
            'fdps': fdps,
            'demand_history': demand_history,
            'selected_quantity_time': quantity_time,
            'selected_unit_time': unit_time,
            **analysis_results,
            **charts,
        }

    # ── Helpers de caché ─────────────────────────────────────────────────────

    _CACHE_TTL = 86_400  # 24 horas para simulaciones deterministas

    @staticmethod
    def _pipeline_cache_key(simulation_instance, n_monte_carlo: int) -> str | None:
        """
        Genera una clave de caché determinista basada en la config de la simulación.
        Retorna None si random_seed es None (simulación no reproducible → no cachear).
        """
        seed = getattr(simulation_instance, 'random_seed', None)
        if seed is None:
            return None

        fingerprint = json.dumps({
            'sim_id': simulation_instance.id,
            'seed': seed,
            'n_scenarios': n_monte_carlo,
            'duration': simulation_instance.duration_in_days,
            'fdp': getattr(simulation_instance.fk_fdp, 'id', None),
        }, sort_keys=True)
        digest = hashlib.sha256(fingerprint.encode()).hexdigest()[:16]
        return f"sim_pipeline:{digest}"

    # ── Pipeline completo (nuevos módulos core) ───────────────────────────────

    def run_full_pipeline(
        self,
        simulation_instance,
        n_monte_carlo: int = 1_000,
        risk_aversion: float = 0.001,
        _progress_callback=None,
    ) -> dict:
        """
        Ejecuta el pipeline completo:
          Monte Carlo → Eventos Discretos → Motor de Decisión

        Cada escenario Monte Carlo es independiente: el engine se resetea antes
        de cada scenario para garantizar que el estado no se acumule entre
        realizaciones probabilísticas distintas.

        Args:
            simulation_instance: instancia de simulate.models.Simulation
            n_monte_carlo: número de escenarios Monte Carlo (default reducido a
                           1 000 para equilibrar precisión y velocidad)
            risk_aversion: coeficiente λ de aversión al riesgo (CARA)

        Returns:
            dict con claves:
              'aggregated'     → AggregatedResult
              'decision_report'→ DecisionReport
              'period_results' → lista de resúmenes por período
        """
        sim = simulation_instance

        # ── 0. Caché determinista (solo cuando random_seed es fijo) ───────────
        cache_key = self._pipeline_cache_key(sim, n_monte_carlo)
        if cache_key:
            cached = cache.get(cache_key)
            if cached is not None:
                logger.info("run_full_pipeline: cache HIT para sim=%s (key=%s)", sim.id, cache_key)
                return cached

        product = sim.fk_questionary_result.fk_questionary.fk_product
        _t0_pipeline = time.perf_counter()

        # ── 1. Cargar CompanyProfile (opcional) ───────────────────────────────
        profile = None
        try:
            from business.models import CompanyProfile
            profile = CompanyProfile.objects.get(fk_business=product.fk_business)
        except Exception:
            pass

        # ── 2. Construir MonteCarloConfig desde la Simulation + perfil ────────
        #   · mapeo distribution_type int→str
        #   · resolución 'auto' vía DistributionFactory.fit_best()
        #   · estacionalidad desde CompanyProfile
        mc_config = MonteCarloConfig.from_simulation(
            simulation=sim,
            company_profile=profile,
            n_scenarios=n_monte_carlo,
        )

        # ── 3. Generador de escenarios (RNG encapsulado, reproducible) ────────
        generator = ScenarioGenerator(mc_config)

        # ── 4. Configurar motor de eventos discretos ──────────────────────────
        from variable.models import Equation
        equations = list(
            Equation.objects.filter(
                is_active=True,
                fk_area__fk_product=product,
            ).select_related('fk_area')
        )

        if profile is not None:
            try:
                company_config = build_config_from_profile(profile, equations)
            except (AttributeError, ValueError) as exc:
                logger.warning("build_config_from_profile falló (%s), usando config mínima", exc)
                company_config = CompanyConfig(
                    sector='other',
                    business_name=product.fk_business.name,
                    equations=equations,
                )
        else:
            company_config = CompanyConfig(
                sector='other',
                business_name=product.fk_business.name,
                equations=equations,
            )
        company_config.total_periods = sim.duration_in_days

        # ── Prometheus: etiquetas disponibles ahora que company_config existe ─
        _sector = getattr(company_config, 'sector', 'other') or 'other'
        _n_bucket = scenarios_bucket(n_monte_carlo)

        # Variables exógenas del cuestionario (invariantes entre períodos).
        # El motor de ecuaciones espera exógenas ESCALARES; se descartan las series
        # (p. ej. DH = demanda histórica), que se manejan vía mc_config/escenarios,
        # no como entrada por período de las ecuaciones.
        from simulate.utils.variable_mapper import VariableMapper
        exogenous = {
            k: v for k, v in VariableMapper().extract_all_variables(sim.fk_questionary_result).items()
            if isinstance(v, (int, float)) and not isinstance(v, bool)
        }

        # ── 5. Ejecutar simulación: un engine reutilizado, reseteado por escenario
        #
        #  Para cada período t:
        #    · Se generan N escenarios probabilísticos (demanda, precio, costos)
        #    · El engine se resetea a estado_inicial antes de cada escenario
        #      → garantiza independencia estadística entre realizaciones MC
        #    · Se acumulan profit/demand/revenue de todos los períodos × escenarios
        #
        #  Esta estrategia "stateless-per-scenario" es correcta para modelos donde
        #  la distribución de resultados importa más que la trayectoria temporal
        #  (caso típico de PyMEs en planificación operativa de corto plazo).
        # ─────────────────────────────────────────────────────────────────────
        total_periods = sim.duration_in_days
        period_results: list = []
        profit_arr = demand_arr = revenue_arr = None

        # ── 5-fast. Ruta vectorizada (CPU NumPy / GPU CuPy) ───────────────────
        #  Reemplaza el bucle T×N objeto-por-objeto por operaciones de array sobre
        #  toda la grilla (válido porque cada escenario corre stateless-per-scenario).
        #  Numéricamente equivalente al motor escalar; ~100–1000× más rápido en CPU
        #  y con aceleración adicional en GPU. Cae al motor escalar si el modelo de
        #  ecuaciones no es vectorizable (ver can_vectorize) o si está deshabilitado.
        if _use_vectorized_engine():
            try:
                from simulate.core.vectorized_engine import VectorizedMonteCarlo, can_vectorize
                from simulate.core.gpu_backend import backend_name
                if can_vectorize(company_config, exogenous):
                    _t_vec = time.perf_counter()
                    with ACTIVE_SIMULATIONS.labels(sector=_sector).track_inprogress():
                        d_grid, r_grid, _c_grid, p_grid = VectorizedMonteCarlo(
                            mc_config, company_config, exogenous
                        ).run_grid()
                    for t in range(total_periods):
                        pd_, pr_, pp_ = d_grid[t], r_grid[t], p_grid[t]
                        period_results.append({
                            'period':       t + 1,
                            'demand_mean':  float(pd_.mean()),
                            'demand_std':   float(pd_.std()),
                            'demand_p5':    float(np.percentile(pd_, 5)),
                            'demand_p95':   float(np.percentile(pd_, 95)),
                            'revenue_mean': float(pr_.mean()),
                            'profit_mean':  float(pp_.mean()),
                            'profit_p5':    float(np.percentile(pp_, 5)),
                            'profit_p95':   float(np.percentile(pp_, 95)),
                            'prob_loss':    float((pp_ < 0).mean()),
                        })
                    demand_arr  = d_grid.reshape(-1)
                    revenue_arr = r_grid.reshape(-1)
                    profit_arr  = p_grid.reshape(-1)
                    logger.info(
                        "Pipeline MC vectorizado [%s]: %d×%d celdas en %.3fs",
                        backend_name(), total_periods, n_monte_carlo,
                        time.perf_counter() - _t_vec,
                    )
            except Exception as exc:  # cualquier fallo → ruta escalar segura
                logger.warning("MC vectorizado falló (%s); usando motor escalar.", exc)
                profit_arr = None

        # ── 5-slow. Ruta escalar clásica (fallback, objeto-por-objeto) ────────
        if profit_arr is None:
            engine = DiscreteEventEngine(company_config)
            all_profits: list = []
            all_demands: list = []
            all_revenues: list = []
            period_results = []

            with ACTIVE_SIMULATIONS.labels(sector=_sector).track_inprogress():
                for period_idx in range(total_periods):
                    if _progress_callback is not None:
                        _progress_callback(period_idx + 1, total_periods)

                    scenarios = generator.generate_for_period(
                        period_idx, n_scenarios=n_monte_carlo
                    )

                    period_profits: list = []
                    period_demands: list = []
                    period_revenues: list = []

                    for scenario in scenarios:
                        engine.reset_state()          # ← clave: cada escenario es independiente
                        result = engine.run_period(scenario, exogenous)
                        period_profits.append(result.profit)
                        period_demands.append(result.demand)
                        period_revenues.append(result.revenue)

                    all_profits.extend(period_profits)
                    all_demands.extend(period_demands)
                    all_revenues.extend(period_revenues)

                    period_results.append({
                        'period': period_idx + 1,
                        'demand_mean':  float(np.mean(period_demands)),
                        'demand_std':   float(np.std(period_demands)),
                        'demand_p5':    float(np.percentile(period_demands, 5)),
                        'demand_p95':   float(np.percentile(period_demands, 95)),
                        'revenue_mean': float(np.mean(period_revenues)),
                        'profit_mean':  float(np.mean(period_profits)),
                        'profit_p5':    float(np.percentile(period_profits, 5)),
                        'profit_p95':   float(np.percentile(period_profits, 95)),
                        'prob_loss':    float(np.mean(np.array(period_profits) < 0)),
                    })

            profit_arr  = np.array(all_profits,   dtype=float)
            demand_arr  = np.array(all_demands,   dtype=float)
            revenue_arr = np.array(all_revenues,  dtype=float)

        aggregated = aggregate_results(profit_arr, demand_arr, revenue_arr, mc_config)

        # ── 7. Motor de decisión ──────────────────────────────────────────────
        if profile is not None:
            try:
                decision_engine_inst = DecisionEngine.from_company_profile(profile)
            except (AttributeError, ValueError) as exc:
                logger.warning("DecisionEngine.from_company_profile falló (%s), usando defaults", exc)
                decision_engine_inst = DecisionEngine(risk_aversion=risk_aversion)
        else:
            decision_engine_inst = DecisionEngine(risk_aversion=risk_aversion)

        rev_mean    = float(np.mean(revenue_arr))
        profit_mean = float(np.mean(profit_arr))
        decision_report = decision_engine_inst.analyze(
            profit_samples=profit_arr,
            demand_samples=demand_arr,
            revenue_samples=revenue_arr,
            aggregated_vars={
                'IT': rev_mean,
                'GT': profit_mean,
                'TG': rev_mean - profit_mean,
            },
        )

        # ── Prometheus: registrar duración y contador ─────────────────────────
        _elapsed = time.perf_counter() - _t0_pipeline
        SIMULATION_DURATION.labels(
            sector=_sector,
            n_scenarios_bucket=_n_bucket,
        ).observe(_elapsed)
        SIMULATION_COUNTER.labels(
            sector=_sector,
            distribution_type=mc_config.distribution,
            status='success',
        ).inc()

        logger.info(
            "Pipeline completo: %d períodos × %d escenarios | "
            "decisión=%s | score=%.3f | t=%.2fs",
            sim.duration_in_days, n_monte_carlo,
            decision_report.overall_assessment,
            decision_report.overall_score,
            _elapsed,
        )

        result = {
            'aggregated':      aggregated,
            'decision_report': decision_report,
            'period_results':  period_results,
        }

        # Guardar en caché si la simulación es determinista
        if cache_key:
            cache.set(cache_key, result, self._CACHE_TTL)
            logger.debug("run_full_pipeline: resultado guardado en caché (key=%s, ttl=%ds)", cache_key, self._CACHE_TTL)

        return result

    # ── Persistencia del nuevo pipeline ──────────────────────────────────────

    def save_pipeline_results_to_db(self, simulation, pipeline_result: dict) -> int:
        """
        Convierte la salida de run_full_pipeline() en registros ResultSimulation.

        Diseño:
          · Un ResultSimulation por período del pipeline.
          · Idempotente: borra registros previos de la simulación antes de insertar.
          · Usa bulk_create para eficiencia.

        Args:
            simulation: instancia de simulate.models.Simulation
            pipeline_result: dict devuelto por run_full_pipeline()

        Returns:
            Número de registros creados.
        """
        from datetime import timedelta
        from simulate.models import ResultSimulation

        period_results = pipeline_result.get('period_results', [])
        if not period_results:
            logger.warning("save_pipeline_results_to_db: sin period_results, nada que guardar.")
            return 0

        base_date = simulation.date_created.date()

        # Idempotencia: borrar resultados anteriores de esta simulación
        deleted, _ = ResultSimulation.objects.filter(fk_simulation=simulation).delete()
        if deleted:
            logger.debug("Borrados %d ResultSimulation previos para simulación %s", deleted, simulation.id)

        objects = []
        for pr in period_results:
            period_idx = pr['period'] - 1
            demand_mean = pr['demand_mean']
            demand_p5   = pr.get('demand_p5', 0.0)
            demand_p95  = pr.get('demand_p95', demand_mean)

            # σ real por período (calculada sobre la grilla T×N de la simulación).
            # Se prefiere al reconstruido del rango p5–p95, que asume Normal (3.29 =
            # span 5–95 de la Normal) y sesga la σ cuando la demanda es asimétrica
            # (lognormal/gamma/GBM). Fallback al supuesto Normal solo si no está.
            demand_std = pr.get('demand_std')
            if demand_std is None:
                demand_std = max((demand_p95 - demand_p5) / 3.29, 0.0)
            else:
                demand_std = max(float(demand_std), 0.0)

            objects.append(ResultSimulation(
                fk_simulation=simulation,
                demand_mean=round(demand_mean, 4),
                demand_std_deviation=round(demand_std, 4),
                date=base_date + timedelta(days=period_idx + 1),
                variables={
                    'demand_p5':    pr.get('demand_p5'),
                    'demand_p95':   pr.get('demand_p95'),
                    'revenue_mean': pr.get('revenue_mean'),
                    'profit_mean':  pr.get('profit_mean'),
                    'profit_p5':    pr.get('profit_p5'),
                    'profit_p95':   pr.get('profit_p95'),
                    'prob_loss':    pr.get('prob_loss'),
                },
                confidence_intervals={
                    'demand_lower':  pr.get('demand_p5', 0.0),
                    'demand_upper':  pr.get('demand_p95', demand_mean),
                    'profit_lower':  pr.get('profit_p5', 0.0),
                    'profit_upper':  pr.get('profit_p95', 0.0),
                },
            ))

        ResultSimulation.objects.bulk_create(objects, ignore_conflicts=False)
        logger.info(
            "Guardados %d ResultSimulation para simulación %s", len(objects), simulation.id
        )
        return len(objects)

    def save_recommendations_to_db(self, simulation, decision_report) -> int:
        """
        Persiste las Recommendation del DecisionReport en FinanceRecommendationSimulation.

        Diseño:
          · Idempotente: borra registros previos de esta simulación antes de insertar.
          · Usa bulk_create para eficiencia.
          · Normaliza severity/category/impact a los choices válidos del modelo.

        Args:
            simulation:      instancia de simulate.models.Simulation
            decision_report: DecisionReport devuelto por run_full_pipeline()

        Returns:
            Número de registros creados.
        """
        from finance.models import FinanceRecommendationSimulation

        # Tablas de normalización entre vocabulario del core y choices del modelo
        _SEV  = {'info': 'low', 'warning': 'medium', 'critical': 'critical'}
        _CAT  = {
            'financiero': 'financial', 'operativo': 'financial',
            'riesgo':     'critical',  'demanda':   'profitability',
            'eficiencia': 'efficiency','costos':    'costs',
        }
        _IMP  = {
            'Bajo': 'low',  'bajo': 'low',   'low':      'low',
            'Medio':'medium','medio':'medium','medium':   'medium',
            'Alto': 'high', 'alto': 'high',  'high':     'high',
            'Crítico':'critical','crítico':'critical','critical':'critical',
        }
        _PRI  = {'low': 'low', 'medium': 'medium', 'high': 'high', 'critical': 'high'}

        # Idempotencia
        deleted, _ = FinanceRecommendationSimulation.objects.filter(
            fk_simulation=simulation
        ).delete()
        if deleted:
            logger.debug(
                "Borradas %d recomendaciones previas para simulación %s",
                deleted, simulation.id,
            )

        recommendations = getattr(decision_report, 'recommendations', [])
        if not recommendations:
            return 0

        objects = []
        for rec in recommendations:
            severity = _SEV.get(getattr(rec, 'severity', 'warning'), 'medium')
            category = _CAT.get(getattr(rec, 'category', 'financiero'), 'financial')
            impact   = _IMP.get(getattr(rec, 'impact',   'Medio'),      'medium')
            priority = _PRI.get(severity, 'medium')
            action   = getattr(rec, 'action', '') or ''

            objects.append(FinanceRecommendationSimulation(
                fk_simulation=simulation,
                category=category,
                severity=severity,
                title=getattr(rec, 'title', ''),
                description=getattr(rec, 'message', ''),
                recommendation=action,
                actions=[action] if action else [],
                impact=impact,
                priority=priority,
                metric_value=getattr(rec, 'metric_value', None),
                variable=getattr(rec, 'metric_name', None),
                threshold=getattr(rec, 'threshold', None),
                value=getattr(rec, 'metric_value', None),
            ))

        FinanceRecommendationSimulation.objects.bulk_create(objects)
        logger.info(
            "Guardadas %d recomendaciones para simulación %s",
            len(objects), simulation.id,
        )
        return len(objects)

    def run_and_save(
        self,
        simulation,
        n_monte_carlo: int = 1_000,
        risk_aversion: float = 0.001,
        _progress_callback=None,
    ) -> dict:
        """
        Punto de entrada único para ejecutar el pipeline completo y persistir
        todos los resultados en BD en una sola llamada.

        Orquesta en secuencia:
          1. run_full_pipeline()              → MC + DES + Motor de Decisión
          2. save_pipeline_results_to_db()    → registros ResultSimulation
          3. save_recommendations_to_db()     → FinanceRecommendationSimulation
          4. simulation.is_completed = True   → marca la simulación como terminada

        Args:
            simulation:    instancia de simulate.models.Simulation
            n_monte_carlo: escenarios MC por período
            risk_aversion: coeficiente λ CARA

        Returns:
            El mismo dict que run_full_pipeline(), para callers que necesiten los datos.
        """
        pipeline_result = self.run_full_pipeline(
            simulation_instance=simulation,
            n_monte_carlo=n_monte_carlo,
            risk_aversion=risk_aversion,
            _progress_callback=_progress_callback,
        )

        n_periods = self.save_pipeline_results_to_db(simulation, pipeline_result)
        n_recs    = self.save_recommendations_to_db(
            simulation, pipeline_result['decision_report']
        )

        simulation.is_completed = True
        simulation.save(update_fields=['is_completed', 'last_updated'])

        agg    = pipeline_result['aggregated']
        report = pipeline_result['decision_report']

        # Disparar alertas VaR en segundo plano (no bloquea la respuesta)
        try:
            from simulate.tasks import check_var_alerts_async
            product_id = (
                simulation.fk_questionary_result.fk_questionary.fk_product_id
            )
            check_var_alerts_async.delay(
                simulation_id=simulation.id,
                var_value=float(agg.value_at_risk),
                cvar_value=float(agg.expected_shortfall),
                product_id=product_id,
            )
        except Exception as exc:
            logger.warning('No se pudo encolar check_var_alerts_async: %s', exc)

        pipeline_result['summary'] = {
            'assessment':          report.overall_assessment,
            'score':               round(float(report.overall_score), 3),
            'profit_mean':         round(float(agg.profit_mean), 2),
            'probability_of_loss': round(float(agg.probability_of_loss), 4),
            'value_at_risk':       round(float(agg.value_at_risk), 2),
            'expected_shortfall':  round(float(agg.expected_shortfall), 2),
            'n_periods':           n_periods,
            'n_recommendations':   n_recs,
        }

        logger.info(
            "run_and_save completo: sim=%s | períodos=%d | recs=%d | "
            "assessment=%s | score=%.3f | profit_mean=%.2f | p_loss=%.4f | VaR=%.2f",
            simulation.id, n_periods, n_recs,
            report.overall_assessment, report.overall_score,
            agg.profit_mean, agg.probability_of_loss, agg.value_at_risk,
        )
        return pipeline_result

    # ── Helpers privados (ya existían en el servicio original) ───────────────

    def _get_questionary_with_data(self, questionary_id):
        from django.shortcuts import get_object_or_404
        from questionary.models import QuestionaryResult
        return get_object_or_404(
            QuestionaryResult.objects.select_related(
                'fk_questionary__fk_product__fk_business'
            ),
            id=questionary_id,
        )

    def _extract_demand_history(self, questionary_result):
        from questionary.models import Answer
        answers = Answer.objects.filter(
            fk_questionary_result=questionary_result,
            fk_question__fk_variable__initials='DH',
        ).values_list('answer', flat=True)
        history = []
        for answer in answers:
            try:
                data = json.loads(answer) if isinstance(answer, str) else answer
                if isinstance(data, list):
                    history.extend(float(v) for v in data if v is not None)
                else:
                    history.append(float(data))
            except (ValueError, TypeError):
                continue
        return history

    def _get_product_areas(self, product):
        from product.models import Area
        return list(Area.objects.filter(fk_product=product, is_active=True))

    def _get_available_fdps(self, business):
        from simulate.models import ProbabilisticDensityFunction
        return list(
            ProbabilisticDensityFunction.objects.filter(
                fk_business=business, is_active=True
            )
        )

    def _generate_analysis_charts(self, demand_history, analysis_results):
        try:
            from simulate.services.chart_service import ChartService
            chart_service = ChartService()
            return chart_service.generate_demand_charts(demand_history, analysis_results)
        except Exception as e:
            logger.warning(f"No se pudieron generar gráficos: {e}")
            return {}
