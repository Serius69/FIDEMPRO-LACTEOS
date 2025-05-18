import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from findempro.business.models import Business

@pytest.mark.django_db
def test_business_creation():
    user = User.objects.create_user(username='testuser', password='testpassword')
    business = Business.objects.create(
        name="Test Business",
        type=1,
        location="Test Location",
        description="Test Description",
        fk_user=user,
        is_active=True,
    )
    assert business.name == "Test Business"
    assert business.type == 1
    assert business.location == "Test Location"
    assert business.description == "Test Description"
    assert business.fk_user == user
    assert business.is_active is True
    assert business.date_created is not None
    assert business.last_updated is not None

@pytest.mark.django_db
def test_business_str_method():
    user = User.objects.create_user(username='testuser', password='testpassword')
    business = Business.objects.create(
        name="Test Business",
        type=1,
        location="Test Location",
        description="Test Description",
        fk_user=user,
    )
    assert str(business) == "Test Business"

@pytest.mark.django_db
def test_business_get_photo_url_with_image():
    user = User.objects.create_user(username='testuser', password='testpassword')
    image = SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg")
    business = Business.objects.create(
        name="Test Business",
        type=1,
        location="Test Location",
        description="Test Description",
        fk_user=user,
        image_src=image,
    )
    assert business.get_photo_url() == business.image_src.url

@pytest.mark.django_db
def test_business_get_photo_url_without_image():
    user = User.objects.create_user(username='testuser', password='testpassword')
    business = Business.objects.create(
        name="Test Business",
        type=1,
        location="Test Location",
        description="Test Description",
        fk_user=user,
    )
    assert business.get_photo_url() == "/static/images/business/business-dummy-img.webp"
    
   
# REGRESSION TESTS

@pytest.mark.django_db
def test_business_type_choices():
    user = User.objects.create_user(username='testuser', password='testpassword')
    business = Business.objects.create(
        name="Test Business",
        type=2,
        location="Test Location",
        description="Test Description",
        fk_user=user,
    )
    assert business.type == 2
    assert dict(Business.TYPE_CHOICES)[business.type] == "Agriculture "

@pytest.mark.django_db
def test_business_default_values():
    user = User.objects.create_user(username='testuser', password='testpassword')
    business = Business.objects.create(
        name="Test Business",
        location="Test Location",
        description="Test Description",
        fk_user=user,
    )
    assert business.type == 1
    assert business.is_active is True

@pytest.mark.django_db
def test_business_last_updated_auto_update():
    user = User.objects.create_user(username='testuser', password='testpassword')
    business = Business.objects.create(
        name="Test Business",
        type=1,
        location="Test Location",
        description="Test Description",
        fk_user=user,
    )
    initial_last_updated = business.last_updated
    business.name = "Updated Business Name"
    business.save()
    assert business.last_updated > initial_last_updated

@pytest.mark.django_db
def test_business_reverse_relationship():
    user = User.objects.create_user(username='testuser', password='testpassword')
    business1 = Business.objects.create(
        name="Business 1",
        type=1,
        location="Location 1",
        description="Description 1",
        fk_user=user,
    )
    business2 = Business.objects.create(
        name="Business 2",
        type=2,
        location="Location 2",
        description="Description 2",
        fk_user=user,
    )
    assert user.fk_user_business.count() == 2
    assert business1 in user.fk_user_business.all()
    assert business2 in user.fk_user_business.all()

@pytest.mark.django_db
def test_business_image_field_nullability():
    user = User.objects.create_user(username='testuser', password='testpassword')
    business = Business.objects.create(
        name="Test Business",
        type=1,
        location="Test Location",
        description="Test Description",
        fk_user=user,
    )
    assert business.image_src is None



    