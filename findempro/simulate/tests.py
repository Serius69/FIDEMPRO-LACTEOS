# FILEPATH: /c:/Users/serio/FIDEMPRO-LACTEOS/findempro/simulate/tests.py
from django.test import TestCase
from datetime import date
from decimal import Decimal
from simulate.models import ResultSimulation
from product.models import Product
from questionary.models import QuestionaryResult
from scenario.models import SimulationScenario

class ResultSimulationModelTest(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name='Test Product')
        self.questionary_result = QuestionaryResult.objects.create(name='Test QuestionaryResult')
        self.simulation_scenario = SimulationScenario.objects.create(name='Test SimulationScenario')
        self.result_simulation = ResultSimulation.objects.create(
            product=self.product,
            simulation_date=date.today(),
            demand_mean=Decimal('10.00'),
            demand_std_deviation=Decimal('2.00'),
            fk_questionary_result=self.questionary_result,
            fk_simulation_scenario=self.simulation_scenario,
            is_active=True
        )

    def test_result_simulation_creation(self):
        self.assertEqual(self.result_simulation.product, self.product)
        self.assertEqual(self.result_simulation.simulation_date, date.today())
        self.assertEqual(self.result_simulation.demand_mean, Decimal('10.00'))
        self.assertEqual(self.result_simulation.demand_std_deviation, Decimal('2.00'))
        self.assertEqual(self.result_simulation.fk_questionary_result, self.questionary_result)
        self.assertEqual(self.result_simulation.fk_simulation_scenario, self.simulation_scenario)
        self.assertTrue(self.result_simulation.is_active)

    def test_str_method(self):
        self.assertEqual(str(self.result_simulation), f"{self.product} - {date.today()}")