from django.test import TestCase
from ..forms import VariableForm, EquationForm
from ..models import Variable, Equation

class VariableFormTest(TestCase):
    def test_variable_form_valid_data(self):
        form = VariableForm(data={
            'name': 'Test Variable',
            'type': 'Type A',
            'unit': 'kg',
            'description': 'A test variable',
            'image_src': 'test_image.png',
            'fk_product': 1
        })
        self.assertTrue(form.is_valid())

    def test_variable_form_invalid_data(self):
        form = VariableForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 6)  # All fields are required

class EquationFormTest(TestCase):
    def test_equation_form_valid_data(self):
        form = EquationForm(data={
            'name': 'Test Equation',
            'description': 'A test equation',
            'expression': 'x + y',
            'fk_variable1': 1,
            'fk_variable2': 2,
            'fk_variable3': 3,
            'fk_variable4': 4,
            'fk_variable5': 5,
            'fk_area': 1
        })
        self.assertTrue(form.is_valid())

    def test_equation_form_invalid_data(self):
        form = EquationForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 8)  # All fields are required