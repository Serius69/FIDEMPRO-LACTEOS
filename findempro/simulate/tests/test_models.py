import pytest
from datetime import datetime
from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import ValidationError
from business.models import Business
from product.models import Product

from findempro.simulate.models import (
    ProbabilisticDensityFunction,
    Simulation,
    ResultSimulation,
    Demand,
    DemandBehavior,
)

@pytest.mark.django_db
def test_probabilistic_density_function_creation():
    business = Business.objects.create(name="Test Business", is_active=True)
    pdf = ProbabilisticDensityFunction.objects.create(
        name="Test PDF",
        distribution_type=1,
        lambda_param=0.5,
        mean_param=10.0,
        std_dev_param=2.0,
        fk_business=business,
    )
    assert pdf.name == "Test PDF"
    assert pdf.distribution_type == 1
    assert pdf.lambda_param == 0.5
    assert pdf.mean_param == 10.0
    assert pdf.std_dev_param == 2.0
    assert pdf.fk_business == business

@pytest.mark.django_db
def test_probabilistic_density_function_to_json():
    business = Business.objects.create(name="Test Business", is_active=True)
    pdf = ProbabilisticDensityFunction.objects.create(
        name="Test PDF",
        distribution_type=1,
        lambda_param=0.5,
        mean_param=10.0,
        std_dev_param=2.0,
        fk_business=business,
    )
    json_data = pdf.to_json()
    assert json_data["name"] == "Test PDF"
    assert json_data["distribution_type"] == 1
    assert json_data["lambda_param"] == 0.5

@pytest.mark.django_db
def test_simulation_creation():
    business = Business.objects.create(name="Test Business", is_active=True)
    pdf = ProbabilisticDensityFunction.objects.create(
        name="Test PDF",
        distribution_type=1,
        lambda_param=0.5,
        mean_param=10.0,
        std_dev_param=2.0,
        fk_business=business,
    )
    simulation = Simulation.objects.create(
        quantity_time=10,
        unit_time="day",
        fk_fdp=pdf,
        demand_history={"day_1": 100, "day_2": 120},
    )
    assert simulation.quantity_time == 10
    assert simulation.unit_time == "day"
    assert simulation.fk_fdp == pdf
    assert simulation.demand_history == {"day_1": 100, "day_2": 120}

@pytest.mark.django_db
def test_result_simulation_get_average_demand_by_date():
    simulation = Simulation.objects.create(quantity_time=10, unit_time="day")
    result_simulation = ResultSimulation.objects.create(
        demand_mean=Decimal("100.50"),
        demand_std_deviation=Decimal("10.25"),
        date="2023-01-01",
        fk_simulation=simulation,
    )
    average_demand = result_simulation.get_average_demand_by_date()
    assert len(average_demand) == 1
    assert average_demand[0]["date"] == "2023-01-01"
    assert average_demand[0]["average_demand"] == 100.5

@pytest.mark.django_db
def test_demand_creation():
    product = Product.objects.create(name="Test Product")
    simulation = Simulation.objects.create(quantity_time=10, unit_time="day")
    demand = Demand.objects.create(
        quantity=50,
        is_predicted=True,
        fk_simulation=simulation,
        fk_product=product,
    )
    assert demand.quantity == 50
    assert demand.is_predicted is True
    assert demand.fk_simulation == simulation
    assert demand.fk_product == product

@pytest.mark.django_db
def test_demand_behavior_calculate_elasticity():
    product = Product.objects.create(name="Test Product")
    simulation = Simulation.objects.create(quantity_time=10, unit_time="day")
    current_demand = Demand.objects.create(
        quantity=100, is_predicted=False, fk_simulation=simulation, fk_product=product
    )
    predicted_demand = Demand.objects.create(
        quantity=120, is_predicted=True, fk_simulation=simulation, fk_product=product
    )
    demand_behavior = DemandBehavior.objects.create(
        current_demand=current_demand, predicted_demand=predicted_demand
    )
    elasticity_type, percentage_change = demand_behavior.calculate_elasticity()
    assert elasticity_type == "Elastica"
    assert percentage_change == 20.0

# TESTS USAGE  
@pytest.mark.django_db
def test_probabilistic_density_function_str_representation():
    business = Business.objects.create(name="Test Business", is_active=True)
    pdf = ProbabilisticDensityFunction.objects.create(
        name="Test PDF",
        distribution_type=1,
        lambda_param=0.5,
        mean_param=10.0,
        std_dev_param=2.0,
        fk_business=business,
    )
    assert str(pdf) == "Test PDF"

@pytest.mark.django_db
def test_probabilistic_density_function_default_values():
    business = Business.objects.create(name="Test Business", is_active=True)
    pdf = ProbabilisticDensityFunction.objects.create(
        fk_business=business,
    )
    assert pdf.name == "Distribution"
    assert pdf.distribution_type == 1
    assert pdf.is_active is True

@pytest.mark.django_db
def test_probabilistic_density_function_field_error_messages():
    business = Business.objects.create(name="Test Business", is_active=True)
    with pytest.raises(ValidationError) as excinfo:
        ProbabilisticDensityFunction.objects.create(
            name="Invalid PDF",
            distribution_type=1,
            lambda_param=-1.0,  # Invalid value
            fk_business=business,
        )
    assert "Ensure this value is greater than or equal to 0." in str(excinfo.value)

@pytest.mark.django_db
def test_probabilistic_density_function_choices_are_logical():
    business = Business.objects.create(name="Test Business", is_active=True)
    pdf = ProbabilisticDensityFunction.objects.create(
        name="Test PDF",
        distribution_type=2,  # Exponential
        lambda_param=0.5,
        fk_business=business,
    )
    assert pdf.get_distribution_type_display() == "Exponential"