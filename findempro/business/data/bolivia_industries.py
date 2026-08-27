"""
business/data/bolivia_industries.py
===================================
Catálogo de industrias bolivianas para el sembrado multi-sector de FindEMPro.

Cubre los 19 ``Business.BusinessType`` con productos representativos y variables
económicas ancladas en datos reales del mercado boliviano (2024-2025). Incluye
(2026-07) los arquetipos **micro** emblemáticos: confección textil de El Alto,
peluquería, taller mecánico, lavandería, farmacia de barrio, ferretería, puesto
de mercado (comercio informal), agencia de turismo, internet/fotocopias y casa
de cambio (esta última con serie de demanda REAL vía ``import_forex_demand``). Los
valores macro y de precios provienen de fuentes oficiales/prensa y pueden ser
refrescados por el scraper (``manage.py scrape_bolivia_data``), que actualiza
``bolivia_market_data.json`` y sobre-escribe estos anclajes en tiempo de
sembrado.

Anclas macro usadas (ver ``MARKET_CONTEXT``):
  · Salario mínimo nacional: Bs 2.750/mes (2025, DS 5383).
  · Inflación: ~10% (cierre 2024) → ~18% YTD 2025 (INE).
  · Tipo de cambio: Bs 6,96 oficial (BCB) vs ~11-20 paralelo (2025).

Precios minoristas ancla (Bs, 2025): leche 7,5/L · queso 42/kg · pan 0,6/u ·
carne de res 60/kg · pollo 25/kg · papa 4,3/kg · arroz 13/kg · almuerzo 16 ·
cemento 60/bolsa · ladrillo 1,4/u · pasaje urbano 2,3 · colegio privado
900/mes · curso 200. Fuentes: INE, BCB, larazon.bo, vision360.bo, eju.tv,
eldeber.com.bo, ibce.org.bo, SEPREC (base empresarial 387.764 unidades, 2024).

Estacionalidad boliviana (meses pico de venta):
  Alasitas (ene) · Carnaval (feb) · Día de la Madre (may) · Todos Santos (nov) ·
  Navidad + aguinaldo (dic) · cosecha agrícola (abr-jun).
"""
from __future__ import annotations

from business.services.seed_service import IndustrySpec, ProductBaseline as P


# Contexto macro — refrescable por el scraper (bolivia_market_data.json).
MARKET_CONTEXT = {
    "min_wage_month_bs": 2750.0,     # DS 5383 (2025)
    "inflation_annual_pct": 10.0,    # cierre 2024 (INE); YTD 2025 ~18%
    "fx_usd_bob_official": 6.96,     # BCB (fijo desde 2011)
    "fx_usd_bob_parallel": 13.0,     # mercado paralelo 2025 (referencia)
    "source": "seed-baseline",       # 'kdp' cuando lo refresca el consumidor
    "updated": "2025 (curado)",
    # Procedencia por clave. Arranca en FALLBACK para las cuatro anclas porque
    # eso es lo que son mientras nadie las haya observado: valores curados de
    # 2025. `_overlay_scraped_context` las sube a OBSERVED_REAL sólo cuando el
    # JSON del consumidor de KDP lo dice. Sin esta línea, un import en frío
    # entregaría el peg de 2011 sin nada que advirtiera de qué es.
    "provenance": {k: "FALLBACK" for k in (
        "min_wage_month_bs", "inflation_annual_pct",
        "fx_usd_bob_official", "fx_usd_bob_parallel")},
    "freshness": {},
    "freshness_status": "SOURCE_DOWN",
    "data_timestamp": None,
}

# Meses pico reutilizables.
_FESTIVE = [5, 11, 12]        # Día de la Madre, Todos Santos, Navidad
_HARVEST = [4, 5, 6]          # cosecha altiplano
_SCHOOL = [1, 2]             # inicio de año escolar
_DRY_SEASON = [5, 6, 7, 8]    # temporada seca (construcción)


def _spec(bt, name, location, products):
    return IndustrySpec(business_type=bt, business_name=name, location=location, products=products)


