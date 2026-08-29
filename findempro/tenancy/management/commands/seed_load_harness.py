from business.models import Business
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from modeling.models import BusinessModelDefinition
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
        parser.add_argument("--free-ratio", type=float, default=1.0)
        parser.add_argument("--prefix", default="load")

    @transaction.atomic
    def handle(self, *args, **options):
        organizations = options["organizations"]
        users_per_org = options["users_per_org"]
        projects_per_org = options["projects_per_org"]
        free_ratio = options["free_ratio"]
        if not 1 <= organizations <= 1000:
            raise CommandError("organizations must be between 1 and 1000")
        if not 1 <= users_per_org <= 100:
            raise CommandError("users-per-org must be between 1 and 100")
        if not 1 <= projects_per_org <= 100:
            raise CommandError("projects-per-org must be between 1 and 100")
        if not 0 <= free_ratio <= 1:
            raise CommandError("free-ratio must be between 0 and 1")

        User = get_user_model()
        created_projects = 0
        for org_index in range(organizations):
            owner = User.objects.create_user(
                username=f"{options['prefix']}-org-{org_index}-owner",
                email=f"{options['prefix']}-org-{org_index}-owner@example.test",
                password="load-harness-only",
            )
            organization = ensure_default_organization(owner)
            organization.name = f"Load Organization {org_index}"
            organization.save(update_fields=["name", "updated_at"])
            target_plan = "FREE" if org_index / organizations < free_ratio else "PRO"
            change_plan(organization, target_plan)
            for user_index in range(1, users_per_org):
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
            for project_index in range(projects_per_org):
                definition = BusinessModelDefinition.objects.create(
                    business=business,
                    name=f"Load Project {org_index}-{project_index}",
                    sector="generic",
                    created_by=owner,
                )
                create_model_version(
                    definition,
                    empty_model_spec(name=definition.name, sector="generic"),
                    user=owner,
                )
                created_projects += 1

        self.stdout.write(
            " ".join((
                f"ORGANIZATIONS={organizations}",
                f"USERS={organizations * users_per_org}",
                f"PROJECTS={created_projects}",
                f"FREE_RATIO={free_ratio}",
            ))
        )
