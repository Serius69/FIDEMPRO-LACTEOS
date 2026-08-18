# Sembrado multi-industria boliviano — FindemproAI

Deja el sistema **listo para funcionar con datos** para los **19 tipos de empresa**
de Bolivia (antes sólo existía el caso lácteo, `type=1`, hardcodeado). Cada tipo
recibe negocios, productos, variables, ecuaciones, cuestionario y respuestas
(incluido histórico de demanda) **listos para simular**.

## Idea de diseño

El motor de simulación (181 variables / 91 ecuaciones / 14 áreas) es **genérico**:
modela ingresos, costos, inventario y márgenes de *cualquier* PyME; sólo era
"lácteo" en sus valores de ejemplo. Por eso el sembrado **reutiliza esa estructura
de motor ya validada** (los mismos helpers del onboarding) y **parametriza los
valores económicos** (precio, costo, demanda, estacionalidad) por industria, con
datos reales del mercado boliviano 2024-2025.

```
Business (tipo N)
  └─ por cada Producto de la industria:
       Product → Áreas + Variables + Ecuaciones + Cuestionario   (helpers validados)
       QuestionaryResult → Answers  (generadas desde el baseline boliviano del producto)
  └─ ProbabilisticDensityFunction (Normal, media = demanda del producto ancla)
```

## Componentes

| Archivo | Rol |
|---|---|
| `business/data/bolivia_industries.py` | Catálogo de los 19 tipos con productos y variables ancladas en cifras bolivianas. `MARKET_CONTEXT` (macro). |
| `business/data/bolivia_market_data.json` | Datos macro/precios producidos por el scraper (se superpone sobre `MARKET_CONTEXT`). |
| `business/services/seed_service.py` | `ProductBaseline`, `IndustrySpec`, `generate_answers()`, `IndustrySeeder` (idempotente, transaccional). |
| `business/management/commands/seed_bolivia.py` | Comando de sembrado. |
| `business/management/commands/scrape_bolivia_data.py` | Scraper best-effort (BCB/INE) con fallback curado. |

## Uso

```bash
# 1) (Opcional) refrescar datos macro reales del mercado boliviano
python manage.py scrape_bolivia_data            # escribe bolivia_market_data.json
python manage.py scrape_bolivia_data --dry-run  # sólo muestra

# 2) One-click: un negocio demo + simulación persistida (seed 42)
python manage.py seed_bolivia

# Variantes
python manage.py seed_bolivia --no-run-sim       # sólo elementos
python manage.py seed_bolivia --types 4,5,16     # sólo algunos tipos
python manage.py seed_bolivia --types 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19
python manage.py seed_bolivia --user sergio      # asignar a un usuario existente
python manage.py seed_bolivia --force            # recrea aunque ya exista
```

El comando es **idempotente**: no duplica un negocio del mismo tipo para el mismo
usuario ni vuelve a ejecutar una simulación ya completada (salvo `--force`).

### Onboarding web (selector de rubro)

La pantalla de configuración inicial (`register-elements/`) incluye un `<select>` con
los 19 tipos. Al confirmar, `pages/views/create_elements.py::register_elements_create`
rutea al `IndustrySeeder` del tipo elegido (mismo camino que el comando). Si no se elige
tipo, cae al flujo lácteo legacy (retrocompatible). Así un usuario final crea su negocio
del rubro que corresponda, con productos y variables bolivianas, sin usar la CLI.

## Datos y fuentes

Anclas macro (curadas, refrescables por el scraper): salario mínimo **Bs 2.750/mes**
(DS 5383, 2025), inflación ~**10 %** (cierre 2024, INE), tipo de cambio **Bs 6,96**
oficial (BCB) vs ~**11-20** paralelo. Precios minoristas ancla (Bs, 2025): leche 7,5/L,
queso 42/kg, pan 0,6/u, carne de res 60/kg, pollo 25/kg, papa 4,3/kg, arroz 13/kg,
almuerzo 16, cemento 60/bolsa, colegio privado 900/mes, hora de desarrollo 120.
Estacionalidad: Alasitas (ene), Carnaval (feb), Día de la Madre (may), Todos Santos
(nov), Navidad + aguinaldo (dic), cosecha agrícola (abr-jun).
Fuentes: INE, BCB, SEPREC, larazon.bo, vision360.bo, eju.tv, eldeber.com.bo, ibce.org.bo.

## El scraper

`scrape_bolivia_data` intenta leer en vivo el tipo de cambio (BCB) y la inflación
anual (INE) y consolida todo en `bolivia_market_data.json`. Es **best-effort**: si
una fuente no responde o cambia su HTML, conserva el valor curado y marca la fuente
como `fallback-curado` — el pipeline **nunca se rompe** por un sitio caído. La
inflación exige contexto anual ("acumulada/12 meses") para no confundir la variación
mensual (~2 %) con la anual.

## Cobertura (19 tipos, 39 productos)

Lácteos · Agricultura · Bienes de Consumo · Panadería · Carnicería ·
Verdulería/Minimarket · Otros · Manufactura Alimentaria · Manufactura General ·
Retail · Mayorista · Servicios · Salud · Educación · Logística · Hotelería/Restaurantes ·
Tecnología/Software · Construcción · Servicios Financieros.

## Calibración de rentabilidad (overhead por línea)

La simulación corre **un producto a la vez**, pero el cuestionario de cada producto
carga el costo fijo del negocio (salarios, costo fijo diario, marketing). Si ese
overhead se dimensiona para un negocio multiproducto, una sola línea queda en
pérdida. Por eso los campos `employees` / `monthly_salaries` / `daily_fixed_cost` /
`marketing_monthly` de cada `ProductBaseline` representan la **carga de esa línea**,
calibrada a un costo fijo ≈ 66 % del margen bruto diario (≈ salario mínimo/empleado,
tope 18 empleados/línea). Resultado: los **19 tipos simulan utilidad positiva** con
márgenes netos realistas y por sector — commodity/mayoreo finos (arroz, aceite,
cemento ~4-6 %), retail/comida medios (10-16 %), servicios/software/educación más
altos (17-22 %). Precios, costos y demandas **no** se tocaron en la calibración.

## Verificación

- `business/tests/test_seed_bolivia.py`: catálogo cubre los 19 tipos, `generate_answers`
  produce histórico ≥30 pts, sembrado construye la cadena completa, idempotencia,
  `--force` recrea sin chocar con el `UNIQUE(name, fk_user)` NOCASE, y tests `slow`
  que corren el pipeline Monte Carlo end-to-end (ingreso **y utilidad** positivos).
- Verificado sobre los 19 tipos sembrados (Monte Carlo, 80 escenarios): 19 ingresos
  distintos y **utilidad diaria positiva en todos** (p.ej. lácteos +Bs 5.566, colegio
  +6.711, fideos +753, cemento +712, flete +884, restaurante +640).
