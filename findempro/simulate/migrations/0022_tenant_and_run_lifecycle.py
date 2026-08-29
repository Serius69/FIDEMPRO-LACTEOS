import django.db.models.deletion
from django.db import migrations, models


def backfill_project_organizations(apps, schema_editor):
    Project = apps.get_model("simulate", "SimulationProject")
    Membership = apps.get_model("tenancy", "OrganizationMembership")
    owner_by_user = dict(
        Membership.objects.filter(role="OWNER", is_active=True).values_list(
            "user_id", "organization_id"
        )
    )
    for project in Project.objects.filter(organization__isnull=True).iterator():
        if project.user_id:
            project.organization_id = owner_by_user[project.user_id]
            project.save(update_fields=["organization"])
    RiskAlert = apps.get_model("simulate", "RiskAlert")
    for alert in RiskAlert.objects.filter(organization__isnull=True).iterator():
        alert.organization_id = owner_by_user[alert.user_id]
        alert.save(update_fields=["organization"])


class Migration(migrations.Migration):
    dependencies = [
        ("simulate", "0021_simulation_demand_distribution"),
        ("tenancy", "0001_initial"),
    ]
    operations = [
        migrations.AddField(model_name="simulationproject", name="organization", field=models.ForeignKey(blank=True, db_index=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="simulation_projects", to="tenancy.organization")),
        migrations.AddField(model_name="riskalert", name="organization", field=models.ForeignKey(blank=True, db_index=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="risk_alerts", to="tenancy.organization")),
        migrations.RunPython(backfill_project_organizations, migrations.RunPython.noop),
        migrations.AddConstraint(model_name="simulationproject", constraint=models.CheckConstraint(condition=models.Q(("organization__isnull", False)), name="canvas_project_requires_organization")),
        migrations.AddConstraint(model_name="riskalert", constraint=models.CheckConstraint(condition=models.Q(("organization__isnull", False)), name="risk_alert_requires_organization")),
        migrations.AddField(model_name="canvassimulationrun", name="status", field=models.CharField(choices=[("queued", "Queued"), ("running", "Running"), ("completed", "Completed"), ("failed", "Failed"), ("cancelled", "Cancelled")], db_index=True, default="queued", max_length=20)),
        migrations.AddField(model_name="canvassimulationrun", name="progress", field=models.PositiveSmallIntegerField(default=0)),
        migrations.AddField(model_name="canvassimulationrun", name="error", field=models.TextField(blank=True)),
        migrations.AddField(model_name="canvassimulationrun", name="idempotency_key", field=models.CharField(blank=True, max_length=180)),
        migrations.AddIndex(model_name="canvassimulationrun", index=models.Index(fields=["project", "status"], name="simulate_ca_project_587151_idx")),
        migrations.AddConstraint(model_name="canvassimulationrun", constraint=models.UniqueConstraint(condition=models.Q(("idempotency_key", ""), _negated=True), fields=("project", "idempotency_key"), name="uniq_canvas_run_idempotency")),
    ]
