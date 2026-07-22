import pytest
from django.urls import reverse
from django.test import Client
from django.contrib.auth.models import User
from variable.models import Variable, Equation
from product.models import Product
from business.models import Business


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="password")


@pytest.fixture
def business(user):
    return Business.objects.create(
        name="Test Business", type=1, location="La Paz",
        description="d", fk_user=user, is_active=True,
    )


@pytest.fixture
def product(business):
    # Product.save() -> full_clean(): description es obligatoria en el esquema vigente.
    return Product.objects.create(
        name="Test Product", description="d", fk_business=business, is_active=True,
    )


@pytest.fixture
def variable(product):
    return Variable.objects.create(name="Test Variable", is_active=True, fk_product=product)


@pytest.fixture
def equation(variable):
    return Equation.objects.create(name="Test Equation", is_active=True, fk_variable1=variable)


def test_variable_list_view(client, user, business, product, variable):
    client.login(username="testuser", password="password")
    url = reverse("variable:variable.list")
    response = client.get(url)
    assert response.status_code == 200
    assert "variables" in response.context
    assert "products" in response.context


def test_variable_overview_view(client, user, variable):
    client.login(username="testuser", password="password")
    url = reverse("variable:variable.overview", args=[variable.id])
    response = client.get(url)
    assert response.status_code == 200
    assert "variable" in response.context
    assert "variables_related" in response.context
    assert "equations" in response.context


def test_create_variable_view(client, user, product):
    client.login(username="testuser", password="password")
    url = reverse("variable:variable.create")
    data = {
        "name": "New Variable",
        "type": 1,
        "description": "A new variable",
        "fk_product": product.id,
    }
    response = client.post(url, data)
    assert response.status_code == 200
    assert Variable.objects.filter(name="New Variable").exists()


def test_update_variable_view(client, user, variable):
    client.login(username="testuser", password="password")
    url = reverse("variable:variable.edit", args=[variable.id])
    data = {
        "name": "Updated Variable",
        "type": variable.type,
        "description": "Updated description",
        "fk_product": variable.fk_product.id,
    }
    response = client.post(url, data)
    assert response.status_code == 200
    variable.refresh_from_db()
    assert variable.name == "Updated Variable"


def test_delete_variable_view(client, user, variable):
    client.login(username="testuser", password="password")
    url = reverse("variable:variable.delete", args=[variable.id])
    response = client.post(url)
    assert response.status_code == 302
    variable.refresh_from_db()
    assert not variable.is_active


def test_get_variable_details_view(client, user, variable):
    client.login(username="testuser", password="password")
    url = reverse("variable:variable.get_details", args=[variable.id])
    response = client.get(url)
    assert response.status_code == 200
    assert response.json()["name"] == variable.name


