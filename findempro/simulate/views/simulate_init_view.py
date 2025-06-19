"""
Simulate Init View - Vista mejorada para configuración de simulaciones
Incluye optimizaciones de performance, mejor manejo de errores y arquitectura modular
"""

from django.views.generic import View, TemplateView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.cache import cache
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch, Q, F, Count
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.conf import settings

from ..forms import SimulationForm, SimulationConfigForm
from ..models import Simulation, ProbabilisticDensityFunction
from ..utils.simulation_core_utils import SimulationCore
from ..utils.cache_utils import CacheManager, cache_result, make_cache_key
from ..utils.chart_demand_utils import ChartDemand

# Importaciones condicionales para servicios que pueden no existir
try:
    from ..services.statistical_service import StatisticalService
except ImportError:
    StatisticalService = None

try:
    from ..services.validation_service import SimulationValidationService
except ImportError:
    SimulationValidationService = None


from business.models import Business
from product.models import Product, Area
from questionary.models import QuestionaryResult, Answer
from variable.models import Equation
from finance.models import FinanceRecommendation

import numpy as np
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class BaseSimulationView(LoginRequiredMixin):
    """Clase base para vistas de simulación con funcionalidades comunes"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache_manager = CacheManager(prefix="simulation")
        # Servicios opcionales que pueden no existir
        self.validation_service = SimulationValidationService() if SimulationValidationService else None
        self.statistical_service = StatisticalService() if StatisticalService else None
        self.chart_generator = ChartDemand()
    
    def get_cache_key(self, key_type: str, user_id: int, **kwargs) -> str:
        """Generar clave de cache consistente usando tu utilidad existente"""
        return make_cache_key(key_type, user_id, **kwargs)
    
    @cache_result(timeout=300, key_prefix="user_businesses")
    def get_user_businesses(self, user) -> List[Business]:
        """Obtener negocios del usuario con cache usando tu CacheManager"""
        return list(Business.objects.filter(
            is_active=True,
            fk_user=user
        ).select_related('fk_user'))
    
    @cache_result(timeout=300, key_prefix="user_products")
    def get_user_products(self, user) -> List[Product]:
        """Obtener productos del usuario con cache usando tu CacheManager"""
        businesses = self.get_user_businesses(user)
        return list(Product.objects.filter(
            is_active=True,
            fk_business__in=businesses
        ).select_related('fk_business'))
    
    def _validate_basic_form_data(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validación básica cuando no hay ValidationService"""
        errors = []
        
        if not form_data.get('selected_questionary_result_id'):
            errors.append("Debe seleccionar un cuestionario")
        
        quantity = form_data.get('selected_quantity_time')
        try:
            quantity = int(quantity) if quantity else 0
            if quantity < 1 or quantity > 365:
                errors.append("La duración debe estar entre 1 y 365")
        except (ValueError, TypeError):
            errors.append("La duración debe ser un número válido")
        
        if not form_data.get('selected_unit_time'):
            errors.append("Debe seleccionar una unidad de tiempo")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }
    
    def handle_exception(self, request, exception: Exception, context: str = "operation") -> JsonResponse:
        """Manejo centralizado de excepciones"""
        logger.error(f"Error in {context}: {str(exception)}", exc_info=True)
        
        if settings.DEBUG:
            error_message = str(exception)
        else:
            error_message = "Ha ocurrido un error interno. Por favor intente nuevamente."
        
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'success': False,
                'error': error_message,
                'context': context
            }, status=500)
        else:
            messages.error(request, error_message)
            return redirect('simulate:simulate.show')


