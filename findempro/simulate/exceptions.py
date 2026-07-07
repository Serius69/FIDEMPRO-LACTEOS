"""
Excepciones de dominio para el módulo de simulación.

Jerarquía:
    SimulationError
    ├── InvalidModelError       — modelo mal configurado (ecuaciones, grafo)
    ├── InsufficientDataError   — datos históricos insuficientes para el análisis
    └── DistributionFitError    — no se pudo ajustar una distribución estadística
"""


class SimulationError(Exception):
    """Raíz de todas las excepciones de simulación."""


class InvalidModelError(SimulationError):
    """El modelo de simulación es inválido o incompleto."""


class InsufficientDataError(SimulationError):
    """No hay suficientes datos históricos para ejecutar la simulación."""


class DistributionFitError(SimulationError):
    """No se pudo ajustar una distribución estadística a los datos."""
