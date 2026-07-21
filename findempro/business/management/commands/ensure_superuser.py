"""
manage.py ensure_superuser
==========================
Asegura, de forma **idempotente**, la existencia del superusuario ``sergio``
(mismo patrón que xgol y forex-erp en el ecosistema Kapitalya):

* Si NO existe → lo crea como superuser/staff activo.
* Si YA existe → garantiza ``is_superuser``/``is_staff``/``is_active`` pero
  **NO pisa la contraseña** existente (regla del ecosistema).

Pensado para correr tras cada ``migrate`` en dev/test/prod sin efectos
colaterales. El usuario, email y (solo para la creación inicial) la contraseña
son configurables por flag o variable de entorno.

La contraseña por defecto es la del ecosistema (misma que xgol/forex-erp); se
puede sobreescribir por flag o env sin tocar la de un usuario ya existente.

Ejemplos:
    python manage.py ensure_superuser
    python manage.py ensure_superuser --username sergio --email kapitalyabolivia@gmail.com
    FINDEMPRO_SUPERUSER_PASSWORD=... python manage.py ensure_superuser
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

# Defaults del ecosistema Kapitalya (idénticos a xgol/forex-erp).
DEFAULT_USERNAME = "sergio"
DEFAULT_EMAIL = "kapitalyabolivia@gmail.com"
DEFAULT_PASSWORD = "Kapitalya2026!"   # solo se usa al CREAR; nunca al actualizar


class Command(BaseCommand):
    help = "Crea/asegura el superusuario sergio sin pisar su password si ya existe."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            default=os.environ.get("FINDEMPRO_SUPERUSER", DEFAULT_USERNAME),
            help="Nombre de usuario del superuser (default: sergio).",
        )
        parser.add_argument(
            "--email",
            default=os.environ.get("FINDEMPRO_SUPERUSER_EMAIL", DEFAULT_EMAIL),
            help="Email del superuser (solo se fija al crear).",
        )
        parser.add_argument(
            "--password",
            default=(os.environ.get("FINDEMPRO_SUPERUSER_PASSWORD")
                     or os.environ.get("DJANGO_SUPERUSER_PASSWORD")
                     or DEFAULT_PASSWORD),
            help="Password inicial (solo se usa al CREAR; no pisa el existente).",
        )

    def handle(self, *args, **opts):
        User = get_user_model()
        username = opts["username"]
        email = opts["email"]
        password = opts["password"]

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_superuser": True, "is_staff": True,
                      "is_active": True},
        )

        if created:
            user.set_password(password)
            user.save(update_fields=["password"])
            self._ensure_verified_email(user)
            self.stdout.write(self.style.SUCCESS(
                f"✓ Superuser '{username}' creado (email verificado)."))
            return

        # Ya existía: asegurar flags SIN tocar la contraseña.
        changed = []
        for flag in ("is_superuser", "is_staff", "is_active"):
            if not getattr(user, flag):
                setattr(user, flag, True)
                changed.append(flag)
        if changed:
            user.save(update_fields=changed)
        self._ensure_verified_email(user)
        if changed:
            self.stdout.write(self.style.SUCCESS(
                f"✓ Superuser '{username}' ya existía; flags corregidos: "
                f"{', '.join(changed)} (password intacto, email verificado)."))
        else:
            self.stdout.write(
                f"✓ Superuser '{username}' ya existía y está OK "
                f"(password intacto, email verificado).")

    def _ensure_verified_email(self, user):
        """
        Deja el email PRIMARY y VERIFIED en allauth (si está instalado) para que
        el login NO dispare el envío del correo de confirmación — que en prod
        rompe con 500 si las credenciales SMTP fallan. No-op si no hay allauth.
        """
        if not user.email:
            return
        try:
            from allauth.account.models import EmailAddress
        except ImportError:
            return
        ea, created = EmailAddress.objects.get_or_create(
            user=user, email=user.email,
            defaults={"verified": True, "primary": True},
        )
        if not created and (not ea.verified or not ea.primary):
            ea.verified = True
            ea.primary = True
            ea.save(update_fields=["verified", "primary"])
