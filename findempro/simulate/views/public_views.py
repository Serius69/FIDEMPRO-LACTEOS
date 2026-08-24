"""
public_views.py
===============
Superficie **pública y sin estado** del simulador.

Política: se permite cálculo anónimo sobre datos que el propio llamante envía.
NO se permite estado de cliente ni de inquilino: este endpoint no lee ni escribe
`Business`, `Simulation` ni nada del usuario, no acepta identificadores de
recursos y no persiste la petición. Todo lo que necesita viene en el cuerpo, y
lo que devuelve se calcula y se olvida.

  POST /api/simulate/montecarlo/  — proyección Monte Carlo de utilidad mensual
"""

import logging

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from findempro.throttles import PublicSimulateThrottle
from simulate.services.simulation_engine import MonteCarloEngine, SimulationConfig

logger = logging.getLogger(__name__)


# Perfil por sector: margen bruto típico y variabilidad de la demanda. Es la misma
# idea que `SectorTemplate` del producto consolidado —el sector es configuración,
# no un fork—, reducida a lo que este cálculo público necesita.
PERFILES_SECTOR = {
    'comercio':    {'margen': 0.25, 'cv': 0.20},
    'servicios':   {'margen': 0.45, 'cv': 0.18},
    'manufactura': {'margen': 0.30, 'cv': 0.25},
    'alimentos':   {'margen': 0.22, 'cv': 0.30},
    'lacteo':      {'margen': 0.18, 'cv': 0.35},
    'generico':    {'margen': 0.25, 'cv': 0.22},
}
SECTOR_POR_DEFECTO = 'generico'

# Topes: el endpoint es anónimo, así que el coste de una petición tiene que estar
# acotado por construcción y no depender de la buena fe del llamante.
MAX_SIMULACIONES = 20_000
MAX_HORIZONTE = 60
MAX_MONTO = 1e12


def _numero(valor, nombre, *, minimo=0.0, maximo=MAX_MONTO):
    """Convierte a float finito dentro de rango, o explica por qué no se puede."""
    if isinstance(valor, bool) or valor is None:
        raise ValueError(f"{nombre} es obligatorio y debe ser un número.")
    try:
        n = float(valor)
    except (TypeError, ValueError):
        raise ValueError(f"{nombre} debe ser un número.")
    if n != n or n in (float('inf'), float('-inf')):
        raise ValueError(f"{nombre} debe ser un número finito.")
    if not (minimo <= n <= maximo):
        raise ValueError(f"{nombre} debe estar entre {minimo:g} y {maximo:g}.")
    return n


class PublicMonteCarloAPIView(APIView):
    """Proyección de utilidad a partir de lo que el visitante declara.

    El onboarding público llamaba a esta ruta desde el primer día
    (`frontend/src/pages/OnboardingPage.tsx`) y no existía en el backend: la
    única simulación que un visitante sin cuenta podía lanzar terminaba en 404
    y se le mostraba como "no pudimos calcular tu proyección".
    """

    permission_classes = [AllowAny]
    throttle_classes = [PublicSimulateThrottle]

    def post(self, request):
        datos = request.data if isinstance(request.data, dict) else {}

        try:
            ventas_mes = _numero(datos.get('ventas_mes'), 'ventas_mes')
            gastos_fijos = _numero(datos.get('gastos_fijos'), 'gastos_fijos')
            horizonte = int(_numero(datos.get('horizonte', 12), 'horizonte',
                                    minimo=1, maximo=MAX_HORIZONTE))
            simulaciones = int(_numero(datos.get('simulaciones', 5000), 'simulaciones',
                                       minimo=1, maximo=MAX_SIMULACIONES))
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        sector = str(datos.get('tipo_negocio') or SECTOR_POR_DEFECTO).strip().lower()
        perfil = PERFILES_SECTOR.get(sector, PERFILES_SECTOR[SECTOR_POR_DEFECTO])

        # La demanda se modela en unidades monetarias de venta (precio unitario 1),
        # que es lo que el visitante sabe declarar: cuánto vende al mes. El coste
        # unitario sale del margen del sector.
        config = SimulationConfig(
            n_iterations=simulaciones,
            time_periods=horizonte,
            distribution_type='lognormal',   # la venta no puede ser negativa
            demand_mean=ventas_mes,
            demand_std=max(ventas_mes * perfil['cv'], 1e-6),
            unit_price=1.0,
            unit_cost=1.0 - perfil['margen'],
            fixed_costs=gastos_fijos,
        )

        try:
            resultado = MonteCarloEngine(config).run()
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            logger.exception('Simulación pública fallida')
            return Response({'error': 'No se pudo completar la simulación.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'p5': resultado.profit_p5,
            'p50': resultado.profit_median,
            'p95': resultado.profit_p95,
            'probabilidad_perdida': resultado.probability_of_loss,
            'sector_aplicado': sector if sector in PERFILES_SECTOR else SECTOR_POR_DEFECTO,
            'horizonte_meses': horizonte,
            'simulaciones': simulaciones,
            'unidad': 'utilidad mensual',
            # Sin cuenta no hay nada que guardar, y conviene decirlo: el visitante
            # no debe suponer que su proyección quedó archivada en alguna parte.
            'persistido': False,
        }, status=status.HTTP_200_OK)
