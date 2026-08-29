import re
import logging
import os
import uuid
from django.shortcuts import render, get_object_or_404, redirect
from .models import Variable, Equation, EquationResult
from product.models import Product
from business.models import Business
from .forms import VariableForm, EquationForm
from pages.models import Instructions
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.conf import settings
from django.http import JsonResponse
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import ObjectDoesNotExist
from sympy import symbols, Eq, solve
from django.db.models import Q, Count
from django.db import models
from tenancy.abuse import consume_abuse_budget

logger = logging.getLogger(__name__)


def _generate_with_claude(prompt, max_tokens, organization=None, actor_id=None):
    """Genera texto con Claude sin convertir la ausencia/falla del LLM en un 500."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key or organization is None:
        return None

    from tenancy.services import has_entitlement

    if not has_entitlement(organization, "ai_analysis"):
        return None
    allowed, _window = consume_abuse_budget("ai", organization, actor_id or "organization")
    if not allowed:
        return None

    correlation_id = uuid.uuid4()
    try:
        import anthropic

        response = anthropic.Anthropic(api_key=api_key).messages.create(
            model=getattr(settings, "ANTHROPIC_MODEL", "claude-sonnet-5"),
            max_tokens=max_tokens,
            cache_control={"type": "ephemeral"},
            messages=[{"role": "user", "content": prompt}],
        )
        text_blocks = [
            block.text for block in response.content
            if getattr(block, "type", None) == "text"
        ]
        from tenancy.models import UsageEvent
        from tenancy.services import record_resource_usage, record_usage

        usage = getattr(response, "usage", None)
        metadata = {
            "model": getattr(settings, "ANTHROPIC_MODEL", "claude-sonnet-5"),
            "provider": "anthropic",
            "outcome": "success",
            "cost": "COST_UNKNOWN",
        }
        record_usage(
            organization, UsageEvent.Metric.AI_CALL, 1,
            "variable.claude", correlation_id, metadata,
        )
        for resource, quantity in (
            ("AI_INPUT_TOKENS", getattr(usage, "input_tokens", None)),
            ("AI_OUTPUT_TOKENS", getattr(usage, "output_tokens", None)),
        ):
            if quantity is not None:
                record_resource_usage(
                    organization, resource, quantity, "tokens",
                    "variable.claude", correlation_id, metadata,
                )
        return "".join(text_blocks).strip() or None
    except Exception:
        logger.warning("Claude no disponible; se usará el fallback local.", exc_info=True)
        from tenancy.models import UsageEvent
        from tenancy.services import record_usage

        record_usage(
            organization, UsageEvent.Metric.AI_CALL, 1,
            "variable.claude", correlation_id,
            {"provider": "anthropic", "outcome": "error", "cost": "COST_UNKNOWN"},
        )
        return None


def _fallback_initials(variable_name):
    words = variable_name.split()
    initials = ''.join(word[0].upper() for word in words[:4] if word)
    return initials.ljust(4, 'X')[:4]


def _normalise_initials(generated, variable_name):
    initials = re.sub(r"[^A-Za-z0-9]", "", generated or "").upper()
    return initials[:4] if len(initials) >= 4 else _fallback_initials(variable_name)


class AppsView(LoginRequiredMixin, TemplateView):
    pass

def _is_ajax(request):
    """Reemplazo de HttpRequest.is_ajax(), eliminado en Django 3.1+."""
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _variables_for_user(request):
    """Queryset de Variable restringido al DUEÑO real (cierra IDOR de esta app).

    La propiedad se establece por la cadena fk_product -> fk_business -> fk_user,
    igual que ``_reports_for_user`` en report/views.py y el filtro directo usado
    en finance/views.py. No filtra ``is_active`` para no cambiar el comportamiento
    previo de los handlers (que ya operaban sobre variables inactivas).
    """
    return Variable.objects.filter(fk_product__fk_business__fk_user=request.user)


def _equations_for_user(request):
    """Queryset de Equation restringido al DUEÑO real (cierra IDOR de esta app).

    ``Equation`` no tiene fk_product/fk_business directo; ``fk_variable1`` es la
    única FK obligatoria (variable2-5 son opcionales), así que la cadena de
    propiedad se resuelve a través de ella.
    """
    return Equation.objects.filter(
        fk_variable1__fk_product__fk_business__fk_user=request.user
    )

VARIABLES_PER_PAGE2 = 24

@login_required
def variable_list(request):
    try:
        # Parámetros de filtro
        product_id = request.GET.get('product_id', 'All')
        search = request.GET.get('search', '')
        type_filter = request.GET.get('type', '')
        sort_by = request.GET.get('sort', '-date_created')
        
        # Obtener negocios del usuario
        businesses = Business.objects.filter(is_active=True, fk_user=request.user).order_by('-id')
        
        # Obtener productos
        products = Product.objects.filter(
            is_active=True, 
            fk_business__in=businesses, 
            fk_business__fk_user=request.user
        ).order_by('-id')
        
        # Construir condiciones de filtro para variables
        variables_conditions = Q(
            is_active=True, 
            fk_product__in=products, 
            fk_product__fk_business__fk_user=request.user
        )
        
        # Filtro por producto
        if product_id != 'All' and product_id:
            try:
                product_id_int = int(product_id)
                variables_conditions &= Q(fk_product_id=product_id_int)
            except (ValueError, TypeError):
                pass
        
        # Filtro por tipo
        if type_filter:
            try:
                type_filter_int = int(type_filter)
                variables_conditions &= Q(type=type_filter_int)
            except (ValueError, TypeError):
                pass
        
        # Filtro por búsqueda
        if search:
            search_conditions = (
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(initials__icontains=search) |
                Q(unit__icontains=search)
            )
            variables_conditions &= search_conditions
        
        # Obtener variables base
        variables_queryset = Variable.objects.filter(variables_conditions).select_related('fk_product', 'fk_product__fk_business')
        
        # Agregar cálculos adicionales para cada variable
        variables_list = []
        for variable in variables_queryset:
            # Contar ecuaciones donde aparece esta variable en cualquier posición
            equation_count = Equation.objects.filter(
                Q(fk_variable1=variable) |
                Q(fk_variable2=variable) |
                Q(fk_variable3=variable) |
                Q(fk_variable4=variable) |
                Q(fk_variable5=variable),
                is_active=True
            ).count()
            
            # Agregar atributos calculados
            variable.equation_count = equation_count
            variable.usage_progress = min((equation_count * 10), 100)
            
            # Determinar nivel de criticidad
            if equation_count > 5:
                variable.criticality = 'high'
                variable.criticality_label = 'Alta'
            elif equation_count > 2:
                variable.criticality = 'medium' 
                variable.criticality_label = 'Media'
            elif equation_count > 0:
                variable.criticality = 'low'
                variable.criticality_label = 'Baja'
            else:
                variable.criticality = 'none'
                variable.criticality_label = 'Ninguna'
                
            variables_list.append(variable)
        
        # Convertir de vuelta a queryset para mantener compatibilidad
        variables = variables_queryset
        
        # Ordenamiento
        valid_sort_fields = [
            'date_created', '-date_created',
            'name', '-name',
            'type', '-type',
            'last_update', '-last_update'
        ]
        
        if sort_by in valid_sort_fields:
            variables = variables.order_by(sort_by)
        else:
            variables = variables.order_by('-date_created')
        
        # Paginación
        paginator = Paginator(variables, VARIABLES_PER_PAGE2)
        page = request.GET.get('page', 1)

        try:
            variables_page = paginator.page(page)
        except PageNotAnInteger:
            variables_page = paginator.page(1)
        except EmptyPage:
            variables_page = paginator.page(paginator.num_pages)

        # Estadísticas para el dashboard
        stats = {
            'exogenas': variables_queryset.filter(type=1).count(),
            'estado': variables_queryset.filter(type=2).count(), 
            'endogenas': variables_queryset.filter(type=3).count(),
        }

        # Obtener instrucciones
        try:
            instructions = Instructions.objects.filter(is_active=True).order_by('-id')
        except:
            instructions = []

        context = {
            'variables': variables_page, 
            'products': products,
            'instructions': instructions,
            'stats': stats,
            'current_filters': {
                'product_id': product_id,
                'search': search,
                'type': type_filter,
                'sort': sort_by,
            }
        }
        
        return render(request, 'variable/variable-list.html', context)
        
    except Exception as e:
        # Log del error para debugging
        import traceback
        logger.exception("Error en variable_list: %s", e)
        
        messages.error(request, f"Ocurrió un error al cargar las variables: {str(e)}")
        
        # Contexto mínimo para evitar errores en el template
        context = {
            'variables': [],
            'products': [],
            'instructions': [],
            'stats': {'exogenas': 0, 'estado': 0, 'endogenas': 0},
            'current_filters': {},
        }
        return render(request, 'variable/variable-list.html', context)

VARIABLES_PER_PAGE = 4

@login_required
def variable_overview(request, pk):
    try:
        # Restringido al dueño real (cierra IDOR).
        variable = get_object_or_404(_variables_for_user(request), pk=pk)
        product_id = variable.fk_product.id
        variable_id = variable.id

        # Variables relacionadas del mismo producto
        variables_related = Variable.objects.filter(
            is_active=True, 
            fk_product_id=product_id
        ).exclude(id=variable_id).select_related('fk_product').order_by('-id')

        # Ecuaciones relacionadas - buscar en todas las posiciones donde puede aparecer la variable
        equations = Equation.objects.filter(
            Q(fk_variable1_id=variable_id) |
            Q(fk_variable2_id=variable_id) |
            Q(fk_variable3_id=variable_id) |
            Q(fk_variable4_id=variable_id) |
            Q(fk_variable5_id=variable_id),
            is_active=True
        ).order_by('-id')
        
        # Paginación para variables relacionadas
        paginator = Paginator(variables_related, VARIABLES_PER_PAGE)
        page = request.GET.get('page', 1)

        try:
            variables_related_page = paginator.page(page)
        except PageNotAnInteger:
            variables_related_page = paginator.page(1)
        except EmptyPage:
            variables_related_page = paginator.page(paginator.num_pages)
            
        context = {
            'variable': variable, 
            'variables_related': variables_related_page,
            'equations': equations
        }
        
        return render(request, "variable/variable-overview.html", context)

    except Http404:
        # get_object_or_404 con filtro de dueño -> 404 real si no existe o no le pertenece.
        raise
    except Exception as e:
        logger.error(f"Error en variable_overview: {str(e)}")
        messages.error(request, f"Ocurrió un error al cargar la variable: {str(e)}")
        return redirect('variable:variable.list')

@login_required
def create_or_update_variable_view(request, pk=None):
    variable = None
    if pk:
        # Restringido al dueño real (cierra IDOR): 404 si no existe o no le pertenece,
        # en vez de tragarse el error y caer silenciosamente al flujo de creación.
        variable = get_object_or_404(_variables_for_user(request), pk=pk)

    if request.method == 'POST':
        form = VariableForm(request.POST, request.FILES, instance=variable)
        try:
            if form.is_valid():
                # Solo generar iniciales para nuevas variables
                if pk is None:
                    variable_name = form.cleaned_data.get('name', '')
                    
                    initial_prompt = (
                        "Generate initials for the following variable using exactly "
                        "four characters. Return only the initials: "
                        f"{variable_name}"
                    )
                    initials = _normalise_initials(
                        _generate_with_claude(
                            initial_prompt,
                            max_tokens=8,
                            organization=request.organization,
                            actor_id=request.user.pk,
                        ),
                        variable_name,
                    )

                    form.instance.initials = initials

                variable = form.save()
                messages.success(request, 'Variable creada exitosamente' if pk is None else 'Variable actualizada exitosamente')
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'errors': form.errors})
                
        except Exception as e:
            logger.error(f"Error al guardar variable: {str(e)}")
            return JsonResponse({'success': False, 'error': 'Ocurrió un error al guardar la variable'})
    else:
        try:
            # Obtener productos para el usuario actual
            businesses = Business.objects.filter(is_active=True, fk_user=request.user)
            products = Product.objects.filter(is_active=True, fk_business__in=businesses)
            
            form = VariableForm(instance=variable)
            
            context = {
                'form': form, 
                'variable': variable,
                'products': products
            }
            return render(request, 'variable/variable-form.html', context)
            
        except Exception as e:
            logger.error(f"Error al cargar formulario: {str(e)}")
            messages.error(request, "Error al cargar el formulario")
            return redirect('variable:variable.list')

@login_required
def delete_variable_view(request, pk):
    try:
        if request.method == 'POST':
            # Restringido al dueño real (cierra IDOR).
            variable = get_object_or_404(_variables_for_user(request), pk=pk)
            variable.is_active = False
            variable.save()
            messages.success(request, "Variable eliminada exitosamente")
            return redirect("variable:variable.list")
        else:
            messages.error(request, "Método de petición inválido")
            return HttpResponse("Método de petición inválido", status=405)

    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar variable: {str(e)}")
        messages.error(request, f"Ocurrió un error al eliminar la variable: {str(e)}")
        return redirect("variable:variable.list")

@login_required
def get_variable_details_view(request, pk):
    try:
        if request.method == 'GET':
            # Restringido al dueño real (cierra IDOR).
            variable = get_object_or_404(_variables_for_user(request), id=pk)
            variable_details = {
                "name": variable.name,
                "type": variable.type,
                "fk_product": variable.fk_product.id,
                "unit": variable.unit or "",
                "image_src": variable.get_photo_url(),
                "initials": variable.initials,
                "description": variable.description,
            }
            return JsonResponse(variable_details)
    except (Http404, ObjectDoesNotExist):
        # get_object_or_404 lanza Http404 (no ObjectDoesNotExist) al no encontrar
        # coincidencia; se capturan ambas por robustez.
        return JsonResponse({"error": "La variable no existe"}, status=404)
    except Exception as e:
        logger.error(f"Error al obtener detalles: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def create_or_update_equation_view(request, pk=None):
    equation = None
    if pk:
        # Restringido al dueño real (cierra IDOR): 404 si no existe o no le
        # pertenece, en vez de tragarse el error y caer al flujo de creación.
        equation = get_object_or_404(_equations_for_user(request), pk=pk)

    if request.method in ['POST', 'PUT']:
        form = EquationForm(request.POST, request.FILES, instance=equation)
        try:
            if form.is_valid():
                equation = form.save()
                messages.success(request, 'Ecuación creada exitosamente' if pk is None else 'Ecuación actualizada exitosamente')

                if request.headers.get('Content-Type') == 'application/json' or _is_ajax(request):
                    return JsonResponse({'success': True})
                else:
                    return redirect("variable:variable.overview", pk=equation.fk_variable1.pk)
            else:
                if request.headers.get('Content-Type') == 'application/json' or _is_ajax(request):
                    return JsonResponse({'success': False, 'errors': form.errors})
                else:
                    # Cargar datos necesarios para re-renderizar
                    businesses = Business.objects.filter(is_active=True, fk_user=request.user)
                    products = Product.objects.filter(is_active=True, fk_business__in=businesses)
                    variables = Variable.objects.filter(is_active=True, fk_product__in=products)
                    
                    context = {
                        'form': form,
                        'equation': equation,
                        'variables': variables,
                        'products': products
                    }
                    return render(request, "variable/equation-form.html", context)
                    
        except Exception as e:
            logger.error(f"Error al guardar ecuación: {str(e)}")
            if request.headers.get('Content-Type') == 'application/json' or _is_ajax(request):
                return JsonResponse({'success': False, 'error': 'Ocurrió un error al guardar la ecuación'})
            else:
                messages.error(request, "Error al guardar la ecuación")
                return HttpResponse(status=500)
    else:
        try:
            # Obtener datos requeridos para el formulario
            businesses = Business.objects.filter(is_active=True, fk_user=request.user)
            products = Product.objects.filter(is_active=True, fk_business__in=businesses)
            variables = Variable.objects.filter(is_active=True, fk_product__in=products)
            
            form = EquationForm(instance=equation)
            
            context = {
                'form': form,
                'equation': equation,
                'variables': variables,
                'products': products
            }
            return render(request, 'variable/equation-form.html', context)
            
        except Exception as e:
            logger.error(f"Error al cargar formulario de ecuación: {str(e)}")
            messages.error(request, "Error al cargar el formulario")
            return redirect('variable:variable.list')

@login_required
def delete_equation_view(request, pk):
    try:
        # Restringido al dueño real (cierra IDOR).
        equation = get_object_or_404(_equations_for_user(request), pk=pk)
        variable_pk = equation.fk_variable1.pk if equation.fk_variable1 else None
        equation.is_active = False
        equation.save()
        messages.success(request, "Ecuación eliminada exitosamente")

        if variable_pk:
            return redirect("variable:variable.overview", pk=variable_pk)
        else:
            return redirect("variable:variable.list")

    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar ecuación: {str(e)}")
        messages.error(request, f"Ocurrió un error al eliminar la ecuación: {str(e)}")
        return redirect("variable:variable.list")

@login_required
def get_equation_details(request, pk):
    try:
        if request.method == 'GET':
            # Restringido al dueño real (cierra IDOR).
            equation = get_object_or_404(_equations_for_user(request), id=pk)
            equation_details = {
                "name": equation.name,
                "expression": equation.expression,
                "fk_area": equation.fk_area.id if equation.fk_area else None,
                "fk_variable1": equation.fk_variable1.id if equation.fk_variable1 else None,
                "fk_variable2": equation.fk_variable2.id if equation.fk_variable2 else None,
                "fk_variable3": equation.fk_variable3.id if equation.fk_variable3 else None,
                "fk_variable4": equation.fk_variable4.id if equation.fk_variable4 else None,
                "fk_variable5": equation.fk_variable5.id if equation.fk_variable5 else None,
                "description": equation.description,
            }
            return JsonResponse(equation_details)
    except (Http404, ObjectDoesNotExist):
        # get_object_or_404 lanza Http404 (no ObjectDoesNotExist) al no encontrar
        # coincidencia; se capturan ambas por robustez.
        return JsonResponse({"error": "La ecuación no existe"}, status=404)
    except Exception as e:
        logger.error(f"Error al obtener detalles de ecuación: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

# SEGURIDAD: nombres alfabéticos permitidos en una ecuación de usuario.
# `parse_expr`/`sympify` de SymPy NO son seguros por sí solos frente a entrada no
# confiable: expresiones como `().__class__.__bases__[0].__subclasses__()` permiten
# escapar el sandbox y llegar a RCE. Por eso se valida con lista blanca ANTES de parsear.
_FUNCIONES_MATEMATICAS_PERMITIDAS = frozenset({
    'x', 'sin', 'cos', 'tan', 'asin', 'acos', 'atan',
    'exp', 'log', 'ln', 'sqrt', 'abs', 'pi', 'E',
})


def _validar_expresion_matematica(expr_str: str) -> str:
    """Rechaza cualquier expresión que no sea aritmética pura sobre `x`."""
    if not expr_str or len(expr_str) > 500:
        raise ValueError('Expresión vacía o demasiado larga.')
    # Prohibir guion bajo (dunder attributes) y corchetes (indexación/escape sandbox).
    if '_' in expr_str or '[' in expr_str or ']' in expr_str or '{' in expr_str:
        raise ValueError('Carácter no permitido en la expresión.')
    # Solo caracteres seguros: dígitos, letras (validadas aparte), operadores y espacios.
    if not re.fullmatch(r'[0-9A-Za-z+\-*/^(). \t]*', expr_str):
        raise ValueError('Carácter no permitido en la expresión.')
    # El punto solo puede ser separador decimal (entre dígitos), nunca acceso a atributos.
    if re.search(r'\.(?!\d)|(?<!\d)\.', expr_str):
        raise ValueError('Uso de punto no permitido.')
    # Toda secuencia alfabética debe ser `x` o una función matemática conocida.
    for nombre in re.findall(r'[A-Za-z]+', expr_str):
        if nombre not in _FUNCIONES_MATEMATICAS_PERMITIDAS:
            raise ValueError(f'Nombre no permitido: {nombre}')
    return expr_str


@login_required
def solve_equation(request):
    if request.method == 'POST':
        equation_str = request.POST.get('equation', '')
        x = symbols('x')

        try:
            # SEGURIDAD: nunca usar eval() sobre entrada del usuario (RCE).
            # Validación estricta por lista blanca + parseo restringido a {x}.
            _validar_expresion_matematica(equation_str)
            from sympy.parsing.sympy_parser import parse_expr
            expr = parse_expr(equation_str, local_dict={'x': x}, evaluate=True)
            equation = Eq(expr, 0)
            solution = solve(equation, x)
        except Exception as e:
            error_message = str(e)
            return render(request, 'error_template.html', {'error_message': error_message})

        return render(request, 'result_template.html', {'solution': solution})

    return render(request, 'input_template.html')

def generate_variable_questions(request, variable):
    try:
        django_variable = f"{variable.name} = models.{variable.get_type_display()}Field()"
        prompt = f"Create a question to gather and add precise data to a financial test form for the company's Variable:\n\n{django_variable}\n\nQuestion:"
        
        generated = _generate_with_claude(
            prompt,
            max_tokens=100,
            organization=request.organization,
            actor_id=request.user.pk,
        )
        question = [generated or f"¿Cuál es el valor para {variable.name}?"]
            
    except Exception as e:
        logger.error(f"Error generando pregunta: {e}", exc_info=True)
        # Fallback question
        question = [f"¿Cuál es el valor para {variable.name}?"]
    
    return question

@login_required
def generate_questions_for_variables(request):
    try:
        businesses = Business.objects.filter(is_active=True, fk_user=request.user)
        products = Product.objects.filter(is_active=True, fk_business__in=businesses)
        variables = Variable.objects.filter(is_active=True, fk_product__in=products)
        
        generated_questions_list = []
        for variable in variables:
            generated_questions = generate_variable_questions(request, variable)
            generated_questions_list.append((variable, generated_questions))
        
        context = {
            "generated_questions_list": generated_questions_list
        }
        return render(request, "questionary/questionary-main.html", context)
        
    except Exception as e:
        logger.error(f"Error generando preguntas: {str(e)}")
        messages.error(request, "Error al generar las preguntas")
        return redirect('variable:variable.list')
