"""
simulate/core — Núcleo del motor de simulación FINDEMPRO AI
===========================================================

Módulos:
  discrete_engine  : motor de eventos discretos genérico (cualquier sector)
  monte_carlo      : generación de escenarios probabilísticos
  decision_engine  : métricas de riesgo + recomendaciones de decisión

Flujo estándar:
  1. MonteCarloConfig  →  ScenarioGenerator  →  List[OperationScenario]
  2. CompanyConfig + List[OperationScenario]  →  DiscreteEventEngine  →  List[PeriodResult]
  3. List[PeriodResult]  →  DecisionEngine  →  DecisionReport
"""

from simulate.core.discrete_engine import (
    CompanyConfig,
    OperationScenario,
    PeriodResult,
    DiscreteEventEngine,
    simular_operacion,
    build_config_from_profile,
)

from simulate.core.monte_carlo import (
    MonteCarloConfig,
    AggregatedResult,
    ScenarioGenerator,
    DistributionFactory,
    aggregate_results,
    generate_scenarios,
)

from simulate.core.decision_engine import (
    RiskMetrics,
    Recommendation,
    DecisionReport,
    DecisionEngine,
    analizar_decision,
)

__all__ = [
    # discrete_engine
    'CompanyConfig',
    'OperationScenario',
    'PeriodResult',
    'DiscreteEventEngine',
    'simular_operacion',
    'build_config_from_profile',
    # monte_carlo
    'MonteCarloConfig',
    'AggregatedResult',
    'ScenarioGenerator',
    'DistributionFactory',
    'aggregate_results',
    'generate_scenarios',
    # decision_engine
    'RiskMetrics',
    'Recommendation',
    'DecisionReport',
    'DecisionEngine',
    'analizar_decision',
]
