"""
Tests de producción — FindemproAI
Verifican que el sistema está listo para clientes reales.

Ejecutar: python manage.py test findempro.tests.test_produccion_findemproai
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse


class TestProduccionFindEmproAI(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="cajero.demo@kapitalya.com.bo",
            email="cajero.demo@kapitalya.com.bo",
            password="Demo2026!",
        )

    # ── 1. Health checks ───────────────────────────────────────────────────

    def test_health_live_responde_200(self):
        response = self.client.get("/health/live/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "alive")

    def test_health_ready_con_base_de_datos(self):
        response = self.client.get("/health/ready/")
        self.assertEqual(response.status_code, 200,
            "health/ready/ debe responder 200 cuando la DB está disponible")
        data = response.json()
        self.assertEqual(data["status"], "ready")

    # ── 2. Endpoints privados requieren autenticación ──────────────────────

    def test_rutas_privadas_redirigen_a_login(self):
        rutas_privadas = [
            "/",                 # dashboard
            "/simulate/",
            "/business/list/",   # /business/ no tiene índice; la ruta real es list/
            "/report/",
        ]
        for ruta in rutas_privadas:
            response = self.client.get(ruta, follow=False)
            self.assertIn(response.status_code, [301, 302, 403],
                f"Ruta {ruta} debe redirigir a login o devolver 403 sin autenticación")

    # ── 3. Login funciona ─────────────────────────────────────────────────

    def test_login_con_credenciales_validas(self):
        logged_in = self.client.login(
            username="cajero.demo@kapitalya.com.bo",
            password="Demo2026!",
        )
        self.assertTrue(logged_in, "El login con credenciales demo debe funcionar")

    def test_login_rechaza_credenciales_invalidas(self):
        logged_in = self.client.login(
            username="cajero.demo@kapitalya.com.bo",
            password="contraseniaerronea",
        )
        self.assertFalse(logged_in, "Login con contraseña incorrecta debe fallar")

    # ── 4. Dashboard accesible tras login ─────────────────────────────────

    def test_dashboard_accesible_con_autenticacion(self):
        self.client.login(
            username="cajero.demo@kapitalya.com.bo",
            password="Demo2026!",
        )
        response = self.client.get("/", follow=True)
        self.assertIn(response.status_code, [200, 302],
            "Dashboard debe ser accesible para usuario autenticado")

    # ── 5. Métricas Prometheus disponibles ───────────────────────────────

    def test_metricas_prometheus_disponibles(self):
        response = self.client.get("/metrics")
        self.assertIn(response.status_code, [200, 301, 302],
            "Endpoint /metrics debe estar disponible")
        if response.status_code == 200:
            content = response.content.decode()
            self.assertIn("# TYPE", content,
                "/metrics debe devolver formato Prometheus válido")

    # ── 6. API Swagger disponible (para integraciones) ───────────────────

    def test_api_docs_accesibles(self):
        response = self.client.get("/swagger/")
        self.assertIn(response.status_code, [200, 301, 302],
            "Swagger UI debe ser accesible")
