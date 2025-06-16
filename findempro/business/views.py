import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from .models import Business
from product.models import Product
from .forms import BusinessForm
from django.utils import timezone
from pages.models import Instructions
from django.urls import reverse
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.models import User
from django.http import Http404

logger = logging.getLogger(__name__)

class AppsView(LoginRequiredMixin, TemplateView):
    pass

@login_required
def business_list_view(request):
    form = BusinessForm()
    try:
        businesses = Business.objects.filter(fk_user=request.user, is_active=True).order_by('-id')
        paginator = Paginator(businesses, 12)
        page = request.GET.get('page')
        try:
            businesses = paginator.page(page)
        except PageNotAnInteger:
            businesses = paginator.page(1)
        except EmptyPage:
            businesses = paginator.page(paginator.num_pages)
        
        instructions = Instructions.objects.filter(fk_user=request.user, is_active=True).order_by('id')
        context = {
            'businesses': businesses, 
            'form': form,
            'instructions': instructions
        }
    except Exception as e:
        logger.error(f"Error in business_list_view: {str(e)}")
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)

    return render(request, 'business/business-list.html', context)

@login_required
def read_business_view(request, pk):
    try:
        business = get_object_or_404(Business, pk=pk, fk_user=request.user, is_active=True)
        products = Product.objects.filter(
            fk_business_id=business.id, 
            fk_business__fk_user=request.user, 
            is_active=True
        ).order_by('-id')
        
        paginator = Paginator(products, 10)
        num_products = products.count()
        page = request.GET.get('page')
        
        try:
            products = paginator.page(page)
        except PageNotAnInteger:
            products = paginator.page(1)
        except EmptyPage:
            products = paginator.page(paginator.num_pages)
        
        context = {
            'business': business, 
            'products': products,
            'num_products': num_products,
            'instructions': Instructions.objects.filter(is_active=True).order_by('-id')
        }
        
        return render(request, 'business/business-overview.html', context)
    except Exception as e:
        logger.error(f"Error in read_business_view: {str(e)}")
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500) 

@login_required
def create_or_update_business_view(request, pk=None):
    # Para crear negocio
    if pk is None:
        if request.method == 'POST':
            try:
                form = BusinessForm(request.POST, request.FILES)
                
                if form.is_valid():
                    business = form.save(commit=False)
                    business.fk_user = request.user
                    business.last_updated = timezone.now()
                    business.save()
                    
                    # Si es una petición AJAX, devolver JSON
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True, 
                            'message': 'Negocio creado exitosamente!',
                            'business_id': business.id
                        })
                    else:
                        messages.success(request, 'Negocio creado exitosamente!')
                        return redirect('business:business.list')
                else:
                    # Si hay errores en el formulario
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False, 
                            'message': 'Por favor corrige los errores en el formulario',
                            'errors': form.errors
                        }, status=400)
                    else:
                        messages.error(request, 'Por favor corrige los errores en el formulario')
                        return redirect('business:business.list')
                        
            except Exception as e:
                logger.error(f"Error in create_or_update_business_view: {str(e)}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False, 
                        'message': f'Error interno del servidor: {str(e)}'
                    }, status=500)
                else:
                    messages.error(request, f"An error occurred: {str(e)}")
                    return redirect('business:business.list')
        else:
            # Método no permitido para crear
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Método no permitido'
                }, status=405)
            else:
                return HttpResponse("Método no permitido", status=405)
    
    # Para actualizar negocio
    else:
        if request.method == 'POST':
            try:
                business_instance = get_object_or_404(Business, pk=pk, fk_user=request.user, is_active=True)
                form = BusinessForm(request.POST, request.FILES, instance=business_instance)
                
                if form.is_valid():
                    business = form.save(commit=False)
                    business.last_updated = timezone.now()
                    business.save()
                    
                    # Si es una petición AJAX, devolver JSON
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True, 
                            'message': 'Negocio actualizado exitosamente!',
                            'business_id': business.id
                        })
                    else:
                        messages.success(request, 'Negocio actualizado exitosamente!')
                        return redirect('business:business.list')
                else:
                    # Si hay errores en el formulario
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False, 
                            'message': 'Por favor corrige los errores en el formulario',
                            'errors': form.errors
                        }, status=400)
                    else:
                        messages.error(request, 'Por favor corrige los errores en el formulario')
                        return redirect('business:business.list')
                        
            except Exception as e:
                logger.error(f"Error in create_or_update_business_view: {str(e)}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False, 
                        'message': f'Error interno del servidor: {str(e)}'
                    }, status=500)
                else:
                    messages.error(request, f"An error occurred: {str(e)}")
                    return redirect('business:business.list')
        else:
            # Método no permitido para actualizar
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Método no permitido'
                }, status=405)
            else:
                return HttpResponse("Método no permitido", status=405)

@login_required
def delete_business_view(request, pk):
    if request.method == 'POST':
        try:
            business = get_object_or_404(Business, pk=pk, fk_user=request.user, is_active=True)
            business.is_active = False  # Eliminación lógica
            business.save(update_fields=['is_active'])
            
            # Si es una petición AJAX, devolver JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Negocio eliminado exitosamente!'
                })
            else:
                messages.success(request, "Negocio eliminado exitosamente!")
                return redirect("business:business.list")
                
        except Exception as e:
            logger.error(f"Error in delete_business_view: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': f'Error al eliminar el negocio: {str(e)}'
                }, status=500)
            else:
                messages.error(request, f"An error occurred: {str(e)}")
                return redirect("business:business.list")
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Método no permitido. Solo POST es válido.'
            }, status=405)
        else:
            messages.error(request, "Método de request inválido. Solo POST está permitido.")
            return redirect("business:business.list")

@login_required
def get_business_details_view(request, pk):
    try:
        business = get_object_or_404(Business, pk=pk, fk_user=request.user, is_active=True)
        
        # Construir URL de imagen si existe
        image_url = business.get_photo_url()
        
        business_details = {
            "id": business.id,
            "name": business.name,
            "type": business.type,
            "location": business.location,
            "image_src": image_url,
            "description": business.description,
        }
        return JsonResponse(business_details)
        
    except Business.DoesNotExist:
        return JsonResponse({"error": "El negocio no existe o no tienes permisos para verlo"}, status=404)
    except Exception as e:
        logger.error(f"Error in get_business_details_view: {str(e)}")
        return JsonResponse({"error": "Error interno del servidor"}, status=500)