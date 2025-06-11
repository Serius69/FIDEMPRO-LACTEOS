# views/api_views.py
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count

from ..models import Simulation, ResultSimulation
from ..services.simulation_core import SimulationCore

import logging

logger = logging.getLogger(__name__)


class SimulationProgressView(LoginRequiredMixin, View):
    """Check simulation progress"""
    
    def get(self, request, simulation_id):
        try:
            simulation = Simulation.objects.get(
                id=simulation_id,
                fk_questionary_result__fk_questionary__fk_product__fk_business__fk_user=request.user
            )
            
            # Calculate progress based on results
            total_days = simulation.quantity_time
            completed_days = simulation.results.filter(is_active=True).count()
            progress = (completed_days / total_days * 100) if total_days > 0 else 0
            
            # Determine status based on results
            if completed_days == 0:
                status = 'pending'
                message = 'Simulación pendiente de ejecución'
            elif completed_days < total_days:
                status = 'processing'
                message = f'Procesando día {completed_days} de {total_days}'
            else:
                status = 'completed'
                message = 'Simulación completada'
            
            return JsonResponse({
                'status': status,
                'progress': round(progress, 2),
                'message': message,
                'completed_days': completed_days,
                'total_days': total_days
            })
            
        except Simulation.DoesNotExist:
            return JsonResponse({'error': 'Simulación no encontrada'}, status=404)
        except Exception as e:
            logger.error(f"Error checking progress: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)


class SimulationRetryView(LoginRequiredMixin, View):
    """Retry failed simulation"""
    
    def post(self, request, simulation_id):
        try:
            simulation = Simulation.objects.get(
                id=simulation_id,
                fk_questionary_result__fk_questionary__fk_product__fk_business__fk_user=request.user
            )
            
            # Delete existing results
            simulation.results.all().delete()
            simulation.demands.all().delete()
            
            # Re-execute simulation
            service = SimulationCore()
            service.execute_simulation(simulation)
            
            return JsonResponse({
                'success': True,
                'message': 'Simulación reiniciada correctamente'
            })
            
        except Exception as e:
            logger.error(f"Error retrying simulation: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)


class SimulationDuplicateView(LoginRequiredMixin, View):
    """Duplicate simulation"""
    
    def post(self, request, simulation_id):
        try:
            original = Simulation.objects.get(
                id=simulation_id,
                fk_questionary_result__fk_questionary__fk_product__fk_business__fk_user=request.user
            )
            
            # Create duplicate
            duplicate = Simulation.objects.create(
                fk_questionary_result=original.fk_questionary_result,
                quantity_time=original.quantity_time,
                unit_time=original.unit_time,
                demand_history=original.demand_history,
                fk_fdp=original.fk_fdp,
                confidence_level=original.confidence_level,
                random_seed=original.random_seed,
                is_active=True
            )
            
            return JsonResponse({
                'success': True,
                'new_id': duplicate.id,
                'message': 'Simulación duplicada correctamente'
            })
            
        except Exception as e:
            logger.error(f"Error duplicating simulation: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)


class SimulationStartView(LoginRequiredMixin, View):
    """Start pending simulation"""
    
    def post(self, request, simulation_id):
        try:
            simulation = Simulation.objects.get(
                id=simulation_id,
                fk_questionary_result__fk_questionary__fk_product__fk_business__fk_user=request.user
            )
            
            # Check if already has results
            if simulation.results.exists():
                return JsonResponse({
                    'success': False,
                    'message': 'La simulación ya fue ejecutada. Use reintentar para volver a ejecutar.'
                })
            
            # Execute simulation
            service = SimulationCore()
            service.execute_simulation(simulation)
            
            return JsonResponse({
                'success': True,
                'message': 'Simulación iniciada correctamente'
            })
            
        except Exception as e:
            logger.error(f"Error starting simulation: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)


class SimulationDeleteView(LoginRequiredMixin, View):
    """Delete simulation (soft delete)"""
    
    def post(self, request, simulation_id):
        try:
            simulation = Simulation.objects.get(
                id=simulation_id,
                fk_questionary_result__fk_questionary__fk_product__fk_business__fk_user=request.user
            )
            
            # Soft delete
            simulation.is_active = False
            simulation.save()
            
            # Also deactivate related records
            simulation.results.update(is_active=False)
            simulation.demands.update(is_active=False)
            
            return JsonResponse({
                'success': True,
                'message': 'Simulación eliminada correctamente'
            })
            
        except Exception as e:
            logger.error(f"Error deleting simulation: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)