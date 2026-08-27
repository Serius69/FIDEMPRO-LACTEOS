"""Anclas curadas: el último bueno conocido, y nada más que eso.

Estos números son de 2024-2025 (INE / BCB / prensa). NO son observaciones y no
se pueden presentar como tales: existen para que el pipeline no se rompa cuando
KDP no responde, con la política `allow_lkg=true` que Findempro tiene declarada.

Vivían dentro de ``management/commands/scrape_bolivia_data.py``. Se mueven aquí
porque ahora también los necesita la tarea de Celery que consume eventos, y una
tarea programada no debe importar un comando de gestión para leer una constante.
El comando los reexporta, así que nada de lo que ya los importaba se entera.

Quien los use se lleva la etiqueta ``FALLBACK`` puesta — ver
``business.provenance``.
"""
from __future__ import annotations

# Contexto macro de referencia. `fx_usd_bob_official` sigue siendo 6,96 (el peg
# 2011-2025) a propósito: es lo que había, no lo que hay. El oficial real ronda
# los 11,50 y sólo KDP lo observa.
CURATED = {
    "min_wage_month_bs": 2750.0,
    "inflation_annual_pct": 10.0,
    "fx_usd_bob_official": 6.96,
    "fx_usd_bob_parallel": 13.0,
}

# Precios minoristas ancla por producto (Bs). Reflejan cifras de mercado 2025;
# KDP no publica precios minoristas bolivianos, así que estos siguen siendo el
# único origen y se etiquetan FALLBACK de forma permanente.
CURATED_PRICES = {
    "leche_litro": 7.50, "queso_kg": 42.0, "yogur_litro": 17.0,
    "pan_unidad": 0.60, "empanada_unidad": 6.0,
    "carne_res_kg": 60.0, "pollo_kg": 25.0,
    "papa_kg": 4.30, "tomate_kg": 5.20, "arroz_kg": 13.0, "azucar_kg": 7.50,
    "almuerzo": 16.0, "consulta_medica": 150.0,
    "cemento_bolsa": 60.0, "ladrillo_unidad": 1.40,
    "pasaje_urbano": 2.30, "colegio_privado_mes": 900.0, "curso": 200.0,
}

#: Etiqueta con la que viaja un valor tomado de aquí. La cadena literal se
#: conserva porque `bolivia_market_data.json` la lleva escrita desde 2025 y hay
#: consumidores que la comparan; la etiqueta legible va aparte, en
#: ``meta.provenance``.
CURATED_SOURCE = "fallback-curado"
