"""Inicio y callback del SSO del Hub, ligados a ESTE navegador.

`?hub_token=` se canjeaba en CUALQUIER ruta y sin nada que ligara el canje al
navegador que inició el login. Alguien con un token válido propio podía mandarle a
otra persona `https://app.kapitalya.com.bo/<lo que sea>?hub_token=<suyo>` y dejarla
operando dentro de la sesión del atacante (login CSRF / fijación de sesión).
`SameSite=Lax` no lo impide: una navegación GET de nivel superior sí manda la cookie.

Ahora el canje ocurre SOLO en `/hub/callback/`, exigiendo el `state` que este
navegador pidió en `/hub/login/`.
"""
from __future__ import annotations

import os
import time
from urllib.parse import urlencode

import jwt as _jwt
from django.conf import settings
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.http import url_has_allowed_host_and_scheme

from . import sso_state
from .middleware import PROYECTO_SLUG
from .tokens import AuthError, validar_token

STATE_COOKIE = "findempro_sso_state"


def _secreto() -> str:
    return getattr(settings, "HUB_JWT_SECRET", "") or os.environ.get("HUB_JWT_SECRET", "")


def _seguro() -> bool:
    return os.environ.get("DJANGO_DEBUG", "False").lower() not in ("true", "1")


def _redis_sso():
    """Cliente Redis para redención de state/jti. Sin él NO se emite sesión.

    Findempro corre con varios workers, así que "ya usé este state/jti" no puede
    vivir en memoria del proceso: dos workers emitirían dos sesiones con el mismo
    token. Se usa la DB 2 (la 1 es la de la app) para no competir con su churn.
    """
    import redis as _r

    url = (os.environ.get("REDIS_URL", "") or "redis://findempro_redis:6379/1")
    url = url.rsplit("/", 1)[0] + "/2"
    return _r.from_url(url, socket_timeout=2, socket_connect_timeout=2)


def _destino_seguro(request, destino: str) -> str:
    """Solo rutas de este host: un `next` externo convertiría un login legítimo en
    el trampolín de un phishing."""
    if destino and url_has_allowed_host_and_scheme(
        destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return destino
    return "/"


def _reiniciar():
    """Reinicia el flujo limpiando el state. Sin detalle del motivo."""
    resp = HttpResponseRedirect("/hub/login/")
    resp.delete_cookie(STATE_COOKIE, path="/")
    return resp


def hub_login(request):
    """GET /hub/login/ — arranca el SSO ligado a ESTE navegador.

    El Hub no puede poner una cookie en este dominio, así que el flujo tiene que
    empezar acá.
    """
    secreto = _secreto()
    if not secreto:
        return JsonResponse({"detail": "SSO sin configurar."}, status=503)

    hub_url = getattr(settings, "HUB_URL", "https://kapitalya.com.bo")
    state = sso_state.nuevo_state()
    destino = _destino_seguro(request, request.GET.get("next", "/"))

    resp = HttpResponseRedirect(
        f"{hub_url}/api/auth/sso/{PROYECTO_SLUG}/?{urlencode({'state': state})}"
    )
    resp.set_cookie(
        STATE_COOKIE,
        sso_state.firmar_sobre(state, secreto, next_path=destino),
        max_age=sso_state.STATE_TTL,
        httponly=True,
        secure=_seguro(),
        samesite="Lax",
        path="/",
    )
    return resp


def hub_callback(request):
    """GET /hub/callback/ — vuelta del Hub con el project_token y el `state`."""
    secreto = _secreto()
    if not secreto:
        return JsonResponse({"detail": "SSO sin configurar."}, status=503)

    hub_token = request.GET.get("hub_token", "")
    state = request.GET.get("state", "")
    if not hub_token or not state:
        return HttpResponseRedirect("/hub/login/")

    # 1. El state tiene que ser el nuestro, vigente, y coincidir por VALOR.
    try:
        esperado, destino = sso_state.abrir_sobre(request.COOKIES.get(STATE_COOKIE), secreto)
    except sso_state.StateError:
        return _reiniciar()
    if not sso_state.coincide(state, esperado):
        return _reiniciar()

    # 2. El token, ANTES de gastar el state. El project_token dura 5 min, así que
    #    llegar acá con uno vencido es corriente; si el state se consumiera primero,
    #    ese fallo normal dejaría al MISMO navegador sin poder reintentar (su
    #    siguiente intento se vería como replay). El state se gasta solo cuando de
    #    verdad se cambia por una sesión.
    try:
        payload = validar_token(hub_token, tipo_esperado="project_token")
    except AuthError as e:
        return JsonResponse({"detail": str(e)}, status=401)

    # 3. Audiencia: el HUB_JWT_SECRET es compartido por todo el ecosistema, así que
    #    un token emitido para otro proyecto tiene firma válida acá.
    if payload.get("proyecto") != PROYECTO_SLUG:
        return JsonResponse({"detail": "Token de otro proyecto."}, status=403)

    # 4. De un solo uso, atómico y compartido entre workers. Va antes del jti para
    #    que el state siga siendo el candado que liga el canje a ESTE navegador.
    try:
        if not sso_state.consumir_state(_redis_sso(), esperado):
            return _reiniciar()                       # replay
    except sso_state.RedencionNoVerificable:
        return JsonResponse({"detail": "No se pudo verificar el inicio de sesion."}, status=503)

    # 5. El mismo token no se canjea dos veces en FindemproAI.
    try:
        if not sso_state.redimir_jti(
            _redis_sso(), PROYECTO_SLUG, str(payload.get("jti") or ""), int(payload["exp"])
        ):
            return JsonResponse({"detail": "Token ya utilizado."}, status=401)
    except sso_state.RedencionNoVerificable:
        return JsonResponse({"detail": "No se pudo verificar el token."}, status=503)

    access_payload = {
        "sub": payload["sub"],
        "email": payload.get("email", ""),
        "nombre": payload.get("nombre", ""),
        "rol": payload.get("rol", "viewer"),
        "proyectos": payload.get("proyectos", []),
        "plan": payload.get("plan", "basico"),
        "tipo": "access_token",
        "iss": "kapitalya-hub",
        "iat": int(time.time()),
        "exp": int(time.time()) + 900,
    }
    resp = HttpResponseRedirect(_destino_seguro(request, destino))
    resp.delete_cookie(STATE_COOKIE, path="/")
    resp.set_cookie(
        "hub_access_token",
        _jwt.encode(access_payload, secreto, algorithm="HS256"),
        httponly=True,
        secure=_seguro(),
        samesite="Lax",
        max_age=900,
    )
    return resp
