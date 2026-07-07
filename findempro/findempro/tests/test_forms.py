import pytest
from django import forms
from django.contrib.auth.models import User
from django.test import RequestFactory

from findempro.forms import (
    UserLoginForm,
    UserRegistrationForm,
    PasswordChangeForm,
    PasswordResetForm,
    PasswordResetKeyForm,
    PasswordSetForm,
)

@pytest.mark.django_db
def test_user_login_form():
    # allauth LoginForm autentica contra la DB: requiere un usuario real y un request.
    User.objects.create_user(username='testuser', password='testpassword')
    request = RequestFactory().post('/account/login/')
    form = UserLoginForm(
        data={'login': 'testuser', 'password': 'testpassword', 'remember': True},
        request=request,
    )
    assert form.is_valid(), form.errors

@pytest.mark.django_db
def test_user_registration_form_valid():
    form = UserRegistrationForm(data={
        'email': 'test@example.com',
        'username': 'testuser',
        'password1': 'strongpassword123',
        'password2': 'strongpassword123',
    })
    assert form.is_valid()

@pytest.mark.django_db
def test_user_registration_form_password_mismatch():
    form = UserRegistrationForm(data={
        'email': 'test@example.com',
        'username': 'testuser',
        'password1': 'strongpassword123',
        'password2': 'differentpassword',
    })
    assert not form.is_valid()
    # Mensaje real de allauth para password2 no coincidente.
    assert 'misma contraseña' in str(form.errors)

@pytest.mark.django_db
def test_password_change_form():
    # allauth ChangePasswordForm verifica oldpassword contra el usuario: requiere user=.
    user = User.objects.create_user(username='pwchange', password='oldpassword123')
    form = PasswordChangeForm(user=user, data={
        'oldpassword': 'oldpassword123',
        'password1': 'newpassword123',
        'password2': 'newpassword123',
    })
    assert form.is_valid(), form.errors

@pytest.mark.django_db
def test_password_reset_form():
    form = PasswordResetForm(data={'email': 'test@example.com'})
    assert form.is_valid()

@pytest.mark.django_db
def test_password_reset_key_form_valid():
    form = PasswordResetKeyForm(data={
        'password1': 'newpassword123',
        'password2': 'newpassword123',
    })
    assert form.is_valid()

@pytest.mark.django_db
def test_password_reset_key_form_password_mismatch():
    form = PasswordResetKeyForm(data={
        'password1': 'newpassword123',
        'password2': 'differentpassword',
    })
    assert not form.is_valid()

@pytest.mark.django_db
def test_password_set_form():
    form = PasswordSetForm(data={
        'password1': 'newpassword123',
        'password2': 'newpassword123',
    })
    assert form.is_valid()