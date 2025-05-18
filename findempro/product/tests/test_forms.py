from django.test import TestCase
from findempro.product.forms import ProductForm, AreaForm
from findempro.product.models import Product, Area
from django.core.files.uploadedfile import SimpleUploadedFile

class ProductFormTest(TestCase):
    def test_valid_product_form(self):
        form_data = {
            'name': 'Test Product',
            'type': 'Type A',
            'description': 'A test product description',
            'fk_business': 1
        }
        file_data = {'image_src': SimpleUploadedFile("test_image.jpg", b"file_content")}
        form = ProductForm(data=form_data, files=file_data)
        self.assertTrue(form.is_valid())

    def test_invalid_product_form(self):
        form_data = {
            'name': '',  # Missing name
            'type': 'Type A',
            'description': 'A test product description',
            'fk_business': 1
        }
        form = ProductForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

class AreaFormTest(TestCase):
    def test_valid_area_form(self):
        form_data = {
            'name': 'Test Area',
            'description': 'A test area description',
            'fk_product': 1
        }
        file_data = {'image_src': SimpleUploadedFile("test_image.jpg", b"file_content")}
        form = AreaForm(data=form_data, files=file_data)
        self.assertTrue(form.is_valid())

    def test_invalid_area_form(self):
        form_data = {
            'name': '',  # Missing name
            'description': 'A test area description',
            'fk_product': 1
        }
        form = AreaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)