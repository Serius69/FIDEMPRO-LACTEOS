# middleware.py
from .models import ActivityLog

class ActivityLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        if request.user.is_authenticated:
            action = f"{request.method} {request.path_info}"
            details = None  # Puedes personalizar esto según tu aplicación

            ActivityLog.objects.create(user=request.user, action=action, details=details)

        return response
