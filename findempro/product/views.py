import json
from sqlite3 import NotSupportedError
from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.http import JsonResponse, HttpResponseForbidden, Http404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import ValidationError
from django.db.models import Prefetch, Count, Q
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.db import transaction
import logging

from .models import Product, Area
from business.models import Business
from variable.models import Variable, Equation
from pages.models import Instructions
from report.models import Report
from simulate.models import ResultSimulation, Simulation, DemandBehavior, Demand
from .forms import ProductForm, AreaForm

# Configurar logging
logger = logging.getLogger(__name__)

# Constantes
ITEMS_PER_PAGE = 12
CACHE_TIMEOUT = 300  # 5 minutos

def paginate(request, queryset, per_page):
    """Función helper para paginación con manejo de errores mejorado"""
    paginator = Paginator(queryset, per_page)
    page = request.GET.get('page', 1)
    
    try:
        items = paginator.page(page)
    except (PageNotAnInteger, ValueError):
        items = paginator.page(1)
    except EmptyPage:
        items = paginator.page(paginator.num_pages)
    except NotSupportedError:
        # Fallback: convert queryset to list to avoid count() issues
        items_list = list(queryset)
        paginator = Paginator(items_list, per_page)
        page = request.GET.get('page', 1)
        return paginator.page(page)
    
    return items


@login_required
def product_list(request):
    """Vista optimizada para listar productos con filtros y paginación"""
    try:
        business_id = request.GET.get('business_id', 'All')
        search_query = request.GET.get('search', '').strip()
        sort_by = request.GET.get('sort', '-last_updated')
        
        # Optimizar consultas con select_related y prefetch_related
        businesses = Business.objects.filter(
            is_active=True, 
            fk_user=request.user
        ).order_by('name')
        
        # Base query con optimizaciones - sin anotar campos que ya son propiedades
        products_query = Product.objects.filter(
            is_active=True
        ).select_related(
            'fk_business', 
            'fk_business__fk_user'
        ).prefetch_related(
            Prefetch(
                'fk_product_variable',
                queryset=Variable.objects.filter(is_active=True).only('id', 'name', 'image_src'),
                to_attr='active_variables'
            ),
            Prefetch(
                'fk_product_area',
                queryset=Area.objects.filter(is_active=True).only('id', 'name'),
                to_attr='active_areas'
            )
        )

        # Filtrar por negocio
        if business_id != 'All':
            try:
                business = businesses.get(id=business_id)
                products_query = products_query.filter(fk_business=business)
            except (Business.DoesNotExist, ValueError):
                messages.warning(request, "El negocio seleccionado no existe.")
                return redirect('product:product.list')
        else:
            products_query = products_query.filter(fk_business__in=businesses)

        # Filtrar por búsqueda
        if search_query:
            products_query = products_query.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(fk_business__name__icontains=search_query)
            )

        # Ordenar productos
        valid_sort_options = {
            'name': 'name',
            '-name': '-name',
            'date_created': 'date_created',
            '-date_created': '-date_created',
            'last_updated': 'last_updated',
            '-last_updated': '-last_updated',
            'business': 'fk_business__name',
            '-business': '-fk_business__name'
        }
        
        if sort_by in valid_sort_options:
            products_query = products_query.order_by(valid_sort_options[sort_by])
        else:
            products_query = products_query.order_by('-last_updated', '-date_created')
        
        # ESTADÍSTICAS - Calcular antes de la paginación
        total_products = products_query.count()
        
        # Obtener productos del usuario para calcular estadísticas
        user_products = Product.objects.filter(
            is_active=True,
            fk_business__fk_user=request.user
        )
        
        # Calcular estadísticas generales
        total_areas = Area.objects.filter(
            fk_product__in=user_products,
            is_active=True
        ).count()
        
        total_variables = Variable.objects.filter(
            fk_product__in=user_products,
            is_active=True
        ).count()

        # Productos recientes (últimos 7 días)
        recent_cutoff = timezone.now() - timezone.timedelta(days=7)
        recent_products_count = user_products.filter(
            date_created__gte=recent_cutoff
        ).count()
        
        # Paginación
        products = paginate(request, products_query, ITEMS_PER_PAGE)
        
        # Los productos ya tienen las propiedades areas_count y variables_count definidas en el modelo
        # Solo necesitamos agregar ecuaciones_count y simulations_count como atributos adicionales
        for product in products:
            # Agregar conteos adicionales como atributos (no properties)
            product.equations_count_display = 0  # Placeholder hasta tener el modelo correcto
            product.simulations_count_display = 0  # Placeholder hasta tener el modelo correcto
        
        # Obtener instrucciones si existen
        try:
            instructions = Instructions.objects.filter(
                fk_user=request.user, 
                is_active=True
            ).order_by('-id')[:5]
        except:
            instructions = []

        context = {
            'products': products, 
            'businesses': businesses, 
            'instructions': instructions,
            'selected_business': business_id,
            'search_query': search_query,
            'sort_by': sort_by,
            'total_products': total_products,
            'total_areas': total_areas,
            'total_variables': total_variables,
            'recent_products_count': recent_products_count,
            'sort_options': [
                {'value': '-last_updated', 'label': 'Más recientes'},
                {'value': 'last_updated', 'label': 'Más antiguos'},
                {'value': 'name', 'label': 'Nombre A-Z'},
                {'value': '-name', 'label': 'Nombre Z-A'},
                {'value': 'business', 'label': 'Negocio A-Z'},
                {'value': '-business', 'label': 'Negocio Z-A'},
            ]
        }
        
        return render(request, 'product/product-list.html', context)
        
    except Exception as e:
        logger.error(f"Error en product_list: {str(e)}", exc_info=True)
        messages.error(request, "Ocurrió un error al cargar los productos.")
        return render(request, 'product/product-list.html', {
            'products': [], 
            'businesses': [], 
            'instructions': [],
            'total_products': 0,
            'total_areas': 0,
            'total_variables': 0,
            'recent_products_count': 0,
            'sort_options': []
        })

