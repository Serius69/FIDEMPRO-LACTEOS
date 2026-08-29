from django.contrib.auth import get_user_model
from django.db import OperationalError, ProgrammingError
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=get_user_model())
def provision_default_organization(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        from .services import ensure_default_organization

        ensure_default_organization(instance)
    except (OperationalError, ProgrammingError):
        # User/auth migrations can run before the tenancy tables exist.
        return
