
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
    """
    Retrieves all products and businesses from the database and passes them as context to a template for rendering.

    Args:
        request: The HTTP request object.

    Returns:
        The rendered `product/product-list.html` template as the HTTP response.
    """
    products = Product.objects.order_by('-id')
    businesses = Business.objects.order_by('-id')
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
    """
    View function that handles the creation of a new product.

    If the request method is POST, the function validates the form data and saves the product.
    If the form is valid, a success message is displayed and a JSON response with a success flag is returned.
    If the form is not valid, a JSON response with the form errors is returned.
    If the request method is not POST, the function renders the product creation form.

    Args:
        request (HttpRequest): The HTTP request object containing information about the request.

    Returns:
        JsonResponse or HttpResponse: JSON response with a success flag or rendered template with form.
    """
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, 'Product created successfully')
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = ProductForm()
    return render(request, 'product/product-list.html', {'form': form})
# Update
def update_product_view(request, pk):
    """
    Handles the updating of a product in a Django web application.

    Args:
        request (HttpRequest): The HTTP request object.
        pk (int): The primary key of the product to be updated.

    Returns:
        None: The function renders a template or redirects the user.
    """
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        form = ProductForm(request.POST or None, request.FILES or None, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated successfully!")
        else:
            messages.error(request, "Something went wrong!")
        return redirect("product:product.overview")

    return render(request, "product/product-list.html")

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

def generate_and_save_products(request):
    if request.method == 'POST':
        # Generate and save 3 products
        for i in range(3):
            product = Product(
                name=f"Product {i + 1}",
                type="Type A",  # You can change this as needed
                description=f"Description of Product {i + 1}",
                is_active=True,
                date_created=timezone.now(),
                last_updated=timezone.now(),
                fk_business_id=1,  # Replace with the appropriate business ID
                fk_category_id=1,  # Replace with the appropriate category ID
            )
            product.save()

    return render(request, 'your_template.html')  # Replace 'your_template.html' with your actual template path