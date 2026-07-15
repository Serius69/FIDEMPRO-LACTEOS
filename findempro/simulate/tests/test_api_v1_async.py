"""
test_api_v1_async.py
====================
Tests del flujo asíncrono (ítem 20 de auditoría): la simulación Monte Carlo del
SPA se encola en Celery en vez de bloquear el worker gunicorn.

  POST /simulate/api/v1/simulate/async/      → 202 {task_id, status_url}
  GET  /simulate/api/v1/simulate/status/<id>/ → estado/resultado de la tarea

Corren bajo settings.testing con CELERY_TASK_ALWAYS_EAGER=True +
CELERY_TASK_STORE_EAGER_RESULT=True + result backend en memoria, de modo que
el flujo completo (encolar → status SUCCESS → result) es verificable sin worker.
"""
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient

# Payload mínimo válido para el motor Monte Carlo.
_VALID_PAYLOAD = {
    "demand_mean": 1000,
    "demand_std": 150,
    "unit_price": 10.0,
    "unit_cost": 6.0,
    "fixed_costs": 5000,
    "n_iterations": 1000,
    "time_periods": 12,
    "industry_sector": "retail",
}


@pytest.fixture
def client(db):
    api = APIClient()
    user = User.objects.create_user(username='async_user', password='pass_async')
    api.force_authenticate(user=user)
    return api


@pytest.mark.django_db
def test_async_enqueue_returns_202_with_task_id(client):
    """El endpoint async responde 202 con task_id y status_url (no bloquea)."""
    url = reverse('simulate:api.v1.simulate_async')
    resp = client.post(url, data=_VALID_PAYLOAD, format='json')

    assert resp.status_code == 202, resp.content
    body = resp.json()
    assert 'task_id' in body and body['task_id']
    assert body['status'] == 'queued'
    assert body['status_url'] == reverse(
        'simulate:api.v1.simulate_status', args=[body['task_id']]
    )


@pytest.mark.django_db
def test_async_invalid_payload_returns_400(client):
    """La validación del payload es idéntica al endpoint síncrono (400)."""
    url = reverse('simulate:api.v1.simulate_async')
    resp = client.post(url, data={"demand_mean": 1000}, format='json')
    assert resp.status_code == 400
    assert 'error' in resp.json()


@pytest.mark.django_db
def test_async_full_flow_enqueue_then_status_success(client):
    """Flujo completo: encolar → consultar status → SUCCESS con result usable."""
    enqueue_url = reverse('simulate:api.v1.simulate_async')
    enqueue = client.post(enqueue_url, data=_VALID_PAYLOAD, format='json')
    assert enqueue.status_code == 202
    task_id = enqueue.json()['task_id']

    status_resp = client.get(enqueue.json()['status_url'])
    assert status_resp.status_code == 200, status_resp.content
    body = status_resp.json()

    assert body['state'] == 'SUCCESS', body
    result = body['result']
    assert isinstance(result, dict)
    # Metadata inyectada por el helper (merge de `extra`).
    assert result.get('_industry_sector') == 'retail'
    assert result.get('_profile_used') is False
    # El motor produjo la estructura esperada (mismo dict que el endpoint sync).
    assert 'demand' in result or 'metadata' in result or 'revenue' in result


@pytest.mark.django_db
def test_status_unknown_task_is_pending(client):
    """Un task_id desconocido devuelve estado pendiente (PENDING), no error."""
    url = reverse('simulate:api.v1.simulate_status', args=['nonexistent-task-id-123'])
    resp = client.get(url)
    assert resp.status_code == 200
    assert resp.json()['state'] == 'pending'