@login_required
@require_http_methods(["GET"])
def read_product_view(request, pk):
    """Vista optimizada para mostrar detalles de un producto"""
    try:
        # Obtener producto con todas las relaciones necesarias
        product = get_object_or_404(
            Product.objects.select_related(
                'fk_business',
                'fk_business__fk_user'
            ).prefetch_related(
                Prefetch(
                    'fk_product_variable',
                    queryset=Variable.objects.filter(is_active=True).order_by('-id'),
                    to_attr='active_variables'
                ),
                Prefetch(
                    'fk_product_area',
                    queryset=Area.objects.filter(is_active=True).order_by('-id'),
                    to_attr='active_areas'
                )
            ),
            pk=pk,
            is_active=True
        )
        
        # Verificar permisos
        if product.fk_business.fk_user != request.user:
            messages.error(request, "No tienes permisos para ver este producto.")
            return redirect('product:product.list')
        
        current_datetime = timezone.now()
        
        # Obtener datos relacionados con consultas optimizadas
        variables_product = product.active_variables if hasattr(product, 'active_variables') else \
                          Variable.objects.filter(fk_product_id=product.id, is_active=True).order_by('-id')
        
        areas = product.active_areas if hasattr(product, 'active_areas') else \
                Area.objects.filter(fk_product_id=product.id, is_active=True).order_by('-id')
        
        reports = Report.objects.filter(
            fk_product_id=product.id, 
            is_active=True
        ).order_by('-date_created')[:10]
        
        demands = Demand.objects.filter(
            fk_product_id=product.id, 
            is_active=True
        ).select_related('fk_simulation')
        
        # Obtener simulaciones con resultados
        results_simulation = ResultSimulation.objects.filter(
            is_active=True,
            fk_simulation__fk_questionary_result__fk_questionary__fk_product=product
        ).select_related(
            'fk_simulation',
            'fk_simulation__fk_questionary_result__fk_questionary'
        ).order_by('-id')[:20]
        
        simulation_ids = list(results_simulation.values_list('fk_simulation_id', flat=True))
        simulations = Simulation.objects.filter(
            id__in=simulation_ids,
            is_active=True
        ).select_related(
            'fk_questionary_result__fk_questionary',
            'fk_fdp'
        ).order_by('-date_created')
        
        # Paginación para variables y simulaciones
        variables_product = paginate(request, list(variables_product), 18)
        simulations = paginate(request, simulations, 5)
        
        # Productos para el selector
        products = Product.objects.filter(
            is_active=True,
            fk_business__fk_user=request.user
        ).only('id', 'name').order_by('name')

        context = {
            'product': product,
            'variables_product': variables_product,
            'current_datetime': current_datetime,
            'simulations': simulations,
            'reports': reports,
            'areas': areas,
            'demands': demands,
            'products': products,
            'areas_count': len(areas),
            'variables_count': len(product.active_variables) if hasattr(product, 'active_variables') else 0,
        }
        
        return render(request, 'product/product-overview.html', context)
        
    except Product.DoesNotExist:
        messages.error(request, "El producto no existe.")
        return redirect('product:product.list')
    except Exception as e:
        logger.error(f"Error en read_product_view: {str(e)}", exc_info=True)
        messages.error(request, "Ocurrió un error al cargar el producto.")
        return redirect('product:product.list')

