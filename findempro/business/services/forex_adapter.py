"""
business/services/forex_adapter.py
==================================
Adaptador del dataset REAL de operaciones de casa de cambio (forex-erp,
``operaciones_forex_anonimizado.csv``) a una serie diaria de demanda que el
simulador puede consumir vía ``demand_import.write_series``.

El CSV está anonimizado: NO trae fecha exacta, solo ``mes`` (``YYYY-MM``) y
``dia_semana``. La serie diaria se reconstruye por **desagregación** honesta:

* el TOTAL de cada mes es exactamente el real (conteo de operaciones o volumen
  en Bs, según ``metric``);
* la forma dentro del mes sigue la distribución REAL por día de semana del
  dataset completo (p.ej. domingo ≈ 6 % del lunes).

No inventa nivel ni tendencia — solo reparte el total mensual real entre los
días calendario del mes con los pesos semanales reales. Los meses de borde
parciales (exportes que empiezan/terminan a mitad de mes) se excluyen por
defecto: un mes se considera parcial si tiene menos de la mitad de las
operaciones del mes mediano.
"""
from __future__ import annotations

import calendar
import datetime as dt
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

REQUIRED_COLUMNS = {"mes", "dia_semana", "total_bs"}

# Python: Monday=0 … Sunday=6 (coincide con date.weekday()).
_WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday",
                  "Friday", "Saturday", "Sunday"]

PARTIAL_MONTH_FRACTION = 0.5  # < 50 % de las ops del mes mediano ⇒ mes parcial


@dataclass
class DailySeries:
    """Serie diaria reconstruida + metadatos de la desagregación."""
    dates: List[dt.date] = field(default_factory=list)
    values: List[float] = field(default_factory=list)
    metric: str = "ops"
    months_used: List[str] = field(default_factory=list)
    months_dropped: List[str] = field(default_factory=list)
    weekday_weights: Dict[str, float] = field(default_factory=dict)
    monthly_totals: Dict[str, float] = field(default_factory=dict)


def load_operations(path: str):
    """Carga el CSV de operaciones y valida las columnas mínimas."""
    import pandas as pd
    df = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"el CSV no parece un export de operaciones forex: faltan columnas "
            f"{sorted(missing)}")
    return df


def _month_days(mes: str) -> List[dt.date]:
    """Días calendario de un mes 'YYYY-MM'."""
    year, month = int(mes[:4]), int(mes[5:7])
    n = calendar.monthrange(year, month)[1]
    return [dt.date(year, month, d) for d in range(1, n + 1)]


def weekday_weights(df) -> Dict[str, float]:
    """Frecuencia relativa REAL de operaciones por día de semana (suma 1.0)."""
    counts = df["dia_semana"].value_counts()
    total = float(counts.sum())
    return {name: float(counts.get(name, 0)) / total for name in _WEEKDAY_NAMES}


def build_daily_series(df, *, metric: str = "ops",
                       include_partial: bool = False) -> DailySeries:
    """
    Reconstruye la serie diaria desde los totales mensuales reales.

    ``metric``: ``'ops'`` = operaciones/día (clientes atendidos) — la noción de
    demanda del simulador; ``'bs'`` = volumen cambiado en Bs/día.
    """
    if metric not in ("ops", "bs"):
        raise ValueError("metric debe ser 'ops' o 'bs'")

    if metric == "ops":
        totals = df.groupby("mes").size().astype(float)
    else:
        totals = df.groupby("mes")["total_bs"].sum().astype(float)
    ops_per_month = df.groupby("mes").size().astype(float)

    out = DailySeries(metric=metric, weekday_weights=weekday_weights(df))

    threshold = ops_per_month.median() * PARTIAL_MONTH_FRACTION
    for mes in sorted(totals.index):
        if not include_partial and ops_per_month[mes] < threshold:
            out.months_dropped.append(mes)
            continue
        out.months_used.append(mes)
        out.monthly_totals[mes] = round(float(totals[mes]), 2)

        days = _month_days(mes)
        day_w = [out.weekday_weights[_WEEKDAY_NAMES[d.weekday()]] for d in days]
        w_sum = sum(day_w) or 1.0
        for day, w in zip(days, day_w):
            out.dates.append(day)
            out.values.append(round(float(totals[mes]) * w / w_sum, 2))
    return out
