import json

import pytest
from business.models import Business
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from modeling.models import BusinessModelDefinition, BusinessSimulationRun
from modeling.schema import empty_model_spec
from modeling.services import create_model_version

pytestmark = pytest.mark.django_db


def test_failed_task_persists_safe_error_envelope_without_internal_message(monkeypatch):
    from modeling.models import BusinessSimulationRun
    from modeling.tasks import run_business_simulation

    owner = get_user_model().objects.create_user(username="safe-error-owner", password="password")
    business = Business.objects.create(name="Safe error business", location="La Paz", fk_user=owner)
    definition = BusinessModelDefinition.objects.create(business=business, name="Safe error model", created_by=owner)
    version = create_model_version(definition, empty_model_spec(name="Safe error model"), user=owner)
    run = BusinessSimulationRun.objects.create(model_version=version, engine="monte_carlo", created_by=owner)

    def explode(*args, **kwargs):
        raise RuntimeError("database password=secret")

    monkeypatch.setattr("modeling.tasks.run_engine", explode)
    with pytest.raises(RuntimeError):
        run_business_simulation.run(str(run.id))

    run.refresh_from_db()
    detail = json.loads(run.error)
    assert run.status == "failed"
    assert detail["code"] == "simulation_failed"
    assert "secret" not in run.error
    client = Client()
    client.force_login(owner)
    payload = client.get(reverse("modeling:run-detail", kwargs={"run_id": run.id})).json()
    assert payload["error"]["how_to_fix"]
    assert "secret" not in json.dumps(payload)


def test_simulation_timeout_persists_failed_lifecycle_and_safe_error(monkeypatch):
    from modeling.tasks import run_business_simulation

    owner = get_user_model().objects.create_user(username="timeout-owner", password="password")
    business = Business.objects.create(name="Timeout business", location="La Paz", fk_user=owner)
    definition = BusinessModelDefinition.objects.create(
        business=business, name="Timeout model", created_by=owner
    )
    version = create_model_version(definition, empty_model_spec(name="Timeout model"), user=owner)
    run = BusinessSimulationRun.objects.create(
        model_version=version, engine="monte_carlo", created_by=owner
    )

    def time_out(*args, **kwargs):
        raise TimeoutError("provider/internal detail must not leak")

    monkeypatch.setattr("modeling.tasks.run_engine", time_out)
    with pytest.raises(TimeoutError):
        run_business_simulation.run(str(run.id))

    run.refresh_from_db()
    assert run.status == "failed"
    assert run.finished_at is not None
    assert "internal detail" not in run.error


def test_model_simulation_persists_reproducible_result():
    user = get_user_model().objects.create_user(username="sim-owner", password="password")
    business = Business.objects.create(name="Retail", location="La Paz", fk_user=user)
    definition = BusinessModelDefinition.objects.create(business=business, name="Retail twin", created_by=user)
    spec = empty_model_spec(name="Retail twin", sector="retail")
    spec["metadata"]["horizon"] = 1
    spec["variables"] = [{"id": "price", "value": 10}, {"id": "sales", "value": 2}]
    spec["revenues"] = [{"id": "sales-revenue", "expression": "price * sales"}]
    create_model_version(definition, spec, user=user)
    client = Client()
    client.force_login(user)

    enqueue = client.post(reverse("modeling:model-simulate", kwargs={"model_id": definition.id}), data={"iterations": 5, "seed": 7}, content_type="application/json")

    assert enqueue.status_code == 202
    run = client.get(enqueue.json()["status_url"])
    assert run.status_code == 200
    assert run.json()["status"] == "completed"
    assert run.json()["result"]["summary"]["mean"] == 20.0
    traceability = run.json()["result"]["traceability"]
    assert traceability["content_hash"] == definition.current_version.content_hash
    assert traceability["model_version"] == 1
    assert traceability["seed"] == 7


