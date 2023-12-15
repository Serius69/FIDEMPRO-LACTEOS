from django.urls import path, include
from report.views import(
    report_list,report_overview,
    generar_reporte_pdf
)
app_name = 'report'

urlpatterns = [
    # Report
    path('list/', view=report_list, name='report.list'),
    path('overview/<int:pk>/', view=report_overview, name='report.overview'),
        path('generar_reporte_pdf/<int:report_id>/', generar_reporte_pdf, name='generar_reporte_pdf'),
]
