import pytest
from django.contrib.auth.models import User
from variable.models import Variable, Equation, EquationResult
from product.models import Product, Area
from business.models import Business


def _make_product():
    """Construye la cadena mínima User -> Business -> Product exigida por el esquema
    vigente (Product.save() llama full_clean(): fk_business y description obligatorios)."""
    user = User.objects.create_user(username="owner", password="pw")
    business = Business.objects.create(
        name="Test Business", type=1, location="La Paz",
        description="d", fk_user=user, is_active=True,
    )
    return Product.objects.create(
        name="Test Product", description="d", fk_business=business, is_active=True,
    )


def _make_area(product):
    return Area.objects.create(name="Test Area", description="d", fk_product=product)


@pytest.mark.django_db
def test_variable_creation():
    product = _make_product()
    variable = Variable.objects.create(
        name="Test Variable",
        initials="TV",
        type=1,
        unit="kg",
        description="Test description",
        fk_product=product,
        is_active=True
    )
    assert variable.name == "Test Variable"
    assert variable.initials == "TV"
    assert variable.type == 1
    assert variable.unit == "kg"
    assert variable.description == "Test description"
    assert variable.fk_product == product
    assert variable.is_active is True
    assert variable.get_photo_url() == "/media/images/variable/variable-dummy-img.jpg"


@pytest.mark.django_db
def test_equation_creation():
    product = _make_product()
    variable1 = Variable.objects.create(name="Variable 1", fk_product=product)
    variable2 = Variable.objects.create(name="Variable 2", fk_product=product)
    area = _make_area(product)
    equation = Equation.objects.create(
        name="Test Equation",
        description="Test description",
        expression="var1=var2+var3",
        fk_variable1=variable1,
        fk_variable2=variable2,
        fk_area=area,
        is_active=True
    )
    assert equation.name == "Test Equation"
    assert equation.description == "Test description"
    assert equation.expression == "var1=var2+var3"
    assert equation.fk_variable1 == variable1
    assert equation.fk_variable2 == variable2
    assert equation.fk_area == area
    assert equation.is_active is True


@pytest.mark.django_db
def test_equation_result_creation():
    product = _make_product()
    variable1 = Variable.objects.create(name="Variable 1", fk_product=product)
    variable2 = Variable.objects.create(name="Variable 2", fk_product=product)
    area = _make_area(product)
    equation = Equation.objects.create(
        name="Test Equation",
        description="Test description",
        expression="var1=var2+var3",
        fk_variable1=variable1,
        fk_variable2=variable2,
        fk_area=area,
        is_active=True
    )
    equation_result = EquationResult.objects.create(
        fk_equation=equation,
        result=42.00,
        is_active=True
    )
    assert equation_result.fk_equation == equation
    assert equation_result.result == 42.00
    assert equation_result.is_active is True


@pytest.mark.django_db
def test_variable_str_method():
    product = _make_product()
    variable = Variable.objects.create(name="Test Variable", fk_product=product)
    assert str(variable) == "Test Variable"


@pytest.mark.django_db
def test_equation_result_str_method():
    product = _make_product()
    variable1 = Variable.objects.create(name="Variable 1", fk_product=product)
    variable2 = Variable.objects.create(name="Variable 2", fk_product=product)
    area = _make_area(product)
    equation = Equation.objects.create(
        name="Test Equation",
        description="Test description",
        expression="var1=var2+var3",
        fk_variable1=variable1,
        fk_variable2=variable2,
        fk_area=area,
        is_active=True
    )
    equation_result = EquationResult.objects.create(
        fk_equation=equation,
        result=42.00,
        is_active=True
    )
    assert str(equation_result) == "Result for Equation Test Equation"
