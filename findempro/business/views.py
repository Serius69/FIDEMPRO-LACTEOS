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
class AppsView(LoginRequiredMixin, TemplateView):
    pass
def business_list(request):
    form = BusinessForm()
    try:
        businesses = Business.objects.filter(fk_user=request.user, is_active=True).order_by('-id')
        paginator = Paginator(businesses, 10)
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
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)

    return render(request, 'business/business-list.html', context)
def business_overview(request, pk):
    # try:
        business = get_object_or_404(Business, pk=pk)
        products = Product.objects.filter(fk_business_id=business.id, fk_business__fk_user=request.user, is_active=True).order_by('-id')
        paginator = Paginator(products, 10)
        num_products = products.count()
        page = request.GET.get('page')
        try:
            products = paginator.page(page)
        except PageNotAnInteger:
            products = paginator.page(1)
        except EmptyPage:
            products = paginator.page(paginator.num_pages)
        context = {'business': business, 
                   'products': products,
                   'num_products': num_products,
                   'instructions': Instructions.objects.filter(is_active=True).order_by('-id')}
        
        return render(request, 'business/business-overview.html', context)
    # except Exception as e:
    #     messages.error(request, "An error occurred. Please check the server logs for more information: ", e)
    #     return HttpResponse(status=500) 
def create_business_view(request):
    if request.method == 'POST':
        form = BusinessForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                if request.user.is_authenticated:
                    try:
                        business_instance = form.save(commit=False)
                        user = User.objects.get(id=request.user.id)
                        business_instance.fk_user = user
                        business_instance.save()
                        messages.success(request, "Business created successfully!")
                    except User.DoesNotExist:
                        messages.error(request, "User does not exist.")
                else:
                    messages.error(request, "User is not authenticated.")
                # business=form.save()
                messages.success(request, 'Business created successfully')
                return JsonResponse({'success': True})
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
                return JsonResponse({'success': False, 'error': f"An error occurred: {str(e)}"})
        else:
            messages.error(request, "Please check your inputs.")
    else:
        form = BusinessForm()
    return render(request, 'business/business-form.html', {'form': form})
def update_business_view(request, pk):
    business = get_object_or_404(Business, pk=pk)
    
    if request.method == "POST":
        form = BusinessForm(request.POST, request.FILES, instance=business)
        try:
            if form.is_valid():
                # Guardar el formulario y verificar si es una actualización o creación
                business_instance = form.save(commit=False)

                if business_instance.id:
                    # Actualización
                    business_instance.fk_user = request.user
                    business_instance.last_updated = timezone.now()
                    business_instance.save()
                    messages.success(request, "Business updated successfully!")
                else:
                    # Creación
                    if request.user.is_authenticated:
                        try:
                            user = User.objects.get(id=request.user.id)
                            business_instance.fk_user = user
                            business_instance.save()
                            messages.success(request, "Business created successfully!")
                        except User.DoesNotExist:
                            messages.error(request, "User does not exist.")
                    else:
                        messages.error(request, "User is not authenticated.")

                return redirect("business:business_list")
            else:
                messages.error(request, "Please check your inputs.")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
    else:
        # Esto es importante para mostrar la información existente en el formulario durante la actualización
        form = BusinessForm(instance=business)

    return render(request, "business/business-update.html", {'form': form, 'business': business})
def delete_business_view(request, pk):
    # try:
        if request.method == 'POST':
            business = get_object_or_404(Business, pk=pk)
            business.is_active = False
            business.save()
            messages.success(request, "Business deleted successfully!")
            return redirect("business:business.list")
        else:
            # Handle the case where the request method is not POST
            return HttpResponse(status=405)  # Method Not Allowed
    # except Exception as e:
    #     messages.error(request, f"An error occurred: {str(e)}")
    #     return HttpResponse(status=500)

def get_business_details(request, pk):
    try:
        business = Business.objects.get(id=pk)
        business_details = {
            "id": business.id,
            "name": business.name,
            "type": business.type,
            "location": business.location,
            "image_src": str(business.image_src),
            "description": business.description,
        }
        return JsonResponse(business_details)
    except Business.DoesNotExist:
        return JsonResponse({"error": "El negocio no existe"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
