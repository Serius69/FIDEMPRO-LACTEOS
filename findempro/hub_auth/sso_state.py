"""Primitivas del SSO ligado a navegador: `state` y redención de `jti`.

Copia adaptada del patrón del ecosistema (`hub_auth/` se copia por proyecto; los
cambios no se propagan solos). La diferencia con la del gateway de fraude es que acá
el sobre además transporta el `next`: FindemproAI es una app Django con rutas, y queremos volver a
la página que la persona pedía sin hacer pasar esa ruta por el Hub.

Dos propiedades distintas, que conviene no mezclar:

* **state** liga el callback al navegador que INICIÓ el login. Es lo que cierra el
  login-CSRF / fijación de sesión. No alcanza con que la cookie exista: hay que
  comparar el valor, o cualquier cookie sirve para cualquier token.

* **jti** evita que el MISMO project_token se canjee dos veces en FindemproAI. Es otra
  cosa: un token fresco del atacante tiene un jti nuevo, así que no sustituye al
  state.

Ambas fallan CERRADO. Si no podemos probar que un state/jti no se usaron, no se
emite sesión: no poder verificar no es lo mismo que verificar.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time

STATE_TTL = 600          # ida y vuelta al Hub, no la sesión
CLOCK_SKEW = 30
_JTI_TTL_MAX = 3600


class StateError(Exception):
    """El state no se pudo validar. El motivo NO se le cuenta al navegador."""


class RedencionNoVerificable(Exception):
    """No se pudo consultar el almacén de redención → se deniega."""


def _clave(secreto: str) -> bytes:
    """Subclave dedicada: una firma de state nunca puede confundirse con un JWT."""
    return hmac.new(secreto.encode(), b'sso-state-v1', hashlib.sha256).digest()


def nuevo_state() -> str:
    return secrets.token_urlsafe(32)          # ~256 bits


def _b64(s: str) -> str:
    return base64.urlsafe_b64encode(s.encode()).decode().rstrip('=')


def _deb64(s: str) -> str:
    return base64.urlsafe_b64decode(s + '=' * (-len(s) % 4)).decode()


def firmar_sobre(state: str, secreto: str, next_path: str = '/', ahora: float | None = None) -> str:
    """Sobre para la cookie: `state|expira|next_b64|firma`.

    Va firmado para que el navegador no se fabrique un state a medida y para que la
    expiración no dependa del `Max-Age`, que lo controla el cliente.
    """
    expira = int(ahora if ahora is not None else time.time()) + STATE_TTL
    cuerpo = f'{state}|{expira}|{_b64(next_path)}'
    firma = hmac.new(_clave(secreto), cuerpo.encode(), hashlib.sha256).hexdigest()
    return f'{cuerpo}|{firma}'


def abrir_sobre(sobre: str | None, secreto: str, ahora: float | None = None) -> tuple[str, str]:
    """Devuelve `(state, next)` del sobre, o levanta StateError."""
    if not sobre or not secreto:
        raise StateError('sin sobre')
    partes = sobre.split('|')
    if len(partes) != 4:
        raise StateError('sobre malformado')
    state, expira_raw, next_b64, firma = partes
    cuerpo = f'{state}|{expira_raw}|{next_b64}'
    esperada = hmac.new(_clave(secreto), cuerpo.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(firma, esperada):
        raise StateError('firma invalida')
    try:
        expira = int(expira_raw)
    except ValueError:
        raise StateError('expiracion invalida') from None
    if expira < int(ahora if ahora is not None else time.time()):
        raise StateError('state expirado')
    try:
        destino = _deb64(next_b64)
    except Exception:  # noqa: BLE001
        destino = '/'
    return state, destino


def coincide(recibido: str | None, esperado: str) -> bool:
    """Comparación por VALOR y en tiempo constante."""
    if not recibido:
        return False
    return hmac.compare_digest(recibido, esperado)


def _hash(valor: str) -> str:
    """El almacén guarda un hash, no el state ni el jti en claro."""
    return base64.urlsafe_b64encode(hashlib.sha256(valor.encode()).digest()).decode().rstrip('=')


def consumir_state(redis, state: str) -> bool:
    """Marca el state como usado. `True` solo la PRIMERA vez (SET NX es atómico)."""
    try:
        ok = redis.set(f'sso:state:{_hash(state)}', b'1', nx=True, ex=STATE_TTL + CLOCK_SKEW)
    except Exception as exc:  # noqa: BLE001
        raise RedencionNoVerificable(str(exc)) from exc
    return bool(ok)


def redimir_jti(redis, audiencia: str, jti: str, exp: int, ahora: float | None = None) -> bool:
    """Canjea el jti UNA vez para esta audiencia.

    El TTL sale de lo que le queda al token, nunca de un valor elegido por quien lo
    manda: un `exp` enorme dejaría basura eterna en Redis.
    """
    if not jti:
        return False
    ahora = int(ahora if ahora is not None else time.time())
    ttl = max(1, min(int(exp) - ahora + CLOCK_SKEW, _JTI_TTL_MAX))
    try:
        ok = redis.set(f'sso:jti:{audiencia}:{_hash(jti)}', b'1', nx=True, ex=ttl)
    except Exception as exc:  # noqa: BLE001
        raise RedencionNoVerificable(str(exc)) from exc
    return bool(ok)
