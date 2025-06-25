# services/simulation_financial.py
"""
Refactored financial analysis service for simulation results.
Analyzes daily financial performance and generates recommendations.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from simulate.services.validation_service import SimulationValidationService
import numpy as np

from django.db import transaction
from django.db.models import Sum, Avg, Max, Min, StdDev
from scipy import stats

from ..models import Simulation, ResultSimulation
from finance.models import FinanceRecommendation, FinanceRecommendationSimulation
from business.models import Business


logger = logging.getLogger(__name__)


class SimulationFinancialAnalyzer:
    """Enhanced financial analyzer for simulation results"""
    
    def __init__(self):
        
        self.critical_thresholds = {
            'min_profit_margin': -0.1,      # -10% minimum acceptable
            'target_profit_margin': 0.15,   # 15% target
            'max_cost_ratio': 0.85,         # 85% max cost to revenue
            'min_liquidity_ratio': 1.2,     # Current ratio
            'max_debt_ratio': 0.6,          # 60% max debt
            'min_roi': 0.1,                 # 10% minimum ROI
            'target_efficiency': 0.85,      # 85% operational efficiency
        }
    
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
                
                # Check if value exceeds threshold
                if threshold > 0 and value > threshold:
                    severity = ((value - threshold) / threshold * 100)
                    
                    recommendations.append({
                        'name': rec.name,
                        'description': rec.description or rec.recommendation,
                        'recommendation': rec.recommendation,
                        'severity': min(100, severity),
                        'value': value,
                        'threshold': threshold,
                        'variable': rec.variable_name,
                        'priority': 'high' if severity > 50 else 'medium' if severity > 20 else 'low',
                        # 'icon': self._get_recommendation_icon(rec.variable_name),
                        # 'color': self._get_recommendation_color(severity)
                    })
        
        # Add dynamic recommendations based on calculated metrics
        
        # 1. Efficiency Analysis
        if 'TOTAL PRODUCTOS VENDIDOS' in totales_acumulativos and 'TOTAL PRODUCTOS PRODUCIDOS' in totales_acumulativos:
            vendidos = totales_acumulativos['TOTAL PRODUCTOS VENDIDOS']['total']
            producidos = totales_acumulativos['TOTAL PRODUCTOS PRODUCIDOS']['total']
            if producidos > 0:
                efficiency = (vendidos / producidos) * 100
                if efficiency < 80:
                    recommendations.append({
                        'name': 'Eficiencia de Ventas Baja',
                        'description': f'Solo se está vendiendo el {efficiency:.1f}% de la producción',
                        'recommendation': 'Revisar estrategias de ventas y marketing. Considerar promociones o ajustar producción.',
                        'severity': 90 - efficiency,
                        'priority': 'high' if efficiency < 60 else 'medium',
                        'variable': 'EFICIENCIA_VENTAS',
                        'icon': 'bx-trending-down',
                        'color': 'danger' if efficiency < 60 else 'warning'
                    })
        
        # 2. Profitability Analysis
        if 'INGRESOS TOTALES' in totales_acumulativos and 'GASTOS TOTALES' in totales_acumulativos:
            ingresos = totales_acumulativos['INGRESOS TOTALES']['total']
            gastos = totales_acumulativos.get('GASTOS TOTALES', {}).get('total', 0) or totales_acumulativos.get('Total Gastos', {}).get('total', 0)
            
            if ingresos > 0:
                profit_margin = ((ingresos - gastos) / ingresos) * 100
                if profit_margin < 10:
                    recommendations.append({
                        'name': 'Margen de Ganancia Bajo',
                        'description': f'El margen de ganancia es solo {profit_margin:.1f}%',
                        'recommendation': 'Analizar estructura de costos y considerar optimizaciones o ajuste de precios.',
                        'severity': 80,
                        'priority': 'high',
                        'variable': 'MARGEN_GANANCIA',
                        'icon': 'bx-dollar-circle',
                        'color': 'danger'
                    })
                elif profit_margin > 40:
                    recommendations.append({
                        'name': 'Excelente Margen de Ganancia',
                        'description': f'El margen de ganancia es {profit_margin:.1f}%',
                        'recommendation': 'Mantener estrategia actual. Considerar expansión o inversión en crecimiento.',
                        'severity': 20,
                        'priority': 'low',
                        'variable': 'MARGEN_GANANCIA',
                        'icon': 'bx-trophy',
                        'color': 'success'
                    })
        
        # 3. Inventory Analysis
        if 'DEMANDA INSATISFECHA' in totales_acumulativos:
            demanda_insatisfecha = totales_acumulativos['DEMANDA INSATISFECHA']['total']
            if demanda_insatisfecha > 0:
                recommendations.append({
                    'name': 'Demanda Insatisfecha Detectada',
                    'description': f'Se dejó de atender {demanda_insatisfecha:.0f} unidades de demanda',
                    'recommendation': 'Aumentar capacidad de producción o mejorar gestión de inventarios.',
                    'severity': min(100, demanda_insatisfecha / 100),
                    'priority': 'high',
                    'variable': 'DEMANDA_INSATISFECHA',
                    'icon': 'bx-error-circle',
                    'color': 'danger'
                })
        
        # 4. Cost Structure Analysis
        if 'GASTOS OPERATIVOS' in totales_acumulativos and 'INGRESOS TOTALES' in totales_acumulativos:
            gastos_op = totales_acumulativos['GASTOS OPERATIVOS']['total']
            ingresos = totales_acumulativos['INGRESOS TOTALES']['total']
            if ingresos > 0:
                cost_ratio = (gastos_op / ingresos) * 100
                if cost_ratio > 70:
                    recommendations.append({
                        'name': 'Costos Operativos Elevados',
                        'description': f'Los costos operativos representan el {cost_ratio:.1f}% de los ingresos',
                        'recommendation': 'Revisar y optimizar procesos operativos. Buscar eficiencias en la cadena de suministro.',
                        'severity': cost_ratio,
                        'priority': 'high',
                        'variable': 'COSTOS_OPERATIVOS',
                        'icon': 'bx-receipt',
                        'color': 'warning'
                    })
        
        # 5. Growth Analysis
        if 'growth_rate' in financial_results:
            growth = financial_results['growth_rate']
            if growth < -5:
                recommendations.append({
                    'name': 'Tendencia Negativa en Demanda',
                    'description': f'La demanda muestra una caída del {abs(growth):.1f}%',
                    'recommendation': 'Implementar estrategias de retención y recuperación de clientes. Revisar competitividad.',
                    'severity': min(100, abs(growth) * 2),
                    'priority': 'high',
                    'variable': 'CRECIMIENTO',
                    'icon': 'bx-down-arrow-alt',
                    'color': 'danger'
                })
            elif growth > 20:
                recommendations.append({
                    'name': 'Crecimiento Acelerado',
                    'description': f'La demanda crece al {growth:.1f}%',
                    'recommendation': 'Preparar infraestructura para expansión. Asegurar capital de trabajo suficiente.',
                    'severity': 30,
                    'priority': 'medium',
                    'variable': 'CRECIMIENTO',
                    'icon': 'bx-up-arrow-alt',
                    'color': 'info'
                })
        
        # 6. ROI Analysis
        if 'Retorno Inversión' in totales_acumulativos:
            roi = totales_acumulativos['Retorno Inversión']['total']
            if roi < 1:
                recommendations.append({
                    'name': 'ROI Bajo',
                    'description': f'El retorno de inversión es {roi:.2f}',
                    'recommendation': 'Revisar estrategia de inversión y buscar oportunidades de mejora en eficiencia.',
                    'severity': 70,
                    'priority': 'medium',
                    'variable': 'ROI',
                    'icon': 'bx-line-chart-down',
                    'color': 'warning'
                })
        
        # Sort by priority and severity
        recommendations.sort(key=lambda x: (
            {'high': 0, 'medium': 1, 'low': 2}.get(x.get('priority', 'low'), 3),
            -x.get('severity', 0)
        ))
        
        # Save recommendations to database
        if recommendations:
            self._save_recommendations_to_db(simulation_instance, recommendations[:10], business)
        
        return recommendations[:10]  # Return top 10 recommendations
    
    def analyze_financial_results(self, simulation_id: int) -> Dict[str, Any]:
        """
        Perform comprehensive financial analysis of simulation results.
        Focus on daily financial performance and trends.
        """
        try:
            # Get simulation and results
            simulation = Simulation.objects.select_related(
                'fk_questionary_result__fk_questionary__fk_product__fk_business'
            ).get(id=simulation_id)
            
            results = ResultSimulation.objects.filter(
                fk_simulation=simulation,
                is_active=True
            ).order_by('date')
            
            if not results.exists():
                logger.warning(f"No results found for simulation {simulation_id}")
                return self._create_empty_analysis()
            
            # Extract financial data
            daily_financials = self._extract_daily_financials(results)
            
            # Perform various analyses
            profitability_analysis = self._analyze_profitability(daily_financials)
            cost_analysis = self._analyze_costs(daily_financials)
            efficiency_analysis = self._analyze_efficiency(daily_financials)
            trend_analysis = self._analyze_trends(daily_financials)
            
            # Generate financial recommendations
            recommendations = self._generate_financial_recommendations(
                simulation,
                profitability_analysis,
                cost_analysis,
                efficiency_analysis,
                trend_analysis
            )
            
            if results.exists():
                first_result = results.first()
                last_result = results.last()
                initial_demand = float(first_result.demand_mean)
                predicted_demand = float(last_result.demand_mean)
            else:
                demand_stats = simulation.get_demand_statistics()
                initial_demand = demand_stats['mean']
                predicted_demand = demand_stats['mean']
            
            simulation_val_service = SimulationValidationService()
            
            growth_rate = self._calculate_growth_rate_between_values(initial_demand, predicted_demand)
            error_permisible = simulation_val_service._calculate_error_percentage(initial_demand, predicted_demand)
            
            # Calculate key financial indicators
            kpis = self._calculate_financial_kpis(daily_financials)
            
            # Risk assessment
            risk_assessment = self._assess_financial_risks(
                daily_financials,
                profitability_analysis,
                cost_analysis
            )
            class DemandData:
                def __init__(self, quantity):
                    self.quantity = quantity
            return {
                'simulation_id': simulation_id,
                'business': simulation.fk_questionary_result.fk_questionary.fk_product.fk_business,
                'daily_financials': daily_financials,
                'profitability': profitability_analysis,
                'costs': cost_analysis,
                'efficiency': efficiency_analysis,
                'trends': trend_analysis,
                'kpis': kpis,
                'recommendations': recommendations,
                'risk_assessment': risk_assessment,
                'summary': self._create_executive_summary(
                    kpis, profitability_analysis, risk_assessment
                ),
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
            return self._create_empty_analysis()
        except Exception as e:
            logger.error(f"Error analyzing financial results: {str(e)}")
            return self._create_empty_analysis()
    
    def _extract_daily_financials(self, results) -> List[Dict[str, Any]]:
        """Extract financial data from daily results"""
        daily_financials = []
        
        for idx, result in enumerate(results):
            if hasattr(result, 'variables') and result.variables:
                vars = result.variables
                
                financial_data = {
                    'day': idx + 1,
                    'date': result.date,
                    # Revenue
                    'revenue': float(vars.get('IT', 0)),
                    'expected_revenue': float(vars.get('IE', 0)),
                    # Costs
                    'operating_costs': float(vars.get('GO', 0)),
                    'general_expenses': float(vars.get('GG', 0)),
                    'total_costs': float(vars.get('TG', 0)),
                    'material_costs': float(vars.get('CTAI', 0)),
                    'transport_costs': float(vars.get('CTTL', 0)),
                    'storage_costs': float(vars.get('CA', 0)),
                    'wastage_costs': float(vars.get('CTM', 0)),
                    # Profit
                    'gross_profit': float(vars.get('IB', 0)),
                    'net_profit': float(vars.get('GT', 0)),
                    # Margins
                    'gross_margin': float(vars.get('MB', 0)),
                    'net_margin': float(vars.get('NR', 0)),
                    # Other metrics
                    'roi': float(vars.get('RI', 0)),
                    'break_even': float(vars.get('PED', 0)),
                    'cost_efficiency': float(vars.get('COST_EFFICIENCY', 0)),
                    # Operational data for context
                    'sales_volume': float(vars.get('TPV', 0)),
                    'price': float(vars.get('PVP', 0)),
                    'demand': float(result.demand_mean),
                }
                
                # Calculate additional metrics
                if financial_data['revenue'] > 0:
                    financial_data['cost_ratio'] = financial_data['total_costs'] / financial_data['revenue']
                    financial_data['ebitda'] = financial_data['gross_profit'] - financial_data['operating_costs']
                else:
                    financial_data['cost_ratio'] = 0
                    financial_data['ebitda'] = -financial_data['operating_costs']
                
                daily_financials.append(financial_data)
        
        return daily_financials
    
    def _analyze_profitability(self, daily_financials: List[Dict]) -> Dict[str, Any]:
        """Analyze profitability metrics and patterns"""
        if not daily_financials:
            return {}
        
        # Extract profit data
        revenues = [d['revenue'] for d in daily_financials]
        net_profits = [d['net_profit'] for d in daily_financials]
        gross_margins = [d['gross_margin'] for d in daily_financials]
        net_margins = [d['net_margin'] for d in daily_financials]
        
        # Calculate statistics
        total_revenue = sum(revenues)
        total_profit = sum(net_profits)
        avg_gross_margin = np.mean(gross_margins) if gross_margins else 0
        avg_net_margin = np.mean(net_margins) if net_margins else 0
        
        # Profitability trends
        profitable_days = sum(1 for p in net_profits if p > 0)
        loss_days = len(net_profits) - profitable_days
        
        # Calculate profit volatility
        profit_std = np.std(net_profits) if len(net_profits) > 1 else 0
        profit_cv = profit_std / abs(np.mean(net_profits)) if np.mean(net_profits) != 0 else 0
        
        # Break-even analysis
        break_even_day = None
        cumulative_profit = 0
        for i, profit in enumerate(net_profits):
            cumulative_profit += profit
            if cumulative_profit > 0 and break_even_day is None:
                break_even_day = i + 1
        
        return {
            'total_revenue': total_revenue,
            'total_profit': total_profit,
            'average_revenue_per_day': total_revenue / len(revenues) if revenues else 0,
            'average_profit_per_day': total_profit / len(net_profits) if net_profits else 0,
            'gross_margin': {
                'average': avg_gross_margin,
                'min': min(gross_margins) if gross_margins else 0,
                'max': max(gross_margins) if gross_margins else 0,
                'std': np.std(gross_margins) if len(gross_margins) > 1 else 0
            },
            'net_margin': {
                'average': avg_net_margin,
                'min': min(net_margins) if net_margins else 0,
                'max': max(net_margins) if net_margins else 0,
                'std': np.std(net_margins) if len(net_margins) > 1 else 0
            },
            'profitable_days': profitable_days,
            'loss_days': loss_days,
            'profitability_rate': profitable_days / len(net_profits) if net_profits else 0,
            'profit_volatility': profit_cv,
            'break_even_day': break_even_day,
            'roi_average': np.mean([d['roi'] for d in daily_financials]),
            'ebitda_total': sum(d['ebitda'] for d in daily_financials)
        }
    
    def _analyze_costs(self, daily_financials: List[Dict]) -> Dict[str, Any]:
        """Analyze cost structure and efficiency"""
        if not daily_financials:
            return {}
        
        # Cost components
        operating_costs = [d['operating_costs'] for d in daily_financials]
        material_costs = [d['material_costs'] for d in daily_financials]
        general_expenses = [d['general_expenses'] for d in daily_financials]
        total_costs = [d['total_costs'] for d in daily_financials]
        
        # Calculate cost structure
        total_operating = sum(operating_costs)
        total_materials = sum(material_costs)
        total_general = sum(general_expenses)
        total_all_costs = sum(total_costs)
        
        # Cost ratios
        cost_structure = {
            'operating': total_operating / total_all_costs if total_all_costs > 0 else 0,
            'materials': total_materials / total_all_costs if total_all_costs > 0 else 0,
            'general': total_general / total_all_costs if total_all_costs > 0 else 0
        }
        
        # Variable vs fixed cost analysis
        # Approximate: materials and transport are variable, others are more fixed
        variable_costs = sum(d['material_costs'] + d['transport_costs'] for d in daily_financials)
        fixed_costs = total_all_costs - variable_costs
        
        # Cost efficiency metrics
        revenues = [d['revenue'] for d in daily_financials]
        cost_to_revenue_ratios = [d['cost_ratio'] for d in daily_financials if d['revenue'] > 0]
        
        return {
            'total_costs': total_all_costs,
            'average_daily_cost': total_all_costs / len(daily_financials) if daily_financials else 0,
            'cost_structure': cost_structure,
            'cost_breakdown': {
                'operating': total_operating,
                'materials': total_materials,
                'general': total_general,
                'transport': sum(d['transport_costs'] for d in daily_financials),
                'storage': sum(d['storage_costs'] for d in daily_financials),
                'wastage': sum(d['wastage_costs'] for d in daily_financials)
            },
            'variable_vs_fixed': {
                'variable_costs': variable_costs,
                'fixed_costs': fixed_costs,
                'variable_ratio': variable_costs / total_all_costs if total_all_costs > 0 else 0
            },
            'cost_efficiency': {
                'average_cost_ratio': np.mean(cost_to_revenue_ratios) if cost_to_revenue_ratios else 0,
                'best_cost_ratio': min(cost_to_revenue_ratios) if cost_to_revenue_ratios else 0,
                'worst_cost_ratio': max(cost_to_revenue_ratios) if cost_to_revenue_ratios else 0
            },
            'cost_per_unit': {
                'average': total_all_costs / sum(d['sales_volume'] for d in daily_financials) 
                          if sum(d['sales_volume'] for d in daily_financials) > 0 else 0
            }
        }
    
    def _analyze_efficiency(self, daily_financials: List[Dict]) -> Dict[str, Any]:
        """Analyze operational and financial efficiency"""
        if not daily_financials:
            return {}
        
        # Efficiency metrics
        cost_efficiencies = [d['cost_efficiency'] for d in daily_financials]
        
        # Revenue per unit analysis
        revenue_per_unit = []
        cost_per_unit = []
        for d in daily_financials:
            if d['sales_volume'] > 0:
                revenue_per_unit.append(d['revenue'] / d['sales_volume'])
                cost_per_unit.append(d['total_costs'] / d['sales_volume'])
        
        # Asset turnover proxy (using daily revenue)
        avg_daily_revenue = np.mean([d['revenue'] for d in daily_financials])
        
        # Working capital efficiency (simplified)
        inventory_days = []  # Would need inventory data
        
        return {
            'cost_efficiency': {
                'average': np.mean(cost_efficiencies) if cost_efficiencies else 0,
                'trend': self._calculate_trend([d['cost_efficiency'] for d in daily_financials])
            },
            'revenue_per_unit': {
                'average': np.mean(revenue_per_unit) if revenue_per_unit else 0,
                'min': min(revenue_per_unit) if revenue_per_unit else 0,
                'max': max(revenue_per_unit) if revenue_per_unit else 0
            },
            'cost_per_unit': {
                'average': np.mean(cost_per_unit) if cost_per_unit else 0,
                'trend': self._calculate_trend(cost_per_unit) if len(cost_per_unit) > 2 else 'stable'
            },
            'contribution_margin': {
                'per_unit': (np.mean(revenue_per_unit) - np.mean(cost_per_unit)) 
                           if revenue_per_unit and cost_per_unit else 0
            },
            'operational_leverage': self._calculate_operational_leverage(daily_financials)
        }
    
    def _analyze_trends(self, daily_financials: List[Dict]) -> Dict[str, Any]:
        """Analyze financial trends over the simulation period"""
        if len(daily_financials) < 3:
            return {'status': 'insufficient_data'}
        
        # Extract time series
        revenues = [d['revenue'] for d in daily_financials]
        profits = [d['net_profit'] for d in daily_financials]
        costs = [d['total_costs'] for d in daily_financials]
        margins = [d['net_margin'] for d in daily_financials]
        
        return {
            'revenue_trend': {
                'direction': self._calculate_trend(revenues),
                'growth_rate': self._calculate_growth_rate(revenues),
                'volatility': np.std(revenues) / np.mean(revenues) if np.mean(revenues) > 0 else 0
            },
            'profit_trend': {
                'direction': self._calculate_trend(profits),
                'improvement_rate': self._calculate_improvement_rate(profits),
                'stability': 1 - (np.std(profits) / (abs(np.mean(profits)) + 0.01))
            },
            'cost_trend': {
                'direction': self._calculate_trend(costs),
                'growth_rate': self._calculate_growth_rate(costs),
                'as_pct_of_revenue': self._calculate_cost_revenue_trend(costs, revenues)
            },
            'margin_trend': {
                'direction': self._calculate_trend(margins),
                'improvement': margins[-1] - margins[0] if margins else 0,
                'consistency': 1 - np.std(margins) if margins else 0
            },
            'sustainability': self._assess_trend_sustainability(daily_financials)
        }
    
    def _calculate_financial_kpis(self, daily_financials: List[Dict]) -> Dict[str, float]:
        """Calculate key financial performance indicators"""
        if not daily_financials:
            return {}
        
        # Aggregate values
        total_revenue = sum(d['revenue'] for d in daily_financials)
        total_profit = sum(d['net_profit'] for d in daily_financials)
        total_costs = sum(d['total_costs'] for d in daily_financials)
        
        # Average values
        avg_revenue = total_revenue / len(daily_financials)
        avg_profit = total_profit / len(daily_financials)
        avg_margin = np.mean([d['net_margin'] for d in daily_financials])
        
        # Best/worst days
        best_day = max(daily_financials, key=lambda x: x['net_profit'])
        worst_day = min(daily_financials, key=lambda x: x['net_profit'])
        
        return {
            'total_revenue': total_revenue,
            'total_profit': total_profit,
            'total_costs': total_costs,
            'average_daily_revenue': avg_revenue,
            'average_daily_profit': avg_profit,
            'profit_margin': total_profit / total_revenue if total_revenue > 0 else 0,
            'average_margin': avg_margin,
            'roi': np.mean([d['roi'] for d in daily_financials]),
            'best_day_profit': best_day['net_profit'],
            'best_day_number': best_day['day'],
            'worst_day_profit': worst_day['net_profit'],
            'worst_day_number': worst_day['day'],
            'revenue_per_demand': total_revenue / sum(d['demand'] for d in daily_financials) 
                                 if sum(d['demand'] for d in daily_financials) > 0 else 0,
            'cost_per_unit_sold': total_costs / sum(d['sales_volume'] for d in daily_financials)
                                 if sum(d['sales_volume'] for d in daily_financials) > 0 else 0
        }
    
    def _generate_financial_recommendations(self, simulation: Simulation,
                                          profitability: Dict,
                                          costs: Dict,
                                          efficiency: Dict,
                                          trends: Dict) -> List[Dict[str, Any]]:
        """Generate actionable financial recommendations"""
        recommendations = []
        business = simulation.fk_questionary_result.fk_questionary.fk_product.fk_business
        
        # Profitability recommendations
        if profitability.get('net_margin', {}).get('average', 0) < self.critical_thresholds['target_profit_margin']:
            severity = 'high' if profitability['net_margin']['average'] < 0 else 'medium'
            recommendations.append({
                'category': 'profitability',
                'severity': severity,
                'title': 'Margen de Ganancia Bajo',
                'description': f"El margen neto promedio es {profitability['net_margin']['average']:.1%}, "
                             f"por debajo del objetivo de {self.critical_thresholds['target_profit_margin']:.0%}",
                'actions': [
                    'Revisar estructura de precios',
                    'Optimizar costos operativos',
                    'Mejorar eficiencia de producción'
                ],
                'impact': 'high',
                'metric_value': profitability['net_margin']['average']
            })
        
        # Cost efficiency recommendations
        if costs.get('cost_efficiency', {}).get('average_cost_ratio', 0) > self.critical_thresholds['max_cost_ratio']:
            recommendations.append({
                'category': 'costs',
                'severity': 'high',
                'title': 'Costos Excesivos',
                'description': f"Los costos representan {costs['cost_efficiency']['average_cost_ratio']:.1%} "
                             f"de los ingresos, superando el límite de {self.critical_thresholds['max_cost_ratio']:.0%}",
                'actions': [
                    'Negociar mejores precios con proveedores',
                    'Reducir desperdicios',
                    'Optimizar rutas de transporte',
                    'Revisar gastos generales'
                ],
                'impact': 'high',
                'metric_value': costs['cost_efficiency']['average_cost_ratio']
            })
        
        # Trend-based recommendations
        if trends.get('profit_trend', {}).get('direction') == 'declining':
            recommendations.append({
                'category': 'trends',
                'severity': 'medium',
                'title': 'Tendencia Negativa en Ganancias',
                'description': 'Las ganancias muestran una tendencia decreciente durante el período simulado',
                'actions': [
                    'Investigar causas de la disminución',
                    'Implementar medidas correctivas inmediatas',
                    'Monitorear indicadores diariamente'
                ],
                'impact': 'medium',
                'metric_value': trends['profit_trend'].get('improvement_rate', 0)
            })
        
        # Efficiency recommendations
        if efficiency.get('operational_leverage', 0) < 1:
            recommendations.append({
                'category': 'efficiency',
                'severity': 'low',
                'title': 'Baja Palanca Operativa',
                'description': 'El negocio tiene baja sensibilidad a cambios en volumen',
                'actions': [
                    'Incrementar proporción de costos variables',
                    'Mejorar escalabilidad del negocio',
                    'Optimizar estructura de costos'
                ],
                'impact': 'medium',
                'metric_value': efficiency['operational_leverage']
            })
        
        # Break-even recommendations
        if not profitability.get('break_even_day'):
            recommendations.append({
                'category': 'critical',
                'severity': 'critical',
                'title': 'No Se Alcanza Punto de Equilibrio',
                'description': 'El negocio no logra cubrir sus costos en el período simulado',
                'actions': [
                    'Revisar urgentemente el modelo de negocio',
                    'Reducir costos fijos',
                    'Aumentar precio o volumen de ventas',
                    'Buscar fuentes alternativas de ingresos'
                ],
                'impact': 'critical',
                'metric_value': profitability.get('total_profit', 0)
            })
        
        # Sort by severity and save to database
        recommendations.sort(key=lambda x: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}[x['severity']])
        
        # Save recommendations
        self._save_recommendations_to_db(simulation, recommendations, business)
        
        return recommendations[:10]  # Return top 10 recommendations
    
    def _assess_financial_risks(self, daily_financials: List[Dict],
                               profitability: Dict,
                               costs: Dict) -> Dict[str, Any]:
        """Assess financial risks based on analysis"""
        risks = {
            'overall_risk': 'low',
            'risk_factors': [],
            'risk_score': 0
        }
        
        risk_score = 0
        
        # Profitability risk
        if profitability.get('profitability_rate', 0) < 0.7:
            risk_score += 30
            risks['risk_factors'].append({
                'factor': 'low_profitability',
                'description': 'Baja tasa de días rentables',
                'severity': 'high'
            })
        
        # Volatility risk
        if profitability.get('profit_volatility', 0) > 0.5:
            risk_score += 20
            risks['risk_factors'].append({
                'factor': 'high_volatility',
                'description': 'Alta volatilidad en ganancias',
                'severity': 'medium'
            })
        
        # Cost structure risk
        if costs.get('variable_vs_fixed', {}).get('variable_ratio', 0) < 0.3:
            risk_score += 15
            risks['risk_factors'].append({
                'factor': 'high_fixed_costs',
                'description': 'Estructura de costos muy rígida',
                'severity': 'medium'
            })
        
        # Margin risk
        avg_margin = profitability.get('net_margin', {}).get('average', 0)
        if avg_margin < 0.05:
            risk_score += 25
            risks['risk_factors'].append({
                'factor': 'low_margins',
                'description': 'Márgenes de ganancia muy bajos',
                'severity': 'high'
            })
        
        # Determine overall risk level
        risks['risk_score'] = risk_score
        if risk_score >= 60:
            risks['overall_risk'] = 'high'
        elif risk_score >= 30:
            risks['overall_risk'] = 'medium'
        else:
            risks['overall_risk'] = 'low'
        
        return risks
    
    def _create_executive_summary(self, kpis: Dict,
                                profitability: Dict,
                                risk_assessment: Dict) -> Dict[str, Any]:
        """Create executive summary of financial analysis"""
        return {
            'status': self._determine_business_health(kpis, profitability, risk_assessment),
            'key_metrics': {
                'total_revenue': kpis.get('total_revenue', 0),
                'total_profit': kpis.get('total_profit', 0),
                'profit_margin': kpis.get('profit_margin', 0),
                'roi': kpis.get('roi', 0)
            },
            'highlights': self._generate_highlights(kpis, profitability),
            'concerns': self._generate_concerns(profitability, risk_assessment),
            'outlook': self._generate_outlook(profitability, risk_assessment)
        }
    
    # Helper methods
    
    def _calculate_trend(self, data: List[float]) -> str:
        """Calculate trend direction from time series data"""
        if len(data) < 3:
            return 'insufficient_data'
        
        x = np.arange(len(data))
        slope, _, r_value, p_value, _ = stats.linregress(x, data)
        
        if p_value > 0.05:  # Not statistically significant
            return 'stable'
        elif slope > 0:
            return 'increasing'
        else:
            return 'declining'
    
    def _calculate_growth_rate(self, data: List[float]) -> float:
        """Calculate average growth rate"""
        if len(data) < 2 or data[0] == 0:
            return 0
        
        # Compound growth rate
        return ((data[-1] / data[0]) ** (1 / (len(data) - 1)) - 1) * 100
    
    def _calculate_growth_rate_between_values(self, initial: float, final: float) -> float:
        """Calculate growth rate between two specific values"""
        if initial == 0:
            return 0.0 if final == 0 else float('inf')
        return (final - initial) / initial
    
    def _calculate_improvement_rate(self, data: List[float]) -> float:
        """Calculate improvement rate for metrics that can be negative"""
        if len(data) < 2:
            return 0
        
        return (data[-1] - data[0]) / len(data)
    
    def _calculate_cost_revenue_trend(self, costs: List[float], 
                                    revenues: List[float]) -> str:
        """Analyze trend of costs as percentage of revenue"""
        if len(costs) != len(revenues) or not revenues:
            return 'unknown'
        
        ratios = [c/r for c, r in zip(costs, revenues) if r > 0]
        if not ratios:
            return 'unknown'
        
        return self._calculate_trend(ratios)
    
    def _calculate_operational_leverage(self, daily_financials: List[Dict]) -> float:
        """Calculate degree of operational leverage"""
        if len(daily_financials) < 2:
            return 0
        
        # Simplified: compare profit changes to revenue changes
        revenues = [d['revenue'] for d in daily_financials]
        profits = [d['net_profit'] for d in daily_financials]
        
        revenue_changes = [revenues[i] - revenues[i-1] for i in range(1, len(revenues))]
        profit_changes = [profits[i] - profits[i-1] for i in range(1, len(profits))]
        
        valid_pairs = [(p, r) for p, r in zip(profit_changes, revenue_changes) if r != 0]
        
        if not valid_pairs:
            return 1.0
        
        leverages = [abs(p/r) for p, r in valid_pairs]
        return np.median(leverages)
    
    def _assess_trend_sustainability(self, daily_financials: List[Dict]) -> str:
        """Assess if current trends are sustainable"""
        if len(daily_financials) < 7:
            return 'insufficient_data'
        
        # Check recent trends (last 7 days)
        recent_profits = [d['net_profit'] for d in daily_financials[-7:]]
        recent_margins = [d['net_margin'] for d in daily_financials[-7:]]
        
        # Calculate volatility and trend
        profit_volatility = np.std(recent_profits) / (abs(np.mean(recent_profits)) + 0.01)
        margin_trend = self._calculate_trend(recent_margins)
        
        if profit_volatility > 0.5:
            return 'unstable'
        elif margin_trend == 'declining':
            return 'deteriorating'
        elif margin_trend == 'increasing' and np.mean(recent_margins) > 0.1:
            return 'improving'
        else:
            return 'stable'
    
    def _determine_business_health(self, kpis: Dict, 
                                 profitability: Dict,
                                 risk_assessment: Dict) -> str:
        """Determine overall business health status"""
        health_score = 0
        
        # Profitability check
        if kpis.get('profit_margin', 0) > 0.15:
            health_score += 30
        elif kpis.get('profit_margin', 0) > 0.05:
            health_score += 15
        
        # Stability check
        if profitability.get('profit_volatility', 1) < 0.3:
            health_score += 20
        
        # Risk check
        if risk_assessment.get('overall_risk') == 'low':
            health_score += 30
        elif risk_assessment.get('overall_risk') == 'medium':
            health_score += 15
        
        # ROI check
        if kpis.get('roi', 0) > 0.2:
            health_score += 20
        elif kpis.get('roi', 0) > 0.1:
            health_score += 10
        
        if health_score >= 70:
            return 'excellent'
        elif health_score >= 50:
            return 'good'
        elif health_score >= 30:
            return 'fair'
        else:
            return 'poor'
    
    def _generate_highlights(self, kpis: Dict, profitability: Dict) -> List[str]:
        """Generate positive highlights from analysis"""
        highlights = []
        
        if kpis.get('profit_margin', 0) > 0.15:
            highlights.append(f"Excelente margen de ganancia: {kpis['profit_margin']:.1%}")
        
        if profitability.get('profitability_rate', 0) > 0.8:
            rate = profitability['profitability_rate'] * 100
            highlights.append(f"{rate:.0f}% de días fueron rentables")
        
        if kpis.get('roi', 0) > 0.2:
            highlights.append(f"Alto retorno de inversión: {kpis['roi']:.1%}")
        
        if profitability.get('break_even_day'):
            highlights.append(f"Punto de equilibrio alcanzado en día {profitability['break_even_day']}")
        
        return highlights
    
    def _generate_concerns(self, profitability: Dict, 
                         risk_assessment: Dict) -> List[str]:
        """Generate concerns from analysis"""
        concerns = []
        
        if profitability.get('loss_days', 0) > profitability.get('profitable_days', 1):
            concerns.append("Más días con pérdidas que con ganancias")
        
        if risk_assessment.get('overall_risk') == 'high':
            concerns.append("Nivel de riesgo financiero alto")
        
        if profitability.get('profit_volatility', 0) > 0.5:
            concerns.append("Alta volatilidad en las ganancias")
        
        if not profitability.get('break_even_day'):
            concerns.append("No se alcanzó el punto de equilibrio")
        
        return concerns
    
    def _generate_outlook(self, profitability: Dict, 
                        risk_assessment: Dict) -> str:
        """Generate business outlook statement"""
        if risk_assessment.get('overall_risk') == 'high':
            return 'El negocio enfrenta desafíos significativos que requieren acción inmediata'
        elif profitability.get('profitability_rate', 0) > 0.7:
            return 'El negocio muestra buen desempeño con oportunidades de mejora'
        else:
            return 'Se requieren ajustes operativos para mejorar la rentabilidad'
    
    def _save_recommendations_to_db(self, simulation: Simulation,
                                recommendations: List[Dict],
                                business: Business) -> None:
        """Save financial recommendations to database"""
        try:
            logger.info(f"Attempting to save {len(recommendations[:5])} recommendations")
            
            for i, rec in enumerate(recommendations[:5]):
                logger.info(f"Processing recommendation {i+1}: {rec}")
                
                if 'metric_value' in rec:
                    try:
                        metric_value = float(rec['metric_value'])
                        logger.info(f"Converting metric_value: {rec['metric_value']} -> {metric_value}")
                        
                        # Create the simulation record
                        sim_rec = FinanceRecommendationSimulation.objects.create(
                            data=metric_value,
                            fk_simulation=simulation,
                        )
                        logger.info(f"Successfully created FinanceRecommendationSimulation ID: {sim_rec.id}")
                        
                    except ValueError as ve:
                        logger.error(f"Error converting metric_value to float: {rec['metric_value']} - {ve}")
                    except Exception as creation_error:
                        logger.error(f"Error creating FinanceRecommendationSimulation: {creation_error}")
                        logger.error(f"Simulation ID: {simulation.id}")
                        logger.error(f"Data: {metric_value}")
                else:
                    logger.warning(f"Missing 'metric_value' in recommendation: {rec}")
                    
        except Exception as e:
            logger.error(f"Error saving recommendations: {str(e)}")
            logger.error(f"Simulation: {simulation}")
            logger.error(f"Business: {business}")
            logger.error(f"Recommendations: {recommendations[:5]}")
    
    def _create_empty_analysis(self) -> Dict[str, Any]:
        """Create empty analysis structure"""
        return {
            'simulation_id': None,
            'business': None,
            'daily_financials': [],
            'profitability': {},
            'costs': {},
            'efficiency': {},
            'trends': {'status': 'no_data'},
            'kpis': {},
            'recommendations': [],
            'risk_assessment': {'overall_risk': 'unknown', 'risk_factors': []},
            'summary': {
                'status': 'no_data',
                'key_metrics': {},
                'highlights': [],
                'concerns': ['No hay datos disponibles para análisis'],
                'outlook': 'Se requieren datos de simulación para generar análisis'
            }
        }
    
    def compare_financial_performance(self, simulation_ids: List[int]) -> Dict[str, Any]:
        """Compare financial performance across multiple simulations"""
        comparisons = []
        
        for sim_id in simulation_ids:
            analysis = self.analyze_financial_results(sim_id)
            if analysis['kpis']:
                comparisons.append({
                    'simulation_id': sim_id,
                    'total_profit': analysis['kpis']['total_profit'],
                    'profit_margin': analysis['kpis']['profit_margin'],
                    'roi': analysis['kpis']['roi'],
                    'risk_level': analysis['risk_assessment']['overall_risk'],
                    'health_status': analysis['summary']['status']
                })
        
        if not comparisons:
            return {'error': 'No valid simulations for comparison'}
        
        # Find best performer
        best_profit = max(comparisons, key=lambda x: x['total_profit'])
        best_margin = max(comparisons, key=lambda x: x['profit_margin'])
        best_roi = max(comparisons, key=lambda x: x['roi'])
        
        return {
            'comparisons': comparisons,
            'best_performers': {
                'profit': best_profit,
                'margin': best_margin,
                'roi': best_roi
            },
            'summary': self._generate_comparison_summary(comparisons)
        }
    
    def _generate_comparison_summary(self, comparisons: List[Dict]) -> str:
        """Generate summary of simulation comparisons"""
        if not comparisons:
            return "No hay datos para comparar"
        
        avg_margin = np.mean([c['profit_margin'] for c in comparisons])
        best_sim = max(comparisons, key=lambda x: x['total_profit'])
        
        return (f"En promedio, las simulaciones muestran un margen de {avg_margin:.1%}. "
                f"La simulación {best_sim['simulation_id']} muestra el mejor desempeño "
                f"con una ganancia total de {best_sim['total_profit']:.2f}")
