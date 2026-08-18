import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings
from django.urls import reverse

from business.models import Business
from modeling.models import BusinessModelDefinition, BusinessModelTemplate
from modeling.schema import empty_model_spec
from modeling.services import create_model_version

pytestmark = pytest.mark.django_db


def make_user(username):
    return get_user_model().objects.create_user(username=username, password="test-password")


def make_business(user, name="Demo"):
    return Business.objects.create(name=name, location="Cochabamba", fk_user=user)


def test_model_version_is_hashed_and_immutable():
    user = make_user("model-owner")
    business = make_business(user)
    definition = BusinessModelDefinition.objects.create(business=business, name="Modelo", created_by=user)
    version = create_model_version(definition, empty_model_spec(name="Modelo"), user=user)

    assert version.version == 1
    assert len(version.content_hash) == 64
    version.spec["metadata"]["name"] = "mutated"
    with pytest.raises(ValidationError, match="inmutables"):
        version.save()


def test_model_version_identity_and_parent_are_immutable():
    user = make_user("version-identity-owner")
    business = make_business(user)
    definition = BusinessModelDefinition.objects.create(business=business, name="Modelo", created_by=user)
    version = create_model_version(definition, empty_model_spec(name="Modelo"), user=user)

    version.version = 99
    with pytest.raises(ValidationError, match="inmutables"):
        version.save()


def test_model_versions_form_a_parent_chain_and_advance_current_version():
    user = make_user("version-chain-owner")
    business = make_business(user, name="Version chain business")
    definition = BusinessModelDefinition.objects.create(business=business, name="Version chain", created_by=user)

    first = create_model_version(definition, empty_model_spec(name="Version chain"), user=user)
    second_spec = empty_model_spec(name="Version chain")
    second_spec["metadata"]["description"] = "second"
    second = create_model_version(definition, second_spec, user=user)

    definition.refresh_from_db()
    assert second.version == 2
    assert second.parent_version_id == first.id
    assert definition.current_version_id == second.id


def test_model_api_isolates_businesses_by_owner():
    owner = make_user("owner-a")
    other = make_user("owner-b")
    business = make_business(owner)
    client = Client()
    client.force_login(other)

    response = client.get(reverse("modeling:model-detail", kwargs={"model_id": "00000000-0000-0000-0000-000000000001"}))

    assert response.status_code == 404
    assert BusinessModelDefinition.objects.filter(business=business).count() == 0


def test_model_api_creates_valid_version_for_owned_business():
    user = make_user("api-owner")
    business = make_business(user)
    client = Client()
    client.force_login(user)
    spec = empty_model_spec(name="Tienda", sector="retail")

    response = client.post(
        reverse("modeling:model-list-create"),
        data={"business_id": business.id, "name": "Tienda", "spec": spec},
        content_type="application/json",
    )

    assert response.status_code == 201
    payload = response.json()["model"]
    assert payload["version"]["version"] == 1
    assert payload["version"]["content_hash"]


def test_model_export_contains_immutable_hash_and_is_owner_scoped():
    owner = make_user("export-owner")
    other = make_user("export-other")
    business = make_business(owner, name="Export business")
    definition = BusinessModelDefinition.objects.create(business=business, name="Export model", created_by=owner)
    version = create_model_version(definition, empty_model_spec(name="Export model"), user=owner)

    owner_client = Client()
    owner_client.force_login(owner)
    response = owner_client.get(reverse("modeling:model-export", kwargs={"model_id": definition.id}))

    assert response.status_code == 200
    assert response["Content-Disposition"].endswith(f"v{version.version}.json\"")
    payload = response.json()
    assert payload["content_hash"] == version.content_hash
    assert payload["spec"] == version.spec

    other_client = Client()
    other_client.force_login(other)
    assert other_client.get(reverse("modeling:model-export", kwargs={"model_id": definition.id})).status_code == 404


def test_templates_and_businesses_are_available_only_in_owner_scope():
    user = make_user("catalog-owner")
    make_business(user)
    client = Client()
    client.force_login(user)

    businesses = client.get(reverse("modeling:business-list"))
    templates = client.get(reverse("modeling:template-list"))

    assert businesses.status_code == 200
    assert len(businesses.json()["businesses"]) == 1
    assert templates.status_code == 200
    assert len(templates.json()["templates"]) >= 20


