from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from allauth.account.models import EmailAddress
from django.http import HttpResponseServerError
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

    @patch("findempro.findempro.views.PasswordChangeView.form_valid", side_effect=Exception("Test exception"))
    def test_password_change_error(self, mock_form_valid):
        response = self.client.post(self.url, {
            "oldpassword": "old_password",
            "password1": "new_password",
            "password2": "new_password",
        })
        self.assertEqual(response.status_code, 500)
        self.assertContains(response, "An error occurred while changing the password.")

class MyPasswordSetViewTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username="testuser", password="old_password")
        EmailAddress.objects.create(user=self.user, email="testuser@example.com", verified=True, primary=True)
        self.client.login(username="testuser", password="old_password")
        self.url = reverse("account_set_password")

    def test_password_set_success(self):
        response = self.client.post(self.url, {
            "password1": "new_password",
            "password2": "new_password",
        })
        self.assertRedirects(response, reverse("dashboard:index"))

    @patch("findempro.findempro.views.PasswordSetView.form_valid", side_effect=Exception("Test exception"))
    def test_password_set_error(self, mock_form_valid):
        response = self.client.post(self.url, {
            "password1": "new_password",
            "password2": "new_password",
        })
        self.assertEqual(response.status_code, 500)
        self.assertContains(response, "An error occurred while setting the password.")