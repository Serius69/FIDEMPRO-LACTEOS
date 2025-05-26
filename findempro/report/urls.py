from django.urls import path
from report.views import (
    # CRUD básico
    report_list,
    report_detail,
    report_create,
    report_update,
    report_delete,
    
    # Simulaciones
    create_simulation_report,
    
    # PDF y utilidades
    generar_reporte_pdf,
    toggle_report_status,
    
    # APIs
    report_api_list,
    report_api_detail,
    
    # Vistas legacy (compatibilidad)
    report_overview,
    AppsView
)

app_name = 'report'

urlpatterns = [
    # CRUD Principal
    path('', view=report_list, name='report.list'),
    path('list/', view=report_list, name='report.list'),
    path('detail/<int:pk>/', view=report_detail, name='report.detail'),
    path('create/', view=report_create, name='report.create'),
    path('update/<int:pk>/', view=report_update, name='report.update'),
    path('delete/<int:pk>/', view=report_delete, name='report.delete'),
    
    # Simulaciones
    path('simulation/create/', view=create_simulation_report, name='simulation.create'),
    
    # PDF Generation
    path('pdf/<int:report_id>/', view=generar_reporte_pdf, name='generar_reporte_pdf'),
    
    # Utilities
    path('toggle-status/<int:pk>/', view=toggle_report_status, name='toggle_status'),
    
    # API Endpoints
    path('api/list/', view=report_api_list, name='api.list'),
    path('api/detail/<int:pk>/', view=report_api_detail, name='api.detail'),
    
    # Legacy URLs (para compatibilidad con código existente)
    path('overview/<int:pk>/', view=report_overview, name='report.overview'),
    path('apps/', view=AppsView.as_view(), name='apps'),
]