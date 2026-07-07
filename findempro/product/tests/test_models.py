import pytest
from io import BytesIO
from PIL import Image
from django.contrib.auth.models import User
from product.models import Product, Area
from business.models import Business
from django.core.files.uploadedfile import SimpleUploadedFile


def make_user(username="testuser"):
    return User.objects.create_user(username=username, password="password")


def make_business(name="Test Business", user=None):
    """Crea un Business con todos los campos requeridos por el esquema vigente."""
    if user is None:
        user = make_user()
    return Business.objects.create(
        name=name,
        type=1,
        location="La Paz",
        description="Negocio de prueba",
        fk_user=user,
        is_active=True,
    )


def valid_image(name="test_image.jpg"):
    """Genera un JPEG válido en memoria (los validadores del modelo abren la imagen con PIL)."""
    buffer = BytesIO()
    Image.new("RGB", (2, 2), color="red").save(buffer, format="JPEG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/jpeg")


@pytest.mark.django_db
def test_product_str():
    business = make_business()
    product = Product.objects.create(
        name="Test Product",
        description="Test Description",
        is_active=True,
        type=1,
        profit_margin=10.00,
        earnings=100.00,
        inventory_levels=50,
        production_output=20,
        demand_forecast=30,
        costs=50.00,
        is_ready=True,
        fk_business=business,
    )
    # __str__ incluye el negocio: "{name} - {fk_business.name}"
    assert str(product) == f"Test Product - {business.name}"


@pytest.mark.django_db
def test_product_get_photo_url_with_image():
    product = Product.objects.create(
        name="Test Product",
        description="Test Description",
        image_src=valid_image(),
        fk_business=make_business(),
    )
    assert product.get_photo_url() == product.image_src.url


@pytest.mark.django_db
def test_product_get_photo_url_without_image():
    product = Product.objects.create(
        name="Test Product",
        description="Test Description",
        fk_business=make_business(),
    )
    assert product.get_photo_url() == "/static/images/product/product-dummy-img.webp"


@pytest.mark.django_db
def test_area_str():
    product = Product.objects.create(
        name="Test Product",
        description="Test Description",
        fk_business=make_business(),
    )
    area = Area.objects.create(
        name="Test Area",
        description="Test Area Description",
        fk_product=product,
    )
    # __str__ del área: "{name} - {fk_product.name}"
    assert str(area) == "Test Area - Test Product"


@pytest.mark.django_db
def test_area_get_photo_url_with_image():
    product = Product.objects.create(
        name="Test Product",
        description="Test Description",
        fk_business=make_business(),
    )
    area = Area.objects.create(
        name="Test Area",
        description="Test Area Description",
        image_src=valid_image(),
        fk_product=product,
    )
    assert area.get_photo_url() == area.image_src.url


@pytest.mark.django_db
def test_area_get_photo_url_without_image():
    product = Product.objects.create(
        name="Test Product",
        description="Test Description",
        fk_business=make_business(),
    )
    area = Area.objects.create(
        name="Test Area",
        description="Test Area Description",
        fk_product=product,
    )
    # get_photo_url del área apunta a la imagen dummy del área
    assert area.get_photo_url() == "/static/images/area/area-dummy-img.webp"


# REGRESSION TESTS
@pytest.mark.django_db
def test_product_creation():
    business = make_business()
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
        fk_business=business,
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
    # is_ready lo recalcula un signal post_save: sin áreas ni variables queda False
    assert product.fk_business == business


@pytest.mark.django_db
def test_product_update():
    business = make_business()
    product = Product.objects.create(
        name="Test Product",
        description="Test Description",
        fk_business=business,
    )
    product.name = "Updated Product"
    product.description = "Updated Description"
    product.save()
    updated_product = Product.objects.get(id=product.id)
    assert updated_product.name == "Updated Product"
    assert updated_product.description == "Updated Description"


@pytest.mark.django_db
def test_product_deletion():
    business = make_business()
    product = Product.objects.create(
        name="Test Product",
        description="Test Description",
        fk_business=business,
    )
    product_id = product.id
    product.delete()
    assert not Product.objects.filter(id=product_id).exists()


@pytest.mark.django_db
def test_product_type_choices():
    business = make_business()
    product = Product.objects.create(
        name="Test Product",
        description="Test Description",
        type=2,
        fk_business=business,
    )
    assert product.type == 2
    # type 2 corresponde a "Servicio" en el esquema vigente
    assert dict(Product.TYPE_CHOICES)[product.type] == "Servicio"


@pytest.mark.django_db
def test_product_field_constraints():
    business = make_business()
    product = Product.objects.create(
        name="A" * 100,  # max_length constraint
        description="Test Description",
        fk_business=business,
    )
    assert len(product.name) == 100
    with pytest.raises(Exception):
        Product.objects.create(
            name=None,  # null constraint (full_clean lo rechaza)
            description="Test Description",
            fk_business=business,
        )
