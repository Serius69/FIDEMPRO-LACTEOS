from django.shortcuts import render, get_object_or_404, redirect, reverse, Http404
from .models import Product, Area
from business.models import Business
from variable.models import Variable, Equation
from pages.models import Instructions
from report.models import Report
from simulate.models import ResultSimulation,Simulation, DemandBehavior,Demand
from .forms import ProductForm, AreaForm
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
from django.views.decorators.http import require_POST
class AppsView(LoginRequiredMixin,TemplateView):
    pass
def paginate(request, queryset, per_page):
    paginator = Paginator(queryset, per_page)
    page = request.GET.get('page')
    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        items = paginator.page(1)
    except EmptyPage:
        items = paginator.page(paginator.num_pages)
    return items
def product_list(request):
    try:
        business_id = request.GET.get('business_id', 'All')
        businesses = Business.objects.filter(is_active=True, fk_user=request.user).order_by('-id')

        if business_id == 'All':
            products = Product.objects.filter(is_active=True, fk_business__in=businesses).order_by('-id')
        else:
            products = Product.objects.filter(fk_business_id=business_id, is_active=True).order_by('-id')

        products = paginate(request, products, 12)  # Show 12 products per page
        instructions = Instructions.objects.filter(fk_user=request.user, is_active=True).order_by('-id')

        context = {'products': products, 'businesses': businesses, 'instructions': instructions}
        return render(request, 'product/product-list.html', context)
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)
def read_product_view(request, pk):
    try:
        current_datetime = timezone.now()
        product = get_object_or_404(Product, pk=pk)
        variables_product = Variable.objects.filter(fk_product_id=product.id, is_active=True).order_by('-id')
        products = Product.objects.filter(is_active=True, fk_business__fk_user=request.user).order_by('-id')
        reports = Report.objects.filter(fk_product_id=product.id, is_active=True).order_by('-id')
        areas = Area.objects.filter(fk_product_id=product.id, is_active=True).order_by('-id')
        results_simulation = ResultSimulation.objects.filter(is_active=True, 
            fk_simulation__fk_questionary_result__fk_questionary__fk_product=product).order_by('-id')
        simulations = Simulation.objects.filter(
            fk_questionary_result__fk_questionary__fk_product_id=product.id, 
            fk_simulation_result_simulation__in=results_simulation,
            is_active=True).order_by('-id')
        demands = Demand.objects.filter(fk_product_id=product.id, is_active=True)

        variables_product = paginate(request, variables_product, 18)
        simulations = paginate(request, simulations, 5)

        context = {
            'variables_product': variables_product, 
            'product': product, 
            'current_datetime': current_datetime,
            'simulations': simulations,
            'reports': reports,
            'areas': areas,
            'demands': demands,
            'products': products,
        } 
        return render(request, 'product/product-overview.html', context)
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)
def area_overview(request, pk):
    try:
        current_datetime = timezone.now()
        area = get_object_or_404(Area, pk=pk)
        equations_area = Equation.objects.filter(fk_area_id=area.id, is_active=True).order_by('-id')
        
        equations_area = paginate(request, equations_area, 10)  # Show 10 equations per page
        
        context = { 
            'area': area,
            'equations_area': equations_area,
            'current_datetime': current_datetime,
        } 
        return render(request, 'product/area-overview.html', context)
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)
def create_or_update_product_view(request, pk=None):
    product_instance = get_object_or_404(Product, pk=pk) if pk else None

    if request.method in ['POST', 'PUT']:
        form = ProductForm(request.POST or None, request.FILES or None, instance=product_instance)
        if form.is_valid():
            form.save()
            if pk:
                messages.success(request, "Product updated successfully!")
            else:
                messages.success(request, "Product created successfully!")
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = ProductForm(instance=product_instance)

    return render(request, 'product/product-list.html', {'form': form})
def delete_product_view(request, pk):
    try:
        product = get_object_or_404(Product, pk=pk)
        product.is_active = False
        product.save()
        messages.success(request, "¡Producto eliminado con éxito!")
        return redirect("product:product.list")
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)

def get_product_details(request, pk):
    try:
        if request.method == 'GET':
            product = get_object_or_404(Product, pk=pk)

            product_details = {
                "name": product.name,
                "type": product.type,
                'image_src': str(product.image_src),
                "fk_business": product.fk_business.id,
                "description": product.description,
            }
            return JsonResponse(product_details)
    except Http404:
        return JsonResponse({"error": "El producto no existe"}, status=404)
    except Exception as e:
        # Manejo de otras excepciones inesperadas
        return JsonResponse({"error": str(e)}, status=500)
def create_or_update_area_view(request, pk=None):
    try:
        if pk:
            area = get_object_or_404(Area, pk=pk)
            if request.method == "PUT":
                form = AreaForm(request.POST or None, request.FILES or None, instance=area)
        else:
            # Create new area
            if request.method == 'POST':
                form = AreaForm(request.POST, request.FILES)
        
        if request.method in ['POST', 'PUT']:
            if form.is_valid():
                area = form.save()
                messages.success(request, 'Área creada con éxito' if pk is None else 'Área actualizada con éxito')
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'errors': form.errors})
    except Exception as e:
        error_message = str(e)
        return JsonResponse({'success': False, 'errors': {'non_field_errors': error_message}})
    
    form = AreaForm()
    return render(request, 'product/product-list.html', {'form': form})
@require_POST
def delete_area_view(request, pk):
    try:
        area = get_object_or_404(Area, pk=pk)
        area.is_active = False
        area.save()
        messages.success(request, "¡Área eliminada con éxito!")
        return redirect("product:product.list")
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)
from django.views.decorators.http import require_GET

@require_GET
def get_area_details_view(request, pk):
    try:
        area = Area.objects.get(id=pk)
        area_details = {
            "name": area.name,
            'image_src': str(area.image_src.url),
            "fk_product": area.fk_product.id,
            "description": area.description,
        }
        return JsonResponse(area_details)
    except Area.DoesNotExist:
        # Manejo de la excepción si el objeto Area no se encuentra
        return JsonResponse({"error": "El área no existe"}, status=404)
    except Exception as e:
        # Manejo de otras excepciones inesperadas
        return JsonResponse({"error": str(e)}, status=500)