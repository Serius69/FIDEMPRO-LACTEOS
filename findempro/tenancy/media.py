"""Private images resolved through authorized objects, never client filesystem paths."""
from pathlib import Path
from io import BytesIO

from PIL import Image, UnidentifiedImageError
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, SuspiciousFileOperation
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe

from .models import OrganizationMembership
from .services import get_request_organization


def active_organization(request):
    """Recheck durable membership; request context alone is not authorization."""
    organization = get_request_organization(request)
    if not OrganizationMembership.objects.filter(
        organization=organization, organization__is_active=True,
        user=request.user, is_active=True,
    ).exists():
        raise Http404
    return organization


@never_cache
@login_required
@require_safe
def private_image(request, kind, pk):
    try:
        organization = active_organization(request)
        if kind == 'profile':
            from user.models import UserProfile
            obj = get_object_or_404(UserProfile, pk=pk, user=request.user)
            field = obj.image_src
        else:
            from business.models import Business
            from product.models import Product, Area
            from variable.models import Variable
            from dashboards.models import Chart
            models = {
                'business': (Business, '', 'image_src'),
                'product': (Product, 'fk_business__', 'image_src'),
                'area': (Area, 'fk_product__fk_business__', 'image_src'),
                'variable': (Variable, 'fk_product__fk_business__', 'image_src'),
                'chart': (Chart, 'fk_product__fk_business__', 'chart_image'),
            }
            if kind not in models:
                raise Http404
            model, prefix, name = models[kind]
            filters = {'pk': pk, 'is_active': True,
                       prefix + 'organization': organization,
                       prefix + 'fk_user': request.user,
                       prefix + 'is_active': True}
            if kind in {'area', 'variable', 'chart'}:
                filters['fk_product__is_active'] = True
            obj = get_object_or_404(model, **filters)
            field = getattr(obj, name)
        if not field:
            raise Http404
        root = Path(settings.MEDIA_ROOT).resolve()
        source = Path(field.path).resolve(strict=True)
        if not source.is_relative_to(root) or not source.is_file() or source.stat().st_size > 5 * 1024 * 1024:
            raise Http404
        with source.open('rb') as stream:
            payload = stream.read(5 * 1024 * 1024 + 1)
        if len(payload) > 5 * 1024 * 1024:
            raise Http404
        with BytesIO(payload) as image_bytes:
            with Image.open(image_bytes) as image:
                content_type = {'PNG': 'image/png', 'JPEG': 'image/jpeg', 'WEBP': 'image/webp'}.get(image.format)
                if not content_type or image.width * image.height > 25_000_000:
                    raise Http404
                image.verify()
        response = FileResponse(BytesIO(payload), content_type=content_type)
        response['X-Content-Type-Options'] = 'nosniff'
        return response
    except (Http404, PermissionDenied, SuspiciousFileOperation, OSError,
            ValueError, UnidentifiedImageError, Image.DecompressionBombError):
        return HttpResponse(status=404)

