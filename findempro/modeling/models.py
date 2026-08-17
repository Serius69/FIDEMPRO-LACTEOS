from __future__ import annotations

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from business.models import Business


class BusinessModelDefinition(models.Model):
    """Container owned by a Business; versions hold immutable model meaning."""

    STATUS_CHOICES = [
        ("draft", "Borrador"),
        ("validated", "Validado"),
        ("published", "Publicado"),
        ("archived", "Archivado"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="model_definitions"
    )
    name = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    sector = models.CharField(max_length=80, default="generic", db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    current_version = models.ForeignKey(
        "BusinessModelVersion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="current_for_definitions",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_model_definitions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["business", "status"]),
            models.Index(fields=["sector", "status"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.business.name})"

    @property
    def owner_id(self):
        return self.business.fk_user_id


class BusinessModelVersion(models.Model):
    """Immutable, hashed snapshot of a canonical model specification."""

    STATUS_CHOICES = [
        ("draft", "Borrador"),
        ("validated", "Validado"),
        ("published", "Publicado"),
        ("superseded", "Reemplazado"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    definition = models.ForeignKey(
        BusinessModelDefinition, on_delete=models.CASCADE, related_name="versions"
    )
    version = models.PositiveIntegerField()
    schema_version = models.CharField(max_length=20, default="1.0")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    parent_version = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True, related_name="children"
    )
    spec = models.JSONField(default=dict)
    content_hash = models.CharField(max_length=64, editable=False)
    validation = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_model_versions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["definition", "version"], name="uniq_model_definition_version"
            ),
        ]
        indexes = [
            models.Index(fields=["definition", "status"]),
            models.Index(fields=["content_hash"]),
        ]

    def clean(self):
        if self.pk and self.__class__.objects.filter(pk=self.pk).exists():
            previous = self.__class__.objects.get(pk=self.pk)
            immutable_fields = (
                "definition_id", "version", "schema_version", "parent_version_id",
                "spec", "content_hash", "created_by_id",
            )
            if any(getattr(previous, field) != getattr(self, field) for field in immutable_fields):
                raise ValidationError("Las versiones de modelo son inmutables.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def owner_id(self):
        return self.definition.owner_id


class BusinessModelTemplate(models.Model):
    """Editable starting point; built-ins contain synthetic/reference data only."""

    slug = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=180)
    sector = models.CharField(max_length=80, default="generic", db_index=True)
    description = models.TextField(blank=True)
    spec = models.JSONField(default=dict)
    provenance = models.JSONField(default=dict, blank=True)
    is_builtin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="created_model_templates",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class BusinessScenario(models.Model):
    """Explicit parameter deltas applied to one immutable model version."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model_version = models.ForeignKey(
        BusinessModelVersion, on_delete=models.PROTECT, related_name="scenarios"
    )
    name = models.CharField(max_length=160)
    label = models.CharField(max_length=30, default="custom")
    changes = models.JSONField(default=dict)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_business_scenarios",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["model_version", "name"], name="uniq_scenario_per_model_version"
            ),
        ]

    @property
    def owner_id(self):
        return self.model_version.owner_id


class BusinessSimulationRun(models.Model):
    """Durable execution metadata and result snapshot for a model version."""

    STATUS_CHOICES = [
        ("queued", "Encolada"),
        ("running", "En ejecución"),
        ("completed", "Completada"),
        ("failed", "Fallida"),
        ("cancelled", "Cancelada"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model_version = models.ForeignKey(
        BusinessModelVersion, on_delete=models.PROTECT, related_name="simulation_runs"
    )
    scenario = models.ForeignKey(
        BusinessScenario, on_delete=models.PROTECT, null=True, blank=True, related_name="runs"
    )
    engine = models.CharField(max_length=40, default="monte_carlo")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="queued")
    seed = models.BigIntegerField(null=True, blank=True)
    parameters_snapshot = models.JSONField(default=dict, blank=True)
    result = models.JSONField(default=dict, blank=True)
    error = models.TextField(blank=True)
    progress = models.PositiveSmallIntegerField(default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="business_simulation_runs",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["model_version", "status"]),
            models.Index(fields=["created_by", "created_at"]),
        ]

    @property
    def owner_id(self):
        return self.model_version.owner_id


class BusinessDataImport(models.Model):
    """Auditable, bounded data receipt linked to one business model version."""

    FORMAT_CHOICES = [("json", "JSON"), ("csv", "CSV"), ("xlsx", "XLSX")]
    STATUS_CHOICES = [("validated", "Validado"), ("rejected", "Rechazado")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model_version = models.ForeignKey(
        BusinessModelVersion, on_delete=models.PROTECT, related_name="data_imports"
    )
    source_name = models.CharField(max_length=255)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="validated")
    mapping = models.JSONField(default=dict, blank=True)
    rows = models.JSONField(default=list, blank=True)
    error_rows = models.JSONField(default=list, blank=True)
    rows_imported = models.PositiveIntegerField(default=0)
    provenance = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="business_data_imports"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["model_version", "created_at"])]

    @property
    def owner_id(self):
        return self.model_version.owner_id
