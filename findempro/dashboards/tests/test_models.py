import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from dashboards.models import Chart
from product.models import Product
from unittest.mock import patch, MagicMock
from io import BytesIO
from PIL import Image


# UNI
@pytest.mark.django_db
def test_chart_creation():
    product = Product.objects.create(name="Test Product")
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
    product = Product.objects.create(name="Test Product")
    chart = Chart.objects.create(
        title="Test Chart",
        fk_product=product,
    )
    chart.chart_image = SimpleUploadedFile("test_image.png", b"file_content", content_type="image/png")
    chart.save()
    assert chart.get_photo_url() == chart.chart_image.url

@pytest.mark.django_db
def test_chart_get_photo_url_without_image():
    product = Product.objects.create(name="Test Product")
    chart = Chart.objects.create(
        title="Test Chart",
        fk_product=product,
    )
    assert chart.get_photo_url() == "/static/images/business/business-dummy-img.webp"

@pytest.mark.django_db
@patch("dashboards.models.plt")
@patch("dashboards.models.Image")
def test_save_chart_image(mock_image, mock_plt):
    product = Product.objects.create(name="Test Product")
    chart = Chart.objects.create(
        title="Test Chart",
        chart_data={"x_label": "X Axis", "y_label": "Y Axis"},
        fk_product=product,
    )

    mock_buffer = BytesIO()
    mock_image.open.return_value = MagicMock()
    mock_plt.savefig.return_value = None

    chart.save_chart_image(image_data=None)

    mock_plt.legend.assert_called_once()
    mock_plt.xlabel.assert_called_once_with("X Axis")
    mock_plt.ylabel.assert_called_once_with("Y Axis")
    mock_plt.title.assert_called_once_with("Test Chart")
    mock_plt.savefig.assert_called_once()
    mock_plt.close.assert_called_once()
    mock_image.open.assert_called_once()
    
    # 
@pytest.mark.django_db
def test_chart_creation_with_defaults():
    product = Product.objects.create(name="Default Product")
    chart = Chart.objects.create(fk_product=product)
    assert chart.title == "Chart"
    assert chart.chart_type == "line"
    assert chart.chart_data == []
    assert chart.widget_config == {}
    assert chart.layout_config == {}
    assert chart.is_active is True
    assert chart.chart_image is None

@pytest.mark.django_db
def test_chart_update():
    product = Product.objects.create(name="Update Product")
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
    product = Product.objects.create(name="Delete Product")
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
    product = Product.objects.create(name="Constraint Product")
    with pytest.raises(ValueError):
        Chart.objects.create(
            title=None,  # title cannot be null
            fk_product=product,
        )
    with pytest.raises(ValueError):
        Chart.objects.create(
            chart_type=None,  # chart_type cannot be null
            fk_product=product,
        )

@pytest.mark.django_db
def test_chart_get_photo_url_with_no_image():
    product = Product.objects.create(name="No Image Product")
    chart = Chart.objects.create(
        title="No Image Chart",
        fk_product=product,
    )
    assert chart.get_photo_url() == "/static/images/business/business-dummy-img.webp"

@pytest.mark.django_db
def test_chart_get_photo_url_with_image():
    product = Product.objects.create(name="Image Product")
    chart = Chart.objects.create(
        title="Image Chart",
        fk_product=product,
    )
    chart.chart_image = SimpleUploadedFile("test_image.png", b"file_content", content_type="image/png")
    chart.save()
    assert chart.get_photo_url() == chart.chart_image.url









