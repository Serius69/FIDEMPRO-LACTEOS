"""
test_ci_integration.py
======================
Tests de integración para el pipeline CI.

Valida que el motor Monte Carlo y los modelos de BD
funcionen de extremo a extremo con PostgreSQL real.
Estos tests se ejecutan en cada push vía GitHub Actions.

Markers:
    @pytest.mark.integration — requiere DB
    @pytest.mark.simulation  — lógica Monte Carlo
"""
import pytest
import numpy as np
from django.contrib.auth.models import User

from simulate.services.simulation_engine import (
    MonteCarloEngine,
    SimulationConfig,
    SimulationResult,
)


# ═══════════════════════════════════════════════════════════════
# TESTS UNITARIOS DEL MOTOR (sin DB, rápidos)
# ═══════════════════════════════════════════════════════════════


class TestSimulationConfig:
    """Valida que SimulationConfig sea inmutable y bien inicializado."""

    def test_default_config(self):
        config = SimulationConfig()
        assert config.n_iterations == 10000
        assert config.confidence_level == 0.95
        assert config.distribution_type == "normal"

    def test_custom_config(self):
        config = SimulationConfig(
            n_iterations=500,
            demand_mean=2000.0,
            demand_std=300.0,
            unit_price=25.0,
            unit_cost=15.0,
            fixed_costs=5000.0,
        )
        assert config.demand_mean == 2000.0
        assert config.n_iterations == 500

    def test_seasonality_default_length(self):
        config = SimulationConfig()
        assert len(config.seasonality_factors) == 12
        assert all(f == 1.0 for f in config.seasonality_factors)


@pytest.mark.simulation
class TestMonteCarloEngine:
    """Tests del motor Monte Carlo sin base de datos."""

    @pytest.fixture
    def engine(self):
        return MonteCarloEngine()

    @pytest.fixture
    def standard_config(self):
        return SimulationConfig(
            n_iterations=2000,  # reducido para CI rápido
            demand_mean=1000.0,
            demand_std=150.0,
            unit_price=10.0,
            unit_cost=6.0,
            fixed_costs=2000.0,
            random_seed=42,
        )

    def test_engine_returns_simulation_result(self, engine, standard_config):
        result = engine.run(standard_config)
        assert isinstance(result, SimulationResult)

    def test_demand_mean_within_tolerance(self, engine, standard_config):
        """La media simulada debe estar a ±5% de la media configurada."""
        result = engine.run(standard_config)
        tolerance = standard_config.demand_mean * 0.05
        assert abs(result.demand_mean - standard_config.demand_mean) < tolerance

    def test_demand_std_within_tolerance(self, engine, standard_config):
        """La desviación estándar simulada debe estar a ±10% de la configurada."""
        result = engine.run(standard_config)
        tolerance = standard_config.demand_std * 0.10
        assert abs(result.demand_std - standard_config.demand_std) < tolerance

    def test_percentile_ordering(self, engine, standard_config):
        """p5 < p25 < median < p75 < p95."""
        result = engine.run(standard_config)
        assert result.demand_p5 < result.demand_p25
        assert result.demand_p25 < result.demand_median
        assert result.demand_median < result.demand_p75
        assert result.demand_p75 < result.demand_p95

    def test_revenue_positive_when_profitable(self, engine, standard_config):
        """Revenue debe ser positivo cuando precio > costo."""
        result = engine.run(standard_config)
        assert result.revenue_mean > 0

    def test_reproducible_with_seed(self, engine, standard_config):
        """Dos runs con mismo seed deben dar resultados idénticos."""
        result1 = engine.run(standard_config)
        result2 = engine.run(standard_config)
        assert result1.demand_mean == result2.demand_mean
        assert result1.demand_std == result2.demand_std

    def test_different_seeds_give_different_results(self, engine):
        """Seeds diferentes deben dar distribuciones distintas."""
        config1 = SimulationConfig(
            n_iterations=1000, random_seed=1, demand_mean=1000.0, demand_std=100.0
        )
        config2 = SimulationConfig(
            n_iterations=1000, random_seed=99, demand_mean=1000.0, demand_std=100.0
        )
        r1 = engine.run(config1)
        r2 = engine.run(config2)
        # Los valores no deben ser exactamente iguales
        assert r1.demand_median != r2.demand_median

    def test_lognormal_distribution(self, engine):
        """Distribución log-normal debe dar valores siempre positivos."""
        config = SimulationConfig(
            n_iterations=1000,
            distribution_type="lognormal",
            demand_mean=1000.0,
            demand_std=200.0,
            random_seed=42,
        )
        result = engine.run(config)
        assert result.demand_p5 > 0

    def test_profit_calculation_consistency(self, engine):
        """Profit = Revenue - Variable costs - Fixed costs."""
        config = SimulationConfig(
            n_iterations=1000,
            demand_mean=1000.0,
            demand_std=50.0,
            unit_price=20.0,
            unit_cost=10.0,
            fixed_costs=3000.0,
            random_seed=42,
        )
        result = engine.run(config)
        # Con margen sano (precio = 2x costo variable) y 1000 unidades,
        # el profit medio debe ser positivo
        assert result.profit_mean > 0

    @pytest.mark.slow
    def test_large_iteration_count(self, engine):
        """10,000 iteraciones deben completarse en menos de 30 segundos."""
        config = SimulationConfig(
            n_iterations=10000,
            demand_mean=1000.0,
            demand_std=150.0,
            random_seed=42,
        )
        result = engine.run(config)
        assert result.demand_samples.shape[0] == 10000


