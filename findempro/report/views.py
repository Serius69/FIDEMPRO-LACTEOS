from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.conf import settings
from django.http import JsonResponse, HttpResponse, FileResponse, HttpResponseForbidden, Http404
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from .models import Report
from .forms import ReportForm, SimulationReportForm
from variable.models import Variable
from product.models import Product
import logging
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from decimal import Decimal
import traceback
from celery.result import AsyncResult

# Configure logger
logger = logging.getLogger(__name__)


def _reports_for_user(user):
    """Queryset base de reportes restringido al DUEÑO real.

    El modelo Report no tiene ``created_by``; la propiedad se establece por la
    cadena fk_product -> fk_business -> fk_user. Los usuarios staff ven todos
    los reportes. Esto cierra el IDOR de la app report (los guardas previos
    ``hasattr(report, 'created_by')`` siempre eran falsos y no protegían nada).
    """
    qs = Report.objects.all()
    if not getattr(user, 'is_staff', False):
        qs = qs.filter(fk_product__fk_business__fk_user=user)
    return qs


def _sanitize_json_numbers(obj):
    """Reemplaza recursivamente inf/-inf/nan por None en dicts/listas.

    JSONField sobre jsonb (Postgres) rechaza Infinity/NaN; el motor sqlite los
    serializa como 'Infinity'/'NaN' inválidos para otros consumidores. Se
    aplica al contenido de los reportes antes de persistirlo.
    """
    import math
    if isinstance(obj, dict):
        return {k: _sanitize_json_numbers(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize_json_numbers(v) for v in obj]
    if isinstance(obj, float) and (math.isinf(obj) or math.isnan(obj)):
        return None
    return obj

class AppsView(LoginRequiredMixin, TemplateView):
    """Main apps view for reports module."""
    template_name = 'report/apps.html'

# List View with improved error handling and caching
@login_required
def report_list(request):
    """Display paginated list of reports with search functionality."""
    try:
        search_query = request.GET.get('search', '').strip()
        filter_type = request.GET.get('type', '')
        filter_status = request.GET.get('status', '')
        sort_by = request.GET.get('sort', '-date_created')

        # Base queryset restringido al dueño (cierra IDOR). Sin @cache_page
        # porque el resultado ahora es específico por usuario.
        reports = _reports_for_user(request.user).select_related('fk_product')
        
        # Apply filters
        if search_query:
            reports = reports.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(fk_product__name__icontains=search_query)
            )
        
        if filter_type:
            reports = reports.filter(report_type=filter_type)
            
        if filter_status:
            reports = reports.filter(is_active=(filter_status == 'active'))
        
        # Apply sorting
        valid_sort_fields = ['title', 'date_created', '-date_created', 'last_updated', '-last_updated']
        if sort_by in valid_sort_fields:
            reports = reports.order_by(sort_by)
        else:
            reports = reports.order_by('-date_created')
        
        # Pagination with validation
        page_size = min(int(request.GET.get('page_size', 10)), 50)  # Max 50 items per page
        paginator = Paginator(reports, page_size)
        page_number = request.GET.get('page', 1)
        
        try:
            page_obj = paginator.get_page(page_number)
        except Exception as e:
            logger.warning(f"Invalid page number: {page_number}")
            page_obj = paginator.get_page(1)
        
        # Get statistics (restringidas al usuario)
        stats = get_report_statistics(request.user)
        
        context = {
            'reports': page_obj,
            'search_query': search_query,
            'filter_type': filter_type,
            'filter_status': filter_status,
            'sort_by': sort_by,
            'total_reports': reports.count(),
            'stats': stats,
            'page_sizes': [10, 25, 50],
            'current_page_size': page_size,
        }
        
        return render(request, 'report/report-list.html', context)
        
    except Exception as e:
        logger.exception("Error in report_list view")
        messages.error(request, "Ocurrió un error al cargar los reportes. Por favor, inténtelo de nuevo.")
        
        # Return empty context on error
        context = {
            'reports': Paginator([], 10).get_page(1),
            'search_query': '',
            'total_reports': 0,
            'stats': {},
        }
        return render(request, 'report/report-list.html', context)

def get_report_statistics(user=None) -> Dict[str, Any]:
    """Get report statistics for dashboard (restringidas al dueño)."""
    try:
        base = Report.objects.all()
        if user is not None and not getattr(user, 'is_staff', False):
            base = base.filter(fk_product__fk_business__fk_user=user)
            cache_key = f'report_statistics_{user.id}'
        else:
            cache_key = 'report_statistics'
        stats = cache.get(cache_key)

        if stats is None:
            total_reports = base.count()
            active_reports = base.filter(is_active=True).count()
            recent_reports = base.filter(
                date_created__gte=timezone.now() - timedelta(days=7)
            ).count()

            # Products with most reports
            top_products = base.filter(
                fk_product__isnull=False
            ).values(
                'fk_product__name'
            ).annotate(
                count=Count('id')
            ).order_by('-count')[:5]
            
            stats = {
                'total_reports': total_reports,
                'active_reports': active_reports,
                'recent_reports': recent_reports,
                'top_products': list(top_products),
            }
            
            # Cache for 30 minutes
            cache.set(cache_key, stats, 60 * 30)
        
        return stats
        
    except Exception as e:
        logger.exception("Error getting report statistics")
        return {}

