from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APIClient
from simulate.canvas_models import CanvasSimulationRun, SimulationProject
from simulate.tasks import execute_canvas_run_async

from tenancy.models import ResourceUsage, UsageEvent
from tenancy.services import ensure_default_organization

pytestmark = pytest.mark.django_db


def account(name):
    return get_user_model().objects.create_user(username=name, password="test-password")


@override_settings(FINDEMPRO_CANVAS_SYNC_MAX_RUNS=1)
def test_large_run_is_queued_idempotent_and_cancellable():
    user = account("queued-owner")
    organization = ensure_default_organization(user)
    project = SimulationProject.objects.create(
        user=user,
        organization=organization,
        name="Queued project",
        domain="generic",
        run_specs={"n_runs_montecarlo": 2},
    )
    client = APIClient()
    client.force_authenticate(user=user)
    url = f"/api/v2/projects/{project.id}/simulate/"

    with patch(
        "simulate.tasks.execute_canvas_run_async.delay",
        return_value=SimpleNamespace(id="task-1"),
    ) as delay:
        first = client.post(
            url,
            {"run_type": "montecarlo", "override_params": {"n_runs_montecarlo": 2}},
            format="json",
            HTTP_IDEMPOTENCY_KEY="stable-run",
        )
        second = client.post(
            url,
            {"run_type": "montecarlo", "override_params": {"n_runs_montecarlo": 2}},
            format="json",
            HTTP_IDEMPOTENCY_KEY="stable-run",
        )

    assert first.status_code == 202
    assert second.status_code == 200
    assert delay.call_count == 1
    assert CanvasSimulationRun.objects.filter(project=project).count() == 1
    assert UsageEvent.objects.filter(
        organization=organization,
        metric=UsageEvent.Metric.SIMULATION_RUN,
    ).count() == 1

    run = CanvasSimulationRun.objects.get(project=project)
    cancelled = client.post(f"/api/v2/projects/{project.id}/runs/{run.id}/")
    assert cancelled.status_code == 200
    run.refresh_from_db()
    assert run.status == "cancelled"


def test_async_worker_records_lifecycle_runtime_and_unknown_cost_resources():
    user = account("worker-owner")
    organization = ensure_default_organization(user)
    project = SimulationProject.objects.create(
        user=user,
        organization=organization,
        name="Worker project",
        domain="generic",
        run_specs={"n_runs_montecarlo": 2},
    )
    run = CanvasSimulationRun.objects.create(
        project=project,
        n_runs=2,
        parameters_snapshot=project.run_specs,
        status="queued",
    )

    with (
        patch("simulate.core.model_compiler.ModelCompiler.compile", return_value={}),
        patch(
            "simulate.core.model_compiler.ModelCompiler.compile_to_montecarlo_config",
            return_value={"n_runs": 2},
        ),
        patch(
            "simulate.views.canvas_views._run_montecarlo",
            return_value=({"outcomes": [1, 2]}, {"mean": 1.5}),
        ),
    ):
        outcome = execute_canvas_run_async.run(str(run.id))

    run.refresh_from_db()
    assert outcome["status"] == "completed"
    assert run.status == "completed"
    assert run.progress == 100
    assert UsageEvent.objects.filter(
        organization=organization,
        metric=UsageEvent.Metric.SIMULATION_RUNTIME,
    ).exists()
    resources = ResourceUsage.objects.filter(organization=organization)
    assert set(resources.values_list("resource", flat=True)) == {"CPU_SIMULATION", "STORAGE"}
    assert all(resource.cost_amount is None for resource in resources)
