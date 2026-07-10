"""
gpu_backend.py
==============
Abstracción de backend de arrays: **CuPy (GPU) con fallback automático a NumPy (CPU)**.

Objetivo
--------
Permitir que el motor Monte Carlo vectorizado corra en GPU cuando hay una
disponible y sea compatible, y caiga a NumPy de forma transparente y segura
cuando no la hay (p. ej. en el cluster K8s CPU-only). Nada en el resto del
proyecto necesita saber si está corriendo en CPU o GPU.

Selección de backend (variable de entorno ``FINDEMPRO_GPU``):
  · ``auto`` (default) — usa GPU si CuPy importa **y** un kernel de prueba compila.
  · ``on``            — fuerza GPU; si falla, cae a CPU y loguea una advertencia.
  · ``off``           — fuerza CPU (NumPy) siempre.

La detección se hace **una sola vez** (memoizada). El probe compila un kernel
mínimo, lo que en GPUs nuevas (p. ej. Blackwell/sm_120) valida que el NVRTC
disponible sea capaz de generar binario para el dispositivo — evitando el error
``CUDA_ERROR_NO_BINARY_FOR_GPU`` en tiempo de simulación.
"""

from __future__ import annotations

import builtins
import logging
import math
import os
from typing import Any, Callable, Dict, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ── Estado memoizado del backend ─────────────────────────────────────────────
_BACKEND: Any = None          # módulo de arrays elegido (cupy o numpy)
_ON_GPU: bool | None = None   # True si el backend activo es CuPy sobre GPU


def _probe_cupy() -> Tuple[Any, bool]:
    """
    Intenta habilitar CuPy y validar que puede ejecutar un kernel en la GPU.

    Devuelve ``(numpy, False)`` ante cualquier problema (import, driver, NVRTC
    incompatible con la arquitectura del dispositivo, sin GPU visible, etc.).
    """
    try:
        import cupy as cp  # type: ignore
    except Exception as exc:  # pragma: no cover - depende del entorno
        logger.info("GPU no disponible (CuPy no importable: %s). Usando NumPy.", exc)
        return np, False

    try:
        # Probe real: fuerza compilación+ejecución de un kernel elementwise.
        # Si el NVRTC no puede generar binario para esta GPU, esto lanza aquí
        # (una sola vez) en vez de a mitad de una simulación.
        a = cp.arange(8, dtype=cp.float64)
        b = cp.maximum(a * 2.0 + 1.0, 0.0)
        cp.cuda.Stream.null.synchronize()
        _ = float(b.sum())
        name = cp.cuda.runtime.getDeviceProperties(0)["name"].decode()
        logger.info("GPU habilitada para Monte Carlo: %s (CuPy %s).", name, cp.__version__)
        return cp, True
    except Exception as exc:  # pragma: no cover - depende del entorno
        logger.warning(
            "GPU detectada pero el kernel de prueba falló (%s). "
            "Cayendo a NumPy/CPU. En GPUs nuevas revisar que NVRTC sea >= 12.8.",
            exc,
        )
        return np, False


def _warmup(xp: Any) -> None:
    """
    Ejecuta una vez las operaciones elementwise usadas al evaluar ecuaciones.

    CuPy importa módulos de forma perezosa en la PRIMERA ejecución de cada tipo
    de kernel. Si esa primera ejecución ocurre dentro de un ``eval`` con
    ``__builtins__={}`` (namespace restringido del solver), el import lanza
    ``KeyError: '__import__'``. Precalentar aquí cachea esos imports en
    ``sys.modules`` para que el ``eval`` restringido posterior funcione.
    """
    try:
        a = xp.asarray([1.0, 2.0, 3.0])
        b = xp.asarray([4.0, 5.0, 6.0])
        for op in (a * b, a + b, a - b, a / b, xp.maximum(a, b), xp.minimum(a, b),
                   xp.power(a, 2.0), xp.abs(a), xp.round(a), xp.sqrt(a),
                   xp.log(a), xp.exp(a), xp.ceil(a), xp.floor(a),
                   # comparaciones + where: kernels usados por ecuaciones con
                   # condicionales (ternarios reescritos a where). Sin precalentar
                   # estos, su lazy-import caía dentro del eval restringido.
                   xp.where(a > b, a, b), (a > b), (a < b), (a >= b), (a == b)):
            float(op.sum())
    except Exception as exc:  # pragma: no cover
        logger.debug("warmup GPU parcial: %s", exc)


