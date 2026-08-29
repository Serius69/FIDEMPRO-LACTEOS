import django.db.models.deletion
from django.db import migrations, models


def backfill_business_organizations(apps, schema_editor):
    Business = apps.get_model("business", "Business")
    Membership = apps.get_model("tenancy", "OrganizationMembership")
    owner_by_user = dict(
        Membership.objects.filter(role="OWNER", is_active=True).values_list(
            "user_id", "organization_id"
        )
    )
    for business in Business.objects.filter(organization__isnull=True).iterator():
        business.organization_id = owner_by_user[business.fk_user_id]
        business.save(update_fields=["organization"])


class Migration(migrations.Migration):
    dependencies = [
        ("business", "0005_alter_business_type_alter_companyprofile_id_and_more"),
        ("tenancy", "0001_initial"),
    ]
    operations = [
        migrations.AddField(
            model_name="business",
            name="organization",
            field=models.ForeignKey(blank=True, db_index=True, help_text="Organization comercial propietaria. fk_user se conserva como creador legacy.", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="businesses", to="tenancy.organization"),
        ),
        migrations.RunPython(backfill_business_organizations, migrations.RunPython.noop),
        migrations.AddIndex(model_name="business", index=models.Index(fields=["organization", "is_active"], name="business_bu_organiz_4ab978_idx")),
        migrations.AddConstraint(model_name="business", constraint=models.UniqueConstraint(condition=models.Q(("is_active", True)), fields=("name", "organization"), name="unique_active_business_per_org")),
        migrations.AddConstraint(model_name="business", constraint=models.CheckConstraint(condition=models.Q(("organization__isnull", False)), name="business_requires_organization")),
    ]
