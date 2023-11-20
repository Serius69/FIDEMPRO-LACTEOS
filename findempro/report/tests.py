# FILEPATH: /c:/Users/serio/FIDEMPRO-LACTEOS/findempro/report/tests.py
from django.test import TestCase
from report.models import Report
from product.models import Product

class ReportModelTest(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name='Test Product')
        self.report = Report.objects.create(
            title='Test Report',
            content={'key': 'value'},
            is_active=True,
            fk_product=self.product
        )

    def test_report_creation(self):
        self.assertEqual(self.report.title, 'Test Report')
        self.assertEqual(self.report.content, {'key': 'value'})
        self.assertEqual(self.report.fk_product, self.product)
        self.assertTrue(self.report.is_active)

    def test_str_method(self):
        self.assertEqual(str(self.report), 'Test Report')