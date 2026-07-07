"""
hub_auth.middleware — Kapitalya Hub SSO middleware (Django edition).
Handles ?hub_token= SSO redirects and injects hub_user into request.
"""
import os
from django.http import HttpResponseRedirect
from django.utils.http import url_has_allowed_host_and_scheme
from .tokens import validar_token, AuthError

PROYECTO_SLUG = "findemproai"


class HubAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        hub_token = request.GET.get("hub_token")
        if hub_token:
            return self._manejar_sso_redirect(request, hub_token)

        cookie = request.COOKIES.get("hub_access_token")
        if cookie:
            try:
                payload = validar_token(cookie, tipo_esperado="access_token")
                request.hub_user = payload.get("sub")
                request.hub_rol = payload.get("rol", "viewer")
                request.hub_proyectos = payload.get("proyectos", [])
            except AuthError:
                pass

        return self.get_response(request)

    def _manejar_sso_redirect(self, request, project_token):
        hub_url = self._hub_url()
        try:
            payload = validar_token(project_token, tipo_esperado="project_token")
        except AuthError:
            return HttpResponseRedirect(f"{hub_url}/login?error=token_invalido")

        if payload.get("proyecto") != PROYECTO_SLUG:
            return HttpResponseRedirect(f"{hub_url}/login?error=proyecto_incorrecto")

        import jwt as _jwt
        import time

        secret = os.environ.get("HUB_JWT_SECRET", "")
        try:
            from django.conf import settings as s
            secret = getattr(s, "HUB_JWT_SECRET", secret)
        except Exception:
            pass

        access_payload = {
            "sub": payload["sub"],
            "email": payload.get("email", ""),
            "nombre": payload.get("nombre", ""),
            "rol": payload.get("rol", "viewer"),
            "proyectos": payload.get("proyectos", []),
            "tipo": "access_token",
            "iss": "kapitalya-hub",
            "iat": int(time.time()),
            "exp": int(time.time()) + 900,
        }
        access_token = _jwt.encode(access_payload, secret, algorithm="HS256")

        # SEGURIDAD: validar 'next' contra open redirect. Solo se permiten rutas
        # internas (mismo host); cualquier URL externa cae al home "/".
        next_url = request.GET.get("next", "/")
        if not url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            next_url = "/"
        response = HttpResponseRedirect(next_url)
        response.set_cookie(
            "hub_access_token",
            access_token,
            httponly=True,
            secure=not os.environ.get("DJANGO_DEBUG", "False").lower() in ("true", "1"),
            samesite="Lax",
            max_age=900,
        )
        return response

    def _hub_url(self):
        try:
            from django.conf import settings as s
            return getattr(s, "HUB_URL", "https://kapitalya.com.bo")
        except Exception:
            return os.environ.get("HUB_URL", "https://kapitalya.com.bo")
