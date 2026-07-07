"""Throttles personalizados para FindemproAI."""
from rest_framework.throttling import UserRateThrottle


class SimulateThrottle(UserRateThrottle):
    """20 simulaciones/hora — TensorFlow inference + Monte Carlo."""
    scope = 'simulate'


class ReportPdfThrottle(UserRateThrottle):
    """10 PDFs/hora — generación async costosa."""
    scope = 'report_pdf'


class ExportThrottle(UserRateThrottle):
    """30 exportaciones/hora."""
    scope = 'export'
