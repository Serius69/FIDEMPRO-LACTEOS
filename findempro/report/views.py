from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.conf import settings
from django.http import JsonResponse, HttpResponse, FileResponse, HttpResponseForbidden
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
import openai
import logging
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from decimal import Decimal
import traceback

# Configure logger
logger = logging.getLogger(__name__)

class AppsView(LoginRequiredMixin, TemplateView):
    """Main apps view for reports module."""
    template_name = 'report/apps.html'

# List View with improved error handling and caching
@login_required
@cache_page(60 * 5)  # Cache for 5 minutes
def report_list(request):
    """Display paginated list of reports with search functionality."""
    try:
        search_query = request.GET.get('search', '').strip()
        filter_type = request.GET.get('type', '')
        filter_status = request.GET.get('status', '')
        sort_by = request.GET.get('sort', '-date_created')
        
        # Base queryset with optimizations
        reports = Report.objects.select_related('fk_product').prefetch_related()
        
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
        
        # Get statistics
        stats = get_report_statistics()
        
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

def get_report_statistics() -> Dict[str, Any]:
    """Get report statistics for dashboard."""
    try:
        cache_key = 'report_statistics'
        stats = cache.get(cache_key)
        
        if stats is None:
            total_reports = Report.objects.count()
            active_reports = Report.objects.filter(is_active=True).count()
            recent_reports = Report.objects.filter(
                date_created__gte=timezone.now() - timedelta(days=7)
            ).count()
            
            # Products with most reports
            top_products = Report.objects.filter(
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
        report = get_object_or_404(Report.objects.select_related('fk_product'), pk=pk)
        
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
            'can_edit': request.user.is_staff or report.created_by == request.user,
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
        report = get_object_or_404(Report, pk=pk)
        
        # Check permissions
        if hasattr(report, 'created_by') and report.created_by != request.user and not request.user.is_staff:
            messages.error(request, 'No tienes permisos para editar este reporte.')
            return redirect('report:report.detail', pk=pk)
        
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
        report = get_object_or_404(Report, pk=pk)
        
        # Check permissions
        if hasattr(report, 'created_by') and report.created_by != request.user and not request.user.is_staff:
            messages.error(request, 'No tienes permisos para eliminar este reporte.')
            return redirect('report:report.detail', pk=pk)
        
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
            form = SimulationReportForm(request.POST)
            
            if form.is_valid():
                # Get form data
                product = form.cleaned_data['product']
                simulation_params = form.cleaned_data.get('simulation_params', {})
                
                # Validate simulation parameters
                validation_errors = validate_simulation_params(simulation_params)
                if validation_errors:
                    for error in validation_errors:
                        messages.error(request, error)
                    return render(request, 'report/create-simulation-report.html', {'form': form})
                
                # Process simulation data
                report_content = process_simulation_data(product, simulation_params)
                
                if 'error' in report_content:
                    messages.error(request, f"Error en la simulación: {report_content['error']}")
                    return render(request, 'report/create-simulation-report.html', {'form': form})
                
                # Create the report
                report = Report.objects.create(
                    title=f"Reporte de Simulación - {product.name} - {timezone.now().strftime('%Y%m%d_%H%M')}",
                    content=report_content,
                    fk_product=product,
                    report_type='simulation' if hasattr(Report, 'report_type') else None,
                    created_by=request.user if hasattr(Report, 'created_by') else None,
                )
                
                # Clear cache
                cache.delete('report_statistics')
                
                messages.success(request, 'Reporte de simulación creado exitosamente.')
                return redirect('report:report.detail', pk=report.pk)
            else:
                messages.error(request, 'Por favor corrige los errores en el formulario.')
        else:
            form = SimulationReportForm()
        
        context = {
            'form': form,
            'products': Product.objects.filter(is_active=True).order_by('name'),
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
    }

def process_simulation_data(product: Product, simulation_params: Dict[str, Any]) -> Dict[str, Any]:
    """Process simulation data with enhanced calculations and error handling."""
    try:
        # Get variables related to product
        variables = Variable.objects.filter(fk_product=product)
        
        # Enhance simulation parameters with defaults
        params = {**get_default_simulation_params(), **simulation_params}
        
        # Perform calculations with error handling
        try:
            utilidad_neta = calculate_utilidad_neta(params)
            flujo_caja = calculate_flujo_caja(params)
            roi = calculate_roi(params)
            punto_equilibrio = calculate_punto_equilibrio(params)
            payback = calculate_payback_period(params)
            van = calculate_van(params)
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
                'roi': round(roi, 2),
                'punto_equilibrio': round(punto_equilibrio, 0),
                'payback_period': round(payback, 2),
                'van': round(van, 2),
                'tir': round(tir, 2),
                'margen_unitario': round(params['precio_unitario'] - params['costo_unitario'], 2),
                'ingresos_totales': round(params['demanda_inicial'] * params['precio_unitario'], 2),
            },
            'analisis_sensibilidad': generate_sensitivity_analysis(params),
            'graficas': generate_enhanced_chart_data(params),
            'fecha_simulacion': timezone.now().isoformat(),
            'metadatos': {
                'version': '2.0',
                'usuario': str(request.user) if 'request' in locals() else 'sistema',
                'tipo': 'simulacion_producto',
                'parametros_version': '2.0',
            }
        }
        
        return simulation_results
        
    except Exception as e:
        logger.exception("Error processing simulation data")
        return {'error': str(e)}

