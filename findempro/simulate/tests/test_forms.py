import json
from django.test import TestCase
from django.contrib.auth.models import User
from simulate.forms import SimulationForm
from simulate.models import Simulation, ProbabilisticDensityFunction
from business.models import Business
from product.models import Product
from questionary.models import Questionary, QuestionaryResult


class SimulationFormTest(TestCase):
    def setUp(self):
        # Grafo mínimo válido: User → Business → (signal crea PDFs) → Product →
        # Questionary → QuestionaryResult. Antes el test usaba FKs hardcodeadas
        # (fk_fdp=1) inexistentes, por lo que el form nunca era válido.
        user = User.objects.create_user(username='form_user', password='pw_12345678')
        business = Business.objects.create(
            name="Neg", type=1, location="LP", description="d",
            fk_user=user, is_active=True,
        )
        pdf = ProbabilisticDensityFunction.objects.filter(
            fk_business=business, distribution_type=1).first()
        product = Product.objects.create(
            name="Prod", description="desc", is_active=True, fk_business=business)
        questionary = Questionary.objects.create(
            questionary="Q1", fk_product=product, is_active=True)
        qresult = QuestionaryResult.objects.create(
            fk_questionary=questionary, is_active=True)

        self.valid_data = {
            'quantity_time': 10,
            'unit_time': 'days',
            'fk_fdp': pdf.id,
            'fk_questionary_result': qresult.id,
            # El form exige al menos 10 puntos de historial de demanda.
            'demand_history': json.dumps([100, 120, 130, 110, 140, 125, 135, 150, 145, 160, 155]),
        }

    def test_simulation_form_valid(self):
        form = SimulationForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_simulation_form_invalid_missing_fields(self):
        invalid_data = self.valid_data.copy()
        invalid_data.pop('quantity_time')  # Remove a required field
        form = SimulationForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('quantity_time', form.errors)

    def test_simulation_form_invalid_field_values(self):
        invalid_data = self.valid_data.copy()
        invalid_data['quantity_time'] = -5  # Invalid value for quantity_time
        form = SimulationForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('quantity_time', form.errors)