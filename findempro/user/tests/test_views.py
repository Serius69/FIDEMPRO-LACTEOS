import json
import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from user.models import UserProfile
from product.models import Product
from business.models import Business
from variable.models import Variable


@pytest.mark.django_db
def test_pages_profile_settings_view(client):
    user = User.objects.create_user(username="testuser", password="password")
    # El UserProfile lo crea un signal; solo lo ajustamos.
    profile = UserProfile.objects.get(user=user)
    profile.state = "Test State"
    profile.country = "Test Country"
    profile.save()
    client.login(username="testuser", password="password")

    response = client.get(reverse("user:user.profile_settings"))
    assert response.status_code == 200
    assert "completeness_percentage" in response.context
    assert "profile" in response.context


@pytest.mark.django_db
def test_profile_product_variable_list_view(client):
    user = User.objects.create_user(username="testuser", password="password")
    business = Business.objects.create(
        fk_user=user, name="Test Business", description="Desc", is_active=True)
    product = Product.objects.create(
        fk_business=business, name="Test Product", description="Desc", is_active=True)
    Variable.objects.create(fk_product=product, name="Test Var", is_active=True)
    client.login(username="testuser", password="password")

    response = client.get(reverse("user:user.profile"))
    assert response.status_code == 200
    assert "products" in response.context
    assert "variables" in response.context
    assert "businesses" in response.context


@pytest.mark.django_db
def test_user_list_view(client):
    User.objects.create_superuser(username="admin", password="password")
    client.login(username="admin", password="password")

    response = client.get(reverse("user:user.list"))
    assert response.status_code == 200
    assert "users" in response.context


@pytest.mark.django_db
def test_create_user_view(client):
    User.objects.create_superuser(username="admin", password="password")
    client.login(username="admin", password="password")

    # La vista responde JSON (200) y valida contraseña fuerte + confirmación.
    response = client.post(reverse("user:user.create"), {
        "username": "newuser",
        "email": "newuser@example.com",
        "first_name": "New",
        "last_name": "User",
        "password": "StrongP@ss1",
        "confirm_password": "StrongP@ss1",
    })
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert User.objects.filter(username="newuser").exists()


@pytest.mark.django_db
def test_update_user_view(client):
    User.objects.create_superuser(username="admin", password="password")
    client.login(username="admin", password="password")
    user_to_update = User.objects.create_user(username="testuser", password="password")

    # La vista responde JSON (200), no redirect.
    response = client.post(reverse("user:user.edit", args=[user_to_update.pk]), {
        "username": "updateduser",
        "email": "updateduser@example.com",
    })
    assert response.status_code == 200
    assert response.json()["success"] is True
    user_to_update.refresh_from_db()
    assert user_to_update.username == "updateduser"


@pytest.mark.django_db
def test_delete_user_view_as_admin(client):
    User.objects.create_superuser(username="admin", password="password")
    client.login(username="admin", password="password")
    user_to_delete = User.objects.create_user(username="testuser", password="password")
    pk = user_to_delete.pk

    # La vista hace hard delete y responde JSON (200).
    response = client.post(reverse("user:user.delete", args=[pk]))
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert not User.objects.filter(pk=pk).exists()


@pytest.mark.django_db
def test_change_password(client):
    user = User.objects.create_user(username="testuser", password="oldpassword")
    client.login(username="testuser", password="oldpassword")

    # La vista responde JSON (200) al cambiar la contraseña.
    response = client.post(reverse("user:password.change"), {
        "old_password": "oldpassword",
        "new_password1": "NewSecureP@ss1",
        "new_password2": "NewSecureP@ss1",
    })
    assert response.status_code == 200
    assert response.json()["success"] is True
    user.refresh_from_db()
    assert user.check_password("NewSecureP@ss1")


@pytest.mark.django_db
def test_deactivate_account(client):
    user = User.objects.create_user(username="testuser", password="password")
    client.login(username="testuser", password="password")

    response = client.post(reverse("user:user.deactivate_account"), {"password": "password"})
    assert response.status_code == 302
    user.refresh_from_db()
    assert not user.is_active
