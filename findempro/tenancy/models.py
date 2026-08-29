from __future__ import annotations

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=210, unique=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_findempro_organizations",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            stem = slugify(self.name)[:180] or "organization"
            self.slug = f"{stem}-{str(self.id)[:8]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class OrganizationMembership(models.Model):
    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        ADMIN = "ADMIN", "Admin"
        MEMBER = "MEMBER", "Member"
        READ_ONLY = "READ_ONLY", "Read only"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="findempro_organization_memberships",
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user"], name="uniq_findempro_org_member"
            )
        ]
        indexes = [models.Index(fields=["user", "is_active", "organization"])]

    def __str__(self):
        return f"{self.user_id}:{self.organization_id}:{self.role}"


class Subscription(models.Model):
    class Plan(models.TextChoices):
        FREE = "FREE", "Free"
        STARTER = "STARTER", "Starter"
        GROWTH = "GROWTH", "Growth"
        PRO = "PRO", "Pro"
        BUSINESS = "BUSINESS", "Business"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        CANCELLED = "CANCELLED", "Cancelled"

    organization = models.OneToOneField(
        Organization, on_delete=models.CASCADE, related_name="subscription"
    )
    plan = models.CharField(max_length=20, choices=Plan.choices, default=Plan.FREE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    trial_started_at = models.DateTimeField(null=True, blank=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    trial_plan = models.CharField(max_length=20, choices=Plan.choices, null=True, blank=True)
    trial_consumed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def trial_is_active(self):
        return bool(
            self.trial_plan
            and self.trial_started_at
            and self.trial_ends_at
            and self.trial_started_at <= timezone.now() < self.trial_ends_at
        )

    @property
    def effective_plan(self):
        if self.status == self.Status.CANCELLED:
            return self.Plan.FREE
        return self.trial_plan if self.trial_is_active else self.plan

    def clean(self):
        if any((self.trial_started_at, self.trial_ends_at, self.trial_plan)) and not all(
            (self.trial_started_at, self.trial_ends_at, self.trial_plan)
        ):
            raise ValidationError("Los tres campos del trial deben configurarse juntos.")
        if self.trial_started_at and self.trial_ends_at <= self.trial_started_at:
            raise ValidationError("trial_ends_at debe ser posterior a trial_started_at.")


class AppendOnlyQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError("El ledger es append-only.")

    def delete(self):
        raise ValidationError("El ledger es append-only.")


class AppendOnlyModel(models.Model):
    objects = AppendOnlyQuerySet.as_manager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError("El ledger es append-only.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("El ledger es append-only.")


class UsageEvent(AppendOnlyModel):
    class Metric(models.TextChoices):
        PROJECT_CREATED = "PROJECT_CREATED", "Project created"
        DATASET_INGESTED = "DATASET_INGESTED", "Dataset ingested"
        DATASET_ROWS = "DATASET_ROWS", "Dataset rows"
        SIMULATION_RUN = "SIMULATION_RUN", "Simulation run"
        SIMULATION_RUNTIME = "SIMULATION_RUNTIME", "Simulation runtime"
        SCENARIO_RUN = "SCENARIO_RUN", "Scenario run"
        EXPORT = "EXPORT", "Export"
        REPORT = "REPORT", "Report"
        AI_CALL = "AI_CALL", "AI call"
        API_REQUEST = "API_REQUEST", "API request"
        STORAGE = "STORAGE", "Storage"

    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="usage_events"
    )
    metric = models.CharField(max_length=40, choices=Metric.choices, db_index=True)
    quantity = models.DecimalField(max_digits=20, decimal_places=6, default=1)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    source = models.CharField(max_length=120)
    correlation_id = models.CharField(max_length=180)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "metric", "source", "correlation_id"],
                name="uniq_findempro_usage_correlation",
            )
        ]
        indexes = [models.Index(fields=["organization", "metric", "timestamp"])]


class ResourceUsage(AppendOnlyModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="resource_usage"
    )
    resource = models.CharField(max_length=40, db_index=True)
    quantity = models.DecimalField(max_digits=20, decimal_places=6)
    unit = models.CharField(max_length=30)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    source = models.CharField(max_length=120)
    correlation_id = models.CharField(max_length=180)
    cost_amount = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    cost_currency = models.CharField(max_length=12, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "resource", "unit", "source", "correlation_id"],
                name="uniq_findempro_resource_correlation",
            )
        ]
        indexes = [models.Index(fields=["organization", "resource", "timestamp"])]
