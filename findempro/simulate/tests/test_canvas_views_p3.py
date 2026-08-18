"""
test_canvas_views_p3.py
========================
Pruebas de integración para los endpoints P3 del canvas:

  · POST /api/v2/projects/{pid}/simulate/sensitivity/  → SensitivityAnalysisView
  · CRUD /api/v2/alerts/                               → RiskAlertViewSet

Ejecutar con:
  cd findempro
  venv/Scripts/python.exe -m pytest simulate/tests/test_canvas_views_p3.py -v
"""
import uuid
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from simulate.canvas_models import SimulationProject, ModelNode, ModelEdge
from simulate.models import RiskAlert
from simulate.views.canvas_views import _minimal_montecarlo, _run_montecarlo, _run_scenario

User = get_user_model()


def test_canvas_adapters_never_fabricate_financial_results_without_inputs():
    result, stats = _run_montecarlo({"variables": {"demand": {"distribution": "normal", "params": {"mean": 10, "std": 1}}}})
    assert result["type"] == "incomplete"
    assert "unit_price" in stats["missing"]

    result, stats = _minimal_montecarlo({})
    assert result["type"] == "incomplete"
    assert stats["status"] == "incomplete"

    result, stats = _run_scenario({"n_runs": 10}, "expected")
    assert result["type"] == "incomplete"
    assert "base_demand" in stats["missing"]


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='testcanvas', password='pass1234', email='canvas@test.com'
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        username='other', password='pass1234', email='other@test.com'
    )


@pytest.fixture
def api_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def anon_client():
    return APIClient()


@pytest.fixture
def project(user, db):
    return SimulationProject.objects.create(
        user=user,
        name='Test Project',
        domain='dairy',
        run_specs={
            'start_time': 0, 'stop_time': 30, 'dt': 1,
            'n_runs_montecarlo': 100, 'random_seed': 42,
            'base_demand': 1000, 'unit_price': 12.5, 'unit_cost': 4.0,
            'fixed_costs': 2500,
        },
    )


@pytest.fixture
def project_with_stochastic_nodes(project, db):
    """Project populated with 3 stochastic ModelNodes."""
    ModelNode.objects.create(
        project=project, node_type='flow', label='demanda_leche',
        equation='1000', units='litros/dia',
        distribution_config={'dist_type': 'normal', 'params': {'mean': 1000, 'std': 150}},
    )
    ModelNode.objects.create(
        project=project, node_type='flow', label='tasa_ventas',
        equation='450', units='unidades/dia',
        distribution_config={'dist_type': 'triangular', 'params': {'low': 350, 'mode': 450, 'high': 580}},
    )
    ModelNode.objects.create(
        project=project, node_type='converter', label='precio_venta',
        equation='12.50', units='BOB/unidad',
        distribution_config={'dist_type': 'uniform', 'params': {'low': 11.0, 'high': 14.0}},
    )
    ModelNode.objects.create(
        project=project, node_type='converter', label='costo_fijo',
        equation='2500', units='BOB/dia',
        distribution_config=None,  # NOT stochastic
    )
    return project


@pytest.fixture
def risk_alert(user, db):
    return RiskAlert.objects.create(
        user=user,
        var_threshold=-5000.0,
        email='alert@empresa.com',
        is_active=True,
    )


@pytest.fixture
def other_alert(other_user, db):
    return RiskAlert.objects.create(
        user=other_user,
        var_threshold=-3000.0,
        email='other@empresa.com',
        is_active=True,
    )


def _sensitivity_url(project_pk):
    return f'/api/v2/projects/{project_pk}/simulate/sensitivity/'


def _alerts_url(pk=None):
    if pk is None:
        return '/api/v2/alerts/'
    return f'/api/v2/alerts/{pk}/'


