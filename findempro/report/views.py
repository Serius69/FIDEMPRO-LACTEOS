from pyexpat.errors import messages
from django.shortcuts import render, get_object_or_404, redirect
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

# List
def report_list(request):
    reports = Report.objects.all().order_by('-id')
    businesses = Business.objects.all().order_by('-id')
    context = {'reports': reports}
    return render(request, 'report/report-list.html', context)

# Detail
def report_overview(request, pk):
    # Configura el registro dentro de la función o vista.
    logger = logging.getLogger(__name__)
    logger.debug("This is a log message.")
    current_datetime = timezone.now()
    try:
        report = get_object_or_404(Report, pk=pk)
        businesses = Report.objects.all().order_by('-id')
        context = {'businesses': businesses, 'report': report, 'current_datetime': current_datetime}  # Corrected the context variable name
        return render(request, 'report/report-overview.html', context)
    except Exception as e:
        # Registra el error completo
        logger.exception("An error occurred in the 'business_overview' view")
        messages.error(request, "An error occurred. Please check the server logs for more information.")
        return HttpResponse(status=500)  # Return an HTTP 500 error response

def generate_pdf_report(request):
    # Create a response object with the appropriate PDF content type.
    response = FileResponse(request, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="sample_report.pdf"'

    # Create a PDF canvas and add content to it.
    c = canvas.Canvas(response, pagesize=letter)
    c.drawString(100, 750, "Sample PDF Report")
    # You can add more content here, like tables and charts.

    # Save the PDF and close the canvas.
    c.showPage()
    c.save()

    return response


def create_report(request):
    if request.method == 'POST':
        title = request.POST['title']
        content = request.POST['content']
        report = Report(title=title, content=content)
        report.save()
        return redirect('report_list')  # Redirect to a list of reports

    return render(request, 'create_report.html')
In this example, when you submit a form with a title and content, a new Report object is created and saved to the database.

You can then create views and templates to list, view, update, and delete reports as needed, based on your application's requirements.





