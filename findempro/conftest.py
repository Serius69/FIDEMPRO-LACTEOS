"""
conftest.py — Fixtures compartidas para toda la suite de tests de FINDEMPRO AI.

Fixtures disponibles por scope:
  - db_user / admin_user         → usuarios de prueba
  - authenticated_client         → APIClient autenticado
  - sample_business              → empresa de prueba
  - sample_product               → producto con area
"""
import pytest
from django.contrib.auth.models import User
from django.test import Client
from rest_framework.test import APIClient


# ─────────────────────────────────────────────────────────────────
# Usuarios
# ─────────────────────────────────────────────────────────────────

@pytest.fixture
def db_user(db):
    """Usuario regular sin privilegios especiales."""
    return User.objects.create_user(
        username="testuser",
        email="testuser@findempro.test",
        password="testpass123",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def admin_user(db):
    """Superusuario para tests de admin."""
    return User.objects.create_superuser(
        username="admin",
        email="admin@findempro.test",
        password="adminpass123",
    )


@pytest.fixture
def second_user(db):
    """Segundo usuario para tests de aislamiento por tenant."""
    return User.objects.create_user(
        username="otheruser",
        email="other@findempro.test",
        password="otherpass123",
    )


# ─────────────────────────────────────────────────────────────────
# Clientes HTTP
# ─────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    """Django test client (sin autenticar)."""
    return Client()


@pytest.fixture
def authenticated_client(db_user):
    """Django test client autenticado como db_user."""
    client = Client()
    client.force_login(db_user)
    return client


@pytest.fixture
def api_client():
    """DRF APIClient (sin autenticar)."""
    return APIClient()


@pytest.fixture
def authenticated_api_client(db_user):
    """DRF APIClient autenticado como db_user."""
    client = APIClient()
    client.force_authenticate(user=db_user)
    return client


@pytest.fixture
def admin_api_client(admin_user):
    """DRF APIClient autenticado como admin."""
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


# ─────────────────────────────────────────────────────────────────
# Datos de negocio (Business)
# ─────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_business(db, db_user):
    """Empresa de prueba activa asociada a db_user."""
    from business.models import Business

    return Business.objects.create(
        name="Empresa Test SA",
        type=1,
        location="La Paz, Bolivia",
        description="Empresa de prueba para tests automatizados",
        fk_user=db_user,
        is_active=True,
    )


@pytest.fixture
def inactive_business(db, db_user):
    """Empresa inactiva para tests de filtrado."""
    from business.models import Business

    return Business.objects.create(
        name="Empresa Inactiva",
        type=1,
        location="Cochabamba, Bolivia",
        description="Empresa inactiva para tests",
        fk_user=db_user,
        is_active=False,
    )


# ─────────────────────────────────────────────────────────────────
# Datos de producto (Product + Area)
# ─────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_area(db, sample_business):
    """Área de producción de prueba."""
    from product.models import Area

    return Area.objects.create(
        name="Área de Producción",
        fk_business=sample_business,
        is_active=True,
    )


@pytest.fixture
def sample_product(db, sample_business, sample_area):
    """Producto de prueba asociado a una empresa y área."""
    from product.models import Product

    return Product.objects.create(
        name="Producto Test",
        description="Descripción del producto de prueba",
        fk_business=sample_business,
        fk_area=sample_area,
        price=100.00,
        is_active=True,
    )


# ─────────────────────────────────────────────────────────────────
# Datos de simulación
# ─────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_pdf(db, sample_business):
    """Función de densidad de probabilidad Normal de prueba."""
    from simulate.models import ProbabilisticDensityFunction

    return ProbabilisticDensityFunction.objects.create(
        name="Distribución Normal Test",
        distribution_type=1,  # Normal
        mean_param=100.0,
        std_dev_param=15.0,
        lambda_param=0.01,
        fk_business=sample_business,
    )


@pytest.fixture
def sample_simulation(db, sample_business, sample_product, sample_pdf):
    """Simulación básica de prueba."""
    from simulate.models import Simulation

    return Simulation.objects.create(
        name="Simulación Test",
        iterations=100,
        fk_business=sample_business,
        fk_product=sample_product,
        fk_pdf=sample_pdf,
        is_active=True,
    )
