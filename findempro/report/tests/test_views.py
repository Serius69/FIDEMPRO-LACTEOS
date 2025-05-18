import pytest
from django.urls import reverse
from django.test import Client
from django.contrib.auth.models import User
from .models import Report
from bs4 import BeautifulSoup

"""
Tests the POST request to the 'create_report' view.

This test verifies that a report can be successfully created by sending
a POST request with valid HTML content. It checks that the response
returns a 302 status code (indicating a redirect after successful creation)
and ensures that the report with the specified title exists in the database.

Args:
    authenticated_client: A test client instance that is authenticated.

Assertions:
    - The response status code is 302.
    - A report with the title 'Test Report' exists in the database.
"""
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
    url = reverse('report_list')
    response = authenticated_client.get(url)
    assert response.status_code == 200
    assert 'report/report-list.html' in [t.name for t in response.templates]

def test_report_overview_view(authenticated_client, report):
    url = reverse('report_overview', args=[report.id])
    response = authenticated_client.get(url)
    assert response.status_code == 200
    assert 'report/report-overview.html' in [t.name for t in response.templates]
    assert response.context['report'] == report

def test_generar_reporte_pdf(authenticated_client, report):
    url = reverse('generar_reporte_pdf', args=[report.id])
    response = authenticated_client.get(url)
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'
    assert f'attachment; filename="{report.title}.pdf"' in response['Content-Disposition']

def test_create_report_view_get(authenticated_client):
    url = reverse('create_report')
    response = authenticated_client.get(url)
    assert response.status_code == 200
    assert 'create_report.html' in [t.name for t in response.templates]

def test_create_report_view_post(authenticated_client):
    url = reverse('create_report')
    html_content = '<html><head><title>Test Report</title></head><body>Content</body></html>'
    response = authenticated_client.post(url, {'html_content': html_content})
    assert response.status_code == 302  # Redirect after successful creation
    assert Report.objects.filter(title='Test Report').exists()