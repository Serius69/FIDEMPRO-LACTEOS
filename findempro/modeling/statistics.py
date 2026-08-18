"""Deterministic, bounded distribution fitting for the uncertainty laboratory.

The fitter is proposal-only.  It never mutates a model version and separates
descriptive fit diagnostics from model ranking.  In particular, it does not
publish the naive one-sample KS p-value after estimating parameters from the
same observations.
"""

from __future__ import annotations

import math
from typing import Any, Callable

import numpy as np
from scipy import stats


class DistributionFitError(ValueError):
    """Raised when observations or a requested candidate are inadmissible."""


METHOD_VERSION = "distribution_fit_v2"
MIN_SAMPLE_SIZE = 5
SUPPORTED_FIT_DISTRIBUTIONS = {
    "normal", "lognormal", "gamma", "exponential", "uniform", "poisson"
}


def _validate_observations(observations: Any) -> np.ndarray:
    if not isinstance(observations, list) or not MIN_SAMPLE_SIZE <= len(observations) <= 10_000:
        raise DistributionFitError(
            f"observations debe contener entre {MIN_SAMPLE_SIZE} y 10.000 valores."
        )
    if any(isinstance(value, bool) for value in observations):
        raise DistributionFitError("observations no puede contener booleanos.")
    try:
        values = np.asarray(observations, dtype=float)
    except (TypeError, ValueError) as exc:
        raise DistributionFitError("Cada observación debe ser numérica.") from exc
    if not np.all(np.isfinite(values)):
        raise DistributionFitError("Cada observación debe ser finita.")
    return values


def _candidate_names(values: np.ndarray, data_semantics: str) -> list[str]:
    if data_semantics == "count":
        return ["poisson"]
    names = ["normal", "uniform"]
    if np.all(values > 0):
        names.extend(["lognormal", "gamma", "exponential"])
    return names


def _fit_normal(values: np.ndarray):
    mean, std = float(values.mean()), float(values.std(ddof=0))
    if std <= 0:
        raise DistributionFitError("normal requiere variación en los datos.")
    params = {"loc": mean, "scale": std}
    return params, lambda x: stats.norm.logpdf(x, mean, std), lambda x: stats.norm.cdf(x, mean, std), "continuous", ["observaciones independientes", "soporte real"]


def _fit_lognormal(values: np.ndarray):
    if np.any(values <= 0):
        raise DistributionFitError("lognormal requiere observaciones estrictamente positivas.")
    logs = np.log(values)
    mean, sigma = float(logs.mean()), float(logs.std(ddof=0))
    if sigma <= 0:
        raise DistributionFitError("lognormal requiere variación en los datos.")
    params = {"log_mean": mean, "shape": sigma, "scale": math.exp(mean)}
    return params, lambda x: stats.lognorm.logpdf(x, sigma, scale=math.exp(mean)), lambda x: stats.lognorm.cdf(x, sigma, scale=math.exp(mean)), "continuous", ["observaciones independientes", "valores estrictamente positivos"]


def _fit_gamma(values: np.ndarray):
    if np.any(values <= 0):
        raise DistributionFitError("gamma requiere observaciones estrictamente positivas.")
    mean, variance = float(values.mean()), float(values.var(ddof=0))
    if variance <= 0 or mean <= 0:
        raise DistributionFitError("gamma requiere media y variación positivas.")
    shape, scale = mean * mean / variance, variance / mean
    params = {"shape": shape, "scale": scale}
    return params, lambda x: stats.gamma.logpdf(x, shape, scale=scale), lambda x: stats.gamma.cdf(x, shape, scale=scale), "continuous", ["observaciones independientes", "valores estrictamente positivos", "parámetros por momentos"]


def _fit_exponential(values: np.ndarray):
    if np.any(values < 0):
        raise DistributionFitError("exponential requiere observaciones no negativas.")
    scale = float(values.mean())
    if scale <= 0:
        raise DistributionFitError("exponential requiere una media positiva.")
    params = {"loc": 0.0, "scale": scale, "rate": 1.0 / scale}
    return params, lambda x: stats.expon.logpdf(x, scale=scale), lambda x: stats.expon.cdf(x, scale=scale), "continuous", ["observaciones independientes", "origen fijado en cero", "valores no negativos"]


def _fit_uniform(values: np.ndarray):
    minimum, maximum = float(values.min()), float(values.max())
    if maximum <= minimum:
        raise DistributionFitError("uniform requiere un rango positivo.")
    params = {"minimum": minimum, "maximum": maximum, "scale": maximum - minimum}
    return params, lambda x: stats.uniform.logpdf(x, minimum, maximum - minimum), lambda x: stats.uniform.cdf(x, minimum, maximum - minimum), "continuous", ["observaciones independientes", "límites estimados de la muestra"]


def _fit_poisson(values: np.ndarray):
    if np.any(values < 0) or not np.allclose(values, np.round(values)):
        raise DistributionFitError("poisson requiere conteos enteros no negativos.")
    rate = float(values.mean())
    if rate <= 0:
        raise DistributionFitError("poisson requiere una media positiva.")
    params = {"rate": rate}
    return params, lambda x: stats.poisson.logpmf(np.round(x), rate), lambda x: stats.poisson.cdf(np.floor(x), rate), "discrete", ["conteos enteros no negativos", "exposición comparable", "eventos independientes con tasa constante"]


