from django.urls import path, include
from report.views import(
    report_list,report_overview,generate_pdf_report
)
app_name = 'report'

urlpatterns = [
    # Report
    path('list/', view=report_list, name='report.list'),
    path('overview/<int:pk>/', view=report_overview, name='report.overview'),
    path('generate-pdf/', view=generate_pdf_report, name='report.generate_pdf'),

]
