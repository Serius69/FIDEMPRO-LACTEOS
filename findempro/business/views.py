import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import TemplateView

from pages.models import Instructions
from product.models import Product

from .forms import BusinessForm
from .models import Business

logger = logging.getLogger(__name__)

_AJAX_HEADER = 'XMLHttpRequest'
_BUSINESS_LIST_URL = 'business:business.list'


class AppsView(LoginRequiredMixin, TemplateView):
    pass


def _is_ajax(request) -> bool:
    return request.headers.get('X-Requested-With') == _AJAX_HEADER


def _json_ok(message: str, **extra) -> JsonResponse:
    return JsonResponse({'success': True, 'message': message, **extra})


def _json_err(message: str, status: int = 400, **extra) -> JsonResponse:
    return JsonResponse({'success': False, 'message': message, **extra}, status=status)


def _paginate(queryset, request, per_page: int):
    paginator = Paginator(queryset, per_page)
    page = request.GET.get('page')
    try:
        return paginator.page(page)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)


@login_required
def business_list_view(request):
    businesses = (
        Business.objects
        .filter(fk_user=request.user, is_active=True)
        .order_by('-id')
    )
    instructions = (
        Instructions.objects
        .filter(fk_user=request.user, is_active=True)
        .order_by('id')
    )
    context = {
        'businesses': _paginate(businesses, request, per_page=12),
        'form': BusinessForm(),
        'instructions': instructions,
    }
    return render(request, 'business/business-list.html', context)


@login_required
def read_business_view(request, pk):
    business = get_object_or_404(Business, pk=pk, fk_user=request.user, is_active=True)
    products = (
        Product.objects
        .filter(fk_business=business, is_active=True)
        .order_by('-id')
    )
    context = {
        'business': business,
        'products': _paginate(products, request, per_page=10),
        'num_products': products.count(),
        'instructions': Instructions.objects.filter(is_active=True).order_by('-id'),
    }
    return render(request, 'business/business-overview.html', context)


@login_required
def create_business_view(request):
    if request.method != 'POST':
        return _json_err('Método no permitido', 405) if _is_ajax(request) else HttpResponse(status=405)

    form = BusinessForm(request.POST, request.FILES)
    if not form.is_valid():
        if _is_ajax(request):
            return _json_err('Por favor corrige los errores en el formulario', errors=form.errors)
        messages.error(request, 'Por favor corrige los errores en el formulario')
        return redirect(_BUSINESS_LIST_URL)

    business = form.save(commit=False)
    business.fk_user = request.user
    business.last_updated = timezone.now()
    business.save()

    if _is_ajax(request):
        return _json_ok('Negocio creado exitosamente!', business_id=business.id)
    messages.success(request, 'Negocio creado exitosamente!')
    return redirect(_BUSINESS_LIST_URL)


@login_required
def update_business_view(request, pk):
    if request.method != 'POST':
        return _json_err('Método no permitido', 405) if _is_ajax(request) else HttpResponse(status=405)

    business = get_object_or_404(Business, pk=pk, fk_user=request.user, is_active=True)
    form = BusinessForm(request.POST, request.FILES, instance=business)
    if not form.is_valid():
        if _is_ajax(request):
            return _json_err('Por favor corrige los errores en el formulario', errors=form.errors)
        messages.error(request, 'Por favor corrige los errores en el formulario')
        return redirect(_BUSINESS_LIST_URL)

    saved = form.save(commit=False)
    saved.last_updated = timezone.now()
    saved.save()

    if _is_ajax(request):
        return _json_ok('Negocio actualizado exitosamente!', business_id=saved.id)
    messages.success(request, 'Negocio actualizado exitosamente!')
    return redirect(_BUSINESS_LIST_URL)


@login_required
def delete_business_view(request, pk):
    if request.method != 'POST':
        if _is_ajax(request):
            return _json_err('Método no permitido. Solo POST es válido.', 405)
        messages.error(request, 'Método de request inválido. Solo POST está permitido.')
        return redirect(_BUSINESS_LIST_URL)

    business = get_object_or_404(Business, pk=pk, fk_user=request.user, is_active=True)
    business.is_active = False
    business.save(update_fields=['is_active'])

    if _is_ajax(request):
        return _json_ok('Negocio eliminado exitosamente!')
    messages.success(request, 'Negocio eliminado exitosamente!')
    return redirect(_BUSINESS_LIST_URL)


@login_required
def get_business_details_view(request, pk):
    business = get_object_or_404(Business, pk=pk, fk_user=request.user, is_active=True)
    return JsonResponse({
        'id': business.id,
        'name': business.name or '',
        'type': str(business.type),
        'location': business.location or '',
        'image_src': business.get_photo_url(),
        'description': business.description or '',
        'date_created': business.date_created.isoformat() if business.date_created else None,
        'last_updated': business.last_updated.isoformat() if business.last_updated else None,
    })
