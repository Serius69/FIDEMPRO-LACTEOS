from __future__ import annotations

import csv
import io
import json
import math
import uuid
import zipfile
from itertools import islice

from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_GET, require_http_methods

from business.models import Business

from .models import BusinessDataImport, BusinessModelDefinition, BusinessModelTemplate, BusinessModelVersion, BusinessScenario, BusinessSimulationRun
from .diagrams import build_diagrams
from .engine import ModelCompileError, SUPPORTED_ENGINES, validate_scenario_changes
from .errors import decode_error
from .schema import empty_model_spec, validate_model_spec
from .services import ModelSpecError, create_model_version, serialize_version
from .statistics import DistributionFitError, fit_distributions
from .templates import SECTOR_TEMPLATES, starter_spec
from tenancy.models import UsageEvent
from tenancy.abuse import expensive_operation
from tenancy.services import (
    enforce_monthly_usage,
    enforce_quota,
    get_request_organization,
    record_resource_usage,
    record_usage,
    require_entitlement,
    require_write,
)


# The legacy Business table stores a stable integer type.  The modeling DSL
# remains open-ended; this mapping only gives the existing account model a
# sensible classification when a user creates a company from the new UI.
BUSINESS_TYPE_BY_SECTOR = {
    "dairy": Business.BusinessType.DAIRY,
    "agriculture": Business.BusinessType.AGRICULTURE,
    "bakery": Business.BusinessType.BAKERY,
    "food-production": Business.BusinessType.FOOD_MANUFACTURING,
    "manufacturing": Business.BusinessType.MANUFACTURING,
    "grocery": Business.BusinessType.GROCERY,
    "retail": Business.BusinessType.RETAIL,
    "wholesale": Business.BusinessType.WHOLESALE,
    "restaurant": Business.BusinessType.HOSPITALITY,
    "tourism": Business.BusinessType.HOSPITALITY,
    "logistics": Business.BusinessType.LOGISTICS,
    "transport": Business.BusinessType.LOGISTICS,
    "health": Business.BusinessType.HEALTH_SERVICES,
    "education": Business.BusinessType.EDUCATION,
    "technology-services": Business.BusinessType.TECH,
    "professional-services": Business.BusinessType.SERVICES,
    "beauty": Business.BusinessType.SERVICES,
    "repair": Business.BusinessType.SERVICES,
    "construction": Business.BusinessType.CONSTRUCTION,
}


def _json_body(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON inválido: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ValueError("El cuerpo debe ser un objeto JSON.")
    return payload


def _simulation_parameters(body):
    if not isinstance(body, dict):
        raise ValueError("El cuerpo debe ser un objeto JSON.")
    raw_iterations = body.get("iterations", 100)
    if isinstance(raw_iterations, bool) or not isinstance(raw_iterations, int):
        raise ValueError("iterations debe ser un entero.")
    if raw_iterations < 1 or raw_iterations > 100_000:
        raise ValueError("iterations debe estar entre 1 y 100.000.")
    seed = body.get("seed")
    if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int) or seed < 0 or seed > 2**63 - 1):
        raise ValueError("seed debe ser un entero entre 0 y 2^63-1.")
    return raw_iterations, seed


def _reference_data_source(value):
    allowed = {choice for choice, _label in BusinessModelDefinition.ReferenceDataSource.choices}
    if value not in allowed:
        raise ValueError(
            "reference_data_source debe ser CUSTOMER_PRIVATE o KDP_GOVERNED."
        )
    return value


def _validate_import_rows(rows, mapping):
    """Validate mapped model inputs without mutating or executing imported data."""
    valid_rows = []
    error_rows = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            error_rows.append({"row": index, "error": "La fila debe ser un objeto."})
            continue
        row_errors = []
        for source in mapping:
            if source not in row or row[source] in (None, ""):
                row_errors.append(f"Falta la columna {source}.")
                continue
            raw_value = row[source]
            try:
                numeric_value = float(raw_value)
            except (TypeError, ValueError):
                numeric_value = math.nan
            if isinstance(raw_value, bool) or not math.isfinite(numeric_value):
                row_errors.append(f"{source} debe ser un número finito.")
        if row_errors:
            error_rows.append({"row": index, "error": " ".join(row_errors)})
        else:
            valid_rows.append(row)
    return valid_rows, error_rows


