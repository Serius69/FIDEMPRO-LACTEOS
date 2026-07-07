import pytest
from django.urls import reverse
from django.test import Client
from django.contrib.auth.models import User
from report.models import Report

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

@pytest.fixture
def report():
    return Report.objects.create(title="Test Report", content={"key": "value"})


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