@login_required
@require_http_methods(["GET", "POST"])
@transaction.atomic
def create_or_update_product_view(request, pk=None):
    """Vista para crear o actualizar productos con validación mejorada"""
    try:
        product_instance = None
        if pk:
            product_instance = get_object_or_404(
                Product.objects.select_related('fk_business__fk_user'),
                pk=pk
            )
            # Verificar permisos
            if product_instance.fk_business.fk_user != request.user:
                return JsonResponse({
                    'success': False,
                    'errors': {'permission': ['No tienes permisos para editar este producto']}
                }, status=403)
        
        if request.method == 'POST':
            form = ProductForm(request.POST, request.FILES, instance=product_instance)
            
            # Validación adicional
            if form.is_valid():
                # Verificar que el negocio pertenece al usuario
                business = form.cleaned_data.get('fk_business')
                if business.fk_user != request.user:
                    return JsonResponse({
                        'success': False,
                        'errors': {'fk_business': ['No tienes permisos para crear productos en este negocio']}
                    }, status=403)
                
                product = form.save()
                action = "actualizado" if pk else "creado"
                
                # Log de actividad
                logger.info(f"Producto {action}: {product.name} (ID: {product.id}) por usuario {request.user.id}")
                
                messages.success(request, f"¡Producto {action} con éxito!")
                return JsonResponse({
                    'success': True,
                    'product_id': product.id,
                    'redirect_url': reverse('product:product.overview', kwargs={'pk': product.id})
                })
            else:
                # Formatear errores para mejor presentación
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = [str(error) for error in error_list]
                
                return JsonResponse({'success': False, 'errors': errors}, status=400)
        else:
            # GET request - para cargar el formulario
            businesses = Business.objects.filter(
                is_active=True,
                fk_user=request.user
            ).order_by('name')
            
            form = ProductForm(instance=product_instance)
            context = {
                'form': form,
                'businesses': businesses,
                'product': product_instance
            }
            return render(request, 'product/product-form.html', context)
            
    except Exception as e:
        logger.error(f"Error en create_or_update_product: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'errors': {'general': ['Ocurrió un error inesperado. Por favor, intente nuevamente.']}
        }, status=500)

@login_required
@require_POST
@transaction.atomic
def delete_product_view(request, pk):
    """Vista para eliminar productos (soft delete) con validaciones"""
    try:
        product = get_object_or_404(
            Product.objects.select_related('fk_business__fk_user'),
            pk=pk
        )
        
        # Verificar permisos
        if product.fk_business.fk_user != request.user:
            messages.error(request, "No tienes permisos para eliminar este producto.")
            return redirect('product:product.list')
        
        # Verificar si tiene simulaciones activas
        active_simulations = Simulation.objects.filter(
            fk_questionary_result__fk_questionary__fk_product=product,
            is_active=True
        ).exists()
        
        if active_simulations:
            messages.warning(request, "No se puede eliminar el producto porque tiene simulaciones activas.")
            return redirect('product:product.overview', pk=product.id)
        
        # Soft delete
        product.soft_delete()
        
        # Log de actividad
        logger.info(f"Producto eliminado: {product.name} (ID: {product.id}) por usuario {request.user.id}")
        
        messages.success(request, "¡Producto eliminado con éxito!")
        return redirect("product:product.list")
        
    except Exception as e:
        logger.error(f"Error al eliminar producto: {str(e)}", exc_info=True)
        messages.error(request, "Ocurrió un error al eliminar el producto.")
        return redirect("product:product.list")

