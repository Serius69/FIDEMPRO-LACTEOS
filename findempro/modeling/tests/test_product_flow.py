import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from business.models import Business

pytestmark = pytest.mark.django_db


def test_owner_can_complete_configure_validate_scenario_simulate_flow():
    user = get_user_model().objects.create_user(username="product-flow-owner", password="password")
    business = Business.objects.create(name="Panadería demo", location="Cochabamba", fk_user=user)
    client = Client()
    assert client.login(username="product-flow-owner", password="password")

    templates = client.get(reverse("modeling:template-list"))
    assert templates.status_code == 200
    assert templates.json()["templates"]

    spec = {
        "schema_version": "1.0",
        "metadata": {"name": "Panadería demo", "sector": "bakery", "horizon": 1, "provenance": "USER_ENTERED"},
        "variables": [{"id": "demand", "value": 2}, {"id": "price", "value": 10}],
        "parameters": [], "entities": [], "resources": [{"id": "oven", "name": "Horno", "capacity": 1}],
        "stocks": [], "flows": [], "products": [{"id": "bread", "name": "Pan"}],
        "materials": [{"id": "flour", "name": "Harina"}],
        "boms": [{"id": "bread-bom", "product_id": "bread", "items": [{"component_id": "flour", "quantity": 0.2, "unit": "kg", "waste_pct": 2}]}],
        "services": [], "processes": [{"id": "bake", "name": "Horneado", "steps": [{"id": "bake-step", "resource_id": "oven", "cycle_time": 1}]}],
        "demand": {}, "costs": [{"id": "fixed", "value": 4}], "revenues": [{"id": "sales", "expression": "demand * price"}],
        "constraints": [], "equations": [], "distributions": [], "causal_links": [], "scenarios": [], "outputs": [],
    }
    created = client.post(
        reverse("modeling:model-list-create"),
        data={"business_id": business.id, "name": "Panadería demo", "sector": "bakery", "spec": spec},
        content_type="application/json",
    )
    assert created.status_code == 201
    model_id = created.json()["model"]["id"]

    validation = client.post(reverse("modeling:model-validate", kwargs={"model_id": model_id}), data={"spec": spec}, content_type="application/json")
    assert validation.status_code == 200
    assert validation.json()["valid"] is True

    imported = client.post(
        reverse("modeling:data-import-create", kwargs={"model_id": model_id}),
        data={"format": "json", "rows": [{"demand": 2}], "mapping": {"demand": "demand"}},
        content_type="application/json",
    )
    assert imported.status_code == 201
    assert imported.json()["import"]["rows_imported"] == 1

    scenario = client.post(
        reverse("modeling:scenario-list-create", kwargs={"model_id": model_id}),
        data={"name": "Más demanda", "label": "CUSTOM", "changes": {"demand": 1}},
        content_type="application/json",
    )
    assert scenario.status_code == 201

    queued = client.post(
        reverse("modeling:model-simulate", kwargs={"model_id": model_id}),
        data={"iterations": 1, "seed": 42, "scenario_id": scenario.json()["scenario"]["id"]},
        content_type="application/json",
    )
    assert queued.status_code == 202
    completed = client.get(queued.json()["status_url"])
    assert completed.json()["status"] == "completed"
    assert completed.json()["result"]["summary"]["mean"] == 26.0
