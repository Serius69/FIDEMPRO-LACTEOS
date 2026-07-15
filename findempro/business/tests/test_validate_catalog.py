"""
Tests del smoke de simulación del catálogo (manage.py validate_catalog):
cada producto activo debe correr el pipeline Monte Carlo real de punta a punta.
"""
from io import StringIO

import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError

from business.data.bolivia_industries import get_spec
from business.services.seed_service import IndustrySeeder
from simulate.models import Simulation


@pytest.fixture
def seeded_user(db):
    user = User.objects.create_user(username="catalog-tester", password="x")
    IndustrySeeder(user).seed_business(get_spec(7))   # 'Otros': 2 productos, rápido
    return user


def test_validates_every_product_and_cleans_up(seeded_user):
    out = StringIO()
    call_command("validate_catalog", "--user", seeded_user.username,
                 "--mc-scenarios", "10", "--periods", "5", stdout=out)
    text = out.getvalue()
    assert "2 productos simulan ✓ · 0 fallan" in text
    assert text.count("✓ tipo  7") == 2                      # ambos productos del tipo 7
    # Las simulaciones de humo no quedan en la DB.
    assert not Simulation.objects.filter(
        fk_questionary_result__fk_questionary__fk_product__fk_business__fk_user=seeded_user
    ).exists()


def test_keep_preserves_smoke_simulations(seeded_user):
    call_command("validate_catalog", "--user", seeded_user.username,
                 "--mc-scenarios", "10", "--periods", "5", "--keep",
                 stdout=StringIO())
    assert Simulation.objects.filter(
        fk_questionary_result__fk_questionary__fk_product__fk_business__fk_user=seeded_user
    ).count() == 2


def test_errors_without_products(db):
    User.objects.create_user(username="vacio", password="x")
    with pytest.raises(CommandError, match="no hay productos"):
        call_command("validate_catalog", "--user", "vacio", stdout=StringIO())


def test_errors_on_unknown_user(db):
    with pytest.raises(CommandError, match="no existe el usuario"):
        call_command("validate_catalog", "--user", "nadie", stdout=StringIO())