@login_required
@require_GET
def get_product_details(request, pk):
    """API endpoint para obtener detalles de un producto"""
    try:
        product = get_object_or_404(
            Product.objects.select_related('fk_business__fk_user'),
            pk=pk
        )
        
        # Verificar permisos
        if product.fk_business.fk_user != request.user:
            return JsonResponse({"error": "No tienes permisos para ver este producto"}, status=403)
        
        product_details = {
            "id": product.id,
            "name": product.name,
            "type": product.type,
            "image_src": product.image_src.url if product.image_src else None,
            "fk_business": product.fk_business.id,
            "description": product.description,
            "is_ready": product.is_ready,
            "areas_count": product.areas_count,
            "variables_count": product.variables_count,
            "date_created": product.date_created.isoformat(),
            "last_updated": product.last_updated.isoformat(),
        }
        
        return JsonResponse(product_details)
        
    except Product.DoesNotExist:
        return JsonResponse({"error": "El producto no existe"}, status=404)
    except Exception as e:
        logger.error(f"Error en get_product_details: {str(e)}", exc_info=True)
        return JsonResponse({"error": "Error al obtener detalles del producto"}, status=500)

@login_required
@require_http_methods(["GET"])
def area_overview(request, pk):
    """Vista optimizada para mostrar detalles de un área"""
    try:
        # Obtener el área con todas las relaciones necesarias
        area = get_object_or_404(
            Area.objects.select_related(
                'fk_product',
                'fk_product__fk_business',
                'fk_product__fk_business__fk_user'
            ).prefetch_related(
                Prefetch(
                    'area_equation',  # Usar el related_name correcto
                    queryset=Equation.objects.filter(is_active=True).select_related(
                        'fk_variable1',
                        'fk_variable2',
                        'fk_variable3',
                        'fk_variable4',
                        'fk_variable5'
                    ).order_by('-id')
                )
            ),
            pk=pk,
            is_active=True
        )
        
        # Verificar permisos
        if area.fk_product.fk_business.fk_user != request.user:
            messages.error(request, "No tienes permisos para ver esta área.")
            return redirect('product:product.list')
        
        current_datetime = timezone.now()
        
        # Obtener ecuaciones del área
        equations_area = area.area_equation.all()
        
        # Obtener todas las variables únicas utilizadas en las ecuaciones del área
        variables_used = set()
        variables_data = []
        
        for equation in equations_area:
            # Recopilar variables de cada ecuación
            equation_variables = []
            for var_field in ['fk_variable1', 'fk_variable2', 'fk_variable3', 'fk_variable4', 'fk_variable5']:
                variable = getattr(equation, var_field, None)
                if variable:
                    variables_used.add(variable.id)
                    equation_variables.append(variable)
            
            # Guardar datos para el gráfico
            variables_data.append({
                'equation': equation,
                'variables': equation_variables
            })
        
        # Obtener detalles completos de las variables utilizadas
        variables_details = Variable.objects.filter(
            id__in=variables_used,
            is_active=True
        ).only('id', 'name', 'description', 'image_src')
        
        # Contar estadísticas
        total_equations = equations_area.count()
        total_variables = len(variables_used)
        total_relations = sum(len(eq_data['variables']) for eq_data in variables_data)
        
        # Paginación para ecuaciones
        equations_area = paginate(request, equations_area, 10)
        
        # Preparar datos para el gráfico de variables
        graph_data = {
            'variables': [
                {
                    'id': var.id,
                    'name': var.name,
                    'description': var.description,
                    'image_url': var.get_photo_url() if hasattr(var, 'get_photo_url') else None
                } for var in variables_details
            ],
            'equations': [
                {
                    'id': eq_data['equation'].id,
                    'name': eq_data['equation'].name,
                    'expression': eq_data['equation'].expression,
                    'variables': [var.id for var in eq_data['variables']]
                } for eq_data in variables_data
            ]
        }
        
        # Obtener todas las variables del producto para el modal de ecuaciones
        product_variables = Variable.objects.filter(
            fk_product=area.fk_product,
            is_active=True
        ).order_by('name')
        
        context = {
            'area': area,
            'equations_area': equations_area,
            'current_datetime': current_datetime,
            'total_equations': total_equations,
            'total_variables': total_variables,
            'total_relations': total_relations,
            'variables_details': variables_details,
            'graph_data': json.dumps(graph_data),  # Convertir a JSON para el template
            'product_variables': product_variables,
        }
        
        return render(request, 'product/area-overview.html', context)
        
    except Area.DoesNotExist:
        messages.error(request, "El área no existe.")
        return redirect('product:product.list')
    except Exception as e:
        logger.error(f"Error en area_overview: {str(e)}", exc_info=True)
        messages.error(request, "Ocurrió un error al cargar el área.")
        return redirect('product:product.list')

