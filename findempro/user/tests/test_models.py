import pytest
from django.contrib.auth.models import User
from user.models import UserProfile, ActivityLog
from social_django.models import UserSocialAuth
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.mark.django_db
def test_user_profile_creation():
    # Un signal post_save crea el UserProfile automáticamente.
    user = User.objects.create_user(username="testuser", password="password")
    assert UserProfile.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_user_profile_save_signal():
    user = User.objects.create_user(username="testuser", password="password")
    user_profile = UserProfile.objects.get(user=user)
    user_profile.bio = "Updated bio"
    user_profile.save()
    assert UserProfile.objects.get(user=user).bio == "Updated bio"


@pytest.mark.django_db
def test_user_profile_get_photo_url():
    user = User.objects.create_user(username="testuser", password="password")
    user_profile = UserProfile.objects.get(user=user)
    assert user_profile.get_photo_url() == "/static/images/users/user-dummy-img.webp"

    # Con una imagen subida devuelve su URL.
    image = SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg")
    user_profile.image_src = image
    user_profile.save()
    assert user_profile.get_photo_url() == user_profile.image_src.url


@pytest.mark.django_db
def test_user_profile_is_profile_complete():
    user = User.objects.create_user(username="testuser", password="password")
    user_profile = UserProfile.objects.get(user=user)
    assert not user_profile.is_profile_complete()

    # is_profile_complete() exige campos del User (first/last/email) y del perfil.
    user.first_name = "Test"
    user.last_name = "User"
    user.email = "test@example.com"
    user.save()

    user_profile.bio = "Bio"
    user_profile.state = "State"
    user_profile.country = "Country"
    user_profile.save()
    # Re-obtener para que profile.user refleje los campos recién guardados.
    user_profile = UserProfile.objects.get(user=user)
    assert user_profile.is_profile_complete()


@pytest.mark.django_db
def test_save_image_src_signal():
    # El signal save_social_image (google-oauth2) NO descarga la imagen:
    # deja image_src vacío y registra un ActivityLog con la URL obtenida.
    user = User.objects.create_user(username="testuser", password="password")
    UserSocialAuth.objects.create(
        user=user,
        provider="google-oauth2",
        extra_data={"picture": "http://example.com/image.jpg"}
    )
    user_profile = UserProfile.objects.get(user=user)
    assert not user_profile.image_src
    assert ActivityLog.objects.filter(
        user=user,
        action="Imagen de perfil de Google obtenida",
    ).exists()


@pytest.mark.django_db
def test_activity_log_creation():
    user = User.objects.create_user(username="testuser", password="password")
    log = ActivityLog.objects.create(user=user, action="Test Action", details="Test Details")
    assert ActivityLog.objects.filter(user=user, action="Test Action").exists()
    assert log.details == "Test Details"
