from django.views.generic import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ..models import Simulation, ResultSimulation
from ..services.simulation_service import SimulationService
from ..utils.chart_generators import ChartGenerator
from finance.models import FinanceRecommendation, FinanceRecommendationSimulation


import numpy as np
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.db.models import Prefetch, Q, Count, Avg, Sum, Exists, OuterRef
from django.http import HttpResponseRedirect, HttpResponseNotFound, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView, View

from ..forms import SimulationForm
from ..models import Simulation, ResultSimulation, Demand
from ..services.simulation_service import SimulationService
from ..services.statistical_service import StatisticalService
from ..utils.chart_generators import ChartGenerator
from ..validators.simulation_validators import SimulationValidator

from business.models import Business
from finance.models import FinanceRecommendation, FinanceRecommendationSimulation
from product.models import Product, Area
from questionary.models import QuestionaryResult, Questionary, Answer, Question
from variable.models import Variable, Equation, EquationResult

import json
import logging

logger = logging.getLogger(__name__)

class SimulateResultView(LoginRequiredMixin, View):
    """Display simulation results with complete analysis and visualization"""
    
    def get(self, request, simulation_id, *args, **kwargs):
        """Display simulation results with enhanced visualization"""
        try:
            # Get simulation with optimized queries
            simulation_instance = get_object_or_404(
                Simulation.objects.select_related(
                    'fk_questionary_result__fk_questionary__fk_product__fk_business',
                    'fk_fdp'
                ).prefetch_related(
                    'fk_questionary_result__fk_question_result_answer__fk_question'
                ),
                pk=simulation_id
            )
            
            # Check permissions
            if not self._user_can_view_simulation(request.user, simulation_instance):
                messages.error(request, "No tiene permisos para ver esta simulación.")
                return redirect('simulate:simulate.show')
            
            # Get results with pagination
            results_simulation = self._get_paginated_results(request, simulation_id)
            
            # Get historical demand data
            historical_demand = self._get_historical_demand(simulation_instance)
            
            # Generate comprehensive analysis
            context = self._prepare_complete_results_context(
                simulation_id, simulation_instance, results_simulation, historical_demand
            )
            
            return render(request, 'simulate/simulate-result.html', context)
            
        except Exception as e:
            logger.error(f"Error displaying results: {str(e)}")
            messages.error(request, "Error al mostrar los resultados.")
            return redirect('simulate:simulate.show')
    
    def _get_historical_demand(self, simulation_instance):
        """Extract historical demand data from questionary results"""
        try:
            # Get from simulation demand_history first
            if simulation_instance.demand_history:
                if isinstance(simulation_instance.demand_history, str):
                    try:
                        return json.loads(simulation_instance.demand_history)
                    except:
                        pass
                elif isinstance(simulation_instance.demand_history, list):
                    return simulation_instance.demand_history
            
            # Get from questionary answers
            for answer in simulation_instance.fk_questionary_result.fk_question_result_answer.all():
                if answer.fk_question.question == 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).':
                    if answer.answer:
                        try:
                            # Try JSON parse
                            return json.loads(answer.answer)
                        except:
                            # Try other parsing methods
                            demand_str = answer.answer.strip()
                            demand_str = demand_str.replace('[', '').replace(']', '')
                            if ',' in demand_str:
                                return [float(x.strip()) for x in demand_str.split(',') if x.strip()]
                            elif ' ' in demand_str:
                                return [float(x) for x in demand_str.split() if x]
                            elif '\n' in demand_str:
                                return [float(x.strip()) for x in demand_str.split('\n') if x.strip()]
            
            return []
        except Exception as e:
            logger.error(f"Error extracting historical demand: {str(e)}")
            return []
    
    def _prepare_complete_results_context(self, simulation_id, simulation_instance, 
                                        results_simulation, historical_demand):
        """Prepare comprehensive context data for results view"""
        # Generate all charts with historical comparison
        chart_generator = ChartGenerator()
        
        # Create enhanced chart data with historical demand
        chart_data = self._create_enhanced_chart_data(
            list(results_simulation), historical_demand
        )
        
        # Generate main analysis charts
        analysis_data = chart_generator.generate_all_charts(
            simulation_id, simulation_instance, list(results_simulation)
        )
        
        # Generate comparison chart: Historical vs Simulated
        comparison_chart = self._generate_demand_comparison_chart(
            historical_demand, list(results_simulation)
        )
        
        # Get financial analysis and recommendations
        simulation_service = SimulationService()
        financial_results = simulation_service.analyze_financial_results(
            simulation_id, analysis_data['totales_acumulativos']
        )
        
        # Generate dynamic recommendations based on results
        recommendations = self._generate_dynamic_recommendations(
            simulation_instance, analysis_data['totales_acumulativos'], 
            financial_results
        )
        
        # Calculate comprehensive statistics
        demand_stats = self._calculate_comprehensive_statistics(
            historical_demand, results_simulation
        )
        
        # Get related instances
        product_instance = simulation_instance.fk_questionary_result.fk_questionary.fk_product
        business_instance = product_instance.fk_business
        
        # Prepare complete context
        context = {
            'simulation_instance': simulation_instance,
            'results_simulation': results_simulation,
            'results': results_simulation,
            'product_instance': product_instance,
            'business_instance': business_instance,
            'all_variables_extracted': analysis_data['all_variables_extracted'],
            'totales_acumulativos': analysis_data['totales_acumulativos'],
            'historical_demand': historical_demand,
            'demand_stats': demand_stats,
            'comparison_chart': comparison_chart,
            'financial_recommendations': recommendations,
            **analysis_data['chart_images'],
            **financial_results,
        }
        
        return context
    
    def _create_enhanced_chart_data(self, results_simulation, historical_demand):
        """Create enhanced chart data including historical demand"""
        chart_data = {
            'historical_demand': historical_demand,
            'labels': list(range(1, len(results_simulation) + 1)),
            'datasets': [
                {
                    'label': 'Demanda Simulada',
                    'values': [float(r.demand_mean) for r in results_simulation]
                }
            ],
            'x_label': 'Días',
            'y_label': 'Demanda (Litros)'
        }
        
        return chart_data
    
    def _generate_demand_comparison_chart(self, historical_demand, results_simulation):
        """Generate comparison chart between historical and simulated demand"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Plot historical demand
            if historical_demand:
                hist_labels = list(range(1, len(historical_demand) + 1))
                ax.plot(hist_labels, historical_demand, 'b-', marker='s', 
                       label='Demanda Histórica', linewidth=2, markersize=6)
                
                # Add historical mean line
                hist_mean = np.mean(historical_demand)
                ax.axhline(y=hist_mean, color='blue', linestyle=':', alpha=0.5,
                         label=f'Media Histórica: {hist_mean:.2f}')
            
            # Plot simulated demand
            simulated_values = [float(r.demand_mean) for r in results_simulation]
            sim_labels = list(range(len(historical_demand) + 1, 
                                  len(historical_demand) + len(simulated_values) + 1))
            ax.plot(sim_labels, simulated_values, 'r-', marker='o',
                   label='Demanda Simulada', linewidth=2, markersize=6)
            
            # Add simulated mean line
            sim_mean = np.mean(simulated_values)
            ax.axhline(y=sim_mean, color='red', linestyle=':', alpha=0.5,
                     label=f'Media Simulada: {sim_mean:.2f}')
            
            # Add vertical separator
            if historical_demand:
                ax.axvline(x=len(historical_demand), color='gray', 
                         linestyle='--', alpha=0.5, label='Inicio Simulación')
            
            # Configure plot
            ax.set_xlabel('Período de Tiempo', fontsize=12)
            ax.set_ylabel('Demanda (Litros)', fontsize=12)
            ax.set_title('Comparación: Demanda Histórica vs Simulada', 
                        fontsize=14, fontweight='bold')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Convert to base64
            from io import BytesIO
            import base64
            
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
            buffer.close()
            plt.close(fig)
            
            return image_data
            
        except Exception as e:
            logger.error(f"Error generating comparison chart: {str(e)}")
            return None
    
    def _calculate_comprehensive_statistics(self, historical_demand, results_simulation):
        """Calculate comprehensive statistics for analysis"""
        stats = {
            'historical': {},
            'simulated': {},
            'comparison': {},
            'forecast_accuracy': {}
        }
        
        # Historical statistics
        if historical_demand:
            historical_array = np.array(historical_demand)
            stats['historical'] = {
                'mean': np.mean(historical_array),
                'std': np.std(historical_array),
                'min': np.min(historical_array),
                'max': np.max(historical_array),
                'median': np.median(historical_array),
                'cv': np.std(historical_array) / np.mean(historical_array) if np.mean(historical_array) > 0 else 0,
                'trend': self._calculate_trend(historical_array)
            }
        
        # Simulated statistics
        try:
            simulated_values = [float(r.demand_mean) for r in results_simulation]
        except (AttributeError, ValueError, TypeError) as e:
            logger.error(f"Error extracting simulated values: {str(e)}")
            simulated_values = []
        
        if simulated_values:
            simulated_array = np.array(simulated_values)
            stats['simulated'] = {
                'mean': np.mean(simulated_array),
                'std': np.std(simulated_array),
                'min': np.min(simulated_array),
                'max': np.max(simulated_array),
                'median': np.median(simulated_array),
                'cv': np.std(simulated_array) / np.mean(simulated_array) if np.mean(simulated_array) > 0 else 0,
                'trend': self._calculate_trend(simulated_array)
            }
            
            # Comparison metrics
            if historical_demand and stats['historical']:
                stats['comparison'] = {
                    'mean_diff': stats['simulated']['mean'] - stats['historical']['mean'],
                    'mean_diff_pct': ((stats['simulated']['mean'] - stats['historical']['mean']) / 
                                    stats['historical']['mean'] * 100) if stats['historical']['mean'] > 0 else 0,
                    'std_diff': stats['simulated']['std'] - stats['historical']['std'],
                    'cv_diff': stats['simulated']['cv'] - stats['historical']['cv'],
                    'trend_change': stats['simulated']['trend'] - stats['historical']['trend']
                }
                
                # Forecast accuracy metrics - only calculate if we have both datasets
                try:
                    stats['forecast_accuracy'] = {
                        'mape': self._calculate_mape(historical_demand, simulated_values),
                        'rmse': self._calculate_rmse(historical_demand, simulated_values),
                        'mae': self._calculate_mae(historical_demand, simulated_values)
                    }
                except Exception as e:
                    logger.error(f"Error calculating forecast accuracy: {str(e)}")
                    stats['forecast_accuracy'] = {
                        'mape': 0,
                        'rmse': 0,
                        'mae': 0
                    }
        
        return stats
    
    def _calculate_trend(self, data):
        """Calculate trend slope"""
        try:
            data_array = np.array(data)
            if len(data_array) < 2:
                return 0
            x = np.arange(len(data_array))
            z = np.polyfit(x, data_array, 1)
            return float(z[0])
        except (ValueError, TypeError) as e:
            logger.error(f"Error calculating trend: {str(e)}")
            return 0
    
    def _calculate_mape(self, actual, predicted):
        """Calculate Mean Absolute Percentage Error"""
        if len(actual) == 0 or len(predicted) == 0:
            return 0
        
        # Convert to numpy arrays
        actual = np.array(actual)
        predicted = np.array(predicted)
        
        # Ensure same length
        n = min(len(actual), len(predicted))
        actual = actual[:n]
        predicted = predicted[:n]
        
        # Avoid division by zero
        mask = actual != 0
        if not np.any(mask):
            return 0
        
        return np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100
    
    def _calculate_rmse(self, actual, predicted):
        """Calculate Root Mean Square Error"""
        if len(actual) == 0 or len(predicted) == 0:
            return 0
        
        # Convert to numpy arrays
        actual = np.array(actual)
        predicted = np.array(predicted)
        
        # Ensure same length
        n = min(len(actual), len(predicted))
        actual = actual[:n]
        predicted = predicted[:n]
        
        return np.sqrt(np.mean((actual - predicted) ** 2))
    
    def _calculate_mae(self, actual, predicted):
        """Calculate Mean Absolute Error"""
        if len(actual) == 0 or len(predicted) == 0:
            return 0
        
        # Convert to numpy arrays
        actual = np.array(actual)
        predicted = np.array(predicted)
        
        # Ensure same length
        n = min(len(actual), len(predicted))
        actual = actual[:n]
        predicted = predicted[:n]
        
        return np.mean(np.abs(actual - predicted))
    
    def _generate_dynamic_recommendations(self, simulation_instance, 
                                        totales_acumulativos, financial_results):
        """Generate dynamic recommendations based on simulation results"""
        recommendations = []
        business = simulation_instance.fk_questionary_result.fk_questionary.fk_product.fk_business
        
        # Get finance recommendations from database
        db_recommendations = FinanceRecommendation.objects.filter(
            fk_business=business,
            is_active=True
        ).order_by('threshold_value')
        
        # Check each recommendation against results
        for rec in db_recommendations:
            if rec.variable_name in totales_acumulativos:
                value = totales_acumulativos[rec.variable_name]['total']
                threshold = float(rec.threshold_value) if rec.threshold_value else 0
                
                if value > threshold:
                    severity = ((value - threshold) / threshold * 100) if threshold > 0 else 100
                    
                    recommendations.append({
                        'name': rec.name,
                        'description': rec.description or rec.recommendation,
                        'recommendation': rec.recommendation,
                        'severity': min(100, severity),
                        'value': value,
                        'threshold': threshold,
                        'variable': rec.variable_name,
                        'priority': 'high' if severity > 50 else 'medium' if severity > 20 else 'low'
                    })
        
        # Add dynamic recommendations based on analysis
        if 'insights' in financial_results:
            insights = financial_results['insights']
            
            # Efficiency recommendations
            if insights.get('efficiency_score', 0) < 20:
                recommendations.append({
                    'name': 'Eficiencia Operativa Baja',
                    'description': 'La eficiencia operativa está por debajo del umbral óptimo',
                    'recommendation': 'Revisar procesos operativos y optimizar costos para mejorar la eficiencia',
                    'severity': 80,
                    'priority': 'high',
                    'variable': 'EFICIENCIA'
                })
            
            # Profitability recommendations
            if insights.get('profitability_index', 0) < 1.2:
                recommendations.append({
                    'name': 'Índice de Rentabilidad Bajo',
                    'description': 'El índice de rentabilidad está por debajo del nivel recomendado',
                    'recommendation': 'Considerar estrategias para aumentar ingresos o reducir gastos',
                    'severity': 60,
                    'priority': 'medium',
                    'variable': 'RENTABILIDAD'
                })
            
            # Risk level recommendations
            if insights.get('risk_level') == 'high':
                recommendations.append({
                    'name': 'Nivel de Riesgo Alto',
                    'description': 'Se detectó un nivel de riesgo elevado en las operaciones',
                    'recommendation': 'Implementar medidas de mitigación de riesgos y diversificación',
                    'severity': 90,
                    'priority': 'high',
                    'variable': 'RIESGO'
                })
        
        # Growth rate recommendations
        if 'growth_rate' in financial_results:
            growth = financial_results['growth_rate']
            if growth < 0:
                recommendations.append({
                    'name': 'Decrecimiento Detectado',
                    'description': f'La demanda muestra una tendencia negativa del {abs(growth):.2f}%',
                    'recommendation': 'Implementar estrategias de marketing y revisar competitividad',
                    'severity': 70,
                    'priority': 'high',
                    'variable': 'CRECIMIENTO'
                })
            elif growth > 50:
                recommendations.append({
                    'name': 'Crecimiento Acelerado',
                    'description': f'La demanda muestra un crecimiento del {growth:.2f}%',
                    'recommendation': 'Preparar infraestructura para manejar el aumento de demanda',
                    'severity': 40,
                    'priority': 'medium',
                    'variable': 'CRECIMIENTO'
                })
        
        # Sort by priority and severity
        recommendations.sort(key=lambda x: (
            {'high': 0, 'medium': 1, 'low': 2}.get(x.get('priority', 'low'), 3),
            -x.get('severity', 0)
        ))
        
        # Save recommendations to database
        if recommendations:
            self._save_recommendations_to_db(simulation_instance, recommendations[:10])
        
        return recommendations[:10]  # Return top 10 recommendations
    
    def _save_recommendations_to_db(self, simulation_instance, recommendations):
        """Save generated recommendations to database"""
        try:
            finance_recs_to_save = []
            
            for rec in recommendations:
                if 'value' in rec and 'threshold' in rec:
                    # Find matching FinanceRecommendation
                    db_rec = FinanceRecommendation.objects.filter(
                        fk_business=simulation_instance.fk_questionary_result.fk_questionary.fk_product.fk_business,
                        variable_name=rec.get('variable', ''),
                        is_active=True
                    ).first()
                    
                    if db_rec:
                        finance_recs_to_save.append(
                            FinanceRecommendationSimulation(
                                data=rec['value'],
                                fk_simulation=simulation_instance,
                                # data=db_rec
                            )
                        )
            
            if finance_recs_to_save:
                FinanceRecommendationSimulation.objects.bulk_create(
                    finance_recs_to_save, ignore_conflicts=True
                )
        except Exception as e:
            logger.error(f"Error saving recommendations: {str(e)}")
    
    def _user_can_view_simulation(self, user, simulation_instance):
        """Check if user has permission to view simulation"""
        business = simulation_instance.fk_questionary_result.fk_questionary.fk_product.fk_business
        return business.fk_user == user
    
    def _get_paginated_results(self, request, simulation_id):
        """Get paginated simulation results"""
        page = request.GET.get('page', 1)
        per_page = 50
        
        results = ResultSimulation.objects.filter(
            is_active=True,
            fk_simulation_id=simulation_id
        ).order_by('date')
        
        paginator = Paginator(results, per_page)
        
        try:
            results_page = paginator.page(page)
        except PageNotAnInteger:
            results_page = paginator.page(1)
        except EmptyPage:
            results_page = paginator.page(paginator.num_pages)
        
        return results_page



def simulate_result_simulation_view(request, simulation_id):
    view = SimulateResultView.as_view()
    return view(request, simulation_id=simulation_id)