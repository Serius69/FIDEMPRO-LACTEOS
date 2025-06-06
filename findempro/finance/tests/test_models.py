import pytest
from django.db.models.signals import post_save
from django.test import TestCase
from finance.models import FinanceRecommendation, FinanceRecommendationSimulation
from business.models import Business
from simulate.models import Simulation
from findempro.finance.data.finance_data import recommendation_data

# UNIT TESTS
@pytest.mark.django_db
class TestFinanceRecommendation(TestCase):
    def setUp(self):
        # Create a mock Business instance
        self.business = Business.objects.create(name="Test Business", is_active=True)

    def test_finance_recommendation_creation_signal(self):
        # Test if FinanceRecommendation objects are created when a Business is created
        recommendations = FinanceRecommendation.objects.filter(fk_business=self.business)
        self.assertEqual(len(recommendations), len(recommendation_data))
        for recommendation, data in zip(recommendations, recommendation_data):
            self.assertEqual(recommendation.name, data['name'])
            self.assertEqual(recommendation.recommendation, data['recommendation'])
            self.assertEqual(recommendation.threshold_value, data['threshold_value'])
            self.assertEqual(recommendation.variable_name, data['variable_name'])
            self.assertTrue(recommendation.is_active)

    def test_finance_recommendation_save_signal(self):
        # Test if FinanceRecommendation objects are updated when Business is updated
        self.business.is_active = False
        self.business.save()
        recommendations = FinanceRecommendation.objects.filter(fk_business=self.business)
        for recommendation in recommendations:
            self.assertFalse(recommendation.is_active)

@pytest.mark.django_db
class TestFinanceRecommendationSimulation(TestCase):
    def setUp(self):
        # Create mock instances for testing
        self.business = Business.objects.create(name="Test Business", is_active=True)
        self.simulation = Simulation.objects.create(name="Test Simulation")
        self.finance_recommendation = FinanceRecommendation.objects.create(
            name="Test Recommendation",
            variable_name="test_variable",
            threshold_value=100.00,
            recommendation="Test recommendation text",
            fk_business=self.business,
            is_active=True
        )

    def test_finance_recommendation_simulation_creation(self):
        # Test creation of FinanceRecommendationSimulation
        simulation_data = FinanceRecommendationSimulation.objects.create(
            data=50.0,
            fk_simulation=self.simulation,
            fk_finance_recommendation=self.finance_recommendation,
            is_active=True
        )
        self.assertEqual(simulation_data.data, 50.0)
        self.assertEqual(simulation_data.fk_simulation, self.simulation)
        self.assertEqual(simulation_data.fk_finance_recommendation, self.finance_recommendation)
        self.assertTrue(simulation_data.is_active)
              
# REGRESSION TESTS
@pytest.mark.django_db
class TestFinanceRecommendationModel(TestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Test Business", is_active=True)

    def test_finance_recommendation_creation(self):
        # Verify FinanceRecommendation instances are created when a Business is created
        recommendations = FinanceRecommendation.objects.filter(fk_business=self.business)
        self.assertEqual(len(recommendations), len(recommendation_data))
        for recommendation, data in zip(recommendations, recommendation_data):
            self.assertEqual(recommendation.name, data['name'])
            self.assertEqual(recommendation.recommendation, data['recommendation'])
            self.assertEqual(recommendation.threshold_value, data['threshold_value'])
            self.assertEqual(recommendation.variable_name, data['variable_name'])
            self.assertTrue(recommendation.is_active)

    def test_finance_recommendation_update(self):
        # Verify FinanceRecommendation instances are updated when Business is updated
        self.business.is_active = False
        self.business.save()
        recommendations = FinanceRecommendation.objects.filter(fk_business=self.business)
        for recommendation in recommendations:
            self.assertFalse(recommendation.is_active)

    def test_finance_recommendation_deletion(self):
        # Verify FinanceRecommendation instances are deleted when Business is deleted
        self.business.delete()
        recommendations = FinanceRecommendation.objects.filter(fk_business=self.business)
        self.assertEqual(len(recommendations), 0)

    def test_finance_recommendation_str_method(self):
        # Verify the __str__ method returns the correct string representation
        recommendation = FinanceRecommendation.objects.create(
            name="Test Recommendation",
            variable_name="test_variable",
            threshold_value=100.00,
            recommendation="Test recommendation text",
            fk_business=self.business,
            is_active=True
        )
        self.assertEqual(str(recommendation), "Test Recommendation")

    def test_field_validations(self):
        # Test max_length constraint on name and variable_name fields
        recommendation = FinanceRecommendation(
            name="x" * 256,  # Exceeding max_length
            variable_name="x" * 256,  # Exceeding max_length
            threshold_value=100.00,
            recommendation="Test recommendation text",
            fk_business=self.business,
            is_active=True
        )
        with self.assertRaises(Exception):
            recommendation.full_clean()

        # Test null constraint on required fields
        recommendation = FinanceRecommendation(
            name=None,
            variable_name=None,
            threshold_value=None,
            recommendation=None,
            fk_business=self.business,
            is_active=True
        )
        with self.assertRaises(Exception):
            recommendation.full_clean()

