"""
Middleware de cabeceras de seguridad a nivel de aplicación.
==========================================================

Emite ``Content-Security-Policy`` y ``Permissions-Policy`` en TODAS las
respuestas servidas por Django, con independencia de las rarezas de herencia de
``add_header`` de nginx (donde un ``add_header`` en un ``location`` hijo anula
los del bloque ``http{}`` padre — por eso la CSP definida en nginx nunca llegaba
a emitirse en `/`, `/api/` ni en el resto del HTML dinámico).

La CSP se toma de ``settings.CONTENT_SECURITY_POLICY`` (vacío = no se emite,
útil para rollback inmediato). La política por defecto está orientada a la SPA
y no permite scripts de terceros. Django ya emite X-Frame-Options, nosniff,
Referrer-Policy y COOP vía SecurityMiddleware/XFrameOptionsMiddleware; aquí solo
añadimos lo que falta.
"""
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Añade CSP + Permissions-Policy sin pisar cabeceras ya presentes."""

    def process_response(self, request, response):
        csp = getattr(settings, "CONTENT_SECURITY_POLICY", "")
        if csp and "Content-Security-Policy" not in response:
            response["Content-Security-Policy"] = csp

        permissions = getattr(
            settings, "PERMISSIONS_POLICY",
            "camera=(), microphone=(), geolocation=(), interest-cohort=()",
        )
        if permissions and "Permissions-Policy" not in response:
            response["Permissions-Policy"] = permissions

        return response