def _validate_xlsx_archive(file_object):
    """Reject compressed XLSX bombs before openpyxl expands their XML."""
    position = file_object.tell()
    try:
        with zipfile.ZipFile(file_object) as archive:
            entries = archive.infolist()
            if len(entries) > 1000 or sum(item.file_size for item in entries) > 20 * 1024 * 1024:
                raise ValueError("El XLSX expandido supera el límite seguro de 20 MB.")
    finally:
        file_object.seek(position)


def _csv_safe(value):
    """Prevent spreadsheet formula execution in user-controlled CSV cells."""
    text = "" if value is None else str(value)
    if text.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + text
    return text


def _owned_model(request, model_id):
    organization = get_request_organization(request)
    return get_object_or_404(
        BusinessModelDefinition.objects.select_related("business", "current_version"),
        id=model_id,
        business__organization=organization,
    )


def _organization_for_write(request):
    organization = get_request_organization(request)
    require_write(request.user, organization)
    return organization


@login_required
@require_http_methods(["GET", "POST"])
def template_list(request):
    if request.method == "POST":
        _organization_for_write(request)
        try:
            body = _json_body(request)
            name = str(body.get("name", "")).strip()
            sector = str(body.get("sector", "generic")).strip() or "generic"
            spec = body.get("spec")
            if len(name) < 3 or len(name) > 180:
                return JsonResponse({"error": "invalid_template", "message": "El nombre debe tener entre 3 y 180 caracteres."}, status=400)
            validation = validate_model_spec(spec)
            if not validation["valid"]:
                return JsonResponse({"error": "invalid_model", "validation": validation}, status=400)
            slug = slugify(str(body.get("slug") or name))[:100]
            if not slug:
                return JsonResponse({"error": "invalid_template", "message": "La plantilla necesita un slug válido."}, status=400)
            if BusinessModelTemplate.objects.filter(slug=slug).exists():
                return JsonResponse({"error": "template_exists", "message": "Ya existe una plantilla con ese slug."}, status=409)
            template = BusinessModelTemplate.objects.create(
                slug=slug,
                name=name,
                sector=sector,
                description=str(body.get("description", "")).strip(),
                spec=spec,
                provenance={"kind": "USER_ENTERED", "label": "Estructura creada por el usuario"},
                created_by=request.user,
                is_builtin=False,
                is_active=True,
            )
            return JsonResponse({"template": {"slug": template.slug, "name": template.name, "sector": template.sector, "description": template.description, "spec": template.spec, "provenance": template.provenance}}, status=201)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            return JsonResponse({"error": "invalid_request", "message": str(exc)}, status=400)

    templates = BusinessModelTemplate.objects.filter(is_active=True).filter(
        Q(is_builtin=True) | Q(created_by=request.user)
    ).order_by("name")
    if not templates.exists():
        return JsonResponse({"templates": [{"slug": slug, "name": name, "sector": slug, "description": "Punto de partida sintético y editable.", "spec": starter_spec(slug, name), "provenance": {"kind": "SIMULATED"}} for slug, name in SECTOR_TEMPLATES]})
    return JsonResponse({"templates": [
        {"slug": item.slug, "name": item.name, "sector": item.sector, "description": item.description, "spec": item.spec, "provenance": item.provenance}
        for item in templates
    ]})


