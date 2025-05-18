from django.test import TestCase
from simulate.forms import SimulationForm
from simulate.models import Simulation
from django.core.exceptions import ValidationError

class SimulationFormTest(TestCase):
    def setUp(self):
        # Set up any necessary data for the tests
        self.valid_data = {
            'quantity_time': 10,
            'unit_time': 'days',
            'fk_fdp': 1,  # Replace with a valid foreign key ID
            'fk_questionary_result': 1,  # Replace with a valid foreign key ID
            'demand_history': 'Sample demand history',
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