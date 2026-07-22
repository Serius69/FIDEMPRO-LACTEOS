"""
[P2] Agregados de dashboard ignoraban is_active.

DashboardService._get_business_products, _get_enhanced_business_stats
(areas_count) y _get_enhanced_top_products consultaban Product/Area sin
filtrar is_active=True: un producto (o área) desactivado seguía apareciendo
en products_count / areas_count / top-products.
"""
import pytest

from business.models import Business
from product.models import Area, Product
from dashboards.services.dashboard_service import DashboardService


@pytest.fixture
def business_with_products(django_user_model):
    user = django_user_model.objects.create_user(username="dash-active", password="p")
    business = Business.objects.create(
        name="Neg is_active", type=1, location="La Paz",
        description="x", fk_user=user, is_active=True,
    )
    active_product = Product.objects.create(
        name="Producto activo", description="x", fk_business=business,
        type=1, is_active=True,
    )
    inactive_product = Product.objects.create(
        name="Producto inactivo", description="x", fk_business=business,
        type=1, is_active=False,
    )
    return business, active_product, inactive_product


@pytest.mark.django_db
def test_get_business_products_excludes_inactive(business_with_products):
    business, active_product, inactive_product = business_with_products

    products = DashboardService._get_business_products(business.id)

    ids = {p.id for p in products}
    assert active_product.id in ids
    assert inactive_product.id not in ids


@pytest.mark.django_db
def test_enhanced_business_stats_products_count_excludes_inactive(business_with_products):
    business, active_product, inactive_product = business_with_products

    products = DashboardService._get_business_products(business.id)
    stats = DashboardService._get_enhanced_business_stats(business.id, products, [])

    assert stats['products_count'] == 1


@pytest.mark.django_db
def test_enhanced_business_stats_areas_count_excludes_inactive_product(business_with_products):
    business, active_product, inactive_product = business_with_products

    Area.objects.create(
        name="Area activa", description="x", fk_product=active_product, is_active=True,
    )
    Area.objects.create(
        name="Area inactiva", description="x", fk_product=active_product, is_active=False,
    )
    # Área que quedó "huérfana" porque su producto se desactivó después de
    # creada (Area.clean() impide asignarla a un producto ya inactivo, así
    # que se simula el escenario real vía update() sin re-validar).
    orphan_area = Area.objects.create(
        name="Area de producto luego desactivado", description="x",
        fk_product=active_product, is_active=True,
    )
    Product.objects.filter(pk=inactive_product.pk).update(is_active=False)
    Area.objects.filter(pk=orphan_area.pk).update(fk_product=inactive_product)

    products = DashboardService._get_business_products(business.id)
    stats = DashboardService._get_enhanced_business_stats(business.id, products, [])

    # Solo cuenta el area activa cuyo producto también está activo.
    assert stats['areas_count'] == 1


@pytest.mark.django_db
def test_enhanced_top_products_excludes_inactive(business_with_products):
    business, active_product, inactive_product = business_with_products

    top = DashboardService._get_enhanced_top_products(business.id)

    ids = {p['id'] for p in top}
    assert active_product.id in ids
    assert inactive_product.id not in ids
