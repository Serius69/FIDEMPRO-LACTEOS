"""
Finance model tests — all classes use django.test.TestCase.

Mixing @pytest.mark.django_db classes with TestCase subclasses in the same
module causes outer-transaction conflicts in pytest-django (the
@pytest.mark.django_db class commits between TestCase savepoints, breaking
rollback isolation). Keeping everything as TestCase avoids that problem.
"""
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model

from finance.models import FinanceRecommendation, FinanceRecommendationSimulation
from business.models import Business
from simulate.models import Simulation, ProbabilisticDensityFunction
from finance.data.finance_test_data import recommendation_data

User = get_user_model()

_DEMAND_HISTORY = [100, 110, 95, 120, 130, 105, 115, 98, 122, 108]  # ≥10 required


def _make_user(username):
    return User.objects.create_user(username=username, password='pw', email=f'{username}@test.com')


def _make_business(user, name='Test Business'):
    return Business.objects.create(name=name, fk_user=user, is_active=True)


# ─────────────────────────────────────────────
# UNIT TESTS
# ─────────────────────────────────────────────
class TestFinanceRecommendation(TestCase):
    def setUp(self):
        self.user = _make_user('rec_unit_user')
        self.business = _make_business(self.user)

    def test_finance_recommendation_creation_signal(self):
        recommendations = (
            FinanceRecommendation.objects.filter(fk_business=self.business)
            .order_by('id')
        )
        self.assertEqual(recommendations.count(), len(recommendation_data))
        for recommendation, data in zip(recommendations, recommendation_data):
            self.assertEqual(recommendation.name, data['name'])
            self.assertEqual(recommendation.recommendation, data['recommendation'])
            self.assertAlmostEqual(
                float(recommendation.threshold_value), float(data['threshold_value'])
            )
            self.assertEqual(recommendation.variable_name, data['variable_name'])
            self.assertTrue(recommendation.is_active)

    def test_finance_recommendation_save_signal(self):
        self.business.is_active = False
        self.business.save()
        for rec in FinanceRecommendation.objects.filter(fk_business=self.business):
            self.assertFalse(rec.is_active)


# ─────────────────────────────────────────────
# FinanceRecommendationSimulation
# ─────────────────────────────────────────────
class TestFinanceRecommendationSimulation(TestCase):
    """Property tests (no DB needed) and one DB creation test."""

    def setUp(self):
        from product.models import Product
        from questionary.models import Questionary, QuestionaryResult

        self.user = _make_user('sim_test_user')
        self.business = _make_business(self.user, 'SimBiz')
        product = Product.objects.create(
            name='Prod', fk_business=self.business, description='Test product'
        )
        questionary = Questionary.objects.create(questionary='Q1', fk_product=product)
        qr = QuestionaryResult.objects.create(fk_questionary=questionary)
        fdp, _ = ProbabilisticDensityFunction.objects.get_or_create(
            distribution_type=1,
            fk_business=self.business,
            defaults={'mean_param': 500.0, 'std_dev_param': 80.0},
        )
        self.simulation = Simulation.objects.create(
            fk_fdp=fdp,
            fk_questionary_result=qr,
            demand_history=_DEMAND_HISTORY,
            quantity_time=12,
            unit_time='months',
        )

    def test_creation_with_required_fields(self):
        rec = FinanceRecommendationSimulation.objects.create(
            fk_simulation=self.simulation,
            category='profitability',
            severity='high',
            priority='high',
            metric_value=50.0,
            title='Margen bajo',
        )
        self.assertEqual(rec.metric_value, 50.0)
        self.assertEqual(rec.fk_simulation, self.simulation)
        self.assertTrue(rec.is_active)

    def test_impact_score_high_high(self):
        rec = FinanceRecommendationSimulation(severity='high', priority='high', category='costs')
        self.assertAlmostEqual(rec.impact_score, 3.0)

    def test_impact_score_low_low(self):
        rec = FinanceRecommendationSimulation(severity='low', priority='low', category='efficiency')
        self.assertAlmostEqual(rec.impact_score, 1.0)

    def test_needs_immediate_attention_true(self):
        for severity in ('high', 'critical'):
            rec = FinanceRecommendationSimulation(severity=severity, priority='high')
            self.assertTrue(rec.needs_immediate_attention, f'severity={severity}')

    def test_needs_immediate_attention_false_low_priority(self):
        rec = FinanceRecommendationSimulation(severity='high', priority='low')
        self.assertFalse(rec.needs_immediate_attention)

    def test_str_method(self):
        rec = FinanceRecommendationSimulation(
            title='Test', severity='medium', category='financial'
        )
        self.assertIn('Test', str(rec))
        self.assertIn('Financiero', str(rec))


# ─────────────────────────────────────────────
# REGRESSION TESTS
# ─────────────────────────────────────────────
class TestFinanceRecommendationModel(TestCase):
    def setUp(self):
        self.user = _make_user('rec_regression_user')
        self.business = _make_business(self.user)

    def test_finance_recommendation_creation(self):
        recommendations = (
            FinanceRecommendation.objects.filter(fk_business=self.business)
            .order_by('id')
        )
        self.assertEqual(recommendations.count(), len(recommendation_data))
        for recommendation, data in zip(recommendations, recommendation_data):
            self.assertEqual(recommendation.name, data['name'])
            self.assertEqual(recommendation.recommendation, data['recommendation'])
            self.assertAlmostEqual(
                float(recommendation.threshold_value), float(data['threshold_value'])
            )
            self.assertEqual(recommendation.variable_name, data['variable_name'])
            self.assertTrue(recommendation.is_active)

    def test_finance_recommendation_update(self):
        self.business.is_active = False
        self.business.save()
        for rec in FinanceRecommendation.objects.filter(fk_business=self.business):
            self.assertFalse(rec.is_active)

    def test_finance_recommendation_deletion(self):
        business_pk = self.business.pk
        before_count = FinanceRecommendation.objects.filter(
            fk_business_id=business_pk
        ).count()
        self.assertEqual(before_count, len(recommendation_data))

        deleted_count, _ = FinanceRecommendation.objects.filter(
            fk_business_id=business_pk
        ).delete()
        self.assertEqual(deleted_count, len(recommendation_data))
        self.assertEqual(
            FinanceRecommendation.objects.filter(fk_business_id=business_pk).count(), 0
        )

    def test_finance_recommendation_str_method(self):
        recommendation = FinanceRecommendation.objects.create(
            name="Test Recommendation",
            variable_name="test_variable",
            threshold_value=Decimal('100.00'),
            recommendation="Test recommendation text",
            fk_business=self.business,
            is_active=True
        )
        self.assertEqual(str(recommendation), "Test Recommendation")

    def test_field_validations_max_length(self):
        recommendation = FinanceRecommendation(
            name="x" * 256,
            variable_name="x" * 256,
            threshold_value=Decimal('100.00'),
            recommendation="Test recommendation text",
            fk_business=self.business,
            is_active=True
        )
        with self.assertRaises(Exception):
            recommendation.full_clean()
