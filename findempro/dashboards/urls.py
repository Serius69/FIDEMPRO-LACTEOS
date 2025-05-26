from pyexpat.errors import messages
from django.urls import path
from django.views.decorators.cache import cache_page
from dashboards.views import (
    index,
    dashboard_admin,
    dashboard_user,
    get_chart_data,
    update_business_metrics,
    # # Nuevas vistas agregadas
    # export_recommendations,
    # dashboard_api,
    # chart_builder,
    # analytics_report,
)

app_name = 'dashboard'

urlpatterns = [
    # Vistas principales
    path('', index, name='index'),
    path('admin/', dashboard_admin, name='dashboard.admin'),
    path('user/', dashboard_user, name='dashboard.user'),
    
    # API endpoints
    path('api/chart/<int:chart_id>/', get_chart_data, name='get_chart_data'),
    path('api/update-metrics/', update_business_metrics, name='update_metrics'),
    # path('api/dashboard-data/', dashboard_api, name='dashboard_api'),
    
    # # Exportación y reportes
    # path('export/recommendations/', export_recommendations, name='export_recommendations'),
    # path('analytics/report/', analytics_report, name='analytics_report'),
    
    # # Chart builder
    # path('charts/builder/', chart_builder, name='chart_builder'),
    
    # URLs con caché para mejorar rendimiento
    path('cached/user/', 
         cache_page(60 * 5)(dashboard_user), 
         name='dashboard.user.cached'),
]

# Agregar las nuevas vistas al views.py
def export_recommendations(request):
    """Exporta las recomendaciones a Excel/CSV"""
    from django.http import HttpResponse
    import csv
    
    business_id = request.GET.get('business_id')
    if not business_id:
        messages.error(request, 'Business ID requerido')
        return redirect('dashboard:dashboard.user')
    
    # Verificar permisos
    business = get_object_or_404(
        Business,
        pk=business_id,
        fk_user=request.user,
        is_active=True
    )
    
    # Obtener recomendaciones
    recommendations = FinanceRecommendationSimulation.objects.filter(
        fk_finance_recommendation__fk_business=business_id,
        is_active=True
    ).select_related(
        'fk_simulation__fk_questionary_result__fk_questionary__fk_product',
        'fk_finance_recommendation'
    )
    
    # Crear respuesta CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="recomendaciones_{business.name}_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Fecha', 'Producto', 'Variable', 'Valor (%)', 
        'Umbral', 'Recomendación'
    ])
    
    for rec in recommendations:
        writer.writerow([
            rec.fk_simulation.date_created.strftime('%Y-%m-%d'),
            rec.fk_simulation.fk_questionary_result.fk_questionary.fk_product.name,
            rec.fk_finance_recommendation.variable_name,
            f"{rec.data * 100:.2f}",
            rec.fk_finance_recommendation.threshold_value,
            rec.fk_finance_recommendation.recommendation
        ])
    
    return response

def dashboard_api(request):
    """API endpoint para obtener datos del dashboard en JSON"""
    from django.http import JsonResponse
    
    business_id = request.GET.get('business_id')
    if not business_id:
        return JsonResponse({'error': 'Business ID required'}, status=400)
    
    try:
        business = get_object_or_404(
            Business,
            pk=business_id,
            fk_user=request.user,
            is_active=True
        )
        
        # Obtener métricas
        metrics = DashboardService.get_business_metrics(business_id)
        totals = DashboardService.calculate_totals(metrics['simulations'])
        
        # Preparar respuesta
        data = {
            'success': True,
            'business': {
                'id': business.id,
                'name': business.name,
                'type': business.get_type_display(),
            },
            'metrics': {
                'revenue': totals['Total Revenue'],
                'costs': totals['Total Costs'],
                'profit_margin': totals['Total Profit Margin'],
                'inventory': totals['Total Inventory Levels'],
                'demand': totals['Total Demand'],
                'production': totals['Total Production Output'],
            },
            'charts': [
                {
                    'id': chart.id,
                    'title': chart.title,
                    'type': chart.chart_type,
                    'last_updated': chart.last_updated.isoformat()
                }
                for chart in metrics['charts']
            ],
            'products_count': metrics['products'].count(),
            'timestamp': timezone.now().isoformat()
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        logger.error(f"Error in dashboard API: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def chart_builder(request):
    """Vista para construir gráficos personalizados"""
    if request.method == 'POST':
        try:
            import json
            
            data = json.loads(request.body)
            product_id = data.get('product_id')
            chart_type = data.get('chart_type')
            chart_data = data.get('chart_data')
            title = data.get('title')
            
            # Validar datos
            if not all([product_id, chart_type, chart_data, title]):
                return JsonResponse({
                    'success': False,
                    'error': 'Faltan datos requeridos'
                }, status=400)
            
            # Crear gráfico
            product = get_object_or_404(Product, pk=product_id)
            chart = Chart.objects.create(
                title=title,
                chart_type=chart_type,
                chart_data=chart_data,
                fk_product=product
            )
            
            # Generar imagen
            chart.generate_chart_image()
            
            return JsonResponse({
                'success': True,
                'chart_id': chart.id,
                'chart_url': chart.get_photo_url()
            })
            
        except Exception as e:
            logger.error(f"Error in chart builder: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    # GET request - mostrar el builder
    products = Product.objects.filter(
        fk_business__fk_user=request.user,
        fk_business__is_active=True
    )
    
    context = {
        'products': products,
        'chart_types': Chart.CHART_TYPES,
    }
    
    return render(request, 'dashboards/chart_builder.html', context)

def analytics_report(request):
    """Genera un reporte analítico completo"""
    from django.template.loader import render_to_string
    from weasyprint import HTML
    from django.http import HttpResponse
    import tempfile
    
    business_id = request.GET.get('business_id')
    if not business_id:
        messages.error(request, 'Business ID requerido')
        return redirect('dashboard:dashboard.user')
    
    try:
        # Obtener datos
        business = get_object_or_404(
            Business,
            pk=business_id,
            fk_user=request.user,
            is_active=True
        )
        
        metrics = DashboardService.get_business_metrics(business_id)
        totals = DashboardService.calculate_totals(metrics['simulations'])
        
        # Preparar contexto para el reporte
        context = {
            'business': business,
            'metrics': totals,
            'products': metrics['products'],
            'charts': metrics['charts'],
            'report_date': timezone.now(),
            'user': request.user,
        }
        
        # Renderizar HTML
        html_string = render_to_string(
            'dashboards/analytics_report_template.html',
            context
        )
        
        # Generar PDF
        html = HTML(string=html_string)
        pdf = html.write_pdf()
        
        # Crear respuesta
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="reporte_analitico_{business.name}_{timezone.now().strftime("%Y%m%d")}.pdf"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating analytics report: {e}")
        messages.error(request, 'Error al generar el reporte')
        return redirect('dashboard:dashboard.user')