from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from allauth.account.models import EmailAddress
from unittest.mock import patch


class MyPasswordChangeViewTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username="testuser", password="old_password")
        EmailAddress.objects.create(user=self.user, email="testuser@example.com", verified=True, primary=True)
        self.client.login(username="testuser", password="old_password")
        self.url = reverse("account_change_password")

    def test_password_change_success(self):
        response = self.client.post(self.url, {
            "oldpassword": "old_password",
            "password1": "new_password",
            "password2": "new_password",
        })
        self.assertRedirects(response, reverse("dashboard:index"))

    @patch("findempro.views.PasswordChangeView.form_valid", side_effect=Exception("Test exception"))
    def test_password_change_error(self, mock_form_valid):
        # MyPasswordChangeView.form_valid llama a super().form_valid() (parcheado
        # para lanzar) y debe devolver 500 con el mensaje de error.
        response = self.client.post(self.url, {
            "oldpassword": "old_password",
            "password1": "new_password",
            "password2": "new_password",
        })
        self.assertEqual(response.status_code, 500)
        self.assertContains(response, "An error occurred while changing the password.", status_code=500)


class MyPasswordSetViewTests(TestCase):
    def setUp(self):
        # Usuario SIN contraseña utilizable: PasswordSetView solo aplica a cuentas
        # sin password (p.ej. login social). Con password usable allauth redirige
        # a la vista de cambio de contraseña.
        self.user = User.objects.create_user(username="testuser")
        self.user.set_unusable_password()
        self.user.save()
        EmailAddress.objects.create(user=self.user, email="testuser@example.com", verified=True, primary=True)
        self.client.force_login(self.user)
        self.url = reverse("account_set_password")

    def test_password_set_success(self):
        response = self.client.post(self.url, {
            "password1": "new_password",
            "password2": "new_password",
        })
        self.assertRedirects(response, reverse("dashboard:index"))

    @patch("findempro.views.PasswordSetView.form_valid", side_effect=Exception("Test exception"))
    def test_password_set_error(self, mock_form_valid):
        response = self.client.post(self.url, {
            "password1": "new_password",
            "password2": "new_password",
        })
        self.assertEqual(response.status_code, 500)
        self.assertContains(response, "An error occurred while setting the password.", status_code=500)
