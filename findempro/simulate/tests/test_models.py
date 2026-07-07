"""
Tests de modelos de la app simulate.

Reescrito para el esquema vigente:
  · Business exige fk_user; Product exige fk_business.
  · El signal post_save de Business crea automáticamente 5 PDFs (tipos 1-5),
    con unique_together (distribution_type, fk_business): NO se pueden crear PDFs
    duplicados manualmente. Los tests consultan los PDFs creados por el signal.
  · Métodos puros (calculate_elasticity, get_average_demand_by_date, …) se prueban
    sobre instancias en memoria, sin tocar la base de datos.
"""
import pytest
from datetime import date
from decimal import Decimal
from django.contrib.auth.models import User

from simulate.models import (
    ProbabilisticDensityFunction,
    ResultSimulation,
    Demand,
    DemandBehavior,
)
from business.models import Business


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def _make_business():
    user = User.objects.create_user(username='u_test', password='pw_test_1234')
    return Business.objects.create(
        name="Test Business", type=1, location="La Paz",
        description="desc", fk_user=user, is_active=True,
    )


# ─────────────────────────────────────────────
# Signal Business → PDFs
# ─────────────────────────────────────────────
@pytest.mark.django_db
def test_business_signal_creates_default_pdfs():
    business = _make_business()
    pdfs = ProbabilisticDensityFunction.objects.filter(fk_business=business)
    assert pdfs.count() == 5
    assert set(pdfs.values_list('distribution_type', flat=True)) == {1, 2, 3, 4, 5}


@pytest.mark.django_db
def test_pdf_default_name_is_distribution():
    """El default del campo name es 'Distribution' (a nivel de campo del modelo)."""
    field = ProbabilisticDensityFunction._meta.get_field('name')
    assert field.default == 'Distribution'


@pytest.mark.django_db
def test_pdf_str_representation():
    business = _make_business()
    pdf = ProbabilisticDensityFunction.objects.filter(
        fk_business=business, distribution_type=1).first()
    assert str(pdf) == f"{pdf.name} - {business.name}"


@pytest.mark.django_db
def test_pdf_to_json_keys_and_values():
    business = _make_business()
    pdf = ProbabilisticDensityFunction.objects.filter(
        fk_business=business, distribution_type=1).first()
    data = pdf.to_json()
    assert data['id'] == pdf.id
    assert data['distribution_type'] == 1
    assert data['fk_business'] == business.id
    assert data['is_active'] is True
    assert 'distribution_type_display' in data


@pytest.mark.django_db
def test_pdf_to_dict_includes_business_name():
    business = _make_business()
    pdf = ProbabilisticDensityFunction.objects.filter(
        fk_business=business, distribution_type=2).first()
    data = pdf.to_dict()
    assert data['business_name'] == business.name
    assert data['distribution_type'] == 2


# ─────────────────────────────────────────────
# ResultSimulation — métodos puros (sin DB)
# ─────────────────────────────────────────────
def test_result_get_average_demand_by_date():
    result = ResultSimulation(demand_mean=Decimal("100.50"), date=date(2023, 1, 1))
    out = result.get_average_demand_by_date()
    assert out == [{'date': '2023-01-01', 'average_demand': 100.5}]


def test_result_calculate_demand_variance():
    result = ResultSimulation(demand_std_deviation=Decimal("10.00"))
    assert result.calculate_demand_variance() == 100.0


def test_result_get_variable_value_default():
    result = ResultSimulation(variables={'precio': 12.5})
    assert result.get_variable_value('precio') == 12.5
    assert result.get_variable_value('inexistente', default=-1) == -1


# ─────────────────────────────────────────────
# DemandBehavior.calculate_elasticity — método puro (sin DB)
# ─────────────────────────────────────────────
@pytest.mark.parametrize('current,predicted,expected_type,expected_pct', [
    (100, 120, 'elastic', 20.0),      # >10% → elástica
    (100, 100.5, 'inelastic', 0.5),   # <1% → inelástica
    (100, 105, 'neutral', 5.0),       # entre 1% y 10% → neutral
])
def test_demand_behavior_calculate_elasticity(current, predicted, expected_type, expected_pct):
    d_cur = Demand(quantity=Decimal(str(current)))
    d_pred = Demand(quantity=Decimal(str(predicted)))
    behavior = DemandBehavior(current_demand=d_cur, predicted_demand=d_pred)
    elasticity_type, percentage_change = behavior.calculate_elasticity()
    assert elasticity_type == expected_type
    assert percentage_change == pytest.approx(expected_pct)


def test_demand_behavior_elasticity_zero_current_returns_none():
    behavior = DemandBehavior(
        current_demand=Demand(quantity=Decimal('0')),
        predicted_demand=Demand(quantity=Decimal('50')),
    )
    assert behavior.calculate_elasticity() == (None, None)
