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
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)

    return render(request, 'business/business-list.html', context)
def read_business_view(request, pk):
    try:
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
    except Exception as e:
        messages.error(request, "An error occurred. Please check the server logs for more information: ", e)
        return HttpResponse(status=500) 
def create_or_update_business_view(request, pk=None):
    business_instance = None
    if pk:
        try:
            business_instance = Business.objects.get(pk=pk)
        except Business.DoesNotExist:
            messages.error(request, "Business does not exist.")
            return redirect("business:business.list")

    if request.method == 'POST':
        form = BusinessForm(request.POST, request.FILES, instance=business_instance)

        if form.is_valid():
            business_instance = form.save(commit=False)
            business_instance.fk_user = request.user
            business_instance.last_updated = timezone.now()
            business_instance.save()

            if business_instance.id:
                messages.success(request, "Business updated successfully!")
            else:
                messages.success(request, "Business created successfully!")

            return redirect("business:business.list")

        messages.error(request, "Please check your inputs.")
    else:
        print(form.errors)
        form = BusinessForm(instance=business_instance)

    return render(request, "business/business-list.html", {'form': form, 'business': business_instance})
@login_required
def delete_business_view(request, pk):
    try:
        if request.method == 'POST':
            business = get_object_or_404(Business, pk=pk)
            business.is_active = False
            business.save()
            messages.success(request, "Business deleted successfully!")
            return redirect("business:business.list")
        else:
            messages.error(request, "Invalid request method. Only POST is allowed.")
            return HttpResponse("Invalid request method. Only POST is allowed.", status=405)  # Method Not Allowed
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)

@login_required
def get_business_details_view(request, pk):
    try:
        business = Business.objects.get(id=pk, is_active=True)
        business_details = {
            "id": business.id,
            "name": business.name,
            "type": business.type,
            "location": business.location,
            "image_src": str(business.image_src),
            "description": business.description,
        }
        return JsonResponse(business_details)
    except ObjectDoesNotExist:
        return JsonResponse({"error": "El negocio no existe"}, status=404)
    except Exception as e:
        return JsonResponse({"error": "Error interno del servidor"}, status=500)
