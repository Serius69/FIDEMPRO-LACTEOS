import pytest
from django import forms

from findempro.findempro.forms import (
    UserLoginForm,
    UserRegistrationForm,
    PasswordChangeForm,
    PasswordResetForm,
    PasswordResetKeyForm,
    PasswordSetForm,
)

@pytest.mark.django_db
def test_user_login_form():
    form = UserLoginForm(data={'login': 'testuser', 'password': 'testpassword', 'remember': True})
    assert form.is_valid()

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
    assert 'Las contraseñas no coinciden' in str(form.errors)

@pytest.mark.django_db
def test_password_change_form():
    form = PasswordChangeForm(data={
        'oldpassword': 'oldpassword123',
        'password1': 'newpassword123',
        'password2': 'newpassword123',
    })
    assert form.is_valid()

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