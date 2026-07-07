"""
Tests de hub_auth — validación de JWT del Hub SSO y middleware.

Cubre el módulo que antes NO tenía tests pese a ser crítico de seguridad:
  · validar_token: expiración, algoritmo, emisor, tipo, claims requeridos.
  · HubAuthMiddleware: rechazo de tokens de proyecto ajeno y, sobre todo,
    protección contra open redirect en el parámetro `next`.
"""
import time
import jwt
import pytest
from django.test import RequestFactory

from hub_auth.tokens import validar_token, AuthError
from hub_auth.middleware import HubAuthMiddleware, PROYECTO_SLUG

SECRET = "test-hub-shared-secret-1234567890"


@pytest.fixture
def hub_settings(settings):
    settings.HUB_JWT_SECRET = SECRET
    settings.ALLOWED_HOSTS = ["testserver"]
    return settings


def _make_token(secret=SECRET, alg="HS256", **overrides):
    now = int(time.time())
    payload = {
        "sub": "user-1",
        "iat": now,
        "exp": now + 300,
        "iss": "kapitalya-hub",
        "tipo": "access_token",
    }
    payload.update(overrides)
    return jwt.encode(payload, secret, algorithm=alg)


# ─────────────────────────────────────────────
# validar_token
# ─────────────────────────────────────────────
class TestValidarToken:
    def test_token_valido(self, hub_settings):
        payload = validar_token(_make_token(), tipo_esperado="access_token")
        assert payload["sub"] == "user-1"

    def test_token_expirado(self, hub_settings):
        expired = _make_token(exp=int(time.time()) - 10, iat=int(time.time()) - 320)
        with pytest.raises(AuthError, match="expirado"):
            validar_token(expired)

    def test_firma_invalida(self, hub_settings):
        with pytest.raises(AuthError):
            validar_token(_make_token(secret="otro-secret-distinto"))

    def test_algoritmo_none_rechazado(self, hub_settings):
        # Un atacante intenta un token 'alg: none' sin firma.
        malicioso = jwt.encode(
            {"sub": "x", "iat": int(time.time()), "exp": int(time.time()) + 300,
             "iss": "kapitalya-hub", "tipo": "access_token"},
            key="", algorithm="none",
        )
        with pytest.raises(AuthError):
            validar_token(malicioso)

    def test_emisor_incorrecto(self, hub_settings):
        with pytest.raises(AuthError, match="Emisor"):
            validar_token(_make_token(iss="atacante"))

    def test_tipo_desconocido(self, hub_settings):
        with pytest.raises(AuthError, match="Tipo"):
            validar_token(_make_token(tipo="cualquiera"))

    def test_tipo_esperado_no_coincide(self, hub_settings):
        with pytest.raises(AuthError):
            validar_token(_make_token(tipo="access_token"), tipo_esperado="project_token")

    def test_claim_requerido_faltante(self, hub_settings):
        # Sin 'exp' el decode debe fallar por require=['exp',...].
        token = jwt.encode(
            {"sub": "x", "iat": int(time.time()), "iss": "kapitalya-hub", "tipo": "access_token"},
            SECRET, algorithm="HS256",
        )
        with pytest.raises(AuthError):
            validar_token(token)

    def test_secret_no_configurado(self, settings):
        settings.HUB_JWT_SECRET = ""
        with pytest.raises(AuthError, match="HUB_JWT_SECRET"):
            validar_token(_make_token())


# ─────────────────────────────────────────────
# Middleware — open redirect en `next`
# ─────────────────────────────────────────────
class TestMiddlewareOpenRedirect:
    def _dispatch(self, next_url):
        rf = RequestFactory()
        token = _make_token(
            tipo="project_token", proyecto=PROYECTO_SLUG,
            email="a@b.co", nombre="A", rol="viewer", proyectos=[PROYECTO_SLUG],
        )
        request = rf.get("/", {"hub_token": token, "next": next_url})
        mw = HubAuthMiddleware(lambda r: r)
        return mw(request)

    def test_next_externo_es_neutralizado(self, hub_settings):
        """Una URL externa en `next` NO debe usarse como destino del redirect."""
        response = self._dispatch("https://evil.example.com/phish")
        assert response.status_code == 302
        assert response["Location"] == "/"

    def test_next_protocol_relative_neutralizado(self, hub_settings):
        response = self._dispatch("//evil.example.com/phish")
        assert response["Location"] == "/"

    def test_next_interno_se_respeta(self, hub_settings):
        response = self._dispatch("/dashboard/")
        assert response["Location"] == "/dashboard/"

    def test_project_token_de_otro_proyecto_rechazado(self, hub_settings):
        rf = RequestFactory()
        token = _make_token(tipo="project_token", proyecto="otro-proyecto")
        request = rf.get("/", {"hub_token": token})
        mw = HubAuthMiddleware(lambda r: r)
        response = mw(request)
        assert response.status_code == 302
        assert "proyecto_incorrecto" in response["Location"]
