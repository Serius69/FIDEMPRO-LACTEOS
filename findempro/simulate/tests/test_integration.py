"""
test_integration.py
===================
Integration tests for FASE 2-4 features:
  - SimulationProgressView  (Celery-path + DB-fallback)
  - SimulationCompareView   (winner identification)
  - SimulationSensitivityView (Pearson correlation structure)
  - SimulationHistoryView   (monthly aggregation)
  - SimulationExportView    (JSON + Excel)
  - SimulationService cache helpers
  - InsufficientDataError propagation
"""
import datetime
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from business.models import Business
from product.models import Product
from questionary.models import Questionary, QuestionaryResult
from simulate.exceptions import InsufficientDataError
from simulate.models import (
    ProbabilisticDensityFunction,
    ResultSimulation,
    Simulation,
)

# ── Constants ─────────────────────────────────────────────────────────────────

_DEMAND = [100, 110, 120, 130, 115, 105, 125, 118, 108, 112, 120, 130]


# ── Shared fixtures ───────────────────────────────────────────────────────────


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="int_user", password="pass_int")


@pytest.fixture
def user2(db):
    return User.objects.create_user(username="other_int_user", password="pass_other")


@pytest.fixture
def business(user):
    return Business.objects.create(name="Integration Biz", is_active=True, fk_user=user)


@pytest.fixture
def product(business):
    return Product.objects.create(
        name="Integration Product",
        description="Test product for integration tests",
        is_active=True,
        fk_business=business,
    )


@pytest.fixture
def questionary(product):
    return Questionary.objects.create(questionary="Integration Questionary", fk_product=product)


@pytest.fixture
def questionary_result(questionary):
    return QuestionaryResult.objects.create(is_active=True, fk_questionary=questionary)


@pytest.fixture
def fdp(business):
    # The post_save signal on Business auto-creates all 5 distributions.
    # Fetch the Normal distribution (type=1) that was created by the signal.
    return ProbabilisticDensityFunction.objects.get(
        distribution_type=1,
        fk_business=business,
    )


@pytest.fixture
def simulation(questionary_result, fdp):
    return Simulation.objects.create(
        fk_questionary_result=questionary_result,
        fk_fdp=fdp,
        quantity_time=10,
        unit_time="days",
        demand_history=_DEMAND,
        confidence_level=0.95,
        random_seed=42,
        is_active=True,
    )


@pytest.fixture
def simulation2(questionary_result, fdp):
    """Second simulation sharing the same questionary_result + fdp."""
    return Simulation.objects.create(
        fk_questionary_result=questionary_result,
        fk_fdp=fdp,
        quantity_time=10,
        unit_time="days",
        demand_history=_DEMAND,
        confidence_level=0.95,
        random_seed=99,
        is_active=True,
    )


# ── Helpers ───────────────────────────────────────────────────────────────────


def _login(client, user, password="pass_int"):
    client.login(username=user.username, password=password)


def _make_results(simulation, n=10, profit_offset=0.0):
    """Bulk-insert n ResultSimulation rows with synthetic GT/IT/TG/D values."""
    base = datetime.date(2024, 3, 1)
    rows = [
        ResultSimulation(
            fk_simulation=simulation,
            date=base + datetime.timedelta(days=i),
            demand_mean=100 + i,
            demand_std_deviation=10,
            variables={
                "GT": float(500 + i * 10 + profit_offset),
                "IT": float(2000 + i * 20),
                "TG": float(1500 + i * 10),
                "D":  float(100 + i),
            },
            is_active=True,
        )
        for i in range(n)
    ]
    ResultSimulation.objects.bulk_create(rows)
    return rows


# ── SimulationProgressView ────────────────────────────────────────────────────


