"""
Mapeo ciudad → región del IPC + factor de presión de precios por ciudad.
=========================================================================

Traduce los nombres de ciudad usados como ``location`` en el catálogo
(``bolivia_industries``: La Paz, El Alto, Santa Cruz, Cochabamba, Oruro, Tarija)
a las regiones que reporta la nota mensual del IPC del INE, y expone el **factor
de presión de precios** de cada ciudad (media ≈ 1.0) para sembrar variantes
regionales con precios escalados.

Fuente del factor: ``bolivia_sector_series.regional_price_pressure()`` — derivado
de la variación mensual del IPC por ciudad de la última nota del INE. Es una
señal de UN mes (sesgo relativo de precios), no un nivel calibrado.

Notas de mapeo:
* **El Alto** y **La Paz** caen bajo la misma región del IPC, *"Conurbación La
  Paz"* (el INE reporta la conurbación, no los municipios por separado).
* **Cochabamba** → *"Región Metropolitana Kanata"*, que es exactamente la
  conurbación metropolitana de Cochabamba que reporta el INE (Cercado + Quillacollo
  + Sacaba + Colcapirhua + Tiquipaya + Vinto + Sipe Sipe). Usar el dato real de
  Kanata es más fiel que dejar Cochabamba neutral.
* **Santa Cruz** NO aparece en las "mayores variaciones" de la nota del INE y cae
  a **factor 1.0** (sin sesgo), de forma explícita.
* Cualquier ciudad no listada, o si no hay señal IPC persistida, → **1.0**.
"""
from __future__ import annotations

from typing import Dict, Optional

from business.data.bolivia_sector_series import regional_price_pressure

# Nombre de ciudad (``location`` del catálogo) → etiqueta regional del IPC.
# Sólo se mapean las ciudades con dato del INE que queremos aplicar.
CITY_TO_IPC_REGION: Dict[str, str] = {
    "La Paz": "Conurbación La Paz",
    "El Alto": "Conurbación La Paz",
    "Oruro": "Oruro",
    "Potosí": "Potosí",
    "Sucre": "Sucre",
    "Tarija": "Tarija",
    "Cobija": "Cobija",
    "Trinidad": "Trinidad",
    "Cochabamba": "Región Metropolitana Kanata",   # conurbación metropolitana de Cochabamba
    # "Santa Cruz": intencionalmente ausente (sin dato en la nota) → factor 1.0.
}


def city_price_factor(city: str,
                      pressures: Optional[Dict[str, float]] = None) -> float:
    """
    Factor de presión de precios de una ciudad (media ≈ 1.0 entre ciudades).

    Fallback seguro a **1.0** si: no hay señal IPC persistida, la ciudad no está
    mapeada (p.ej. Santa Cruz, Cochabamba), o la región no aparece en la nota.
    ``pressures`` permite inyectar el dict (para tests); si es None se lee de
    ``regional_price_pressure()``.
    """
    if pressures is None:
        pressures = regional_price_pressure()
    if not pressures:
        return 1.0
    region = CITY_TO_IPC_REGION.get((city or "").strip())
    if region is None:
        return 1.0
    return pressures.get(region, 1.0)
