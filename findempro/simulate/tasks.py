# tasks.py
import logging
from typing import Dict, Any
from celery import shared_task, Task
from celery.result import AsyncResult
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings

from .models import Simulation, ResultSimulation
from .utils.chart_utils import ChartGenerator

logger = logging.getLogger(__name__)


class SimulationTask(Task):
    """Base task class for simulation tasks"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        logger.error(f"Task {task_id} failed: {exc}")
        
        # Simulation.status / error_message no existen como campos del modelo;
        # solo marcamos is_completed=False para reflejar el fallo.
        if args:
            simulation_id = args[0]
            try:
                Simulation.objects.filter(id=simulation_id).update(is_completed=False)
            except Exception:
                pass
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success"""
        logger.info(f"Task {task_id} completed successfully")


@shared_task
def run_stateless_simulation(config_dict: Dict[str, Any], extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Ejecuta una simulación Monte Carlo *stateless* en segundo plano.

    Reconstruye ``SimulationConfig`` desde ``config_dict`` (payload ya validado
    por ``SimulateAsyncAPIView``), corre el motor y devuelve el ``to_dict()``
    fusionado con ``extra`` (metadata como ``_profile_used`` / ``_industry_sector``).

    No persiste nada en BD: Celery guarda el valor de retorno en el result
    backend (Redis en prod), de donde el endpoint de status lo recupera.

    Los errores se propagan para que la tarea quede en estado FAILURE con el
    mensaje de la excepción (sin trazas hacia el cliente).
    """
    from simulate.services.simulation_engine import MonteCarloEngine, SimulationConfig

    try:
        config = SimulationConfig(**config_dict)
        result = MonteCarloEngine(config).to_dict()
        if extra:
            result.update(extra)
        return result
    except ValueError as exc:
        logger.error("Error en run_stateless_simulation: %s", exc)
        raise
    except Exception as exc:
        logger.error("Error en run_stateless_simulation: %s", exc)
        raise


@shared_task(base=SimulationTask, bind=True, max_retries=3)
def execute_simulation_async(self, simulation_id: int) -> Dict[str, Any]:
    """Execute simulation asynchronously with real per-period progress tracking."""
    try:
        logger.info("Starting async simulation %s", simulation_id)

        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Inicializando...', 'phase': 'init'},
        )

        simulation = Simulation.objects.get(id=simulation_id)
        logger.info("Simulation %s → Celery task %s", simulation_id, self.request.id)

        # Guardar task_id en caché para que el frontend pueda hacer polling
        cache.set(f"sim_task_id:{simulation_id}", self.request.id, 3600)

        from simulate.services.simulation_service import SimulationService
        from simulate.core import (
            MonteCarloConfig, ScenarioGenerator, CompanyConfig,
            DiscreteEventEngine, build_config_from_profile,
        )
        import numpy as np

        service = SimulationService()
        product = simulation.fk_questionary_result.fk_questionary.fk_product
        total_periods = simulation.duration_in_days

        # ── Cargar config (igual que run_full_pipeline) ───────────────────────
        self.update_state(
            state='PROGRESS',
            meta={'current': 5, 'total': 100, 'status': 'Cargando configuración...', 'phase': 'config'},
        )

        # Delegar al pipeline completo con callback de progreso
        # Para progress real, el servicio necesita un callback; usamos
        # un patrón sencillo: actualizamos el estado por períodos en lotes.
        pipeline_result = service.run_and_save(
            simulation=simulation,
            _progress_callback=lambda period, total: self.update_state(
                state='PROGRESS',
                meta={
                    'current': 10 + int(period / total * 75),
                    'total': 100,
                    'status': f'Simulando período {period}/{total}...',
                    'phase': 'simulation',
                    'period': period,
                    'total_periods': total,
                },
            ) if period % max(1, total // 10) == 0 else None,
        )

        # ── Generar gráficos ──────────────────────────────────────────────────
        self.update_state(
            state='PROGRESS',
            meta={'current': 88, 'total': 100, 'status': 'Generando gráficos...', 'phase': 'charts'},
        )

        results = ResultSimulation.objects.filter(fk_simulation_id=simulation_id)
        chart_generator = ChartGenerator()
        charts = chart_generator.generate_all_charts(simulation_id, simulation, list(results))

        if hasattr(settings, 'SEND_SIMULATION_EMAILS') and settings.SEND_SIMULATION_EMAILS:
            send_simulation_complete_email.delay(simulation_id)

        self.update_state(
            state='SUCCESS',
            meta={'current': 100, 'total': 100, 'status': 'Completado', 'phase': 'done'},
        )

        return {
            'status': 'success',
            'simulation_id': simulation_id,
            'results_count': results.count(),
            'charts_generated': len(charts.get('chart_images', {})),
        }

    except Exception as e:
        logger.error("Error in async simulation %s: %s", simulation_id, e)
        retry_in = 60 * (2 ** self.request.retries)
        self.retry(exc=e, countdown=retry_in, max_retries=3)


@shared_task
def send_simulation_complete_email(simulation_id: int):
    """Send email notification when simulation completes"""
    try:
        simulation = Simulation.objects.select_related(
            'fk_questionary_result__fk_questionary__fk_product__fk_business__fk_user'
        ).get(id=simulation_id)
        
        user = simulation.fk_questionary_result.fk_questionary.fk_product.fk_business.fk_user
        product = simulation.fk_questionary_result.fk_questionary.fk_product
        
        subject = f"Simulación Completada - {product.name}"
        message = f"""
        Estimado {user.get_full_name() or user.username},
        
        Su simulación para el producto {product.name} ha sido completada exitosamente.
        
        Detalles:
        - ID de Simulación: {simulation_id}
        - Duración: {simulation.quantity_time} {simulation.unit_time}
        - Fecha de finalización: {simulation.last_updated.strftime('%d/%m/%Y %H:%M')}
        
        Puede ver los resultados en:
        {settings.SITE_URL}/simulate/result/{simulation_id}/
        
        Saludos,
        El equipo de Simulación
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        logger.info(f"Email sent to {user.email} for simulation {simulation_id}")
        
    except Exception as e:
        logger.error(f"Error sending email for simulation {simulation_id}: {str(e)}")


@shared_task
def cleanup_old_simulations():
    """Clean up old simulation data periodically"""
    from datetime import timedelta
    from django.utils import timezone
    
    try:
        # Delete simulations older than 90 days
        cutoff_date = timezone.now() - timedelta(days=90)
        
        old_simulations = Simulation.objects.filter(
            date_created__lt=cutoff_date,
            is_completed=True
        )
        
        count = old_simulations.count()
        
        # Delete related data first
        for sim in old_simulations:
            # Clear cache
            cache.delete(f"simulation_results_{sim.id}")
            cache.delete(f"charts_{sim.id}")
            
            # Delete results
            ResultSimulation.objects.filter(fk_simulation=sim).delete()
        
        # Delete simulations
        old_simulations.delete()
        
        logger.info(f"Cleaned up {count} old simulations")
        
        return {'deleted_count': count}
        
    except Exception as e:
        logger.error(f"Error in cleanup task: {str(e)}")
        raise


@shared_task
def check_simulation_status(task_id: str) -> Dict[str, Any]:
    """Check the status of an async simulation task"""
    try:
        result = AsyncResult(task_id)
        
        return {
            'task_id': task_id,
            'status': result.status,
            'result': result.result,
            'info': result.info
        }
        
    except Exception as e:
        logger.error(f"Error checking task status: {str(e)}")
        return {
            'task_id': task_id,
            'status': 'ERROR',
            'error': str(e)
        }


@shared_task(bind=True, max_retries=2)
def run_sensitivity_async(
    self,
    project_id: str,
    variation_pct: float = 0.20,
    n_runs: int = 500,
    seed=None,
) -> Dict[str, Any]:
    """
    Ejecuta análisis de sensibilidad OAT en segundo plano.
    Disparado por SensitivityAnalysisView cuando n_variables > 10.
    Guarda el resultado en cache (TTL 1h) bajo la key 'sensitivity:{project_id}:{task_id}'.
    """
    from simulate.canvas_models import SimulationProject
    from simulate.services.sensitivity_service import SensitivityService

    try:
        project = SimulationProject.objects.prefetch_related('nodes', 'edges').get(id=project_id)

        nodes = list(project.nodes.values(
            'id', 'node_type', 'label', 'equation', 'initial_value',
            'units', 'distribution_config',
        ))
        for n in nodes:
            n['id'] = str(n['id'])

        edges = list(project.edges.values(
            'id', 'source_node_id', 'target_node_id', 'edge_type',
        ))
        for e in edges:
            e['id'] = str(e['id'])
            e['source_node_id'] = str(e['source_node_id'])
            e['target_node_id'] = str(e['target_node_id'])

        service = SensitivityService()
        results = service.run_oat(
            nodes=nodes,
            edges=edges,
            run_specs=project.run_specs,
            variation_pct=variation_pct,
            n_runs=n_runs,
            seed=seed,
        )

        baseline_profit = results[0].baseline_mean if results else None
        chart_data = service.to_apexcharts(results, variation_pct, baseline_profit)

        cache_key = f'sensitivity:{project_id}:{self.request.id}'
        cache.set(cache_key, chart_data, 3600)
        logger.info('run_sensitivity_async: done, %d variables, key=%s', len(results), cache_key)

        return {
            'status': 'success',
            'project_id': project_id,
            'n_results': len(results),
            'tornado_chart': chart_data,
        }

    except ValueError as exc:
        logger.warning('run_sensitivity_async: incomplete financial contract for %s: %s', project_id, exc)
        return {
            'status': 'incomplete',
            'project_id': project_id,
            'error': str(exc),
            'code': 'financial_inputs_required',
        }
    except Exception as exc:
        logger.error('Error en run_sensitivity_async para proyecto %s: %s', project_id, exc)
        self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, name="simulate.execute_canvas_run_async", max_retries=2)
