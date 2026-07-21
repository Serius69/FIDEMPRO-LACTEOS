import pytest
from django.urls import reverse
from django.test import Client
from django.contrib.auth.models import User
from report.models import Report
from business.models import Business
from product.models import Product

"""
Tests de las vistas de report contra el esquema/rutas vigentes.

La app está enrutada bajo el namespace 'report' (app_name='report' en report/urls.py),
por lo que todos los reverse() deben usar 'report:<name>'.
Todos los tests requieren acceso a BD -> pytestmark django_db a nivel de módulo.
"""

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return Client()

@pytest.fixture
def user():
    return User.objects.create_user(username='testuser', password='testpassword')

@pytest.fixture
def authenticated_client(client, user):
    client.login(username='testuser', password='testpassword')
    return client

def _product_for(user, suffix=""):
    """Cadena User -> Business -> Product para dar DUEÑO a un reporte.

    Tras el fix de IDOR, un reporte sin producto (sin dueño) no es visible por
    ninguna vista, así que las pruebas de acceso necesitan la cadena completa.
    """
    business = Business.objects.create(
        name=f"Test Business {suffix}", type=1, location="La Paz",
        description="desc", fk_user=user, is_active=True,
    )
    return Product.objects.create(
        fk_business=business, name=f"Test Product {suffix}",
        description="d", is_active=True,
    )


@pytest.fixture
def report(user):
    # El reporte pertenece a `user` (testuser) vía fk_product -> fk_business -> fk_user.
    product = _product_for(user, "main")
    return Report.objects.create(
        title="Test Report", content={"key": "value"}, fk_product=product
    )


@pytest.fixture
def other_user():
    return User.objects.create_user(username='intruso', password='otherpass-123')


def test_report_list_view(authenticated_client):
    url = reverse('report:report.list')
    response = authenticated_client.get(url)
    assert response.status_code == 200
    assert 'report/report-list.html' in [t.name for t in response.templates]

def test_report_overview_view(authenticated_client, report):
    url = reverse('report:report.overview', args=[report.id])
    response = authenticated_client.get(url)
    assert response.status_code == 200
    # report_overview delega en report_detail -> plantilla report-detail.html.
    assert 'report/report-detail.html' in [t.name for t in response.templates]
    assert response.context['report'] == report

@pytest.mark.skip(reason="Generación de PDF migrada a tarea async Celery (responde 202 + task_id "
                         "vía generar_reporte_pdf); ya no devuelve un application/pdf síncrono y "
                         "requiere broker Celery para ejercitarse.")
def test_generar_reporte_pdf(authenticated_client, report):
    url = reverse('report:generar_reporte_pdf', args=[report.id])
    response = authenticated_client.get(url)
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'
    assert f'attachment; filename="{report.title}.pdf"' in response['Content-Disposition']

def test_create_report_view_get(authenticated_client):
    url = reverse('report:report.create')
    response = authenticated_client.get(url)
    assert response.status_code == 200
    assert 'report/report-create.html' in [t.name for t in response.templates]

def test_create_report_view_post(authenticated_client):
    url = reverse('report:report.create')
    response = authenticated_client.post(url, {
        'title': 'Test Report',
        'content': '{"key": "value"}',
        'is_active': 'on',
    })
    assert response.status_code == 302  # Redirect after successful creation
    assert Report.objects.filter(title='Test Report').exists()


# ─────────────────────────────────────────────
# Aislamiento por dueño (IDOR)
# ─────────────────────────────────────────────
def test_report_api_detail_isolation_returns_404_for_non_owner(client, report, other_user):
    """Un usuario que NO es dueño no puede ver el reporte de otro -> 404."""
    client.login(username='intruso', password='otherpass-123')
    url = reverse('report:api.detail', args=[report.id])
    response = client.get(url)
    assert response.status_code == 404


def test_report_list_excludes_other_users_reports(client, report, other_user):
    """La lista del intruso no incluye el reporte ajeno."""
    client.login(username='intruso', password='otherpass-123')
    response = client.get(reverse('report:report.list'))
    assert response.status_code == 200
    assert report not in list(response.context['reports'])
    assert response.context['total_reports'] == 0
