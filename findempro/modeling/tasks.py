from __future__ import annotations

import logging
import json
import time

from celery import shared_task
from django.utils import timezone

from .engine import run_engine
from .errors import encode_error, simulation_error
from .models import BusinessSimulationRun

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="modeling.run_business_simulation")
def run_business_simulation(self, run_id: str, iterations: int = 100, seed: int | None = None):
    run = BusinessSimulationRun.objects.select_related(
        "model_version__definition__business__organization", "scenario"
    ).get(id=run_id)
    organization = run.model_version.definition.business.organization
    if run.status == "cancelled":
        return {"status": "cancelled", "run_id": run_id}
    run.status = "running"
    run.progress = 10
    run.started_at = timezone.now()
    run.parameters_snapshot = {
        **(run.parameters_snapshot or {}),
        "model_version": run.model_version.version,
        "schema_version": run.model_version.schema_version,
        "content_hash": run.model_version.content_hash,
        "engine": run.engine,
        "seed": seed,
        "scenario_id": str(run.scenario_id) if run.scenario_id else None,
    }
    run.save(update_fields=["status", "progress", "started_at", "parameters_snapshot"])
    try:
        started_monotonic = time.monotonic()
        scenario = {"changes": run.scenario.changes} if run.scenario else {}
        run.progress = 20
        run.save(update_fields=["progress"])
        result = run_engine(run.model_version.spec, run.engine, iterations=iterations, seed=seed, scenario=scenario)
        result["traceability"] = {
            "model_version_id": str(run.model_version_id),
            "model_version": run.model_version.version,
            "schema_version": run.model_version.schema_version,
            "content_hash": run.model_version.content_hash,
            "engine": run.engine,
            "seed": seed,
            "iterations": iterations,
            "scenario_id": str(run.scenario_id) if run.scenario_id else None,
            "scenario": run.scenario.name if run.scenario else "BASE",
        }
        # The current engines execute as one bounded phase.  Exposing explicit
        # phase boundaries keeps polling truthful until finer-grained callbacks
        # are introduced for very large runs.
        run.progress = 80
        run.save(update_fields=["progress"])
        updated = BusinessSimulationRun.objects.filter(id=run.id, status="running").update(
            result=result, status="completed", progress=100, finished_at=timezone.now()
        )
        if updated:
            from tenancy.models import UsageEvent
            from tenancy.services import record_resource_usage, record_usage

            runtime_seconds = max(0.0, time.monotonic() - started_monotonic)
            result_bytes = len(json.dumps(result, ensure_ascii=False, default=str).encode("utf-8"))
            record_usage(
                organization, UsageEvent.Metric.SIMULATION_RUNTIME, runtime_seconds,
                "modeling.task.runtime", run.id, {"engine": run.engine, "cost": "COST_UNKNOWN"},
            )
            record_resource_usage(
                organization, "CPU_SIMULATION", runtime_seconds, "seconds",
                "modeling.task", run.id, {"cost": "COST_UNKNOWN"},
            )
            record_resource_usage(
                organization, "STORAGE", result_bytes, "bytes",
                "modeling.result", run.id, {"cost": "COST_UNKNOWN"},
            )
        return result if updated else {"status": "cancelled", "run_id": run_id}
    except Exception as exc:
        detail = simulation_error(exc)
        logger.exception("Business simulation failed", extra={"run_id": run_id, "error_code": detail["code"]})
        updated = BusinessSimulationRun.objects.filter(id=run.id, status="running").update(
            status="failed", error=encode_error(detail), finished_at=timezone.now()
        )
        if not updated:
            return {"status": "cancelled", "run_id": run_id}
        raise
