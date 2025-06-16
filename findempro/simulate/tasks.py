# tasks.py
import logging
from typing import Dict, Any
from celery import shared_task, Task
from celery.result import AsyncResult
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings

from .models import Simulation, ResultSimulation
from .utils.simulation_core_utils import SimulationCore
from .utils.chart_base_utils import ChartBase
from .utils.chart_utils import ChartGenerator

logger = logging.getLogger(__name__)


class SimulationTask(Task):
    """Base task class for simulation tasks"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        logger.error(f"Task {task_id} failed: {exc}")
        
        # Update simulation status if ID is available
        if args:
            simulation_id = args[0]
            try:
                simulation = Simulation.objects.get(id=simulation_id)
                simulation.status = 'failed'
                simulation.error_message = str(exc)
                simulation.save()
            except Simulation.DoesNotExist:
                pass
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success"""
        logger.info(f"Task {task_id} completed successfully")


@shared_task(base=SimulationTask, bind=True, max_retries=3)
def execute_simulation_async(self, simulation_id: int) -> Dict[str, Any]:
    """Execute simulation asynchronously"""
    try:
        logger.info(f"Starting async simulation {simulation_id}")
        
        # Update task progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Initializing...'}
        )
        
        # Get simulation instance
        simulation = Simulation.objects.get(id=simulation_id)
        simulation.status = 'processing'
        simulation.celery_task_id = self.request.id
        simulation.save()
        
        # Initialize service
        service = SimulationCore()
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': 'Loading data...'}
        )
        
        # Execute simulation with progress updates
        total_days = int(simulation.quantity_time)
        
        # Custom execute method with progress callback
        def progress_callback(current_day):
            progress = 10 + (current_day / total_days * 80)  # 10-90% for simulation
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': progress,
                    'total': 100,
                    'status': f'Simulating day {current_day}/{total_days}...'
                }
            )
        
        # Execute simulation
        service.execute_simulation_with_progress(simulation, progress_callback)
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 90, 'total': 100, 'status': 'Generating results...'}
        )
        
        # Generate charts
        results = ResultSimulation.objects.filter(fk_simulation_id=simulation_id)
        chart_generator = ChartGenerator()
        charts = chart_generator.generate_all_charts(
            simulation_id, simulation, list(results)
        )
        
        # Update simulation status
        simulation.status = 'completed'
        simulation.save()
        
        # Send notification email if configured
        if hasattr(settings, 'SEND_SIMULATION_EMAILS') and settings.SEND_SIMULATION_EMAILS:
            send_simulation_complete_email.delay(simulation_id)
        
        # Final progress update
        self.update_state(
            state='SUCCESS',
            meta={'current': 100, 'total': 100, 'status': 'Completed!'}
        )
        
        return {
            'status': 'success',
            'simulation_id': simulation_id,
            'results_count': results.count(),
            'charts_generated': len(charts.get('chart_images', {}))
        }
        
    except Exception as e:
        logger.error(f"Error in async simulation {simulation_id}: {str(e)}")
        
        # Retry with exponential backoff
        retry_in = 60 * (2 ** self.request.retries)  # 1min, 2min, 4min
        
        self.retry(
            exc=e,
            countdown=retry_in,
            max_retries=3
        )


@shared_task
def send_simulation_complete_email(simulation_id: int):
    """Send email notification when simulation completes"""
    try:
        simulation = Simulation.objects.select_related(
            'fk_questionary_result__fk_questionary__fk_product__fk_business__fk_user'
        ).get(id=simulation_id)
        
        user = simulation.fk_questionary_result.fk_questionary.fk_product.fk_business.fk_user
        product = simulation.fk_questionary_result.fk_questionary.fk_product
        
        subject = f"Simulación Completada - {product.name}"
        message = f"""
        Estimado {user.get_full_name() or user.username},
        
        Su simulación para el producto {product.name} ha sido completada exitosamente.
        
        Detalles:
        - ID de Simulación: {simulation_id}
        - Duración: {simulation.quantity_time} {simulation.unit_time}
        - Fecha de finalización: {simulation.last_updated.strftime('%d/%m/%Y %H:%M')}
        
        Puede ver los resultados en:
        {settings.SITE_URL}/simulate/result/{simulation_id}/
        
        Saludos,
        El equipo de Simulación
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        logger.info(f"Email sent to {user.email} for simulation {simulation_id}")
        
    except Exception as e:
        logger.error(f"Error sending email for simulation {simulation_id}: {str(e)}")


@shared_task
def cleanup_old_simulations():
    """Clean up old simulation data periodically"""
    from datetime import timedelta
    from django.utils import timezone
    
    try:
        # Delete simulations older than 90 days
        cutoff_date = timezone.now() - timedelta(days=90)
        
        old_simulations = Simulation.objects.filter(
            date_created__lt=cutoff_date,
            status='completed'
        )
        
        count = old_simulations.count()
        
        # Delete related data first
        for sim in old_simulations:
            # Clear cache
            cache.delete(f"simulation_results_{sim.id}")
            cache.delete(f"charts_{sim.id}")
            
            # Delete results
            ResultSimulation.objects.filter(fk_simulation=sim).delete()
        
        # Delete simulations
        old_simulations.delete()
        
        logger.info(f"Cleaned up {count} old simulations")
        
        return {'deleted_count': count}
        
    except Exception as e:
        logger.error(f"Error in cleanup task: {str(e)}")
        raise


@shared_task
def generate_simulation_report(simulation_id: int, format: str = 'pdf'):
    """Generate detailed simulation report"""
    try:
        from .utils.report_generator import ReportGenerator
        
        simulation = Simulation.objects.get(id=simulation_id)
        generator = ReportGenerator()
        
        if format == 'pdf':
            report_path = generator.generate_pdf_report(simulation)
        elif format == 'excel':
            report_path = generator.generate_excel_report(simulation)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        # Store report path in cache
        cache.set(f"report_{simulation_id}_{format}", report_path, 3600)
        
        return {
            'status': 'success',
            'report_path': report_path,
            'format': format
        }
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise


@shared_task
def check_simulation_status(task_id: str) -> Dict[str, Any]:
    """Check the status of an async simulation task"""
    try:
        result = AsyncResult(task_id)
        
        return {
            'task_id': task_id,
            'status': result.status,
            'result': result.result,
            'info': result.info
        }
        
    except Exception as e:
        logger.error(f"Error checking task status: {str(e)}")
        return {
            'task_id': task_id,
            'status': 'ERROR',
            'error': str(e)
        }


# Periodic tasks (configure in celery beat)
@shared_task
def daily_statistics_update():
    """Update daily statistics for all active simulations"""
    try:
        from django.db.models import Count, Avg
        from datetime import timedelta
        from django.utils import timezone
        
        yesterday = timezone.now() - timedelta(days=1)
        
        stats = Simulation.objects.filter(
            date_created__gte=yesterday
        ).aggregate(
            total_simulations=Count('id'),
            avg_duration=Avg('quantity_time'),
        )
        
        # Store in cache for dashboard
        cache.set('daily_simulation_stats', stats, 86400)  # 24 hours
        
        logger.info(f"Daily stats updated: {stats}")
        
        return stats
        
    except Exception as e:
        logger.error(f"Error updating daily stats: {str(e)}")
        raise