import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

pytestmark = pytest.mark.django_db(transaction=True)


OLD_TARGETS = [
    ("business", "0005_alter_business_type_alter_companyprofile_id_and_more"),
    ("simulate", "0021_simulation_demand_distribution"),
    ("tenancy", None),
]

NEW_TARGETS = [
    ("business", "0006_organization_ownership"),
    ("simulate", "0022_tenant_and_run_lifecycle"),
    ("tenancy", "0001_initial"),
]


def test_existing_user_and_resources_are_backfilled_to_one_organization():
    executor = MigrationExecutor(connection)
    leaf_targets = executor.loader.graph.leaf_nodes()
    try:
        executor.migrate(OLD_TARGETS)
        old_apps = executor.loader.project_state(OLD_TARGETS[:2]).apps
        User = old_apps.get_model("auth", "User")
        Business = old_apps.get_model("business", "Business")
        Project = old_apps.get_model("simulate", "SimulationProject")
        RiskAlert = old_apps.get_model("simulate", "RiskAlert")

        user = User.objects.create(username="existing-before-tenancy")
        business = Business.objects.create(
            name="Existing business",
            type=7,
            industry_sector="other",
            location="La Paz",
            fk_user_id=user.id,
        )
        project = Project.objects.create(user_id=user.id, name="Existing canvas", domain="generic")
        alert = RiskAlert.objects.create(
            user_id=user.id,
            var_threshold=-1,
            email="existing@example.test",
        )

        executor = MigrationExecutor(connection)
        executor.migrate(NEW_TARGETS)
        new_apps = executor.loader.project_state(NEW_TARGETS).apps
        Organization = new_apps.get_model("tenancy", "Organization")
        Membership = new_apps.get_model("tenancy", "OrganizationMembership")
        Subscription = new_apps.get_model("tenancy", "Subscription")
        NewBusiness = new_apps.get_model("business", "Business")
        NewProject = new_apps.get_model("simulate", "SimulationProject")
        NewRiskAlert = new_apps.get_model("simulate", "RiskAlert")

        organization = Organization.objects.get(created_by_id=user.id)
        assert Membership.objects.filter(
            organization_id=organization.id,
            user_id=user.id,
            role="OWNER",
        ).exists()
        assert Subscription.objects.get(organization_id=organization.id).plan == "FREE"
        assert NewBusiness.objects.get(id=business.id).organization_id == organization.id
        assert NewProject.objects.get(id=project.id).organization_id == organization.id
        assert NewRiskAlert.objects.get(id=alert.id).organization_id == organization.id
    finally:
        MigrationExecutor(connection).migrate(leaf_targets)
