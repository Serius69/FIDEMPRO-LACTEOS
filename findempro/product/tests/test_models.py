import pytest
from django.utils import timezone
from findempro.product.models import Product, Area
from business.models import Business
from django.core.files.uploadedfile import SimpleUploadedFile

@pytest.mark.django_db
def test_product_str():
    product = Product.objects.create(
        name="Test Product",
        description="Test Description",
        is_active=True,
        date_created=timezone.now(),
        last_updated=timezone.now(),
        type=1,
        profit_margin=10.00,
        earnings=100.00,
        inventory_levels=50,
        production_output=20,
        demand_forecast=30,
        costs=50.00,
        is_ready=True,
        fk_business=Business.objects.create(name="Test Business")
    )
    assert str(product) == "Test Product"

@pytest.mark.django_db
def test_product_get_photo_url_with_image():
    product = Product.objects.create(
        name="Test Product",
        description="Test Description",
        image_src=SimpleUploadedFile(name='test_image.jpg', content=b'', content_type='image/jpeg'),
        fk_business=Business.objects.create(name="Test Business")
    )
    assert product.get_photo_url() == product.image_src.url

@pytest.mark.django_db
def test_product_get_photo_url_without_image():
    product = Product.objects.create(
        name="Test Product",
        description="Test Description",
        fk_business=Business.objects.create(name="Test Business")
    )
    assert product.get_photo_url() == "/static/images/product/product-dummy-img.webp"

@pytest.mark.django_db
def test_area_str():
    product = Product.objects.create(
        name="Test Product",
        description="Test Description",
        fk_business=Business.objects.create(name="Test Business")
    )
    area = Area.objects.create(
        name="Test Area",
        description="Test Area Description",
        fk_product=product
    )
    assert str(area) == "Test Area"

@pytest.mark.django_db
def test_area_get_photo_url_with_image():
    product = Product.objects.create(
        name="Test Product",
        description="Test Description",
        fk_business=Business.objects.create(name="Test Business")
    )
    area = Area.objects.create(
        name="Test Area",
        description="Test Area Description",
        image_src=SimpleUploadedFile(name='test_image.jpg', content=b'', content_type='image/jpeg'),
        fk_product=product
    )
    assert area.get_photo_url() == area.image_src.url

@pytest.mark.django_db
def test_area_get_photo_url_without_image():
    product = Product.objects.create(
        name="Test Product",
        description="Test Description",
        fk_business=Business.objects.create(name="Test Business")
    )
    area = Area.objects.create(
        name="Test Area",
        description="Test Area Description",
        fk_product=product
    )
    assert area.get_photo_url() == "/static/images/product/product-dummy-img.webp"

    
# REGRESSION TESTS
@pytest.mark.django_db
def test_product_creation():
    business = Business.objects.create(name="Test Business")
    product = Product.objects.create(
        name="Test Product",
        description="Test Description",
        is_active=True,
        type=1,
        profit_margin=15.00,
        earnings=200.00,
        inventory_levels=100,
        production_output=50,
        demand_forecast=60,
        costs=80.00,
        is_ready=True,
        fk_business=business
    )
    assert product.name == "Test Product"
    assert product.description == "Test Description"
    assert product.is_active is True
    assert product.type == 1
    assert product.profit_margin == 15.00
    assert product.earnings == 200.00
    assert product.inventory_levels == 100
    assert product.production_output == 50
    assert product.demand_forecast == 60
    assert product.costs == 80.00
    assert product.is_ready is True
    assert product.fk_business == business

@pytest.mark.django_db
def test_product_update():
    business = Business.objects.create(name="Test Business")
    product = Product.objects.create(
        name="Test Product",
        description="Test Description",
        fk_business=business
    )
    product.name = "Updated Product"
    product.description = "Updated Description"
    product.save()
    updated_product = Product.objects.get(id=product.id)
    assert updated_product.name == "Updated Product"
    assert updated_product.description == "Updated Description"

@pytest.mark.django_db
def test_product_deletion():
    business = Business.objects.create(name="Test Business")
    product = Product.objects.create(
        name="Test Product",
        description="Test Description",
        fk_business=business
    )
    product_id = product.id
    product.delete()
    assert not Product.objects.filter(id=product_id).exists()

@pytest.mark.django_db
def test_product_type_choices():
    business = Business.objects.create(name="Test Business")
    product = Product.objects.create(
        name="Test Product",
        description="Test Description",
        type=2,
        fk_business=business
    )
    assert product.type == 2
    assert dict(Product.TYPE_CHOICES)[product.type] == "Service"

@pytest.mark.django_db
def test_product_field_constraints():
    business = Business.objects.create(name="Test Business")
    product = Product.objects.create(
        name="A" * 100,  # max_length constraint
        description="Test Description",
        fk_business=business
    )
    assert len(product.name) == 100
    with pytest.raises(Exception):
        Product.objects.create(
            name=None,  # null constraint
            description="Test Description",
            fk_business=business
        )


