import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponse
from .models import Business
from product.models import Product
from .forms import BusinessForm
from django.urls import reverse
from django.http import JsonResponse
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
class AppsView(LoginRequiredMixin, TemplateView):
    pass
def business_list(request):
    form = BusinessForm()
    try:
        businesses = Business.objects.filter(fk_user=request.user).order_by('-id')
        per_page = 10
        paginator = Paginator(businesses, per_page)
        page = request.GET.get('page')
        try:
            businesses = paginator.page(page)
        except PageNotAnInteger:
            businesses = paginator.page(1)
        except EmptyPage:
            businesses = paginator.page(paginator.num_pages)
        context = {'businesses': businesses, 'form': form}
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)

    return render(request, 'business/business-list.html', context)
def business_overview(request, pk):
    try:
        business = get_object_or_404(Business, pk=pk)
        products = Product.objects.filter(fk_business_id=business.id).order_by('-id')
        return render(request, 'business/business-overview.html', 
                      {'business': business,
                       'products': products
                       })
    except Exception as e:
        messages.error(request, "An error occurred. Please check the server logs for more information: ", e)
        return HttpResponse(status=500) 
def create_business_view(request):
    if request.method == 'POST':
        form = BusinessForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                business=form.save()  # Ahora sí, guarda el objeto Business en la base de datos
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
                form.save()
                messages.success(request, "Business updated successfully!")
                return redirect("business:business_list")  # Corrected the redirect URL name
            else:
                messages.error(request, "Please check your inputs.")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
    form = BusinessForm(instance=business)  # Provide the form instance if it's a GET request
    return render(request, "business/business-update.html", {'form': form, 'business': business})
def delete_business_view(request, pk):
    try:
        business = get_object_or_404(Business, pk=pk)
        business.is_active=False
        business.save()
        messages.success(request, "Business deleted successfully!")
        return redirect("business:business_list")
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)
def get_business_details(request, pk):
    try:
        if request.method == 'GET':
            business = Business.objects.get(id=pk)
            business_details = {
                "name": business.name,
                "type": business.type,
                "fk_business": business.fk_business.name,
                "description": business.description,
            }
            return JsonResponse(business_details)
    except ObjectDoesNotExist:
        return JsonResponse({"error": "El negocio no existe"}, status=404)