# Enhanced calculation functions
def calculate_utilidad_neta(params: Dict[str, Any]) -> float:
    """Calculate net profit with enhanced validation."""
    demanda = float(params.get('demanda_inicial', 0))
    precio = float(params.get('precio_unitario', 0))
    costo = float(params.get('costo_unitario', 0))
    
    return (precio - costo) * demanda

def calculate_flujo_caja(params: Dict[str, Any]) -> float:
    """Calculate cash flow."""
    utilidad = calculate_utilidad_neta(params)
    gastos_fijos = float(params.get('gastos_fijos', 0))
    
    return utilidad - gastos_fijos

def calculate_roi(params: Dict[str, Any]) -> float:
    """Calculate ROI (Return on Investment)."""
    inversion = float(params.get('inversion_inicial', 1))
    flujo_caja = calculate_flujo_caja(params)
    
    if inversion <= 0:
        return 0
    
    return (flujo_caja / inversion) * 100

def calculate_punto_equilibrio(params: Dict[str, Any]) -> float:
    """Calculate break-even point."""
    precio = float(params.get('precio_unitario', 0))
    costo_variable = float(params.get('costo_unitario', 0))
    gastos_fijos = float(params.get('gastos_fijos', 0))
    
    margen_contribucion = precio - costo_variable
    
    if margen_contribucion <= 0:
        return float('inf')
    
    return gastos_fijos / margen_contribucion

def calculate_payback_period(params: Dict[str, Any]) -> float:
    """Calculate payback period in months."""
    inversion = float(params.get('inversion_inicial', 1))
    flujo_caja_mensual = calculate_flujo_caja(params)
    
    if flujo_caja_mensual <= 0:
        return float('inf')
    
    return inversion / flujo_caja_mensual

def calculate_van(params: Dict[str, Any], tasa_descuento: float = 0.12) -> float:
    """Calculate Net Present Value (VAN)."""
    inversion = float(params.get('inversion_inicial', 0))
    flujo_caja_mensual = calculate_flujo_caja(params)
    horizonte = int(params.get('horizonte', 12))
    
    van = -inversion
    tasa_mensual = tasa_descuento / 12
    
    for mes in range(1, horizonte + 1):
        flujo_descontado = flujo_caja_mensual / ((1 + tasa_mensual) ** mes)
        van += flujo_descontado
    
    return van

def calculate_tir(params: Dict[str, Any]) -> float:
    """Calculate Internal Rate of Return (TIR) using approximation."""
    # Simplified TIR calculation using binary search
    inversion = float(params.get('inversion_inicial', 1))
    flujo_caja_mensual = calculate_flujo_caja(params)
    horizonte = int(params.get('horizonte', 12))
    
    if flujo_caja_mensual <= 0:
        return 0
    
    # Simple approximation
    total_flujos = flujo_caja_mensual * horizonte
    tir_anual = ((total_flujos / inversion) ** (1/horizonte)) - 1
    
    return tir_anual * 100

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
                    'roi': round(new_roi, 2),
                    'roi_change': round(new_roi - base_roi, 2),
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