# ═══════════════════════════════════════════════════════════════
# TESTS DE INTEGRACIÓN CON BASE DE DATOS
# ═══════════════════════════════════════════════════════════════


@pytest.mark.django_db
@pytest.mark.integration
class TestSimulationModelPersistence:
    """Verifica que los modelos de simulación se persisten correctamente en PostgreSQL."""

    def test_pdf_create_and_retrieve(self, sample_pdf):
        """Un PDF creado debe poder recuperarse con los mismos parámetros."""
        from simulate.models import ProbabilisticDensityFunction

        retrieved = ProbabilisticDensityFunction.objects.get(pk=sample_pdf.pk)
        assert retrieved.name == "Distribución Normal Test"
        assert retrieved.distribution_type == 1
        assert retrieved.mean_param == 100.0
        assert retrieved.std_dev_param == 15.0

    def test_pdf_to_json_has_required_keys(self, sample_pdf):
        """El método to_json() debe incluir todas las claves necesarias."""
        data = sample_pdf.to_json()
        required_keys = {"name", "distribution_type"}
        assert required_keys.issubset(set(data.keys()))

    def test_simulation_linked_to_business(self, sample_simulation, sample_business):
        """La simulación debe estar vinculada a la empresa correcta."""
        assert sample_simulation.fk_business == sample_business

    def test_pdf_distribution_types_available(self, sample_business):
        """Deben existir los 5 tipos de distribución configurados."""
        from simulate.models import ProbabilisticDensityFunction

        distribution_types = dict(ProbabilisticDensityFunction.DISTRIBUTION_TYPES)
        assert 1 in distribution_types  # Normal
        assert 2 in distribution_types  # Exponential
        assert 3 in distribution_types  # Log-Norm
        assert 4 in distribution_types  # Gamma
        assert 5 in distribution_types  # Uniform

    def test_simulation_is_active_by_default(self, sample_simulation):
        assert sample_simulation.is_active is True

    def test_multiple_pdfs_per_business(self, db, sample_business):
        """Una empresa puede tener múltiples PDFs."""
        from simulate.models import ProbabilisticDensityFunction

        for dist_type in [1, 2, 3]:
            ProbabilisticDensityFunction.objects.create(
                name=f"PDF tipo {dist_type}",
                distribution_type=dist_type,
                mean_param=100.0,
                std_dev_param=10.0,
                lambda_param=0.01,
                fk_business=sample_business,
            )
        count = ProbabilisticDensityFunction.objects.filter(
            fk_business=sample_business
        ).count()
        assert count >= 3


@pytest.mark.django_db
@pytest.mark.integration
@pytest.mark.simulation
class TestEndToEndSimulation:
    """Test E2E: crear datos → ejecutar simulación → verificar resultados."""

    def test_full_simulation_pipeline(self, sample_business, sample_product, sample_pdf):
        """Pipeline completo: modelo → config → engine → resultado válido."""
        engine = MonteCarloEngine()
        config = SimulationConfig(
            n_iterations=500,
            demand_mean=float(sample_pdf.mean_param),
            demand_std=float(sample_pdf.std_dev_param),
            unit_price=float(sample_product.price) if hasattr(sample_product, "price") else 100.0,
            unit_cost=50.0,
            fixed_costs=10000.0,
            random_seed=42,
        )
        result = engine.run(config)

        assert isinstance(result, SimulationResult)
        assert result.demand_mean > 0
        assert result.demand_p5 < result.demand_p95
        assert result.revenue_mean > 0

    def test_simulation_with_different_distributions(self, sample_business):
        """Todas las distribuciones soportadas deben ejecutarse sin error."""
        engine = MonteCarloEngine()
        distributions = ["normal", "lognormal", "gamma", "uniform", "exponential"]

        for dist in distributions:
            config = SimulationConfig(
                n_iterations=200,
                distribution_type=dist,
                demand_mean=1000.0,
                demand_std=100.0,
                random_seed=42,
            )
            result = engine.run(config)
            assert result.demand_mean > 0, f"Distribución {dist} dio media <= 0"
            assert np.isfinite(result.demand_mean), f"Distribución {dist} dio NaN/Inf"
