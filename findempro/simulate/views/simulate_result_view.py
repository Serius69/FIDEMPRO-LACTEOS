# views/simulate_result_view.py
"""
Vista corregida y optimizada para resultados de simulación.
Genera todos los datos necesarios para los templates HTML.
"""
import json
import logging
from typing import Dict, List, Any, Optional
import numpy as np
import scipy.stats

from simulate.services.statistical_service import StatisticalService
from simulate.utils.chart_demand_utils import ChartDemand
from django.views.generic import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from ..models import Simulation, ResultSimulation
from ..utils.simulation_math_utils import SimulationMathEngine
from ..services.validation_service import SimulationValidationService
from ..utils.simulation_financial_utils import SimulationFinancialAnalyzer
from ..utils.chart_utils import ChartGenerator
from ..utils.data_parsers_utils import DataParser
from questionary.models import Answer
from variable.models import Variable, Equation
from finance.models import FinanceRecommendation, FinanceRecommendationSimulation

logger = logging.getLogger(__name__)


class SimulateResultView(LoginRequiredMixin, View):
    """Vista optimizada para mostrar resultados de simulación con todos los datos necesarios"""
    
    def __init__(self):
        super().__init__()
        self.validation_service = SimulationValidationService()
        self.statistical_service = StatisticalService()
        self.chart_demand = ChartDemand()
        self.financial_analyzer = SimulationFinancialAnalyzer()
        self.chart_generator = ChartGenerator()
        self.data_parser = DataParser()
        self.math_engine = SimulationMathEngine()
    
    def get(self, request, simulation_id, *args, **kwargs):
        """Método principal GET optimizado"""
        
        logger.info(f"Procesando simulación ID: {simulation_id}")
        
        try:
            # 1. Validar y obtener simulación
            simulation_id = self._validate_simulation_id(simulation_id)
            if simulation_id is None:
                messages.error(request, "ID de simulación inválido.")
                return redirect('simulate:simulate.show')
            
            simulation_instance = self._get_simulation_with_relations(simulation_id)
            
            # 2. Verificar permisos
            if not self._user_can_view_simulation(request.user, simulation_instance):
                messages.error(request, "No tiene permisos para ver esta simulación.")
                return redirect('simulate:simulate.show')
            
            # 3. Obtener resultados
            results_simulation = self._get_simulation_results(simulation_id)
            if not results_simulation:
                messages.warning(request, "No se encontraron resultados para esta simulación.")
                return self._render_empty_results(request, simulation_instance, simulation_id)
            
            # 4. Extraer demanda histórica
            historical_demand = self._extract_historical_demand_safe(simulation_instance)
            
            # 5. Procesar variables y generar análisis
            context = self._build_complete_context(
                simulation_id, simulation_instance, results_simulation, historical_demand
            )
            
            logger.info("Contexto generado exitosamente")
            return render(request, 'simulate/result/simulate-result.html', context)
            
        except Exception as e:
            logger.error(f"Error crítico en SimulateResultView: {str(e)}")
            logger.exception("Traceback completo:")
            messages.error(request, f"Error al mostrar los resultados: {str(e)}")
            return redirect('simulate:simulate.show')
    
    def _validate_simulation_id(self, simulation_id):
        """Valida el ID de simulación"""
        try:
            sim_id = int(simulation_id)
            return sim_id if sim_id > 0 else None
        except (ValueError, TypeError):
            logger.error(f"ID de simulación inválido: {simulation_id}")
            return None
    
    def _get_simulation_with_relations(self, simulation_id):
        """Obtiene la simulación con todas las relaciones necesarias"""
        return get_object_or_404(
            Simulation.objects.select_related(
                'fk_questionary_result__fk_questionary__fk_product__fk_business',
                'fk_fdp'
            ).prefetch_related(
                'fk_questionary_result__fk_question_result_answer__fk_question'
            ),
            pk=simulation_id
        )
    
    def _user_can_view_simulation(self, user, simulation):
        """Verifica permisos del usuario"""
        try:
            business = simulation.fk_questionary_result.fk_questionary.fk_product.fk_business
            return business.fk_user == user
        except Exception as e:
            logger.error(f"Error verificando permisos: {str(e)}")
            return False
    
    def _get_simulation_results(self, simulation_id):
        """Obtiene y procesa los resultados de simulación"""
        try:
            results = ResultSimulation.objects.filter(
                fk_simulation_id=simulation_id,
                is_active=True
            ).order_by('date')
            
            if not results.exists():
                return []
            
            # Procesar variables JSON
            results_list = []
            for result in results:
                if hasattr(result, 'variables') and result.variables:
                    if isinstance(result.variables, str):
                        try:
                            result.variables = json.loads(result.variables)
                        except json.JSONDecodeError:
                            result.variables = {}
                    elif not isinstance(result.variables, dict):
                        result.variables = {}
                else:
                    result.variables = {}
                
                # Asegurar demand_mean
                if not hasattr(result, 'demand_mean') or result.demand_mean is None:
                    result.demand_mean = 0.0
                
                results_list.append(result)
            
            logger.info(f"Procesados {len(results_list)} resultados")
            return results_list
            
        except Exception as e:
            logger.error(f"Error obteniendo resultados: {str(e)}")
            return []
    
    def _extract_historical_demand_safe(self, simulation_instance):
        """Extrae demanda histórica de forma segura"""
        try:
            # Desde demand_history de la simulación
            if hasattr(simulation_instance, 'demand_history') and simulation_instance.demand_history:
                if isinstance(simulation_instance.demand_history, str):
                    try:
                        demand_data = json.loads(simulation_instance.demand_history)
                    except json.JSONDecodeError:
                        demand_data = None
                else:
                    demand_data = simulation_instance.demand_history
                
                if isinstance(demand_data, list) and demand_data:
                    historical_demand = []
                    for value in demand_data:
                        try:
                            float_val = float(value)
                            if float_val >= 0:
                                historical_demand.append(float_val)
                        except (ValueError, TypeError):
                            continue
                    
                    if historical_demand:
                        logger.info(f"Extraídos {len(historical_demand)} valores históricos")
                        return historical_demand
            
            # Desde respuestas del cuestionario
            try:
                answers = simulation_instance.fk_questionary_result.fk_question_result_answer.all()
                for answer in answers:
                    question_text = answer.fk_question.question.lower()
                    if 'históric' in question_text and 'demanda' in question_text:
                        if answer.answer:
                            parsed_data = self.data_parser.parse_demand_history(answer.answer)
                            if parsed_data:
                                logger.info(f"Extraídos {len(parsed_data)} valores del cuestionario")
                                return parsed_data
            except Exception as e:
                logger.warning(f"Error extrayendo desde cuestionario: {str(e)}")
            
            logger.warning("No se encontró demanda histórica")
            return []
            
        except Exception as e:
            logger.error(f"Error extrayendo demanda histórica: {str(e)}")
            return []
    
    def _build_complete_context(self, simulation_id, simulation_instance, results_simulation, historical_demand):
        """Construye el contexto completo para todos los templates"""
        
        try:
            # Extraer variables de todos los días
            all_variables_extracted = self._extract_all_variables_complete(results_simulation)
            
            # Calcular totales acumulativos
            totales_acumulativos = self._calculate_enhanced_totals(all_variables_extracted)
            
            # Generar todos los gráficos
            chart_images = self._generate_all_charts(
                simulation_id, simulation_instance, all_variables_extracted, historical_demand
            )
            
            # Análisis financiero
            financial_results = self._get_complete_financial_analysis(
                simulation_id, simulation_instance, totales_acumulativos
            )
            
            # Estadísticas de demanda
            demand_stats = self._calculate_complete_demand_statistics(
                historical_demand, results_simulation
            )
            
            # Validación del modelo
            validation_results = self._get_complete_validation_results(
                simulation_id, simulation_instance, results_simulation, historical_demand
            )
            
            # Gráficos endógenos
            endogenous_charts = self._generate_endogenous_charts(
                all_variables_extracted, totales_acumulativos
            )
            
            # Obtener instancias relacionadas
            product_instance = simulation_instance.fk_questionary_result.fk_questionary.fk_product
            business_instance = product_instance.fk_business
            
            # KPIs principales
            kpis = self._calculate_main_kpis(all_variables_extracted, totales_acumulativos)
            
            # Construir contexto completo
            context = {
                # Datos básicos
                'simulation_id': simulation_id,
                'simulation_instance': simulation_instance,
                'results_simulation': results_simulation,
                'results': results_simulation,  # Alias para compatibilidad
                'product_instance': product_instance,
                'business_instance': business_instance,
                
                # Variables y totales
                'all_variables_extracted': all_variables_extracted,
                'totales_acumulativos': totales_acumulativos,
                
                # Demanda
                'historical_demand': historical_demand,
                'demand_stats': demand_stats,
                
                # Gráficos principales
                'chart_images': chart_images,
                'image_data_simulation': chart_images.get('demand_comparison'),
                'image_data_ingresos_gastos': chart_images.get('financial_overview'),
                'image_data_eficiencia': chart_images.get('efficiency_chart'),
                'image_data_costos': chart_images.get('costs_analysis'),
                'image_data_rentabilidad': chart_images.get('profitability'),
                'image_data_roi': chart_images.get('roi_analysis'),
                'image_data_kpis': chart_images.get('kpis_overview'),
                'image_data_gastos': chart_images.get('expenses_breakdown'),
                'image_data_indicadores': chart_images.get('financial_indicators'),
                'image_data_proyecciones': chart_images.get('projections'),
                'image_data_tendencias': chart_images.get('trends'),
                'image_data_flujo_caja': chart_images.get('cash_flow'),
                'comparison_chart': chart_images.get('demand_comparison'),
                
                # Gráficos adicionales (para operations tab)
                'image_data_5': chart_images.get('operational_costs'),
                'image_data_6': chart_images.get('production_vs_sales'),
                'image_data_7': chart_images.get('average_costs'),
                
                # Gráficos de análisis estadístico
                'demand_boxplot': chart_images.get('demand_boxplot'),
                'scatter_plot': chart_images.get('scatter_plot'),
                
                # Métricas financieras
                'total_revenue': financial_results.get('total_revenue', 0),
                'total_profit': financial_results.get('total_profit', 0),
                'total_expenses': financial_results.get('total_expenses', 0),
                'average_margin': financial_results.get('average_margin', 0),
                'financial_recommendations': financial_results.get('financial_recommendations', []),
                'financial_recommendations_to_show': financial_results.get('financial_recommendations', []),
                
                # Métricas de error y validación
                'mape': validation_results.get('mape', 0),
                'mae': validation_results.get('mae', 0),
                'rmse': validation_results.get('rmse', 0),
                'r_squared': validation_results.get('r_squared', 0),
                'growth_rate': demand_stats.get('comparison', {}).get('mean_diff_pct', 0),
                'error_permisible': abs(demand_stats.get('comparison', {}).get('mean_diff_pct', 0)),
                
                # Validación
                'validation_results': validation_results,
                'validation_summary': validation_results.get('summary', {}),
                'validation_details': validation_results.get('details', []),
                'validation_totals': validation_results.get('totals', {}),
                'validation_metrics': validation_results.get('metrics', {}),
                'validation_recommendations': validation_results.get('recommendations', []),
                'validation_alerts': validation_results.get('alerts', []),
                'simulation_valid': validation_results.get('summary', {}).get('is_valid', False),
                
                # Validación del modelo
                'model_validation_summary': validation_results.get('model_validation', {}).get('summary', {}),
                'model_validation_by_variable': validation_results.get('model_validation', {}).get('by_variable', {}),
                'model_validation_recommendations': validation_results.get('model_validation', {}).get('recommendations', []),
                
                # Gráfico de tres líneas
                'has_three_line_chart': validation_results.get('has_three_line_chart', False),
                'three_line_validation_chart': validation_results.get('three_line_chart'),
                'three_line_validation_metrics': validation_results.get('three_line_metrics', {}),
                
                # Gráficos endógenos
                'endogenous_charts': endogenous_charts,
                'additional_charts': chart_images,
                
                # Estados y contadores
                'has_results': len(results_simulation) > 0,
                'results_count': len(results_simulation),
                
                # KPIs para dashboard
                'kpis': kpis,
                
                # Datos para charts interactivos
                'chart_data': self._prepare_chart_data(historical_demand, all_variables_extracted),
                
                # Comparación realista
                'realistic_comparison': self._calculate_realistic_comparison(
                    historical_demand, results_simulation
                ),
                
                # Análisis adicionales
                'additional_analisis_costos_detallado': chart_images.get('detailed_costs'),
                'additional_eficiencia_operativa': chart_images.get('operational_efficiency'),
            }
            
            # Log del contexto generado
            self._log_context_summary(context)
            
            return context
            
        except Exception as e:
            logger.error(f"Error construyendo contexto: {str(e)}")
            logger.exception("Traceback completo:")
            return self._create_minimal_context(simulation_id, simulation_instance, results_simulation)
    
    def _extract_all_variables_complete(self, results_simulation):
        """Extrae todas las variables de forma completa"""
        all_variables = []
        
        try:
            for day_idx, result in enumerate(results_simulation):
                day_data = {
                    'day': day_idx + 1,
                    'date': result.date.isoformat() if hasattr(result, 'date') and result.date else None,
                    'demand_mean': float(result.demand_mean) if hasattr(result, 'demand_mean') else 0.0,
                    'demand_std': float(result.demand_std_deviation) if hasattr(result, 'demand_std_deviation') else 0.0
                }
                
                # Procesar variables del resultado
                if hasattr(result, 'variables') and result.variables:
                    if isinstance(result.variables, dict):
                        for key, value in result.variables.items():
                            if not key.startswith('_'):
                                try:
                                    if isinstance(value, (int, float)):
                                        day_data[key] = float(value)
                                    elif isinstance(value, str) and value.replace('.', '').replace('-', '').isdigit():
                                        day_data[key] = float(value)
                                    else:
                                        day_data[key] = value
                                except (ValueError, TypeError):
                                    day_data[key] = 0.0
                
                # Calcular variables faltantes
                day_data = self._calculate_missing_variables(day_data)
                
                all_variables.append(day_data)
            
            logger.info(f"Variables extraídas para {len(all_variables)} días")
            return all_variables
            
        except Exception as e:
            logger.error(f"Error extrayendo variables: {str(e)}")
            return []
    
    def _calculate_missing_variables(self, day_data):
        """Calcula variables faltantes basándose en la demanda"""
        demand = day_data.get('demand_mean', 100)
        
        # Variables financieras básicas
        if 'PVP' not in day_data:
            day_data['PVP'] = 15.5  # Precio por defecto
        
        if 'IT' not in day_data:
            day_data['IT'] = demand * day_data.get('PVP', 15.5)
        
        if 'CVU' not in day_data:
            day_data['CVU'] = 8.5  # Costo variable unitario por defecto
        
        if 'CFD' not in day_data:
            day_data['CFD'] = 200  # Costo fijo diario por defecto
        
        if 'TG' not in day_data:
            day_data['TG'] = (demand * day_data.get('CVU', 8.5)) + day_data.get('CFD', 200)
        
        if 'GT' not in day_data:
            day_data['GT'] = day_data.get('IT', 0) - day_data.get('TG', 0)
        
        if 'NR' not in day_data:
            it = day_data.get('IT', 0)
            day_data['NR'] = (day_data.get('GT', 0) / it) if it > 0 else 0
        
        # Variables operativas
        if 'TPV' not in day_data:
            day_data['TPV'] = demand * 0.95  # 95% de la demanda se vende
        
        if 'NSC' not in day_data:
            day_data['NSC'] = 0.85  # 85% satisfacción del cliente
        
        if 'EOG' not in day_data:
            day_data['EOG'] = 0.80  # 80% eficiencia operativa
        
        if 'CPROD' not in day_data:
            day_data['CPROD'] = demand * 1.2  # 20% más de capacidad
        
        if 'NEPP' not in day_data:
            day_data['NEPP'] = max(1, int(demand / 100))  # 1 empleado por cada 100L
        
        if 'DPH' not in day_data:
            day_data['DPH'] = demand
        
        return day_data
    
    def _calculate_enhanced_totals(self, all_variables_extracted):
        """Calcula totales acumulativos mejorados"""
        enhanced_totales = {}
        
        try:
            # Variables para procesar
            variables_to_process = [
                'IT', 'GT', 'TG', 'TPV', 'NSC', 'EOG', 'PVP', 'CFD', 'CVU',
                'CPROD', 'NEPP', 'DPH', 'NR'
            ]
            
            for var_name in variables_to_process:
                values = []
                
                for day_data in all_variables_extracted:
                    if var_name in day_data and day_data[var_name] is not None:
                        try:
                            value = float(day_data[var_name])
                            values.append(value)
                        except (ValueError, TypeError):
                            continue
                
                if values:
                    total = sum(values)
                    mean = np.mean(values)
                    std = np.std(values)
                    
                    # Calcular tendencia
                    trend = self._calculate_trend(values)
                    
                    # Nombres descriptivos
                    descriptive_names = {
                        'IT': 'INGRESOS TOTALES',
                        'GT': 'GANANCIAS TOTALES',
                        'TG': 'GASTOS TOTALES',
                        'TPV': 'TOTAL PRODUCTOS VENDIDOS',
                        'NSC': 'SATISFACCIÓN DEL CLIENTE',
                        'EOG': 'EFICIENCIA OPERATIVA GENERAL',
                        'PVP': 'PRECIO DE VENTA AL PÚBLICO',
                        'CFD': 'COSTO FIJO DIARIO',
                        'CVU': 'COSTO VARIABLE UNITARIO',
                        'CPROD': 'CAPACIDAD DE PRODUCCIÓN',
                        'NEPP': 'NÚMERO DE EMPLEADOS EN PRODUCCIÓN',
                        'DPH': 'DEMANDA PROMEDIO HISTÓRICA',
                        'NR': 'NIVEL DE RENTABILIDAD'
                    }
                    
                    var_key = descriptive_names.get(var_name, var_name)
                    
                    enhanced_totales[var_key] = {
                        'total': total,
                        'average': mean,
                        'count': len(values),
                        'unit': self._get_variable_unit(var_name),
                        'trend': trend['direction'],
                        'min_value': min(values),
                        'max_value': max(values),
                        'std_deviation': std,
                        'cv': std / mean if mean != 0 else 0,
                        'trend_strength': trend.get('strength', 0),
                        'volatility': (std / mean * 100) if mean != 0 else 0
                    }
            
            logger.info(f"Totales calculados para {len(enhanced_totales)} variables")
            return enhanced_totales
            
        except Exception as e:
            logger.error(f"Error calculando totales: {str(e)}")
            return {}
    
    def _calculate_trend(self, values):
        """Calcula tendencia de una serie de valores"""
        try:
            if len(values) < 3:
                return {'direction': 'stable', 'strength': 0}
            
            x = np.arange(len(values))
            slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(x, values)
            
            threshold = 0.01 * np.mean(values)
            
            if slope > threshold:
                direction = 'increasing'
            elif slope < -threshold:
                direction = 'decreasing'
            else:
                direction = 'stable'
            
            strength = abs(r_value) * 100
            
            return {
                'direction': direction,
                'strength': strength,
                'slope': slope,
                'r_squared': r_value ** 2
            }
            
        except Exception as e:
            logger.error(f"Error calculando tendencia: {str(e)}")
            return {'direction': 'stable', 'strength': 0}
    
    def _get_variable_unit(self, var_name):
        """Obtiene la unidad de una variable"""
        units = {
            'IT': 'BS',
            'GT': 'BS',
            'TG': 'BS',
            'PVP': 'BS/L',
            'CFD': 'BS',
            'CVU': 'BS/L',
            'TPV': 'L',
            'CPROD': 'L',
            'DPH': 'L',
            'NSC': '%',
            'EOG': '%',
            'NR': '%',
            'NEPP': 'Personas'
        }
        return units.get(var_name, '')
    
    def _generate_all_charts(self, simulation_id, simulation_instance, all_variables_extracted, historical_demand):
        """Genera todos los gráficos necesarios"""
        chart_images = {}
        
        try:
            # Gráfico de comparación de demanda
            if historical_demand and all_variables_extracted:
                chart_images['demand_comparison'] = self._generate_demand_comparison_chart(
                    historical_demand, all_variables_extracted
                )
            
            # Gráfico financiero
            chart_images['financial_overview'] = self._generate_financial_chart(all_variables_extracted)
            
            # Gráfico de eficiencia
            chart_images['efficiency_chart'] = self._generate_efficiency_chart(all_variables_extracted)
            
            # Gráficos adicionales
            chart_images.update(self._generate_additional_charts(all_variables_extracted))
            
            logger.info(f"Generados {len(chart_images)} gráficos")
            return chart_images
            
        except Exception as e:
            logger.error(f"Error generando gráficos: {str(e)}")
            return {}
    
    def _generate_demand_comparison_chart(self, historical_demand, all_variables_extracted):
        """Genera gráfico de comparación de demanda"""
        try:
            simulated_demand = [d.get('demand_mean', 0) for d in all_variables_extracted]
            
            if not simulated_demand:
                return None
            
            return self.chart_demand.generate_demand_comparison_chart(
                historical_demand, simulated_demand
            )
            
        except Exception as e:
            logger.error(f"Error generando gráfico de demanda: {str(e)}")
            return None
    
    def _generate_financial_chart(self, all_variables_extracted):
        """Genera gráfico financiero"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            from io import BytesIO
            import base64
            
            days = [d.get('day', i+1) for i, d in enumerate(all_variables_extracted)]
            revenues = [d.get('IT', 0) for d in all_variables_extracted]
            profits = [d.get('GT', 0) for d in all_variables_extracted]
            
            if not any(revenues) and not any(profits):
                return None
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            ax.plot(days, revenues, 'b-', linewidth=2, label='Ingresos Totales', marker='o')
            ax.plot(days, profits, 'g-', linewidth=2, label='Ganancias Totales', marker='s')
            
            ax.set_xlabel('Día')
            ax.set_ylabel('Monto (Bs.)')
            ax.set_title('Evolución Financiera')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            return chart_base64
            
        except Exception as e:
            logger.error(f"Error generando gráfico financiero: {str(e)}")
            return None
    
    def _generate_efficiency_chart(self, all_variables_extracted):
        """Genera gráfico de eficiencia"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            from io import BytesIO
            import base64
            
            days = [d.get('day', i+1) for i, d in enumerate(all_variables_extracted)]
            efficiency = [d.get('EOG', 0.8) * 100 for d in all_variables_extracted]
            service_level = [d.get('NSC', 0.85) * 100 for d in all_variables_extracted]
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            ax.plot(days, efficiency, 'r-', linewidth=2, label='Eficiencia Operativa (%)', marker='o')
            ax.plot(days, service_level, 'b-', linewidth=2, label='Nivel de Servicio (%)', marker='s')
            
            ax.axhline(y=85, color='green', linestyle='--', alpha=0.5, label='Meta 85%')
            
            ax.set_xlabel('Día')
            ax.set_ylabel('Porcentaje (%)')
            ax.set_title('Indicadores de Eficiencia')
            ax.legend()
            ax.grid(True, alpha=0.3)
            ax.set_ylim(0, 100)
            
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            return chart_base64
            
        except Exception as e:
            logger.error(f"Error generando gráfico de eficiencia: {str(e)}")
            return None
    
    def _generate_additional_charts(self, all_variables_extracted):
        """Genera gráficos adicionales"""
        additional_charts = {}
        
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            from io import BytesIO
            import base64
            
            # Gráfico de costos
            additional_charts['costs_analysis'] = self._create_costs_chart(all_variables_extracted)
            
            # Gráfico de rentabilidad
            additional_charts['profitability'] = self._create_profitability_chart(all_variables_extracted)
            
            # Gráfico de ROI
            additional_charts['roi_analysis'] = self._create_roi_chart(all_variables_extracted)
            
            # Gráficos operativos
            additional_charts['operational_costs'] = self._create_operational_costs_chart(all_variables_extracted)
            additional_charts['production_vs_sales'] = self._create_production_sales_chart(all_variables_extracted)
            additional_charts['average_costs'] = self._create_average_costs_chart(all_variables_extracted)
            
            # Gráficos de análisis estadístico
            additional_charts['demand_boxplot'] = self._create_demand_boxplot(all_variables_extracted)
            additional_charts['scatter_plot'] = self._create_scatter_plot(all_variables_extracted)
            
            return additional_charts
            
        except Exception as e:
            logger.error(f"Error generando gráficos adicionales: {str(e)}")
            return {}
    
    def _create_costs_chart(self, all_variables_extracted):
        """Crea gráfico de análisis de costos"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            from io import BytesIO
            import base64
            
            days = [d.get('day', i+1) for i, d in enumerate(all_variables_extracted)]
            fixed_costs = [d.get('CFD', 200) for d in all_variables_extracted]
            variable_costs = [d.get('CVU', 8.5) * d.get('TPV', 100) for d in all_variables_extracted]
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            ax.bar(days, fixed_costs, label='Costos Fijos', alpha=0.7, color='orange')
            ax.bar(days, variable_costs, bottom=fixed_costs, label='Costos Variables', alpha=0.7, color='red')
            
            ax.set_xlabel('Día')
            ax.set_ylabel('Costos (Bs.)')
            ax.set_title('Estructura de Costos por Día')
            ax.legend()
            ax.grid(True, alpha=0.3, axis='y')
            
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            return chart_base64
            
        except Exception as e:
            logger.error(f"Error creando gráfico de costos: {str(e)}")
            return None
    
    def _create_profitability_chart(self, all_variables_extracted):
        """Crea gráfico de rentabilidad"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            from io import BytesIO
            import base64
            
            days = [d.get('day', i+1) for i, d in enumerate(all_variables_extracted)]
            margins = [d.get('NR', 0) * 100 for d in all_variables_extracted]
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            colors = ['green' if m > 15 else 'orange' if m > 5 else 'red' for m in margins]
            ax.bar(days, margins, color=colors, alpha=0.7)
            
            ax.axhline(y=15, color='green', linestyle='--', alpha=0.5, label='Meta 15%')
            ax.axhline(y=5, color='orange', linestyle='--', alpha=0.5, label='Mínimo 5%')
            
            ax.set_xlabel('Día')
            ax.set_ylabel('Margen de Rentabilidad (%)')
            ax.set_title('Evolución de la Rentabilidad')
            ax.legend()
            ax.grid(True, alpha=0.3, axis='y')
            
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            return chart_base64
            
        except Exception as e:
            logger.error(f"Error creando gráfico de rentabilidad: {str(e)}")
            return None
    
    def _create_roi_chart(self, all_variables_extracted):
        """Crea gráfico de ROI"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            from io import BytesIO
            import base64
            
            days = [d.get('day', i+1) for i, d in enumerate(all_variables_extracted)]
            roi_values = []
            
            for d in all_variables_extracted:
                profit = d.get('GT', 0)
                investment = d.get('TG', 1)
                roi = (profit / investment * 100) if investment > 0 else 0
                roi_values.append(roi)
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            ax.plot(days, roi_values, 'purple', linewidth=2, marker='o', label='ROI (%)')
            ax.axhline(y=0, color='red', linestyle='-', alpha=0.5, label='Punto de equilibrio')
            
            ax.set_xlabel('Día')
            ax.set_ylabel('ROI (%)')
            ax.set_title('Retorno sobre la Inversión (ROI)')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            return chart_base64
            
        except Exception as e:
            logger.error(f"Error creando gráfico de ROI: {str(e)}")
            return None
    
    def _create_operational_costs_chart(self, all_variables_extracted):
        """Crea gráfico de costos operativos"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            from io import BytesIO
            import base64
            
            days = [d.get('day', i+1) for i, d in enumerate(all_variables_extracted)]
            total_costs = [d.get('TG', 0) for d in all_variables_extracted]
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            ax.plot(days, total_costs, 'red', linewidth=2, marker='s', label='Costos Totales')
            
            # Promedio móvil
            if len(total_costs) >= 7:
                moving_avg = np.convolve(total_costs, np.ones(7)/7, mode='valid')
                moving_days = days[6:]
                ax.plot(moving_days, moving_avg, 'orange', linewidth=2, linestyle='--', label='Promedio Móvil (7 días)')
            
            ax.set_xlabel('Día')
            ax.set_ylabel('Costos (Bs.)')
            ax.set_title('Evolución de Costos Operativos')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            return chart_base64
            
        except Exception as e:
            logger.error(f"Error creando gráfico operativo: {str(e)}")
            return None
    
    def _create_production_sales_chart(self, all_variables_extracted):
        """Crea gráfico de producción vs ventas"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            from io import BytesIO
            import base64
            
            days = [d.get('day', i+1) for i, d in enumerate(all_variables_extracted)]
            production = [d.get('CPROD', 120) for d in all_variables_extracted]
            sales = [d.get('TPV', 100) for d in all_variables_extracted]
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            ax.bar([d - 0.2 for d in days], production, width=0.4, label='Capacidad de Producción', alpha=0.7, color='blue')
            ax.bar([d + 0.2 for d in days], sales, width=0.4, label='Productos Vendidos', alpha=0.7, color='green')
            
            ax.set_xlabel('Día')
            ax.set_ylabel('Cantidad (L)')
            ax.set_title('Producción vs Ventas')
            ax.legend()
            ax.grid(True, alpha=0.3, axis='y')
            
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            return chart_base64
            
        except Exception as e:
            logger.error(f"Error creando gráfico producción-ventas: {str(e)}")
            return None
    
    def _create_average_costs_chart(self, all_variables_extracted):
        """Crea gráfico de costos promedio"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            from io import BytesIO
            import base64
            
            days = [d.get('day', i+1) for i, d in enumerate(all_variables_extracted)]
            avg_costs = []
            
            for d in all_variables_extracted:
                total_cost = d.get('TG', 0)
                quantity = d.get('TPV', 1)
                avg_cost = total_cost / quantity if quantity > 0 else 0
                avg_costs.append(avg_cost)
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            ax.plot(days, avg_costs, 'brown', linewidth=2, marker='d', label='Costo Promedio por Unidad')
            
            if avg_costs:
                avg_line = np.mean(avg_costs)
                ax.axhline(y=avg_line, color='brown', linestyle='--', alpha=0.5, label=f'Promedio: {avg_line:.2f} Bs/L')
            
            ax.set_xlabel('Día')
            ax.set_ylabel('Costo por Unidad (Bs/L)')
            ax.set_title('Evolución del Costo Promedio por Unidad')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            return chart_base64
            
        except Exception as e:
            logger.error(f"Error creando gráfico de costos promedio: {str(e)}")
            return None
    
    def _create_demand_boxplot(self, all_variables_extracted):
        """Crea diagrama de cajas para análisis de demanda"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            from io import BytesIO
            import base64
            
            demands = [d.get('demand_mean', 0) for d in all_variables_extracted]
            
            if not demands:
                return None
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            bp = ax.boxplot([demands], labels=['Demanda Simulada'], patch_artist=True)
            bp['boxes'][0].set_facecolor('lightblue')
            bp['boxes'][0].set_alpha(0.7)
            
            ax.set_ylabel('Demanda (L)')
            ax.set_title('Distribución de la Demanda Simulada')
            ax.grid(True, alpha=0.3, axis='y')
            
            # Estadísticas
            stats_text = f'Media: {np.mean(demands):.2f}\nMediana: {np.median(demands):.2f}\nDesv. Est.: {np.std(demands):.2f}'
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            return chart_base64
            
        except Exception as e:
            logger.error(f"Error creando boxplot: {str(e)}")
            return None
    
    def _create_scatter_plot(self, all_variables_extracted):
        """Crea gráfico de dispersión para análisis de correlación"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            from io import BytesIO
            import base64
            
            demands = [d.get('demand_mean', 0) for d in all_variables_extracted]
            revenues = [d.get('IT', 0) for d in all_variables_extracted]
            
            if not demands or not revenues:
                return None
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            ax.scatter(demands, revenues, alpha=0.6, color='blue', s=50)
            
            # Línea de tendencia
            if len(demands) > 1:
                z = np.polyfit(demands, revenues, 1)
                p = np.poly1d(z)
                ax.plot(demands, p(demands), "r--", alpha=0.8, linewidth=2)
                
                # Coeficiente de correlación
                correlation = np.corrcoef(demands, revenues)[0, 1]
                ax.text(0.02, 0.98, f'Correlación: {correlation:.3f}', transform=ax.transAxes,
                       verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            
            ax.set_xlabel('Demanda (L)')
            ax.set_ylabel('Ingresos (Bs.)')
            ax.set_title('Correlación: Demanda vs Ingresos')
            ax.grid(True, alpha=0.3)
            
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            return chart_base64
            
        except Exception as e:
            logger.error(f"Error creando scatter plot: {str(e)}")
            return None
    
    def _get_complete_financial_analysis(self, simulation_id, simulation_instance, totales_acumulativos):
        """Obtiene análisis financiero completo"""
        try:
            total_revenue = totales_acumulativos.get('INGRESOS TOTALES', {}).get('total', 0)
            total_profit = totales_acumulativos.get('GANANCIAS TOTALES', {}).get('total', 0)
            total_expenses = totales_acumulativos.get('GASTOS TOTALES', {}).get('total', 0)
            
            # Calcular margen promedio
            average_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
            
            # Generar recomendaciones
            recommendations = []
            
            if average_margin < 10:
                recommendations.append({
                    'type': 'warning',
                    'title': 'Margen Bajo',
                    'message': 'El margen de ganancia es inferior al 10%. Considere revisar la estructura de costos.',
                    'priority': 'high'
                })
            elif average_margin > 25:
                recommendations.append({
                    'type': 'success',
                    'title': 'Excelente Rentabilidad',
                    'message': 'El margen de ganancia es superior al 25%. Mantener estrategia actual.',
                    'priority': 'low'
                })
            
            if total_expenses > total_revenue:
                recommendations.append({
                    'type': 'danger',
                    'title': 'Gastos Excesivos',
                    'message': 'Los gastos superan los ingresos. Requiere acción inmediata.',
                    'priority': 'high'
                })
            
            return {
                'total_revenue': total_revenue,
                'total_profit': total_profit,
                'total_expenses': total_expenses,
                'average_margin': average_margin,
                'financial_recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Error en análisis financiero: {str(e)}")
            return {
                'total_revenue': 0,
                'total_profit': 0,
                'total_expenses': 0,
                'average_margin': 0,
                'financial_recommendations': []
            }
    
    def _calculate_complete_demand_statistics(self, historical_demand, results_simulation):
        """Calcula estadísticas completas de demanda"""
        try:
            demand_stats = {
                'historical': {},
                'simulated': {},
                'comparison': {}
            }
            
            # Estadísticas históricas
            if historical_demand:
                hist_array = np.array(historical_demand)
                demand_stats['historical'] = {
                    'mean': float(np.mean(hist_array)),
                    'std': float(np.std(hist_array)),
                    'min': float(np.min(hist_array)),
                    'max': float(np.max(hist_array)),
                    'median': float(np.median(hist_array)),
                    'q25': float(np.percentile(hist_array, 25)),
                    'q75': float(np.percentile(hist_array, 75)),
                    'cv': float(np.std(hist_array) / np.mean(hist_array)) if np.mean(hist_array) > 0 else 0,
                    'count': len(historical_demand)
                }
            
            # Estadísticas simuladas
            simulated_demands = []
            for result in results_simulation:
                if hasattr(result, 'demand_mean') and result.demand_mean is not None:
                    simulated_demands.append(float(result.demand_mean))
            
            if simulated_demands:
                sim_array = np.array(simulated_demands)
                demand_stats['simulated'] = {
                    'mean': float(np.mean(sim_array)),
                    'std': float(np.std(sim_array)),
                    'min': float(np.min(sim_array)),
                    'max': float(np.max(sim_array)),
                    'median': float(np.median(sim_array)),
                    'q25': float(np.percentile(sim_array, 25)),
                    'q75': float(np.percentile(sim_array, 75)),
                    'cv': float(np.std(sim_array) / np.mean(sim_array)) if np.mean(sim_array) > 0 else 0,
                    'count': len(simulated_demands)
                }
                
                # Comparación
                if historical_demand:
                    hist_mean = demand_stats['historical']['mean']
                    sim_mean = demand_stats['simulated']['mean']
                    
                    # Calcular métricas de error
                    min_len = min(len(historical_demand), len(simulated_demands))
                    if min_len > 0:
                        hist_subset = historical_demand[:min_len]
                        sim_subset = simulated_demands[:min_len]
                        
                        mape = self._calculate_mape(hist_subset, sim_subset)
                        mae = np.mean(np.abs(np.array(hist_subset) - np.array(sim_subset)))
                        rmse = np.sqrt(np.mean((np.array(hist_subset) - np.array(sim_subset)) ** 2))
                        
                        # Correlación
                        correlation = np.corrcoef(hist_subset, sim_subset)[0, 1] if min_len > 1 else 0
                        
                        demand_stats['comparison'] = {
                            'mean_diff': sim_mean - hist_mean,
                            'mean_diff_pct': ((sim_mean - hist_mean) / hist_mean * 100) if hist_mean > 0 else 0,
                            'cv_diff': demand_stats['simulated']['cv'] - demand_stats['historical']['cv'],
                            'mape': mape,
                            'mae': mae,
                            'rmse': rmse,
                            'correlation': correlation if not np.isnan(correlation) else 0
                        }
            
            return demand_stats
            
        except Exception as e:
            logger.error(f"Error calculando estadísticas de demanda: {str(e)}")
            return {'historical': {}, 'simulated': {}, 'comparison': {}}
    
    def _calculate_mape(self, actual, predicted):
        """Calcula Mean Absolute Percentage Error"""
        try:
            actual = np.array(actual)
            predicted = np.array(predicted)
            
            # Evitar división por cero
            mask = actual != 0
            if not np.any(mask):
                return 100.0
            
            mape = np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100
            return float(mape)
            
        except Exception as e:
            logger.error(f"Error calculando MAPE: {str(e)}")
            return 100.0
    
    def _get_complete_validation_results(self, simulation_id, simulation_instance, results_simulation, historical_demand):
        """Obtiene resultados completos de validación"""
        try:
            validation_results = {}
            
            # Validación básica del modelo
            if historical_demand and results_simulation:
                simulated_demands = [float(r.demand_mean) for r in results_simulation if hasattr(r, 'demand_mean')]
                
                if simulated_demands:
                    min_len = min(len(historical_demand), len(simulated_demands))
                    if min_len > 0:
                        hist_subset = historical_demand[:min_len]
                        sim_subset = simulated_demands[:min_len]
                        
                        # Métricas de error
                        mape = self._calculate_mape(hist_subset, sim_subset)
                        mae = np.mean(np.abs(np.array(hist_subset) - np.array(sim_subset)))
                        rmse = np.sqrt(np.mean((np.array(hist_subset) - np.array(sim_subset)) ** 2))
                        
                        # R²
                        ss_res = np.sum((np.array(hist_subset) - np.array(sim_subset)) ** 2)
                        ss_tot = np.sum((np.array(hist_subset) - np.mean(hist_subset)) ** 2)
                        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
                        
                        validation_results['mape'] = mape
                        validation_results['mae'] = mae
                        validation_results['rmse'] = rmse
                        validation_results['r_squared'] = max(0, r_squared)
                        
                        # Resumen de validación
                        precise_count = sum(1 for i in range(min_len) 
                        if hist_subset[i] != 0 and abs(hist_subset[i] - sim_subset[i]) / hist_subset[i] < 0.1)

                        acceptable_count = sum(1 for i in range(min_len) 
                        if hist_subset[i] != 0 and 0.1 <= abs(hist_subset[i] - sim_subset[i]) / hist_subset[i] < 0.2)

                        inaccurate_count = min_len - precise_count - acceptable_count

                        
                        success_rate = (precise_count + acceptable_count) / min_len * 100 if min_len > 0 else 0
                        
                        validation_results['summary'] = {
                            'total_days': min_len,
                            'precise_count': precise_count,
                            'acceptable_count': acceptable_count,
                            'inaccurate_count': inaccurate_count,
                            'success_rate': success_rate,
                            'avg_mape': mape,
                            'is_valid': mape < 20 and success_rate > 60
                        }
                        
                        # Detalles por día
                        details = []
                        totals = {
                            'total_simulated': sum(sim_subset),
                            'total_real': sum(hist_subset),
                            'total_difference': sum(sim_subset) - sum(hist_subset),
                            'avg_error': mape
                        }
                        
                        for i in range(min_len):
                            real_val = hist_subset[i]
                            sim_val = sim_subset[i]
                            difference = sim_val - real_val
                            error_pct = abs(difference / real_val * 100) if real_val != 0 else 0
                            
                            if error_pct < 10:
                                verdict = 'PRECISA'
                            elif error_pct < 20:
                                verdict = 'ACEPTABLE'
                            else:
                                verdict = 'INEXACTA'
                            
                            details.append({
                                'day_number': i + 1,
                                'date': results_simulation[i].date if i < len(results_simulation) else None,
                                'product': simulation_instance.fk_questionary_result.fk_questionary.fk_product.name,
                                'business_name': simulation_instance.fk_questionary_result.fk_questionary.fk_product.fk_business.name,
                                'simulated_demand': sim_val,
                                'real_demand': real_val,
                                'difference': difference,
                                'error_percentage': error_pct,
                                'verdict': verdict
                            })
                        
                        validation_results['details'] = details
                        validation_results['totals'] = totals
                        validation_results['metrics'] = {
                            'mape': mape,
                            'mae': mae,
                            'rmse': rmse,
                            'r_squared': validation_results['r_squared']
                        }
                        
                        # Recomendaciones
                        recommendations = []
                        if mape < 10:
                            recommendations.append("El modelo muestra excelente precisión")
                        elif mape < 20:
                            recommendations.append("El modelo tiene precisión aceptable")
                        else:
                            recommendations.append("El modelo requiere calibración")
                        
                        if success_rate > 80:
                            recommendations.append("Alta confiabilidad en las predicciones")
                        elif success_rate > 60:
                            recommendations.append("Confiabilidad moderada")
                        else:
                            recommendations.append("Revisar parámetros del modelo")
                        
                        validation_results['recommendations'] = recommendations
                        
                        # Alertas
                        alerts = []
                        if mape > 30:
                            alerts.append({
                                'type': 'ERROR',
                                'message': f'Error muy alto: {mape:.1f}%',
                                'severity': 'HIGH'
                            })
                        elif mape > 20:
                            alerts.append({
                                'type': 'WARNING',
                                'message': f'Error elevado: {mape:.1f}%',
                                'severity': 'MEDIUM'
                            })
                        
                        validation_results['alerts'] = alerts
            
            # Gráfico de tres líneas (placeholder)
            validation_results['has_three_line_chart'] = False
            validation_results['three_line_chart'] = None
            validation_results['three_line_metrics'] = {}
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error en validación: {str(e)}")
            return {
                'summary': {'is_valid': False, 'success_rate': 0},
                'details': [],
                'metrics': {},
                'recommendations': [],
                'alerts': []
            }
    
    def _generate_endogenous_charts(self, all_variables_extracted, totales_acumulativos):
        """Genera gráficos de variables endógenas"""
        endogenous_charts = {}
        
        try:
            # Variables endógenas principales
            endogenous_vars = ['IT', 'GT', 'TG', 'TPV', 'NSC', 'EOG']
            
            for var in endogenous_vars:
                chart = self._create_endogenous_variable_chart(var, all_variables_extracted)
                if chart:
                    endogenous_charts[f'{var}_evolution'] = chart
            
            return endogenous_charts
            
        except Exception as e:
            logger.error(f"Error generando gráficos endógenos: {str(e)}")
            return {}
    
    def _create_endogenous_variable_chart(self, var_name, all_variables_extracted):
        """Crea gráfico para una variable endógena específica"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            from io import BytesIO
            import base64
            
            days = [d.get('day', i+1) for i, d in enumerate(all_variables_extracted)]
            values = [d.get(var_name, 0) for d in all_variables_extracted]
            
            if not any(values):
                return None
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Configurar según el tipo de variable
            if var_name in ['NSC', 'EOG', 'NR']:
                # Variables porcentuales
                values = [v * 100 if v <= 1 else v for v in values]
                ax.set_ylabel('Porcentaje (%)')
                ax.set_ylim(0, 100)
            elif var_name in ['IT', 'GT', 'TG']:
                # Variables monetarias
                ax.set_ylabel('Monto (Bs.)')
            else:
                # Variables de cantidad
                ax.set_ylabel('Cantidad (L)')
            
            ax.plot(days, values, linewidth=2, marker='o', markersize=4)
            
            # Títulos específicos
            titles = {
                'IT': 'Evolución de Ingresos Totales',
                'GT': 'Evolución de Ganancias Totales',
                'TG': 'Evolución de Gastos Totales',
                'TPV': 'Evolución de Productos Vendidos',
                'NSC': 'Evolución de Satisfacción del Cliente',
                'EOG': 'Evolución de Eficiencia Operativa'
            }
            
            ax.set_title(titles.get(var_name, f'Evolución de {var_name}'))
            ax.set_xlabel('Día')
            ax.grid(True, alpha=0.3)
            
            # Línea de tendencia
            if len(values) > 1:
                z = np.polyfit(days, values, 1)
                p = np.poly1d(z)
                ax.plot(days, p(days), "--", alpha=0.8, linewidth=1)
            
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            return chart_base64
            
        except Exception as e:
            logger.error(f"Error creando gráfico para {var_name}: {str(e)}")
            return None
    
    def _calculate_main_kpis(self, all_variables_extracted, totales_acumulativos):
        """Calcula KPIs principales"""
        try:
            if not all_variables_extracted:
                return {
                    'total_days': 0,
                    'avg_demand': 0,
                    'avg_sales': 0,
                    'avg_service_level': 0,
                    'avg_efficiency': 0,
                    'profit_margin': 0
                }
            
            demands = [d.get('demand_mean', 0) for d in all_variables_extracted]
            sales = [d.get('TPV', 0) for d in all_variables_extracted]
            service_levels = [d.get('NSC', 0.85) for d in all_variables_extracted]
            efficiencies = [d.get('EOG', 0.80) for d in all_variables_extracted]
            
            total_revenue = totales_acumulativos.get('INGRESOS TOTALES', {}).get('total', 0)
            total_profit = totales_acumulativos.get('GANANCIAS TOTALES', {}).get('total', 0)
            
            kpis = {
                'total_days': len(all_variables_extracted),
                'avg_demand': np.mean(demands) if demands else 0,
                'avg_sales': np.mean(sales) if sales else 0,
                'avg_service_level': np.mean(service_levels) * 100 if service_levels else 85,
                'avg_efficiency': np.mean(efficiencies) * 100 if efficiencies else 80,
                'profit_margin': (total_profit / total_revenue * 100) if total_revenue > 0 else 0,
                'total_revenue': total_revenue,
                'total_profit': total_profit
            }
            
            return kpis
            
        except Exception as e:
            logger.error(f"Error calculando KPIs: {str(e)}")
            return {
                'total_days': 0,
                'avg_demand': 0,
                'avg_sales': 0,
                'avg_service_level': 0,
                'avg_efficiency': 0,
                'profit_margin': 0
            }
    
    def _prepare_chart_data(self, historical_demand, all_variables_extracted):
        """Prepara datos para gráficos interactivos"""
        try:
            chart_data = {
                'historical_demand': historical_demand if historical_demand else [],
                'labels': [d.get('day', i+1) for i, d in enumerate(all_variables_extracted)],
                'datasets': [
                    {
                        'label': 'Demanda Simulada',
                        'values': [d.get('demand_mean', 0) for d in all_variables_extracted]
                    }
                ],
                'x_label': 'Días',
                'y_label': 'Demanda (Litros)'
            }
            return chart_data
        except Exception as e:
            logger.error(f"Error preparando datos de gráfico: {str(e)}")
            return {'historical_demand': [], 'labels': [], 'datasets': []}
    
    def _calculate_realistic_comparison(self, historical_demand, results_simulation):
        """Calcula comparación realista"""
        try:
            if not historical_demand or not results_simulation:
                return None
            
            hist_mean = np.mean(historical_demand)
            sim_demands = [float(r.demand_mean) for r in results_simulation if hasattr(r, 'demand_mean')]
            sim_mean = np.mean(sim_demands) if sim_demands else 0
            
            growth_rate = ((sim_mean - hist_mean) / hist_mean * 100) if hist_mean > 0 else 0
            is_realistic = abs(growth_rate) < 50
            
            return {
                'historical_mean': hist_mean,
                'simulated_mean': sim_mean,
                'growth_rate': growth_rate,
                'is_realistic': is_realistic,
                'deviation_percentage': abs(growth_rate)
            }
        except Exception as e:
            logger.error(f"Error calculando comparación realista: {str(e)}")
            return None
    
    def _render_empty_results(self, request, simulation_instance, simulation_id):
        """Renderiza página con resultados vacíos"""
        context = {
            'simulation_instance': simulation_instance,
            'simulation_id': simulation_id,
            'error': 'No hay resultados disponibles',
            'results_simulation': [],
            'has_results': False,
            'results_count': 0,
            'total_revenue': 0,
            'total_profit': 0,
            'average_margin': 0,
            'chart_images': {},
            'financial_recommendations': [],
            'validation_alerts': [],
            'totales_acumulativos': {},
            'all_variables_extracted': [],
            'historical_demand': [],
            'demand_stats': {},
            'kpis': {
                'total_days': 0,
                'avg_demand': 0,
                'avg_sales': 0,
                'avg_service_level': 0,
                'avg_efficiency': 0,
                'profit_margin': 0
            }
        }
        return render(request, 'simulate/result/simulate-result.html', context)
    
    def _create_minimal_context(self, simulation_id, simulation_instance, results_simulation):
        """Crea contexto mínimo en caso de error"""
        return {
            'simulation_id': simulation_id,
            'simulation_instance': simulation_instance,
            'results_simulation': results_simulation or [],
            'product_instance': getattr(simulation_instance.fk_questionary_result.fk_questionary, 'fk_product', None),
            'business_instance': None,
            'error': 'Error al procesar los datos de simulación',
            'has_results': len(results_simulation) > 0 if results_simulation else False,
            'results_count': len(results_simulation) if results_simulation else 0,
            'total_revenue': 0,
            'total_profit': 0,
            'average_margin': 0,
            'growth_rate': 0.0,
            'error_permisible': 0.0,
            'chart_images': {},
            'financial_recommendations': [],
            'validation_alerts': [],
            'totales_acumulativos': {},
            'all_variables_extracted': [],
            'historical_demand': [],
            'demand_stats': {},
            'validation_results': {'summary': {'is_valid': False}},
            'simulation_valid': False,
            'kpis': {
                'total_days': 0,
                'avg_demand': 0,
                'avg_sales': 0,
                'avg_service_level': 0,
                'avg_efficiency': 0,
                'profit_margin': 0
            },
            'endogenous_charts': {},
            'has_three_line_chart': False,
            'mape': 0,
            'mae': 0,
            'rmse': 0,
            'r_squared': 0
        }
    
    def _log_context_summary(self, context):
        """Log resumen del contexto generado"""
        try:
            logger.info("=== RESUMEN DEL CONTEXTO GENERADO ===")
            logger.info(f"Simulation ID: {context.get('simulation_id')}")
            logger.info(f"Resultados: {context.get('results_count', 0)}")
            logger.info(f"Variables extraídas: {len(context.get('all_variables_extracted', []))}")
            logger.info(f"Gráficos generados: {len(context.get('chart_images', {}))}")
            logger.info(f"Ingresos totales: {context.get('total_revenue', 0)}")
            logger.info(f"Ganancia total: {context.get('total_profit', 0)}")
            logger.info(f"Margen promedio: {context.get('average_margin', 0):.2f}%")
            logger.info(f"MAPE: {context.get('mape', 0):.2f}%")
            logger.info(f"Demanda histórica: {len(context.get('historical_demand', []))} puntos")
            logger.info("=== FIN RESUMEN ===")
        except Exception as e:
            logger.error(f"Error logging contexto: {str(e)}")


def simulate_result_simulation_view(request, simulation_id):
    """Vista basada en función para compatibilidad"""
    view = SimulateResultView.as_view()
    return view(request, simulation_id=simulation_id)