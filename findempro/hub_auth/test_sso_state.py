"""El callback SSO no puede aceptar un token que este navegador no pidió.

Incidente que previene: `?hub_token=` se canjeaba en CUALQUIER ruta servida por
Django (incluidas `/sitemap.xml` y `/health/live/`) sin nada que ligara el canje al
navegador que inició el login. Alguien con un token válido propio podía mandarle a
otra persona `https://insights…/<lo que sea>?hub_token=<suyo>` y dejarla operando
dentro de la sesión del atacante. `SameSite=Lax` no lo impide: una navegación GET de
nivel superior sí manda la cookie.

Segundo invariante: el `state` se compara por VALOR. Un chequeo de "la cookie existe"
dejaría que cualquier cookie sirviera para cualquier token.
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest

_SECRET = "test-hub-secret-0123456789abcdef0123456789"
_SLUG = "findemproai"
UTC = timezone.utc


class FakeRedis:
    """Lo justo de Redis para `SET NX EX`.

    `romper_prefijo` tira abajo SOLO las claves de state o SOLO las de jti: con
    Redis entero caído basta que una de las dos deniegue para ver un 503, y la otra
    podría estar fallando ABIERTA sin que ningún test lo note.
    """

    def __init__(self, roto=False, romper_prefijo=None):
        self.datos, self.roto, self.romper_prefijo = {}, roto, romper_prefijo

    def set(self, clave, valor, nx=False, ex=None):
        if self.roto or (self.romper_prefijo and clave.startswith(self.romper_prefijo)):
            raise ConnectionError("redis caido")
        if nx and clave in self.datos:
            return None
        self.datos[clave] = valor
        return True


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _secreto_del_hub(settings):
    settings.HUB_JWT_SECRET = _SECRET


@pytest.fixture()
def redis(monkeypatch):
    from hub_auth import views

    fake = FakeRedis()
    monkeypatch.setattr(views, "_redis_sso", lambda: fake)
    return fake


def _token(proyecto=_SLUG, tipo="project_token", jti=None, ttl=300):
    now = datetime.now(UTC)
    return jwt.encode(
        {"jti": jti or str(uuid.uuid4()), "sub": "42", "iss": "kapitalya-hub",
         "tipo": tipo, "proyecto": proyecto, "rol": "superadmin",
         "email": "sso@kapitalya.bo", "proyectos": [_SLUG],
         "iat": now, "exp": now + timedelta(seconds=ttl)},
        _SECRET, algorithm="HS256",
    )


def _iniciar(client, next_path=None):
    url = "/hub/login/" + (f"?next={next_path}" if next_path else "")
    r = client.get(url)
    assert r.status_code == 302
    assert f"/api/auth/sso/{_SLUG}/" in r["Location"]
    return r["Location"].split("state=")[1].split("&")[0]


def _emite_sesion(resp) -> bool:
    c = resp.cookies.get("hub_access_token")
    return bool(c and c.value)


# --- el caso feliz primero: si no, los "no emite sesión" pasan por accidente ---


def test_flujo_legitimo_emite_sesion(client, redis):
    state = _iniciar(client)
    r = client.get(f"/hub/callback/?hub_token={_token()}&state={state}")
    assert _emite_sesion(r)
    assert r.status_code == 302


def test_next_interno_se_respeta(client, redis):
    state = _iniciar(client, next_path="/dashboards/")
    r = client.get(f"/hub/callback/?hub_token={_token()}&state={state}")
    assert r["Location"] == "/dashboards/"


def test_next_externo_en_un_sobre_VALIDO_no_saca_del_sitio(client, redis):
    """Segunda capa: aunque el sobre venga bien firmado con un `next` externo, el
    callback lo revalida antes de redirigir."""
    from hub_auth import sso_state

    state = sso_state.nuevo_state()
    client.cookies["findempro_sso_state"] = sso_state.firmar_sobre(
        state, _SECRET, next_path="https://evil.example"
    )
    r = client.get(f"/hub/callback/?hub_token={_token()}&state={state}")
    assert _emite_sesion(r)
    assert r["Location"] == "/"


# --- state ---------------------------------------------------------------------


def test_sin_state_en_la_url_no_emite_sesion(client, redis):
    _iniciar(client)
    assert not _emite_sesion(client.get(f"/hub/callback/?hub_token={_token()}"))


def test_sin_cookie_de_inicio_no_emite_sesion(client, redis):
    """El navegador de la víctima nunca pasó por /hub/login/: es el ataque exacto."""
    assert not _emite_sesion(client.get(f"/hub/callback/?hub_token={_token()}&state=loquesea"))


def test_state_equivocado_no_emite_sesion(client, redis):
    """Mata la variante 'la cookie existe, adelante'."""
    from hub_auth import sso_state

    _iniciar(client)
    otro = sso_state.nuevo_state()
    assert not _emite_sesion(client.get(f"/hub/callback/?hub_token={_token()}&state={otro}"))


def test_state_vencido_no_emite_sesion(client, redis):
    """Se envejece el SOBRE, no el reloj global: mover `time.time` vencería también
    el JWT y el test pasaría por el motivo equivocado."""
    from hub_auth import sso_state

    state = sso_state.nuevo_state()
    viejo = time.time() - sso_state.STATE_TTL - 60
    client.cookies["findempro_sso_state"] = sso_state.firmar_sobre(state, _SECRET, "/", ahora=viejo)
    assert not _emite_sesion(client.get(f"/hub/callback/?hub_token={_token()}&state={state}"))


def test_sobre_falsificado_no_emite_sesion(client, redis):
    from hub_auth import sso_state

    state = sso_state.nuevo_state()
    client.cookies["findempro_sso_state"] = f"{state}|{int(time.time()) + 600}|Lw|{'00' * 32}"
    assert not _emite_sesion(client.get(f"/hub/callback/?hub_token={_token()}&state={state}"))


def test_state_es_de_un_solo_uso(client, redis):
    from hub_auth import sso_state

    state = _iniciar(client)
    assert _emite_sesion(client.get(f"/hub/callback/?hub_token={_token()}&state={state}"))
    client.cookies["findempro_sso_state"] = sso_state.firmar_sobre(state, _SECRET, "/")
    assert not _emite_sesion(client.get(f"/hub/callback/?hub_token={_token()}&state={state}"))


@pytest.mark.parametrize(
    "token_malo",
    [
        pytest.param("esto.no.es-un-jwt", id="jwt-malformado"),
        pytest.param(_token(proyecto="xgol"), id="otro-proyecto"),
        pytest.param(_token(tipo="access_token"), id="tipo-equivocado"),
    ],
)
def test_token_rechazado_no_quema_el_state_del_mismo_navegador(client, redis, token_malo):
    """Un token que no sirve NO puede dejar al navegador sin poder reintentar.

    El project_token vive 5 minutos: llegar al callback con uno vencido, de otro
    proyecto o directamente malformado es rutina, no un ataque. Si el state se
    consumiera antes de mirar el token, ese fallo corriente lo quemaría y el
    SIGUIENTE intento del MISMO navegador (mismo state en la cookie) se leería como
    replay: el login queda trabado hasta que expire la cookie. El state es el
    candado que liga el canje a ESTE navegador; solo se gasta cuando de verdad se
    cambia por una sesión.
    """
    state = _iniciar(client)

    r_malo = client.get(f"/hub/callback/?hub_token={token_malo}&state={state}")
    assert not _emite_sesion(r_malo)

    # Mismo navegador, mismo state, ahora con un token bueno.
    r_bueno = client.get(f"/hub/callback/?hub_token={_token()}&state={state}")
    assert _emite_sesion(r_bueno)


# --- audiencia y replay ---------------------------------------------------------


def test_token_de_otro_proyecto_no_emite_sesion(client, redis):
    """El HUB_JWT_SECRET es del ecosistema entero: la firma sola no alcanza."""
    state = _iniciar(client)
    r = client.get(f"/hub/callback/?hub_token={_token(proyecto='xgol')}&state={state}")
    assert not _emite_sesion(r)
    assert r.status_code == 403


def test_mismo_jti_no_se_canjea_dos_veces(client, redis):
    tok = _token(jti="repetido")
    s1 = _iniciar(client)
    assert _emite_sesion(client.get(f"/hub/callback/?hub_token={tok}&state={s1}"))
    client.cookies.clear()
    s2 = _iniciar(client)
    r = client.get(f"/hub/callback/?hub_token={tok}&state={s2}")
    assert not _emite_sesion(r)
    assert r.status_code == 401


def test_tipo_de_token_incorrecto_no_emite_sesion(client, redis):
    state = _iniciar(client)
    assert not _emite_sesion(
        client.get(f"/hub/callback/?hub_token={_token(tipo='access')}&state={state}"))


# --- fail-closed -----------------------------------------------------------------


@pytest.mark.parametrize("prefijo", ["sso:state:", "sso:jti:"])
def test_cada_almacen_falla_por_separado_cerrado(client, monkeypatch, prefijo):
    from hub_auth import views

    monkeypatch.setattr(views, "_redis_sso", lambda: FakeRedis(romper_prefijo=prefijo))
    state = _iniciar(client)
    r = client.get(f"/hub/callback/?hub_token={_token()}&state={state}")
    assert not _emite_sesion(r)
    assert r.status_code == 503


# --- retiro del canje legado en rutas arbitrarias ---------------------------------


@pytest.mark.parametrize("ruta", ["/", "/dashboards/", "/product/"])
def test_token_en_ruta_arbitraria_ya_no_crea_sesion(client, redis, ruta):
    """La forma exacta del ataque, y de paso: `/sitemap.xml?hub_token=` ya no se va
    redirigido al Hub."""
    r = client.get(f"{ruta}?hub_token={_token()}")
    assert not _emite_sesion(r)
    assert r.status_code == 302
    assert r["Location"].startswith("/hub/login/")