# Detail View with enhanced error handling
@login_required
def report_detail(request, pk):
    """Display detailed view of a specific report."""
    try:
        report = get_object_or_404(
            _reports_for_user(request.user).select_related('fk_product'), pk=pk
        )

        # Track view count (optional)
        if hasattr(report, 'view_count'):
            report.view_count += 1
            report.save(update_fields=['view_count'])
        
        # Get related reports
        related_reports = []
        if report.fk_product:
            related_reports = Report.objects.filter(
                fk_product=report.fk_product
            ).exclude(pk=pk).order_by('-date_created')[:3]
        
        context = {
            'report': report,
            'current_datetime': timezone.now(),
            'related_reports': related_reports,
            # El queryset ya restringe al dueño (o staff): quien puede verlo, puede editarlo.
            'can_edit': True,
        }
        
        return render(request, 'report/report-detail.html', context)
        
    except Exception as e:
        logger.exception(f"Error in report_detail view for pk={pk}")
        messages.error(request, f"Error al cargar el reporte: {str(e)}")
        return redirect('report:report.list')

# Create View with improved validation
@login_required
@require_http_methods(["GET", "POST"])
def report_create(request):
    """Create a new report."""
    try:
        if request.method == 'POST':
            form = ReportForm(request.POST, request.FILES)
            
            if form.is_valid():
                report = form.save(commit=False)
                
                # Set additional fields
                if hasattr(report, 'created_by'):
                    report.created_by = request.user
                
                # Validate content if it's JSON
                if hasattr(report, 'content') and isinstance(report.content, str):
                    try:
                        json.loads(report.content)
                    except json.JSONDecodeError:
                        messages.error(request, 'El contenido debe ser JSON válido.')
                        return render(request, 'report/report-create.html', {'form': form})
                
                report.save()
                
                # Clear cache
                cache.delete('report_statistics')
                
                messages.success(request, f'Reporte "{report.title}" creado exitosamente.')
                return redirect('report:report.detail', pk=report.pk)
            else:
                messages.error(request, 'Por favor corrige los errores en el formulario.')
        else:
            form = ReportForm()
        
        # Get available products for form
        products = Product.objects.filter(is_active=True).order_by('name')
        
        context = {
            'form': form,
            'products': products,
            'report_types': getattr(Report, 'REPORT_TYPE_CHOICES', []),
        }
        
        return render(request, 'report/report-create.html', context)
        
    except Exception as e:
        logger.exception("Error in report_create view")
        messages.error(request, f"Error al crear el reporte: {str(e)}")
        return redirect('report:report.list')

# Update View with permission checks
@login_required
def report_update(request, pk):
    """Update an existing report."""
    try:
        # Restringido al dueño real (cierra IDOR); staff incluido en el helper.
        report = get_object_or_404(_reports_for_user(request.user), pk=pk)

        if request.method == 'POST':
            form = ReportForm(request.POST, request.FILES, instance=report)
            
            if form.is_valid():
                updated_report = form.save(commit=False)
                updated_report.last_updated = timezone.now()
                updated_report.save()
                
                # Clear cache
                cache.delete('report_statistics')
                
                messages.success(request, f'Reporte "{updated_report.title}" actualizado exitosamente.')
                return redirect('report:report.detail', pk=updated_report.pk)
            else:
                messages.error(request, 'Por favor corrige los errores en el formulario.')
        else:
            form = ReportForm(instance=report)
        
        context = {
            'form': form,
            'report': report,
            'is_update': True,
        }
        
        return render(request, 'report/report-update.html', context)
        
    except Exception as e:
        logger.exception(f"Error in report_update view for pk={pk}")
        messages.error(request, f"Error al actualizar el reporte: {str(e)}")
        return redirect('report:report.list')

# Delete View with soft delete option
@login_required
def report_delete(request, pk):
    """Delete a report with confirmation."""
    try:
        # Restringido al dueño real (cierra IDOR); staff incluido en el helper.
        report = get_object_or_404(_reports_for_user(request.user), pk=pk)

        if request.method == 'POST':
            report_title = report.title
            
            # Check if soft delete is available
            if hasattr(report, 'is_deleted'):
                report.is_deleted = True
                report.save()
                action = "archivado"
            else:
                report.delete()
                action = "eliminado"
            
            # Clear cache
            cache.delete('report_statistics')
            
            messages.success(request, f'Reporte "{report_title}" {action} exitosamente.')
            return redirect('report:report.list')
        
        context = {'report': report}
        return render(request, 'report/report-delete.html', context)
        
    except Exception as e:
        logger.exception(f"Error in report_delete view for pk={pk}")
        messages.error(request, f"Error al eliminar el reporte: {str(e)}")
        return redirect('report:report.list')

