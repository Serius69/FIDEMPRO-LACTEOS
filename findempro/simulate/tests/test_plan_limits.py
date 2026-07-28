import json
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings

from simulate.plan_limits import verificar_limite
from simulate.views.simulate_init_view import SimulateShowView


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
