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
from findempro.views import convert_to_webp
from django.core.files import File
from django.core.files.base import ContentFile
# Create your business views here.
class AppsView(LoginRequiredMixin, TemplateView):
    pass

# List
def business_list(request):
    """
    Renders a list of businesses based on the logged-in user.

    Args:
        request (HttpRequest): The HTTP request object containing metadata about the request.

    Returns:
        HttpResponse: The rendered HTML template with the list of businesses and the form instance.
    """
    form = BusinessForm()
    try:
        businesses = Business.objects.filter(fk_user=request.user).order_by('-id')
        context = {'businesses': businesses, 'form': form}
        return render(request, 'business/business-list.html', context)
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)


# Detail
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

@login_required
def create_business_view(request):
    if request.method == 'POST':
        form = BusinessForm(request.POST, request.FILES)
        if form.is_valid():
            # try:
                business = form.save(commit=False)  # No guardes el formulario aún

                # Obtiene la imagen original del formulario
                image = form.cleaned_data['image_src']
                # Convierte la imagen a WebP usando Pillow
                converted_image = convert_to_webp(image)

                # Crea un archivo temporal para el archivo WebP
                webp_data = converted_image.tobytes()
                webp_file = ContentFile(webp_data, name=f"{image.name}.webp")

                # Guarda el archivo WebP en el campo image_src
                business.image_src.save(f"{image.name}.webp", webp_file, save=False)
                business.save()  # Ahora sí, guarda el objeto Business en la base de datos
                messages.success(request, 'Business created successfully')
                return JsonResponse({'success': True})
            # except Exception as e:
                # messages.error(request, f"An error occurred: {str(e)}")
                # return JsonResponse({'success': False, 'error': f"An error occurred: {str(e)}"})
        else:
            # Handle form validation errors
            return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = BusinessForm()
    return render(request, 'business/business-form.html', {'form': form})

# Update
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

# Delete
def delete_business_view(request, pk):
    try:
        business = get_object_or_404(Business, pk=pk)
        business.is_active=False
        business.save()
        messages.success(request, "Business deleted successfully!")
        return redirect("business:business_list")  # Corrected the redirect URL name
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)  # Return an HTTP 500 error response
