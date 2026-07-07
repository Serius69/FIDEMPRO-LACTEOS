"""
api_v1_views.py
===============
API REST v1 — Motor de decisiones financieras genérico para PyMEs.

Endpoints:
  POST /api/v1/simulate/         — Simulación Monte Carlo completa
  POST /api/v1/forecast/         — Proyección de demanda
  POST /api/v1/risk-analysis/    — Análisis de riesgo financiero
  POST /api/v1/scenarios/        — Escenarios financieros (pesimista/base/optimista)
  GET  /api/v1/company-profile/<id>/    — Perfil de configuración por empresa
  PUT  /api/v1/company-profile/<id>/    — Actualizar perfil de empresa
"""

import logging
from typing import Any, Dict

import numpy as np
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from findempro.throttles import SimulateThrottle

from business.models import Business, CompanyProfile
from simulate.services.simulation_engine import MonteCarloEngine, SimulationConfig
from simulate.services.demand_model import DemandModelService
from simulate.services.financial_analysis import FinancialAnalysisEngine

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Helpers de validación
# ─────────────────────────────────────────────

def _require_fields(data: Dict, fields: list) -> tuple[bool, str]:
    """Valida que los campos requeridos estén presentes y sean numéricos válidos."""
    for f in fields:
        if f not in data:
            return False, f"Campo requerido faltante: '{f}'"
        try:
            val = float(data[f])
            if not np.isfinite(val):
                return False, f"El campo '{f}' debe ser un número finito."
        except (TypeError, ValueError):
            return False, f"El campo '{f}' debe ser numérico."
    return True, ""


def _get_business(business_id: int, user) -> tuple:
    """Retorna (business, error_response) — error_response es None si OK."""
    try:
        business = Business.objects.get(pk=business_id, fk_user=user, is_active=True)
        return business, None
    except Business.DoesNotExist:
        return None, Response(
            {"error": "Negocio no encontrado o sin permisos de acceso."},
            status=status.HTTP_404_NOT_FOUND,
        )


def _clamp(value, min_val, max_val, default):
    """Retorna value entre [min_val, max_val] o default si no es válido."""
    try:
        v = float(value)
        return max(min_val, min(max_val, v))
    except (TypeError, ValueError):
        return default


# ─────────────────────────────────────────────
# POST /api/v1/simulate/
# ─────────────────────────────────────────────