@login_required
@require_http_methods(["GET", "POST"])
def business_list(request):
    organization = get_request_organization(request)
    if request.method == "POST":
        require_write(request.user, organization)
        try:
            body = _json_body(request)
            name = str(body.get("name", "")).strip()
            location = str(body.get("location", "")).strip()
            sector = str(body.get("sector", "generic")).strip().lower() or "generic"
            if len(name) < 3 or len(name) > 255:
                return JsonResponse({"error": "invalid_business", "message": "El nombre debe tener entre 3 y 255 caracteres."}, status=400)
            if not location or len(location) > 255:
                return JsonResponse({"error": "invalid_business", "message": "La ubicación es obligatoria."}, status=400)
            raw_type = body.get("type")
            business_type = int(raw_type) if raw_type is not None else BUSINESS_TYPE_BY_SECTOR.get(sector, Business.BusinessType.OTHER)
            valid_types = {choice for choice, _label in Business.BusinessType.choices}
            if business_type not in valid_types:
                return JsonResponse({"error": "invalid_business", "message": "Tipo de negocio no reconocido."}, status=400)
            if Business.objects.filter(organization=organization, is_active=True, name__iexact=name).exists():
                return JsonResponse({"error": "business_exists", "message": "Ya existe un negocio activo con ese nombre."}, status=409)
            business = Business(
                name=name,
                location=location,
                type=business_type,
                description=str(body.get("description", "")).strip()[:1000],
                fk_user=request.user,
                organization=organization,
            )
            business.full_clean()
            business.save()
            return JsonResponse({"business": {"id": business.id, "name": business.name, "sector": business.industry_sector, "type": business.type}}, status=201)
        except IntegrityError:
            return JsonResponse({"error": "business_exists", "message": "Ya existe un negocio activo con ese nombre."}, status=409)
        except ValidationError as exc:
            return JsonResponse({"error": "invalid_business", "message": exc.message_dict if hasattr(exc, "message_dict") else str(exc)}, status=400)
        except (TypeError, ValueError) as exc:
            return JsonResponse({"error": "invalid_business", "message": str(exc)}, status=400)

    businesses = Business.objects.filter(organization=organization, is_active=True).order_by("name")
    return JsonResponse({"businesses": [{"id": item.id, "name": item.name, "sector": item.industry_sector, "type": item.type} for item in businesses]})


@login_required
@require_http_methods(["GET", "POST"])
def model_list_create(request):
    organization = get_request_organization(request)
    if request.method == "GET":
        models = BusinessModelDefinition.objects.filter(business__organization=organization).select_related("business", "current_version")
        return JsonResponse({"models": [{
            "id": str(item.id), "name": item.name, "business_id": item.business_id,
            "business_name": item.business.name, "sector": item.sector, "status": item.status,
            "reference_data_source": item.reference_data_source,
            "current_version": item.current_version.version if item.current_version else None,
            "readiness": (item.current_version.validation or {}).get("readiness") if item.current_version else None,
        } for item in models]})
    try:
        require_write(request.user, organization)
        active_projects = BusinessModelDefinition.objects.filter(
            business__organization=organization,
            status__in=("draft", "validated", "published"),
        ).count()
        enforce_quota(organization, "active_projects", active_projects)
        body = _json_body(request)
        status = body.get("status", "validated")
        if status not in {choice for choice, _label in BusinessModelDefinition.STATUS_CHOICES}:
            return JsonResponse({"error": "invalid_status", "message": "Estado de modelo no reconocido."}, status=400)
        business = get_object_or_404(Business, id=body.get("business_id"), organization=organization)
        reference_data_source = _reference_data_source(
            body.get(
                "reference_data_source",
                BusinessModelDefinition.ReferenceDataSource.CUSTOMER_PRIVATE,
            )
        )
        # Omitted spec means "start from a template"; an explicitly supplied
        # empty/malformed spec must be validated and rejected rather than
        # silently replaced with a different business model.
        spec = body["spec"] if "spec" in body else empty_model_spec(
            name=body.get("name", "Modelo sin nombre"), sector=body.get("sector", "generic")
        )
        with transaction.atomic():
            definition = BusinessModelDefinition.objects.create(
                business=business, name=body.get("name") or spec.get("metadata", {}).get("name", "Modelo sin nombre"),
                description=body.get("description", ""), sector=body.get("sector") or spec.get("metadata", {}).get("sector", "generic"),
                reference_data_source=reference_data_source, created_by=request.user,
            )
            version = create_model_version(definition, spec, user=request.user, status=status)
        record_usage(
            organization, UsageEvent.Metric.PROJECT_CREATED, 1,
            "modeling.model", definition.id,
        )
        return JsonResponse({"model": {"id": str(definition.id), "name": definition.name, "business_id": definition.business_id, "sector": definition.sector, "status": definition.status, "reference_data_source": definition.reference_data_source, "version": serialize_version(version)}}, status=201)
    except ModelSpecError as exc:
        return JsonResponse({"error": "invalid_model", "validation": exc.validation}, status=400)
    except ValueError as exc:
        return JsonResponse({"error": "invalid_request", "message": str(exc)}, status=400)


@login_required
@require_GET
def model_detail(request, model_id):
    definition = _owned_model(request, model_id)
    return JsonResponse({
        "id": str(definition.id), "name": definition.name, "description": definition.description,
        "business_id": definition.business_id, "sector": definition.sector, "status": definition.status,
        "reference_data_source": definition.reference_data_source,
        "current_version": serialize_version(definition.current_version) if definition.current_version else None,
        "versions": [serialize_version(version) for version in definition.versions.all()],
    })


