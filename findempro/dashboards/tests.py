# FILEPATH: /c:/Users/serio/FIDEMPRO-LACTEOS/findempro/dashboards/tests.py
from django.test import TestCase
from dashboards.models import Dashboard
from .models import Product  # Assuming you have a Product model

class DashboardModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up non-modified objects used by all test methods
        Product.objects.create(name='Test Product')
        Dashboard.objects.create(
            title='Test Dashboard',
            chart_type='bar',
            chart_data={"data": [1, 2, 3]},
            fk_product=Product.objects.get(name='Test Product'),
            widget_config={"config": "test"},
            layout_config={"layout": "test"}
        )

    def test_dashboard_creation(self):
        dashboard = Dashboard.objects.get(id=1)
        self.assertTrue(isinstance(dashboard, Dashboard))
        self.assertEqual(dashboard.__str__(), 'Dashboard for Test Product')

    def test_title_label(self):
        dashboard = Dashboard.objects.get(id=1)
        field_label = dashboard._meta.get_field('title').verbose_name
        self.assertEqual(field_label, 'title')

    def test_chart_type_label(self):
        dashboard = Dashboard.objects.get(id=1)
        field_label = dashboard._meta.get_field('chart_type').verbose_name
        self.assertEqual(field_label, 'chart type')

    def test_chart_data_default(self):
        dashboard = Dashboard.objects.get(id=1)
        self.assertEqual(dashboard.chart_data, {"data": [1, 2, 3]})

    def test_widget_config_default(self):
        dashboard = Dashboard.objects.get(id=1)
        self.assertEqual(dashboard.widget_config, {"config": "test"})

    def test_layout_config_default(self):
        dashboard = Dashboard.objects.get(id=1)
        self.assertEqual(dashboard.layout_config, {"layout": "test"})

    def test_is_active_default(self):
        dashboard = Dashboard.objects.get(id=1)
        self.assertTrue(dashboard.is_active)

    def test_fk_product_label(self):
        dashboard = Dashboard.objects.get(id=1)
        field_label = dashboard._meta.get_field('fk_product').verbose_name
        self.assertEqual(field_label, 'fk product')