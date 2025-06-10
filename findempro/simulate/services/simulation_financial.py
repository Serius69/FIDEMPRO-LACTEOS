# simulation_financial.py
import logging
from typing import Dict, Any, List
from ..models import Simulation, ResultSimulation
from finance.models import FinanceRecommendation, FinanceRecommendationSimulation
from business.models import Business

logger = logging.getLogger(__name__)

class SimulationFinancial:
    def analyze_financial_results(self, simulation_id: int, totales_acumulativos: Dict[str, Dict]) -> Dict[str, Any]:
        """Analyze financial results with enhanced insights"""
        try:
            simulation = Simulation.objects.select_related(
                'fk_questionary_result__fk_questionary__fk_product__fk_business'
            ).get(id=simulation_id)
            
            business_instance = simulation.fk_questionary_result.fk_questionary.fk_product.fk_business
            
            results = ResultSimulation.objects.filter(
                fk_simulation_id=simulation_id,
                is_active=True
            ).order_by('date')
            
            if results.exists():
                first_result = results.first()
                last_result = results.last()
                initial_demand = float(first_result.demand_mean)
                predicted_demand = float(last_result.demand_mean)
            else:
                demand_stats = simulation.get_demand_statistics()
                initial_demand = demand_stats['mean']
                predicted_demand = demand_stats['mean']
            
            growth_rate = self._calculate_growth_rate(initial_demand, predicted_demand)
            error_permisible = self._calculate_error(initial_demand, predicted_demand)
            
            recommendations = []
            try:
                recommendations = self._generate_financial_recommendations_optimized(
                    business_instance, totales_acumulativos, simulation
                )
            except Exception as e:
                logger.warning(f"Could not generate recommendations: {str(e)}")
            
            insights = self._calculate_additional_insights(
                totales_acumulativos, growth_rate, error_permisible
            )
            
            class DemandData:
                def __init__(self, quantity):
                    self.quantity = quantity
            
            return {
                'demand_initial': DemandData(initial_demand),
                'demand_predicted': DemandData(predicted_demand),
                'growth_rate': growth_rate,
                'error_permisible': error_permisible,
                # 'financial_recommendations_to_show': recommendations,
                # 'insights': insights,
                'has_results': results.exists(),
                'results_count': results.count(),
            }
            
        except Simulation.DoesNotExist:
            logger.error(f"Simulation {simulation_id} not found")
            raise
        except Exception as e:
            logger.error(f"Error analyzing financial results: {str(e)}")
            return {
                'demand_initial': type('obj', (object,), {'quantity': 0})(),
                'demand_predicted': type('obj', (object,), {'quantity': 0})(),
                'growth_rate': 0,
                'error_permisible': 0,
                'financial_recommendations_to_show': [],
                'insights': {
                    'efficiency_score': 0,
                    'profitability_index': 0,
                    'risk_level': 'unknown',
                    'opportunities': []
                },
                'has_results': False,
                'results_count': 0,
            }

    def _calculate_growth_rate(self, initial: float, predicted: float) -> float:
        """Calculate growth rate with safety checks"""
        if initial == 0:
            return 0.0
        growth = ((predicted / initial) - 1) * 100
        return round(abs(growth), 2)

    def _calculate_error(self, initial: float, predicted: float) -> float:
        """Calculate permissible error"""
        if initial == 0:
            return 0.0
        error = abs((initial - predicted) / initial) * 100
        return round(error, 2)

    def _generate_financial_recommendations_optimized(self, business_instance: Business, totales_acumulativos: Dict[str, Dict], simulation_instance: Simulation) -> List[Dict[str, Any]]:
        """Generate financial recommendations with batch processing"""
        recommendations = FinanceRecommendation.objects.filter(
            is_active=True,
            fk_business=business_instance
        ).select_related('fk_business')
        
        recommendations_to_show = []
        recommendations_to_save = []
        
        for recommendation in recommendations:
            variable_name = recommendation.variable_name
            
            if variable_name in totales_acumulativos:
                variable_value = totales_acumulativos[variable_name]['total']
                threshold_value = recommendation.threshold_value
                
                if threshold_value and variable_value > threshold_value:
                    recommendations_to_show.append({
                        'name': recommendation.name,
                        'recommendation': recommendation.recommendation,
                        'variable_name': variable_name,
                        'severity': self._calculate_severity(variable_value, threshold_value)
                    })
                    
                    recommendations_to_save.append(
                        FinanceRecommendationSimulation(
                            data=variable_value,
                            fk_simulation=simulation_instance,
                        )
                    )
        
        if recommendations_to_save:
            FinanceRecommendationSimulation.objects.bulk_create(recommendations_to_save)
        
        recommendations_to_show.sort(key=lambda x: x['severity'], reverse=True)
        
        return recommendations_to_show

    def _calculate_severity(self, value: float, threshold: float) -> float:
        if threshold == 0:
            return 0.0
        value = float(value)
        threshold = float(threshold)
        excess_percentage = ((value - threshold) / threshold) * 100
        return min(100, excess_percentage)

    def _calculate_additional_insights(self, totales_acumulativos: Dict[str, Dict], growth_rate: float, error_permisible: float) -> Dict[str, Any]:
        """Calculate additional business insights"""
        insights = {
            'efficiency_score': 0,
            'profitability_index': 0,
            'risk_level': 'low',
            'opportunities': []
        }
        
        if 'INGRESOS TOTALES' in totales_acumulativos and 'GASTOS TOTALES' in totales_acumulativos:
            income = totales_acumulativos['INGRESOS TOTALES']['total']
            expenses = totales_acumulativos['GASTOS TOTALES']['total']
            
            if income > 0:
                insights['efficiency_score'] = round((1 - expenses / income) * 100, 2)
                insights['profitability_index'] = round(income / expenses, 2)
        
        if error_permisible > 15 or growth_rate < -10:
            insights['risk_level'] = 'high'
        elif error_permisible > 10 or growth_rate < 0:
            insights['risk_level'] = 'medium'
        
        if growth_rate > 20:
            insights['opportunities'].append('Expansión rápida detectada')
        if insights['efficiency_score'] > 30:
            insights['opportunities'].append('Alta eficiencia operativa')
        
        return insights