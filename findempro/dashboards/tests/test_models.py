import itertools

import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from unittest.mock import patch

from dashboards.models import Chart
from business.models import Business
from product.models import Product


# URL por defecto que retorna Chart.get_photo_url() cuando no hay imagen
DEFAULT_CHART_PHOTO_URL = "/static/images/charts/default-chart.png"

_counter = itertools.count(1)


def _make_product(label="p"):
    """Crea User + Business + Product con nombres unicos por llamada.

    Product.save() ejecuta full_clean(), por lo que necesita fk_business y
    description no vacia. Business tiene UNIQUE(name, fk_user) para activos,
    de ahi que cada Product use un usuario/negocio nuevo.
    """
    n = next(_counter)
    user = User.objects.create_user(username=f"user_{label}_{n}", password="pw")
    business = Business.objects.create(
        name=f"Business {label} {n}",
        type=1,
        location="La Paz",
        description="Negocio de prueba",
        fk_user=user,
        is_active=True,
    )
    return Product.objects.create(
        name=f"Product {label} {n}",
        description="Descripcion de producto de prueba",
        fk_business=business,
    )


# UNIT TESTS
@pytest.mark.django_db
def test_chart_creation():
    product = _make_product("create")
    chart = Chart.objects.create(
        title="Test Chart",
        chart_type="bar",
        chart_data={"x_label": "X Axis", "y_label": "Y Axis"},
        fk_product=product,
        widget_config={"key": "value"},
        layout_config={"layout": "value"},
        is_active=True,
    )
    assert chart.title == "Test Chart"
    assert chart.chart_type == "bar"
    assert chart.chart_data == {"x_label": "X Axis", "y_label": "Y Axis"}
    assert chart.fk_product == product
    assert chart.is_active is True


@pytest.mark.django_db
def test_chart_get_photo_url_with_image():
    product = _make_product("photo")
    chart = Chart.objects.create(
        title="Test Chart",
        fk_product=product,
    )
    chart.chart_image = SimpleUploadedFile(
        "test_image.png", b"file_content", content_type="image/png"
    )
    chart.save()
    assert chart.get_photo_url() == chart.chart_image.url


@pytest.mark.django_db
def test_chart_get_photo_url_without_image():
    product = _make_product("nophoto")
    chart = Chart.objects.create(
        title="Test Chart",
        fk_product=product,
    )
    assert chart.get_photo_url() == DEFAULT_CHART_PHOTO_URL


@pytest.mark.django_db
@patch("dashboards.models.plt")
def test_generate_chart_image(mock_plt):
    """Ejercita Chart.generate_chart_image() (reemplaza al removido
    save_chart_image). Con plt mockeado no se renderiza nada real, pero se
    verifica el flujo: ejes, leyenda, guardado y cierre de figura."""
    product = _make_product("img")
    chart = Chart.objects.create(
        title="Test Chart",
        chart_type="line",
        chart_data={
            "labels": ["A", "B"],
            "datasets": [{"data": [1, 2], "label": "serie"}],
            "x_label": "X Axis",
            "y_label": "Y Axis",
        },
        fk_product=product,
    )

    result = chart.generate_chart_image()

    assert result is True
    mock_plt.xlabel.assert_called_once_with("X Axis")
    mock_plt.ylabel.assert_called_once_with("Y Axis")
    mock_plt.legend.assert_called_once()
    mock_plt.title.assert_called_once()
    mock_plt.savefig.assert_called_once()
    mock_plt.close.assert_called_once()


@pytest.mark.django_db
def test_chart_creation_with_defaults():
    product = _make_product("defaults")
    chart = Chart.objects.create(fk_product=product)
    # title es CharField sin default -> cadena vacia
    assert chart.title == ""
    assert chart.chart_type == "line"
    # chart_data usa default=dict -> {}
    assert chart.chart_data == {}
    assert chart.widget_config == {}
    assert chart.layout_config == {}
    assert chart.is_active is True
    # ImageField vacio es "falsy" (no None)
    assert not chart.chart_image


@pytest.mark.django_db
def test_chart_update():
    product = _make_product("update")
    chart = Chart.objects.create(
        title="Initial Title",
        chart_type="line",
        fk_product=product,
    )
    chart.title = "Updated Title"
    chart.chart_type = "bar"
    chart.save()
    updated_chart = Chart.objects.get(id=chart.id)
    assert updated_chart.title == "Updated Title"
    assert updated_chart.chart_type == "bar"


@pytest.mark.django_db
def test_chart_deletion():
    product = _make_product("delete")
    chart = Chart.objects.create(
        title="To Be Deleted",
        fk_product=product,
    )
    chart_id = chart.id
    chart.delete()
    with pytest.raises(Chart.DoesNotExist):
        Chart.objects.get(id=chart_id)


@pytest.mark.django_db
def test_chart_field_constraints():
    product = _make_product("constraint")
    # title NOT NULL -> IntegrityError
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Chart.objects.create(title=None, fk_product=product)
    # chart_type NOT NULL -> IntegrityError
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Chart.objects.create(title="Valid", chart_type=None, fk_product=product)


@pytest.mark.django_db
def test_chart_get_photo_url_with_no_image():
    product = _make_product("noimg")
    chart = Chart.objects.create(
        title="No Image Chart",
        fk_product=product,
    )
    assert chart.get_photo_url() == DEFAULT_CHART_PHOTO_URL
