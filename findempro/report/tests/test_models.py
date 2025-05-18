import pytest
from django.utils import timezone
from findempro.report.models import Report
from product.models import Product

@pytest.mark.django_db
def test_report_creation():
    product = Product.objects.create(name="Test Product")  # Assuming Product has a 'name' field
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
    assert str(report) == "Test Report"

@pytest.mark.django_db
def test_report_fk_product_null():
    report = Report.objects.create(
        title="Test Report Without Product",
        content={"key": "value"},
        is_active=True,
        fk_product=None
    )
    assert report.fk_product is None