# ─────────────────────────────────────────────────────────────────────────────
# SensitivityAnalysisView
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestSensitivityAnalysisView:

    def test_unauthenticated_returns_403(self, anon_client, project):
        resp = anon_client.post(_sensitivity_url(project.pk))
        assert resp.status_code in (401, 403)

    def test_project_not_found_returns_404(self, api_client):
        resp = api_client.post(_sensitivity_url(uuid.uuid4()))
        assert resp.status_code == 404

    def test_other_user_project_returns_404(self, api_client, other_user, db):
        other_project = SimulationProject.objects.create(
            user=other_user, name='Other', domain='generic',
        )
        resp = api_client.post(_sensitivity_url(other_project.pk))
        assert resp.status_code == 404

    def test_invalid_variation_pct_low_returns_400(self, api_client, project):
        resp = api_client.post(
            _sensitivity_url(project.pk),
            data={'variation_pct': 0.001},
            format='json',
        )
        assert resp.status_code == 400
        assert 'variation_pct' in str(resp.data.get('error', ''))

    def test_invalid_variation_pct_high_returns_400(self, api_client, project):
        resp = api_client.post(
            _sensitivity_url(project.pk),
            data={'variation_pct': 0.99},
            format='json',
        )
        assert resp.status_code == 400

    def test_invalid_n_runs_returns_400(self, api_client, project):
        resp = api_client.post(
            _sensitivity_url(project.pk),
            data={'n_runs': 5},
            format='json',
        )
        assert resp.status_code == 400

    def test_no_stochastic_nodes_returns_empty_tornado(self, api_client, project, db):
        # Project has no nodes → no stochastic variables
        resp = api_client.post(
            _sensitivity_url(project.pk),
            data={'variation_pct': 0.20, 'n_runs': 100},
            format='json',
        )
        assert resp.status_code == 200
        data = resp.data
        assert 'tornado_chart' in data
        assert data['n_stochastic_variables'] == 0
        assert data['tornado_chart']['n_variables'] == 0

    def test_stochastic_nodes_returns_tornado_chart(
        self, api_client, project_with_stochastic_nodes
    ):
        project = project_with_stochastic_nodes
        resp = api_client.post(
            _sensitivity_url(project.pk),
            data={'variation_pct': 0.20, 'n_runs': 100},
            format='json',
        )
        assert resp.status_code == 200
        data = resp.data
        assert data['n_stochastic_variables'] == 3  # only the 3 with distribution_config
        assert 'tornado_chart' in data
        chart = data['tornado_chart']
        assert chart['chart_type'] == 'bar'
        assert chart['horizontal'] is True
        assert len(chart['series']) == 2
        assert len(chart['categories']) == 3

    def test_tornado_chart_series_names(self, api_client, project_with_stochastic_nodes):
        resp = api_client.post(
            _sensitivity_url(project_with_stochastic_nodes.pk),
            data={'variation_pct': 0.15, 'n_runs': 100},
            format='json',
        )
        assert resp.status_code == 200
        chart = resp.data['tornado_chart']
        names = [s['name'] for s in chart['series']]
        assert '+15%' in names
        assert '-15%' in names

    def test_tornado_chart_sensitivity_table_length(
        self, api_client, project_with_stochastic_nodes
    ):
        resp = api_client.post(
            _sensitivity_url(project_with_stochastic_nodes.pk),
            data={'n_runs': 100},
            format='json',
        )
        assert resp.status_code == 200
        table = resp.data['tornado_chart']['sensitivity_table']
        assert len(table) == 3
        assert table[0]['rank'] == 1

    def test_duration_ms_in_response(self, api_client, project_with_stochastic_nodes):
        resp = api_client.post(
            _sensitivity_url(project_with_stochastic_nodes.pk),
            data={'n_runs': 50},
            format='json',
        )
        assert resp.status_code == 200
        assert 'duration_ms' in resp.data
        assert isinstance(resp.data['duration_ms'], int)

    def test_default_params_used_when_not_provided(
        self, api_client, project_with_stochastic_nodes
    ):
        # POST with no body — should use defaults (variation_pct=0.20, n_runs=500)
        resp = api_client.post(
            _sensitivity_url(project_with_stochastic_nodes.pk),
            data={},
            format='json',
        )
        assert resp.status_code == 200
        assert resp.data['variation_pct'] == pytest.approx(0.20)

    def test_costo_fijo_not_in_results(self, api_client, project_with_stochastic_nodes):
        """Non-stochastic node (costo_fijo) must not appear in sensitivity table."""
        resp = api_client.post(
            _sensitivity_url(project_with_stochastic_nodes.pk),
            data={'n_runs': 100},
            format='json',
        )
        assert resp.status_code == 200
        table = resp.data['tornado_chart']['sensitivity_table']
        variables = [row['variable'] for row in table]
        assert 'costo_fijo' not in variables

    def test_many_stochastic_nodes_dispatches_celery(
        self, api_client, project, db
    ):
        """When n_stochastic > 10, view enqueues Celery task and returns 202."""
        from unittest.mock import patch, MagicMock

        for i in range(11):
            ModelNode.objects.create(
                project=project,
                node_type='converter',
                label=f'var_{i}',
                equation='1',
                distribution_config={'dist_type': 'normal', 'params': {'mean': 100, 'std': 10}},
            )

        fake_result = MagicMock()
        fake_result.id = 'fake-celery-id'

        with patch('simulate.tasks.run_sensitivity_async.delay', return_value=fake_result) as mock_task:
            resp = api_client.post(
                _sensitivity_url(project.pk),
                data={'n_runs': 100},
                format='json',
            )

        assert resp.status_code == 202
        assert resp.data['status'] == 'queued'
        assert 'task_id' in resp.data
        assert resp.data['n_stochastic_variables'] == 11
        mock_task.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