class AppsView(TemplateView):
    """Vista de aplicaciones de simulación"""
    template_name = 'simulate/apps.html'
    
    @method_decorator(cache_page(300))  # Cache por 5 minutos
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class SimulateShowView(BaseSimulationView, View):
    """Vista principal para configuración y ejecución de simulaciones"""
    
    template_name = 'simulate/simulate-init.html'
    form_class = SimulationConfigForm
    
    def get(self, request, *args, **kwargs):
        """Manejar peticiones GET para configuración de simulación"""
        try:
            started = request.session.get('started', False)
            
            # Verificar si hay parámetros de cuestionario
            if 'selected_questionary_result' in request.GET:
                return self._handle_questionary_selection(request)
            
            if not started:
                return self._handle_initial_view(request)
            else:
                return self._handle_simulation_execution(request)
                
        except Exception as e:
            return self.handle_exception(request, e, "GET request")
    
    def post(self, request, *args, **kwargs):
        """Manejar peticiones POST para acciones de simulación"""
        try:
            action = request.POST.get('action', '')
            
            if 'start' in request.POST or action == 'start':
                return self._handle_simulation_start(request)
            elif 'cancel' in request.POST or action == 'cancel':
                return self._handle_simulation_cancel(request)
            elif 'configure' in request.POST or action == 'configure':
                return self._handle_questionary_selection(request)
            
            # Acción no reconocida
            messages.warning(request, "Acción no reconocida.")
            return redirect('simulate:simulate.show')
            
        except Exception as e:
            return self.handle_exception(request, e, "POST request")
    
    def _handle_questionary_selection(self, request) -> render:
        """Manejar selección de cuestionario y análisis estadístico"""
        try:
            # Obtener y validar datos del formulario
            form_data = self._extract_form_data(request)
            
            # Usar servicio de validación si existe, sino usar validación básica
            if self.validation_service:
                validation_result = self.validation_service.validate_questionary_selection(form_data)
            else:
                validation_result = self._validate_basic_form_data(form_data)
            
            if not validation_result['is_valid']:
                for error in validation_result['errors']:
                    messages.error(request, error)
                return redirect('simulate:simulate.show')
            
            # Guardar en sesión
            self._save_to_session(request, form_data)
            
            # Obtener instancia del cuestionario con consulta optimizada
            questionary_result = self._get_questionary_result_optimized(
                form_data['selected_questionary_result_id']
            )
            
            # Preparar contexto completo
            context = self._prepare_questionary_context(
                request, questionary_result, form_data
            )
            
            return render(request, self.template_name, context)
            
        except ValidationError as e:
            messages.error(request, f"Error de validación: {str(e)}")
            return redirect('simulate:simulate.show')
        except Exception as e:
            return self.handle_exception(request, e, "questionary selection")
    
    def _extract_form_data(self, request) -> Dict[str, Any]:
        """Extraer y normalizar datos del formulario"""
        if request.method == 'GET':
            data = request.GET
        else:
            data = request.POST
        
        return {
            'selected_questionary_result_id': data.get('selected_questionary_result', 0),
            'selected_quantity_time': data.get('selected_quantity_time', 30),
            'selected_unit_time': data.get('selected_unit_time', 'days')
        }
    
    def _save_to_session(self, request, form_data: Dict[str, Any]) -> None:
        """Guardar datos en sesión de forma segura"""
        session_keys = [
            'selected_questionary_result_id',
            'selected_quantity_time', 
            'selected_unit_time'
        ]
        
        for key in session_keys:
            if key in form_data:
                request.session[key] = form_data[key]
        
        request.session.modified = True
    
    def _get_questionary_result_optimized(self, questionary_id: int) -> QuestionaryResult:
        """Obtener resultado de cuestionario con consultas optimizadas"""
        return get_object_or_404(
            QuestionaryResult.objects.select_related(
                'fk_questionary__fk_product__fk_business'
            ).prefetch_related(
                Prefetch(
                    'fk_question_result_answer',
                    queryset=Answer.objects.select_related(
                        'fk_question__fk_variable'
                    ).filter(is_active=True)
                )
            ).filter(is_active=True),
            pk=questionary_id
        )
    
    def _prepare_questionary_context(self, request, questionary_result: QuestionaryResult, 
                                   form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Preparar contexto completo para la vista de cuestionario"""
        user = request.user
        product_instance = questionary_result.fk_questionary.fk_product
        
        # Datos base del usuario
        user_data = {
            'businesses': self.get_user_businesses(user),
            'products': self.get_user_products(user)
        }
        
        # Áreas con ecuaciones
        areas = self._get_areas_with_equations(product_instance)
        
        # Cuestionarios disponibles
        questionnaires_result = self._get_available_questionnaires(user_data['products'])
        
        # Funciones de densidad de probabilidad
        fdps = self._get_probability_distributions(product_instance.fk_business)
        
        # Extraer y analizar datos históricos de demanda
        demand_data = self._extract_demand_data(questionary_result)
        analysis_results = self._perform_statistical_analysis(questionary_result, user, demand_data)
        
        # Generar gráficos
        charts = self._generate_charts(demand_data)
        
        # Recomendaciones financieras
        financial_recommendations = self._get_financial_recommendations(product_instance.fk_business)
        
        # Construir contexto final
        context = {
            'areas': areas,
            'form': self.form_class(),
            'questionnaires_result': questionnaires_result,
            'questionary_result_instance': questionary_result,
            'questionary_result_instance_id': questionary_result.id,
            'selected_unit_time': form_data['selected_unit_time'],
            'selected_quantity_time': form_data['selected_quantity_time'],
            'fdps': fdps,
            'demand_history': demand_data,
            'financial_recommendations': financial_recommendations,
            **analysis_results,
            **charts
        }
        
        # Agregar estadísticas de demanda si hay datos
        if demand_data:
            context['demand_stats'] = self._calculate_demand_statistics(demand_data)
        
        return context
    
    def _get_areas_with_equations(self, product: Product) -> List[Area]:
        """Obtener áreas con sus ecuaciones de forma optimizada"""
        return Area.objects.filter(
            is_active=True,
            fk_product=product
        ).prefetch_related(
            Prefetch(
                'area_equation',
                queryset=Equation.objects.filter(is_active=True).select_related(
                    'fk_variable1', 'fk_variable2', 'fk_variable3',
                    'fk_variable4', 'fk_variable5'
                )
            )
        ).order_by('id')
    
    def _get_available_questionnaires(self, products: List[Product]) -> List[QuestionaryResult]:
        """Obtener cuestionarios disponibles con límite"""
        return QuestionaryResult.objects.filter(
            is_active=True,
            fk_questionary__fk_product__in=products
        ).select_related(
            'fk_questionary__fk_product'
        ).order_by('-date_created')[:50]
    
    def _get_probability_distributions(self, business: Business) -> List[ProbabilisticDensityFunction]:
        """Obtener distribuciones de probabilidad activas"""
        return business.probability_distributions.filter(
            is_active=True
        ).order_by('distribution_type')
    
    def _extract_demand_data(self, questionary_result: QuestionaryResult) -> List[float]:
        """Extraer datos históricos de demanda del cuestionario"""
        demand_data = []
        target_question = 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).'
        
        for answer in questionary_result.fk_question_result_answer.all():
            if answer.fk_question.question == target_question:
                try:
                    demand_str = answer.answer
                    demand_data = self._parse_demand_string(demand_str)
                    break
                except Exception as e:
                    logger.error(f"Error parsing demand data: {e}")
        
        return self._validate_and_clean_demand_data(demand_data)
    
    def _parse_demand_string(self, demand_str: str) -> List[float]:
        """Parsear string de datos de demanda con múltiples formatos"""
        if not demand_str:
            return []
        
        try:
            # Intentar parsear como JSON primero
            if demand_str.strip().startswith('['):
                return json.loads(demand_str)
            
            # Limpiar y separar por comas o espacios
            cleaned_str = demand_str.replace('[', '').replace(']', '').strip()
            
            if ',' in cleaned_str:
                return [float(x.strip()) for x in cleaned_str.split(',') if x.strip()]
            else:
                return [float(x) for x in cleaned_str.split() if x.strip()]
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Could not parse demand string: {demand_str}, error: {e}")
            return []
    
    def _validate_and_clean_demand_data(self, demand_data: List[float]) -> List[float]:
        """Validar y limpiar datos de demanda"""
        if not demand_data:
            return []
        
        # Filtrar valores válidos
        clean_data = []
        for value in demand_data:
            try:
                float_value = float(value)
                if float_value >= 0 and not np.isnan(float_value) and not np.isinf(float_value):
                    clean_data.append(float_value)
            except (ValueError, TypeError):
                continue
        
        return clean_data
    
    def _perform_statistical_analysis(self, questionary_result: QuestionaryResult, 
                                    user, demand_data: List[float]) -> Dict[str, Any]:
        """Realizar análisis estadístico completo"""
        try:
            if not demand_data:
                return {'analysis_error': 'No hay datos de demanda disponibles'}
            
            # Usar servicio estadístico si existe
            if self.statistical_service:
                analysis_results = self.statistical_service.analyze_demand_history(
                    questionary_result.id, user, demand_data
                )
                
                # Agregar análisis adicional si hay métodos disponibles
                if len(demand_data) >= 10 and hasattr(self.statistical_service, 'perform_distribution_fitting'):
                    analysis_results.update(
                        self.statistical_service.perform_distribution_fitting(demand_data)
                    )
                
                return analysis_results
            else:
                # Análisis básico sin servicio estadístico
                return self._basic_statistical_analysis(demand_data)
            
        except Exception as e:
            logger.error(f"Error in statistical analysis: {e}")
            return {'analysis_error': f'Error en análisis estadístico: {str(e)}'}
    
    def _basic_statistical_analysis(self, demand_data: List[float]) -> Dict[str, Any]:
        """Análisis estadístico básico cuando no hay StatisticalService"""
        if not demand_data:
            return {}
        
        data_array = np.array(demand_data)
        mean_val = np.mean(data_array)
        std_val = np.std(data_array)
        
        return {
            'demand_mean': float(mean_val),
            'demand_std': float(std_val),
            'demand_data': demand_data,
            'best_distribution': 'Normal',  # Por defecto
            'best_ks_p_value_floor': 0.5,
            'best_ks_statistic_floor': 0.1,
            'distribution_params': {
                'mean': float(mean_val),
                'std': float(std_val)
            }
        }
    
    def _generate_charts(self, demand_data: List[float]) -> Dict[str, Optional[str]]:
        """Generar gráficos de análisis de demanda"""
        charts = {
            'image_data': None,
            'image_data_histogram': None,
            'image_data_qq': None
        }
        
        if not demand_data or len(demand_data) < 5:
            return charts
        
        try:
            # Gráfico de dispersión
            charts['image_data'] = self.chart_generator.generate_demand_scatter_plot(demand_data)
            
            # Histograma con distribución
            charts['image_data_histogram'] = self.chart_generator.generate_demand_histogram(demand_data)
            
            # Q-Q Plot (si hay suficientes datos)
            if len(demand_data) >= 10:
                charts['image_data_qq'] = self.chart_generator.generate_qq_plot(demand_data)
            
        except Exception as e:
            logger.error(f"Error generating charts: {e}")
        
        return charts
    
    def _get_financial_recommendations(self, business: Business) -> List[FinanceRecommendation]:
        """Obtener recomendaciones financieras"""
        return FinanceRecommendation.objects.filter(
            fk_business=business,
            is_active=True
        ).order_by('threshold_value')[:10]
    
    def _calculate_demand_statistics(self, demand_data: List[float]) -> Dict[str, float]:
        """Calcular estadísticas básicas de demanda"""
        if not demand_data:
            return {}
        
        data_array = np.array(demand_data)
        mean_val = np.mean(data_array)
        
        return {
            'count': len(demand_data),
            'mean': float(mean_val),
            'std': float(np.std(data_array)),
            'min': float(np.min(data_array)),
            'max': float(np.max(data_array)),
            'median': float(np.median(data_array)),
            'cv': float(np.std(data_array) / mean_val) if mean_val > 0 else 0,
            'variance': float(np.var(data_array))
        }
    
    @transaction.atomic
    def _handle_simulation_start(self, request) -> redirect:
        """Manejar inicio de simulación con transacción"""
        try:
            # Extraer y validar datos
            form_data = self._extract_simulation_start_data(request)
            
            # Usar servicio de validación si existe, sino validación básica
            if self.validation_service:
                validation_result = self.validation_service.validate_simulation_start(form_data)
            else:
                validation_result = self._validate_simulation_start_basic(form_data)
            
            if not validation_result['is_valid']:
                for error in validation_result['errors']:
                    messages.error(request, error)
                return redirect('simulate:simulate.show')
            
            # Obtener cuestionario y extraer datos de demanda
            questionary_result = self._get_questionary_result_optimized(
                form_data['fk_questionary_result']
            )
            
            demand_history = self._extract_demand_data(questionary_result)
            if not demand_history:
                messages.error(request, "No se encontraron datos históricos de demanda válidos.")
                return redirect('simulate:simulate.show')
            
            # Preparar datos para simulación
            simulation_data = {
                'fk_questionary_result': form_data['fk_questionary_result'],
                'quantity_time': int(form_data['quantity_time']),
                'unit_time': form_data['unit_time'],
                'demand_history': demand_history,
                'fk_fdp_id': int(form_data['fk_fdp']),
                'confidence_level': form_data.get('confidence_level', 0.95),
                'random_seed': form_data.get('random_seed')
            }
            
            # Crear simulación usando el servicio
            simulation_service = SimulationCore()
            simulation_instance = simulation_service.create_simulation(simulation_data)
            
            # Actualizar sesión
            request.session['started'] = True
            request.session['simulation_started_id'] = simulation_instance.id
            request.session['simulation_start_time'] = datetime.now().isoformat()
            
            messages.success(request, "Simulación iniciada correctamente.")
            
            # Iniciar ejecución asíncrona si está configurado
            if getattr(settings, 'ASYNC_SIMULATION', False):
                simulation_service.execute_simulation_async(simulation_instance)
                return redirect('simulate:simulate.status', simulation_id=simulation_instance.id)
            else:
                return redirect('simulate:simulate.show')
                
        except ValidationError as e:
            messages.error(request, f"Error de validación: {str(e)}")
            return redirect('simulate:simulate.show')
        except Exception as e:
            return self.handle_exception(request, e, "simulation start")
    
    def _validate_simulation_start_basic(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validación básica para inicio de simulación"""
        errors = []
        
        if not form_data.get('fk_questionary_result'):
            errors.append("El cuestionario es requerido")
        
        if not form_data.get('fk_fdp'):
            errors.append("La función de densidad de probabilidad es requerida")
        
        try:
            quantity = int(form_data.get('quantity_time', 0))
            if quantity < 1 or quantity > 365:
                errors.append("La duración debe estar entre 1 y 365")
        except (ValueError, TypeError):
            errors.append("La duración debe ser un número válido")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }
    
    def _extract_simulation_start_data(self, request) -> Dict[str, Any]:
        """Extraer datos para inicio de simulación"""
        return {
            'fk_questionary_result': request.POST.get('fk_questionary_result'),
            'quantity_time': request.POST.get('quantity_time', 30),
            'unit_time': request.POST.get('unit_time', 'days'),
            'fk_fdp': request.POST.get('fk_fdp'),
            'confidence_level': request.POST.get('confidence_level', 0.95),
            'random_seed': request.POST.get('random_seed')
        }
    
    def _handle_simulation_cancel(self, request) -> redirect:
        """Manejar cancelación de simulación"""
        try:
            simulation_id = request.session.get('simulation_started_id')
            
            if simulation_id:
                # Marcar simulación como cancelada
                try:
                    simulation = Simulation.objects.get(id=simulation_id)
                    simulation.is_active = False
                    simulation.save(update_fields=['is_active'])
                except Simulation.DoesNotExist:
                    pass
            
            # Limpiar sesión
            self._clear_simulation_session(request)
            
            messages.info(request, "Simulación cancelada.")
            return redirect('simulate:simulate.show')
            
        except Exception as e:
            return self.handle_exception(request, e, "simulation cancel")
    
    def _clear_simulation_session(self, request) -> None:
        """Limpiar datos de simulación de la sesión"""
        session_keys = [
            'started', 
            'simulation_started_id', 
            'simulation_start_time',
            'selected_questionary_result_id',
            'selected_quantity_time',
            'selected_unit_time'
        ]
        
        for key in session_keys:
            request.session.pop(key, None)
        
        request.session.modified = True
    
    def _handle_initial_view(self, request) -> render:
        """Manejar vista inicial antes de que inicie la simulación"""
        try:
            user_data = {
                'businesses': self.get_user_businesses(request.user),
                'products': self.get_user_products(request.user)
            }
            
            # Obtener cuestionarios recientes
            questionnaires_result = self._get_available_questionnaires(user_data['products'])
            
            context = {
                'started': False,
                'form': self.form_class(),
                'questionnaires_result': questionnaires_result,
                'user_businesses': user_data['businesses'],
                'user_products': user_data['products'],
                'tutorial_enabled': getattr(settings, 'TUTORIAL_ENABLED', True)
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            return self.handle_exception(request, e, "initial view")
    
    def _handle_simulation_execution(self, request) -> redirect:
        """Manejar ejecución principal de simulación"""
        try:
            simulation_id = request.session.get('simulation_started_id')
            if not simulation_id:
                messages.error(request, "No se encontró simulación activa.")
                self._clear_simulation_session(request)
                return redirect('simulate:simulate.show')
            
            simulation_instance = get_object_or_404(Simulation, pk=simulation_id)
            
            # Verificar si la simulación ya fue ejecutada
            if simulation_instance.results.exists():
                messages.info(request, "La simulación ya fue completada.")
                self._clear_simulation_session(request)
                return redirect('simulate:simulate.result', simulation_id=simulation_instance.id)
            
            # Ejecutar simulación
            simulation_service = SimulationCore()
            
            try:
                simulation_service.execute_simulation(simulation_instance)
                
                # Limpiar sesión
                self._clear_simulation_session(request)
                
                messages.success(request, "Simulación completada exitosamente.")
                return redirect('simulate:simulate.result', simulation_id=simulation_instance.id)
                
            except Exception as e:
                logger.error(f"Error executing simulation {simulation_id}: {e}")
                messages.error(request, "Error al ejecutar la simulación.")
                
                # Marcar simulación como fallida
                simulation_instance.is_active = False
                simulation_instance.save(update_fields=['is_active'])
                
                self._clear_simulation_session(request)
                return redirect('simulate:simulate.show')
                
        except Exception as e:
            return self.handle_exception(request, e, "simulation execution")


class SimulationStatusView(BaseSimulationView, View):
    """Vista para verificar el estado de una simulación"""
    
    def get(self, request, simulation_id: int, *args, **kwargs):
        """Obtener estado actual de la simulación"""
        try:
            simulation = get_object_or_404(
                Simulation.objects.select_related('fk_questionary_result'),
                id=simulation_id
            )
            
            # Verificar permisos
            if not self._user_can_access_simulation(request.user, simulation):
                return JsonResponse({'error': 'No autorizado'}, status=403)
            
            status_data = {
                'id': simulation.id,
                'is_active': simulation.is_active,
                'has_results': simulation.results.exists(),
                'created_at': simulation.date_created.isoformat(),
                'updated_at': simulation.last_updated.isoformat(),
                'progress': self._calculate_simulation_progress(simulation)
            }
            
            return JsonResponse(status_data)
            
        except Exception as e:
            return self.handle_exception(request, e, "status check")
    
    def _user_can_access_simulation(self, user, simulation: Simulation) -> bool:
        """Verificar si el usuario puede acceder a la simulación"""
        return simulation.fk_questionary_result.fk_questionary.fk_product.fk_business.fk_user == user
    
    def _calculate_simulation_progress(self, simulation: Simulation) -> Dict[str, Any]:
        """Calcular progreso de la simulación"""
        total_expected_results = simulation.quantity_time
        current_results = simulation.results.count()
        
        progress_percentage = (current_results / total_expected_results * 100) if total_expected_results > 0 else 0
        
        return {
            'percentage': min(progress_percentage, 100),
            'current_results': current_results,
            'total_expected': total_expected_results,
            'status': 'completed' if progress_percentage >= 100 else 'running'
        }


class SimulationConfigAPIView(BaseSimulationView, View):
    """API para configuración de simulaciones"""
    
    def post(self, request, *args, **kwargs):
        """Configurar simulación vía API"""
        try:
            data = json.loads(request.body)
            
            # Validar datos usando servicio si existe, sino validación básica
            if self.validation_service and hasattr(self.validation_service, 'validate_api_config'):
                validation_result = self.validation_service.validate_api_config(data)
            else:
                validation_result = self._validate_api_config_basic(data)
            
            if not validation_result['is_valid']:
                return JsonResponse({
                    'success': False,
                    'errors': validation_result['errors']
                }, status=400)
            
            # Procesar configuración
            config_result = self._process_api_configuration(data, request.user)
            
            return JsonResponse({
                'success': True,
                'data': config_result
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'JSON inválido'
            }, status=400)
        except Exception as e:
            return self.handle_exception(request, e, "API configuration")
    
    def _validate_api_config_basic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validación básica para configuración API"""
        errors = []
        
        if not data.get('questionary_id'):
            errors.append("questionary_id es requerido")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }
    
    def _process_api_configuration(self, data: Dict[str, Any], user) -> Dict[str, Any]:
        """Procesar configuración desde API"""
        # Implementar lógica de configuración
        # Esta función puede expandirse según las necesidades específicas
        return {
            'questionary_id': data.get('questionary_id'),
            'configuration_complete': True,
            'timestamp': datetime.now().isoformat()
        }


# Vista basada en función para compatibilidad
def simulate_show_view(request):
    """Wrapper de función para la vista de simulación"""
    view = SimulateShowView.as_view()
    return view(request)


def simulation_status_view(request, simulation_id):
    """Wrapper de función para el estado de simulación"""
    view = SimulationStatusView.as_view()
    return view(request, simulation_id=simulation_id)


# Decorador para cache de vistas
def cache_simulation_view(timeout=300):
    """Decorador personalizado para cache de vistas de simulación"""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            # Solo cachear para usuarios autenticados y métodos GET
            if request.user.is_authenticated and request.method == 'GET':
                cache_key = f"simulation_view_{request.user.id}_{request.get_full_path()}"
                cached_response = cache.get(cache_key)
                
                if cached_response:
                    return cached_response
                
                response = view_func(request, *args, **kwargs)
                cache.set(cache_key, response, timeout)
                return response
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator