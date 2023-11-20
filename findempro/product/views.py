from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Area
from business.models import Business
from variable.models import Variable
from report.models import Report
from simulate.models import ResultSimulation
from .forms import ProductForm
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin  # Create a Django form for Product
from django.http import JsonResponse
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
class AppsView(LoginRequiredMixin,TemplateView):
    pass
def product_list(request):
    try:
        business_id = request.GET.get('business_id', 'All')
        if business_id == 'All':
            products = Product.objects.filter(is_active=True).order_by('-id')
            businesses = Business.objects.filter(is_active=True).order_by('-id')
        else:
            products = Product.objects.filter(fk_business_id=business_id, is_active=True).order_by('-id')
            businesses = Business.objects.filter(is_active=True).order_by('-id')
        paginator = Paginator(products, 10)  # Show 10 products per page
        page = request.GET.get('page')

        try:
            products = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            products = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            products = paginator.page(paginator.num_pages)

        context = {'products': products, 'businesses': businesses}
        return render(request, 'product/product-list.html', context)
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)
def product_overview(request, pk):
        current_datetime = timezone.now()
    # try:
        product = get_object_or_404(Product, pk=pk)
        variables_product = Variable.objects.filter(fk_product_id=product.id, is_active=True).order_by('-id')
        reports = Report.objects.filter(fk_product_id=product.id, is_active=True).order_by('-id')
        areas = Area.objects.filter(fk_product_id=product.id, is_active=True).order_by('-id')
        simulations = ResultSimulation.objects.filter(fk_simulation_scenario__fk_product_id=product.id, is_active=True).order_by('-id')
        paginator = Paginator(variables_product, 10)
        page = request.GET.get('page')
        try:
            variables_product = paginator.page(page)
        except PageNotAnInteger:
            variables_product = paginator.page(1)
        except EmptyPage:
            variables_product = paginator.page(paginator.num_pages)
        
        context = {
                'variables_product': variables_product, 
                'product': product, 
                'current_datetime': current_datetime,
                'simulations': simulations,
                'reports': reports,
                'areas': areas
                   } 
        return render(request, 'product/product-overview.html', context)
    # except Exception as e:
    #     messages.error(request, "An error occurred. Please check the server logs for more information.")
    #     return HttpResponse(status=500)
def create_product_view(request):
    if request.method == 'POST':
        try:
            form = ProductForm(request.POST, request.FILES)
            if form.is_valid():
                product = form.save()
                messages.success(request, 'Product created successfully')
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'errors': form.errors})
        except Exception as e:
            # Manejo de excepción. Puedes imprimir un mensaje de error o realizar otras acciones necesarias.
            error_message = str(e)
            return JsonResponse({'success': False, 'errors': {'non_field_errors': error_message}})
    else:
        form = ProductForm()
    return render(request, 'product/product-list.html', {'form': form})
def update_product_view(request, pk):
    try:
        product = get_object_or_404(Product, pk=pk)

        if request.method == "PUT":
            form = ProductForm(request.POST or None, request.FILES or None, instance=product)
            if form.is_valid():
                form.save()
                messages.success(request, "Product updated successfully!")
                return redirect("product:product.overview")
            else:
                messages.error(request, "Something went wrong!")

    except Exception as e:
        # Manejo de excepción. Puedes imprimir un mensaje de error o realizar otras acciones necesarias.
        error_message = str(e)
        messages.error(request, f"An error occurred: {error_message}")

    return render(request, "product/product-list.html")
def delete_product_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    # Realiza la eliminación lógica (por ejemplo, establecer un campo "eliminado" en True)
    if request.method == 'PATCH':
        product.is_active = False
        product.save()
        messages.success(request, "Product deleted successfully!")
        return redirect("product:product.list")
    
    # Si se accede a la vista mediante GET, puedes mostrar un error o redirigir
    return HttpResponseForbidden("GET request not allowed for this view")
def get_product_details(request, pk):
    try:
        if request.method == 'GET':
            product = Product.objects.get(id=pk)

            product_details = {
                "name": product.name,
                "type": product.type,
                "fk_business": product.fk_business.name,
                "description": product.description,
            }
            return JsonResponse(product_details)
    except ObjectDoesNotExist:
        # Manejo de la excepción si el objeto Product no se encuentra
        return JsonResponse({"error": "El producto no existe"}, status=404)
    except Exception as e:
        # Manejo de otras excepciones inesperadas
        return JsonResponse({"error": str(e)}, status=500)
