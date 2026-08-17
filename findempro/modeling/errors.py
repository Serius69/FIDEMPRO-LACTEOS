"""Safe, user-facing error envelopes for asynchronous model runs."""

from __future__ import annotations

import json
from typing import Any

from .engine import ModelCompileError
from .safe_expression import ExpressionError


def simulation_error(exc: Exception) -> dict[str, Any]:
    """Return actionable information without exposing internals or tracebacks."""
    if isinstance(exc, ModelCompileError) and exc.args and isinstance(exc.args[0], dict):
        validation = exc.args[0]
        errors = validation.get("errors", [])
        first = errors[0] if errors else {}
        return {
            "code": "invalid_model",
            "where": first.get("path", "model"),
            "message": "El modelo no puede ejecutarse porque no supera la validación.",
            "how_to_fix": "Corrige los errores de validación y crea una nueva versión del modelo.",
            "details": {"errors": errors[:20]},
        }
    if isinstance(exc, ExpressionError):
        return {
            "code": "invalid_expression",
            "where": "equation",
            "message": "Una ecuación del modelo no pudo evaluarse.",
            "how_to_fix": "Revisa nombres, unidades, sintaxis y divisiones por cero de la fórmula.",
        }
    if isinstance(exc, ModelCompileError):
        return {
            "code": "model_compile_failed",
            "where": "model_compiler",
            "message": "El modelo no pudo compilarse para la simulación.",
            "how_to_fix": "Revisa la configuración del modelo y vuelve a validarlo.",
        }
    return {
        "code": "simulation_failed",
        "where": "simulation_engine",
        "message": "La simulación no pudo completarse.",
        "how_to_fix": "Revisa la configuración y los datos del modelo; si persiste, solicita soporte.",
    }


def encode_error(detail: dict[str, Any]) -> str:
    return json.dumps(detail, ensure_ascii=False, sort_keys=True)


def decode_error(raw: str | None) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        return {"code": "simulation_failed", "where": "simulation_engine", "message": "La simulación no pudo completarse.", "how_to_fix": "Revisa la configuración del modelo y vuelve a intentarlo."}
    return value if isinstance(value, dict) else None
