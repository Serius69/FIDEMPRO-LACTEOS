"""Shared statistical contracts for simulation and reporting paths."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

import numpy as np


@dataclass(frozen=True)
class DistributionShape:
    """Location/scale-independent shape moments with availability metadata."""

    skewness: Optional[float]
    kurtosis: Optional[float]
    status: str


def stable_distribution_shape(values: Iterable[float]) -> DistributionShape:
    """Return biased skewness/excess kurtosis without inventing degenerate shape.

    Shape is not defined for fewer than three observations or for a series whose
    spread cannot be distinguished from floating-point resolution at its scale.
    Non-degenerate observations are centered and normalized before calculating
    moments, avoiding catastrophic cancellation for large monetary locations.
    """

    data = np.asarray(list(values), dtype=float).reshape(-1)
    if not np.all(np.isfinite(data)):
        raise ValueError("Los datos para momentos estadísticos deben ser finitos.")
    if data.size < 3:
        return DistributionShape(None, None, "INSUFFICIENT_OBSERVATIONS")

    spread = float(np.ptp(data))
    resolution = (
        np.finfo(float).eps
        * max(1.0, float(np.max(np.abs(data))))
        * 100.0
    )
    if spread <= resolution:
        return DistributionShape(None, None, "DEGENERATE_DISTRIBUTION")

    # Subtract one observation first so a large location does not erase small,
    # but still representable, differences while centering the sample.
    centered = data - data[0]
    centered -= float(np.mean(centered))
    scale = float(np.max(np.abs(centered)))
    normalized = centered / scale
    second_moment = float(np.mean(normalized ** 2))
    if second_moment <= np.finfo(float).eps:
        return DistributionShape(None, None, "DEGENERATE_DISTRIBUTION")

    skewness = float(np.mean(normalized ** 3) / second_moment ** 1.5)
    kurtosis = float(np.mean(normalized ** 4) / second_moment ** 2 - 3.0)
    return DistributionShape(skewness, kurtosis, "AVAILABLE")