@login_required
@require_GET
@expensive_operation("export")
def model_export(request, model_id):
    """Download the immutable version envelope for backup/review/reuse."""
    definition = _owned_model(request, model_id)
    organization = get_request_organization(request)
    require_entitlement(organization, "exports", "modeling.model_export", model_id)
    enforce_monthly_usage(organization, "exports", UsageEvent.Metric.EXPORT)
    if not definition.current_version:
        return JsonResponse({"error": "model_has_no_version"}, status=404)
    version = definition.current_version
    payload = {
        "format": "findempro-business-model",
        "format_version": "1",
        "model_id": str(definition.id),
        "business_id": definition.business_id,
        "model_name": definition.name,
        "sector": definition.sector,
        "version": version.version,
        "schema_version": version.schema_version,
        "content_hash": version.content_hash,
        "validation": version.validation,
        "created_at": version.created_at.isoformat(),
        "spec": version.spec,
    }
    response = HttpResponse(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2), content_type="application/json; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="findempro-model-{definition.id}-v{version.version}.json"'
    record_usage(organization, UsageEvent.Metric.EXPORT, 1, "modeling.model_export", model_id)
    return response


@login_required
@require_http_methods(["POST"])
def model_validate(request, model_id):
    definition = _owned_model(request, model_id)
    try:
        body = _json_body(request)
    except ValueError as exc:
        return JsonResponse({"error": "invalid_request", "message": str(exc)}, status=400)
    spec = body.get("spec") if isinstance(body, dict) and "spec" in body else (definition.current_version.spec if definition.current_version else {})
    return JsonResponse(validate_model_spec(spec))


@login_required
@require_GET
def model_diagrams(request, model_id):
    definition = _owned_model(request, model_id)
    spec = definition.current_version.spec if definition.current_version else empty_model_spec(name=definition.name, sector=definition.sector)
    return JsonResponse({"model_id": str(definition.id), "version": definition.current_version.version if definition.current_version else None, "diagrams": build_diagrams(spec)})


@login_required
@require_http_methods(["POST"])
def model_version_create(request, model_id):
    definition = _owned_model(request, model_id)
    _organization_for_write(request)
    try:
        body = _json_body(request)
        status = body.get("status", "validated")
        if status not in {choice for choice, _label in BusinessModelVersion.STATUS_CHOICES}:
            return JsonResponse({"error": "invalid_status", "message": "Estado de versión no reconocido."}, status=400)
        version = create_model_version(definition, body.get("spec", {}), user=request.user, status=status)
        return JsonResponse({"version": serialize_version(version)}, status=201)
    except ModelSpecError as exc:
        return JsonResponse({"error": "invalid_model", "validation": exc.validation}, status=400)
    except ValueError as exc:
        return JsonResponse({"error": "invalid_request", "message": str(exc)}, status=400)


@login_required
@require_http_methods(["GET", "POST"])
def scenario_list_create(request, model_id):
    definition = _owned_model(request, model_id)
    if not definition.current_version:
        return JsonResponse({"error": "model_has_no_version"}, status=400)
    if request.method == "GET":
        scenarios = definition.current_version.scenarios.all()
        return JsonResponse({"scenarios": [{"id": str(item.id), "name": item.name, "label": item.label, "changes": item.changes} for item in scenarios]})
    _organization_for_write(request)
    try:
        body = _json_body(request)
    except ValueError as exc:
        return JsonResponse({"error": "invalid_request", "message": str(exc)}, status=400)
    if not isinstance(body, dict):
        return JsonResponse({"error": "invalid_request", "message": "El cuerpo debe ser un objeto JSON."}, status=400)
    changes = body.get("changes", {})
    try:
        validate_scenario_changes(definition.current_version.spec, changes)
    except ModelCompileError as exc:
        return JsonResponse({"error": "invalid_changes", "message": str(exc)}, status=400)
    name = body.get("name", "Escenario personalizado")
    label = body.get("label", "custom")
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 160 or not isinstance(label, str) or not 1 <= len(label.strip()) <= 30:
        return JsonResponse({"error": "invalid_scenario", "message": "Nombre o etiqueta de escenario inválidos."}, status=400)
    try:
        scenario = BusinessScenario.objects.create(
            model_version=definition.current_version, name=name.strip(),
            label=label.strip(), changes=changes, created_by=request.user,
        )
    except IntegrityError:
        return JsonResponse({"error": "scenario_exists", "message": "Ya existe un escenario con ese nombre para esta versión."}, status=409)
    return JsonResponse({"scenario": {"id": str(scenario.id), "name": scenario.name, "label": scenario.label, "changes": scenario.changes}}, status=201)