def test_owner_can_create_business_from_modeling_api_and_duplicate_is_rejected():
    user = make_user("business-create-owner")
    client = Client()
    client.force_login(user)

    response = client.post(
        reverse("modeling:business-list"),
        data={"name": "Mi Panadería", "location": "Cochabamba", "sector": "bakery"},
        content_type="application/json",
    )

    assert response.status_code == 201
    assert response.json()["business"]["type"] == Business.BusinessType.BAKERY
    duplicate = client.post(
        reverse("modeling:business-list"),
        data={"name": "Mi Panadería", "location": "Cochabamba", "sector": "bakery"},
        content_type="application/json",
    )
    assert duplicate.status_code == 409


def test_user_template_is_validated_and_hidden_from_other_owner():
    user = make_user("template-create-owner")
    other = make_user("template-other-owner")
    client = Client()
    client.force_login(user)
    response = client.post(
        reverse("modeling:template-list"),
        data={"name": "Mi modelo de taller", "slug": "mi-taller", "sector": "repair", "spec": empty_model_spec(name="Taller", sector="repair")},
        content_type="application/json",
    )
    assert response.status_code == 201
    assert BusinessModelTemplate.objects.get(slug="mi-taller").created_by == user

    client.force_login(other)
    visible = {item["slug"] for item in client.get(reverse("modeling:template-list")).json()["templates"]}
    assert "mi-taller" not in visible


