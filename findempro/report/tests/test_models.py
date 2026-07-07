import pytest
from django.utils import timezone
from django.contrib.auth.models import User
from report.models import Report
from business.models import Business
from product.models import Product


def _build_product(suffix=""):
    """Crea la cadena User -> Business -> Product que exige el esquema vigente."""
    user = User.objects.create_user(username=f"tester{suffix}", password="password")
    business = Business.objects.create(
        name=f"Test Business {suffix}",
        type=1,
        location="La Paz",
        description="Negocio de prueba",
        fk_user=user,
        is_active=True,
    )
    return Product.objects.create(
        fk_business=business,
        name=f"Test Product {suffix}",
        description="d",
        is_active=True,
    )


@pytest.mark.django_db
def test_report_creation():
    product = _build_product("rc")
    report = Report.objects.create(
        title="Test Report",
        content={"key": "value"},
        is_active=True,
        fk_product=product
    )
    assert report.title == "Test Report"
    assert report.content == {"key": "value"}
    assert report.is_active is True
    assert report.fk_product == product
    assert report.date_created <= timezone.now()
    assert report.last_updated <= timezone.now()

@pytest.mark.django_db
def test_report_str_method():
    report = Report.objects.create(
        title="Test Report",
        content={"key": "value"},
        is_active=True
    )
    # __str__ incluye el tipo de reporte (por defecto 'simulation' -> 'Simulación').
    assert str(report) == "Test Report - Simulación"

@pytest.mark.django_db
def test_report_fk_product_null():
    report = Report.objects.create(
        title="Test Report Without Product",
        content={"key": "value"},
        is_active=True,
        fk_product=None
    )
    assert report.fk_product is None