# RiskAlertViewSet
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRiskAlertViewSet:

    def test_unauthenticated_list_returns_403(self, anon_client):
        resp = anon_client.get(_alerts_url())
        assert resp.status_code in (401, 403)

    def test_empty_list_for_new_user(self, api_client):
        resp = api_client.get(_alerts_url())
        assert resp.status_code == 200
        assert resp.data == []

    def test_list_returns_own_alerts_only(
        self, api_client, risk_alert, other_alert
    ):
        resp = api_client.get(_alerts_url())
        assert resp.status_code == 200
        assert len(resp.data) == 1
        assert str(resp.data[0]['id']) == str(risk_alert.id)

    def test_create_alert_sets_user_from_request(self, api_client, user):
        resp = api_client.post(
            _alerts_url(),
            data={
                'var_threshold': -5000.0,
                'email': 'new@alert.com',
                'is_active': True,
            },
            format='json',
        )
        assert resp.status_code == 201
        assert RiskAlert.objects.filter(user=user, email='new@alert.com').exists()

    def test_create_alert_with_cvar_threshold(self, api_client, user):
        resp = api_client.post(
            _alerts_url(),
            data={
                'var_threshold': -5000.0,
                'cvar_threshold': -8000.0,
                'email': 'cvar@alert.com',
                'is_active': True,
            },
            format='json',
        )
        assert resp.status_code == 201
        alert = RiskAlert.objects.get(email='cvar@alert.com')
        assert alert.cvar_threshold == pytest.approx(-8000.0)

    def test_create_alert_missing_email_returns_400(self, api_client):
        resp = api_client.post(
            _alerts_url(),
            data={'var_threshold': -5000.0},
            format='json',
        )
        assert resp.status_code == 400
        assert 'email' in resp.data

    def test_create_alert_invalid_email_returns_400(self, api_client):
        resp = api_client.post(
            _alerts_url(),
            data={'var_threshold': -5000.0, 'email': 'not-valid'},
            format='json',
        )
        assert resp.status_code == 400

    def test_retrieve_own_alert(self, api_client, risk_alert):
        resp = api_client.get(_alerts_url(risk_alert.id))
        assert resp.status_code == 200
        assert resp.data['id'] == risk_alert.id
        assert resp.data['email'] == 'alert@empresa.com'

    def test_retrieve_other_users_alert_returns_404(
        self, api_client, other_alert
    ):
        resp = api_client.get(_alerts_url(other_alert.id))
        assert resp.status_code == 404

    def test_update_own_alert(self, api_client, risk_alert):
        resp = api_client.patch(
            _alerts_url(risk_alert.id),
            data={'var_threshold': -7000.0},
            format='json',
        )
        assert resp.status_code == 200
        risk_alert.refresh_from_db()
        assert risk_alert.var_threshold == pytest.approx(-7000.0)

    def test_update_other_users_alert_returns_404(
        self, api_client, other_alert
    ):
        resp = api_client.patch(
            _alerts_url(other_alert.id),
            data={'var_threshold': -1.0},
            format='json',
        )
        assert resp.status_code == 404

    def test_delete_own_alert(self, api_client, risk_alert):
        resp = api_client.delete(_alerts_url(risk_alert.id))
        assert resp.status_code == 204
        assert not RiskAlert.objects.filter(id=risk_alert.id).exists()

    def test_delete_other_users_alert_returns_404(
        self, api_client, other_alert
    ):
        resp = api_client.delete(_alerts_url(other_alert.id))
        assert resp.status_code == 404
        assert RiskAlert.objects.filter(id=other_alert.id).exists()

    def test_deactivate_alert_via_patch(self, api_client, risk_alert):
        resp = api_client.patch(
            _alerts_url(risk_alert.id),
            data={'is_active': False},
            format='json',
        )
        assert resp.status_code == 200
        risk_alert.refresh_from_db()
        assert risk_alert.is_active is False

    def test_response_contains_expected_fields(self, api_client, risk_alert):
        resp = api_client.get(_alerts_url(risk_alert.id))
        assert resp.status_code == 200
        fields = set(resp.data.keys())
        assert {'id', 'var_threshold', 'email', 'is_active', 'created_at', 'updated_at'}.issubset(fields)

    def test_read_only_fields_not_writable(self, api_client, user):
        """Attempting to set id/created_at in POST is silently ignored."""
        fake_id = 9999
        resp = api_client.post(
            _alerts_url(),
            data={
                'id': fake_id,
                'var_threshold': -1000.0,
                'email': 'ro@test.com',
            },
            format='json',
        )
        assert resp.status_code == 201
        assert resp.data['id'] != fake_id


