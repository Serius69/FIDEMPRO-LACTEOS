import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from user.models import UserProfile
from product.models import Product
from business.models import Business
from variable.models import Variable
from django.test import Client
from django.core.paginator import Paginator

@pytest.mark.django_db
def test_pages_profile_settings_view(client):
    user = User.objects.create_user(username="testuser", password="password")
    UserProfile.objects.create(user=user, state="Test State", country="Test Country")
    client.login(username="testuser", password="password")
    
    response = client.get(reverse("pages_profile_settings"))
    assert response.status_code == 200
    assert "completeness_percentage" in response.context
    assert "profile" in response.context

@pytest.mark.django_db
def test_profile_product_variable_list_view(client):
    user = User.objects.create_user(username="testuser", password="password")
    UserProfile.objects.create(user=user)
    business = Business.objects.create(fk_user=user, is_active=True)
    Product.objects.create(fk_business=business, is_active=True)
    Variable.objects.create(fk_product=Product.objects.first(), is_active=True)
    client.login(username="testuser", password="password")
    
    response = client.get(reverse("profile_product_variable_list_view"))
    assert response.status_code == 200
    assert "products" in response.context
    assert "variables" in response.context
    assert "businesses" in response.context

@pytest.mark.django_db
def test_user_list_view(client):
    user = User.objects.create_superuser(username="admin", password="password")
    client.login(username="admin", password="password")
    
    response = client.get(reverse("user_list_view"))
    assert response.status_code == 200
    assert "users" in response.context

@pytest.mark.django_db
def test_create_user_view(client):
    user = User.objects.create_superuser(username="admin", password="password")
    client.login(username="admin", password="password")
    
    response = client.post(reverse("create_user_view"), {
        "username": "newuser",
        "password": "password",
        "email": "newuser@example.com"
    })
    assert response.status_code == 200
    assert User.objects.filter(username="newuser").exists()

@pytest.mark.django_db
def test_update_user_view(client):
    user = User.objects.create_superuser(username="admin", password="password")
    client.login(username="admin", password="password")
    user_to_update = User.objects.create_user(username="testuser", password="password")
    
    response = client.post(reverse("update_user_view", args=[user_to_update.pk]), {
        "username": "updateduser",
        "email": "updateduser@example.com"
    })
    assert response.status_code == 302
    user_to_update.refresh_from_db()
    assert user_to_update.username == "updateduser"

@pytest.mark.django_db
def test_delete_user_view_as_admin(client):
    admin = User.objects.create_superuser(username="admin", password="password")
    client.login(username="admin", password="password")
    user_to_delete = User.objects.create_user(username="testuser", password="password")
    
    response = client.post(reverse("delete_user_view_as_admin", args=[user_to_delete.pk]))
    assert response.status_code == 302
    user_to_delete.refresh_from_db()
    assert not user_to_delete.is_active

@pytest.mark.django_db
def test_change_password(client):
    user = User.objects.create_user(username="testuser", password="oldpassword")
    client.login(username="testuser", password="oldpassword")
    
    response = client.post(reverse("change_password"), {
        "old_password": "oldpassword",
        "new_password1": "newpassword",
        "new_password2": "newpassword"
    })
    assert response.status_code == 302
    user.refresh_from_db()
    assert user.check_password("newpassword")

@pytest.mark.django_db
def test_deactivate_account(client):
    user = User.objects.create_user(username="testuser", password="password")
    client.login(username="testuser", password="password")
    
    response = client.post(reverse("deactivate_account"), {"password": "password"})
    assert response.status_code == 302
    user.refresh_from_db()
    assert not user.is_active