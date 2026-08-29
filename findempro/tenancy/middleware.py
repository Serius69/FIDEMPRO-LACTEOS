from django.core.exceptions import PermissionDenied

from .services import get_user_organization


class OrganizationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.organization = None
        if getattr(request, "user", None) and request.user.is_authenticated:
            try:
                request.organization = get_user_organization(
                    request.user, request.headers.get("X-Organization-ID")
                )
            except (ValueError, PermissionDenied):
                raise PermissionDenied("Invalid organization context")
        return self.get_response(request)
