from functools import wraps

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse

from .services import get_request_organization

DEFAULT_ABUSE_LIMITS = {
    "simulation": (20, 3600),
    "import": (30, 3600),
    "export": (30, 3600),
    "sensitivity": (10, 3600),
    "ai": (10, 3600),
}


def consume_abuse_budget(kind, organization, actor_id):
    limits = {
        **DEFAULT_ABUSE_LIMITS,
        **(getattr(settings, "FINDEMPRO_ABUSE_LIMITS", None) or {}),
    }
    limit, window = limits[kind]
    key = f"findempro:abuse:{kind}:{organization.id}:{actor_id}"
    if cache.add(key, 1, timeout=window):
        count = 1
    else:
        count = cache.incr(key)
    return count <= limit, window


def expensive_operation(kind):
    """Fixed-window antiabuse guard, deliberately separate from product quotas."""
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            organization = get_request_organization(request)
            allowed, window = consume_abuse_budget(kind, organization, request.user.pk)
            if not allowed:
                return JsonResponse(
                    {"error": "rate_limited", "operation": kind, "retry_after_seconds": window},
                    status=429,
                )
            return view(request, *args, **kwargs)
        return wrapped
    return decorator