def test_model_simulation_applies_versioned_scenario_changes():
    user = get_user_model().objects.create_user(username="scenario-sim-owner", password="password")
    business = Business.objects.create(name="Scenario retail", location="La Paz", fk_user=user)
    definition = BusinessModelDefinition.objects.create(business=business, name="Scenario twin", created_by=user)
    spec = empty_model_spec(name="Scenario twin", sector="retail")
    spec["metadata"]["horizon"] = 1
    spec["variables"] = [{"id": "demand", "value": 2}, {"id": "price", "value": 10}]
    spec["revenues"] = [{"id": "revenue", "expression": "demand * price"}]
    version = create_model_version(definition, spec, user=user)
    client = Client()
    client.force_login(user)
    scenario_response = client.post(
        reverse("modeling:scenario-list-create", kwargs={"model_id": definition.id}),
        data={"name": "Demand +3", "label": "CUSTOM", "changes": {"demand": 3}},
        content_type="application/json",
    )
    scenario_id = scenario_response.json()["scenario"]["id"]

    enqueue = client.post(
        reverse("modeling:model-simulate", kwargs={"model_id": definition.id}),
        data={"iterations": 1, "seed": 9, "scenario_id": scenario_id},
        content_type="application/json",
    )

    assert enqueue.status_code == 202
    assert client.get(enqueue.json()["status_url"]).json()["result"]["summary"]["mean"] == 50.0
    assert version.scenarios.count() == 1


def test_run_history_is_owner_scoped_and_contains_uncertainty_summary():
    owner = get_user_model().objects.create_user(username="history-owner", password="password")
    other = get_user_model().objects.create_user(username="history-other", password="password")
    business = Business.objects.create(name="History retail", location="La Paz", fk_user=owner)
    definition = BusinessModelDefinition.objects.create(business=business, name="History model", created_by=owner)
    spec = empty_model_spec(name="History model")
    spec["metadata"]["horizon"] = 1
    spec["variables"] = [{"id": "price", "value": 10}, {"id": "sales", "value": 2}]
    spec["revenues"] = [{"id": "revenue", "expression": "price * sales"}]
    create_model_version(definition, spec, user=owner)
    owner_client = Client()
    owner_client.force_login(owner)
    enqueue = owner_client.post(reverse("modeling:model-simulate", kwargs={"model_id": definition.id}), data={"iterations": 2, "seed": 11}, content_type="application/json")
    assert enqueue.status_code == 202
    assert owner_client.get(enqueue.json()["status_url"]).json()["status"] == "completed"

    history = owner_client.get(reverse("modeling:run-list"))
    assert history.status_code == 200
    assert history.json()["runs"][0]["summary"]["p5"] == 20.0
    assert history.json()["runs"][0]["traceability"]["seed"] == 11
    assert history.json()["runs"][0]["traceability"]["content_hash"] == definition.current_version.content_hash
    other_client = Client()
    other_client.force_login(other)
    assert other_client.get(reverse("modeling:run-list")).json()["runs"] == []


def test_run_access_follows_business_owner_boundary_not_incidental_creator():
    owner = get_user_model().objects.create_user(username="run-business-owner", password="password")
    creator = get_user_model().objects.create_user(username="run-creator", password="password")
    business = Business.objects.create(name="Transferred business", location="La Paz", fk_user=owner)
    definition = BusinessModelDefinition.objects.create(business=business, name="Transferred model", created_by=owner)
    version = create_model_version(definition, empty_model_spec(name="Transferred model"), user=owner)
    from modeling.models import BusinessSimulationRun
    run = BusinessSimulationRun.objects.create(
        model_version=version, engine="monte_carlo", created_by=creator, status="completed",
        result={"summary": {"mean": 1}},
    )

    owner_client = Client()
    owner_client.force_login(owner)
    assert owner_client.get(reverse("modeling:run-detail", kwargs={"run_id": run.id})).status_code == 200
    assert owner_client.get(reverse("modeling:run-list")).json()["runs"][0]["id"] == str(run.id)

    creator_client = Client()
    creator_client.force_login(creator)
    assert creator_client.get(reverse("modeling:run-detail", kwargs={"run_id": run.id})).status_code == 404


