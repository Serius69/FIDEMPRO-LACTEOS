from business.models import Business
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from modeling.models import BusinessDataImport, BusinessModelDefinition
from modeling.schema import empty_model_spec
from modeling.services import create_model_version

from tenancy.models import Organization, OrganizationMembership, Subscription
from tenancy.services import change_plan, ensure_default_organization


class Command(BaseCommand):
    help = "Seed deterministic Organization-scoped DEV data for the no-Docker load harness."

    def add_arguments(self, parser):
        parser.add_argument("--organizations", type=int, default=1)
        parser.add_argument("--users-per-org", type=int, default=1)
        parser.add_argument("--projects-per-org", type=int, default=1)
        parser.add_argument("--datasets-per-project", type=int, default=1)
        parser.add_argument("--dataset-size", type=int, default=100)
        parser.add_argument("--free-ratio", type=float, default=0.0)
        parser.add_argument("--heavy-paid-ratio", type=float, default=0.1)
        parser.add_argument("--prefix", default="load")

    @transaction.atomic
    def handle(self, *args, **options):
        paid_organizations = options["organizations"]
        users_per_org = options["users_per_org"]
        projects_per_org = options["projects_per_org"]
        datasets_per_project = options["datasets_per_project"]
        dataset_size = options["dataset_size"]
        free_ratio = options["free_ratio"]
        heavy_paid_ratio = options["heavy_paid_ratio"]
        if not 1 <= paid_organizations <= 1000:
            raise CommandError("organizations must be between 1 and 1000")
        if not 1 <= users_per_org <= 100:
            raise CommandError("users-per-org must be between 1 and 100")
        if not 1 <= projects_per_org <= 100:
            raise CommandError("projects-per-org must be between 1 and 100")
        if not 0 <= datasets_per_project <= 100:
            raise CommandError("datasets-per-project must be between 0 and 100")
        if not 1 <= dataset_size <= 10_000:
            raise CommandError("dataset-size must be between 1 and 10000")
        if not 0 <= free_ratio <= 10:
            raise CommandError("free-ratio must be between 0 and 10")
        if not 0 <= heavy_paid_ratio <= 1:
            raise CommandError("heavy-paid-ratio must be between 0 and 1")

        free_organizations = round(paid_organizations * free_ratio)
        organizations = paid_organizations + free_organizations

        User = get_user_model()
        created_projects = 0
        created_datasets = 0
        for org_index in range(organizations):
            is_paid = org_index < paid_organizations
            paid_position = org_index / max(1, paid_organizations)
            profile = (
                "HEAVY_PAID"
                if is_paid and paid_position >= 1 - heavy_paid_ratio
                else "PAID" if is_paid else "FREE"
            )
            org_users = users_per_org if is_paid else 1
            org_projects = projects_per_org if is_paid else 1
            org_datasets = datasets_per_project if is_paid else min(1, datasets_per_project)
            owner = User.objects.create_user(
                username=f"{options['prefix']}-org-{org_index}-owner",
                email=f"{options['prefix']}-org-{org_index}-owner@example.test",
                password="load-harness-only",
            )
            organization = ensure_default_organization(owner)
            organization.name = f"Load Organization {org_index}"
            organization.save(update_fields=["name", "updated_at"])
            target_plan = "PRO" if profile == "HEAVY_PAID" else "GROWTH" if is_paid else "FREE"
            change_plan(organization, target_plan)
            for user_index in range(1, org_users):
                member = User.objects.create_user(
                    username=f"{options['prefix']}-org-{org_index}-member-{user_index}",
                    email=f"{options['prefix']}-org-{org_index}-member-{user_index}@example.test",
                    password="load-harness-only",
                )
                personal = ensure_default_organization(member)
                OrganizationMembership.objects.filter(organization=personal, user=member).delete()
                Subscription.objects.filter(organization=personal).delete()
                Organization.objects.filter(pk=personal.pk).delete()
                OrganizationMembership.objects.create(
                    organization=organization, user=member, role="MEMBER"
                )
            business = Business.objects.create(
                name=f"Load Business {org_index}",
                location="DEV",
                fk_user=owner,
                organization=organization,
            )
            for project_index in range(org_projects):
                definition = BusinessModelDefinition.objects.create(
                    business=business,
                    name=f"Load Project {org_index}-{project_index}",
                    sector="generic",
                    created_by=owner,
                )
                spec = empty_model_spec(name=definition.name, sector="generic")
                spec["metadata"]["horizon"] = 12
                spec["variables"] = [
                    {"id": "demand", "value": 100 + (org_index % 17)},
                    {"id": "price", "value": 10 + (project_index % 5)},
                    {"id": "unit_cost", "value": 6},
                ]
                spec["revenues"] = [
                    {"id": "sales_revenue", "expression": "demand * price"},
                ]
                spec["costs"] = [
                    {"id": "variable_cost", "expression": "demand * unit_cost"},
                ]
                version = create_model_version(definition, spec, user=owner)
                for dataset_index in range(org_datasets):
                    rows = [
                        {
                            "period": row_index,
                            "demand": 80 + ((row_index + org_index + dataset_index) % 41),
                        }
                        for row_index in range(dataset_size)
                    ]
                    BusinessDataImport.objects.create(
                        model_version=version,
                        source_name=f"synthetic-{profile.lower()}-{dataset_index}.json",
                        format="json",
                        status="validated",
                        mapping={},
                        rows=rows,
                        rows_imported=len(rows),
                        created_by=owner,
                        provenance={"kind": "SIMULATED", "profile": profile},
                    )
                    created_datasets += 1
                created_projects += 1

        self.stdout.write(
            " ".join((
                f"PAID_ORGANIZATIONS={paid_organizations}",
                f"FREE_ORGANIZATIONS={free_organizations}",
                f"ORGANIZATIONS={organizations}",
                f"USERS={paid_organizations * users_per_org + free_organizations}",
                f"PROJECTS={created_projects}",
                f"DATASETS={created_datasets}",
                f"DATASET_ROWS={created_datasets * dataset_size}",
                f"FREE_RATIO={free_ratio}",
                f"HEAVY_PAID_RATIO={heavy_paid_ratio}",
            ))
        )
