from io import BytesIO
from PIL import Image
from django.test import TestCase
from django.contrib.auth.models import User
from product.forms import ProductForm, AreaForm
from product.models import Product
from business.models import Business
from django.core.files.uploadedfile import SimpleUploadedFile


def valid_image(name="test_image.jpg"):
    """JPEG válido en memoria; el ImageField y clean_image_src exigen imagen real image/jpeg."""
    buffer = BytesIO()
    Image.new("RGB", (2, 2), color="red").save(buffer, format="JPEG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/jpeg")


class ProductFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="formuser", password="password")
        self.business = Business.objects.create(
            name="Test Business",
            type=1,
            location="La Paz",
            description="Negocio de prueba",
            fk_user=self.user,
            is_active=True,
        )

    def test_valid_product_form(self):
        form_data = {
            'name': 'Test Product',
            'type': 1,  # IntegerField con choices
            'description': 'A test product description',
            'fk_business': self.business.id,
        }
        file_data = {'image_src': valid_image()}
        form = ProductForm(data=form_data, files=file_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_product_form(self):
        form_data = {
            'name': '',  # Missing name
            'type': 1,
            'description': 'A test product description',
            'fk_business': self.business.id,
        }
        form = ProductForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)


class AreaFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="areauser", password="password")
        self.business = Business.objects.create(
            name="Test Business",
            type=1,
            location="La Paz",
            description="Negocio de prueba",
            fk_user=self.user,
            is_active=True,
        )
        self.product = Product.objects.create(
            name="Test Product",
            description="Test Description",
            fk_business=self.business,
        )

    def test_valid_area_form(self):
        form_data = {
            'name': 'Test Area',
            'description': 'A test area description',
            'fk_product': self.product.id,
        }
        file_data = {'image_src': valid_image()}
        form = AreaForm(data=form_data, files=file_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_area_form(self):
        form_data = {
            'name': '',  # Missing name
            'description': 'A test area description',
            'fk_product': self.product.id,
        }
        form = AreaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
