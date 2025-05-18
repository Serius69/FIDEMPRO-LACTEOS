from django.test import TestCase
from ..forms import FinancialDecisionForm, FinanceRecommendationForm
from parameterized import parameterized

# UNIT TESTS
class FinancialDecisionFormTest(TestCase):
    def test_valid_form(self):
        form_data = {
            'name': 'Decision Name',
            'type': 'Type A',
            'location': 'Location A',
            'image_src': 'http://example.com/image.jpg',
            'description': 'This is a valid description.'
        }
        form = FinancialDecisionForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_form_missing_fields(self):
        form_data = {
            'name': '',
            'type': 'Type A',
            'location': 'Location A',
            'image_src': 'http://example.com/image.jpg',
            'description': 'This is a valid description.'
        }
        form = FinancialDecisionForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)


class FinanceRecommendationFormTest(TestCase):
    def test_valid_form(self):
        form_data = {
            'name': 'Recommendation Name',
            'recommendation': 'This is a valid recommendation.',
            'description': 'This is a valid description.'
        }
        form = FinanceRecommendationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_form_empty_name(self):
        form_data = {
            'name': '',
            'recommendation': 'This is a valid recommendation.',
            'description': 'This is a valid description.'
        }
        form = FinanceRecommendationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_invalid_form_short_recommendation(self):
        form_data = {
            'name': 'Recommendation Name',
            'recommendation': 'Short',
            'description': 'This is a valid description.'
        }
        form = FinanceRecommendationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('recommendation', form.errors)

    def test_invalid_form_long_description(self):
        form_data = {
            'name': 'Recommendation Name',
            'recommendation': 'This is a valid recommendation.',
            'description': 'A' * 201  # Exceeds 200 characters
        }
        form = FinanceRecommendationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('description', form.errors)
        
        
# REGRESSION TESTS
class FinanceRecommendationFormValidationTest(TestCase):
    @parameterized.expand([
        ("valid_data", {
            'name': 'Valid Name',
            'recommendation': 'This is a valid recommendation.',
            'description': 'This is a valid description.'
        }, True, None),
        ("empty_name", {
            'name': '',
            'recommendation': 'This is a valid recommendation.',
            'description': 'This is a valid description.'
        }, False, 'name'),
        ("short_recommendation", {
            'name': 'Valid Name',
            'recommendation': 'Short',
            'description': 'This is a valid description.'
        }, False, 'recommendation'),
        ("long_description", {
            'name': 'Valid Name',
            'recommendation': 'This is a valid recommendation.',
            'description': 'A' * 201  # Exceeds 200 characters
        }, False, 'description'),
    ])
    def test_form_validation(self, _, form_data, is_valid, error_field):
        form = FinanceRecommendationForm(data=form_data)
        self.assertEqual(form.is_valid(), is_valid)
        if not is_valid and error_field:
            self.assertIn(error_field, form.errors)

    

