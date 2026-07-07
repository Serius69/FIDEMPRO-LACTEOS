from django.test import TestCase
from business.forms import BusinessForm
from business.models import Business

# unIT TESTS
# BUSINESS FORMS
class BusinessFormTest(TestCase):
    def test_valid_form(self):
        form_data = {
            'name': 'Test Business',
            'type': Business.BusinessType.RETAIL,  # type es IntegerField con choices
            'location': 'La Paz',
            'description': 'A test business description.'
        }
        form = BusinessForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_form_missing_fields(self):
        form_data = {
            'name': 'Test Business',
            'type': Business.BusinessType.RETAIL,
            # 'location' is missing
            # 'description' is missing
        }
        form = BusinessForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('location', form.errors)
        # 'description' es opcional en el modelo (blank=True, default='')

    def test_invalid_form_empty_fields(self):
        form_data = {
            'name': '',
            'type': '',
            'location': '',
            'image_src': '',
            'description': ''
        }
        form = BusinessForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn('type', form.errors)
        self.assertIn('location', form.errors)
        # image_src y description son opcionales (blank=True) — no generan error si vacíos
        