# Enhanced Simulation Report Creation
@login_required
def create_simulation_report(request):
    """Create a simulation report with enhanced validation."""
    try:
        if request.method == 'POST':
            form = SimulationReportForm(request.POST, user=request.user)
            
            if form.is_valid():
                # Get form data
                product = form.cleaned_data['product']
                simulation_params = form.get_simulation_params()
                
                # Validate simulation parameters
                validation_errors = validate_simulation_params(simulation_params)
                if validation_errors:
                    for error in validation_errors:
                        messages.error(request, error)
                    return render(request, 'report/create-simulation-report.html', {'form': form})
                
                # Process simulation data
                report_content = process_simulation_data(
                    product, simulation_params, username=str(request.user))
                
                if 'error' in report_content:
                    messages.error(request, f"Error en la simulación: {report_content['error']}")
                    return render(request, 'report/create-simulation-report.html', {'form': form})
                
                # Create the report
                # Nota: Report NO tiene campo created_by; el dueño se deriva de
                # fk_product -> fk_business -> fk_user. Pasar created_by=None
                # rompía el create() con TypeError (tragado por el except).
                report = Report.objects.create(
                    title=f"Reporte de Simulación - {product.name} - {timezone.now().strftime('%Y%m%d_%H%M%S')}",
                    content=report_content,
                    fk_product=product,
                    report_type='simulation',
                )
                
                # Clear cache
                cache.delete('report_statistics')
                
                messages.success(request, 'Reporte de simulación creado exitosamente.')
                return redirect('report:report.detail', pk=report.pk)
            else:
                messages.error(request, 'Por favor corrige los errores en el formulario.')
        else:
            form = SimulationReportForm(user=request.user)
        
        context = {
            'form': form,
            'products': form.fields['product'].queryset,
            'default_params': get_default_simulation_params(),
        }
        
        return render(request, 'report/create-simulation-report.html', context)
        
    except Exception as e:
        logger.exception("Error in create_simulation_report view")
        messages.error(request, f"Error al crear el reporte de simulación: {str(e)}")
        return redirect('report:report.list')

def validate_simulation_params(params: Dict[str, Any]) -> list:
    """Validate simulation parameters."""
    errors = []
    
    try:
        # Required parameters
        required_params = ['demanda_inicial', 'precio_unitario', 'costo_unitario']
        for param in required_params:
            if param not in params or params[param] is None:
                errors.append(f"El parámetro '{param}' es requerido.")
        
        # Numeric validations
        if 'precio_unitario' in params and 'costo_unitario' in params:
            precio = float(params.get('precio_unitario', 0))
            costo = float(params.get('costo_unitario', 0))
            
            if precio <= 0:
                errors.append("El precio unitario debe ser mayor a 0.")
            
            if costo < 0:
                errors.append("El costo unitario no puede ser negativo.")
            
            if precio <= costo:
                errors.append("El precio unitario debe ser mayor al costo para tener margen positivo.")
        
        # Range validations
        if 'tasa_crecimiento' in params:
            tasa = float(params.get('tasa_crecimiento', 0))
            if tasa < -100 or tasa > 1000:
                errors.append("La tasa de crecimiento debe estar entre -100% y 1000%.")
        
        if 'horizonte' in params:
            horizonte = int(params.get('horizonte', 12))
            if horizonte < 1 or horizonte > 120:
                errors.append("El horizonte debe estar entre 1 y 120 meses.")
                
    except (ValueError, TypeError) as e:
        errors.append("Error en el formato de los parámetros numéricos.")
    
    return errors

def get_default_simulation_params() -> Dict[str, Any]:
    """Get default simulation parameters."""
    return {
        'demanda_inicial': 1000,
        'precio_unitario': 100,
        'costo_unitario': 60,
        'tasa_crecimiento': 5,
        'horizonte': 12,
        'gastos_fijos': 5000,
        'inversion_inicial': 50000,
        'tasa_descuento_anual': 0.12,
    }