class TestSimulationProgressView:

    @pytest.mark.django_db
    def test_db_fallback_pending(self, client, user, simulation):
        _login(client, user)
        url = reverse("simulate:api.progress", args=[simulation.id])
        with patch("django.core.cache.cache.get", return_value=None):
            resp = client.get(url)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "pending"
        assert data["is_completed"] is False

    @pytest.mark.django_db
    def test_db_fallback_completed(self, client, user, simulation):
        simulation.is_completed = True
        simulation.save()
        _login(client, user)
        url = reverse("simulate:api.progress", args=[simulation.id])
        with patch("django.core.cache.cache.get", return_value=None):
            resp = client.get(url)
        data = resp.json()
        assert data["status"] == "completed"
        assert data["is_completed"] is True

    @pytest.mark.django_db
    def test_db_fallback_progress_with_results(self, client, user, simulation):
        _make_results(simulation, n=5)
        _login(client, user)
        url = reverse("simulate:api.progress", args=[simulation.id])
        with patch("django.core.cache.cache.get", return_value=None):
            resp = client.get(url)
        data = resp.json()
        assert data["status"] == "processing"
        assert data["completed_days"] == 5
        assert data["total_days"] == 10

    @pytest.mark.django_db
    def test_celery_success_path(self, client, user, simulation):
        _login(client, user)
        url = reverse("simulate:api.progress", args=[simulation.id])
        mock_result = MagicMock()
        mock_result.state = "SUCCESS"
        mock_result.info = {}
        with patch("django.core.cache.cache.get", return_value="fake-task-id"), \
             patch("simulate.views.api_views.AsyncResult", return_value=mock_result):
            resp = client.get(url)
        data = resp.json()
        assert data["is_completed"] is True
        assert data["progress"] == 100

    @pytest.mark.django_db
    def test_celery_progress_path(self, client, user, simulation):
        _login(client, user)
        url = reverse("simulate:api.progress", args=[simulation.id])
        mock_result = MagicMock()
        mock_result.state = "PROGRESS"
        mock_result.info = {"current": 30, "total": 100, "phase": "monte_carlo"}
        with patch("django.core.cache.cache.get", return_value="fake-task-id"), \
             patch("simulate.views.api_views.AsyncResult", return_value=mock_result):
            resp = client.get(url)
        data = resp.json()
        assert data["status"] == "processing"
        assert data["progress"] == 30.0
        assert data["phase"] == "monte_carlo"

    @pytest.mark.django_db
    def test_celery_failure_path(self, client, user, simulation):
        _login(client, user)
        url = reverse("simulate:api.progress", args=[simulation.id])
        mock_result = MagicMock()
        mock_result.state = "FAILURE"
        mock_result.info = {}
        mock_result.result = Exception("Computation failed")
        with patch("django.core.cache.cache.get", return_value="fake-task-id"), \
             patch("simulate.views.api_views.AsyncResult", return_value=mock_result):
            resp = client.get(url)
        data = resp.json()
        assert data["status"] == "failed"
        assert data["is_completed"] is False

    @pytest.mark.django_db
    def test_unauthenticated_redirects(self, client, simulation):
        url = reverse("simulate:api.progress", args=[simulation.id])
        resp = client.get(url)
        assert resp.status_code == 302

    @pytest.mark.django_db
    def test_not_found_returns_404(self, client, user):
        _login(client, user)
        url = reverse("simulate:api.progress", args=[99999])
        resp = client.get(url)
        assert resp.status_code == 404


# ── SimulationCompareView ─────────────────────────────────────────────────────


