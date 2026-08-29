import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from modeling.schema import empty_model_spec

from tenancy.models import Subscription, UsageEvent
from tenancy.services import change_plan, ensure_default_organization, start_trial

pytestmark = pytest.mark.django_db


def test_signup_free_project_import_simulation_result_trial_upgrade_downgrade_export():
    account = get_user_model().objects.create_user(
        username="journey", password="test-password", email="journey@example.test"
    )
    organization = ensure_default_organization(account)
    client = Client()
    client.force_login(account)

    context = client.get("/api/subscription/context/")
    assert context.status_code == 200
    assert context.json()["subscription"]["effective_plan"] == "FREE"

    business = client.post(
        reverse("modeling:business-list"),
        data={"name": "Journey Business", "location": "La Paz", "sector": "retail"},
        content_type="application/json",
    )
    assert business.status_code == 201
    model = client.post(
        reverse("modeling:model-list-create"),
        data={
            "business_id": business.json()["business"]["id"],
            "name": "Journey Model",
            "spec": empty_model_spec(name="Journey Model", sector="retail"),
        },
        content_type="application/json",
    )
    assert model.status_code == 201
    model_id = model.json()["model"]["id"]

    second = client.post(
        reverse("modeling:model-list-create"),
        data={
            "business_id": business.json()["business"]["id"],
            "name": "Over quota",
            "spec": empty_model_spec(name="Over quota", sector="retail"),
        },
        content_type="application/json",
    )
    assert second.status_code == 403

    imported = client.post(
        reverse("modeling:data-import-create", args=[model_id]),
        data={"format": "json", "rows": [{"demand": 10}], "mapping": {}},
        content_type="application/json",
    )
    assert imported.status_code == 201

    simulated = client.post(
        reverse("modeling:model-simulate", args=[model_id]),
        data={"iterations": 2, "seed": 7}, content_type="application/json",
    )
    assert simulated.status_code == 202
    result = client.get(simulated.json()["status_url"])
    assert result.status_code == 200
    assert result.json()["status"] in {"completed", "failed"}

    trial = start_trial(organization, Subscription.Plan.PRO, duration_days=14)
    assert trial.effective_plan == "PRO"
    assert change_plan(organization, "GROWTH").effective_plan == "GROWTH"
    exported = client.get(reverse("modeling:model-export", args=[model_id]))
    assert exported.status_code == 200
    assert change_plan(organization, "FREE").effective_plan == "FREE"

    metrics = set(UsageEvent.objects.filter(organization=organization).values_list("metric", flat=True))
    assert {"PROJECT_CREATED", "DATASET_INGESTED", "DATASET_ROWS", "SIMULATION_RUN", "EXPORT"} <= metrics