# ─────────────────────────────────────────────────────────────────────────────
# 19 industrias × productos representativos con datos bolivianos reales.
# ─────────────────────────────────────────────────────────────────────────────
INDUSTRIES = {

    # 1 — Lácteos
    1: _spec(1, "Láctea Andina PyME", "La Paz", [
        P("Leche", "litros", price=7.50, unit_cost=5.20, daily_demand=2500, daily_clients=85,
          employees=18, monthly_salaries=52200, daily_fixed_cost=800, transport_unit_cost=0.35,
          marketing_monthly=3500, demand_cv=0.10, seasonal=True, peak_months=[1, 12],
          profit_margin=25, description="Leche entera pasteurizada, base del mercado lácteo boliviano."),
        P("Queso Fresco", "kilogramos", price=42.0, unit_cost=30.0, daily_demand=180, daily_clients=70,
          employees=9, monthly_salaries=26100, daily_fixed_cost=320, transport_unit_cost=1.2,
          marketing_monthly=2900, demand_cv=0.14, seasonal=True, peak_months=_FESTIVE,
          profit_margin=28, description="Queso fresco tradicional, alta rotación."),
        P("Yogur", "litros", price=17.0, unit_cost=10.0, daily_demand=330, daily_clients=75,
          employees=10, monthly_salaries=29000, daily_fixed_cost=350, transport_unit_cost=0.6,
          marketing_monthly=3200, demand_cv=0.15, profit_margin=35,
          description="Yogur bebible con cultivos probióticos."),
    ]),

    # 2 — Agricultura
    2: _spec(2, "Agropecuaria Valle Alto", "Cochabamba", [
        P("Papa", "kilogramos", price=4.30, unit_cost=2.60, daily_demand=1200, daily_clients=40,
          employees=8, monthly_salaries=23200, daily_fixed_cost=280, transport_unit_cost=0.30,
          marketing_monthly=800, demand_cv=0.22, seasonal=True, peak_months=_HARVEST,
          profit_margin=18, description="Papa del altiplano; precio volátil por cosecha y bloqueos."),
        P("Tomate", "kilogramos", price=5.20, unit_cost=3.20, daily_demand=600, daily_clients=35,
          employees=5, monthly_salaries=14500, daily_fixed_cost=160, transport_unit_cost=0.35,
          marketing_monthly=800, demand_cv=0.25, seasonal=True, peak_months=_HARVEST,
          profit_margin=20, description="Tomate de valle; alta estacionalidad."),
    ]),

    # 3 — Bienes de Consumo
    3: _spec(3, "Distribuidora Consumo Bolivia", "Santa Cruz", [
        P("Arroz", "kilogramos", price=13.0, unit_cost=10.5, daily_demand=900, daily_clients=120,
          employees=10, monthly_salaries=29000, daily_fixed_cost=330, transport_unit_cost=0.25,
          marketing_monthly=1500, demand_cv=0.10, profit_margin=12,
          description="Arroz envasado, producto de canasta básica."),
        P("Azúcar", "kilogramos", price=7.50, unit_cost=6.0, daily_demand=800, daily_clients=120,
          employees=5, monthly_salaries=14500, daily_fixed_cost=170, transport_unit_cost=0.22,
          marketing_monthly=1500, demand_cv=0.12, seasonal=True, peak_months=_FESTIVE,
          profit_margin=10, description="Azúcar; demanda sube en repostería de fin de año."),
    ]),

    # 4 — Panadería
    4: _spec(4, "Panadería San Jorge", "La Paz", [
        P("Marraqueta", "unidades", price=0.60, unit_cost=0.38, daily_demand=6000, daily_clients=350,
          employees=6, monthly_salaries=17400, daily_fixed_cost=200, transport_unit_cost=0.02,
          marketing_monthly=600, demand_cv=0.09, profit_margin=22,
          description="Pan de batalla subsidiado; altísima rotación diaria."),
        P("Empanada", "unidades", price=6.0, unit_cost=3.2, daily_demand=450, daily_clients=200,
          employees=6, monthly_salaries=17400, daily_fixed_cost=200, transport_unit_cost=0.05,
          marketing_monthly=600, demand_cv=0.16, seasonal=True, peak_months=[11, 12],
          profit_margin=30, description="Empanada de queso; pico en Todos Santos y Navidad."),
        P("Masitas de Todos Santos", "kilogramos", price=45.0, unit_cost=26.0, daily_demand=40,
          daily_clients=60, employees=4, monthly_salaries=11600, daily_fixed_cost=120,
          transport_unit_cost=0.8, marketing_monthly=600, demand_cv=0.30, seasonal=True,
          peak_months=[11], profit_margin=32, description="Masitas y tantawawas; fuerte pico en noviembre."),
    ]),

    # 5 — Carnicería
    5: _spec(5, "Carnicería El Buen Corte", "Santa Cruz", [
        P("Carne de Res", "kilogramos", price=60.0, unit_cost=46.0, daily_demand=220, daily_clients=90,
          employees=14, monthly_salaries=40600, daily_fixed_cost=470, transport_unit_cost=1.0,
          marketing_monthly=1000, demand_cv=0.15, seasonal=True, peak_months=_FESTIVE,
          profit_margin=18, description="Carne de res de mostrador; precio +50% en 2025."),
        P("Pollo", "kilogramos", price=25.0, unit_cost=19.0, daily_demand=300, daily_clients=110,
          employees=8, monthly_salaries=23200, daily_fixed_cost=270, transport_unit_cost=0.6,
          marketing_monthly=1000, demand_cv=0.18, profit_margin=20,
          description="Pollo faenado; precio volátil (pico Bs 29,5 en jun-2025)."),
    ]),

    # 6 — Verdulería / Minimarket
    6: _spec(6, "Minimarket Doña Rosa", "El Alto", [
        P("Abarrotes Varios", "unidades", price=9.0, unit_cost=7.2, daily_demand=550, daily_clients=180,
          employees=5, monthly_salaries=14500, daily_fixed_cost=150, transport_unit_cost=0.15,
          marketing_monthly=400, demand_cv=0.12, profit_margin=15,
          description="Canasta de abarrotes de barrio; ticket promedio bajo, alto flujo."),
        P("Verduras", "kilogramos", price=6.0, unit_cost=4.3, daily_demand=280, daily_clients=150,
          employees=2, monthly_salaries=5800, daily_fixed_cost=70, transport_unit_cost=0.20,
          marketing_monthly=400, demand_cv=0.20, seasonal=True, peak_months=_HARVEST,
          profit_margin=18, description="Verduras frescas; precio ligado a cosecha."),
    ]),

    # 7 — Otros (servicio genérico)
    7: _spec(7, "Servicios Generales Bolivia", "Cochabamba", [
        P("Servicio General", "servicios", price=120.0, unit_cost=70.0, daily_demand=25, daily_clients=25,
          employees=6, monthly_salaries=17400, daily_fixed_cost=200, transport_unit_cost=2.0,
          marketing_monthly=1200, demand_cv=0.18, profit_margin=25,
          description="Servicio genérico multiuso para PyME no clasificada."),
        P("Internet y Fotocopias", "servicios", price=3.0, unit_cost=1.2, daily_demand=120, daily_clients=90,
          employees=1, monthly_salaries=2900, daily_fixed_cost=95, transport_unit_cost=0.0,
          marketing_monthly=60, demand_cv=0.14, seasonal=True, peak_months=_SCHOOL,
          profit_margin=40, description="Punto de barrio (micro): impresiones, fotocopias y cabina de internet; pico escolar."),
    ]),

    # 8 — Manufactura Alimentaria
    8: _spec(8, "Alimentos Procesados del Sur", "Tarija", [
        P("Fideos", "kilogramos", price=11.0, unit_cost=7.5, daily_demand=700, daily_clients=90,
          employees=10, monthly_salaries=29000, daily_fixed_cost=370, transport_unit_cost=0.30,
          marketing_monthly=3400, demand_cv=0.11, profit_margin=20,
          description="Fideos envasados; producción industrial continua."),
        P("Mermelada", "unidades", price=18.0, unit_cost=11.0, daily_demand=200, daily_clients=70,
          employees=6, monthly_salaries=17400, daily_fixed_cost=210, transport_unit_cost=0.5,
          marketing_monthly=2000, demand_cv=0.16, seasonal=True, peak_months=_FESTIVE,
          profit_margin=28, description="Mermelada de frutas del valle tarijeño."),
    ]),

    # 9 — Manufactura General
    9: _spec(9, "Manufacturas Illimani", "El Alto", [
        P("Muebles de Melamina", "unidades", price=850.0, unit_cost=560.0, daily_demand=8, daily_clients=8,
          employees=9, monthly_salaries=26100, daily_fixed_cost=340, transport_unit_cost=35.0,
          marketing_monthly=3100, demand_cv=0.20, seasonal=True, peak_months=[11, 12],
          profit_margin=22, description="Muebles a pedido; pico por aguinaldo de fin de año."),
        P("Puertas Metálicas", "unidades", price=1200.0, unit_cost=820.0, daily_demand=5, daily_clients=5,
          employees=8, monthly_salaries=23200, daily_fixed_cost=270, transport_unit_cost=50.0,
          marketing_monthly=2500, demand_cv=0.22, profit_margin=24,
          description="Puertas y portones metálicos para vivienda."),
        P("Prenda de Confección", "unidades", price=38.0, unit_cost=22.0, daily_demand=60, daily_clients=12,
          employees=4, monthly_salaries=11600, daily_fixed_cost=150, transport_unit_cost=0.5,
          marketing_monthly=700, demand_cv=0.22, seasonal=True, peak_months=[1, 2, 12],
          profit_margin=30, description="Taller textil de El Alto (micro): poleras/uniformes al por mayor; picos escolar y navideño."),
    ]),

    # 10 — Retail / Comercio
    10: _spec(10, "Comercial La Cancha", "Cochabamba", [
        P("Ropa Casual", "unidades", price=70.0, unit_cost=45.0, daily_demand=90, daily_clients=110,
          employees=10, monthly_salaries=29000, daily_fixed_cost=350, transport_unit_cost=1.5,
          marketing_monthly=2500, demand_cv=0.20, seasonal=True, peak_months=_FESTIVE,
          profit_margin=30, description="Prenda casual de mercado; picos en Día de la Madre y Navidad."),
        P("Calzado", "unidades", price=180.0, unit_cost=120.0, daily_demand=40, daily_clients=70,
          employees=11, monthly_salaries=31900, daily_fixed_cost=380, transport_unit_cost=3.0,
          marketing_monthly=2500, demand_cv=0.22, seasonal=True, peak_months=_FESTIVE,
          profit_margin=28, description="Calzado importado y nacional."),
        P("Artículos de Ferretería", "unidades", price=55.0, unit_cost=38.0, daily_demand=35, daily_clients=35,
          employees=3, monthly_salaries=8700, daily_fixed_cost=160, transport_unit_cost=1.0,
          marketing_monthly=600, demand_cv=0.16, seasonal=True, peak_months=_DRY_SEASON,
          profit_margin=25, description="Ferretería de barrio (ticket promedio); sigue a la construcción en temporada seca."),
        P("Venta de Puesto de Mercado", "unidades", price=15.0, unit_cost=10.0, daily_demand=80, daily_clients=80,
          employees=1, monthly_salaries=2750, daily_fixed_cost=45, transport_unit_cost=0.3,
          marketing_monthly=50, demand_cv=0.18, seasonal=True, peak_months=_FESTIVE,
          profit_margin=25, description="Comercio informal gremial (micro): puesto de mercado, ticket bajo y alta rotación."),
    ]),

    # 11 — Mayorista
    11: _spec(11, "Distribuidora Mayorista Oriente", "Santa Cruz", [
        P("Aceite (caja)", "unidades", price=95.0, unit_cost=82.0, daily_demand=140, daily_clients=45,
          employees=7, monthly_salaries=20300, daily_fixed_cost=240, transport_unit_cost=2.5,
          marketing_monthly=2000, demand_cv=0.10, profit_margin=9,
          description="Venta al por mayor de aceite; márgenes bajos, alto volumen."),
        P("Bebidas (caja)", "unidades", price=48.0, unit_cost=40.0, daily_demand=260, daily_clients=60,
          employees=8, monthly_salaries=23200, daily_fixed_cost=270, transport_unit_cost=1.8,
          marketing_monthly=2000, demand_cv=0.14, seasonal=True, peak_months=[2, 12],
          profit_margin=11, description="Distribución de bebidas; pico en Carnaval y Navidad."),
    ]),

    # 12 — Servicios Generales
    12: _spec(12, "Multiservicios Kollasuyo", "La Paz", [
        P("Servicio de Limpieza", "servicios", price=350.0, unit_cost=210.0, daily_demand=14, daily_clients=14,
          employees=9, monthly_salaries=26100, daily_fixed_cost=300, transport_unit_cost=8.0,
          marketing_monthly=1800, demand_cv=0.15, profit_margin=25,
          description="Servicio de limpieza a empresas y hogares por contrato."),
        P("Mantenimiento", "servicios", price=280.0, unit_cost=160.0, daily_demand=10, daily_clients=10,
          employees=5, monthly_salaries=14500, daily_fixed_cost=180, transport_unit_cost=10.0,
          marketing_monthly=1600, demand_cv=0.18, profit_margin=28,
          description="Mantenimiento general y reparaciones."),
        P("Corte de Cabello", "servicios", price=25.0, unit_cost=5.0, daily_demand=18, daily_clients=18,
          employees=2, monthly_salaries=5800, daily_fixed_cost=90, transport_unit_cost=0.0,
          marketing_monthly=300, demand_cv=0.15, seasonal=True, peak_months=_FESTIVE,
          profit_margin=45, description="Peluquería/salón de barrio (micro); picos antes de festividades."),
        P("Reparación Mecánica", "servicios", price=180.0, unit_cost=95.0, daily_demand=6, daily_clients=6,
          employees=3, monthly_salaries=9500, daily_fixed_cost=140, transport_unit_cost=2.0,
          marketing_monthly=500, demand_cv=0.20, profit_margin=30,
          description="Taller mecánico automotriz (micro): mano de obra + repuestos menores por servicio."),
        P("Lavado de Ropa", "kilogramos", price=12.0, unit_cost=5.0, daily_demand=45, daily_clients=15,
          employees=2, monthly_salaries=5800, daily_fixed_cost=110, transport_unit_cost=0.0,
          marketing_monthly=250, demand_cv=0.16, profit_margin=38,
          description="Lavandería de barrio (micro): Bs/kg lavado y secado."),
    ]),

    # 13 — Salud
    13: _spec(13, "Centro Médico Vida Sana", "Santa Cruz", [
        P("Consulta Médica", "servicios", price=150.0, unit_cost=70.0, daily_demand=35, daily_clients=35,
          employees=14, monthly_salaries=40600, daily_fixed_cost=460, transport_unit_cost=0.0,
          marketing_monthly=2000, demand_cv=0.12, profit_margin=30,
          description="Consulta médica particular; sin costo de transporte por unidad."),
        P("Análisis de Laboratorio", "servicios", price=90.0, unit_cost=45.0, daily_demand=50, daily_clients=45,
          employees=11, monthly_salaries=31900, daily_fixed_cost=370, transport_unit_cost=0.0,
          marketing_monthly=2000, demand_cv=0.14, profit_margin=32,
          description="Exámenes de laboratorio clínico."),
        P("Venta de Medicamentos", "unidades", price=35.0, unit_cost=26.0, daily_demand=95, daily_clients=85,
          employees=3, monthly_salaries=9800, daily_fixed_cost=200, transport_unit_cost=0.0,
          marketing_monthly=400, demand_cv=0.10, profit_margin=22,
          description="Farmacia de barrio (micro): ~95 tickets/día de Bs 35; validado rentable por validate_catalog."),
    ]),

    # 14 — Educación
    14: _spec(14, "Instituto Saber Más", "La Paz", [
        P("Mensualidad Colegio", "servicios", price=900.0, unit_cost=560.0, daily_demand=18, daily_clients=18,
          employees=18, monthly_salaries=52200, daily_fixed_cost=1010, transport_unit_cost=0.0,
          marketing_monthly=3000, demand_cv=0.08, seasonal=True, peak_months=_SCHOOL,
          profit_margin=22, description="Mensualidad de colegio privado; matrícula pico en feb."),
        P("Curso Corto", "servicios", price=200.0, unit_cost=95.0, daily_demand=25, daily_clients=25,
          employees=12, monthly_salaries=34800, daily_fixed_cost=430, transport_unit_cost=0.0,
          marketing_monthly=3000, demand_cv=0.18, seasonal=True, peak_months=[1, 2, 7],
          profit_margin=35, description="Cursos cortos y diplomados; picos por temporada."),
    ]),

    # 15 — Logística / Transporte
    15: _spec(15, "TransCarga Andes", "Oruro", [
        P("Flete Urbano", "servicios", price=120.0, unit_cost=75.0, daily_demand=30, daily_clients=30,
          employees=3, monthly_salaries=8700, daily_fixed_cost=100, transport_unit_cost=25.0,
          marketing_monthly=900, demand_cv=0.16, profit_margin=20,
          description="Fletes urbanos; costo de combustible/diésel relevante."),
        P("Encomienda Interdepartamental", "servicios", price=45.0, unit_cost=28.0, daily_demand=120,
          daily_clients=120, employees=3, monthly_salaries=8700, daily_fixed_cost=100,
          transport_unit_cost=12.0, marketing_monthly=900, demand_cv=0.14, seasonal=True,
          peak_months=_FESTIVE, profit_margin=22, description="Envío de encomiendas entre ciudades."),
    ]),

    # 16 — Hotelería / Restaurantes
    16: _spec(16, "Restaurante Sabor Paceño", "La Paz", [
        P("Almuerzo del Día", "servicios", price=16.0, unit_cost=9.5, daily_demand=180, daily_clients=180,
          employees=5, monthly_salaries=14500, daily_fixed_cost=190, transport_unit_cost=0.10,
          marketing_monthly=1500, demand_cv=0.12, seasonal=True, peak_months=[2, 5],
          profit_margin=25, description="Menú del día; picos en Carnaval y Día de la Madre."),
        P("Plato a la Carta", "servicios", price=45.0, unit_cost=24.0, daily_demand=70, daily_clients=70,
          employees=7, monthly_salaries=20300, daily_fixed_cost=240, transport_unit_cost=0.15,
          marketing_monthly=1500, demand_cv=0.18, seasonal=True, peak_months=[5, 12],
          profit_margin=30, description="Platos a la carta; mayor ticket en fechas festivas."),
        P("Tour Turístico", "servicios", price=320.0, unit_cost=190.0, daily_demand=9, daily_clients=9,
          employees=4, monthly_salaries=12200, daily_fixed_cost=220, transport_unit_cost=15.0,
          marketing_monthly=1800, demand_cv=0.30, seasonal=True, peak_months=[6, 7, 8],
          profit_margin=28, description="Agencia de turismo (micro): tours de día; temporada alta invierno (jun-ago)."),
    ]),

    # 17 — Tecnología / Software
    17: _spec(17, "Kapitalya Dev Studio", "Cochabamba", [
        P("Hora de Desarrollo", "servicios", price=120.0, unit_cost=55.0, daily_demand=40, daily_clients=6,
          employees=12, monthly_salaries=34800, daily_fixed_cost=430, transport_unit_cost=0.0,
          marketing_monthly=2500, demand_cv=0.15, profit_margin=35,
          description="Hora de desarrollo de software (~USD 10-25/h)."),
        P("Suscripción SaaS", "servicios", price=280.0, unit_cost=90.0, daily_demand=12, daily_clients=12,
          employees=11, monthly_salaries=31900, daily_fixed_cost=380, transport_unit_cost=0.0,
          marketing_monthly=2500, demand_cv=0.10, profit_margin=45,
          description="Suscripción mensual a producto SaaS; ingreso recurrente."),
    ]),

    # 18 — Construcción
    18: _spec(18, "Constructora Pachamama", "Santa Cruz", [
        P("Bolsa de Cemento", "unidades", price=60.0, unit_cost=48.0, daily_demand=350, daily_clients=40,
          employees=18, monthly_salaries=52200, daily_fixed_cost=610, transport_unit_cost=1.5,
          marketing_monthly=3000, demand_cv=0.14, seasonal=True, peak_months=_DRY_SEASON,
          profit_margin=15, description="Cemento; obra concentrada en temporada seca."),
        P("Millar de Ladrillos", "unidades", price=1400.0, unit_cost=1050.0, daily_demand=6, daily_clients=6,
          employees=8, monthly_salaries=23200, daily_fixed_cost=290, transport_unit_cost=60.0,
          marketing_monthly=2600, demand_cv=0.18, seasonal=True, peak_months=_DRY_SEASON,
          profit_margin=18, description="Ladrillo gambote por millar (Bs 1,2-1,7/u)."),
    ]),

    # 19 — Servicios Financieros
    19: _spec(19, "Cooperativa Crédito Ágil", "La Paz", [
        P("Microcrédito", "servicios", price=450.0, unit_cost=250.0, daily_demand=20, daily_clients=20,
          employees=18, monthly_salaries=52200, daily_fixed_cost=660, transport_unit_cost=0.0,
          marketing_monthly=3500, demand_cv=0.12, profit_margin=30,
          description="Comisión/interés por colocación de microcrédito a PyME."),
        P("Seguro PyME", "servicios", price=320.0, unit_cost=190.0, daily_demand=14, daily_clients=14,
          employees=8, monthly_salaries=23200, daily_fixed_cost=300, transport_unit_cost=0.0,
          marketing_monthly=2700, demand_cv=0.14, profit_margin=28,
          description="Prima mensual de microseguro para pequeños negocios."),
        # Anclado al dataset REAL de operaciones de casa de cambio (forex-erp,
        # jul-2025→jun-2026: 12,5 ops/día, ~Bs 4.325/op → comisión ~1,5%).
        # `import_forex_demand` reemplaza su demanda sintética por la serie real.
        P("Cambio de Divisas", "servicios", price=65.0, unit_cost=20.0, daily_demand=12.5,
          daily_clients=12, employees=3, monthly_salaries=8700, daily_fixed_cost=180,
          transport_unit_cost=0.0, marketing_monthly=900, demand_cv=0.21, profit_margin=45,
          description="Comisión por operación de cambio USD/EUR/etc. (casa de cambio)."),
    ]),
}


