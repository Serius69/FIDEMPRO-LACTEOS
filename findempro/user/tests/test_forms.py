from django.test import TestCase
from django.contrib.auth.models import User
from findempro.user.forms import UserForm

class UserFormTest(TestCase):
    def test_user_form_empty_fields(self):
        form = UserForm(data={})
        self.assertTrue(form.is_valid(), "The form should be valid even with no fields defined.")

    def test_user_form_with_data(self):
        # Since no fields are defined, any data should still result in a valid form
        form = UserForm(data={'username': 'testuser', 'password': 'testpass'})
        self.assertTrue(form.is_valid(), "The form should be valid even with extra data provided.")