@login_required
@require_http_methods(["POST"])
@expensive_operation("import")
def data_import_create(request, model_id):
    """Create a bounded import receipt; imported rows remain explicitly sourced."""
    definition = _owned_model(request, model_id)
    organization = _organization_for_write(request)
    if not definition.current_version:
        return JsonResponse({"error": "model_has_no_version"}, status=400)
    source_name = request.FILES.get("file").name if request.FILES.get("file") else "request.json"
    fmt = (request.POST.get("format") if request.FILES else None) or "json"
    preview_requested = request.POST.get("preview") == "true" if request.FILES else False
    mapping = {}
    try:
        if request.FILES:
            uploaded = request.FILES["file"]
            mapping = json.loads(request.POST.get("mapping", "{}") or "{}")
            if not isinstance(mapping, dict):
                return JsonResponse({"error": "invalid_mapping"}, status=400)
            if uploaded.size > 2 * 1024 * 1024:
                return JsonResponse({"error": "file_too_large", "message": "El archivo no puede superar 2 MB."}, status=400)
            if fmt == "csv":
                rows = list(csv.DictReader(io.TextIOWrapper(uploaded.file, encoding="utf-8-sig", newline="")))
            elif fmt == "xlsx":
                from openpyxl import load_workbook
                _validate_xlsx_archive(uploaded.file)
                sheet = load_workbook(uploaded.file, read_only=True, data_only=True).active
                values = list(islice(sheet.values, 10_002))
                headers = [str(value) for value in (values[0] if values else [])]
                rows = [dict(zip(headers, row)) for row in values[1:]]
            else:
                return JsonResponse({"error": "unsupported_format"}, status=400)
        else:
            body = _json_body(request)
            fmt = body.get("format", "json")
            rows = body.get("rows", [])
            mapping = body.get("mapping", {})
            preview_requested = bool(body.get("preview", False))
        if fmt not in {"json", "csv", "xlsx"} or not isinstance(rows, list):
            return JsonResponse({"error": "invalid_import"}, status=400)
        if len(rows) > 10_000:
            return JsonResponse({"error": "too_many_rows", "message": "El límite es 10.000 filas."}, status=400)
        dataset_count = BusinessDataImport.objects.filter(
            model_version__definition__business__organization=organization,
            status="validated",
        ).count()
        enforce_quota(organization, "datasets", dataset_count)
        enforce_quota(organization, "dataset_rows", 0, len(rows))
        if not isinstance(mapping, dict) or any(not isinstance(source, str) or not isinstance(target, str) for source, target in mapping.items()):
            return JsonResponse({"error": "invalid_mapping", "message": "El mapeo debe ser un objeto de columnas a variables."}, status=400)
        known_targets = {item.get("id") for section in ("variables", "parameters", "stocks") for item in definition.current_version.spec.get(section, []) if isinstance(item, dict) and item.get("id")}
        unknown_targets = sorted(set(mapping.values()) - known_targets)
        if unknown_targets:
            return JsonResponse({"error": "unknown_mapping_target", "message": "Destinos no definidos en el modelo: " + ", ".join(unknown_targets)}, status=400)
        valid_rows, error_rows = _validate_import_rows(rows, mapping)
        if preview_requested:
            return JsonResponse({"preview": valid_rows[:25], "rows_total": len(rows), "error_rows": error_rows[:25], "mapping": mapping, "provenance": {"kind": "IMPORTED", "source_name": source_name, "format": fmt}})
        receipt = BusinessDataImport.objects.create(
            model_version=definition.current_version, source_name=source_name, format=fmt,
            status="rejected" if error_rows else "validated", mapping=mapping, rows=valid_rows,
            error_rows=error_rows, rows_imported=len(valid_rows), created_by=request.user,
            provenance={"kind": "IMPORTED", "source_name": source_name, "format": fmt},
        )
        record_usage(organization, UsageEvent.Metric.DATASET_INGESTED, 1, "modeling.import", receipt.id)
        record_usage(organization, UsageEvent.Metric.DATASET_ROWS, receipt.rows_imported, "modeling.import.rows", receipt.id)
        size_bytes = request.FILES["file"].size if request.FILES else len(request.body or b"")
        record_usage(organization, UsageEvent.Metric.STORAGE, size_bytes, "modeling.import.storage", receipt.id)
        record_resource_usage(organization, "STORAGE", size_bytes, "bytes", "modeling.import", receipt.id)
        return JsonResponse({"import": {"id": str(receipt.id), "status": receipt.status, "rows_imported": receipt.rows_imported, "error_rows": receipt.error_rows, "provenance": receipt.provenance}}, status=201)
    except (ValueError, KeyError, UnicodeDecodeError, zipfile.BadZipFile) as exc:
        return JsonResponse({"error": "invalid_import", "message": str(exc)}, status=400)