def all_specs():
    """Devuelve la lista de IndustrySpec de las 19 industrias."""
    return list(INDUSTRIES.values())


def get_spec(business_type: int):
    return INDUSTRIES.get(business_type)


def _overlay_scraped_context(path=None):
    """Superpone sobre MARKET_CONTEXT lo que escribió el consumidor de KDP.

    Best-effort: nunca rompe el import. Pero best-effort NO significa que un
    valor pueda entrar sin etiqueta — si el JSON trae un número sin procedencia,
    se toma como FALLBACK, que es lo que un valor sin procedencia es en el mejor
    de los casos. Ver ``business.provenance``.
    """
    import json
    from pathlib import Path
    path = Path(path) if path else Path(__file__).resolve().parent / "bolivia_market_data.json"
    try:
        if not path.exists():
            return
        data = json.loads(path.read_text(encoding="utf-8"))
        macro = data.get("macro", {})
        meta = data.get("meta", {}) or {}
        procedencia = meta.get("provenance", {}) or {}
        for key in ("min_wage_month_bs", "inflation_annual_pct",
                    "fx_usd_bob_official", "fx_usd_bob_parallel"):
            if key in macro and isinstance(macro[key], (int, float)):
                MARKET_CONTEXT[key] = macro[key]
                # La etiqueta viaja PEGADA al valor: se escriben juntos o no se
                # escribe ninguno. Separarlos es exactamente cómo un curado
                # acaba leyéndose como medición tres capas más arriba.
                MARKET_CONTEXT["provenance"][key] = procedencia.get(key, "FALLBACK")
        # La procedencia viaja por campo, no como una etiqueta global: cada ancla
        # puede venir de una fuente distinta (kdp:dolarapi-bo, kdp:criptoya-bo,
        # kdp-event:bcb-semanal-bulk) o seguir siendo el valor curado. Decir
        # "scraped" para todas volvía invisible cuál era cuál.
        fuentes = meta.get("sources", {}) or {}
        MARKET_CONTEXT["sources"] = dict(fuentes)
        MARKET_CONTEXT["freshness"] = dict(meta.get("freshness", {}) or {})
        MARKET_CONTEXT["freshness_status"] = meta.get("freshness_status", "SOURCE_DOWN")
        MARKET_CONTEXT["data_timestamp"] = meta.get("data_timestamp")
        MARKET_CONTEXT["source"] = (
            "kdp" if any(str(v).startswith("kdp") for v in fuentes.values())
            else "scraped" if fuentes else "seed-baseline")
        MARKET_CONTEXT["updated"] = meta.get("generated_by", "scraper")
        MARKET_CONTEXT["generated_at"] = meta.get("generated_at")
    except Exception:  # noqa: BLE001
        pass


_overlay_scraped_context()
