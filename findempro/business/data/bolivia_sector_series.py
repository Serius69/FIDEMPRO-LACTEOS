"""
Perfiles estacionales mensuales por sector — mercado boliviano.
===============================================================

Da la **forma real** (estacionalidad) de la demanda por rubro, para calibrar el
generador de demanda del simulador con patrones bolivianos reales en vez de ruido
gaussiano plano. Cada perfil son 12 factores (enero…diciembre) con **media ≈ 1.0**:
un factor 1.30 en diciembre = demanda 30 % sobre el promedio anual ese mes.

Anclados a la estacionalidad económica boliviana documentada (INE — IPC por
división y variación mensual; calendario económico nacional):

* **Diciembre — aguinaldo**: por ley se paga un sueldo extra en diciembre (y un
  segundo aguinaldo si el PIB crece > 4,5 %). Dispara consumo en retail, comida,
  vestido y servicios → pico anual de la mayoría de los rubros de consumo.
* **Enero — Alasitas (La Paz, 24-ene) + prep. escolar**: consumo sostenido tras
  el aguinaldo; útiles/uniformes.
* **Febrero — inicio del año escolar + Carnaval**: pico de educación; alza de
  comida/bebida; algunos servicios bajan por feriados.
* **Mayo — Día de la Madre (27-may)**: pico de retail, restaurantes y regalos.
* **Nov — Todos Santos (1-2 nov)**: pico de panadería (t'antawawas, masitas) y
  comida; construcción antes de lluvias.
* **Cosecha (abr-jul)**: mayor oferta agrícola (papa/tomate del altiplano/valle)
  → estacionalidad del agro.
* **Estación seca (ago-oct)**: pico de construcción antes de la temporada de lluvia.

El comando ``ingest_ine_series`` refresca en vivo (best-effort) contra INE/BCB y
conserva estos perfiles como fallback curado. Mantener media ≈ 1.0 al editar.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

# Meses índice 0=enero … 11=diciembre.
_MONTHS = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
           "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def _normalize(factors: List[float]) -> List[float]:
    """Reescala a media exactamente 1.0 (preserva la forma estacional)."""
    m = sum(factors) / len(factors)
    return [round(f / m, 4) for f in factors]


# ─────────────────────────────────────────────────────────────────────────────
# Perfiles por BusinessType (1..19). Comentario = driver estacional dominante.
#                    Ene   Feb   Mar   Abr   May   Jun   Jul   Ago   Sep   Oct   Nov   Dic
# ─────────────────────────────────────────────────────────────────────────────
_RAW: Dict[int, List[float]] = {
    # 1 Lácteos — consumo estable; leve alza fin de año (repostería navideña).
    1:  [1.02, 0.98, 0.99, 0.98, 1.02, 0.99, 0.98, 0.99, 1.00, 1.01, 1.05, 1.12],
    # 2 Agricultura — oferta por cosecha altiplano/valle (abr-jul); escasez fin de año.
    2:  [0.90, 0.88, 0.95, 1.12, 1.20, 1.18, 1.12, 1.02, 0.95, 0.92, 0.88, 0.85],
    # 3 Bienes de consumo (canasta) — pico aguinaldo dic + Todos Santos.
    3:  [1.00, 0.95, 0.96, 0.97, 1.03, 0.98, 0.97, 0.99, 1.00, 1.02, 1.08, 1.28],
    # 4 Panadería — pico Todos Santos (nov) + navidad (dic).
    4:  [0.98, 0.96, 0.97, 0.98, 1.02, 0.98, 0.97, 0.99, 1.00, 1.03, 1.22, 1.18],
    # 5 Carnicería — asados fin de año, Día de la Madre; cuaresma baja (abr).
    5:  [1.02, 0.98, 0.97, 0.90, 1.06, 1.00, 0.99, 1.01, 1.00, 1.02, 1.05, 1.24],
    # 6 Verdulería/minimarket — sigue a la cosecha y al consumo de fin de año.
    6:  [1.00, 0.96, 0.98, 1.02, 1.05, 1.02, 0.99, 0.99, 0.99, 1.00, 1.04, 1.18],
    # 7 Otros — perfil casi plano con leve alza diciembre.
    7:  [1.00, 0.98, 0.99, 0.99, 1.01, 0.99, 0.99, 1.00, 1.00, 1.01, 1.03, 1.10],
    # 8 Manufactura alimentaria — producción anticipa fiestas (nov-dic).
    8:  [0.99, 0.96, 0.98, 0.98, 1.02, 0.99, 0.98, 1.00, 1.01, 1.04, 1.12, 1.22],
    # 9 Manufactura general — baja enero (vacaciones), pico pre-fiestas.
    9:  [0.92, 0.97, 1.02, 1.03, 1.04, 1.02, 1.01, 1.03, 1.04, 1.05, 1.06, 1.02],
    # 10 Retail/comercio — el más marcado: aguinaldo dic + Día de la Madre may.
    10: [1.02, 0.94, 0.95, 0.96, 1.08, 0.97, 0.96, 0.98, 1.00, 1.03, 1.10, 1.35],
    # 11 Mayorista — abastece al retail: se adelanta ~1 mes (nov fuerte).
    11: [0.98, 0.95, 0.97, 0.98, 1.05, 0.99, 0.97, 0.99, 1.01, 1.05, 1.18, 1.20],
    # 12 Servicios generales — bastante estable, leve alza fin de año.
    12: [1.00, 0.97, 0.99, 1.00, 1.02, 1.00, 0.99, 1.00, 1.01, 1.01, 1.02, 1.09],
    # 13 Salud — alza en invierno (jun-ago, respiratorias) y baja en fiestas.
    13: [0.98, 0.99, 1.00, 1.02, 1.05, 1.08, 1.09, 1.06, 1.01, 0.98, 0.96, 0.94],
    # 14 Educación — pico inscripción feb-mar; segundo pico mitad de año (jul-ago).
    14: [1.05, 1.28, 1.12, 0.98, 0.94, 0.92, 1.04, 1.10, 0.98, 0.92, 0.88, 0.84],
    # 15 Logística/transporte — sigue al comercio: pico fin de año.
    15: [0.98, 0.95, 0.98, 0.99, 1.04, 0.99, 0.98, 1.00, 1.01, 1.04, 1.10, 1.24],
    # 16 Hotelería/restaurantes — Carnaval (feb), Día de la Madre, fiestas patrias, dic.
    16: [0.98, 1.12, 1.02, 0.96, 1.06, 0.98, 1.02, 1.08, 1.00, 0.98, 1.00, 1.20],
    # 17 Tecnología/software — B2B: gasto se ejecuta fin de año (dic) tras presupuestos.
    17: [0.94, 0.98, 1.02, 1.02, 1.02, 1.00, 1.00, 1.02, 1.03, 1.04, 1.05, 1.18],
    # 18 Construcción — pico estación seca (ago-nov); baja lluvias (ene-mar).
    18: [0.85, 0.86, 0.92, 1.00, 1.06, 1.08, 1.10, 1.14, 1.12, 1.10, 1.04, 0.90],
    # 19 Servicios financieros — colocación de crédito/consumo sube a fin de año.
    19: [0.96, 0.97, 1.00, 1.00, 1.03, 1.00, 0.99, 1.01, 1.02, 1.03, 1.05, 1.16],
}

# Perfiles normalizados a media 1.0 exacta.
BUSINESS_TYPE_SEASONALITY: Dict[int, List[float]] = {
    bt: _normalize(f) for bt, f in _RAW.items()
}

# Perfil neutro (sin estacionalidad) para tipos desconocidos.
FLAT_PROFILE: List[float] = [1.0] * 12


def seasonal_factors(business_type: int) -> List[float]:
    """Devuelve los 12 factores mensuales (media 1.0) del tipo de negocio."""
    return list(BUSINESS_TYPE_SEASONALITY.get(business_type, FLAT_PROFILE))


def monthly_factor(business_type: int, month: int) -> float:
    """Factor estacional para un mes (1=enero … 12=diciembre)."""
    if not 1 <= month <= 12:
        return 1.0
    return seasonal_factors(business_type)[month - 1]


def peak_months(business_type: int, threshold: float = 1.08) -> List[int]:
    """Meses (1..12) cuyo factor supera ``threshold`` — los picos del rubro."""
    return [i + 1 for i, f in enumerate(seasonal_factors(business_type)) if f >= threshold]


def month_labels() -> List[str]:
    return list(_MONTHS)


# ─────────────────────────────────────────────────────────────────────────────
# Señal IPC en vivo (persistida por ``ingest_ine_series`` en el JSON hermano).
# ─────────────────────────────────────────────────────────────────────────────
_JSON_PATH = Path(__file__).resolve().parent / "bolivia_sector_series.json"


def live_ipc() -> Optional[Dict]:
    """
    Última señal del IPC persistida por ``ingest_ine_series`` (o None si no hay
    JSON, si se generó ``--offline``, o si el INE no respondió en ese refresco).
    Claves: period, monthly_pct, annual_pct, accumulated_pct, regional, ...
    """
    try:
        data = json.loads(_JSON_PATH.read_text(encoding="utf-8"))
        return data.get("live_signal", {}).get("ipc") or None
    except Exception:  # noqa: BLE001 — best-effort, nunca rompe el import/uso
        return None


def regional_price_pressure() -> Optional[Dict[str, float]]:
    """
    Presión de precios **relativa** por ciudad, derivada de la variación mensual
    del IPC por ciudad de la última nota del INE: factor = 1 + (var_ciudad −
    var_promedio)/100, media ≈ 1.0. Es una *señal de un mes* (no un nivel de
    precios calibrado): sirve para sesgar costos/precios al expandir el catálogo
    por región, no para reemplazar precios ancla.
    """
    ipc = live_ipc()
    regional = (ipc or {}).get("regional")
    if not regional:
        return None
    mean = sum(regional.values()) / len(regional)
    return {city: round(1 + (pct - mean) / 100, 4) for city, pct in regional.items()}
