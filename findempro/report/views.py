from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.conf import settings
from django.http import JsonResponse, HttpResponse, FileResponse, HttpResponseForbidden
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
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
from datetime import datetime

# Create your views here.
class AppsView(LoginRequiredMixin, TemplateView):
    template_name = 'report/apps.html'

# List View
@login_required
def report_list(request):
    try:
        search_query = request.GET.get('search', '')
        reports = Report.objects.all().order_by('-date_created')
        
        if search_query:
            reports = reports.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query)
            )
        
        # Paginación
        paginator = Paginator(reports, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'reports': page_obj,
            'search_query': search_query,
            'total_reports': reports.count()
        }
        return render(request, 'report/report-list.html', context)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.exception("Error in report_list view")
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)

# Detail View
@login_required
def report_detail(request, pk):
    logger = logging.getLogger(__name__)
    current_datetime = timezone.now()
    try:
        report = get_object_or_404(Report, pk=pk)
        context = {
            'report': report,
            'current_datetime': current_datetime
        }
        return render(request, 'report/report-detail.html', context)
    except Exception as e:
        logger.exception("An error occurred in the 'report_detail' view")
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)

# Create View
@login_required
def report_create(request):
    try:
        if request.method == 'POST':
            form = ReportForm(request.POST)
            if form.is_valid():
                report = form.save()
                messages.success(request, f'Reporte "{report.title}" creado exitosamente.')
                return redirect('report:report.detail', pk=report.pk)
            else:
                messages.error(request, 'Por favor corrige los errores en el formulario.')
        else:
            form = ReportForm()
        
        context = {'form': form}
        return render(request, 'report/report-create.html', context)
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)

# Update View
@login_required
def report_update(request, pk):
    try:
        report = get_object_or_404(Report, pk=pk)
        if request.method == 'POST':
            form = ReportForm(request.POST, instance=report)
            if form.is_valid():
                updated_report = form.save()
                messages.success(request, f'Reporte "{updated_report.title}" actualizado exitosamente.')
                return redirect('report:report.detail', pk=updated_report.pk)
            else:
                messages.error(request, 'Por favor corrige los errores en el formulario.')
        else:
            form = ReportForm(instance=report)
        
        context = {'form': form, 'report': report}
        return render(request, 'report/report-update.html', context)
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)

# Delete View
@login_required
def report_delete(request, pk):
    try:
        report = get_object_or_404(Report, pk=pk)
        if request.method == 'POST':
            report_title = report.title
            report.delete()
            messages.success(request, f'Reporte "{report_title}" eliminado exitosamente.')
            return redirect('report:report.list')
        
        context = {'report': report}
        return render(request, 'report/report-delete.html', context)
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)

# Create Report from Simulation
@login_required
def create_simulation_report(request):
    try:
        if request.method == 'POST':
            form = SimulationReportForm(request.POST)
            if form.is_valid():
                # Obtener datos de la simulación
                product = form.cleaned_data['product']
                simulation_params = form.cleaned_data['simulation_params']
                
                # Procesar datos de simulación
                report_content = process_simulation_data(product, simulation_params)
                
                # Crear el reporte
                report = Report.objects.create(
                    title=f"Reporte de Simulación - {product.name}",
                    content=report_content,
                    fk_product=product
                )
                
                messages.success(request, f'Reporte de simulación creado exitosamente.')
                return redirect('report:report.detail', pk=report.pk)
            else:
                messages.error(request, 'Por favor corrige los errores en el formulario.')
        else:
            form = SimulationReportForm()
        
        context = {
            'form': form,
            'products': Product.objects.filter(is_active=True)
        }
        return render(request, 'report/create-simulation-report.html', context)
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)

def process_simulation_data(product, simulation_params):
    """
    Procesa los datos de simulación y genera el contenido del reporte
    """
    try:
        # Obtener variables relacionadas al producto
        variables = Variable.objects.filter(fk_product=product)
        
        # Datos de ejemplo para simulación (reemplazar con lógica real)
        simulation_results = {
            'parametros': simulation_params,
            'producto': {
                'nombre': product.name,
                'id': product.id,
            },
            'variables': [
                {
                    'nombre': var.name,
                    'valor': getattr(var, 'value', 0),
                    'descripcion': getattr(var, 'description', '')
                } for var in variables
            ],
            'resultados_simulacion': {
                'demanda_inicial': simulation_params.get('demanda_inicial', 1000),
                'tasa_crecimiento': simulation_params.get('tasa_crecimiento', 5),
                'horizonte': simulation_params.get('horizonte', 12),
                'utilidad_neta': calculate_utilidad_neta(simulation_params),
                'flujo_caja': calculate_flujo_caja(simulation_params),
                'roi': calculate_roi(simulation_params),
                'punto_equilibrio': calculate_punto_equilibrio(simulation_params)
            },
            'graficas': generate_chart_data(simulation_params),
            'fecha_simulacion': timezone.now().isoformat(),
            'metadatos': {
                'version': '1.0',
                'usuario': 'sistema',
                'tipo': 'simulacion_producto'
            }
        }
        
        return simulation_results
    except Exception as e:
        logging.getLogger(__name__).exception("Error processing simulation data")
        return {'error': str(e)}

