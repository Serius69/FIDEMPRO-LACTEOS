# FILEPATH: /c:/Users/serio/FIDEMPRO-LACTEOS/findempro/finance/tests.py
from django.test import TestCase
from finance.models import FinanceRecommendation
from business.models import Business

class FinanceRecommendationModelTest(TestCase):
    def setUp(self):
        self.business = Business.objects.create(name='Test Business')
        self.finance_recommendation = FinanceRecommendation.objects.create(
            name='Test Finance',
            recommendation='Test Recommendation',
            description='Test Description',
            fk_business=self.business,
            is_active=True
        )

    def test_finance_recommendation_creation(self):
        self.assertEqual(self.finance_recommendation.name, 'Test Finance')
        self.assertEqual(self.finance_recommendation.recommendation, 'Test Recommendation')
        self.assertEqual(self.finance_recommendation.description, 'Test Description')
        self.assertEqual(self.finance_recommendation.fk_business, self.business)
        self.assertTrue(self.finance_recommendation.is_active)

    def test_create_finance_recommendation_function(self):
        new_business = Business.objects.create(name='New Business')
        finance_data = [
            {
                'name': 'New Finance',
                'recommendation': 'New Recommendation',
                'description': 'New Description',
            }
        ]
        FinanceRecommendation.create_finance_recommendation(Business, new_business, True, finance_data=finance_data)
        finance_recommendation = FinanceRecommendation.objects.get(name='New Finance')
        self.assertIsNotNone(finance_recommendation)
        self.assertEqual(finance_recommendation.fk_business, new_business)

    def test_save_finance_recommendation_method(self):
        self.business.is_active = False
        self.business.save()
        self.finance_recommendation.refresh_from_db()
        self.assertFalse(self.finance_recommendation.is_active)