def test_completed_run_report_contains_traceability_and_limitation():
    user = get_user_model().objects.create_user(username="report-owner", password="password")
    business = Business.objects.create(name="Report retail", location="La Paz", fk_user=user)
    definition = BusinessModelDefinition.objects.create(business=business, name="Report model", created_by=user)
    spec = empty_model_spec(name="Report model")
    spec["metadata"]["horizon"] = 1
    spec["variables"] = [{"id": "price", "value": 10}, {"id": "sales", "value": 2}]
    spec["revenues"] = [{"id": "revenue", "expression": "price * sales"}]
    create_model_version(definition, spec, user=user)
    client = Client()
    client.force_login(user)
    enqueue = client.post(reverse("modeling:model-simulate", kwargs={"model_id": definition.id}), data={"iterations": 1, "seed": 17}, content_type="application/json")
    run_id = enqueue.json()["run_id"]
    assert client.get(enqueue.json()["status_url"]).json()["status"] == "completed"

    report = client.get(reverse("modeling:run-report", kwargs={"run_id": run_id}))

    assert report.status_code == 200
    assert report["Content-Type"].startswith("text/csv")
    assert b"model_hash" in report.content
    assert b"schema_version" in report.content
    assert b"iterations" in report.content
    assert b"conditional" in report.content


def test_failed_run_cannot_be_exported_and_remains_coherent():
    user = get_user_model().objects.create_user(username="failed-export-owner", password="password")
    business = Business.objects.create(name="Failed export", location="La Paz", fk_user=user)
    definition = BusinessModelDefinition.objects.create(
        business=business, name="Failed export model", created_by=user
    )
    version = create_model_version(definition, empty_model_spec(name="Failed export model"), user=user)
    run = BusinessSimulationRun.objects.create(
        model_version=version, created_by=user, status="failed", error='{"code":"simulation_failed"}'
    )
    client = Client()
    client.force_login(user)

    response = client.get(reverse("modeling:run-report", kwargs={"run_id": run.id}))

    assert response.status_code == 404
    run.refresh_from_db()
    assert run.status == "failed"
    assert run.result == {}


def test_csv_report_neutralizes_spreadsheet_formulas_from_user_names():
    user = get_user_model().objects.create_user(username="csv-safe-owner", password="password")
    business = Business.objects.create(
        name="=HYPERLINK(\"https://invalid.example\")",
        location="La Paz",
        fk_user=user,
    )
    definition = BusinessModelDefinition.objects.create(
        business=business,
        name="+SUM(1,1)",
        created_by=user,
    )
    version = create_model_version(definition, empty_model_spec(name="CSV safe"), user=user)
    run = BusinessSimulationRun.objects.create(
        model_version=version,
        created_by=user,
        status="completed",
        result={"summary": {"mean": 1}},
    )
    client = Client()
    client.force_login(user)

    report = client.get(reverse("modeling:run-report", kwargs={"run_id": run.id}))

    assert report.status_code == 200
    assert b"'=Hyperlink" in report.content
    assert b"'+SUM" in report.content


