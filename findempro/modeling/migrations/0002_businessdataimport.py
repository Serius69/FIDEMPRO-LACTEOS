from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("modeling", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="BusinessDataImport",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("source_name", models.CharField(max_length=255)),
                ("format", models.CharField(choices=[("json", "JSON"), ("csv", "CSV"), ("xlsx", "XLSX")], max_length=10)),
                ("status", models.CharField(choices=[("validated", "Validado"), ("rejected", "Rechazado")], default="validated", max_length=20)),
                ("mapping", models.JSONField(blank=True, default=dict)),
                ("rows", models.JSONField(blank=True, default=list)),
                ("error_rows", models.JSONField(blank=True, default=list)),
                ("rows_imported", models.PositiveIntegerField(default=0)),
                ("provenance", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="business_data_imports", to=settings.AUTH_USER_MODEL)),
                ("model_version", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="data_imports", to="modeling.businessmodelversion")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="businessdataimport",
            index=models.Index(fields=["model_version", "created_at"], name="modeling_bu_model_v_75a8c3_idx"),
        ),
    ]
