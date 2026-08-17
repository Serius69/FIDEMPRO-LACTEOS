import pytest

from modeling.diagrams import build_diagrams
from modeling.schema import empty_model_spec


def test_diagrams_are_derived_from_bom_process_causal_stock_flow_and_finance():
    spec = empty_model_spec(name="Panadería", sector="bakery")
    spec["products"] = [{"id": "bread", "name": "Pan"}]
    spec["materials"] = [{"id": "flour", "name": "Harina"}]
    spec["boms"] = [{"id": "bread-bom", "product_id": "bread", "items": [{"component_id": "flour", "quantity": 1, "unit": "kg"}]}]
    spec["resources"] = [{"id": "oven", "name": "Horno"}]
    spec["processes"] = [{"id": "bake", "steps": [{"id": "mix", "name": "Mezclar", "resource_id": "oven"}]}]
    spec["stocks"] = [{"id": "inventory", "name": "Inventario", "unit": "unit"}]
    spec["flows"] = [{"id": "sales", "name": "Ventas", "source_id": "inventory", "unit": "unit"}]
    spec["variables"] = [{"id": "demand", "name": "Demanda"}]
    spec["causal_links"] = [{"id": "link", "source_id": "demand", "target_id": "sales", "polarity": "positive"}]
    spec["revenues"] = [{"id": "revenue", "name": "Ingresos", "inputs": ["demand"]}]
    spec["variables"][0]["position"] = {"x": 120, "y": 80}

    diagrams = build_diagrams(spec)

    assert diagrams["bom"]["edges"][0]["relation"] == "CONTAINS"
    assert diagrams["process"]["edges"][0]["relation"] == "USES_RESOURCE"
    assert diagrams["causal"]["edges"][0]["polarity"] == "positive"
    assert {edge["relation"] for edge in diagrams["stock_flow"]["edges"]} == {"OUTFLOW"}
    assert diagrams["finance"]["edges"][0]["relation"] == "DRIVES"


def test_diagram_nodes_preserve_versioned_layout_positions():
    spec = empty_model_spec(name="Positioned")
    spec["stocks"] = [{"id": "cash", "name": "Caja", "position": {"x": 44, "y": 55}}]
    stock = build_diagrams(spec)["stock_flow"]["nodes"][0]
    assert stock["position"] == {"x": 44, "y": 55}


@pytest.mark.django_db
def test_diagrams_endpoint_is_owner_scoped(client):
    from django.contrib.auth import get_user_model
    from django.urls import reverse
    from business.models import Business
    from modeling.models import BusinessModelDefinition
    from modeling.services import create_model_version

    owner = get_user_model().objects.create_user(username="diagram-owner", password="password")
    other = get_user_model().objects.create_user(username="diagram-other", password="password")
    business = Business.objects.create(name="Diagram business", location="La Paz", fk_user=owner)
    definition = BusinessModelDefinition.objects.create(business=business, name="Diagram model", created_by=owner)
    create_model_version(definition, empty_model_spec(name="Diagram model"), user=owner)

    client.force_login(owner)
    response = client.get(reverse("modeling:model-diagrams", kwargs={"model_id": definition.id}))
    assert response.status_code == 200
    assert set(response.json()["diagrams"]) == {"bom", "process", "causal", "stock_flow", "resources", "finance"}

    client.force_login(other)
    assert client.get(reverse("modeling:model-diagrams", kwargs={"model_id": definition.id})).status_code == 404