@login_required
@require_http_methods(["GET", "POST"])
@transaction.atomic
def create_or_update_area_view(request, pk=None):
    """Vista para crear o actualizar áreas con validación mejorada"""
    try:
        area_instance = None
        if pk:
            area_instance = get_object_or_404(
                Area.objects.select_related(
                    'fk_product__fk_business__fk_user'
                ),
                pk=pk
            )
            # Verificar permisos
            if area_instance.fk_product.fk_business.fk_user != request.user:
                return JsonResponse({
                    'success': False,
                    'errors': {'permission': ['No tienes permisos para editar esta área']}
                }, status=403)
        
        if request.method == 'POST':
            form = AreaForm(request.POST, request.FILES, instance=area_instance)
            
            if form.is_valid():
                # Verificar que el producto pertenece al usuario
                product = form.cleaned_data.get('fk_product')
                if product.fk_business.fk_user != request.user:
                    return JsonResponse({
                        'success': False,
                        'errors': {'fk_product': ['No tienes permisos para crear áreas en este producto']}
                    }, status=403)
                
                area = form.save()
                action = "actualizada" if pk else "creada"
                
                # Log de actividad
                logger.info(f"Área {action}: {area.name} (ID: {area.id}) por usuario {request.user.id}")
                
                messages.success(request, f"¡Área {action} con éxito!")
                return JsonResponse({
                    'success': True,
                    'area_id': area.id,
                    'redirect_url': reverse('product:area.overview', kwargs={'pk': area.id})
                })
            else:
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = [str(error) for error in error_list]
                
                return JsonResponse({'success': False, 'errors': errors}, status=400)
        else:
            # GET request
            products = Product.objects.filter(
                is_active=True,
                fk_business__fk_user=request.user
            ).order_by('name')
            
            form = AreaForm(instance=area_instance)
            context = {
                'form': form,
                'products': products,
                'area': area_instance
            }
            return render(request, 'product/area-form.html', context)
            
    except Exception as e:
        logger.error(f"Error en create_or_update_area: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'errors': {'general': ['Ocurrió un error inesperado. Por favor, intente nuevamente.']}
        }, status=500)

@login_required
@require_POST
@transaction.atomic
def delete_area_view(request, pk):
    """Vista para eliminar áreas (soft delete) con validaciones"""
    try:
        area = get_object_or_404(
            Area.objects.select_related(
                'fk_product__fk_business__fk_user'
            ),
            pk=pk
        )
        
        # Verificar permisos
        if area.fk_product.fk_business.fk_user != request.user:
            messages.error(request, "No tienes permisos para eliminar esta área.")
            return redirect('product:product.list')
        
        product_id = area.fk_product.id
        
        # Verificar si tiene ecuaciones activas
        active_equations = Equation.objects.filter(
            fk_area=area,
            is_active=True
        ).exists()
        
        if active_equations:
            messages.warning(request, "No se puede eliminar el área porque tiene ecuaciones activas.")
            return redirect('product:area.overview', pk=area.id)
        
        # Soft delete
        area.soft_delete()
        
        # Log de actividad
        logger.info(f"Área eliminada: {area.name} (ID: {area.id}) por usuario {request.user.id}")
        
        messages.success(request, "¡Área eliminada con éxito!")
        return redirect("product:product.overview", pk=product_id)
        
    except Exception as e:
        logger.error(f"Error al eliminar área: {str(e)}", exc_info=True)
        messages.error(request, "Ocurrió un error al eliminar el área.")
        return redirect('product:product.list')

@login_required
@require_GET
def get_area_details_view(request, pk):
    """API endpoint para obtener detalles de un área"""
    try:
        area = get_object_or_404(
            Area.objects.select_related(
                'fk_product__fk_business__fk_user'
            ),
            pk=pk
        )
        
        # Verificar permisos
        if area.fk_product.fk_business.fk_user != request.user:
            return JsonResponse({"error": "No tienes permisos para ver esta área"}, status=403)
        
        area_details = {
            "id": area.id,
            "name": area.name,
            "image_src": area.image_src.url if area.image_src else None,
            "fk_product": area.fk_product.id,
            "description": area.description,
            "is_checked_for_simulation": area.is_checked_for_simulation,
            "equations_count": area.equations_count,
            "date_created": area.date_created.isoformat(),
            "last_updated": area.last_updated.isoformat(),
        }
        
        return JsonResponse(area_details)
        
    except Area.DoesNotExist:
        return JsonResponse({"error": "El área no existe"}, status=404)
    except Exception as e:
        logger.error(f"Error en get_area_details: {str(e)}", exc_info=True)
        return JsonResponse({"error": "Error al obtener detalles del área"}, status=500)