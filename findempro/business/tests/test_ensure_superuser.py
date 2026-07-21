"""
Tests del comando ensure_superuser (idempotente, no pisa password existente).
"""
from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

User = get_user_model()


@pytest.mark.django_db
def test_creates_sergio_superuser():
    call_command("ensure_superuser", stdout=StringIO())
    u = User.objects.get(username="sergio")
    assert u.is_superuser and u.is_staff and u.is_active
    assert u.email == "kapitalyabolivia@gmail.com"
    assert u.check_password("Kapitalya2026!")


@pytest.mark.django_db
def test_idempotent_does_not_reset_password():
    # Existe con OTRA password → segunda corrida NO debe pisarla.
    u = User.objects.create_user(username="sergio", password="mi-clave-real")
    call_command("ensure_superuser", stdout=StringIO())
    u.refresh_from_db()
    assert u.check_password("mi-clave-real")          # password intacto
    assert u.is_superuser and u.is_staff               # flags asegurados


@pytest.mark.django_db
def test_repairs_flags_without_touching_password():
    User.objects.create_user(username="sergio", password="x",
                             is_superuser=False, is_staff=False)
    call_command("ensure_superuser", stdout=StringIO())
    u = User.objects.get(username="sergio")
    assert u.is_superuser and u.is_staff
    assert u.check_password("x")


@pytest.mark.django_db
def test_custom_username_and_password():
    call_command("ensure_superuser", "--username", "otro",
                 "--password", "clave123", stdout=StringIO())
    u = User.objects.get(username="otro")
    assert u.is_superuser and u.check_password("clave123")


@pytest.mark.django_db
def test_leaves_email_verified_for_allauth_login():
    # Sin email verificado, allauth intentaría enviar confirmación al hacer login
    # (500 si el SMTP falla). El comando debe dejarlo primary+verified.
    pytest.importorskip("allauth")
    from allauth.account.models import EmailAddress
    call_command("ensure_superuser", stdout=StringIO())
    u = User.objects.get(username="sergio")
    ea = EmailAddress.objects.get(user=u, email=u.email)
    assert ea.verified and ea.primary
