from django.core.management.base import BaseCommand

from modeling.models import BusinessModelTemplate
from modeling.templates import SECTOR_TEMPLATES, starter_spec


class Command(BaseCommand):
    help = "Crea o actualiza plantillas sintéticas iniciales de FindemproAI."

    def handle(self, *args, **options):
        for slug, name in SECTOR_TEMPLATES:
            BusinessModelTemplate.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "sector": slug,
                    "description": "Punto de partida editable; no representa datos reales.",
                    "spec": starter_spec(slug, name),
                    "provenance": {"kind": "SIMULATED", "label": "Datos sintéticos"},
                    "is_builtin": True,
                    "is_active": True,
                },
            )
        self.stdout.write(self.style.SUCCESS(f"Plantillas sincronizadas: {len(SECTOR_TEMPLATES)}"))
