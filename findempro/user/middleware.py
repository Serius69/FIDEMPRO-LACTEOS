"""
Middleware mejorado para el sistema de usuarios
Incluye registro de actividades, sesiones y seguridad
"""

import logging
import time
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.conf import settings
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.contrib.sessions.models import Session
from .models import ActivityLog, UserSession
import json

logger = logging.getLogger(__name__)


class ActivityLogMiddleware:
    """Middleware para registrar actividades del usuario"""
    
    # Rutas que no requieren logging
    EXCLUDED_PATHS = [
        '/static/',
        '/media/',
        '/favicon.ico',
        '/admin/jsi18n/',
        '/api/health/',
    ]
    
    # Métodos HTTP que se registran
    LOGGED_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Procesar request
        start_time = time.time()
        
        response = self.get_response(request)
        
        # Registrar actividad después del response
        if self.should_log_activity(request, response):
            self.log_activity(request, response, start_time)

        return response

    def should_log_activity(self, request, response):
        """Determinar si se debe registrar la actividad"""
        # No registrar si el usuario no está autenticado
        if not request.user.is_authenticated:
            return False
        
        # No registrar rutas excluidas
        for excluded_path in self.EXCLUDED_PATHS:
            if request.path.startswith(excluded_path):
                return False
        
        # Registrar solo métodos específicos o responses con errores
        if request.method in self.LOGGED_METHODS or response.status_code >= 400:
            return True
        
        # Registrar navegación importante (GET a páginas específicas)
        important_paths = [
            '/profile/',
            '/settings/',
            '/admin/',
            '/dashboard/',
        ]
        
        if request.method == 'GET':
            for path in important_paths:
                if request.path.startswith(path):
                    return True
        
        return False

    def log_activity(self, request, response, start_time):
        """Registrar la actividad"""
        try:
            # Calcular tiempo de respuesta
            response_time = round((time.time() - start_time) * 1000, 2)
            
            # Determinar acción basada en método y ruta
            action = self.get_action_description(request)
            
            # Obtener detalles adicionales
            details = self.get_activity_details(request, response, response_time)
            
            # Determinar prioridad basada en el status code
            priority = self.get_priority_from_status(response.status_code)
            
            # Obtener categoría
            category = self.get_category_from_path(request.path)
            
            # Registrar actividad
            ActivityLog.log_activity(
                user=request.user,
                action=action,
                details=details,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                priority=priority,
                category=category
            )
            
        except Exception as e:
            logger.error(f"Error logging activity: {str(e)}")

    def get_action_description(self, request):
        """Generar descripción de la acción"""
        method = request.method
        path = request.path
        
        # Mapeo de rutas comunes
        path_mappings = {
            '/profile/': 'Visitó perfil',
            '/profile-settings': 'Accedió a configuración de perfil',
            '/user/list/': 'Listó usuarios',
            '/user/create/': 'Creó usuario',
            '/dashboard/': 'Accedió al dashboard',
            '/login/': 'Intentó iniciar sesión',
            '/logout/': 'Cerró sesión',
        }
        
        # Buscar mapeo específico
        for pattern, description in path_mappings.items():
            if path.startswith(pattern):
                return description
        
        # Generar descripción genérica
        if method == 'GET':
            return f"Accedió a {path}"
        elif method == 'POST':
            return f"Envió datos a {path}"
        elif method == 'PUT':
            return f"Actualizó {path}"
        elif method == 'DELETE':
            return f"Eliminó en {path}"
        else:
            return f"{method} {path}"

    def get_activity_details(self, request, response, response_time):
        """Obtener detalles de la actividad"""
        details = {
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'response_time_ms': response_time,
        }
        
        # Agregar parámetros GET si existen
        if request.GET:
            details['get_params'] = dict(request.GET)
        
        # Agregar información del referer
        if request.META.get('HTTP_REFERER'):
            details['referer'] = request.META['HTTP_REFERER']
        
        # Agregar tamaño de respuesta si está disponible
        if hasattr(response, 'content') and response.content:
            details['response_size'] = len(response.content)
        
        return json.dumps(details, default=str)

    def get_priority_from_status(self, status_code):
        """Determinar prioridad basada en el código de estado"""
        if status_code >= 500:
            return 'critical'
        elif status_code >= 400:
            return 'high'
        elif status_code >= 300:
            return 'medium'
        else:
            return 'low'

    def get_category_from_path(self, path):
        """Determinar categoría basada en la ruta"""
        if path.startswith('/admin/'):
            return 'admin'
        elif path.startswith('/profile/') or path.startswith('/settings/'):
            return 'profile'
        elif path.startswith('/user/'):
            return 'user_management'
        elif path.startswith('/api/'):
            return 'api'
        elif path.startswith('/auth/') or path.startswith('/accounts/'):
            return 'auth'
        elif path.startswith('/business/'):
            return 'business'
        elif path.startswith('/product/'):
            return 'product'
        elif path.startswith('/variable/'):
            return 'variable'
        else:
            return 'general'

    def get_client_ip(self, request):
        """Obtener la IP real del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UserSessionMiddleware:
    """Middleware para gestionar sesiones de usuario"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            self.update_user_session(request)
        
        response = self.get_response(request)
        return response

    def update_user_session(self, request):
        """Actualizar o crear sesión de usuario"""
        try:
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key
            
            user_session, created = UserSession.objects.get_or_create(
                session_key=session_key,
                defaults={
                    'user': request.user,
                    'ip_address': self.get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                }
            )
            
            if not created:
                user_session.last_activity = timezone.now()
                user_session.save(update_fields=['last_activity'])
                
        except Exception as e:
            logger.error(f"Error updating user session: {str(e)}")

    def get_client_ip(self, request):
        """Obtener la IP real del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RateLimitMiddleware:
    """Middleware para limitar tasa de requests por usuario"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limit = getattr(settings, 'RATE_LIMIT_PER_MINUTE', 100)
        self.cache_timeout = 60  # 1 minuto

    def __call__(self, request):
        if self.is_rate_limited(request):
            return HttpResponse(
                'Demasiadas solicitudes. Intenta de nuevo en un momento.',
                status=429,
                content_type='text/plain'
            )
        
        response = self.get_response(request)
        return response

    def is_rate_limited(self, request):
        """Verificar si el usuario ha excedido el límite de tasa"""
        # Solo aplicar rate limiting a usuarios autenticados
        if not request.user.is_authenticated:
            return False
        
        # Excluir administradores del rate limiting
        if request.user.is_staff:
            return False
        
        # Crear clave única para el usuario
        cache_key = f"rate_limit_{request.user.id}"
        
        # Obtener contador actual
        current_requests = cache.get(cache_key, 0)
        
        if current_requests >= self.rate_limit:
            return True
        
        # Incrementar contador
        cache.set(cache_key, current_requests + 1, self.cache_timeout)
        return False


