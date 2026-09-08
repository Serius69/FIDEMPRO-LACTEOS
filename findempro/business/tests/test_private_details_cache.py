import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client
from business.models import Business

pytestmark = pytest.mark.django_db


def test_private_details_cannot_leak_after_owner_warms_cache():
    cache.clear()
    owner=User.objects.create_user(username="cache-owner")
    outsider=User.objects.create_user(username="cache-outsider")
    business=Business.objects.create(fk_user=owner,name="Synthetic confidential business",location="SYNTHETIC")
    own=Client();own.force_login(owner)
    other=Client();other.force_login(outsider)
    url=f"/business/api/details/{business.pk}/"
    response=own.get(url)
    assert response.status_code==200
    assert "private" in response.headers["Cache-Control"]
    assert "no-store" in response.headers["Cache-Control"]
    response=other.get(url)
    assert response.status_code==404
    assert business.name not in response.content.decode()
    assert Client().get(url).status_code==302
    assert own.get(url).status_code==200
    cache.clear()