def calculate_utilidad_neta(params):
    """Calcula la utilidad neta basada en parámetros de simulación"""
    demanda = params.get('demanda_inicial', 1000)
    precio = params.get('precio_unitario', 100)
    costo = params.get('costo_unitario', 60)
    return (precio - costo) * demanda

def calculate_flujo_caja(params):
    """Calcula el flujo de caja proyectado"""
    utilidad = calculate_utilidad_neta(params)
    gastos_fijos = params.get('gastos_fijos', 5000)
    return utilidad - gastos_fijos

def calculate_roi(params):
    """Calcula el ROI"""
    inversion = params.get('inversion_inicial', 50000)
    flujo_caja = calculate_flujo_caja(params)
    if inversion > 0:
        return (flujo_caja / inversion) * 100
    return 0

def calculate_punto_equilibrio(params):
    """Calcula el punto de equilibrio"""
    precio = params.get('precio_unitario', 100)
    costo_variable = params.get('costo_unitario', 60)
    gastos_fijos = params.get('gastos_fijos', 5000)
    if precio - costo_variable > 0:
        return gastos_fijos / (precio - costo_variable)
    return 0

def generate_chart_data(params):
    """Genera datos para gráficas"""
    horizonte = params.get('horizonte', 12)
    demanda_inicial = params.get('demanda_inicial', 1000)
    tasa_crecimiento = params.get('tasa_crecimiento', 5) / 100
    
    meses = []
    ventas = []
    ingresos = []
    
    for mes in range(1, horizonte + 1):
        demanda_mes = demanda_inicial * (1 + tasa_crecimiento) ** mes
        precio = params.get('precio_unitario', 100)
        
        meses.append(f"Mes {mes}")
        ventas.append(round(demanda_mes))
        ingresos.append(round(demanda_mes * precio))
    
    return {
        'ventas_proyectadas': {
            'labels': meses,
            'data': ventas
        },
        'ingresos_proyectados': {
            'labels': meses,
            'data': ingresos
        }
    }

# PDF Generation (Mejorado)
@login_required
def generar_reporte_pdf(request, report_id):
    try:
        reporte = get_object_or_404(Report, pk=report_id)
        
        # Configuración del response para un archivo PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{reporte.title}.pdf"'
        
        # Crear el documento PDF
        doc = SimpleDocTemplate(response, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Título
        title = Paragraph(f"<b>{reporte.title}</b>", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Fecha
        fecha = Paragraph(f"Fecha: {reporte.date_created.strftime('%d/%m/%Y %H:%M')}", styles['Normal'])
        story.append(fecha)
        story.append(Spacer(1, 12))
        
        # Contenido
        if isinstance(reporte.content, dict):
            for key, value in reporte.content.items():
                if key == 'resultados_simulacion' and isinstance(value, dict):
                    # Crear tabla para resultados
                    story.append(Paragraph("<b>Resultados de Simulación:</b>", styles['Heading2']))
                    
                    data = [['Métrica', 'Valor']]
                    for metric_key, metric_value in value.items():
                        data.append([metric_key.replace('_', ' ').title(), str(metric_value)])
                    
                    table = Table(data)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 14),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    story.append(table)
                    story.append(Spacer(1, 12))
                elif key != 'graficas':  # Omitir datos de gráficas en PDF
                    content_paragraph = Paragraph(f"<b>{key.replace('_', ' ').title()}:</b> {str(value)}", styles['Normal'])
                    story.append(content_paragraph)
                    story.append(Spacer(1, 6))
        
        # Construir PDF
        doc.build(story)
        return response
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.exception("Error generating PDF")
        messages.error(request, f"Error generando PDF: {str(e)}")
        return redirect('report:report.detail', pk=report_id)

# Report Overview (mantenido para compatibilidad)
@login_required
def report_overview(request, pk):
    return report_detail(request, pk)

# Toggle Report Status
@login_required
def toggle_report_status(request, pk):
    try:
        report = get_object_or_404(Report, pk=pk)
        report.is_active = not report.is_active
        report.save()
        
        status = "activado" if report.is_active else "desactivado"
        messages.success(request, f'Reporte "{report.title}" {status} exitosamente.')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'is_active': report.is_active})
        
        return redirect('report:report.detail', pk=pk)
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)})
        messages.error(request, f"Error: {str(e)}")
        return redirect('report:report.list')

# API Endpoints
@login_required
def report_api_list(request):
    """API endpoint para obtener lista de reportes"""
    try:
        reports = Report.objects.all().order_by('-date_created')
        data = []
        for report in reports:
            data.append({
                'id': report.id,
                'title': report.title,
                'date_created': report.date_created.isoformat(),
                'is_active': report.is_active,
                'product': report.fk_product.name if report.fk_product else None
            })
        return JsonResponse({'reports': data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def report_api_detail(request, pk):
    """API endpoint para obtener detalles de un reporte"""
    try:
        report = get_object_or_404(Report, pk=pk)
        data = {
            'id': report.id,
            'title': report.title,
            'content': report.content,
            'date_created': report.date_created.isoformat(),
            'last_updated': report.last_updated.isoformat(),
            'is_active': report.is_active,
            'product': {
                'id': report.fk_product.id,
                'name': report.fk_product.name
            } if report.fk_product else None
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)