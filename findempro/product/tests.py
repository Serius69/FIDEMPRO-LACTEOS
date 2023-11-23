# FILEPATH: /c:/Users/serio/FIDEMPRO-LACTEOS/findempro/product/tests.py
from django.test import TestCase
from product.models import Product
from business.models import Business

class ProductModelTest(TestCase):
    def setUp(self):
        self.business = Business.objects.create(name='Test Business')
        self.product = Product.objects.create(
            name='Test Product',
            description='Test Description',
            is_active=True,
            fk_business=self.business,
            type=1
        )

    def test_product_creation(self):
        self.assertEqual(self.product.name, 'Test Product')
        self.assertEqual(self.product.description, 'Test Description')
        self.assertEqual(self.product.fk_business, self.business)
        self.assertTrue(self.product.is_active)

    def test_create_product_function(self):
        new_business = Business.objects.create(name='New Business')
        product_data = [
            {
                'name': 'New Product',
                'description': 'New Description',
                'type': 1,
                'is_active': True,
            }
        ]
        Product.create_product(Business, new_business, True, product_data=product_data)
        new_product = Product.objects.get(name='New Product')
        self.assertIsNotNone(new_product)
        self.assertEqual(new_product.fk_business, new_business)

    def test_save_product_method(self):
        self.business.is_active = False
        self.business.save()
        self.product.refresh_from_db()
        self.assertFalse(self.product.is_active)