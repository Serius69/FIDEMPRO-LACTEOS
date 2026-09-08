from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from business.models import Business
from product.models import Product
from report.models import Report
from tenancy.models import OrganizationMembership

pytestmark = pytest.mark.django_db


def png():
    data = BytesIO()
    Image.new('RGB', (12, 12), color='green').save(data, format='PNG')
    return data.getvalue()


@pytest.fixture
def owned(settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path / 'media')
    settings.DEBUG = False
    cache.clear()
    owner = User.objects.create_user(username='media-owner', password='synthetic-only')
    business = Business.objects.create(name='Synthetic Media', type=1, location='Synthetic', fk_user=owner)
    business.image_src.save('synthetic.png', SimpleUploadedFile('synthetic.png', png(), content_type='image/png'))
    product = Product.objects.create(name='Synthetic Product', description='Synthetic', fk_business=business)
    return owner, business, product


def media_url(business):
    return f'/private-media/business/{business.pk}/'


def test_business_image_owner_and_private_headers(client, owned):
    owner, business, _ = owned
    client.force_login(owner)
    response = client.get(media_url(business))
    assert response.status_code == 200
    assert b''.join(response.streaming_content) == png()
    assert response['Content-Type'] == 'image/png'
    assert 'private' in response['Cache-Control'] and 'no-store' in response['Cache-Control']
    assert response['X-Content-Type-Options'] == 'nosniff'
    assert business.get_photo_url() == media_url(business)


def test_image_denies_anonymous_other_tenant_and_foreign_staff(client, owned):
    owner, business, _ = owned
    assert client.get(media_url(business)).status_code in (302, 403)
    stranger = User.objects.create_user(username='media-stranger', is_staff=True)
    client.force_login(stranger)
    assert client.get(media_url(business)).status_code == 404


def test_image_rechecks_membership_after_successful_cached_request(client, owned):
    owner, business, _ = owned
    client.force_login(owner)
    assert client.get(media_url(business)).status_code == 200
    OrganizationMembership.objects.filter(user=owner, organization=business.organization).update(is_active=False)
    assert client.get(media_url(business)).status_code == 404


def test_image_denies_inactive_organization(client, owned):
    owner, business, _ = owned
    client.force_login(owner)
    business.organization.is_active = False
    business.organization.save(update_fields=['is_active'])
    assert client.get(media_url(business)).status_code == 404


def test_image_denies_inactive_object_missing_unknown_and_path_routes(client, owned):
    owner, business, _ = owned
    client.force_login(owner)
    assert client.get('/private-media/business/999999/').status_code == 404
    assert client.get('/private-media/business/../../private.txt').status_code == 404
    assert client.get('/private-media/unknown/1/').status_code == 404
    business.image_src.delete(save=True)
    assert client.get(media_url(business)).status_code == 404
    business.is_active = False
    business.save(update_fields=['is_active'])
    assert client.get(media_url(business)).status_code == 404


def test_image_rejects_escaping_storage_name_and_symlink(client, owned, settings, tmp_path):
    owner, business, _ = owned
    client.force_login(owner)
    outside = tmp_path / 'outside.png'
    outside.write_bytes(png())
    Business.objects.filter(pk=business.pk).update(image_src='../outside.png')
    assert client.get(media_url(business)).status_code == 404
    link = Path(settings.MEDIA_ROOT) / 'escape.png'
    link.symlink_to(outside)
    Business.objects.filter(pk=business.pk).update(image_src='escape.png')
    assert client.get(media_url(business)).status_code == 404


def test_profile_image_is_only_accessible_to_its_owner(client, owned):
    owner, _, _ = owned
    profile = owner.userprofile
    profile.image_src.save('profile.png', SimpleUploadedFile('profile.png', png(), content_type='image/png'))
    url = f'/private-media/profile/{profile.pk}/'
    client.force_login(owner)
    assert client.get(url).status_code == 200
    other = User.objects.create_user(username='profile-other')
    client.force_login(other)
    assert client.get(url).status_code == 404


def test_cached_pdf_revocation_denies_previously_available_bytes(client, owned):
    owner, business, product = owned
    report = Report.objects.create(title='Synthetic PDF', content={'synthetic': True}, fk_product=product)
    cache.set(f'pdf_bytes:{report.pk}:{owner.pk}', b'%PDF-synthetic')
    client.force_login(owner)
    assert client.get(f'/report/pdf/download/{report.pk}/').status_code == 200
    OrganizationMembership.objects.filter(user=owner, organization=business.organization).update(is_active=False)
    assert client.get(f'/report/pdf/download/{report.pk}/').status_code == 404


def test_cached_pdf_does_not_survive_business_ownership_change(client, owned):
    owner, business, product = owned
    report = Report.objects.create(title='Synthetic PDF', content={'synthetic': True}, fk_product=product)
    cache.set(f'pdf_bytes:{report.pk}:{owner.pk}', b'%PDF-synthetic')
    other = User.objects.create_user(username='pdf-new-owner')
    Business.objects.filter(pk=business.pk).update(fk_user=other)
    client.force_login(owner)
    assert client.get(f'/report/pdf/download/{report.pk}/').status_code == 404


@pytest.mark.parametrize('kind', ['business', 'product', 'area', 'variable', 'chart'])
def test_business_derived_images_keep_current_tenant_boundary(client, owned, kind):
    from product.models import Area
    from variable.models import Variable
    from dashboards.models import Chart
    owner, business, product = owned
    if kind == 'business':
        obj, field = business, business.image_src
    elif kind == 'product':
        obj, field = product, product.image_src
    elif kind == 'area':
        obj = Area.objects.create(name='Synthetic Area', description='Synthetic', fk_product=product)
        field = obj.image_src
    elif kind == 'variable':
        obj = Variable.objects.create(name='Synthetic Variable', fk_product=product)
        field = obj.image_src
    else:
        obj = Chart.objects.create(title='Synthetic Chart', fk_product=product)
        field = obj.chart_image
    field.save('synthetic.png', SimpleUploadedFile('synthetic.png', png(), content_type='image/png'))
    client.force_login(owner)
    url = f'/private-media/{kind}/{obj.pk}/'
    assert obj.get_photo_url() == url
    assert client.get(url).status_code == 200
    peer = User.objects.create_user(username='same-org-media-peer')
    OrganizationMembership.objects.create(user=peer, organization=business.organization, role=OrganizationMembership.Role.MEMBER)
    client.force_login(peer)
    assert client.get(url, HTTP_X_ORGANIZATION_ID=str(business.organization_id)).status_code == 404
    client.force_login(owner)
    Business.objects.filter(pk=business.pk).update(is_active=False)
    assert client.get(url).status_code == 404


def test_owner_cannot_read_business_image_in_another_active_context(client, owned):
    from tenancy.models import Organization
    owner, business, _ = owned
    colleague = owner
    client.force_login(owner)
    assert client.get(media_url(business), HTTP_X_ORGANIZATION_ID=str(business.organization_id)).status_code == 200
    second = Organization.objects.create(name='Other Synthetic Organization', created_by=colleague)
    OrganizationMembership.objects.create(user=colleague, organization=second, role=OrganizationMembership.Role.OWNER)
    assert client.get(media_url(business), HTTP_X_ORGANIZATION_ID=str(second.pk)).status_code == 404


def test_non_image_bytes_cannot_be_served_as_uploaded_image(client, owned):
    owner, business, _ = owned
    Path(business.image_src.path).write_bytes(b'<html><script>alert(1)</script></html>')
    client.force_login(owner)
    assert client.get(media_url(business)).status_code == 404