def process_simulation_data(product: Product, simulation_params: Dict[str, Any],
                            username: str = 'sistema') -> Dict[str, Any]:
    """Process simulation data with enhanced calculations and error handling."""
    try:
        # Get variables related to product
        variables = Variable.objects.filter(fk_product=product)
        
        # Enhance simulation parameters with defaults
        defaults = get_default_simulation_params()
        supplied_keys = set(simulation_params)
        params = {**defaults, **simulation_params}
        
        # Perform calculations with error handling
        try:
            utilidad_neta = calculate_utilidad_neta(params)
            flujo_caja = calculate_flujo_caja(params)
            roi = calculate_roi(params)
            punto_equilibrio = calculate_punto_equilibrio(params)
            payback = calculate_payback_period(params)
            van = calculate_van(params, tasa_descuento=params['tasa_descuento_anual'])
            tir = calculate_tir(params)
            
        except Exception as calc_error:
            logger.error(f"Calculation error: {calc_error}")
            return {'error': f'Error en los cálculos: {str(calc_error)}'}
        
        # Generate enhanced results
        simulation_results = {
            'parametros': params,
            'producto': {
                'nombre': product.name,
                'id': product.id,
                'descripcion': getattr(product, 'description', ''),
            },
            'variables': [
                {
                    'nombre': var.name,
                    'valor': getattr(var, 'value', 0),
                    'descripcion': getattr(var, 'description', ''),
                    'tipo': getattr(var, 'variable_type', 'numeric'),
                } for var in variables
            ],
            'resultados_simulacion': {
                'utilidad_neta': round(utilidad_neta, 2),
                'flujo_caja': round(flujo_caja, 2),
                'roi': _round_optional(roi),
                'punto_equilibrio': round(punto_equilibrio, 0),
                'payback_period': _round_optional(payback),
                'van': round(van, 2),
                'tir': _round_optional(tir),
                'margen_unitario': round(params['precio_unitario'] - params['costo_unitario'], 2),
                'ingresos_totales': round(params['demanda_inicial'] * params['precio_unitario'], 2),
            },
            'analisis_sensibilidad': generate_sensitivity_analysis(params),
            'graficas': generate_enhanced_chart_data(params),
            'fecha_simulacion': timezone.now().isoformat(),
            'metadatos': {
                'version': '2.0',
                'usuario': username,
                'tipo': 'simulacion_producto',
                'parametros_version': '2.0',
                'parameter_provenance': {
                    key: 'USER_ENTERED' if key in supplied_keys else 'TEMPLATE_DEFAULT'
                    for key in params
                },
                'financial_contract': {
                    'currency': 'Bs',
                    'period': 'month',
                    'roi': 'net_horizon_cash_return / initial_investment',
                    'npv': 'monthly_annuity discounted by explicit annual nominal rate',
                    'irr': 'annual_effective_rate from monthly NPV root',
                    'payback': 'initial_investment / positive_monthly_cash_flow',
                    'tasa_descuento_anual': params['tasa_descuento_anual'],
                },
            }
        }

        # Sanea inf/-inf/nan (p.ej. punto_equilibrio / payback cuando el flujo
        # de caja es <= 0) para que el JSONField/jsonb no reciba Infinity/NaN.
        return _sanitize_json_numbers(simulation_results)

    except Exception as e:
        logger.exception("Error processing simulation data")
        return {'error': str(e)}

# Enhanced calculation functions
_REPORT_MONEY = Decimal("0.01")


def _report_non_negative(params: Dict[str, Any], key: str, default: str | None = None) -> Decimal:
    if key not in params and default is None:
        raise ValueError(f"{key} es obligatorio para este cálculo.")
    try:
        value = Decimal(str(params.get(key, default)))
    except Exception as exc:
        raise ValueError(f"{key} debe ser numérico.") from exc
    if not value.is_finite() or value < 0:
        raise ValueError(f"{key} debe ser finito y no negativo.")
    return value


def _report_horizon(params: Dict[str, Any]) -> int:
    raw = params.get('horizonte')
    if isinstance(raw, bool):
        raise ValueError("horizonte debe ser un entero entre 1 y 120 meses.")
    try:
        horizon = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("horizonte es obligatorio y debe ser entero.") from exc
    if horizon < 1 or horizon > 120 or str(raw).strip() not in {str(horizon), f"{horizon}.0"}:
        raise ValueError("horizonte debe ser un entero entre 1 y 120 meses.")
    return horizon


def _annuity_npv(investment: Decimal, monthly_cash_flow: Decimal, horizon: int, monthly_rate: Decimal) -> Decimal:
    if monthly_rate <= Decimal("-1"):
        raise ValueError("La tasa mensual debe ser mayor a -100%.")
    value = -investment
    factor = Decimal("1") + monthly_rate
    for month in range(1, horizon + 1):
        value += monthly_cash_flow / (factor ** month)
    return value


def _round_optional(value: Optional[float], digits: int = 2) -> Optional[float]:
    return round(value, digits) if value is not None else None


def calculate_utilidad_neta(params: Dict[str, Any]) -> float:
    """Calculate net operating result with Decimal monetary arithmetic."""
    demanda = _report_non_negative(params, 'demanda_inicial')
    precio = _report_non_negative(params, 'precio_unitario')
    costo = _report_non_negative(params, 'costo_unitario')
    return float(((precio - costo) * demanda).quantize(_REPORT_MONEY))
def calculate_flujo_caja(params: Dict[str, Any]) -> float:
    """Calculate the legacy operating cash proxy with explicit naming."""
    utilidad = Decimal(str(calculate_utilidad_neta(params)))
    gastos_fijos = _report_non_negative(params, 'gastos_fijos')
    return float((utilidad - gastos_fijos).quantize(_REPORT_MONEY))


