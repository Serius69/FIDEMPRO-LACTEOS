"""
simulate/services/sensitivity_service.py
=========================================
Análisis de sensibilidad OAT (One-At-a-Time) para proyectos canvas.

Para cada nodo estocástico del modelo (con distribution_config):
  1. Baseline: muestrea n_runs del parámetro de posición original
  2. High:     muestrea con mean * (1 + variation_pct)
  3. Low:      muestrea con mean * (1 - variation_pct)
  4. Swing:    profit_proxy_high - profit_proxy_low

Devuelve lista de SensitivityResult + formato ApexCharts tornado chart.

Proxy de utilidad: profit = mean(samples) * 0.30 (consistente con
_minimal_montecarlo en canvas_views.py; margen bruto estimado del 30%).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SensitivityResult:
    variable: str
    dist_type: str
    baseline_mean: float
    high_mean: float
    low_mean: float
    swing: float
    sensitivity_pct: float


class SensitivityService:
    """
    Análisis de sensibilidad OAT para proyectos canvas.

    Requiere los mismos datos de entrada que SimulationRunView:
      nodes    – lista de dicts con 'label', 'distribution_config', etc.
      edges    – lista de dicts (sólo para trazabilidad futura)
      run_specs– dict con parámetros de corrida del proyecto
    """

    _PROFIT_MARGIN = 0.30  # proxy margen bruto, consistente con _minimal_montecarlo

    # ── API pública ──────────────────────────────────────────────────────────

    def run_oat(
        self,
        nodes: List[Dict],
        edges: List[Dict],
        run_specs: Dict,
        variation_pct: float = 0.20,
        n_runs: int = 500,
        seed: Optional[int] = None,
    ) -> List[SensitivityResult]:
        """
        Ejecuta análisis OAT sobre todas las variables estocásticas del modelo.

        Returns:
            Lista de SensitivityResult ordenada por |swing| descendente.
            Lista vacía si no hay nodos estocásticos.
        """
        stochastic = self._extract_stochastic(nodes)
        if not stochastic:
            return []

        seed_eff = seed if seed is not None else run_specs.get("random_seed")

        results: List[SensitivityResult] = []
        for idx, (var_name, dist_cfg) in enumerate(stochastic.items()):
            result = self._analyze_variable(
                var_name, dist_cfg, variation_pct, n_runs,
                # Offsets de semilla distintos por variable para independencia
                None if seed_eff is None else seed_eff + idx * 3,
            )
            if result is not None:
                results.append(result)

        results.sort(key=lambda r: abs(r.swing), reverse=True)
        return results

    def to_apexcharts(
        self,
        results: List[SensitivityResult],
        variation_pct: float = 0.20,
        baseline_profit: Optional[float] = None,
    ) -> Dict:
        """
        Convierte los resultados al formato ApexCharts (tornado chart horizontal).

        Series:
          • "+N%" : impacto positivo (profit_high - profit_baseline)
          • "-N%" : impacto negativo (profit_low  - profit_baseline)

        Las barras positivas van a la derecha y las negativas a la izquierda,
        lo que produce el aspecto visual de tornado.
        """
        pct_label = int(variation_pct * 100)
        categories = [r.variable for r in results]
        high_data = [round(r.high_mean - r.baseline_mean, 2) for r in results]
        low_data  = [round(r.low_mean  - r.baseline_mean, 2) for r in results]

        sensitivity_table = [
            {
                "rank":             idx + 1,
                "variable":         r.variable,
                "dist_type":        r.dist_type,
                "baseline_profit":  r.baseline_mean,
                "profit_high":      r.high_mean,
                "profit_low":       r.low_mean,
                "swing":            r.swing,
                "sensitivity_pct":  r.sensitivity_pct,
            }
            for idx, r in enumerate(results)
        ]

        return {
            "chart_type":     "bar",
            "horizontal":     True,
            "title":          f"Análisis de Sensibilidad OAT (±{pct_label}%)",
            "series": [
                {"name": f"+{pct_label}%", "data": high_data, "color": "#16a34a"},
                {"name": f"-{pct_label}%", "data": low_data,  "color": "#dc2626"},
            ],
            "categories":     categories,
            "xaxis_title":    "Impacto en Utilidad (BOB)",
            "baseline_profit": baseline_profit,
            "n_variables":    len(results),
            "sensitivity_table": sensitivity_table,
        }

    # ── Helpers privados ─────────────────────────────────────────────────────

    def _extract_stochastic(self, nodes: List[Dict]) -> Dict[str, Dict]:
        """Retorna {label: distribution_config} para nodos con distribución definida."""
        out: Dict[str, Dict] = {}
        for node in nodes:
            cfg = node.get("distribution_config")
            if cfg and isinstance(cfg, dict) and cfg.get("dist_type"):
                label = node.get("label") or node.get("id", "unknown")
                out[label] = cfg
        return out

    def _get_location_param(self, dist_cfg: Dict) -> Optional[Tuple[str, float]]:
        """
        Retorna (param_key, value) del parámetro de posición de la distribución.

        Distribución → parámetro de posición:
          normal / lognormal → 'mean'  (o 'mu')
          triangular          → 'mode'  (o midpoint low/high)
          uniform             → midpoint (low+high)/2
          gamma               → 'mean' (o shape*scale)
          beta                → 'mean' (o midpoint de high)
          weibull             → 'scale'
        """
        params = dist_cfg.get("params", {})
        dist_type = dist_cfg.get("dist_type", "normal").lower()

        if dist_type in ("normal", "lognormal"):
            for k in ("mean", "mu"):
                if k in params and params[k] is not None:
                    return (k, float(params[k]))

        elif dist_type == "triangular":
            if "mode" in params and params["mode"] is not None:
                return ("mode", float(params["mode"]))
            if "low" in params and "high" in params:
                mid = (float(params["low"]) + float(params["high"])) / 2
                return ("mode_computed", mid)

        elif dist_type == "uniform":
            if "low" in params and "high" in params:
                mid = (float(params["low"]) + float(params["high"])) / 2
                return ("midpoint_computed", mid)

        elif dist_type == "gamma":
            if "mean" in params and params["mean"] is not None:
                return ("mean", float(params["mean"]))
            if "shape" in params and "scale" in params:
                computed = float(params["shape"]) * float(params["scale"])
                return ("mean_computed", computed)

        elif dist_type == "beta":
            if "mean" in params and params["mean"] is not None:
                return ("mean", float(params["mean"]))
            # Beta mean = α/(α+β) scaled by 'high' (if provided)
            alpha_v = params.get("alpha") or params.get("shape")
            beta_v  = params.get("beta")  or params.get("scale")
            if alpha_v is not None and beta_v is not None:
                hi = float(params.get("high", 1.0))
                computed = float(alpha_v) / (float(alpha_v) + float(beta_v)) * hi
                return ("mean_computed", computed)

        elif dist_type == "weibull":
            for k in ("scale", "lambda", "mean"):
                if k in params and params[k] is not None:
                    return (k, float(params[k]))

        # Fallback genérico
        for k in ("mean", "mu", "mode", "scale", "rate"):
            if k in params and params[k] is not None:
                return (k, float(params[k]))

        return None

    def _sample(
        self,
        dist_cfg: Dict,
        location_override: Optional[float],
        n: int,
        rng: np.random.Generator,
    ) -> np.ndarray:
        """Genera n muestras de la distribución, opcionalmente con media sobreescrita."""
        from scipy import stats

        params = dict(dist_cfg.get("params", {}))
        dist_type = dist_cfg.get("dist_type", "normal").lower()
        loc_info = self._get_location_param(dist_cfg)

        if location_override is not None and loc_info is not None:
            key, original = loc_info
            if key.endswith("_computed"):
                # Parámetro derivado: escalar todos los parámetros proporcionales
                factor = location_override / max(abs(original), 1e-6)
                if dist_type == "uniform":
                    params["low"]  = float(params.get("low",  0)) * factor
                    params["high"] = float(params.get("high", 1)) * factor
                elif dist_type == "triangular":
                    for k in ("low", "mode", "high"):
                        if k in params:
                            params[k] = float(params[k]) * factor
                elif dist_type in ("gamma", "beta"):
                    if "scale" in params:
                        params["scale"] = float(params["scale"]) * factor
            else:
                params[key] = location_override

        try:
            if dist_type == "normal":
                mu    = float(params.get("mean", params.get("mu", 500)))
                sigma = max(float(params.get("std", params.get("sigma", 80))), 1e-6)
                return np.maximum(rng.normal(mu, sigma, n), 0.0)

            elif dist_type == "lognormal":
                mu    = float(params.get("mean", params.get("mu", 6.0)))
                sigma = max(float(params.get("std", params.get("sigma", 0.3))), 1e-6)
                return stats.lognorm.rvs(s=sigma, scale=np.exp(mu), size=n, random_state=rng)

            elif dist_type == "triangular":
                low  = float(params.get("low", 0))
                mode = float(params.get("mode", 500))
                high = float(params.get("high", 1000))
                if low >= high:
                    high = low + 1
                mode = float(np.clip(mode, low, high))
                c = (mode - low) / (high - low)
                return stats.triang.rvs(c=c, loc=low, scale=high - low, size=n, random_state=rng)

            elif dist_type == "uniform":
                low  = float(params.get("low", 0))
                high = float(params.get("high", 1000))
                if low >= high:
                    high = low + 1
                return stats.uniform.rvs(loc=low, scale=high - low, size=n, random_state=rng)

            elif dist_type == "gamma":
                shape = max(float(params.get("shape", params.get("alpha", 2.0))), 0.01)
                scale = max(float(params.get("scale", params.get("beta", 100.0))), 0.01)
                return stats.gamma.rvs(a=shape, scale=scale, size=n, random_state=rng)

            elif dist_type == "beta":
                alpha = max(float(params.get("alpha", 2.0)), 0.01)
                beta  = max(float(params.get("beta",  2.0)), 0.01)
                hi    = float(params.get("high", 1000.0))
                raw   = stats.beta.rvs(a=alpha, b=beta, size=n, random_state=rng)
                return raw * hi

            elif dist_type == "weibull":
                c     = max(float(params.get("shape", params.get("k", 2.0))), 0.01)
                scale = max(float(params.get("scale", params.get("lambda", 500.0))), 0.01)
                return stats.weibull_min.rvs(c=c, scale=scale, size=n, random_state=rng)

        except Exception as exc:
            logger.warning("Error muestreando %s: %s — fallback normal", dist_type, exc)

        # Fallback normal con media estimada
        mu = location_override or (loc_info[1] if loc_info else 500.0)
        return np.maximum(rng.normal(mu, max(mu * 0.15, 1.0), n), 0.0)

    def _profit_proxy(self, samples: np.ndarray) -> float:
        return float(np.mean(samples)) * self._PROFIT_MARGIN

    def _analyze_variable(
        self,
        var_name: str,
        dist_cfg: Dict,
        variation_pct: float,
        n_runs: int,
        seed: Optional[int],
    ) -> Optional[SensitivityResult]:
        """Baseline + high + low para una variable. Retorna None si no hay parámetro de posición."""
        loc_info = self._get_location_param(dist_cfg)
        if loc_info is None:
            logger.debug("Sin parámetro de posición para '%s'", var_name)
            return None

        _, baseline_loc = loc_info
        high_loc = baseline_loc * (1 + variation_pct)
        # Evitar negativos para distribuciones con soporte ≥ 0
        low_loc  = max(baseline_loc * (1 - variation_pct), baseline_loc * 1e-3)

        rng_b = np.random.default_rng(seed)
        rng_h = np.random.default_rng(None if seed is None else seed + 1)
        rng_l = np.random.default_rng(None if seed is None else seed + 2)

        s_b = self._sample(dist_cfg, baseline_loc, n_runs, rng_b)
        s_h = self._sample(dist_cfg, high_loc,     n_runs, rng_h)
        s_l = self._sample(dist_cfg, low_loc,      n_runs, rng_l)

        p_b = self._profit_proxy(s_b)
        p_h = self._profit_proxy(s_h)
        p_l = self._profit_proxy(s_l)

        swing = p_h - p_l
        sensitivity_pct = abs(swing) / max(abs(p_b), 1e-6) * 100 if p_b != 0 else 0.0

        return SensitivityResult(
            variable=var_name,
            dist_type=dist_cfg.get("dist_type", "normal"),
            baseline_mean=round(p_b, 2),
            high_mean=round(p_h, 2),
            low_mean=round(p_l, 2),
            swing=round(swing, 2),
            sensitivity_pct=round(sensitivity_pct, 2),
        )
