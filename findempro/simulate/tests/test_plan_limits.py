import json
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings

from business.models import Business
from product.models import Product
from questionary.models import Questionary, QuestionaryResult
from simulate.models import ProbabilisticDensityFunction, Simulation
from simulate.plan_limits import verificar_limite
from simulate.views.simulate_init_view import SimulateShowView


DEMAND_HISTORY = [100] * 10


def _simulation_context(username, *, is_staff=False):
    user = User.objects.create_user(username=username, is_staff=is_staff)
    business = Business.objects.create(
        name=f"Negocio {username}",
        type=1,
        location="Test",
        fk_user=user,
    )
    product = Product.objects.create(
        name=f"Producto {username}",
        description="Producto para verificar límites",
        fk_business=business,
    )
    questionary = Questionary.objects.create(
        questionary="Cuestionario de prueba",
        fk_product=product,
    )
    result = QuestionaryResult.objects.create(fk_questionary=questionary)
    fdp = ProbabilisticDensityFunction.objects.get(
        fk_business=business,
        distribution_type=1,
    )
    return user, result, fdp


def _create_simulations(result, fdp, count):
    Simulation.objects.bulk_create([
        Simulation(
            fk_questionary_result=result,
            fk_fdp=fdp,
            demand_history=DEMAND_HISTORY,
        )
        for _ in range(count)
    ])


class PlanLimitTests(SimpleTestCase):
    def setUp(self):
        self.user = SimpleNamespace(is_staff=False, is_superuser=False)

    @override_settings(PLAN_GATES_ENABLED=False)
    @patch("simulate.plan_limits.Simulation.objects.filter")
    def test_flag_apagado_siempre_permite(self, filter_mock):
        assert verificar_limite(self.user, "basico") == (True, 0, None)
        filter_mock.assert_not_called()

    @override_settings(
        PLAN_GATES_ENABLED=True,
        PLAN_SIM_LIMITS={"basico": 10, "pro": 100, "empresa": None},
    )
    @patch("simulate.plan_limits.Simulation.objects.filter")
    def test_basico_con_diez_usadas_no_permite(self, filter_mock):
        filter_mock.return_value.count.return_value = 10
        assert verificar_limite(self.user, "basico") == (False, 10, 10)

    @override_settings(
        PLAN_GATES_ENABLED=True,
        PLAN_SIM_LIMITS={"basico": 10, "pro": 100, "empresa": None},
    )
    @patch("simulate.plan_limits.Simulation.objects.filter")
    def test_pro_bajo_el_limite_permite(self, filter_mock):
        filter_mock.return_value.count.return_value = 10
        assert verificar_limite(self.user, "pro") == (True, 10, 100)

    @override_settings(PLAN_GATES_ENABLED=True)
    @patch("simulate.plan_limits.Simulation.objects.filter")
    def test_superuser_es_ilimitado(self, filter_mock):
        filter_mock.return_value.count.return_value = 500
        superuser = SimpleNamespace(is_staff=False, is_superuser=True)
        assert verificar_limite(superuser, "basico") == (True, 500, None)


class PlanLimitViewTests(SimpleTestCase):
    @override_settings(HUB_UPGRADE_URL="https://hub.example/upgrade")
    @patch("simulate.views.simulate_init_view.verificar_limite")
    def test_start_rechazado_devuelve_402_json(self, verificar_mock):
        verificar_mock.return_value = (False, 10, 10)
        request = RequestFactory().post("/simulate/init/", {"action": "start"})
        request.user = SimpleNamespace(is_staff=False, is_superuser=False)
        request.hub_plan = "basico"

        response = SimulateShowView().post(request)

        assert response.status_code == 402
        assert json.loads(response.content) == {
            "error": "LIMITE_SIMULACIONES",
            "usadas": 10,
            "limite": 10,
            "plan": "basico",
            "upgrade_url": "https://hub.example/upgrade",
        }

    @patch("simulate.views.simulate_init_view.verificar_limite")
    def test_start_permitido_conserva_el_flujo_normal(self, verificar_mock):
        verificar_mock.return_value = (True, 0, None)
        request = RequestFactory().post("/simulate/init/", {"action": "start"})
        request.user = SimpleNamespace(is_staff=False, is_superuser=False)
        expected = HttpResponse(status=204)
        view = SimulateShowView()
        view._handle_simulation_start = Mock(return_value=expected)

        response = view.post(request)

        assert response is expected
        view._handle_simulation_start.assert_called_once_with(request)


@pytest.mark.django_db
@override_settings(
    PLAN_GATES_ENABLED=True,
    PLAN_SIM_LIMITS={"basico": 10, "pro": 100, "empresa": None},
    HUB_UPGRADE_URL="https://hub.example/upgrade",
)
def test_limite_real_de_bd_devuelve_402_al_superarse():
    user, result, fdp = _simulation_context("limited-user")
    _create_simulations(result, fdp, 10)
    request = RequestFactory().post("/simulate/init/", {"action": "start"})
    request.user = user
    request.hub_plan = "basico"

    response = SimulateShowView().post(request)

    assert response.status_code == 402
    assert json.loads(response.content)["usadas"] == 10
    assert Simulation.objects.count() == 10


@pytest.mark.django_db
@override_settings(
    PLAN_GATES_ENABLED=True,
    PLAN_SIM_LIMITS={"basico": 10, "pro": 100, "empresa": None},
)
def test_staff_es_ilimitado_con_conteo_real_de_bd():
    staff, result, fdp = _simulation_context("staff-user", is_staff=True)
    _create_simulations(result, fdp, 11)
    assert verificar_limite(staff, "basico") == (True, 11, None)

    request = RequestFactory().post("/simulate/init/", {"action": "start"})
    request.user = staff
    request.hub_plan = "basico"
    expected = HttpResponse(status=204)
    view = SimulateShowView()
    view._handle_simulation_start = Mock(return_value=expected)

    response = view.post(request)

    assert response is expected
    view._handle_simulation_start.assert_called_once_with(request)
