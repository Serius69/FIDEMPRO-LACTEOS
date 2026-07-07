from django.test import TestCase
from django.contrib.auth.models import User
from user.forms import UserForm


class UserFormTest(TestCase):
    """UserForm es hoy un UserCreationForm con campos obligatorios
    (username, email, first_name, last_name, password1/2) y validaciones
    fuertes. Se ejercita el comportamiento real de validación."""

    valid_data = {
        'username': 'juanperez',
        'email': 'juan@example.com',
        'first_name': 'Juan',
        'last_name': 'Perez',
        'password1': 'SecureP@ss99',
        'password2': 'SecureP@ss99',
    }

    def test_user_form_empty_fields(self):
        form = UserForm(data={})
        self.assertFalse(form.is_valid(),
                         "El form no debe ser válido sin datos (campos obligatorios).")
        for field in ('username', 'email', 'first_name', 'last_name',
                      'password1', 'password2'):
            self.assertIn(field, form.errors)

    def test_user_form_with_valid_data(self):
        form = UserForm(data=self.valid_data)
        self.assertTrue(form.is_valid(),
                        f"El form debería ser válido. Errores: {form.errors}")

    def test_user_form_password_mismatch(self):
        data = dict(self.valid_data, password2='OtraP@ss123')
        form = UserForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_user_form_saves_normalized_user(self):
        form = UserForm(data=self.valid_data)
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertTrue(User.objects.filter(username='juanperez').exists())
        # save() normaliza username/email a minúsculas
        self.assertEqual(user.username, 'juanperez')
        self.assertEqual(user.email, 'juan@example.com')