class SimulateAPIView(APIView):
    """
    Ejecuta una simulación Monte Carlo completa.
    Rate limit: 20 simulaciones/hora (TensorFlow inference + Monte Carlo costosos).

    Body (JSON):
        business_id        int     — ID del negocio (opcional, para usar CompanyProfile)
        demand_mean        float   — Media de demanda histórica
        demand_std         float   — Desviación estándar de demanda
        unit_price         float   — Precio unitario de venta
        unit_cost          float   — Costo variable unitario
        fixed_costs        float   — Costos fijos totales
        distribution_type  str     — normal | lognormal | gamma | uniform | exponential
        n_iterations       int     — Iteraciones Monte Carlo (1000-100000, def: 10000)
        time_periods       int     — Períodos a simular (def: 30)
        confidence_level   float   — Nivel de confianza (0.80-0.99, def: 0.95)
        random_seed        int     — Semilla aleatoria (opcional)
        seasonality_factors list   — 12 factores mensuales (opcional)
        industry_sector    str     — Sector de la empresa (para defaults)

    Returns:
        {demand, revenue, profit, risk, scenarios, time_series, metadata}
    """

    throttle_classes = [SimulateThrottle]
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        data = request.data
        required = ['demand_mean', 'unit_price', 'unit_cost', 'fixed_costs']
        ok, err = _require_fields(data, required)
        if not ok:
            return Response({"error": err}, status=status.HTTP_400_BAD_REQUEST)

        # Cargar CompanyProfile si se provee business_id
        profile = None
        if 'business_id' in data:
            business, err_resp = _get_business(int(data['business_id']), request.user)
            if err_resp:
                return err_resp
            profile = CompanyProfile.get_or_create_for_business(business)

        # Parámetros con fallback a CompanyProfile o defaults
        demand_mean = float(data['demand_mean'])
        demand_std = float(data.get('demand_std', demand_mean * 0.15))
        n_iter = int(_clamp(data.get('n_iterations', 10000), 1000, 100000, 10000))
        time_periods = int(_clamp(data.get('time_periods', 30), 1, 365, 30))
        confidence = _clamp(
            data.get('confidence_level', profile.confidence_level if profile else 0.95),
            0.80, 0.99, 0.95,
        )
        dist = data.get(
            'distribution_type',
            profile.distribution_preference if profile and profile.distribution_preference != 'auto' else 'normal'
        )
        seed = data.get('random_seed', None)
        if seed is not None:
            seed = int(seed)

        seasonality = data.get('seasonality_factors', profile.get_seasonality_factors() if profile else [1.0] * 12)
        if not isinstance(seasonality, list) or len(seasonality) != 12:
            seasonality = [1.0] * 12

        config = SimulationConfig(
            n_iterations=n_iter,
            confidence_level=confidence,
            time_periods=time_periods,
            random_seed=seed,
            distribution_type=dist,
            demand_mean=demand_mean,
            demand_std=demand_std,
            unit_price=float(data['unit_price']),
            unit_cost=float(data['unit_cost']),
            fixed_costs=float(data['fixed_costs']),
            seasonality_factors=seasonality,
        )

        try:
            engine = MonteCarloEngine(config)
            result = engine.to_dict()
            result['_profile_used'] = bool(profile)
            result['_industry_sector'] = data.get('industry_sector', profile.fk_business.industry_sector if profile else 'other')
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("Error en SimulateAPIView")
            return Response({"error": "Error interno en la simulación."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────
# POST /api/v1/forecast/
# ─────────────────────────────────────────────

class ForecastAPIView(APIView):
    """
    Proyecta la demanda futura a partir de datos históricos.

    Body (JSON):
        historical_data    list    — Lista de valores históricos de demanda (mínimo 5)
        periods            int     — Períodos a proyectar (def: 30)
        method             str     — linear | moving_average | exponential_smoothing | auto
        confidence_level   float   — Nivel de confianza (def: 0.95)
        seasonality_period int     — Período de estacionalidad conocido (opcional)
        include_analysis   bool    — Si retornar análisis estadístico completo (def: false)

    Returns:
        {forecast, analysis (opcional), simulation_params}
    """

    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        data = request.data

        if 'historical_data' not in data:
            return Response({"error": "Campo requerido: 'historical_data'"}, status=status.HTTP_400_BAD_REQUEST)

        historical = data['historical_data']
        if not isinstance(historical, list) or len(historical) < 5:
            return Response(
                {"error": "Se requieren al menos 5 puntos de datos históricos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            historical_arr = [float(v) for v in historical]
        except (TypeError, ValueError):
            return Response({"error": "Todos los valores de 'historical_data' deben ser numéricos."}, status=status.HTTP_400_BAD_REQUEST)

        periods = int(_clamp(data.get('periods', 30), 1, 365, 30))
        method = data.get('method', 'auto')
        confidence = _clamp(data.get('confidence_level', 0.95), 0.80, 0.99, 0.95)
        seasonality_period = data.get('seasonality_period', None)
        if seasonality_period:
            seasonality_period = int(seasonality_period)
        include_analysis = str(data.get('include_analysis', 'false')).lower() in ('true', '1', 'yes')

        try:
            service = DemandModelService(
                historical_data=historical_arr,
                confidence_level=confidence,
                seasonality_period=seasonality_period,
            )

            forecast = service.forecast(periods=periods, method=method)
            sim_params = service.to_simulation_params()

            response_data: Dict[str, Any] = {
                'forecast': {
                    'periods': forecast.periods,
                    'values': forecast.forecasted_values,
                    'ci_lower': forecast.ci_lower,
                    'ci_upper': forecast.ci_upper,
                    'method_used': forecast.method_used,
                    'confidence_level': forecast.confidence_level,
                    'mape': forecast.mape,
                },
                'simulation_params': sim_params,
            }

            if include_analysis:
                analysis = service.analyze(forecast_periods=periods)
                response_data['analysis'] = {
                    'descriptive': {
                        'mean': analysis.mean,
                        'std': analysis.std,
                        'median': analysis.median,
                        'min': analysis.min,
                        'max': analysis.max,
                        'cv': analysis.cv,
                        'skewness': analysis.skewness,
                        'kurtosis': analysis.kurtosis,
                    },
                    'distribution': {
                        'best_fit': analysis.best_distribution,
                        'params': analysis.distribution_params,
                        'ks_statistic': analysis.goodness_of_fit_ks,
                        'ks_pvalue': analysis.goodness_of_fit_pvalue,
                    },
                    'trend': {
                        'direction': analysis.trend_direction,
                        'slope': analysis.trend_slope,
                        'r2': analysis.trend_r2,
                    },
                    'seasonality': {
                        'has_seasonality': analysis.has_seasonality,
                        'period': analysis.seasonality_period,
                        'strength': analysis.seasonality_strength,
                    },
                    'alerts': {
                        'volatility_alert': analysis.volatility_alert,
                        'outliers_count': analysis.outliers_count,
                    },
                }

            return Response(response_data, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("Error en ForecastAPIView")
            return Response({"error": "Error interno en la proyección."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────
# POST /api/v1/risk-analysis/
# ─────────────────────────────────────────────

class RiskAnalysisAPIView(APIView):
    """
    Análisis de riesgo financiero completo.
    Combina simulación Monte Carlo + análisis financiero para generar
    métricas de riesgo y recomendaciones automáticas.

    Body (JSON):
        revenue            float   — Ingresos totales actuales
        variable_costs     float   — Costos variables totales
        fixed_costs        float   — Costos fijos totales
        demand_mean        float   — Demanda media
        demand_std         float   — Desviación estándar de demanda
        unit_price         float   — Precio unitario
        industry_sector    str     — Sector (agro/production/retail/services/manufacturing/other)
        business_id        int     — ID negocio para usar CompanyProfile (opcional)
        n_iterations       int     — Iteraciones Monte Carlo (def: 10000)
        confidence_level   float   — Nivel de confianza (def: 0.95)

    Returns:
        {metrics, risk, recommendations, scenarios, summary, score_overall}
    """

    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        data = request.data
        required = ['revenue', 'variable_costs', 'fixed_costs', 'demand_mean']
        ok, err = _require_fields(data, required)
        if not ok:
            return Response({"error": err}, status=status.HTTP_400_BAD_REQUEST)

        # Cargar perfil de empresa si se provee
        profile = None
        industry_sector = data.get('industry_sector', 'other')
        if 'business_id' in data:
            business, err_resp = _get_business(int(data['business_id']), request.user)
            if err_resp:
                return err_resp
            profile = CompanyProfile.get_or_create_for_business(business)
            industry_sector = business.industry_sector

        revenue = float(data['revenue'])
        variable_costs = float(data['variable_costs'])
        fixed_costs = float(data['fixed_costs'])
        demand_mean = float(data['demand_mean'])
        demand_std = float(data.get('demand_std', demand_mean * 0.15))
        unit_price = float(data.get('unit_price', revenue / max(demand_mean, 1)))
        unit_cost = float(data.get('unit_cost', variable_costs / max(demand_mean, 1)))
        n_iter = int(_clamp(data.get('n_iterations', 10000), 1000, 100000, 10000))
        confidence = _clamp(
            data.get('confidence_level', profile.confidence_level if profile else 0.95),
            0.80, 0.99, 0.95,
        )

        try:
            # Simulación Monte Carlo para obtener distribución de ganancias
            config = SimulationConfig(
                n_iterations=n_iter,
                confidence_level=confidence,
                demand_mean=demand_mean,
                demand_std=demand_std,
                unit_price=unit_price,
                unit_cost=unit_cost,
                fixed_costs=fixed_costs,
            )
            mc_engine = MonteCarloEngine(config)
            mc_result = mc_engine.run()

            # Análisis financiero con muestras reales de la simulación
            fa_engine = FinancialAnalysisEngine(
                revenue=revenue,
                variable_costs=variable_costs,
                fixed_costs=fixed_costs,
                demand_mean=demand_mean,
                demand_std=demand_std,
                unit_price=unit_price,
                industry_sector=industry_sector,
                profit_samples=mc_result.demand_samples * unit_price - mc_result.demand_samples * unit_cost - fixed_costs,
                min_profit_margin=profile.min_profit_margin_pct if profile else None,
                max_cost_ratio=profile.max_cost_revenue_ratio if profile else None,
            )

            return Response(fa_engine.to_dict(), status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("Error en RiskAnalysisAPIView")
            return Response({"error": "Error interno en el análisis de riesgo."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────
# POST /api/v1/scenarios/
# ─────────────────────────────────────────────

class ScenariosAPIView(APIView):
    """
    Genera escenarios financieros (pesimista / conservador / base / optimista / muy_optimista).

    Body (JSON):
        revenue            float   — Ingresos base actuales
        variable_costs     float   — Costos variables actuales
        fixed_costs        float   — Costos fijos
        demand_mean        float   — Demanda media
        unit_price         float   — Precio unitario
        industry_sector    str     — Sector (def: other)
        demand_factors     dict    — Factores de demanda por escenario (opcional)
                                     ej: {"pesimista": 0.65, "optimista": 1.20}
        business_id        int     — ID negocio (opcional)

    Returns:
        {scenarios: {pesimista, conservador, base, optimista, muy_optimista},
         break_even, summary_table}
    """

    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        data = request.data
        required = ['revenue', 'variable_costs', 'fixed_costs', 'demand_mean']
        ok, err = _require_fields(data, required)
        if not ok:
            return Response({"error": err}, status=status.HTTP_400_BAD_REQUEST)

        profile = None
        industry_sector = data.get('industry_sector', 'other')
        if 'business_id' in data:
            business, err_resp = _get_business(int(data['business_id']), request.user)
            if err_resp:
                return err_resp
            profile = CompanyProfile.get_or_create_for_business(business)
            industry_sector = business.industry_sector

        revenue = float(data['revenue'])
        variable_costs = float(data['variable_costs'])
        fixed_costs = float(data['fixed_costs'])
        demand_mean = float(data['demand_mean'])
        demand_std = float(data.get('demand_std', demand_mean * 0.15))
        unit_price = float(data.get('unit_price', revenue / max(demand_mean, 1)))

        # Factores de demanda personalizados (optional override)
        custom_factors = data.get('demand_factors', {})

        try:
            fa_engine = FinancialAnalysisEngine(
                revenue=revenue,
                variable_costs=variable_costs,
                fixed_costs=fixed_costs,
                demand_mean=demand_mean,
                demand_std=demand_std,
                unit_price=unit_price,
                industry_sector=industry_sector,
            )

            metrics = fa_engine.compute_metrics()
            scenarios = fa_engine.compute_scenarios()

            # Aplicar factores personalizados si se proveyeron
            if custom_factors:
                unit_var_cost = variable_costs / max(demand_mean, 1)
                for scenario_name, factor in custom_factors.items():
                    try:
                        factor = float(factor)
                        d = demand_mean * factor
                        rev = d * unit_price
                        var_c = d * unit_var_cost
                        total_c = var_c + fixed_costs
                        gp = rev - total_c
                        scenarios[scenario_name] = {
                            'demand_factor': factor,
                            'demand_units': round(d, 2),
                            'revenue': round(rev, 2),
                            'variable_costs': round(var_c, 2),
                            'total_costs': round(total_c, 2),
                            'gross_profit': round(gp, 2),
                            'profit_margin_pct': round((gp / rev * 100) if rev > 0 else 0, 2),
                            'roi_pct': round((gp / total_c * 100) if total_c > 0 else 0, 2),
                            'is_profitable': gp > 0,
                        }
                    except (TypeError, ValueError):
                        continue

            # Tabla resumen ordenada
            summary_table = [
                {
                    'scenario': k,
                    'demand_factor': f"{v['demand_factor']:.0%}",
                    'revenue': v['revenue'],
                    'profit': v['gross_profit'],
                    'margin': v['profit_margin_pct'],
                    'profitable': v['is_profitable'],
                }
                for k, v in scenarios.items()
            ]

            return Response({
                'scenarios': scenarios,
                'break_even': {
                    'units': metrics.breakeven_units,
                    'revenue': metrics.breakeven_revenue,
                    'margin_of_safety_pct': metrics.margin_of_safety_pct,
                },
                'summary_table': summary_table,
                'industry_sector': industry_sector,
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception("Error en ScenariosAPIView")
            return Response({"error": "Error interno en la generación de escenarios."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────
# GET/PUT /api/v1/company-profile/<business_id>/
# ─────────────────────────────────────────────

class CompanyProfileAPIView(APIView):
    """
    Gestión del perfil de configuración de simulación por empresa.

    GET  — Retorna el perfil actual (crea uno con defaults si no existe)
    PUT  — Actualiza los parámetros del perfil

    Campos actualizables:
        distribution_preference, monte_carlo_iterations, confidence_level,
        demand_pattern, seasonality_factors, peak_months,
        primary_cost_driver, primary_revenue_driver, demand_variable_name,
        min_profit_margin_pct, max_cost_revenue_ratio, inventory_days_target,
        custom_kpis, simulation_notes
    """

    permission_classes = [IsAuthenticated]

    UPDATABLE_FIELDS = [
        'distribution_preference', 'monte_carlo_iterations', 'confidence_level',
        'demand_pattern', 'seasonality_factors', 'peak_months',
        'primary_cost_driver', 'primary_revenue_driver', 'demand_variable_name',
        'min_profit_margin_pct', 'max_cost_revenue_ratio', 'inventory_days_target',
        'custom_kpis', 'simulation_notes',
    ]

    def _serialize_profile(self, profile: CompanyProfile) -> Dict:
        b = profile.fk_business
        return {
            'id': profile.id,
            'business': {
                'id': b.id,
                'name': b.name,
                'type': b.get_type_display(),
                'industry_sector': b.industry_sector,
                'sector_label': b.sector_label,
            },
            'simulation': {
                'distribution_preference': profile.distribution_preference,
                'monte_carlo_iterations': profile.get_effective_iterations(),
                'confidence_level': profile.confidence_level,
            },
            'demand': {
                'pattern': profile.demand_pattern,
                'seasonality_factors': profile.get_seasonality_factors(),
                'peak_months': profile.peak_months,
                'demand_variable_name': profile.demand_variable_name,
            },
            'financial': {
                'primary_cost_driver': profile.primary_cost_driver,
                'primary_revenue_driver': profile.primary_revenue_driver,
                'min_profit_margin_pct': profile.min_profit_margin_pct,
                'max_cost_revenue_ratio': profile.max_cost_revenue_ratio,
                'inventory_days_target': profile.inventory_days_target,
            },
            'custom_kpis': profile.custom_kpis,
            'simulation_notes': profile.simulation_notes,
            'last_updated': profile.last_updated.isoformat() if profile.last_updated else None,
        }

    def get(self, request, business_id: int) -> Response:
        business, err_resp = _get_business(business_id, request.user)
        if err_resp:
            return err_resp
        profile = CompanyProfile.get_or_create_for_business(business)
        return Response(self._serialize_profile(profile), status=status.HTTP_200_OK)

    def put(self, request, business_id: int) -> Response:
        business, err_resp = _get_business(business_id, request.user)
        if err_resp:
            return err_resp
        profile = CompanyProfile.get_or_create_for_business(business)

        data = request.data
        updated = []
        errors = {}

        for field in self.UPDATABLE_FIELDS:
            if field not in data:
                continue
            value = data[field]
            try:
                # Validaciones específicas
                if field == 'confidence_level':
                    value = float(value)
                    if not (0.80 <= value <= 0.99):
                        errors[field] = "Debe estar entre 0.80 y 0.99"
                        continue
                elif field == 'monte_carlo_iterations':
                    value = int(value)
                    if not (1000 <= value <= 100000):
                        errors[field] = "Debe estar entre 1000 y 100000"
                        continue
                elif field == 'min_profit_margin_pct':
                    value = float(value)
                    if not (0 <= value <= 100):
                        errors[field] = "Debe estar entre 0 y 100"
                        continue
                elif field == 'max_cost_revenue_ratio':
                    value = float(value)
                    if not (0 <= value <= 150):
                        errors[field] = "Debe estar entre 0 y 150"
                        continue
                elif field == 'seasonality_factors':
                    if not isinstance(value, list) or len(value) != 12:
                        errors[field] = "Debe ser una lista de exactamente 12 factores numéricos"
                        continue
                    value = [float(v) for v in value]
                elif field == 'distribution_preference':
                    valid = [c[0] for c in CompanyProfile.DistributionPreference.choices]
                    if value not in valid:
                        errors[field] = f"Debe ser uno de: {valid}"
                        continue
                elif field == 'demand_pattern':
                    valid = [c[0] for c in CompanyProfile.DemandPattern.choices]
                    if value not in valid:
                        errors[field] = f"Debe ser uno de: {valid}"
                        continue

                setattr(profile, field, value)
                updated.append(field)
            except (TypeError, ValueError) as e:
                errors[field] = f"Valor inválido: {e}"

        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        if updated:
            profile.save(update_fields=updated + ['last_updated'])

        return Response({
            'updated_fields': updated,
            'profile': self._serialize_profile(profile),
        }, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────
# POST /api/v1/full-pipeline/<simulation_id>/
# ─────────────────────────────────────────────

class FullPipelineAPIView(APIView):
    """
    Ejecuta el pipeline completo de simulación sobre una Simulation ya guardada en BD:
      Monte Carlo → Eventos Discretos → Motor de Decisión

    Requiere que la Simulation exista y esté asociada al usuario autenticado.

    Body (JSON, todos opcionales):
        n_monte_carlo  int    — Escenarios Monte Carlo por período (def: 5000)
        risk_aversion  float  — Coeficiente λ de aversión al riesgo CARA (def: 0.001)

    Returns:
        {
          aggregated: { demand_mean, demand_p5/p95, revenue_mean, profit_mean,
                        probability_of_loss, value_at_risk, expected_shortfall, ... },
          decision: { assessment, score, summary, recommendations, risk_metrics },
          period_summary: [ {period, demand_mean, revenue_mean, profit_mean}, ... ]
        }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, simulation_id: int) -> Response:
        from simulate.models import Simulation
        from simulate.services.simulation_service import SimulationService

        # Validar que la simulación existe y pertenece al usuario
        try:
            simulation = Simulation.objects.select_related(
                'fk_questionary_result__fk_questionary__fk_product__fk_business__fk_user',
                'fk_fdp',
            ).get(
                pk=simulation_id,
                fk_questionary_result__fk_questionary__fk_product__fk_business__fk_user=request.user,
                is_active=True,
            )
        except Simulation.DoesNotExist:
            return Response(
                {"error": "Simulación no encontrada o sin permisos de acceso."},
                status=status.HTTP_404_NOT_FOUND,
            )

        data = request.data
        n_mc = int(_clamp(data.get('n_monte_carlo', 5000), 100, 50000, 5000))
        risk_av = _clamp(data.get('risk_aversion', 0.001), 1e-6, 1.0, 0.001)
        persist = str(data.get('persist', 'false')).lower() in ('true', '1', 'yes')

        try:
            service = SimulationService()
            if persist:
                pipeline_result = service.run_and_save(
                    simulation=simulation,
                    n_monte_carlo=n_mc,
                    risk_aversion=risk_av,
                )
            else:
                pipeline_result = service.run_full_pipeline(
                    simulation_instance=simulation,
                    n_monte_carlo=n_mc,
                    risk_aversion=risk_av,
                )
        except Exception:
            logger.exception("Error en FullPipelineAPIView simulation_id=%s", simulation_id)
            return Response(
                {"error": "Error interno al ejecutar el pipeline de simulación."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        agg = pipeline_result['aggregated']
        report = pipeline_result['decision_report']

        response_body = {
            'simulation_id': simulation_id,
            'persisted': persist,
        }
        if persist and 'summary' in pipeline_result:
            response_body['summary'] = pipeline_result['summary']

        response_body.update({
            'aggregated': {
                'demand_mean': agg.demand_mean,
                'demand_p5': agg.demand_p5,
                'demand_p95': agg.demand_p95,
                'revenue_mean': agg.revenue_mean,
                'profit_mean': agg.profit_mean,
                'profit_p5': agg.profit_p5,
                'profit_p95': agg.profit_p95,
                'probability_of_loss': agg.probability_of_loss,
                'probability_breakeven': agg.probability_breakeven,
                'value_at_risk': agg.value_at_risk,
                'expected_shortfall': agg.expected_shortfall,
                'n_scenarios': agg.n_scenarios,
                'distribution_used': agg.distribution_used,
                'scenarios': {
                    'pessimistic': agg.scenario_pessimistic,
                    'base': agg.scenario_base,
                    'optimistic': agg.scenario_optimistic,
                },
            },
            'decision': {
                'assessment': report.overall_assessment,
                'score': report.overall_score,
                'summary': report.summary,
                'expected_utility': report.expected_utility,
                'risk_metrics': {
                    'mean': report.risk_metrics.mean,
                    'std': report.risk_metrics.std,
                    'p5': report.risk_metrics.p5,
                    'p50': report.risk_metrics.p50,
                    'p95': report.risk_metrics.p95,
                    'probability_of_loss': report.risk_metrics.probability_of_loss,
                    'var_95': report.risk_metrics.var_95,
                    'cvar_95': report.risk_metrics.cvar_95,
                    'sharpe_ratio': report.risk_metrics.sharpe_ratio,
                },
                'recommendations': [r.to_dict() for r in report.recommendations],
                'scenario_comparison': report.scenario_comparison,
            },
            'period_summary': pipeline_result['period_results'],
        })
        return Response(response_body, status=status.HTTP_200_OK)
