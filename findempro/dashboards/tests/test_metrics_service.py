"""
Tests de regresión para DashboardService:

1. Las métricas financieras quedan a escala de UNA simulación (promedio por
   período de la simulación más reciente), NO la suma multiplicada por el nº de
   simulaciones ni por el nº de períodos (fix de agregación inflada).
2. Las recomendaciones NO salen vacías cuando existen datos: se anota sobre el
   campo real ``metric_value`` en vez del campo ``data`` (eliminado en la
   migración finance/0009), que provocaba FieldError -> lista siempre vacía.
"""
from datetime import date, timedelta

import pytest
from django.utils import timezone

from business.models import Business
from product.models import Product
from questionary.models import Questionary, QuestionaryResult
from simulate.models import (
    ProbabilisticDensityFunction,
    Simulation,
    ResultSimulation,
)
from finance.models import FinanceRecommendationSimulation
from dashboards.services.dashboard_service import DashboardService


def _make_simulation(business, pdf, days_offset=0):
    """Crea el grafo mínimo negocio->...->Simulation."""
    product = Product.objects.create(
        name=f"Producto {days_offset}",
        description="prod de prueba",
        fk_business=business,
        type=1,
    )
    questionary = Questionary.objects.create(questionary="Q", fk_product=product)
    qresult = QuestionaryResult.objects.create(fk_questionary=questionary)
    sim = Simulation.objects.create(
        quantity_time=5,
        unit_time="days",
        fk_fdp=pdf,
        demand_history=[10.0] * 12,  # >=10 valores para pasar full_clean
        fk_questionary_result=qresult,
        date_created=timezone.now() - timedelta(days=days_offset),
    )
    return sim


def _add_periods(sim, n, tpv, it, gt):
    """Agrega n períodos (ResultSimulation) con las mismas variables por período."""
    for i in range(n):
        ResultSimulation.objects.create(
            demand_mean=100,
            demand_std_deviation=5,
            date=date(2025, 1, 1) + timedelta(days=i),
            variables={"TPV": tpv, "IT": it, "GT": gt},
            fk_simulation=sim,
        )


@pytest.mark.django_db
def test_metrics_are_single_simulation_scale(django_user_model):
    """revenue/costs/profit deben ser el promedio por período de la simulación
    más reciente, no la suma sobre todas las simulaciones y períodos."""
    user = django_user_model.objects.create_user(username="u1", password="p")
    business = Business.objects.create(
        name="Neg escala", type=1, location="La Paz",
        description="x", fk_user=user, is_active=True,
    )
    pdf, _ = ProbabilisticDensityFunction.objects.get_or_create(
        distribution_type=1, fk_business=business,
        defaults=dict(name="Normal", mean_param=100, std_dev_param=10),
    )

    # Simulación ANTIGUA: 5 períodos con TPV=100 (no debe contarse)
    old_sim = _make_simulation(business, pdf, days_offset=30)
    _add_periods(old_sim, n=5, tpv=100, it=60, gt=40)

    # Simulación RECIENTE: 5 períodos con TPV=100 -> promedio esperado = 100
    new_sim = _make_simulation(business, pdf, days_offset=0)
    _add_periods(new_sim, n=5, tpv=100, it=60, gt=40)

    metrics = DashboardService._calculate_enhanced_metrics([old_sim, new_sim])

    # La versión con bug daría 2 sims * 5 períodos * 100 = 1000.
    # Correcto: promedio por período de la simulación más reciente = 100.
    assert metrics.revenue == 100.0
    assert metrics.costs == 60.0
    assert metrics.profit == 40.0
    # Escala acotada: nunca del orden de sum(sims*periodos)
    assert metrics.revenue < 500


@pytest.mark.django_db
def test_recommendations_not_empty_when_data_exists(django_user_model):
    """Con FinanceRecommendationSimulation existentes, la lista no debe salir
    vacía (regresión del FieldError por Avg('data'))."""
    user = django_user_model.objects.create_user(username="u2", password="p")
    business = Business.objects.create(
        name="Neg rec", type=1, location="La Paz",
        description="x", fk_user=user, is_active=True,
    )
    pdf, _ = ProbabilisticDensityFunction.objects.get_or_create(
        distribution_type=1, fk_business=business,
        defaults=dict(name="Normal", mean_param=100, std_dev_param=10),
    )
    sim = _make_simulation(business, pdf, days_offset=0)

    FinanceRecommendationSimulation.objects.create(
        fk_simulation=sim,
        title="Rec 1",
        category="financial",
        metric_value=0.8,
    )
    FinanceRecommendationSimulation.objects.create(
        fk_simulation=sim,
        title="Rec 2",
        category="profitability",
        metric_value=0.4,
    )

    recs = DashboardService._get_enhanced_recommendations(business.id)

    assert len(recs) >= 1  # ya no [] por FieldError
    # Ambas recs son de la misma simulación -> se agrupan (GROUP BY) y se
    # promedia metric_value: (0.8 + 0.4) / 2 = 0.6. Esto prueba que se anota
    # sobre metric_value (real) y NO se cae al fallback 0.5.
    data_values = [r["data"] for r in recs]
    assert any(v == pytest.approx(0.6) for v in data_values)
    assert all(v != 0.5 for v in data_values)