def calculate_roi(params: Dict[str, Any]) -> Optional[float]:
    """Return net horizon cash return as a percentage of invested capital."""
    inversion = _report_non_negative(params, 'inversion_inicial')
    horizon = _report_horizon(params)
    monthly_cash_flow = Decimal(str(calculate_flujo_caja(params)))
    if inversion == 0:
        return None
    net_horizon_return = monthly_cash_flow * horizon - inversion
    return float(((net_horizon_return / inversion) * 100).quantize(Decimal("0.0001")))


def calculate_punto_equilibrio(params: Dict[str, Any]) -> float:
    """Calculate break-even point."""
    precio = _report_non_negative(params, 'precio_unitario')
    costo_variable = _report_non_negative(params, 'costo_unitario')
    gastos_fijos = _report_non_negative(params, 'gastos_fijos')
    margen_contribucion = precio - costo_variable
    if margen_contribucion <= 0:
        return float('inf')
    return float((gastos_fijos / margen_contribucion).quantize(Decimal("0.0001")))


def calculate_payback_period(params: Dict[str, Any]) -> Optional[float]:
    """Calculate payback period in months."""
    inversion = _report_non_negative(params, 'inversion_inicial')
    flujo_caja_mensual = Decimal(str(calculate_flujo_caja(params)))
    if inversion == 0:
        return 0.0
    if flujo_caja_mensual <= 0:
        return None
    return float((inversion / flujo_caja_mensual).quantize(Decimal("0.0001")))
def calculate_van(params: Dict[str, Any], tasa_descuento: Optional[float] = None) -> float:
    """Calculate NPV using equal monthly cash flow and an annual nominal rate."""
    inversion = _report_non_negative(params, 'inversion_inicial')
    flujo_caja_mensual = Decimal(str(calculate_flujo_caja(params)))
    horizonte = _report_horizon(params)
    if tasa_descuento is None:
        if 'tasa_descuento_anual' not in params:
            raise ValueError("tasa_descuento_anual es obligatoria para calcular VAN.")
        tasa_descuento = params['tasa_descuento_anual']
    try:
        annual_discount_rate = Decimal(str(tasa_descuento))
    except Exception as exc:
        raise ValueError("tasa_descuento debe ser numérica y finita.") from exc
    if not annual_discount_rate.is_finite() or annual_discount_rate < 0:
        raise ValueError("tasa_descuento debe ser finita y no negativa.")
    tasa_mensual = annual_discount_rate / 12
    van = _annuity_npv(inversion, flujo_caja_mensual, horizonte, tasa_mensual)
    return float(van.quantize(_REPORT_MONEY))


def calculate_tir(params: Dict[str, Any]) -> Optional[float]:
    """Solve monthly IRR by bisection and return its annual effective rate."""
    inversion = _report_non_negative(params, 'inversion_inicial')
    flujo_caja_mensual = Decimal(str(calculate_flujo_caja(params)))
    horizonte = _report_horizon(params)
    if inversion <= 0 or flujo_caja_mensual <= 0:
        return None

    lower = Decimal("-0.999999")
    upper = Decimal("1")
    while _annuity_npv(inversion, flujo_caja_mensual, horizonte, upper) > 0 and upper < Decimal("1048575"):
        upper = upper * 2 + 1
    if _annuity_npv(inversion, flujo_caja_mensual, horizonte, upper) > 0:
        return None

    tolerance = Decimal("0.0000000001")
    for _ in range(200):
        midpoint = (lower + upper) / 2
        npv = _annuity_npv(inversion, flujo_caja_mensual, horizonte, midpoint)
        if abs(npv) <= tolerance:
            lower = upper = midpoint
            break
        if npv > 0:
            lower = midpoint
        else:
            upper = midpoint

    monthly_rate = (lower + upper) / 2
    annual_effective_rate = ((Decimal("1") + monthly_rate) ** 12 - Decimal("1")) * 100
    return float(annual_effective_rate.quantize(Decimal("0.0001")))

def generate_sensitivity_analysis(params: Dict[str, Any]) -> Dict[str, Any]:
    """Generate sensitivity analysis for key parameters."""
    base_roi = calculate_roi(params)
    sensitivity = {}
    
    # Parameters to analyze
    key_params = ['precio_unitario', 'costo_unitario', 'demanda_inicial', 'gastos_fijos']
    variations = [-20, -10, -5, 5, 10, 20]  # Percentage variations
    
    for param in key_params:
        if param in params:
            param_analysis = []
            base_value = float(params[param])
            
            for variation in variations:
                new_params = params.copy()
                new_value = base_value * (1 + variation / 100)
                new_params[param] = new_value
                
                new_roi = calculate_roi(new_params)
                param_analysis.append({
                    'variation': variation,
                    'new_value': round(new_value, 2),
                    'roi': _round_optional(new_roi),
                    'roi_change': round(new_roi - base_roi, 2) if new_roi is not None and base_roi is not None else None,
                })
            
            sensitivity[param] = param_analysis
    
    return sensitivity