@login_required
@require_http_methods(["POST"])
@expensive_operation("simulation")
def model_simulate(request, model_id):
    definition = _owned_model(request, model_id)
    organization = _organization_for_write(request)
    if not definition.current_version:
        return JsonResponse({"error": "model_has_no_version", "message": "Valida una versión antes de simular."}, status=400)
    try:
        body = _json_body(request)
        iterations, seed = _simulation_parameters(body)
    except (ValueError, TypeError) as exc:
        return JsonResponse({"error": "invalid_simulation", "message": str(exc)}, status=400)
    engine = body.get("engine", "monte_carlo")
    if engine not in SUPPORTED_ENGINES:
        return JsonResponse({"error": "invalid_engine", "message": "Engine no soportado."}, status=400)
    if engine != "monte_carlo":
        require_entitlement(organization, "advanced_simulation", "modeling.simulate", model_id)
    enforce_monthly_usage(organization, "simulation_runs", UsageEvent.Metric.SIMULATION_RUN)
    if iterations < 1 or iterations > 100_000:
        return JsonResponse({"error": "invalid_iterations", "message": "iterations debe estar entre 1 y 100.000."}, status=400)
    max_active = max(1, int(getattr(settings, "MODELING_MAX_ACTIVE_RUNS", 4)))
    active_runs = BusinessSimulationRun.objects.filter(
        model_version__definition__business__organization=organization,
        status__in=("queued", "running")
    ).count()
    if active_runs >= max_active:
        return JsonResponse(
            {
                "error": "simulation_capacity_reached",
                "message": "Se alcanzó el límite de simulaciones activas para esta cuenta.",
                "active_runs": active_runs,
                "limit": max_active,
                "how_to_fix": "Espera a que termine una ejecución o cancela una ejecución pendiente.",
            },
            status=429,
        )
    scenario = None
    if body.get("scenario_id"):
        try:
            scenario = get_object_or_404(BusinessScenario, id=uuid.UUID(str(body["scenario_id"])), model_version=definition.current_version)
        except (ValueError, TypeError):
            return JsonResponse({"error": "invalid_scenario", "message": "scenario_id no es válido."}, status=400)
    run = BusinessSimulationRun.objects.create(
        model_version=definition.current_version,
        scenario=scenario,
        engine=engine,
        seed=seed,
        parameters_snapshot={
            "iterations": iterations,
            "seed": seed,
            "reference_data_source": definition.reference_data_source,
        },
        reference_data_source=definition.reference_data_source,
        created_by=request.user,
    )
    record_usage(
        organization, UsageEvent.Metric.SIMULATION_RUN, 1,
        "modeling.simulation", run.id,
        {"engine": engine, "iterations": iterations},
    )
    if scenario:
        record_usage(
            organization, UsageEvent.Metric.SCENARIO_RUN, 1,
            "modeling.scenario", run.id, {"scenario_id": str(scenario.id)},
        )
    from .tasks import run_business_simulation
    task = run_business_simulation.delay(str(run.id), iterations=iterations, seed=seed)
    return JsonResponse({"run_id": str(run.id), "task_id": task.id, "status": run.status, "status_url": f"/modeling/runs/{run.id}/"}, status=202)