_FITTERS: dict[str, Callable] = {
    "normal": _fit_normal,
    "lognormal": _fit_lognormal,
    "gamma": _fit_gamma,
    "exponential": _fit_exponential,
    "uniform": _fit_uniform,
    "poisson": _fit_poisson,
}


def _fit_diagnostic(name: str, values: np.ndarray) -> dict[str, Any]:
    parameters, log_probability, cdf, family, assumptions = _FITTERS[name](values)
    log_likelihood = float(np.sum(log_probability(values)))
    if not math.isfinite(log_likelihood):
        raise DistributionFitError(f"{name} produjo una verosimilitud no finita.")

    if family == "continuous":
        statistic = float(stats.kstest(values, cdf).statistic)
        test_name = "kolmogorov_smirnov_distance"
        p_reason = "PARAMETERS_ESTIMATED_FROM_SAME_SAMPLE"
        warning = "El p-value KS ingenuo no se calcula porque los parámetros se estimaron con la misma muestra."
    else:
        ordered = np.sort(values)
        support = np.unique(ordered)
        empirical_cdf = np.searchsorted(ordered, support, side="right") / values.size
        statistic = float(np.max(np.abs(empirical_cdf - cdf(support))))
        test_name = "discrete_cdf_max_distance"
        p_reason = "DISCRETE_TEST_NOT_CALIBRATED"
        warning = "No se aplica el p-value KS continuo a observaciones discretas."

    if not math.isfinite(statistic):
        raise DistributionFitError(f"{name} produjo un diagnóstico no finito.")
    parameter_count = len(parameters)
    return {
        "distribution": name,
        "family": family,
        "parameters": {key: round(float(value), 12) for key, value in parameters.items()},
        "fit_method": "maximum_likelihood" if name in {"normal", "lognormal", "exponential", "uniform", "poisson"} else "method_of_moments",
        "method_version": METHOD_VERSION,
        "statistic": round(statistic, 12),
        "ks_statistic": round(statistic, 12) if family == "continuous" else None,
        "p_value": None,
        "test_name": test_name,
        "p_value_method": "not_computed",
        "p_value_unavailable_reason": p_reason,
        "n_observations": int(values.size),
        "sample_size": int(values.size),
        "valid": True,
        "unavailable_reason": None,
        "assumptions": assumptions,
        "warnings": [warning],
        "log_likelihood": round(log_likelihood, 12),
        "aic": round(2 * parameter_count - 2 * log_likelihood, 12),
        "bic": round(parameter_count * math.log(values.size) - 2 * log_likelihood, 12),
    }


def fit_distributions(
    observations: list[Any],
    candidates: list[str] | None = None,
    *,
    data_semantics: str = "continuous",
) -> dict[str, Any]:
    values = _validate_observations(observations)
    resolution = np.finfo(float).eps * max(1.0, float(np.max(np.abs(values)))) * 100
    if float(np.ptp(values)) <= resolution:
        raise DistributionFitError(
            "Ninguna distribución candidata es compatible con datos sin variación."
        )
    if data_semantics not in {"continuous", "count"}:
        raise DistributionFitError("data_semantics debe ser 'continuous' o 'count'.")
    requested = candidates or _candidate_names(values, data_semantics)
    if not isinstance(requested, list) or not requested:
        raise DistributionFitError("candidates debe contener al menos una distribución.")
    unknown = sorted(set(requested) - SUPPORTED_FIT_DISTRIBUTIONS)
    if unknown:
        raise DistributionFitError("Distribuciones no soportadas: " + ", ".join(unknown))

    fitted: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []
    for name in dict.fromkeys(requested):
        try:
            fitted.append(_fit_diagnostic(name, values))
        except (DistributionFitError, ValueError, FloatingPointError) as exc:
            rejected.append({"distribution": name, "reason": str(exc)})
    if not fitted:
        raise DistributionFitError("Ninguna distribución candidata es compatible con los datos.")

    families = {candidate["family"] for candidate in fitted}
    comparable = len(families) == 1
    fitted.sort(key=lambda item: (item["family"], item["aic"], item["statistic"], item["distribution"]))
    selected = min(fitted, key=lambda item: (item["aic"], item["statistic"], item["distribution"])) if comparable else None
    return {
        "method": METHOD_VERSION,
        "method_version": METHOD_VERSION,
        "support": {
            "min": float(values.min()),
            "max": float(values.max()),
            "positive": bool(np.all(values > 0)),
            "integer_nonnegative": bool(np.all(values >= 0) and np.allclose(values, np.round(values))),
        },
        "data_semantics": data_semantics,
        "n_observations": int(values.size),
        "quantiles": {f"p{p}": float(np.percentile(values, p)) for p in (5, 25, 50, 75, 95)},
        "candidates": fitted,
        "rejected": rejected,
        "ranking": {
            "criterion": "AIC_THEN_DIAGNOSTIC_WITHIN_LIKELIHOOD_FAMILY",
            "comparable": comparable,
            "selected_distribution": selected["distribution"] if selected else None,
            "unavailable_reason": None if comparable else "MIXED_LIKELIHOOD_FAMILIES",
        },
        "provenance": "USER_ENTERED_OBSERVATIONS",
        "requires_review": True,
    }