def generate_enhanced_chart_data(params: Dict[str, Any]) -> Dict[str, Any]:
    """Generate enhanced chart data with multiple series."""
    horizonte = int(params.get('horizonte', 12))
    demanda_inicial = float(params.get('demanda_inicial', 1000))
    precio = float(params.get('precio_unitario', 100))
    costo = float(params.get('costo_unitario', 60))
    tasa_crecimiento = float(params.get('tasa_crecimiento', 5)) / 100
    gastos_fijos = float(params.get('gastos_fijos', 5000))
    
    meses = []
    ventas = []
    ingresos = []
    costos = []
    utilidad_bruta = []
    utilidad_neta = []
    flujo_acumulado = []
    
    acumulado = 0
    
    for mes in range(1, horizonte + 1):
        # Calculate demand with growth
        demanda_mes = demanda_inicial * ((1 + tasa_crecimiento) ** (mes - 1))
        
        # Calculate metrics
        ventas_mes = round(demanda_mes)
        ingresos_mes = round(demanda_mes * precio)
        costos_mes = round(demanda_mes * costo)
        utilidad_bruta_mes = ingresos_mes - costos_mes
        utilidad_neta_mes = utilidad_bruta_mes - gastos_fijos
        acumulado += utilidad_neta_mes
        
        # Append to arrays
        meses.append(f"Mes {mes}")
        ventas.append(ventas_mes)
        ingresos.append(ingresos_mes)
        costos.append(costos_mes)
        utilidad_bruta.append(utilidad_bruta_mes)
        utilidad_neta.append(utilidad_neta_mes)
        flujo_acumulado.append(round(acumulado))
    
    return {
        'ventas_proyectadas': {
            'labels': meses,
            'data': ventas,
            'title': 'Ventas Proyectadas (Unidades)'
        },
        'ingresos_proyectados': {
            'labels': meses,
            'data': ingresos,
            'title': 'Ingresos Proyectados'
        },
        'analisis_financiero': {
            'labels': meses,
            'datasets': [
                {
                    'label': 'Ingresos',
                    'data': ingresos,
                    'color': '#28a745'
                },
                {
                    'label': 'Costos',
                    'data': costos,
                    'color': '#dc3545'
                },
                {
                    'label': 'Utilidad Neta',
                    'data': utilidad_neta,
                    'color': '#007bff'
                }
            ]
        },
        'flujo_acumulado': {
            'labels': meses,
            'data': flujo_acumulado,
            'title': 'Flujo de Caja Acumulado'
        }
    }

# ── Async PDF Generation ──────────────────────────────────────────────────────

@login_required
def generar_reporte_pdf(request, report_id):
    """Enqueue async PDF generation and return task info (202)."""
    from .tasks import generate_report_pdf_async

    # Restringido al dueño real (cierra IDOR); 404 si no le pertenece.
    reporte = get_object_or_404(_reports_for_user(request.user), pk=report_id)

    user_id = request.user.id
    task = generate_report_pdf_async.delay(report_id, user_id)
    cache.set(f"pdf_task_id:{report_id}:{user_id}", task.id, 3600)

    status_url = request.build_absolute_uri(f'/report/pdf/status/{report_id}/')
    download_url = request.build_absolute_uri(f'/report/pdf/download/{report_id}/')

    return JsonResponse({
        'task_id': task.id,
        'status': 'queued',
        'message': 'Generación de PDF en proceso. Consulte status_url para el estado.',
        'status_url': status_url,
        'download_url': download_url,
    }, status=202)


@login_required
def report_pdf_status(request, report_id):
    """Poll Celery task state for PDF generation."""
    user_id = request.user.id
    task_id = cache.get(f"pdf_task_id:{report_id}:{user_id}")

    if not task_id:
        pdf_bytes = cache.get(f"pdf_bytes:{report_id}:{user_id}")
        if pdf_bytes:
            download_url = request.build_absolute_uri(f'/report/pdf/download/{report_id}/')
            return JsonResponse({'state': 'SUCCESS', 'download_url': download_url})
        return JsonResponse({'state': 'NOT_FOUND', 'message': 'No hay tarea en curso para este reporte.'}, status=404)

    result = AsyncResult(task_id)
    state = result.state
    meta = result.info if isinstance(result.info, dict) else {}

    if state == 'SUCCESS':
        download_url = request.build_absolute_uri(f'/report/pdf/download/{report_id}/')
        return JsonResponse({'state': state, 'download_url': download_url})

    if state == 'FAILURE':
        return JsonResponse({'state': state, 'message': str(result.result)})

    return JsonResponse({
        'state': state,
        'current': meta.get('current', 0),
        'total': meta.get('total', 100),
        'message': meta.get('status', 'Procesando...'),
    })


