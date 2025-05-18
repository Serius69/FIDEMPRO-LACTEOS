from django.test import TestCase
from findempro.business.forms import BusinessForm
from findempro.business.models import Business

# unIT TESTS
# BUSINESS FORMS
class BusinessFormTest(TestCase):
    def test_valid_form(self):
        form_data = {
            'name': 'Test Business',
            'type': 'Retail',
            'location': '123 Test Street',
            'image_src': 'test_image.jpg',
            'description': 'A test business description.'
        }
        form = BusinessForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_form_missing_fields(self):
        form_data = {
            'name': 'Test Business',
            'type': 'Retail',
            # 'location' is missing
            'image_src': 'test_image.jpg',
            # 'description' is missing
        }
        form = BusinessForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('location', form.errors)
        self.assertIn('description', form.errors)

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
        self.assertIn('image_src', form.errors)
        self.assertIn('description', form.errors)
        