def execute_canvas_run_async(self, run_id: str, scenario: str = "expected") -> Dict[str, Any]:
    """Execute a large canvas run through the existing simulations queue."""
    import json
    import time

    from simulate.canvas_models import CanvasSimulationRun
    from simulate.core.model_compiler import ModelCompiler
    from simulate.views.canvas_views import _run_des, _run_montecarlo, _run_scenario
    from tenancy.models import UsageEvent
    from tenancy.services import record_resource_usage, record_usage

    run = CanvasSimulationRun.objects.select_related("project__organization").get(id=run_id)
    if run.status == "cancelled":
        return {"run_id": run_id, "status": "cancelled"}
    project = run.project
    organization = project.organization
    run.status = "running"
    run.progress = 10
    run.save(update_fields=["status", "progress"])
    started = time.monotonic()
    try:
        nodes = list(project.nodes.values(
            "id", "node_type", "label", "equation", "initial_value", "units",
            "position_x", "position_y", "distribution_config",
        ))
        for node in nodes:
            node["id"] = str(node["id"])
        edges = list(project.edges.values(
            "id", "source_node_id", "target_node_id", "edge_type", "line_style", "polarity",
        ))
        for edge in edges:
            edge["id"] = str(edge["id"])
            edge["source_node_id"] = str(edge["source_node_id"])
            edge["target_node_id"] = str(edge["target_node_id"])
        compiler = ModelCompiler(nodes, edges, run.parameters_snapshot or project.run_specs)
        compiler.compile()
        run.progress = 30
        run.save(update_fields=["progress"])
        if run.run_type == "des":
            results, statistics = _run_des(compiler.compile_to_des_config())
        elif run.run_type == "scenario":
            results, statistics = _run_scenario(compiler.compile_to_montecarlo_config(), scenario)
        else:
            results, statistics = _run_montecarlo(compiler.compile_to_montecarlo_config())
        runtime_seconds = max(0.0, time.monotonic() - started)
        updated = CanvasSimulationRun.objects.filter(id=run.id, status="running").update(
            results=results,
            statistics=statistics,
            run_duration_ms=int(runtime_seconds * 1000),
            status="completed",
            progress=100,
        )
        if not updated:
            return {"run_id": run_id, "status": "cancelled"}
        record_usage(
            organization, UsageEvent.Metric.SIMULATION_RUNTIME, runtime_seconds,
            "canvas.task.runtime", run.id, {"cost": "COST_UNKNOWN"},
        )
        record_resource_usage(
            organization, "CPU_SIMULATION", runtime_seconds, "seconds",
            "canvas.task", run.id, {"cost": "COST_UNKNOWN"},
        )
        record_resource_usage(
            organization, "STORAGE",
            len(json.dumps({"results": results, "statistics": statistics}, default=str).encode("utf-8")),
            "bytes", "canvas.task.result", run.id, {"cost": "COST_UNKNOWN"},
        )
        return {"run_id": run_id, "status": "completed"}
    except Exception as exc:
        CanvasSimulationRun.objects.filter(id=run.id, status="running").update(
            status="failed", error=type(exc).__name__, progress=100
        )
        logger.exception("Canvas simulation failed", extra={"run_id": run_id})
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task
def check_var_alerts_async(
    simulation_id: int,
    var_value: float,
    cvar_value: float,
    product_id: int | None = None,
) -> Dict[str, Any]:
    """
    Evalúa RiskAlerts activos tras una simulación y envía emails si se superan umbrales.

    Llamado automáticamente por SimulationService.run_and_save() cuando la
    simulación termina con éxito.

    Args:
        simulation_id: ID de la simulación completada.
        var_value:     VaR calculado por el pipeline (en BOB).
        cvar_value:    CVaR/ES calculado por el pipeline (en BOB).
        product_id:    ID del producto asociado (para filtrar alertas por producto).
    """
    from django.core.mail import send_mail
    from simulate.models import RiskAlert, Simulation

    try:
        simulation = Simulation.objects.select_related(
            'fk_questionary_result__fk_questionary__fk_product__fk_business__fk_user'
        ).get(id=simulation_id)

        user = simulation.fk_questionary_result.fk_questionary.fk_product.fk_business.fk_user
        product = simulation.fk_questionary_result.fk_questionary.fk_product

        alerts_qs = RiskAlert.objects.filter(user=user, is_active=True)
        if product_id is not None:
            alerts_qs = alerts_qs.filter(fk_product_id=product_id) | RiskAlert.objects.filter(
                user=user, is_active=True, fk_product__isnull=True
            )

        triggered = 0
        for alert in alerts_qs:
            if not alert.is_triggered(var_value, cvar_value):
                continue

            triggered += 1
            subject = f'⚠️ Alerta de Riesgo VaR — {product.name}'
            body = (
                f'Estimado {user.get_full_name() or user.username},\n\n'
                f'La simulación #{simulation_id} para el producto "{product.name}" '
                f'ha superado el umbral de riesgo configurado.\n\n'
                f'  VaR calculado:    BOB {var_value:,.2f}\n'
                f'  Umbral VaR:       BOB {alert.var_threshold:,.2f}\n'
                f'  CVaR calculado:   BOB {cvar_value:,.2f}\n'
                + (
                    f'  Umbral CVaR:      BOB {alert.cvar_threshold:,.2f}\n'
                    if alert.cvar_threshold else ''
                )
                + f'\nRevise los resultados en el panel de FindemproAI.\n\n'
                f'— Equipo FindemproAI'
            )

            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[alert.email],
                fail_silently=True,
            )
            logger.info(
                'RiskAlert disparada (sim=%s, alert=%s, VaR=%.2f, email=%s)',
                simulation_id, alert.id, var_value, alert.email,
            )

        return {'simulation_id': simulation_id, 'triggered': triggered}

    except Exception as exc:
        logger.error('Error en check_var_alerts_async (sim=%s): %s', simulation_id, exc)
        return {'simulation_id': simulation_id, 'error': str(exc)}


# Periodic tasks (configure in celery beat)
@shared_task
def daily_statistics_update():
    """Update daily statistics for all active simulations"""
    try:
        from django.db.models import Count, Avg
        from datetime import timedelta
        from django.utils import timezone
        
        yesterday = timezone.now() - timedelta(days=1)
        
        stats = Simulation.objects.filter(
            date_created__gte=yesterday
        ).aggregate(
            total_simulations=Count('id'),
            avg_duration=Avg('quantity_time'),
        )
        
        # Store in cache for dashboard
        cache.set('daily_simulation_stats', stats, 86400)  # 24 hours
        
        logger.info(f"Daily stats updated: {stats}")
        
        return stats
        
    except Exception as e:
        logger.error(f"Error updating daily stats: {str(e)}")
        raise