@login_required
@require_http_methods(["POST"])
@expensive_operation("sensitivity")
def model_sensitivity(request, model_id):
    definition = _owned_model(request, model_id)
    organization = _organization_for_write(request)
    require_entitlement(organization, "advanced_simulation", "modeling.sensitivity", model_id)
    if not definition.current_version:
        return JsonResponse({"error": "model_has_no_version"}, status=400)
    try:
        body = _json_body(request)
        iterations, seed = _simulation_parameters(body)
        changes = body.get("changes", {})
        engine = body.get("engine", "monte_carlo")
        metric = body.get("metric", "profit")
        if engine not in SUPPORTED_ENGINES:
            return JsonResponse({"error": "invalid_engine", "message": "Engine no soportado."}, status=400)
        from .engine import run_sensitivity
        result = run_sensitivity(definition.current_version.spec, changes, engine=engine, metric=metric, iterations=iterations, seed=seed)
        return JsonResponse({"model_version": definition.current_version.version, "content_hash": definition.current_version.content_hash, "result": result})
    except (ValueError, TypeError) as exc:
        return JsonResponse({"error": "invalid_sensitivity", "message": str(exc)}, status=400)


@login_required
@require_http_methods(["POST"])
def model_distribution_fit(request, model_id):
    """Return reviewed candidate fits without mutating the immutable model."""
    _owned_model(request, model_id)
    organization = get_request_organization(request)
    require_entitlement(organization, "advanced_distributions", "modeling.distribution_fit", model_id)
    try:
        body = _json_body(request)
        result = fit_distributions(
            body.get("observations", []),
            body.get("candidates"),
            data_semantics=body.get("data_semantics", "continuous"),
        )
        return JsonResponse(result)
    except DistributionFitError as exc:
        return JsonResponse({"error": "invalid_distribution_fit", "message": str(exc), "how_to_fix": "Envía observaciones finitas y elige candidatos compatibles con su soporte."}, status=400)


@login_required
@require_GET
@expensive_operation("export")
def run_report(request, run_id):
    organization = get_request_organization(request)
    require_entitlement(organization, "exports", "modeling.run_report", run_id)
    enforce_monthly_usage(organization, "exports", UsageEvent.Metric.EXPORT)
    run = get_object_or_404(
        BusinessSimulationRun.objects.select_related("model_version__definition__business", "scenario"),
        id=run_id,
        model_version__definition__business__organization=organization,
        status="completed",
    )
    summary = (run.result or {}).get("summary", {})
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="findempro-run-{run.id}.csv"'
    writer = csv.writer(response)
    writer.writerow(["FindemproAI simulation report"])
    writer.writerow(["business", _csv_safe(run.model_version.definition.business.name)])
    writer.writerow(["model", _csv_safe(run.model_version.definition.name)])
    writer.writerow(["model_version", run.model_version.version])
    writer.writerow(["schema_version", run.model_version.schema_version])
    writer.writerow(["model_hash", run.model_version.content_hash])
    writer.writerow(["scenario", _csv_safe(run.scenario.name if run.scenario else "BASE")])
    writer.writerow(["engine", run.engine])
    writer.writerow(["seed", run.seed if run.seed is not None else ""])
    writer.writerow(["iterations", (run.parameters_snapshot or {}).get("iterations", "")])
    writer.writerow(["scenario_id", run.scenario_id or ""])
    writer.writerow(["created_at", run.created_at.isoformat()])
    writer.writerow([])
    writer.writerow(["metric", "value"])
    for key in ("mean", "median", "std", "p5", "p95", "probability_loss"):
        writer.writerow([key, summary.get(key, "")])
    if summary.get("financial") is not None:
        writer.writerow(["financial_summary", json.dumps(summary["financial"], ensure_ascii=False, sort_keys=True)])
    writer.writerow([])
    writer.writerow(["limitation", "Results are conditional on model, data, assumptions, distributions, parameters and scenario; they are not a guarantee of business reality."])
    record_usage(organization, UsageEvent.Metric.EXPORT, 1, "modeling.run_report", run.id)
    return response


