"""
hub_auth.tokens — Kapitalya Hub JWT validation (Django edition).
Validates tokens issued by kapitalya-hub. Read-only: never issues tokens.
"""
import os
from typing import Any

_ALGORITMO = "HS256"
_TIPOS_VALIDOS = {"access_token", "project_token"}


class AuthError(Exception):
    pass


def _get_secret() -> str:
    try:
        from django.conf import settings
        return getattr(settings, "HUB_JWT_SECRET", "") or os.environ.get("HUB_JWT_SECRET", "")
    except Exception:
        return os.environ.get("HUB_JWT_SECRET", "")


def validar_token(token: str, tipo_esperado: str | None = None) -> dict[str, Any]:
    try:
        import jwt
    except ImportError:
        raise AuthError("PyJWT not installed. Add PyJWT>=2.8.0 to requirements.")

    secret = _get_secret()
    if not secret:
        raise AuthError("HUB_JWT_SECRET no configurado.")

    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[_ALGORITMO],
            options={"require": ["exp", "iat", "sub", "tipo"]},
        )
    except jwt.ExpiredSignatureError:
        raise AuthError("Token expirado.")
    except jwt.InvalidTokenError as e:
        raise AuthError(f"Token invalido: {e}")

    if payload.get("iss") != "kapitalya-hub":
        raise AuthError("Emisor de token incorrecto.")

    tipo = payload.get("tipo")
    if tipo not in _TIPOS_VALIDOS:
        raise AuthError(f"Tipo de token desconocido: {tipo}")

    if tipo_esperado and tipo != tipo_esperado:
        raise AuthError(f"Se esperaba {tipo_esperado}, se recibio {tipo}.")

    return payload
