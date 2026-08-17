from __future__ import annotations

from typing import Any

from django.db import transaction

from .models import BusinessModelDefinition, BusinessModelVersion
from .schema import SCHEMA_VERSION, model_hash, validate_model_spec


class ModelSpecError(ValueError):
    def __init__(self, validation: dict[str, Any]):
        self.validation = validation
        super().__init__("La especificación del modelo no es válida.")


def validate_and_normalize(spec: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    validation = validate_model_spec(spec)
    if not validation["valid"]:
        raise ModelSpecError(validation)
    normalized = dict(spec)
    normalized["schema_version"] = SCHEMA_VERSION
    return normalized, validation


@transaction.atomic
def create_model_version(
    definition: BusinessModelDefinition,
    spec: dict[str, Any],
    *,
    user,
    status: str = "validated",
) -> BusinessModelVersion:
    normalized, validation = validate_and_normalize(spec)
    # Serialize version allocation per definition.  Without a row lock, two
    # concurrent saves can both observe the same latest version and race into
    # the unique constraint, leaving callers with an opaque 500/retry.
    locked_definition = BusinessModelDefinition.objects.select_for_update().get(pk=definition.pk)
    latest = locked_definition.versions.order_by("-version").first()
    version = (latest.version + 1) if latest else 1
    parent = latest
    if latest and latest.status == "published":
        latest.status = "superseded"
        latest.save(update_fields=["status"])
    version_obj = BusinessModelVersion.objects.create(
        definition=locked_definition,
        version=version,
        schema_version=SCHEMA_VERSION,
        status=status,
        parent_version=parent,
        spec=normalized,
        content_hash=model_hash(normalized),
        validation=validation,
        created_by=user,
    )
    locked_definition.current_version = version_obj
    locked_definition.status = status if status in {"draft", "validated", "published", "archived"} else "draft"
    locked_definition.save(update_fields=["current_version", "status", "updated_at"])
    # Keep the caller's instance coherent as well; views/tests may continue
    # using the object they passed after the transactional write.
    definition.current_version = version_obj
    definition.status = locked_definition.status
    return version_obj


def serialize_version(version: BusinessModelVersion) -> dict[str, Any]:
    return {
        "id": str(version.id),
        "definition_id": str(version.definition_id),
        "version": version.version,
        "schema_version": version.schema_version,
        "status": version.status,
        "content_hash": version.content_hash,
        "spec": version.spec,
        "validation": version.validation,
        "created_at": version.created_at.isoformat(),
    }