@login_required
@require_GET
def run_list(request):
    organization = get_request_organization(request)
    runs = BusinessSimulationRun.objects.filter(model_version__definition__business__organization=organization).select_related(
        "model_version__definition__business", "scenario"
    )[:100]
    return JsonResponse({"runs": [{
        "id": str(run.id),
        "status": run.status,
        "engine": run.engine,
        "seed": run.seed,
        "scenario": run.scenario.name if run.scenario else "BASE",
        "model": run.model_version.definition.name,
        "business": run.model_version.definition.business.name,
        "version": run.model_version.version,
        "content_hash": run.model_version.content_hash,
        "created_at": run.created_at.isoformat(),
        "traceability": (run.result or {}).get("traceability") if run.status == "completed" else None,
        "summary": (run.result or {}).get("summary", {}) if run.status == "completed" else {},
        "error": decode_error(run.error) if run.status == "failed" else None,
    } for run in runs]})


@login_required
@require_GET
def run_compare(request):
    """Compare completed runs from one immutable model version."""
    raw_ids = [value.strip() for value in request.GET.get("ids", "").split(",") if value.strip()]
    if len(raw_ids) < 2 or len(raw_ids) > 10:
        return JsonResponse({"error": "invalid_comparison", "message": "Selecciona entre 2 y 10 ejecuciones."}, status=400)
    try:
        run_ids = [uuid.UUID(value) for value in raw_ids]
    except ValueError:
        return JsonResponse({"error": "invalid_comparison", "message": "Una ejecución seleccionada no es válida."}, status=400)
    organization = get_request_organization(request)
    require_entitlement(organization, "scenario_comparison", "modeling.run_compare", request.GET.get("ids", ""))
    runs = list(BusinessSimulationRun.objects.filter(id__in=run_ids, model_version__definition__business__organization=organization, status="completed").select_related("model_version", "scenario"))
    if len(runs) != len(set(run_ids)):
        return JsonResponse({"error": "comparison_not_available", "message": "Una o más ejecuciones no pertenecen al usuario o no están completadas."}, status=404)
    hashes = {run.model_version.content_hash for run in runs}
    if len(hashes) != 1:
        return JsonResponse({"error": "different_model_versions", "message": "Solo se pueden comparar ejecuciones de la misma versión de modelo."}, status=400)
    order = {run_id: index for index, run_id in enumerate(run_ids)}
    runs.sort(key=lambda run: order[run.id])
    baseline = (runs[0].result or {}).get("summary", {})
    metric_names = (
        "mean", "median", "std", "p5", "p95", "probability_loss",
        "mean_unmet_demand", "p95_unmet_demand", "mean_stock_service_level",
    )
    comparisons = []
    for run in runs:
        summary = (run.result or {}).get("summary", {})
        delta = {metric: summary[metric] - baseline[metric] for metric in metric_names if isinstance(summary.get(metric), (int, float)) and isinstance(baseline.get(metric), (int, float))}
        comparisons.append({"run_id": str(run.id), "scenario": run.scenario.name if run.scenario else "BASE", "seed": run.seed, "summary": summary, "delta": delta})
    return JsonResponse({"model_version": runs[0].model_version.version, "content_hash": runs[0].model_version.content_hash, "baseline_run_id": str(runs[0].id), "comparisons": comparisons})


@login_required
@require_http_methods(["POST"])
def run_cancel(request, run_id):
    """Cooperatively cancel a queued/running owner-scoped execution."""
    organization = _organization_for_write(request)
    run = get_object_or_404(BusinessSimulationRun, id=run_id, model_version__definition__business__organization=organization)
    if run.status not in {"queued", "running"}:
        return JsonResponse({"error": "not_cancellable", "message": "Solo se pueden cancelar ejecuciones encoladas o activas.", "status": run.status}, status=409)
    updated = BusinessSimulationRun.objects.filter(id=run.id, status__in=["queued", "running"]).update(status="cancelled", finished_at=timezone.now())
    if not updated:
        run.refresh_from_db(fields=["status"])
        return JsonResponse({"error": "state_changed", "status": run.status}, status=409)
    return JsonResponse({"run_id": str(run.id), "status": "cancelled"})


@login_required
@require_GET
def run_detail(request, run_id):
    organization = get_request_organization(request)
    run = get_object_or_404(BusinessSimulationRun.objects.select_related("model_version"), id=run_id, model_version__definition__business__organization=organization)
    return JsonResponse({
        "run_id": str(run.id), "status": run.status, "progress": run.progress, "engine": run.engine,
        "seed": run.seed, "result": run.result if run.status == "completed" else None,
        "error": decode_error(run.error) if run.status == "failed" else None,
        "created_at": run.created_at.isoformat(), "finished_at": run.finished_at.isoformat() if run.finished_at else None,
    })