# ─────────────────────────────────────────────────────────────────────────────
# RiskAlert model — database-level tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRiskAlertDB:

    def test_create_and_retrieve(self, user):
        alert = RiskAlert.objects.create(
            user=user, var_threshold=-4000.0, email='db@test.com',
        )
        fetched = RiskAlert.objects.get(pk=alert.pk)
        assert fetched.var_threshold == pytest.approx(-4000.0)
        assert fetched.email == 'db@test.com'
        assert fetched.is_active is True
        assert fetched.cvar_threshold is None

    def test_index_on_user_and_is_active(self, user):
        """Querying by user+is_active should hit the index — at least no error."""
        RiskAlert.objects.create(user=user, var_threshold=-1000.0, email='idx@test.com')
        qs = RiskAlert.objects.filter(user=user, is_active=True)
        assert qs.count() == 1

    def test_fk_product_nullable(self, user):
        alert = RiskAlert.objects.create(
            user=user, var_threshold=-1000.0, email='null@test.com',
            fk_product=None,
        )
        assert alert.fk_product is None

    def test_cascade_delete_with_user(self, db):
        u = User.objects.create_user(username='cascade_u', password='x')
        RiskAlert.objects.create(user=u, var_threshold=-1.0, email='c@c.com')
        u.delete()
        assert RiskAlert.objects.filter(email='c@c.com').count() == 0

    def test_ordering_newest_first(self, user):
        a1 = RiskAlert.objects.create(user=user, var_threshold=-1000.0, email='old@t.com')
        a2 = RiskAlert.objects.create(user=user, var_threshold=-2000.0, email='new@t.com')
        alerts = list(RiskAlert.objects.filter(user=user))
        assert alerts[0].pk == a2.pk  # newest first

    def test_is_triggered_db_object(self, user):
        alert = RiskAlert.objects.create(
            user=user, var_threshold=-5000.0, email='t@t.com',
        )
        assert alert.is_triggered(-6000.0) is True
        assert alert.is_triggered(-4000.0) is False