# Enhanced PDF Generation
@login_required
def generar_reporte_pdf(request, report_id):
    """Generate enhanced PDF report."""
    try:
        reporte = get_object_or_404(Report, pk=report_id)
        
        # Check permissions
        if hasattr(reporte, 'created_by') and reporte.created_by != request.user and not request.user.is_staff:
            return HttpResponseForbidden("No tienes permisos para descargar este reporte.")
        
        response = HttpResponse(content_type='application/pdf')
        filename = f"{reporte.title.replace(' ', '_')}_{timezone.now().strftime('%Y%m%d_%H%M')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Create PDF document
        doc = SimpleDocTemplate(response, pagesize=letter, topMargin=72, bottomMargin=72)
        styles = getSampleStyleSheet()
        story = []
        
        # Title and header
        title = Paragraph(f"<b>{reporte.title}</b>", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Report info
        info_data = [
            ['Fecha de Creación:', reporte.date_created.strftime('%d/%m/%Y %H:%M')],
            ['Última Actualización:', reporte.last_updated.strftime('%d/%m/%Y %H:%M')],
        ]
        
        if reporte.fk_product:
            info_data.append(['Producto:', reporte.fk_product.name])
        
        if hasattr(reporte, 'created_by') and reporte.created_by:
            info_data.append(['Creado por:', str(reporte.created_by)])
        
        info_table = Table(info_data, colWidths=[2*72, 4*72])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 18))
        
        # Process content based on type
        if isinstance(reporte.content, dict):
            story.extend(generate_pdf_content_sections(reporte.content, styles))
        else:
            # Handle string content
            content_paragraph = Paragraph(str(reporte.content), styles['Normal'])
            story.append(content_paragraph)
        
        # Footer
        story.append(Spacer(1, 24))
        footer = Paragraph(
            f"<i>Generado el {timezone.now().strftime('%d/%m/%Y a las %H:%M')}</i>",
            styles['Normal']
        )
        story.append(footer)
        
        # Build PDF
        doc.build(story)
        return response
        
    except Exception as e:
        logger.exception(f"Error generating PDF for report {report_id}")
        messages.error(request, f"Error generando PDF: {str(e)}")
        return redirect('report:report.detail', pk=report_id)

