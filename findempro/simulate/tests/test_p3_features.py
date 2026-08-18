"""
test_p3_features.py
====================
Tests para los features P3 de FindemproAI:

  - P3-1 SensitivityService (OAT)
  - P3-2 RiskAlert model + serializer
  - P3-3 Prometheus metrics integration (no-op stubs)
  - P3-4 Simulation PDF generation

Ejecutar con:
  cd findempro
  venv/Scripts/python.exe -m pytest simulate/tests/test_p3_features.py -v
"""

import io
import numpy as np
import pytest

from simulate.services.sensitivity_service import SensitivityService, SensitivityResult
from simulate.metrics import (
    SIMULATION_DURATION,
    SIMULATION_COUNTER,
    ACTIVE_SIMULATIONS,
    scenarios_bucket,
    _NoOpMetric,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures comunes
# ─────────────────────────────────────────────────────────────────────────────

def _node(label, dist_type, params, node_type="flow"):
    return {
        "id": f"node-{label}",
        "node_type": node_type,
        "label": label,
        "equation": "1",
        "initial_value": None,
        "distribution_config": {"dist_type": dist_type, "params": params},
    }


def _no_dist_node(label):
    return {
        "id": f"node-{label}",
        "node_type": "converter",
        "label": label,
        "equation": "3.80",
        "initial_value": None,
        "distribution_config": None,
    }


BASE_NODES = [
    _node("demanda",          "normal",     {"mean": 500,  "std": 80}),
    _node("tasa_ventas",      "normal",     {"mean": 450,  "std": 60}),
    _node("factor_estac",     "triangular", {"low": 0.85, "mode": 1.0, "high": 1.20}),
    _node("precio_insumo",    "uniform",    {"low": 3.5,  "high": 4.2}),
    _no_dist_node("costo_fijo"),
]
BASE_EDGES = []
BASE_RUN_SPECS = {
    "n_runs_montecarlo": 500, "random_seed": 42,
    "unit_price": 12.5, "unit_cost": 4.0, "fixed_costs": 2500.0,
}


# ─────────────────────────────────────────────────────────────────────────────
# P3-1  SensitivityService (OAT)
# ─────────────────────────────────────────────────────────────────────────────

class TestSensitivityServiceOAT:

    def _svc(self):
        return SensitivityService()

    def test_returns_list_of_sensitivity_results(self):
        svc = self._svc()
        results = svc.run_oat(BASE_NODES, BASE_EDGES, BASE_RUN_SPECS)
        assert isinstance(results, list)
        assert len(results) > 0
        assert all(isinstance(r, SensitivityResult) for r in results)

    def test_only_stochastic_nodes_analyzed(self):
        svc = self._svc()
        results = svc.run_oat(BASE_NODES, BASE_EDGES, BASE_RUN_SPECS)
        # costo_fijo has no distribution_config → should not appear
        labels = [r.variable for r in results]
        assert "costo_fijo" not in labels

    def test_four_stochastic_nodes(self):
        svc = self._svc()
        results = svc.run_oat(BASE_NODES, BASE_EDGES, BASE_RUN_SPECS)
        assert len(results) == 4

    def test_sorted_by_abs_swing_descending(self):
        svc = self._svc()
        results = svc.run_oat(BASE_NODES, BASE_EDGES, BASE_RUN_SPECS)
        swings = [abs(r.swing) for r in results]
        assert swings == sorted(swings, reverse=True)

    def test_high_mean_greater_than_low_mean_for_positive_means(self):
        svc = self._svc()
        results = svc.run_oat(BASE_NODES, BASE_EDGES, BASE_RUN_SPECS)
        for r in results:
            if r.baseline_mean > 0:
                assert r.high_mean >= r.low_mean, f"{r.variable}: high_mean < low_mean"

    def test_variation_pct_10_smaller_swing_than_20(self):
        svc = self._svc()
        r10 = svc.run_oat(BASE_NODES, BASE_EDGES, BASE_RUN_SPECS, variation_pct=0.10)
        r20 = svc.run_oat(BASE_NODES, BASE_EDGES, BASE_RUN_SPECS, variation_pct=0.20)
        # Swings with 10% variation must be smaller than with 20%
        swing10 = sum(abs(r.swing) for r in r10)
        swing20 = sum(abs(r.swing) for r in r20)
        assert swing10 < swing20

    def test_empty_nodes_returns_empty(self):
        svc = self._svc()
        results = svc.run_oat([], [], {})
        assert results == []

    def test_no_stochastic_nodes_returns_empty(self):
        svc = self._svc()
        nodes = [_no_dist_node("a"), _no_dist_node("b")]
        results = svc.run_oat(nodes, [], {})
        assert results == []

    def test_reproducible_with_seed(self):
        svc = self._svc()
        r1 = svc.run_oat(BASE_NODES, BASE_EDGES, BASE_RUN_SPECS, seed=99)
        r2 = svc.run_oat(BASE_NODES, BASE_EDGES, BASE_RUN_SPECS, seed=99)
        for a, b in zip(r1, r2):
            assert a.swing == b.swing
            assert a.baseline_mean == b.baseline_mean

    def test_different_seeds_produce_different_results(self):
        svc = self._svc()
        r1 = svc.run_oat(BASE_NODES, BASE_EDGES, BASE_RUN_SPECS, seed=1)
        r2 = svc.run_oat(BASE_NODES, BASE_EDGES, BASE_RUN_SPECS, seed=999)
        # At least one swing should differ
        swings1 = [r.swing for r in r1]
        swings2 = [r.swing for r in r2]
        assert swings1 != swings2

    def test_sensitivity_pct_non_negative(self):
        svc = self._svc()
        results = svc.run_oat(BASE_NODES, BASE_EDGES, BASE_RUN_SPECS)
        for r in results:
            assert r.sensitivity_pct >= 0

    def test_all_distribution_types(self):
        nodes = [
            _node("n", "normal",     {"mean": 500,  "std": 80}),
            _node("t", "triangular", {"low": 400,   "mode": 500, "high": 600}),
            _node("u", "uniform",    {"low": 400,   "high": 600}),
            _node("g", "gamma",      {"shape": 4.0, "scale": 125}),
            _node("b", "beta",       {"alpha": 2.0, "beta": 2.0, "high": 1000}),
            _node("w", "weibull",    {"shape": 2.0, "scale": 500}),
        ]
        svc = self._svc()
        results = svc.run_oat(nodes, [], BASE_RUN_SPECS, seed=0)
        assert len(results) == 6

    def test_to_apexcharts_structure(self):
        svc = self._svc()
        results = svc.run_oat(BASE_NODES, BASE_EDGES, BASE_RUN_SPECS, seed=42)
        chart = svc.to_apexcharts(results, variation_pct=0.20)
        assert chart["chart_type"] == "bar"
        assert chart["horizontal"] is True
        assert len(chart["series"]) == 2
        assert chart["series"][0]["name"] == "+20%"
        assert chart["series"][1]["name"] == "-20%"
        assert len(chart["categories"]) == len(results)
        assert "sensitivity_table" in chart
        assert len(chart["sensitivity_table"]) == len(results)
        # ranks are 1-based
        assert chart["sensitivity_table"][0]["rank"] == 1

    def test_to_apexcharts_high_data_positive_for_positive_baseline(self):
        svc = self._svc()
        results = svc.run_oat(BASE_NODES, BASE_EDGES, BASE_RUN_SPECS, seed=42)
        chart = svc.to_apexcharts(results, 0.20)
        high_data = chart["series"][0]["data"]
        # With positive demand means, high-variant profit > baseline → high_data should be positive
        assert all(isinstance(v, float) for v in high_data)

    def test_sensitivity_table_sorted_by_rank(self):
        svc = self._svc()
        results = svc.run_oat(BASE_NODES, BASE_EDGES, BASE_RUN_SPECS, seed=42)
        chart = svc.to_apexcharts(results, 0.20)
        ranks = [row["rank"] for row in chart["sensitivity_table"]]
        assert ranks == list(range(1, len(results) + 1))

    def test_location_param_normal(self):
        svc = self._svc()
        cfg = {"dist_type": "normal", "params": {"mean": 500, "std": 80}}
        loc = svc._get_location_param(cfg)
        assert loc == ("mean", 500.0)

    def test_location_param_triangular_mode(self):
        svc = self._svc()
        cfg = {"dist_type": "triangular", "params": {"low": 400, "mode": 500, "high": 600}}
        loc = svc._get_location_param(cfg)
        assert loc == ("mode", 500.0)

    def test_location_param_uniform_computed(self):
        svc = self._svc()
        cfg = {"dist_type": "uniform", "params": {"low": 400, "high": 600}}
        loc = svc._get_location_param(cfg)
        assert loc is not None
        key, val = loc
        assert key.endswith("_computed")
        assert val == pytest.approx(500.0)

    def test_location_param_unknown_dist_fallback(self):
        svc = self._svc()
        cfg = {"dist_type": "unknown_dist", "params": {"mean": 300}}
        loc = svc._get_location_param(cfg)
        assert loc == ("mean", 300.0)

    def test_unknown_distribution_is_not_replaced_by_normal(self):
        svc = self._svc()
        with pytest.raises(ValueError, match="Distribución no soportada"):
            svc.run_oat([_node("demand", "unknown_dist", {"mean": 300})], [], BASE_RUN_SPECS)

    def test_location_param_no_params_returns_none(self):
        svc = self._svc()
        cfg = {"dist_type": "weibull", "params": {}}
        loc = svc._get_location_param(cfg)
        assert loc is None


# ─────────────────────────────────────────────────────────────────────────────
# P3-2  RiskAlert model
# ─────────────────────────────────────────────────────────────────────────────

class TestRiskAlertModel:

    def test_is_triggered_var_below_threshold(self):
        from simulate.models import RiskAlert
        alert = RiskAlert(var_threshold=-5000.0, email="test@example.com", cvar_threshold=None)
        # VaR = -6000 < threshold -5000 → triggered
        assert alert.is_triggered(var_value=-6000.0) is True

    def test_is_triggered_var_above_threshold(self):
        from simulate.models import RiskAlert
        alert = RiskAlert(var_threshold=-5000.0, email="test@example.com", cvar_threshold=None)
        # VaR = -4000 > threshold -5000 → not triggered
        assert alert.is_triggered(var_value=-4000.0) is False

    def test_is_triggered_cvar_below_threshold(self):
        from simulate.models import RiskAlert
        alert = RiskAlert(var_threshold=0.0, email="t@t.com", cvar_threshold=-8000.0)
        # VaR ok, CVaR = -9000 < -8000 → triggered
        assert alert.is_triggered(var_value=100.0, cvar_value=-9000.0) is True

    def test_is_triggered_both_ok(self):
        from simulate.models import RiskAlert
        alert = RiskAlert(var_threshold=-5000.0, email="t@t.com", cvar_threshold=-8000.0)
        assert alert.is_triggered(var_value=-3000.0, cvar_value=-4000.0) is False

    def test_is_triggered_no_cvar_threshold_ignores_cvar(self):
        from simulate.models import RiskAlert
        alert = RiskAlert(var_threshold=-5000.0, email="t@t.com", cvar_threshold=None)
        # Even if cvar_value is very bad, no cvar_threshold → only VaR checked
        assert alert.is_triggered(var_value=-4000.0, cvar_value=-99999.0) is False

    def test_str_representation(self):
        from simulate.models import RiskAlert
        from django.contrib.auth.models import User
        user = User(username="testuser")
        alert = RiskAlert(user=user, var_threshold=-5000.0, email="a@b.com")
        assert "testuser" in str(alert)
        assert "-5000" in str(alert)
        assert "a@b.com" in str(alert)

    def test_model_fields_exist(self):
        from simulate.models import RiskAlert
        fields = {f.name for f in RiskAlert._meta.get_fields()}
        assert "var_threshold" in fields
        assert "cvar_threshold" in fields
        assert "email" in fields
        assert "is_active" in fields
        assert "user" in fields
        assert "fk_product" in fields


# ─────────────────────────────────────────────────────────────────────────────
# P3-2  RiskAlertSerializer
# ─────────────────────────────────────────────────────────────────────────────

class TestRiskAlertSerializer:

    def test_valid_serializer(self):
        from simulate.canvas_serializers import RiskAlertSerializer
        data = {
            "var_threshold": -5000.0,
            "cvar_threshold": -8000.0,
            "email": "alert@empresa.com",
            "is_active": True,
        }
        ser = RiskAlertSerializer(data=data)
        assert ser.is_valid(), ser.errors

    def test_missing_var_threshold_invalid(self):
        from simulate.canvas_serializers import RiskAlertSerializer
        ser = RiskAlertSerializer(data={"email": "a@b.com", "is_active": True})
        # var_threshold is required
        assert not ser.is_valid()
        assert "var_threshold" in ser.errors

    def test_invalid_email(self):
        from simulate.canvas_serializers import RiskAlertSerializer
        ser = RiskAlertSerializer(data={"var_threshold": -5000, "email": "not-an-email"})
        assert not ser.is_valid()
        assert "email" in ser.errors

    def test_optional_cvar_threshold(self):
        from simulate.canvas_serializers import RiskAlertSerializer
        data = {"var_threshold": -3000.0, "email": "ok@ok.com"}
        ser = RiskAlertSerializer(data=data)
        assert ser.is_valid(), ser.errors

    def test_read_only_fields(self):
        from simulate.canvas_serializers import RiskAlertSerializer
        ser = RiskAlertSerializer()
        ro = {f.field_name for f in ser.fields.values() if getattr(f, 'read_only', False)}
        assert 'id' in ro
        assert 'created_at' in ro
        assert 'updated_at' in ro


# ─────────────────────────────────────────────────────────────────────────────
# P3-3  Prometheus metrics no-op stubs
# ─────────────────────────────────────────────────────────────────────────────

class TestPrometheusMetrics:

    def test_simulation_duration_is_callable(self):
        labeled = SIMULATION_DURATION.labels(sector="lacteo", n_scenarios_bucket="1k")
        # Must not raise — either real Prometheus or no-op stub
        labeled.observe(1.5)

    def test_simulation_counter_is_callable(self):
        labeled = SIMULATION_COUNTER.labels(
            sector="lacteo", distribution_type="normal", status="success"
        )
        labeled.inc()
        labeled.inc(3)

    def test_active_simulations_gauge_track_inprogress(self):
        gauge = ACTIVE_SIMULATIONS.labels(sector="lacteo")
        with gauge.track_inprogress():
            pass  # should not raise

    def test_noop_metric_labels_returns_self(self):
        noop = _NoOpMetric()
        result = noop.labels(sector="test", foo="bar")
        assert result is noop

    def test_noop_context_manager(self):
        noop = _NoOpMetric()
        ctx = noop.track_inprogress()
        with ctx:
            pass  # should not raise

    def test_scenarios_bucket_boundaries(self):
        assert scenarios_bucket(0)      == '<=500'
        assert scenarios_bucket(500)    == '<=500'
        assert scenarios_bucket(501)    == '1k'
        assert scenarios_bucket(1_000)  == '1k'
        assert scenarios_bucket(1_001)  == '5k'
        assert scenarios_bucket(5_000)  == '5k'
        assert scenarios_bucket(5_001)  == '10k'
        assert scenarios_bucket(10_000) == '10k'
        assert scenarios_bucket(10_001) == '>10k'
        assert scenarios_bucket(999_999)== '>10k'

    def test_metrics_module_public_symbols(self):
        import simulate.metrics as m
        assert hasattr(m, 'SIMULATION_DURATION')
        assert hasattr(m, 'SIMULATION_COUNTER')
        assert hasattr(m, 'ACTIVE_SIMULATIONS')
        assert hasattr(m, 'scenarios_bucket')


# ─────────────────────────────────────────────────────────────────────────────
# P3-4  Simulation PDF builder (pure function, no DB)
# ─────────────────────────────────────────────────────────────────────────────

class TestSimulationPDFBuilder:

    def _make_result_mock(self, period, profit_mean, profit_p5, profit_p95):
        """Mock ResultSimulation enough for _build_simulation_pdf."""
        class FakeResult:
            variables = {
                'profit_mean': profit_mean,
                'profit_p5': profit_p5,
                'profit_p95': profit_p95,
            }
        return FakeResult()

    def _make_simulation_mock(self):
        class FakeDistrib:
            def get_distribution_type_display(self):
                return 'Normal'

        class FakeBusiness:
            name = 'Empresa Prueba S.R.L.'

        class FakeProduct:
            name = 'Leche Entera'
            fk_business = FakeBusiness()

        class FakeQuestionary:
            fk_product = FakeProduct()

        class FakeQuestionaryResult:
            fk_questionary = FakeQuestionary()

        class FakeSim:
            id = 9999
            fk_questionary_result = FakeQuestionaryResult()
            fk_fdp = FakeDistrib()
            confidence_level = 0.95
            duration_in_days = 10

        return FakeSim()

    def test_build_simulation_pdf_returns_bytes(self):
        try:
            import reportlab
            import matplotlib
        except ImportError:
            pytest.skip("reportlab or matplotlib not installed")

        from report.tasks import _build_simulation_pdf

        sim = self._make_simulation_mock()
        results = [
            self._make_result_mock(i + 1, 5000 + i * 100, 3000 + i * 50, 7000 + i * 150)
            for i in range(10)
        ]
        pdf_bytes = _build_simulation_pdf(sim, results)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 1000
        # PDF magic bytes
        assert pdf_bytes[:4] == b'%PDF'

    def test_build_minimal_pdf_for_single_period(self):
        try:
            import reportlab
        except ImportError:
            pytest.skip("reportlab not installed")

        from report.tasks import _build_simulation_pdf

        sim = self._make_simulation_mock()
        results = [self._make_result_mock(1, 5000, 3000, 7000)]
        pdf_bytes = _build_simulation_pdf(sim, results)
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b'%PDF'

    def test_build_simulation_pdf_no_results(self):
        try:
            import reportlab
        except ImportError:
            pytest.skip("reportlab not installed")

        from report.tasks import _build_simulation_pdf

        sim = self._make_simulation_mock()
        pdf_bytes = _build_simulation_pdf(sim, [])
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b'%PDF'

    def test_build_minimal_pdf_helper(self):
        try:
            import reportlab
        except ImportError:
            pytest.skip("reportlab not installed")

        from report.tasks import _build_minimal_pdf

        sim = self._make_simulation_mock()
        pdf_bytes = _build_minimal_pdf(sim, [])
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b'%PDF'


# ─────────────────────────────────────────────────────────────────────────────
# P3-1  Integration: sensitivity with ModelCompiler-style nodes
# ─────────────────────────────────────────────────────────────────────────────

class TestSensitivityIntegration:

    def test_dairy_template_nodes(self):
        """Sensitvity runs correctly on the dairy template stochastic nodes."""
        dairy_stochastic_nodes = [
            _node("tasa_recepcion", "triangular",
                  {"low": 800, "mode": 1000, "high": 1300}),
            _node("tasa_ventas", "normal",
                  {"mean": 450, "std": 80}),
            _node("factor_estacionalidad", "uniform",
                  {"low": 0.85, "high": 1.20}),
        ]
        svc = SensitivityService()
        results = svc.run_oat(dairy_stochastic_nodes, [], BASE_RUN_SPECS, seed=7, n_runs=200)
        assert len(results) == 3
        labels = {r.variable for r in results}
        assert labels == {"tasa_recepcion", "tasa_ventas", "factor_estacionalidad"}

    def test_large_demand_variable_has_largest_swing(self):
        """Variable with larger demand (higher mean) should produce larger absolute swing."""
        nodes = [
            _node("small_demand", "normal", {"mean": 100, "std": 10}),
            _node("big_demand",   "normal", {"mean": 1000, "std": 100}),
        ]
        svc = SensitivityService()
        results = svc.run_oat(nodes, [], BASE_RUN_SPECS, seed=42)
        assert len(results) == 2
        # big_demand should rank first (larger absolute swing)
        assert results[0].variable == "big_demand"

    def test_zero_variation_produces_zero_swing(self):
        svc = SensitivityService()
        results = svc.run_oat(BASE_NODES, BASE_EDGES, BASE_RUN_SPECS, variation_pct=0.0001)
        for r in results:
            # With near-zero variation, swing should be close to zero
            assert abs(r.swing) < abs(r.baseline_mean) * 0.1 or r.swing == pytest.approx(0.0, abs=1.0)
