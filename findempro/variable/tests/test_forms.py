from django.test import TestCase
from django.contrib.auth.models import User
from ..forms import VariableForm, EquationForm
from ..models import Variable
from business.models import Business
from product.models import Product


class VariableFormTest(TestCase):
    def setUp(self):
        user = User.objects.create_user(username="owner", password="pw")
        business = Business.objects.create(
            name="Test Business", type=1, location="La Paz",
            description="d", fk_user=user, is_active=True,
        )
        self.product = Product.objects.create(
            name="Test Product", description="d", fk_business=business, is_active=True,
        )

    def test_variable_form_valid_data(self):
        # Campos obligatorios del esquema vigente: name, type (int válido),
        # description y fk_product (existente). unit/image_src son opcionales.
        form = VariableForm(data={
            'name': 'Test Variable',
            'type': 1,
            'unit': 'kg',
            'description': 'A test variable',
            'fk_product': self.product.id,
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_variable_form_invalid_data(self):
        form = VariableForm(data={})
        self.assertFalse(form.is_valid())
        # Requeridos: name, type, description, fk_product.
        self.assertEqual(len(form.errors), 4)


class EquationFormTest(TestCase):
    def setUp(self):
        user = User.objects.create_user(username="owner", password="pw")
        business = Business.objects.create(
            name="Test Business", type=1, location="La Paz",
            description="d", fk_user=user, is_active=True,
        )
        product = Product.objects.create(
            name="Test Product", description="d", fk_business=business, is_active=True,
        )
        self.variable = Variable.objects.create(
            name="Var 1", fk_product=product, is_active=True,
        )

    def test_equation_form_valid_data(self):
        # fk_variable2..5 y fk_area son opcionales (null/blank en el modelo).
        form = EquationForm(data={
            'name': 'Test Equation',
            'description': 'A test equation',
            'expression': 'x + y',
            'fk_variable1': self.variable.id,
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_equation_form_invalid_data(self):
        form = EquationForm(data={})
        self.assertFalse(form.is_valid())
        # Requeridos: name, description, expression, fk_variable1.
        self.assertEqual(len(form.errors), 4)