@login_required
def report_pdf_download(request, report_id):
    """Serve cached PDF bytes generated by the async task."""
    user_id = request.user.id
    pdf_bytes = cache.get(f"pdf_bytes:{report_id}:{user_id}")

    if not pdf_bytes:
        return JsonResponse({'error': 'PDF no disponible. Genera el reporte primero.'}, status=404)

    filename = cache.get(f"pdf_filename:{report_id}:{user_id}", f"reporte_{report_id}.pdf")
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

# Report Overview (enhanced)
@login_required
def report_overview(request, pk):
    """Enhanced report overview with analytics."""
    return report_detail(request, pk)

# Toggle Report Status with AJAX support
@login_required
@require_http_methods(["POST"])
def toggle_report_status(request, pk):
    """Toggle report active status with enhanced validation."""
    try:
        # Restringido al dueño real (cierra IDOR); staff incluido en el helper.
        report = get_object_or_404(_reports_for_user(request.user), pk=pk)

        # Toggle status
        old_status = report.is_active
        report.is_active = not report.is_active
        report.last_updated = timezone.now()
        report.save(update_fields=['is_active', 'last_updated'])
        
        # Clear cache
        cache.delete('report_statistics')
        
        status = "activado" if report.is_active else "desactivado"
        success_message = f'Reporte "{report.title}" {status} exitosamente.'
        
        # Log the change
        logger.info(f"Report {pk} status changed from {old_status} to {report.is_active} by user {request.user}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True, 
                'is_active': report.is_active,
                'message': success_message
            })
        
        messages.success(request, success_message)
        return redirect('report:report.detail', pk=pk)
        
    except Exception as e:
        logger.exception(f"Error toggling report status for pk={pk}")
        error_message = f"Error al cambiar el estado: {str(e)}"
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_message})
        
        messages.error(request, error_message)
        return redirect('report:report.list')