class SecurityHeadersMiddleware:
    """Middleware para agregar headers de seguridad"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Agregar headers de seguridad
        self.add_security_headers(response)
        
        return response

    def add_security_headers(self, response):
        """Agregar headers de seguridad a la respuesta"""
        # Prevenir clickjacking
        response['X-Frame-Options'] = 'DENY'
        
        # Prevenir MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Habilitar XSS protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy básico
        if not response.get('Content-Security-Policy'):
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
                "https://cdn.jsdelivr.net https://cdnjs.cloudflare.com "
                "https://cdn.lordicon.com; "
                "style-src 'self' 'unsafe-inline' "
                "https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "img-src 'self' data: https:; "
                "font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com;"
            )


class MaintenanceModeMiddleware:
    """Middleware para modo de mantenimiento"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Verificar si el modo mantenimiento está activo
        if self.is_maintenance_mode() and not self.is_exempt_user(request):
            return self.maintenance_response()
        
        response = self.get_response(request)
        return response

    def is_maintenance_mode(self):
        """Verificar si el modo mantenimiento está activo"""
        return cache.get('maintenance_mode', False)

    def is_exempt_user(self, request):
        """Verificar si el usuario está exento del modo mantenimiento"""
        return (
            request.user.is_authenticated and 
            request.user.is_staff
        )

    def maintenance_response(self):
        """Respuesta para modo mantenimiento"""
        return HttpResponse(
            '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Sitio en Mantenimiento</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        text-align: center; 
                        padding: 50px;
                        background: #f5f5f5;
                    }
                    .container {
                        max-width: 500px;
                        margin: 0 auto;
                        background: white;
                        padding: 40px;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }
                    h1 { color: #333; }
                    p { color: #666; line-height: 1.6; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🔧 Sitio en Mantenimiento</h1>
                    <p>Estamos realizando mejoras en nuestro sitio.</p>
                    <p>Volveremos pronto. Gracias por tu paciencia.</p>
                </div>
            </body>
            </html>
            ''',
            status=503,
            content_type='text/html'
        )


class TimezoneMiddleware:
    """Middleware para manejar zonas horarias de usuario"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            self.activate_user_timezone(request)
        
        response = self.get_response(request)
        return response

    def activate_user_timezone(self, request):
        """Activar zona horaria del usuario"""
        try:
            if hasattr(request.user, 'userprofile'):
                user_timezone = request.user.userprofile.timezone
                if user_timezone:
                    timezone.activate(user_timezone)
                    return
        except Exception as e:
            logger.error(f"Error activating user timezone: {str(e)}")
        
        # Fallback a zona horaria por defecto
        timezone.activate(settings.TIME_ZONE)


# Middleware de compatibilidad con versiones anteriores de Django
class LegacyMiddleware(MiddlewareMixin):
    """Middleware base para compatibilidad"""
    
    def process_request(self, request):
        """Procesar request antes de la vista"""
        pass
    
    def process_response(self, request, response):
        """Procesar response después de la vista"""
        return response
    
    def process_exception(self, request, exception):
        """Procesar excepciones"""
        logger.error(f"Exception in view: {str(exception)}", exc_info=True)
        return None