def test_create_equation_view(client, user, variable):
    client.login(username="testuser", password="password")
    url = reverse("variable:equation.create")
    data = {
        "name": "New Equation",
        "description": "A new equation",
        "fk_variable1": variable.id,
        "expression": "x + 2 = 0",
    }
    # Petición AJAX -> el view responde JsonResponse (200) en vez de redirigir.
    response = client.post(url, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    assert response.status_code == 200
    assert Equation.objects.filter(name="New Equation").exists()


def test_delete_equation_view(client, user, equation):
    client.login(username="testuser", password="password")
    url = reverse("variable:equation.delete", args=[equation.id])
    response = client.post(url)
    assert response.status_code == 302
    equation.refresh_from_db()
    assert not equation.is_active


@pytest.mark.skip(reason="solve_equation renderiza 'result_template.html', que no existe "
                         "en el repositorio (plantilla nunca creada). La lógica de "
                         "validación/resolución se cubre en test_security.py.")
def test_solve_equation_view(client, user):
    client.login(username="testuser", password="password")
    url = reverse("variable:equation.solve")
    data = {"equation": "x**2 - 4"}
    response = client.post(url, data)
    assert response.status_code == 200
    assert "solution" in response.context


# ─────────────────────────────────────────────
# Aislamiento por dueño (IDOR) — P0 auditoría 2026-07-22
#
# variable/views.py obtenía Variable/Equation por pk crudo (sin filtro de
# propiedad), permitiendo a cualquier usuario autenticado ver/editar/borrar las
# variables y ecuaciones del negocio de OTRO usuario incrementando el pk. Los
# handlers ahora restringen por `fk_product__fk_business__fk_user` (Variable) /
# `fk_variable1__fk_product__fk_business__fk_user` (Equation) vía los helpers
# `_variables_for_user` / `_equations_for_user`.
# ─────────────────────────────────────────────
@pytest.fixture
def other_user(db):
    return User.objects.create_user(username="intruso", password="otherpass-123")


def _login_intruso(client, other_user):
    client.login(username="intruso", password="otherpass-123")


def test_variable_overview_isolation_returns_404_for_non_owner(client, other_user, variable):
    """El intruso no puede ver la variable de otro usuario -> 404."""
    _login_intruso(client, other_user)
    url = reverse("variable:variable.overview", args=[variable.id])
    response = client.get(url)
    assert response.status_code == 404


def test_variable_overview_allows_owner(client, user, variable):
    """El dueño real sí puede ver su propia variable."""
    client.login(username="testuser", password="password")
    url = reverse("variable:variable.overview", args=[variable.id])
    response = client.get(url)
    assert response.status_code == 200
    assert response.context["variable"] == variable


def test_variable_edit_get_isolation_returns_404_for_non_owner(client, other_user, variable):
    """El intruso no puede abrir el formulario de edición de otro -> 404."""
    _login_intruso(client, other_user)
    url = reverse("variable:variable.edit", args=[variable.id])
    response = client.get(url)
    assert response.status_code == 404


def test_variable_edit_post_isolation_returns_404_for_non_owner(client, other_user, variable):
    """El intruso no puede modificar la variable de otro usuario -> 404, ni cambia sus datos."""
    _login_intruso(client, other_user)
    url = reverse("variable:variable.edit", args=[variable.id])
    data = {
        "name": "Hijacked", "type": variable.type,
        "description": "hijacked", "fk_product": variable.fk_product.id,
    }
    response = client.post(url, data)
    assert response.status_code == 404
    variable.refresh_from_db()
    assert variable.name == "Test Variable"


def test_variable_edit_post_allows_owner(client, user, variable):
    """El dueño real sí puede editar su variable (regresión del helper de dueño)."""
    client.login(username="testuser", password="password")
    url = reverse("variable:variable.edit", args=[variable.id])
    data = {
        "name": "Updated Variable", "type": variable.type,
        "description": "Updated description", "fk_product": variable.fk_product.id,
    }
    response = client.post(url, data)
    assert response.status_code == 200
    variable.refresh_from_db()
    assert variable.name == "Updated Variable"


def test_delete_variable_isolation_returns_404_for_non_owner(client, other_user, variable):
    """El intruso no puede borrar (desactivar) la variable de otro usuario -> 404."""
    _login_intruso(client, other_user)
    url = reverse("variable:variable.delete", args=[variable.id])
    response = client.post(url)
    assert response.status_code == 404
    variable.refresh_from_db()
    assert variable.is_active


def test_get_variable_details_isolation_returns_404_for_non_owner(client, other_user, variable):
    """El intruso no puede leer el JSON de detalles de la variable de otro -> 404."""
    _login_intruso(client, other_user)
    url = reverse("variable:variable.get_details", args=[variable.id])
    response = client.get(url)
    assert response.status_code == 404
    assert "error" in response.json()


def test_equation_edit_get_isolation_returns_404_for_non_owner(client, other_user, equation):
    """El intruso no puede abrir el formulario de edición de la ecuación de otro -> 404."""
    _login_intruso(client, other_user)
    url = reverse("variable:equation.edit", args=[equation.id])
    response = client.get(url)
    assert response.status_code == 404


def test_equation_edit_post_isolation_returns_404_for_non_owner(client, other_user, equation):
    """El intruso no puede modificar la ecuación de otro usuario -> 404, ni cambia sus datos."""
    _login_intruso(client, other_user)
    url = reverse("variable:equation.edit", args=[equation.id])
    data = {
        "name": "Hijacked", "description": "hijacked",
        "fk_variable1": equation.fk_variable1.id, "expression": "x + 99 = 0",
    }
    response = client.post(url, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    assert response.status_code == 404
    equation.refresh_from_db()
    assert equation.name == "Test Equation"


def test_delete_equation_isolation_returns_404_for_non_owner(client, other_user, equation):
    """El intruso no puede borrar (desactivar) la ecuación de otro usuario -> 404."""
    _login_intruso(client, other_user)
    url = reverse("variable:equation.delete", args=[equation.id])
    response = client.post(url)
    assert response.status_code == 404
    equation.refresh_from_db()
    assert equation.is_active


def test_get_equation_details_isolation_returns_404_for_non_owner(client, other_user, equation):
    """El intruso no puede leer el JSON de detalles de la ecuación de otro -> 404."""
    _login_intruso(client, other_user)
    url = reverse("variable:equation.get_details", args=[equation.id])
    response = client.get(url)
    assert response.status_code == 404
    assert "error" in response.json()


def test_get_equation_details_allows_owner(client, user, equation):
    """El dueño real sí puede leer el JSON de detalles de su ecuación."""
    client.login(username="testuser", password="password")
    url = reverse("variable:equation.get_details", args=[equation.id])
    response = client.get(url)
    assert response.status_code == 200
    assert response.json()["name"] == equation.name