# Enhanced API Endpoints
@login_required
def report_api_list(request):
    """Enhanced API endpoint for reports list with filtering."""
    try:
        # Get query parameters
        limit = min(int(request.GET.get('limit', 50)), 100)  # Max 100 items
        offset = int(request.GET.get('offset', 0))
        search = request.GET.get('search', '').strip()
        status = request.GET.get('status', '')
        product_id = request.GET.get('product_id', '')
        
        # Build queryset restringido al dueño (cierra IDOR)
        reports = _reports_for_user(request.user).select_related('fk_product').order_by('-date_created')
        
        # Apply filters
        if search:
            reports = reports.filter(
                Q(title__icontains=search) | 
                Q(fk_product__name__icontains=search)
            )
        
        if status:
            reports = reports.filter(is_active=(status == 'active'))
        
        if product_id:
            reports = reports.filter(fk_product_id=product_id)
        
        # Apply pagination
        total_count = reports.count()
        reports = reports[offset:offset + limit]
        
        # Serialize data
        data = []
        for report in reports:
            report_data = {
                'id': report.id,
                'title': report.title,
                'date_created': report.date_created.isoformat(),
                'last_updated': report.last_updated.isoformat(),
                'is_active': report.is_active,
                'product': {
                    'id': report.fk_product.id,
                    'name': report.fk_product.name
                } if report.fk_product else None,
                'summary': getattr(report, 'summary', '')[:100],
                'report_type': getattr(report, 'report_type', 'general'),
            }
            
            # Add metrics if available
            if hasattr(report, 'content') and isinstance(report.content, dict):
                if 'resultados_simulacion' in report.content:
                    results = report.content['resultados_simulacion']
                    report_data['metrics'] = {
                        'roi': results.get('roi'),
                        'utilidad_neta': results.get('utilidad_neta', 0),
                        'punto_equilibrio': results.get('punto_equilibrio', 0),
                    }
            
            data.append(report_data)
        
        response_data = {
            'reports': data,
            'pagination': {
                'total': total_count,
                'limit': limit,
                'offset': offset,
                'has_next': offset + limit < total_count,
                'has_previous': offset > 0,
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.exception("Error in report_api_list")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def report_api_detail(request, pk):
    """Enhanced API endpoint for report details."""
    try:
        # Restringido al dueño real (cierra IDOR)
        report = get_object_or_404(
            _reports_for_user(request.user).select_related('fk_product'),
            pk=pk
        )

        # Serialize data
        data = {
            'id': report.id,
            'title': report.title,
            'content': report.content,
            'date_created': report.date_created.isoformat(),
            'last_updated': report.last_updated.isoformat(),
            'is_active': report.is_active,
            'product': {
                'id': report.fk_product.id,
                'name': report.fk_product.name,
                'description': getattr(report.fk_product, 'description', ''),
            } if report.fk_product else None,
            'summary': getattr(report, 'summary', ''),
            'report_type': getattr(report, 'report_type', 'general'),
            'tags': getattr(report, 'tags', '').split(',') if getattr(report, 'tags', '') else [],
        }
        
        # Add user info if available
        if hasattr(report, 'created_by') and report.created_by:
            data['created_by'] = {
                'id': report.created_by.id,
                'username': report.created_by.username,
                'full_name': report.created_by.get_full_name(),
            }
        
        # Add view count if available
        if hasattr(report, 'view_count'):
            data['view_count'] = report.view_count
        
        return JsonResponse(data)

    except Http404:
        return JsonResponse({'error': 'Reporte no encontrado.'}, status=404)
    except Exception as e:
        logger.exception(f"Error in report_api_detail for pk={pk}")
        return JsonResponse({'error': str(e)}, status=500)

# Bulk operations
@login_required
@require_http_methods(["POST"])
def bulk_report_operations(request):
    """Handle bulk operations on reports."""
    try:
        data = json.loads(request.body)
        operation = data.get('operation')
        report_ids = data.get('report_ids', [])
        
        if not report_ids:
            return JsonResponse({'success': False, 'error': 'No se seleccionaron reportes.'})
        
        # Validate report IDs — restringido al dueño real (cierra IDOR)
        reports = _reports_for_user(request.user).filter(id__in=report_ids)

        success_count = 0
        
        if operation == 'activate':
            success_count = reports.update(is_active=True, last_updated=timezone.now())
        elif operation == 'deactivate':
            success_count = reports.update(is_active=False, last_updated=timezone.now())
        elif operation == 'delete':
            if hasattr(Report, 'is_deleted'):
                success_count = reports.update(is_deleted=True, last_updated=timezone.now())
            else:
                success_count = len(reports)
                reports.delete()
        else:
            return JsonResponse({'success': False, 'error': 'Operación no válida.'})
        
        # Clear cache
        cache.delete('report_statistics')
        
        return JsonResponse({
            'success': True,
            'message': f'Operación completada en {success_count} reportes.',
            'count': success_count
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Datos JSON inválidos.'})
    except Exception as e:
        logger.exception("Error in bulk_report_operations")
        return JsonResponse({'success': False, 'error': str(e)})

# Export functionality
@login_required
def export_reports(request):
    """Export reports in various formats."""
    try:
        export_format = request.GET.get('format', 'csv')
        report_ids = request.GET.getlist('ids')
        
        # Get reports — restringido al dueño real (cierra IDOR)
        reports = _reports_for_user(request.user).select_related('fk_product').order_by('-date_created')

        if report_ids:
            reports = reports.filter(id__in=report_ids)

        if export_format == 'csv':
            return export_reports_csv(reports)
        elif export_format == 'excel':
            return export_reports_excel(reports)
        else:
            return JsonResponse({'error': 'Formato no soportado.'}, status=400)
            
    except Exception as e:
        logger.exception("Error in export_reports")
        return JsonResponse({'error': str(e)}, status=500)

def export_reports_csv(reports):
    """Export reports to CSV format."""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="reportes_{timezone.now().strftime("%Y%m%d_%H%M")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'Título', 'Producto', 'Fecha Creación', 'Última Actualización', 'Estado', 'Tipo'])
    
    for report in reports:
        writer.writerow([
            report.id,
            report.title,
            report.fk_product.name if report.fk_product else '',
            report.date_created.strftime('%Y-%m-%d %H:%M'),
            report.last_updated.strftime('%Y-%m-%d %H:%M'),
            'Activo' if report.is_active else 'Inactivo',
            getattr(report, 'report_type', 'General')
        ])
    
    return response

def export_reports_excel(reports):
    """Export reports to Excel format."""
    try:
        import xlsxwriter
        from io import BytesIO
        
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Reportes')
        
        # Define formats
        header_format = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2'})
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy hh:mm'})
        
        # Write headers
        headers = ['ID', 'Título', 'Producto', 'Fecha Creación', 'Última Actualización', 'Estado', 'Tipo']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Write data
        for row, report in enumerate(reports, 1):
            worksheet.write(row, 0, report.id)
            worksheet.write(row, 1, report.title)
            worksheet.write(row, 2, report.fk_product.name if report.fk_product else '')
            worksheet.write(row, 3, report.date_created, date_format)
            worksheet.write(row, 4, report.last_updated, date_format)
            worksheet.write(row, 5, 'Activo' if report.is_active else 'Inactivo')
            worksheet.write(row, 6, getattr(report, 'report_type', 'General'))
        
        # Adjust column widths
        worksheet.set_column('A:A', 8)   # ID
        worksheet.set_column('B:B', 30)  # Title
        worksheet.set_column('C:C', 20)  # Product
        worksheet.set_column('D:E', 18)  # Dates
        worksheet.set_column('F:G', 12)  # Status, Type
        
        workbook.close()
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="reportes_{timezone.now().strftime("%Y%m%d_%H%M")}.xlsx"'
        
        return response
        
    except ImportError:
        return JsonResponse({'error': 'xlsxwriter no está instalado.'}, status=500)
    except Exception as e:
        logger.exception("Error exporting to Excel")
        return JsonResponse({'error': f'Error exportando a Excel: {str(e)}'}, status=500)
