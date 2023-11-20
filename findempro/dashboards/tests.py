# FILEPATH: /c:/Users/serio/FIDEMPRO-LACTEOS/findempro/dashboards/tests.py
from django.test import TestCase
from dashboards.models import DemandBehavior, Demand
from products.models import Product

class DemandBehaviorModelTest(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name='Test Product')
        self.current_demand = Demand.objects.create(product=self.product, quantity=100)
        self.predicted_demand = Demand.objects.create(product=self.product, quantity=120)
        self.demand_behavior = DemandBehavior.objects.create(
            current_demand=self.current_demand,
            predicted_demand=self.predicted_demand
        )

    def test_demand_behavior_creation(self):
        self.assertEqual(self.demand_behavior.current_demand, self.current_demand)
        self.assertEqual(self.demand_behavior.predicted_demand, self.predicted_demand)
        self.assertTrue(self.demand_behavior.is_active)

    def test_calculate_elasticity_method(self):
        elasticity_type, percentage_change = self.demand_behavior.calculate_elasticity()
        self.assertEqual(elasticity_type, 'Elastica')
        self.assertEqual(percentage_change, 20.0)

    def test_create_demand_behavior_function(self):
        new_product = Product.objects.create(name='New Product')
        new_demand = Demand.objects.create(product=new_product, quantity=150, is_predicted=True)
        DemandBehavior.create_demand_behavior(Demand, new_demand, True)
        demand_behavior = DemandBehavior.objects.get(predicted_demand=new_demand)
        self.assertIsNotNone(demand_behavior)

    def test_update_demand_behavior_method(self):
        new_demand = Demand.objects.create(product=self.product, quantity=130)
        self.demand_behavior.update_demand_behavior(new_demand)
        self.assertEqual(self.demand_behavior.predicted_demand, new_demand)
        self.assertEqual(self.demand_behavior.quantity, new_demand)

    def test_predict_demand_behavior_method(self):
        predicted_demand = self.demand_behavior.predict_demand_behavior(None)
        self.assertEqual(predicted_demand, 110)