"""
Tests del comando ensure_superuser (idempotente, no pisa password existente).
"""
from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

User = get_user_model()

# Contrasena de prueba. El comando ya NO trae una por defecto: el literal que
# vivia en el codigo creaba al administrador con una clave publica.
PASSWORD = "clave-solo-para-tests-9f2a"


@pytest.mark.django_db
def test_creates_sergio_superuser():
    call_command("ensure_superuser", "--password", PASSWORD, stdout=StringIO())
    u = User.objects.get(username="sergio")
    assert u.is_superuser and u.is_staff and u.is_active
    assert u.email == "kapitalyabolivia@gmail.com"
    assert u.check_password(PASSWORD)


@pytest.mark.django_db
def test_creation_without_password_fails_and_leaves_no_user():
    """Sin contrasena explicita no se crea nada.

    El comando corre en el deploy contra la base de produccion. Cuando traia un
    literal por defecto, la primera corrida sobre una base nueva dejaba al
    superusuario con una contrasena publicada en el repositorio.
    """
    with pytest.raises(CommandError, match="[Ff]alta la contrase"):
        call_command("ensure_superuser", stdout=StringIO())
    assert not User.objects.filter(username="sergio").exists()


@pytest.mark.django_db
def test_password_can_come_from_the_environment(monkeypatch):
    monkeypatch.setenv("FINDEMPRO_SUPERUSER_PASSWORD", PASSWORD)
    call_command("ensure_superuser", stdout=StringIO())
    assert User.objects.get(username="sergio").check_password(PASSWORD)


@pytest.mark.django_db
def test_existing_user_needs_no_password():
    """La ruta idempotente (la que corre en cada deploy) no pide contrasena."""
    User.objects.create_user(username="sergio", password="mi-clave-real",
                             is_superuser=False, is_staff=False)
    call_command("ensure_superuser", stdout=StringIO())
    u = User.objects.get(username="sergio")
    assert u.is_superuser and u.is_staff and u.check_password("mi-clave-real")


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
    call_command("ensure_superuser", "--password", PASSWORD, stdout=StringIO())
    u = User.objects.get(username="sergio")
    ea = EmailAddress.objects.get(user=u, email=u.email)
    assert ea.verified and ea.primary
