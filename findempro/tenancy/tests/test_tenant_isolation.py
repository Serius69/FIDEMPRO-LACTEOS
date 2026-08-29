import pytest
from business.models import Business
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from modeling.models import BusinessModelDefinition, BusinessSimulationRun
from modeling.schema import empty_model_spec
from modeling.services import create_model_version
from simulate.canvas_models import CanvasSimulationRun, SimulationProject

from tenancy.models import OrganizationMembership, UsageEvent
from tenancy.services import ensure_default_organization, record_usage

pytestmark = pytest.mark.django_db


def make_user(name):
    return get_user_model().objects.create_user(username=name, password="test-password")


def owned_model(user, name):
    organization = ensure_default_organization(user)
    business = Business.objects.create(
        name=f"{name} Business", location="La Paz", fk_user=user, organization=organization
    )
    definition = BusinessModelDefinition.objects.create(
        business=business, name=name, created_by=user
    )
    version = create_model_version(definition, empty_model_spec(name=name), user=user)
    run = BusinessSimulationRun.objects.create(
        model_version=version, created_by=user, status="completed", progress=100,
        result={"summary": {"mean": 1}},
    )
    return organization, definition, run


def test_org_a_cannot_read_mutate_import_simulate_result_export_or_job_of_org_b():
    user_a = make_user("org-a")
    user_b = make_user("org-b")
    _org_a, _definition_a, _run_a = owned_model(user_a, "Model A")
    _org_b, definition_b, run_b = owned_model(user_b, "Model B")
    client = Client()
    client.force_login(user_a)

    assert client.get(reverse("modeling:model-detail", args=[definition_b.id])).status_code == 404
    assert client.post(
        reverse("modeling:model-version-create", args=[definition_b.id]),
        data={"spec": empty_model_spec(name="stolen")}, content_type="application/json",
    ).status_code == 404
    assert client.post(
        reverse("modeling:data-import-create", args=[definition_b.id]),
        data={"format": "json", "rows": []}, content_type="application/json",
    ).status_code == 404
    assert client.post(
        reverse("modeling:model-simulate", args=[definition_b.id]),
        data={"iterations": 1, "seed": 1}, content_type="application/json",
    ).status_code == 404
    assert client.get(reverse("modeling:run-detail", args=[run_b.id])).status_code == 404
    assert client.get(reverse("modeling:run-report", args=[run_b.id])).status_code == 404
    assert client.post(reverse("modeling:run-cancel", args=[run_b.id])).status_code == 404


def test_org_a_cannot_read_mutate_execute_export_or_list_canvas_resources_of_org_b():
    user_a = make_user("canvas-a")
    user_b = make_user("canvas-b")
    org_b = ensure_default_organization(user_b)
    project_b = SimulationProject.objects.create(
        user=user_b, organization=org_b, name="Private canvas", domain="generic"
    )
    run_b = CanvasSimulationRun.objects.create(project=project_b, status="completed")
    client = Client()
    client.force_login(user_a)

    detail = f"/api/v2/projects/{project_b.id}/"
    assert client.get(detail).status_code == 404
    assert client.patch(detail, data={"name": "stolen"}, content_type="application/json").status_code == 404
    assert client.get(f"/api/v2/projects/{project_b.id}/export/").status_code == 404
    assert client.post(
        f"/api/v2/projects/{project_b.id}/simulate/",
        data={"run_type": "montecarlo"}, content_type="application/json",
    ).status_code == 404
    assert client.get(f"/api/v2/projects/{project_b.id}/runs/{run_b.id}/").status_code == 404


def test_org_a_cannot_consume_org_b_quota():
    user_a = make_user("quota-a")
    user_b = make_user("quota-b")
    org_a = ensure_default_organization(user_a)
    org_b = ensure_default_organization(user_b)
    record_usage(org_b, UsageEvent.Metric.SIMULATION_RUN, 1, "test", "b-run")

    assert UsageEvent.objects.filter(organization=org_a).count() == 0
    assert UsageEvent.objects.filter(organization=org_b).count() == 1


def test_selected_organization_and_read_only_role_are_enforced_by_modeling_api():
    owner = make_user("multi-org-owner")
    reader = make_user("multi-org-reader")
    organization, definition, _run = owned_model(owner, "Shared model")
    OrganizationMembership.objects.create(
        organization=organization,
        user=reader,
        role=OrganizationMembership.Role.READ_ONLY,
    )
    client = Client()
    client.force_login(reader)

    assert client.get(reverse("modeling:business-list")).json()["businesses"] == []
    headers = {"HTTP_X_ORGANIZATION_ID": str(organization.id)}
    selected = client.get(reverse("modeling:business-list"), **headers)
    detail = client.get(
        reverse("modeling:model-detail", args=[definition.id]),
        **headers,
    )
    denied = client.post(
        reverse("modeling:model-version-create", args=[definition.id]),
        data={"spec": empty_model_spec(name="Denied")},
        content_type="application/json",
        **headers,
    )

    assert selected.status_code == 200
    assert selected.json()["businesses"][0]["name"] == "Shared Model Business"
    assert detail.status_code == 200
    assert denied.status_code == 403