def test_sensitivity_endpoint_is_owner_scoped_and_seeded():
    user = get_user_model().objects.create_user(username="sensitivity-owner", password="password")
    business = Business.objects.create(name="Sensitivity retail", location="La Paz", fk_user=user)
    definition = BusinessModelDefinition.objects.create(business=business, name="Sensitivity model", created_by=user)
    spec = empty_model_spec(name="Sensitivity model")
    spec["metadata"]["horizon"] = 1
    spec["variables"] = [{"id": "price", "value": 10}, {"id": "sales", "value": 2}]
    spec["revenues"] = [{"id": "revenue", "expression": "price * sales"}]
    version = create_model_version(definition, spec, user=user)
    client = Client()
    client.force_login(user)

    response = client.post(
        reverse("modeling:model-sensitivity", kwargs={"model_id": definition.id}),
        data={"changes": {"price": 1}, "iterations": 10, "seed": 7},
        content_type="application/json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["content_hash"] == version.content_hash
    assert payload["result"]["factors"][0]["variable"] == "price"


def test_scenario_rejects_unknown_or_non_finite_changes():
    user = get_user_model().objects.create_user(username="scenario-validation-owner", password="password")
    business = Business.objects.create(name="Scenario validation", location="La Paz", fk_user=user)
    definition = BusinessModelDefinition.objects.create(business=business, name="Scenario validation model", created_by=user)
    spec = empty_model_spec(name="Scenario validation model")
    spec["variables"] = [{"id": "demand", "value": 2}]
    create_model_version(definition, spec, user=user)
    client = Client()
    client.force_login(user)
    url = reverse("modeling:scenario-list-create", kwargs={"model_id": definition.id})

    unknown = client.post(url, data={"name": "Unknown", "changes": {"not_in_model": 1}}, content_type="application/json")
    non_finite = client.post(url, data={"name": "NaN", "changes": {"demand": float("nan")}}, content_type="application/json")

    assert unknown.status_code == 400
    assert non_finite.status_code == 400


def test_simulation_and_sensitivity_reject_malformed_parameters_without_500():
    user = get_user_model().objects.create_user(username="parameter-validation-owner", password="password")
    business = Business.objects.create(name="Parameter validation", location="La Paz", fk_user=user)
    definition = BusinessModelDefinition.objects.create(business=business, name="Parameter model", created_by=user)
    spec = empty_model_spec(name="Parameter model")
    create_model_version(definition, spec, user=user)
    client = Client()
    client.force_login(user)

    simulate = client.post(reverse("modeling:model-simulate", kwargs={"model_id": definition.id}), data={"iterations": "not-an-int"}, content_type="application/json")
    bad_seed = client.post(reverse("modeling:model-simulate", kwargs={"model_id": definition.id}), data={"seed": -1}, content_type="application/json")
    sensitivity = client.post(reverse("modeling:model-sensitivity", kwargs={"model_id": definition.id}), data={"iterations": 1.5, "changes": {}}, content_type="application/json")
    malformed = client.post(reverse("modeling:model-simulate", kwargs={"model_id": definition.id}), data="{", content_type="application/json")

    assert [response.status_code for response in (simulate, bad_seed, sensitivity, malformed)] == [400, 400, 400, 400]


def test_completed_runs_can_be_compared_with_owner_and_version_guards():
    owner = get_user_model().objects.create_user(username="compare-owner", password="password")
    other = get_user_model().objects.create_user(username="compare-other", password="password")
    business = Business.objects.create(name="Compare business", location="La Paz", fk_user=owner)
    definition = BusinessModelDefinition.objects.create(business=business, name="Compare model", created_by=owner)
    spec = empty_model_spec(name="Compare model")
    spec["metadata"]["horizon"] = 1
    spec["variables"] = [{"id": "price", "value": 10}, {"id": "sales", "value": 2}]
    spec["revenues"] = [{"id": "revenue", "expression": "price * sales"}]
    create_model_version(definition, spec, user=owner)
    client = Client()
    client.force_login(owner)
    first = client.post(reverse("modeling:model-simulate", kwargs={"model_id": definition.id}), data={"iterations": 1, "seed": 1}, content_type="application/json")
    second = client.post(reverse("modeling:model-simulate", kwargs={"model_id": definition.id}), data={"iterations": 1, "seed": 2}, content_type="application/json")
    first_id, second_id = first.json()["run_id"], second.json()["run_id"]
    assert client.get(first.json()["status_url"]).json()["status"] == "completed"
    assert client.get(second.json()["status_url"]).json()["status"] == "completed"
    first_run = BusinessSimulationRun.objects.get(id=first_id)
    second_run = BusinessSimulationRun.objects.get(id=second_id)
    first_run.result["summary"].update({"mean_unmet_demand": 3.0, "mean_stock_service_level": 0.4})
    second_run.result["summary"].update({"mean_unmet_demand": 1.0, "mean_stock_service_level": 0.8})
    first_run.save(update_fields=["result"])
    second_run.save(update_fields=["result"])

    comparison = client.get(reverse("modeling:run-compare") + f"?ids={first_id},{second_id}")
    assert comparison.status_code == 200
    assert comparison.json()["baseline_run_id"] == first_id
    assert comparison.json()["comparisons"][1]["delta"]["mean"] == 0
    assert comparison.json()["comparisons"][1]["delta"]["mean_unmet_demand"] == -2.0
    assert comparison.json()["comparisons"][1]["delta"]["mean_stock_service_level"] == pytest.approx(0.4)
    client.force_login(other)
    assert client.get(reverse("modeling:run-compare") + f"?ids={first_id},{second_id}").status_code == 404


def test_simulation_api_selects_engine_and_rejects_unknown_engine():
    user = get_user_model().objects.create_user(username="engine-api-owner", password="password")
    business = Business.objects.create(name="Engine business", location="La Paz", fk_user=user)
    definition = BusinessModelDefinition.objects.create(business=business, name="Engine model", created_by=user)
    spec = empty_model_spec(name="Engine model")
    spec["metadata"]["horizon"] = 1
    spec["demand"] = {"arrivals_per_period": 2}
    spec["resources"] = [{"id": "worker", "capacity": 1}]
    spec["processes"] = [{"id": "service", "steps": [{"id": "step", "resource_id": "worker", "cycle_time": 1}]}]
    create_model_version(definition, spec, user=user)
    client = Client()
    client.force_login(user)

    invalid = client.post(reverse("modeling:model-simulate", kwargs={"model_id": definition.id}), data={"engine": "unknown"}, content_type="application/json")
    queued = client.post(reverse("modeling:model-simulate", kwargs={"model_id": definition.id}), data={"engine": "discrete_event", "seed": 3}, content_type="application/json")

    assert invalid.status_code == 400
    assert queued.status_code == 202
    result = client.get(queued.json()["status_url"])
    assert result.json()["status"] == "completed"
    assert result.json()["result"]["engine"] == "discrete_event"


def test_queued_run_can_be_cancelled_and_task_does_not_complete_it():
    from django.utils import timezone

    from modeling.models import BusinessSimulationRun
    from modeling.tasks import run_business_simulation

    owner = get_user_model().objects.create_user(username="cancel-owner", password="password")
    business = Business.objects.create(name="Cancel business", location="La Paz", fk_user=owner)
    definition = BusinessModelDefinition.objects.create(business=business, name="Cancel model", created_by=owner)
    version = create_model_version(definition, empty_model_spec(name="Cancel model"), user=owner)
    run = BusinessSimulationRun.objects.create(model_version=version, engine="monte_carlo", created_by=owner, created_at=timezone.now())
    client = Client()
    client.force_login(owner)

    response = client.post(reverse("modeling:run-cancel", kwargs={"run_id": run.id}))
    assert response.status_code == 200
    run.refresh_from_db()
    assert run.status == "cancelled"
    assert run_business_simulation.run(str(run.id))["status"] == "cancelled"
    run.refresh_from_db()
    assert run.status == "cancelled"


def test_model_simulation_enforces_configurable_active_run_limit(settings):
    from modeling.models import BusinessSimulationRun

    owner = get_user_model().objects.create_user(username="capacity-owner", password="password")
    business = Business.objects.create(name="Capacity business", location="La Paz", fk_user=owner)
    definition = BusinessModelDefinition.objects.create(business=business, name="Capacity model", created_by=owner)
    version = create_model_version(definition, empty_model_spec(name="Capacity model"), user=owner)
    settings.MODELING_MAX_ACTIVE_RUNS = 1
    BusinessSimulationRun.objects.create(model_version=version, engine="monte_carlo", created_by=owner, status="queued")

    client = Client()
    client.force_login(owner)
    response = client.post(
        reverse("modeling:model-simulate", kwargs={"model_id": definition.id}),
        data={"iterations": 1, "seed": 1},
        content_type="application/json",
    )

    assert response.status_code == 429
    assert response.json()["error"] == "simulation_capacity_reached"