class TestSimulationCompareView:

    @pytest.mark.django_db
    def test_compare_returns_winner(self, client, user, simulation, simulation2):
        _make_results(simulation, n=10, profit_offset=0.0)
        _make_results(simulation2, n=10, profit_offset=10000.0)
        _login(client, user)
        url = reverse("simulate:api.compare")
        resp = client.get(url, {"ids": f"{simulation.id},{simulation2.id}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["winner_simulation_id"] == simulation2.id
        assert len(data["comparisons"]) == 2

    @pytest.mark.django_db
    def test_compare_kpi_keys_present(self, client, user, simulation, simulation2):
        _make_results(simulation, n=10)
        _make_results(simulation2, n=10)
        _login(client, user)
        url = reverse("simulate:api.compare")
        resp = client.get(url, {"ids": f"{simulation.id},{simulation2.id}"})
        data = resp.json()
        entry = data["comparisons"][0]
        for key in (
            "total_profit", "total_revenue", "total_costs",
            "profit_margin_pct", "var_95", "probability_loss_pct", "mean_demand",
        ):
            assert key in entry, f"Missing KPI key: {key}"

    @pytest.mark.django_db
    def test_compare_no_results_entry(self, client, user, simulation, simulation2):
        # simulation has no results — entry should contain no_results flag
        _make_results(simulation2, n=10)
        _login(client, user)
        url = reverse("simulate:api.compare")
        resp = client.get(url, {"ids": f"{simulation.id},{simulation2.id}"})
        data = resp.json()
        empty_entry = next(c for c in data["comparisons"] if c["simulation_id"] == simulation.id)
        assert empty_entry.get("no_results") is True

    @pytest.mark.django_db
    def test_compare_requires_two_ids(self, client, user, simulation):
        _login(client, user)
        url = reverse("simulate:api.compare")
        resp = client.get(url, {"ids": str(simulation.id)})
        assert resp.status_code == 400

    @pytest.mark.django_db
    def test_compare_invalid_ids_returns_400(self, client, user):
        _login(client, user)
        url = reverse("simulate:api.compare")
        resp = client.get(url, {"ids": "abc,xyz"})
        assert resp.status_code == 400

    @pytest.mark.django_db
    def test_compare_unauthenticated_redirects(self, client, simulation, simulation2):
        url = reverse("simulate:api.compare")
        resp = client.get(url, {"ids": f"{simulation.id},{simulation2.id}"})
        assert resp.status_code == 302


# ── SimulationSensitivityView ─────────────────────────────────────────────────


class TestSimulationSensitivityView:

    @pytest.mark.django_db
    def test_sensitivity_success_structure(self, client, user, simulation):
        _make_results(simulation, n=10)
        _login(client, user)
        url = reverse("simulate:api.sensitivity", args=[simulation.id])
        resp = client.get(url)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "sensitivity" in data
        assert data["periods_analyzed"] == 10

    @pytest.mark.django_db
    def test_sensitivity_entry_schema(self, client, user, simulation):
        _make_results(simulation, n=10)
        _login(client, user)
        url = reverse("simulate:api.sensitivity", args=[simulation.id])
        resp = client.get(url)
        data = resp.json()
        assert len(data["sensitivity"]) > 0
        entry = data["sensitivity"][0]
        for key in ("variable", "correlation", "abs_correlation", "direction", "impact_label"):
            assert key in entry, f"Missing sensitivity key: {key}"
        assert entry["direction"] in ("positive", "negative")
        assert entry["impact_label"] in ("Alto", "Medio", "Bajo")

    @pytest.mark.django_db
    def test_sensitivity_sorted_by_abs_correlation(self, client, user, simulation):
        _make_results(simulation, n=10)
        _login(client, user)
        url = reverse("simulate:api.sensitivity", args=[simulation.id])
        resp = client.get(url)
        entries = resp.json()["sensitivity"]
        for i in range(len(entries) - 1):
            assert entries[i]["abs_correlation"] >= entries[i + 1]["abs_correlation"]

    @pytest.mark.django_db
    def test_sensitivity_gt_not_in_results(self, client, user, simulation):
        # GT itself should not appear as a driver since it is the target
        _make_results(simulation, n=10)
        _login(client, user)
        url = reverse("simulate:api.sensitivity", args=[simulation.id])
        resp = client.get(url)
        variables = [e["variable"] for e in resp.json()["sensitivity"]]
        assert "GT" not in variables

    @pytest.mark.django_db
    def test_sensitivity_needs_four_periods(self, client, user, simulation):
        base = datetime.date(2024, 5, 1)
        for i in range(3):
            ResultSimulation.objects.create(
                fk_simulation=simulation,
                date=base + datetime.timedelta(days=i),
                demand_mean=100,
                demand_std_deviation=10,
                variables={"GT": 500.0, "IT": 2000.0},
                is_active=True,
            )
        _login(client, user)
        url = reverse("simulate:api.sensitivity", args=[simulation.id])
        resp = client.get(url)
        assert resp.status_code == 400

    @pytest.mark.django_db
    def test_sensitivity_not_found_returns_404(self, client, user):
        _login(client, user)
        url = reverse("simulate:api.sensitivity", args=[99999])
        resp = client.get(url)
        assert resp.status_code == 404

    @pytest.mark.django_db
    def test_sensitivity_unauthenticated_redirects(self, client, simulation):
        url = reverse("simulate:api.sensitivity", args=[simulation.id])
        resp = client.get(url)
        assert resp.status_code == 302


# ── SimulationHistoryView ─────────────────────────────────────────────────────


class TestSimulationHistoryView:

    @pytest.mark.django_db
    def test_history_returns_aggregation(self, client, user, business, simulation):
        simulation.is_completed = True
        simulation.save()
        _login(client, user)
        url = reverse("simulate:api.history")
        resp = client.get(url, {"business_id": business.id})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["total_simulations"] >= 1
        assert data["completed_simulations"] >= 1
        assert len(data["timeline"]) >= 1

    @pytest.mark.django_db
    def test_history_timeline_entry_schema(self, client, user, business, simulation):
        _login(client, user)
        url = reverse("simulate:api.history")
        resp = client.get(url, {"business_id": business.id})
        data = resp.json()
        assert len(data["timeline"]) > 0
        entry = data["timeline"][0]
        for key in ("month", "total", "completed", "avg_days"):
            assert key in entry, f"Missing timeline key: {key}"

    @pytest.mark.django_db
    def test_history_top_products_schema(self, client, user, business, simulation):
        _login(client, user)
        url = reverse("simulate:api.history")
        resp = client.get(url, {"business_id": business.id})
        data = resp.json()
        for product_entry in data.get("top_products", []):
            assert "name" in product_entry
            assert "count" in product_entry

    @pytest.mark.django_db
    def test_history_requires_business_id(self, client, user):
        _login(client, user)
        url = reverse("simulate:api.history")
        resp = client.get(url)
        assert resp.status_code == 400

    @pytest.mark.django_db
    def test_history_access_denied_for_other_user(self, client, user2, business):
        client.login(username=user2.username, password="pass_other")
        url = reverse("simulate:api.history")
        resp = client.get(url, {"business_id": business.id})
        assert resp.status_code == 404

    @pytest.mark.django_db
    def test_history_unauthenticated_redirects(self, client, business):
        url = reverse("simulate:api.history")
        resp = client.get(url, {"business_id": business.id})
        assert resp.status_code == 302


# ── SimulationExportView ──────────────────────────────────────────────────────


class TestSimulationExportView:

    @pytest.mark.django_db
    def test_json_export_top_level_keys(self, client, user, simulation):
        _make_results(simulation, n=5)
        _login(client, user)
        url = reverse("simulate:api.export", args=[simulation.id])
        resp = client.get(url, {"format": "json"})
        assert resp.status_code == 200
        data = resp.json()
        for key in ("simulation_id", "product", "business", "risk_summary", "periods"):
            assert key in data, f"Missing JSON export key: {key}"

    @pytest.mark.django_db
    def test_json_export_simulation_id_matches(self, client, user, simulation):
        _make_results(simulation, n=5)
        _login(client, user)
        url = reverse("simulate:api.export", args=[simulation.id])
        resp = client.get(url, {"format": "json"})
        assert resp.json()["simulation_id"] == simulation.id

    @pytest.mark.django_db
    def test_json_export_period_count(self, client, user, simulation):
        _make_results(simulation, n=5)
        _login(client, user)
        url = reverse("simulate:api.export", args=[simulation.id])
        resp = client.get(url, {"format": "json"})
        assert len(resp.json()["periods"]) == 5

    @pytest.mark.django_db
    def test_json_export_risk_summary_keys(self, client, user, simulation):
        _make_results(simulation, n=5)
        _login(client, user)
        url = reverse("simulate:api.export", args=[simulation.id])
        resp = client.get(url, {"format": "json"})
        rs = resp.json()["risk_summary"]
        for key in ("total_profit", "mean", "std", "var_95", "probability_loss_pct"):
            assert key in rs, f"Missing risk_summary key: {key}"

    @pytest.mark.django_db
    def test_excel_export_content_type(self, client, user, simulation):
        _make_results(simulation, n=5)
        _login(client, user)
        url = reverse("simulate:api.export", args=[simulation.id])
        resp = client.get(url, {"format": "excel"})
        assert resp.status_code == 200
        assert "spreadsheetml" in resp.get("Content-Type", "")

    @pytest.mark.django_db
    def test_excel_export_has_attachment_header(self, client, user, simulation):
        _make_results(simulation, n=5)
        _login(client, user)
        url = reverse("simulate:api.export", args=[simulation.id])
        resp = client.get(url, {"format": "excel"})
        assert "attachment" in resp.get("Content-Disposition", "")
        assert ".xlsx" in resp.get("Content-Disposition", "")

    @pytest.mark.django_db
    def test_export_not_found_returns_404(self, client, user):
        _login(client, user)
        url = reverse("simulate:api.export", args=[99999])
        resp = client.get(url)
        assert resp.status_code == 404

    @pytest.mark.django_db
    def test_export_unauthenticated_redirects(self, client, simulation):
        url = reverse("simulate:api.export", args=[simulation.id])
        resp = client.get(url)
        assert resp.status_code == 302


# ── SimulationService cache helpers ──────────────────────────────────────────


class TestSimulationServiceCacheKey:

    @pytest.mark.django_db
    def test_cache_key_none_without_seed(self, simulation):
        from simulate.services.simulation_service import SimulationService
        simulation.random_seed = None
        key = SimulationService._pipeline_cache_key(simulation, 1000)
        assert key is None

    @pytest.mark.django_db
    def test_cache_key_is_deterministic(self, simulation):
        from simulate.services.simulation_service import SimulationService
        key1 = SimulationService._pipeline_cache_key(simulation, 1000)
        key2 = SimulationService._pipeline_cache_key(simulation, 1000)
        assert key1 is not None
        assert key1 == key2

    @pytest.mark.django_db
    def test_cache_key_differs_for_different_n_scenarios(self, simulation):
        from simulate.services.simulation_service import SimulationService
        key1 = SimulationService._pipeline_cache_key(simulation, 1000)
        key2 = SimulationService._pipeline_cache_key(simulation, 500)
        assert key1 != key2

    @pytest.mark.django_db
    def test_run_full_pipeline_uses_cache_hit(self, simulation):
        from simulate.services.simulation_service import SimulationService
        service = SimulationService()
        fake = {"aggregated": "mocked", "decision_report": None, "period_results": []}
        with patch("django.core.cache.cache.get", return_value=fake):
            result = service.run_full_pipeline(simulation, n_monte_carlo=10)
        assert result is fake


# ── InsufficientDataError propagation ────────────────────────────────────────


class TestInsufficientDataError:

    @pytest.mark.django_db
    def test_raised_when_no_demand_history(self, user, questionary, questionary_result):
        from simulate.services.simulation_service import SimulationService
        service = SimulationService()
        with patch.object(service, "_extract_demand_history", return_value=[]), \
             patch.object(service, "_get_questionary_with_data", return_value=questionary_result):
            with pytest.raises(InsufficientDataError):
                service.prepare_simulation_analysis(
                    questionary_id=questionary_result.id,
                    user=user,
                    quantity_time=10,
                    unit_time="days",
                )