def _init_backend() -> None:
    global _BACKEND, _ON_GPU
    if _BACKEND is not None:
        return
    mode = os.environ.get("FINDEMPRO_GPU", "auto").strip().lower()
    if mode == "off":
        _BACKEND, _ON_GPU = np, False
        logger.info("FINDEMPRO_GPU=off → Monte Carlo en NumPy/CPU.")
        return
    xp, on_gpu = _probe_cupy()
    if mode == "on" and not on_gpu:
        logger.warning("FINDEMPRO_GPU=on pero la GPU no está utilizable; se usa CPU.")
    if on_gpu:
        _warmup(xp)
    _BACKEND, _ON_GPU = xp, on_gpu


def get_array_module() -> Any:
    """Devuelve el módulo de arrays activo (``cupy`` o ``numpy``)."""
    _init_backend()
    return _BACKEND


def on_gpu() -> bool:
    """True si el backend activo es CuPy corriendo sobre GPU."""
    _init_backend()
    return bool(_ON_GPU)


def backend_name() -> str:
    return "cupy/gpu" if on_gpu() else "numpy/cpu"


def asnumpy(arr: Any) -> np.ndarray:
    """Convierte un array del backend activo a ``numpy.ndarray`` en host."""
    if _ON_GPU:
        import cupy as cp  # type: ignore
        return cp.asnumpy(arr)
    return np.asarray(arr)


def make_generator(seed: int | None) -> Any:
    """RNG del backend activo. CuPy y NumPy comparten la API ``default_rng``."""
    xp = get_array_module()
    return xp.random.default_rng(seed)


def reset_backend_for_tests() -> None:
    """Fuerza re-detección del backend (solo para tests)."""
    global _BACKEND, _ON_GPU
    _BACKEND, _ON_GPU = None, None


# ── Namespace matemático seguro y vectorizado ────────────────────────────────
# El motor de ecuaciones escalar usa builtins (max/min/abs/round) y funciones de
# ``math`` que NO operan elementwise sobre arrays. Aquí construimos equivalentes
# que funcionan tanto con escalares como con arrays del backend activo, para que
# las MISMAS expresiones de ecuación evalúen correctamente en modo vectorizado.

def build_safe_namespace(xp: Any) -> Dict[str, Callable | float]:
    """
    Namespace para ``eval`` de expresiones de ecuación en modo vectorizado.

    Reemplaza builtins/funciones ``math`` no-vectorizables por sus versiones
    de ``xp`` (numpy/cupy), preservando la semántica del motor escalar:
      · ``max(a, b)`` → elementwise ``xp.maximum``  (2 args)
      · ``max(iterable)`` → ``xp.max``              (1 arg)
      · idem ``min``; ``abs``/``round``/``sqrt``/``log``/``exp``/``ceil``/``floor``.
    """

    def _vmax(*args: Any) -> Any:
        if len(args) == 1:
            return xp.max(xp.asarray(args[0]))
        out = args[0]
        for other in args[1:]:
            out = xp.maximum(out, other)
        return out

    def _vmin(*args: Any) -> Any:
        if len(args) == 1:
            return xp.min(xp.asarray(args[0]))
        out = args[0]
        for other in args[1:]:
            out = xp.minimum(out, other)
        return out

    def _vpow(a: Any, b: Any) -> Any:
        return xp.power(a, b)

    def _vsum(iterable: Any) -> Any:
        return xp.sum(xp.asarray(iterable))

    return {
        # CuPy importa submódulos de forma PEREZOSA en la 1ª ejecución de cada
        # tipo de kernel (comparaciones, where, etc.). Si esa importación ocurre
        # dentro de este ``eval`` restringido, el sandbox ``__builtins__: {}``
        # provoca ``KeyError: '__import__'`` → ``can_vectorize`` lo captura y
        # SIEMPRE cae al motor escalar (la GPU nunca se usaba en el pipeline real,
        # pese a on_gpu=True). Exponer solo ``__import__`` permite esos imports
        # internos de CuPy sin reintroducir el resto de builtins peligrosos. El
        # ``_warmup`` sigue reduciendo la latencia del primer eval, pero este
        # __import__ lo hace robusto ante cualquier kernel no precalentado.
        "__builtins__": {"__import__": builtins.__import__},
        "max": _vmax,
        "min": _vmin,
        "abs": xp.abs,
        "round": xp.round,
        "pow": _vpow,
        "sum": _vsum,
        "sqrt": xp.sqrt,
        "log": xp.log,
        "exp": xp.exp,
        "ceil": xp.ceil,
        "floor": xp.floor,
        # where(cond, a, b): equivalente vectorizado del ternario escalar
        # ``a if cond else b`` (ver _rewrite_ternaries_to_where en vectorized_engine).
        # Element-wise y con broadcasting → permite que ecuaciones con `if/else`
        # pasen can_vectorize y corran en GPU en vez de caer al motor escalar.
        "where": xp.where,
        "pi": math.pi,
    }
