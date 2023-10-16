from django.urls import path, include
from report.views import(
    report_list
)
app_name = 'question'

urlpatterns = [
    # Report
    path('list/', view=report_list, name='report.list'),
    path('overview/', view=generate_questions_for_variables, name='report.overview'),
    path('generate-pdf-report/', views.generate_pdf_report, name='generate_pdf_report'),

]
