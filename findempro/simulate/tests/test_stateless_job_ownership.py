import uuid
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from simulate.models import StatelessSimulationJob
from tenancy.models import OrganizationMembership
from tenancy.services import ensure_default_organization

pytestmark = pytest.mark.django_db
PAYLOAD = {"demand_mean": 1000, "demand_std": 150, "unit_price": 10,
           "unit_cost": 6, "fixed_costs": 5000, "n_iterations": 1000, "time_periods": 5}


def account(name):
    user = User.objects.create_user(username=name)
    org = ensure_default_organization(user)
    client = APIClient()
    client.force_authenticate(user=user)
    return user, org, client


@pytest.mark.parametrize("state", ["SUCCESS", "FAILURE", "PENDING"])
def test_other_tenant_never_reaches_result_backend(state):
    owner, org, own = account("owner")
    other, _, outsider = account("other")
    job = StatelessSimulationJob.objects.create(user=owner, organization=org)
    with patch("celery.result.AsyncResult") as result:
        result.return_value.state = state
        response = outsider.get(f"/simulate/api/v1/simulate/status/{job.pk}/")
    assert response.status_code == 404
    result.assert_not_called()


@pytest.mark.parametrize("identifier", [str(uuid.uuid4()), "not-a-task"])
def test_unknown_jobs_never_reach_backend(identifier):
    _, _, client = account("unknown")
    with patch("celery.result.AsyncResult") as result:
        response = client.get(f"/simulate/api/v1/simulate/status/{identifier}/")
    assert response.status_code == 404
    result.assert_not_called()


def test_durable_ownership_precedes_publish_and_matches_task_id():
    user, org, client = account("enqueue")
    def publish(*, args, task_id):
        assert StatelessSimulationJob.objects.filter(pk=task_id,user=user,organization=org).exists()
    with patch("simulate.tasks.run_stateless_simulation.apply_async", side_effect=publish):
        response = client.post("/simulate/api/v1/simulate/async/", PAYLOAD, format="json")
    assert response.status_code == 202
    assert StatelessSimulationJob.objects.get(pk=response.json()["task_id"]).user == user


def test_broker_failure_removes_orphan_and_hides_error():
    _, _, client = account("broker")
    with patch("simulate.tasks.run_stateless_simulation.apply_async", side_effect=RuntimeError("redis://sensitive-value")):
        response = client.post("/simulate/api/v1/simulate/async/", PAYLOAD, format="json")
    assert response.status_code == 503
    assert "sensitive-value" not in response.content.decode()
    assert not StatelessSimulationJob.objects.exists()


def test_revoked_membership_cannot_read_owned_result():
    user, org, client = account("revoked")
    job = StatelessSimulationJob.objects.create(user=user, organization=org)
    OrganizationMembership.objects.filter(user=user, organization=org).update(is_active=False)
    with patch("celery.result.AsyncResult") as result:
        response = client.get(f"/simulate/api/v1/simulate/status/{job.pk}/")
    assert response.status_code == 404
    result.assert_not_called()


def test_same_organization_other_user_cannot_read_private_job():
    owner, org, _ = account("privateowner")
    user = User.objects.create_user(username="colleague")
    OrganizationMembership.objects.create(user=user,organization=org,role="MEMBER")
    client=APIClient();client.force_authenticate(user=user)
    job=StatelessSimulationJob.objects.create(user=owner,organization=org)
    with patch("celery.result.AsyncResult") as result:
        response=client.get(f"/simulate/api/v1/simulate/status/{job.pk}/")
    assert response.status_code==404
    result.assert_not_called()
