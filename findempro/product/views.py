
from django.shortcuts import render, get_object_or_404, redirect
from .models import Product
from business.models import Business
from .forms import ProductForm
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin  # Create a Django form for Product
from django.http import JsonResponse
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from django.http import HttpResponseForbidden
import logging
# Create your product views here.
class AppsView(LoginRequiredMixin,TemplateView):
    pass
# List
def product_list(request):
    products = Product.objects.all().order_by('-id')
    businesses = Business.objects.all().order_by('-id')
    context = {'products': products, 'businesses': businesses}
    return render(request, 'product/product-list.html', context)

# Detail
def product_overview(request, pk):
    # Configura el registro dentro de la función o vista.
    logger = logging.getLogger(__name__)
    logger.debug("This is a log message.")
    current_datetime = timezone.now()
    try:
        product = get_object_or_404(Product, pk=pk)
        businesses = Business.objects.all().order_by('-id')
        context = {'businesses': businesses, 'product': product, 'current_datetime': current_datetime}  # Corrected the context variable name
        return render(request, 'product/product-overview.html', context)
    except Exception as e:
        # Registra el error completo
        logger.exception("An error occurred in the 'business_overview' view")
        messages.error(request, "An error occurred. Please check the server logs for more information.")
        return HttpResponse(status=500)  # Return an HTTP 500 error response

# Create
def create_product_view(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()  # Save the form data to the database
            messages.success(request, 'Business created successfully')
            return JsonResponse({'success': True})
        else:
            # Handle form validation errors
            return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = ProductForm()
    return render(request, 'product/product-list.html', {'form': form})
# Update
def update_product_view(request,pk):
    product = Product.objects.get(pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST or None,request.FILES or None,instance=product)
        if form.is_valid():
            form.save()
            messages.success(request,"Company updated successfully!")
            return redirect("product:product.overview")
        else:
            messages.error(request,"Something went wrong!")
            return redirect("product:product.overview")
    return render(request,"product/product-list.html")

# Delete
def delete_product_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    # Realiza la eliminación lógica (por ejemplo, establecer un campo "eliminado" en True)
    if request.method == 'POST':
        product.status = 0
        product.save()
        messages.success(request, "Product deleted successfully!")
        return redirect("product:product.list")
    
    # Si se accede a la vista mediante GET, puedes mostrar un error o redirigir
    return HttpResponseForbidden("GET request not allowed for this view")