def test_model_api_rejects_invalid_model_before_persisting_version():
    user = make_user("invalid-owner")
    business = make_business(user)
    client = Client()
    client.force_login(user)
    spec = empty_model_spec()
    spec["equations"] = [{"id": "bad", "expression": "__import__('os')"}]

    response = client.post(
        reverse("modeling:model-list-create"),
        data={"business_id": business.id, "name": "Invalid", "spec": spec},
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_model"
    assert BusinessModelDefinition.objects.filter(business=business).count() == 0


@override_settings(MODELING_MAX_MODEL_NODES=1)
def test_model_api_rejects_oversized_spec_before_persisting_definition():
    user = make_user("oversized-model-owner")
    business = make_business(user, name="Oversized model business")
    client = Client()
    client.force_login(user)
    spec = empty_model_spec(name="Oversized")
    spec["variables"] = [{"id": "first", "value": 1}, {"id": "second", "value": 2}]

    response = client.post(
        reverse("modeling:model-list-create"),
        data={"business_id": business.id, "name": "Oversized", "spec": spec},
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.json()["validation"]["errors"][0]["code"] == "model_node_limit"
    assert response.json()["validation"]["complexity"]["nodes"] == 2
    assert not BusinessModelDefinition.objects.filter(business=business).exists()


@override_settings(MODELING_MAX_EXPRESSION_LENGTH=8)
def test_model_api_rejects_formula_above_resource_limit():
    user = make_user("oversized-formula-owner")
    business = make_business(user, name="Oversized formula business")
    client = Client()
    client.force_login(user)
    spec = empty_model_spec(name="Oversized formula")
    spec["variables"] = [{"id": "first", "value": 1}, {"id": "second", "value": 2}]
    spec["equations"] = [{"id": "total", "expression": "first + second"}]

    response = client.post(
        reverse("modeling:model-list-create"),
        data={"business_id": business.id, "name": "Oversized formula", "spec": spec},
        content_type="application/json",
    )

    assert response.status_code == 400
    errors = response.json()["validation"]["errors"]
    assert any(error["code"] == "unsafe_expression" and "8 caracteres" in error["message"] for error in errors)
    assert not BusinessModelDefinition.objects.filter(business=business).exists()


def test_model_api_does_not_replace_an_explicit_empty_spec_with_a_starter_model():
    user = make_user("empty-spec-owner")
    business = make_business(user, name="Empty spec business")
    client = Client()
    client.force_login(user)

    response = client.post(
        reverse("modeling:model-list-create"),
        data={"business_id": business.id, "name": "Empty spec", "spec": {}},
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_model"
    assert not BusinessModelDefinition.objects.filter(business=business).exists()


def test_modeling_api_rejects_json_arrays_and_invalid_version_statuses():
    user = make_user("model-input-boundary")
    business = make_business(user, name="Input boundary")
    client = Client()
    client.force_login(user)

    array_body = client.post(
        reverse("modeling:model-list-create"), data="[]", content_type="application/json"
    )
    assert array_body.status_code == 400
    assert array_body.json()["error"] == "invalid_request"

    definition = BusinessModelDefinition.objects.create(business=business, name="Status model", created_by=user)
    create_model_version(definition, empty_model_spec(name="Status model"), user=user)
    invalid_status = client.post(
        reverse("modeling:model-version-create", kwargs={"model_id": definition.id}),
        data={"spec": empty_model_spec(name="Status model"), "status": "published-by-user"},
        content_type="application/json",
    )
    assert invalid_status.status_code == 400
    assert invalid_status.json()["error"] == "invalid_status"


def test_duplicate_scenario_returns_conflict_instead_of_server_error():
    user = make_user("scenario-conflict-owner")
    business = make_business(user, name="Scenario conflict")
    definition = BusinessModelDefinition.objects.create(business=business, name="Scenario model", created_by=user)
    spec = empty_model_spec(name="Scenario model")
    spec["variables"] = [{"id": "demand", "value": 1}]
    create_model_version(definition, spec, user=user)
    client = Client()
    client.force_login(user)
    payload = {"name": "BASE", "label": "BASE", "changes": {"demand": 1}}
    first = client.post(reverse("modeling:scenario-list-create", kwargs={"model_id": definition.id}), data=payload, content_type="application/json")
    second = client.post(reverse("modeling:scenario-list-create", kwargs={"model_id": definition.id}), data=payload, content_type="application/json")
    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["error"] == "scenario_exists"


def test_scenario_changes_are_version_scoped_and_owner_scoped():
    user = make_user("scenario-owner")
    business = make_business(user)
    definition = BusinessModelDefinition.objects.create(business=business, name="Scenario model", created_by=user)
    spec = empty_model_spec(name="Scenario model")
    spec["variables"] = [{"id": "costs.unit", "value": 0}]
    version = create_model_version(definition, spec, user=user)
    client = Client()
    client.force_login(user)

    response = client.post(
        reverse("modeling:scenario-list-create", kwargs={"model_id": definition.id}),
        data={"name": "Cost +10%", "label": "CUSTOM", "changes": {"costs.unit": 0.1}},
        content_type="application/json",
    )

    assert response.status_code == 201
    scenario = response.json()["scenario"]
    assert scenario["changes"] == {"costs.unit": 0.1}
    assert client.get(reverse("modeling:scenario-list-create", kwargs={"model_id": definition.id})).json()["scenarios"][0]["id"] == scenario["id"]
    assert version.scenarios.count() == 1


def test_json_import_creates_provenance_receipt_and_rejects_invalid_rows():
    user = make_user("import-owner")
    business = make_business(user)
    definition = BusinessModelDefinition.objects.create(business=business, name="Import model", created_by=user)
    spec = empty_model_spec(name="Import model")
    spec["variables"] = [{"id": "units", "value": 0}]
    create_model_version(definition, spec, user=user)
    client = Client()
    client.force_login(user)

    response = client.post(
        reverse("modeling:data-import-create", kwargs={"model_id": definition.id}),
        data={"format": "json", "rows": [{"demand": 2}, "bad-row"], "mapping": {"demand": "units"}},
        content_type="application/json",
    )

    assert response.status_code == 201
    receipt = response.json()["import"]
    assert receipt["status"] == "rejected"
    assert receipt["rows_imported"] == 1
    assert receipt["provenance"]["kind"] == "IMPORTED"


def test_import_is_owner_scoped_and_row_limit_is_enforced():
    owner = make_user("import-owner-limit")
    other = make_user("import-other")
    business = make_business(owner)
    definition = BusinessModelDefinition.objects.create(business=business, name="Bounded import", created_by=owner)
    create_model_version(definition, empty_model_spec(name="Bounded import"), user=owner)
    client = Client()
    client.force_login(other)

    forbidden = client.post(
        reverse("modeling:data-import-create", kwargs={"model_id": definition.id}),
        data={"format": "json", "rows": [{"value": 1}]},
        content_type="application/json",
    )
    assert forbidden.status_code == 404

    client.force_login(owner)
    limited = client.post(
        reverse("modeling:data-import-create", kwargs={"model_id": definition.id}),
        data={"format": "json", "rows": [{"value": 1}] * 10_001},
        content_type="application/json",
    )
    assert limited.status_code == 400
    assert limited.json()["error"] == "too_many_rows"


def test_csv_import_preserves_mapping_in_receipt():
    user = make_user("csv-import-owner")
    business = make_business(user)
    definition = BusinessModelDefinition.objects.create(business=business, name="CSV model", created_by=user)
    spec = empty_model_spec(name="CSV model")
    spec["variables"] = [{"id": "units", "value": 0}]
    create_model_version(definition, spec, user=user)
    client = Client()
    client.force_login(user)
    upload = SimpleUploadedFile("sales.csv", b"demand,price\n3,10\n", content_type="text/csv")

    response = client.post(
        reverse("modeling:data-import-create", kwargs={"model_id": definition.id}),
        data={"file": upload, "format": "csv", "mapping": '{"demand":"units"}'},
    )

    assert response.status_code == 201
    receipt = response.json()["import"]
    assert receipt["rows_imported"] == 1
    assert BusinessModelDefinition.objects.get(id=definition.id).current_version.data_imports.get().mapping == {"demand": "units"}


def test_invalid_xlsx_archive_returns_controlled_import_error():
    user = make_user("invalid-xlsx-owner")
    business = make_business(user)
    definition = BusinessModelDefinition.objects.create(business=business, name="Invalid XLSX model", created_by=user)
    spec = empty_model_spec(name="Invalid XLSX model")
    spec["variables"] = [{"id": "units", "value": 0}]
    create_model_version(definition, spec, user=user)
    client = Client()
    client.force_login(user)
    upload = SimpleUploadedFile("broken.xlsx", b"not a zip archive", content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    response = client.post(
        reverse("modeling:data-import-create", kwargs={"model_id": definition.id}),
        data={"file": upload, "format": "xlsx", "mapping": '{"units":"units"}'},
    )

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_import"


def test_import_preview_validates_mapping_without_persisting_receipt():
    user = make_user("preview-import-owner")
    business = make_business(user)
    definition = BusinessModelDefinition.objects.create(business=business, name="Preview model", created_by=user)
    spec = empty_model_spec(name="Preview model")
    spec["variables"] = [{"id": "demand", "value": 0}]
    create_model_version(definition, spec, user=user)
    client = Client()
    client.force_login(user)

    response = client.post(reverse("modeling:data-import-create", kwargs={"model_id": definition.id}), data={"format": "json", "preview": True, "rows": [{"units": 3}, "bad"], "mapping": {"units": "demand"}}, content_type="application/json")

    assert response.status_code == 200
    assert response.json()["rows_total"] == 2
    assert response.json()["preview"] == [{"units": 3}]
    assert definition.current_version.data_imports.count() == 0


def test_import_rejects_missing_and_non_finite_mapped_values_per_row():
    user = make_user("import-value-validation")
    business = make_business(user)
    definition = BusinessModelDefinition.objects.create(business=business, name="Import values", created_by=user)
    spec = empty_model_spec(name="Import values")
    spec["variables"] = [{"id": "units", "value": 0}]
    create_model_version(definition, spec, user=user)
    client = Client()
    client.force_login(user)

    response = client.post(
        reverse("modeling:data-import-create", kwargs={"model_id": definition.id}),
        data={"format": "json", "rows": [{"source": "3"}, {"source": "NaN"}, {}], "mapping": {"source": "units"}},
        content_type="application/json",
    )

    assert response.status_code == 201
    payload = response.json()["import"]
    assert payload["status"] == "rejected"
    assert payload["rows_imported"] == 1
    assert len(payload["error_rows"]) == 2
