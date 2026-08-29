import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


def provision_existing_users(apps, schema_editor):
    User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
    Organization = apps.get_model("tenancy", "Organization")
    Membership = apps.get_model("tenancy", "OrganizationMembership")
    Subscription = apps.get_model("tenancy", "Subscription")
    for user in User.objects.all().iterator():
        full_name = " ".join(
            value.strip()
            for value in (getattr(user, "first_name", ""), getattr(user, "last_name", ""))
            if value and value.strip()
        )
        username = getattr(user, "username", "") or f"user-{user.pk}"
        organization = Organization.objects.create(
            id=uuid.uuid4(),
            name=full_name or f"{username} Organization",
            slug=f"user-{user.pk}-{uuid.uuid4().hex[:8]}",
            created_by_id=user.pk,
        )
        Membership.objects.create(
            organization_id=organization.pk, user_id=user.pk, role="OWNER"
        )
        Subscription.objects.create(organization_id=organization.pk, plan="FREE")


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Organization",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=180)),
                ("slug", models.SlugField(max_length=210, unique=True)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_findempro_organizations", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Subscription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("plan", models.CharField(choices=[("FREE", "Free"), ("STARTER", "Starter"), ("GROWTH", "Growth"), ("PRO", "Pro"), ("BUSINESS", "Business")], default="FREE", max_length=20)),
                ("status", models.CharField(choices=[("ACTIVE", "Active"), ("CANCELLED", "Cancelled")], default="ACTIVE", max_length=20)),
                ("trial_started_at", models.DateTimeField(blank=True, null=True)),
                ("trial_ends_at", models.DateTimeField(blank=True, null=True)),
                ("trial_plan", models.CharField(blank=True, choices=[("FREE", "Free"), ("STARTER", "Starter"), ("GROWTH", "Growth"), ("PRO", "Pro"), ("BUSINESS", "Business")], max_length=20, null=True)),
                ("trial_consumed_at", models.DateTimeField(blank=True, null=True)),
                ("cancelled_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("organization", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="subscription", to="tenancy.organization")),
            ],
        ),
        migrations.CreateModel(
            name="OrganizationMembership",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("OWNER", "Owner"), ("ADMIN", "Admin"), ("MEMBER", "Member"), ("READ_ONLY", "Read only")], default="MEMBER", max_length=20)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="memberships", to="tenancy.organization")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="findempro_organization_memberships", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="UsageEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("metric", models.CharField(choices=[("PROJECT_CREATED", "Project created"), ("DATASET_INGESTED", "Dataset ingested"), ("DATASET_ROWS", "Dataset rows"), ("SIMULATION_RUN", "Simulation run"), ("SIMULATION_RUNTIME", "Simulation runtime"), ("SCENARIO_RUN", "Scenario run"), ("EXPORT", "Export"), ("REPORT", "Report"), ("AI_CALL", "AI call"), ("API_REQUEST", "API request"), ("STORAGE", "Storage")], db_index=True, max_length=40)),
                ("quantity", models.DecimalField(decimal_places=6, default=1, max_digits=20)),
                ("timestamp", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("source", models.CharField(max_length=120)),
                ("correlation_id", models.CharField(max_length=180)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="usage_events", to="tenancy.organization")),
            ],
            options={"ordering": ["-timestamp"]},
        ),
        migrations.CreateModel(
            name="ResourceUsage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("resource", models.CharField(db_index=True, max_length=40)),
                ("quantity", models.DecimalField(decimal_places=6, max_digits=20)),
                ("unit", models.CharField(max_length=30)),
                ("timestamp", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("source", models.CharField(max_length=120)),
                ("correlation_id", models.CharField(max_length=180)),
                ("cost_amount", models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True)),
                ("cost_currency", models.CharField(blank=True, max_length=12)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="resource_usage", to="tenancy.organization")),
            ],
            options={"ordering": ["-timestamp"]},
        ),
        migrations.AddConstraint(model_name="organizationmembership", constraint=models.UniqueConstraint(fields=("organization", "user"), name="uniq_findempro_org_member")),
        migrations.AddIndex(model_name="organizationmembership", index=models.Index(fields=["user", "is_active", "organization"], name="tenancy_org_user_id_a0c11f_idx")),
        migrations.AddConstraint(model_name="usageevent", constraint=models.UniqueConstraint(fields=("organization", "metric", "source", "correlation_id"), name="uniq_findempro_usage_correlation")),
        migrations.AddIndex(model_name="usageevent", index=models.Index(fields=["organization", "metric", "timestamp"], name="tenancy_usa_organiz_7cb694_idx")),
        migrations.AddConstraint(model_name="resourceusage", constraint=models.UniqueConstraint(fields=("organization", "resource", "unit", "source", "correlation_id"), name="uniq_findempro_resource_correlation")),
        migrations.AddIndex(model_name="resourceusage", index=models.Index(fields=["organization", "resource", "timestamp"], name="tenancy_res_organiz_361125_idx")),
        migrations.RunPython(provision_existing_users, migrations.RunPython.noop),
    ]