def generate_pdf_content_sections(content: Dict[str, Any], styles) -> list:
    """Generate PDF content sections from report data."""
    story = []
    
    try:
        # Parameters section
        if 'parametros' in content and content['parametros']:
            story.append(Paragraph("<b>Parámetros de Simulación</b>", styles['Heading2']))
            story.append(Spacer(1, 6))
            
            param_data = [['Parámetro', 'Valor']]
            for key, value in content['parametros'].items():
                param_name = key.replace('_', ' ').title()
                param_data.append([param_name, str(value)])
            
            param_table = Table(param_data, colWidths=[3*72, 2*72])
            param_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(param_table)
            story.append(Spacer(1, 18))
        
        # Results section
        if 'resultados_simulacion' in content and content['resultados_simulacion']:
            story.append(Paragraph("<b>Resultados de Simulación</b>", styles['Heading2']))
            story.append(Spacer(1, 6))
            
            results_data = [['Métrica', 'Valor', 'Unidad']]
            for key, value in content['resultados_simulacion'].items():
                metric_name = key.replace('_', ' ').title()
                
                # Format value based on type
                if 'utilidad' in key or 'flujo' in key or 'inversion' in key or 'van' in key:
                    formatted_value = f"${value:,.2f}"
                    unit = "USD"
                elif 'roi' in key or 'tasa' in key or 'tir' in key:
                    formatted_value = f"{value:.2f}%"
                    unit = "%"
                elif 'punto' in key or 'equilibrio' in key or 'payback' in key:
                    formatted_value = f"{value:,.0f}"
                    unit = "Unidades/Meses"
                else:
                    formatted_value = str(value)
                    unit = "-"
                
                results_data.append([metric_name, formatted_value, unit])
            
            results_table = Table(results_data, colWidths=[2.5*72, 1.5*72, 1*72])
            results_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            story.append(results_table)
            story.append(Spacer(1, 18))
        
        # Variables section
        if 'variables' in content and content['variables']:
            story.append(Paragraph("<b>Variables del Producto</b>", styles['Heading2']))
            story.append(Spacer(1, 6))
            
            var_data = [['Variable', 'Valor', 'Descripción']]
            for var in content['variables']:
                var_data.append([
                    var.get('nombre', ''),
                    str(var.get('valor', '')),
                    var.get('descripcion', '')[:50] + '...' if len(var.get('descripcion', '')) > 50 else var.get('descripcion', '')
                ])
            
            var_table = Table(var_data, colWidths=[2*72, 1*72, 2*72])
            var_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.green),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
            ]))
            story.append(var_table)
            story.append(Spacer(1, 18))
        
        # Summary section
        if 'metadatos' in content:
            story.append(Paragraph("<b>Información de la Simulación</b>", styles['Heading2']))
            story.append(Spacer(1, 6))
            
            metadata = content['metadatos']
            summary_text = f"""
            <b>Versión:</b> {metadata.get('version', 'N/A')}<br/>
            <b>Tipo:</b> {metadata.get('tipo', 'N/A').replace('_', ' ').title()}<br/>
            <b>Usuario:</b> {metadata.get('usuario', 'N/A')}<br/>
            <b>Fecha de Simulación:</b> {content.get('fecha_simulacion', 'N/A')[:19] if content.get('fecha_simulacion') else 'N/A'}
            """
            
            summary_paragraph = Paragraph(summary_text, styles['Normal'])
            story.append(summary_paragraph)
    
    except Exception as e:
        logger.exception("Error generating PDF content sections")
        error_paragraph = Paragraph(f"<b>Error al generar contenido:</b> {str(e)}", styles['Normal'])
        story.append(error_paragraph)
    
    return story

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
        report = get_object_or_404(Report, pk=pk)
        
        # Check permissions
        if hasattr(report, 'created_by') and report.created_by != request.user and not request.user.is_staff:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'No tienes permisos para modificar este reporte.'})
            messages.error(request, 'No tienes permisos para modificar este reporte.')
            return redirect('report:report.detail', pk=pk)
        
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
@cache_page(60 * 2)  # Cache for 2 minutes
def report_api_list(request):
    """Enhanced API endpoint for reports list with filtering."""
    try:
        # Get query parameters
        limit = min(int(request.GET.get('limit', 50)), 100)  # Max 100 items
        offset = int(request.GET.get('offset', 0))
        search = request.GET.get('search', '').strip()
        status = request.GET.get('status', '')
        product_id = request.GET.get('product_id', '')
        
        # Build queryset
        reports = Report.objects.select_related('fk_product').order_by('-date_created')
        
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
                        'roi': results.get('roi', 0),
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
        report = get_object_or_404(
            Report.objects.select_related('fk_product'), 
            pk=pk
        )
        
        # Check permissions for private reports
        if hasattr(report, 'is_private') and report.is_private:
            if hasattr(report, 'created_by') and report.created_by != request.user and not request.user.is_staff:
                return JsonResponse({'error': 'No tienes permisos para ver este reporte.'}, status=403)
        
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
        
        # Validate report IDs
        reports = Report.objects.filter(id__in=report_ids)
        
        if not request.user.is_staff:
            # Filter by user permissions
            if hasattr(Report, 'created_by'):
                reports = reports.filter(created_by=request.user)
        
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
        
        # Get reports
        reports = Report.objects.select_related('fk_product').order_by('-date_created')
        
        if report_ids:
            reports = reports.filter(id__in=report_ids)
        
        if not request.user.is_staff:
            if hasattr(Report, 'created_by'):
                reports = reports.filter(created_by=request.user)
        
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