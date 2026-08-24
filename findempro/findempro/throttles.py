"""Throttles personalizados para FindemproAI."""
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class SimulateThrottle(UserRateThrottle):
    """20 simulaciones/hora — motor Monte Carlo (numpy/CuPy) costoso."""
    scope = 'simulate'


class ReportPdfThrottle(UserRateThrottle):
    """10 PDFs/hora — generación async costosa."""
    scope = 'report_pdf'


class ExportThrottle(UserRateThrottle):
    """30 exportaciones/hora."""
    scope = 'export'


class PublicSimulateThrottle(AnonRateThrottle):
    """Simulador público: anónimo y por IP.

    Va aparte de `simulate` (que es por usuario): el visitante no autenticado no
    tiene identidad que limitar, así que se limita la IP, y más bajo, porque cada
    llamada arranca un Monte Carlo completo sin que nadie haya iniciado sesión.
    """
    scope = 'public_simulate'
