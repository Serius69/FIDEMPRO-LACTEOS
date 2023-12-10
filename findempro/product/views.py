from django.shortcuts import render, get_object_or_404, redirect
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
class AppsView(LoginRequiredMixin,TemplateView):
    pass
def product_list(request):
    # try:
        business_id = request.GET.get('business_id', 'All')
        if business_id == 'All':
            businesses = Business.objects.filter(is_active=True, fk_user=request.user).order_by('-id')
            products = Product.objects.filter(is_active=True, fk_business__in=businesses ,fk_business__fk_user=request.user).order_by('-id')
            
        else:
            businesses = Business.objects.filter(is_active=True, fk_user=request.user).order_by('-id')
            products = Product.objects.filter(fk_business_id=business_id, is_active=True , fk_business__fk_user=request.user).order_by('-id')

        paginator = Paginator(products, 10)  # Show 10 products per page
        page = request.GET.get('page')
        instructions = Instructions.objects.filter(fk_user=request.user, is_active=True).order_by('-id')
        try:
            products = paginator.page(page)
        except PageNotAnInteger:
            products = paginator.page(1)
        except EmptyPage:
            products = paginator.page(paginator.num_pages)
        context = {'products': products, 
                   'businesses': businesses,
                   'instructions': instructions
                   }
        return render(request, 'product/product-list.html', context)
    # except Exception as e:
    #     messages.error(request, f"An error occurred: {str(e)}")
    #     return HttpResponse(status=500)
def read_product_view(request, pk):
        current_datetime = timezone.now()
    # try:
        product = get_object_or_404(Product, pk=pk)
        variables_product = Variable.objects.filter(fk_product_id=product.id, is_active=True).order_by('-id')
        reports = Report.objects.filter(fk_product_id=product.id, is_active=True).order_by('-id')
        areas = Area.objects.filter(fk_product_id=product.id, is_active=True).order_by('-id')
        results_simulation = ResultSimulation.objects.filter(is_active=True, 
            fk_simulation__fk_questionary_result__fk_questionary__fk_product=product).order_by('-id')
        simulations = Simulation.objects.filter(
            fk_questionary_result__fk_questionary__fk_product_id=product.id, 
            fk_simulation_result_simulation__in=results_simulation,
            is_active=True).order_by('-id')
        
        demands = Demand.objects.filter(
            fk_product_id=product.id, is_active=True
        )
        print('demandas')
        print(demands)
        paginator = Paginator(variables_product, 18)
        paginator2 = Paginator(simulations, 5)
        page = request.GET.get('page')
        page2 = request.GET.get('page')
        try:
            variables_product = paginator.page(page)
            simulations = paginator2.page(page2)
        except PageNotAnInteger:
            variables_product = paginator.page(1)
            simulations = paginator2.page(1)
        except EmptyPage:
            variables_product = paginator.page(paginator.num_pages)
            simulations = paginator2.page(paginator2.num_pages)
        
        context = {
                'variables_product': variables_product, 
                'product': product, 
                'current_datetime': current_datetime,
                'simulations': simulations,
                'reports': reports,
                'areas': areas,
                'demands': demands,
                } 
        return render(request, 'product/product-overview.html', context)
    # except Exception as e:
    #     messages.error(request, "An error occurred. Please check the server logs for more information.")
    #     return HttpResponse(status=500)
    
def area_overview(request, pk):
        current_datetime = timezone.now()
    # try:
        # product = get_object_or_404(Product, pk=pk)
        area = get_object_or_404(Area, pk=pk)
        equations_area = Equation.objects.filter(fk_area_id=area.id, is_active=True).order_by('-id')
        paginator = Paginator(equations_area, 10)
        page = request.GET.get('page')
        try:
            equations_area = paginator.page(page)
        except PageNotAnInteger:
            equations_area = paginator.page(1)
        except EmptyPage:
            equations_area = paginator.page(paginator.num_pages)
        
        context = { 
                'area': area,
                'equations_area':equations_area,
                'current_datetime': current_datetime,
                } 
        return render(request, 'product/area-overview.html', context)
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
    # try:
        if request.method == 'POST':
            product = get_object_or_404(Product, pk=pk)
            product.is_active = False
            product.save()
            messages.success(request, "¡Producto eliminado con éxito!")
            return redirect("product:product.list")
        else:
            # Handle the case where the request method is not POST
            return HttpResponse(status=405)  # Method Not Allowed
    # except Exception as e:
    #     messages.error(request, f"An error occurred: {str(e)}")
    #     return HttpResponse(status=500)
def get_product_details(request, pk):
    # try:
        if request.method == 'GET':
            product = Product.objects.get(id=pk)

            product_details = {
                "name": product.name,
                "type": product.type,
                'image_src': str(product.image_src),
                "fk_business": product.fk_business_id,
                "description": product.description,
            }
            return JsonResponse(product_details)
    # except ObjectDoesNotExist:
    #     # Manejo de la excepción si el objeto Product no se encuentra
    #     return JsonResponse({"error": "El producto no existe"}, status=404)
    # except Exception as e:
    #     # Manejo de otras excepciones inesperadas
    #     return JsonResponse({"error": str(e)}, status=500)

def create_area_view(request):
    if request.method == 'POST':
        try:
            form = AreaForm(request.POST, request.FILES)
            if form.is_valid():
                area = form.save()
                messages.success(request, 'Área creada con éxito')
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'errors': form.errors})
        except Exception as e:
            # Manejo de excepción. Puedes imprimir un mensaje de error o realizar otras acciones necesarias.
            error_message = str(e)
            return JsonResponse({'success': False, 'errors': {'non_field_errors': error_message}})
    else:
        form = AreaForm()
    return render(request, 'product/product-list.html', {'form': form})
def update_area_view(request, pk):
    try:
        area = get_object_or_404(Area, pk=pk)
        if request.method == "PUT":
            form = AreaForm(request.POST or None, request.FILES or None, instance=area)
            if form.is_valid():
                form.save()
                messages.success(request, "Área actualizada con éxito!")
                return redirect("product:area.overview")
            else:
                messages.error(request, "Something went wrong!")
    except Exception as e:
        # Manejo de excepción. Puedes imprimir un mensaje de error o realizar otras acciones necesarias.
        error_message = str(e)
        messages.error(request, f"An error occurred: {error_message}")

    return render(request, "product/product-list.html")
def delete_area_view(request, pk):
    # try:
        if request.method == 'POST':
            area = get_object_or_404(Area, pk=pk)
            area.is_active = False
            area.save()
            messages.success(request, "¡Producto eliminado con éxito!")
            return redirect("product:product.list")
        else:
            # Handle the case where the request method is not POST
            return HttpResponse(status=405)  # Method Not Allowed
    # except Exception as e:
    #     messages.error(request, f"An error occurred: {str(e)}")
    #     return HttpResponse(status=500)
def get_area_details(request, pk):
    # try:
        if request.method == 'GET':
            area = Area.objects.get(id=pk)
            area_details = {
                "name": area.name,
                'image_src': str(area.image_src.url),
                "fk_product": area.fk_product.id,
                "description": area.description,
            }
            return JsonResponse(area_details)
    # except ObjectDoesNotExist:
    #     # Manejo de la excepción si el objeto Product no se encuentra
    #     return JsonResponse({"error": "El producto no existe"}, status=404)
    # except Exception as e:
    #     # Manejo de otras excepciones inesperadas
    #     return JsonResponse({"error": str(e)}, status=500)