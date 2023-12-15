from pyexpat.errors import messages
from django.shortcuts import render, get_object_or_404, redirect
from .models import Report
from variable.models import Variable
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.conf import settings
from django.http import JsonResponse
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from django.http import HttpResponseForbidden
import openai
import logging
from django.http import FileResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Create your views here.
class AppsView(LoginRequiredMixin, TemplateView):
    pass

# List
def report_list(request):
    try:
        reports = Report.objects.all().order_by('-id')
        context = {'reports': reports}
        return render(request, 'report/report-list.html', context)
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)

# Detail
def report_overview(request, pk):
    # Configura el registro dentro de la función o vista.
    logger = logging.getLogger(__name__)
    logger.debug("This is a log message.")
    current_datetime = timezone.now()
    try:
        report = get_object_or_404(Report, pk=pk)
        businesses = Report.objects.all().order_by('-id')
        context = {'businesses': businesses, 'report': report, 'current_datetime': current_datetime}
        return render(request, 'report/report-overview.html', context)
    except Exception as e:
        # Registra el error completo
        logger.exception("An error occurred in the 'read_business_view' view")
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)

def generar_reporte_pdf(request, report_id):
    # Obtener el objeto Report
    reporte = get_object_or_404(Report, pk=report_id)

    # Configuración del response para un archivo PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{reporte.title}.pdf"'

    # Crear el objeto PDF con reportlab
    p = canvas.Canvas(response)
    p.drawString(100, 800, f'Título del Informe: {reporte.title}')
    p.drawString(100, 780, 'Contenido:')
    
    # Iterar sobre el contenido JSON y agregarlo al PDF
    y_position = 760
    for key, value in reporte.content.items():
        p.drawString(120, y_position, f'{key}: {value}')
        y_position -= 20

    # Cerrar el objeto PDF
    p.showPage()
    p.save()

    return response
def create_report(request):
    try:
        if request.method == 'POST':
            title = request.POST['title']
            content = request.POST['content']
            report = Report(title=title, content=content)
            report.save()
            return redirect('report_list')  # Redirect to a list of reports
        return render(request, 'create_report.html')
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)
