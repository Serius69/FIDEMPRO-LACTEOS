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


# ─────────────────────────────────────────────────────────────────────────────
# Semántica de ausencia
#
# `ResultSimulation.variables` es un JSON: una corrida vieja, parcial o fallida
# puede no traer `IT`/`GT`/`TG`. Convertir esas ausencias en 0.0 hacía que la
# falta de datos se presentara como un hecho observado — un negocio que factura
# Bs 0.00 y pierde todos los días — y, peor, que una serie de ceros inventados
# tuviera volatilidad cero y sumara puntos de "estabilidad".
#
#   AUSENTE != 0 · INDEFINIDO != 0 · DESCONOCIDO != SANO
#
# Todo lo que no se observó vale None y se propaga como None hasta la vista,
# que debe mostrarlo como "no disponible".
# ─────────────────────────────────────────────────────────────────────────────

def _num(source: Dict[str, Any], key: str) -> Optional[float]:
    """Valor numérico observado, o None si no vino en la corrida."""
    value = source.get(key)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _observed(values) -> List[float]:
    """Sólo lo realmente observado."""
    return [v for v in values if v is not None]


def _sum_obs(values) -> Optional[float]:
    obs = _observed(values)
    return sum(obs) if obs else None


def _mean_obs(values) -> Optional[float]:
    obs = _observed(values)
    return float(np.mean(obs)) if obs else None


def _min_obs(values) -> Optional[float]:
    obs = _observed(values)
    return min(obs) if obs else None


def _max_obs(values) -> Optional[float]:
    obs = _observed(values)
    return max(obs) if obs else None


def _std_obs(values) -> Optional[float]:
    obs = _observed(values)
    return float(np.std(obs)) if len(obs) > 1 else (0.0 if obs else None)


def _ratio(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    """Cociente, o None si falta un término o el denominador lo deja indefinido."""
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def _gt(value: Optional[float], threshold: float) -> bool:
    """`value > threshold` que trata lo no observado como "no se cumple"."""
    return value is not None and value > threshold


def _lt(value: Optional[float], threshold: float) -> bool:
    """`value < threshold` que NO se dispara por un dato ausente."""
    return value is not None and value < threshold


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
    
    # MÉTODO ALTERNATIVO: Actualizar el método que genera las recomendaciones
    def _generate_dynamic_recommendations(self, simulation_instance, 
                                    totales_acumulativos, financial_results):
        """Generate dynamic recommendations based on simulation results - CORREGIDO"""
        recommendations = []
        business = simulation_instance.fk_questionary_result.fk_questionary.fk_product.fk_business
        
        # Get finance recommendations from database
        try:
            from finance.models import FinanceRecommendation
            db_recommendations = FinanceRecommendation.objects.filter(
                fk_business=business,
                is_active=True
            ).order_by('threshold_value')
        except Exception as e:
            logger.error(f"Error getting database recommendations: {e}")
            db_recommendations = []
        
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
                        'title': rec.name,  # AGREGADO: title explícito
                        'description': rec.description or rec.recommendation,
                        'recommendation': rec.recommendation,
                        'severity': min(100, severity),
                        'metric_value': value,  # CORREGIDO: usar metric_value en lugar de data
                        'threshold': threshold,
                        'value': value,  # AGREGADO: campo value
                        'variable': rec.variable_name,
                        'category': 'financial',  # AGREGADO: categoría por defecto
                        'priority': 'high' if severity > 50 else 'medium' if severity > 20 else 'low',
                        'impact': 'high' if severity > 50 else 'medium' if severity > 20 else 'low',
                        'actions': [rec.recommendation] if rec.recommendation else []  # AGREGADO
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
                        'title': 'Eficiencia de Ventas Baja',
                        'description': f'Solo se está vendiendo el {efficiency:.1f}% de la producción',
                        'recommendation': 'Revisar estrategias de ventas y marketing. Considerar promociones o ajustar producción.',
                        'severity': 90 - efficiency,
                        'priority': 'high' if efficiency < 60 else 'medium',
                        'category': 'efficiency',
                        'variable': 'EFICIENCIA_VENTAS',
                        'metric_value': efficiency,
                        'value': efficiency,
                        'impact': 'high' if efficiency < 60 else 'medium',
                        'actions': [
                            'Revisar estrategias de ventas y marketing',
                            'Considerar promociones',
                            'Ajustar producción'
                        ]
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
                        'title': 'Margen de Ganancia Bajo',
                        'description': f'El margen de ganancia es solo {profit_margin:.1f}%',
                        'recommendation': 'Analizar estructura de costos y considerar optimizaciones o ajuste de precios.',
                        'severity': 80,
                        'priority': 'high',
                        'category': 'profitability',
                        'variable': 'MARGEN_GANANCIA',
                        'metric_value': profit_margin,
                        'value': profit_margin,
                        'impact': 'high',
                        'actions': [
                            'Analizar estructura de costos',
                            'Considerar optimizaciones',
                            'Ajustar precios'
                        ]
                    })
                elif profit_margin > 40:
                    recommendations.append({
                        'name': 'Excelente Margen de Ganancia',
                        'title': 'Excelente Margen de Ganancia',
                        'description': f'El margen de ganancia es {profit_margin:.1f}%',
                        'recommendation': 'Mantener estrategia actual. Considerar expansión o inversión en crecimiento.',
                        'severity': 20,
                        'priority': 'low',
                        'category': 'profitability',
                        'variable': 'MARGEN_GANANCIA',
                        'metric_value': profit_margin,
                        'value': profit_margin,
                        'impact': 'low',
                        'actions': [
                            'Mantener estrategia actual',
                            'Considerar expansión',
                            'Invertir en crecimiento'
                        ]
                    })
        
        # 3. Growth Analysis
        if 'growth_rate' in financial_results:
            growth = financial_results['growth_rate']
            if growth < -5:
                recommendations.append({
                    'name': 'Tendencia Negativa en Demanda',
                    'title': 'Tendencia Negativa en Demanda',
                    'description': f'La demanda muestra una caída del {abs(growth):.1f}%',
                    'recommendation': 'Implementar estrategias de retención y recuperación de clientes. Revisar competitividad.',
                    'severity': min(100, abs(growth) * 2),
                    'priority': 'high',
                    'category': 'trends',
                    'variable': 'CRECIMIENTO',
                    'metric_value': growth,
                    'value': growth,
                    'impact': 'high',
                    'actions': [
                        'Implementar estrategias de retención de clientes',
                        'Estrategias de recuperación',
                        'Revisar competitividad'
                    ]
                })
            elif growth > 20:
                recommendations.append({
                    'name': 'Crecimiento Acelerado',
                    'title': 'Crecimiento Acelerado',
                    'description': f'La demanda crece al {growth:.1f}%',
                    'recommendation': 'Preparar infraestructura para expansión. Asegurar capital de trabajo suficiente.',
                    'severity': 30,
                    'priority': 'medium',
                    'category': 'trends',
                    'variable': 'CRECIMIENTO',
                    'metric_value': growth,
                    'value': growth,
                    'impact': 'medium',
                    'actions': [
                        'Preparar infraestructura para expansión',
                        'Asegurar capital de trabajo',
                        'Planificar crecimiento'
                    ]
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
                
                # Cada campo vale None si la corrida no lo trajo. Antes se leían
                # con `.get(clave, 0)`, así que una corrida sin variables
                # financieras producía un día completo de ceros indistinguible
                # de un día realmente malo.
                financial_data = {
                    'day': idx + 1,
                    'date': result.date,
                    # Revenue
                    'revenue': _num(vars, 'IT'),
                    'expected_revenue': _num(vars, 'IE'),
                    # Costs
                    'operating_costs': _num(vars, 'GO'),
                    'general_expenses': _num(vars, 'GG'),
                    'total_costs': _num(vars, 'TG'),
                    'material_costs': _num(vars, 'CTAI'),
                    'transport_costs': _num(vars, 'CTTL'),
                    'storage_costs': _num(vars, 'CA'),
                    'wastage_costs': _num(vars, 'CTM'),
                    # Profit
                    'gross_profit': _num(vars, 'IB'),
                    'net_profit': _num(vars, 'GT'),
                    # Margins
                    'gross_margin': _num(vars, 'MB'),
                    'net_margin': _num(vars, 'NR'),
                    # Other metrics
                    'roi': _num(vars, 'RI'),
                    'break_even': _num(vars, 'PED'),
                    'cost_efficiency': _num(vars, 'COST_EFFICIENCY'),
                    # Operational data for context
                    'sales_volume': _num(vars, 'TPV'),
                    'price': _num(vars, 'PVP'),
                    'demand': float(result.demand_mean),
                }
                
                # Sin ingresos observados el ratio es indefinido, no 0.
                financial_data['cost_ratio'] = _ratio(
                    financial_data['total_costs'], financial_data['revenue']
                )
                # EBITDA is not derivable from gross profit and operating
                # costs without an explicit depreciation/amortization policy.
                financial_data['ebitda'] = _num(vars, 'EBITDA')
                
                daily_financials.append(financial_data)
        
        return daily_financials
    
    def _analyze_profitability(self, daily_financials: List[Dict]) -> Dict[str, Any]:
        """Analyze profitability metrics and patterns"""
        if not daily_financials:
            return {}
        
        # Se agrega SÓLO lo observado y se declara sobre cuántos días se agregó,
        # para que la vista pueda decir "X de Y días" en vez de insinuar que la
        # serie está completa.
        revenues = [d['revenue'] for d in daily_financials]
        net_profits = [d['net_profit'] for d in daily_financials]
        gross_margins = _observed(d['gross_margin'] for d in daily_financials)
        net_margins = _observed(d['net_margin'] for d in daily_financials)
        roi_values = _observed(d['roi'] for d in daily_financials)
        ebitda_values = _observed(d['ebitda'] for d in daily_financials)

        observed_profits = _observed(net_profits)
        observed_revenues = _observed(revenues)

        total_revenue = _sum_obs(revenues)
        total_profit = _sum_obs(net_profits)

        # Días rentables/con pérdida se cuentan sobre lo observado. Un día sin
        # datos no es un día con pérdida.
        profitable_days = sum(1 for p in observed_profits if p > 0)
        loss_days = sum(1 for p in observed_profits if p <= 0)

        # Volatilidad: indefinida sin observaciones; una sola observación no
        # tiene dispersión que medir.
        if len(observed_profits) > 1:
            mean_profit = float(np.mean(observed_profits))
            profit_cv = (float(np.std(observed_profits)) / abs(mean_profit)
                         if mean_profit != 0 else None)
        else:
            profit_cv = None

        # Break-even sobre la serie observada.
        break_even_day = None
        cumulative_profit = 0.0
        for daily in daily_financials:
            if daily['net_profit'] is None:
                continue
            cumulative_profit += daily['net_profit']
            if cumulative_profit > 0:
                break_even_day = daily['day']
                break
        
        return {
            'total_revenue': total_revenue,
            'total_profit': total_profit,
            'observed_days': len(observed_profits),
            'total_days': len(daily_financials),
            'average_revenue_per_day': _mean_obs(revenues),
            'average_profit_per_day': _mean_obs(net_profits),
            'gross_margin': {
                'average': _mean_obs(gross_margins),
                'min': _min_obs(gross_margins),
                'max': _max_obs(gross_margins),
                'std': _std_obs(gross_margins)
            },
            'net_margin': {
                'average': _mean_obs(net_margins),
                'min': _min_obs(net_margins),
                'max': _max_obs(net_margins),
                'std': _std_obs(net_margins)
            },
            'profitable_days': profitable_days,
            'loss_days': loss_days,
            'profitability_rate': (profitable_days / len(observed_profits)
                                   if observed_profits else None),
            'profit_volatility': profit_cv,
            'break_even_day': break_even_day,
            'roi_average': _mean_obs(roi_values),
            'ebitda_total': _sum_obs(ebitda_values),
            'observed_revenue_days': len(observed_revenues)
        }
    
    def _analyze_costs(self, daily_financials: List[Dict]) -> Dict[str, Any]:
        """Analyze cost structure and efficiency"""
        if not daily_financials:
            return {}
        
        operating_costs = [d['operating_costs'] for d in daily_financials]
        material_costs = [d['material_costs'] for d in daily_financials]
        general_expenses = [d['general_expenses'] for d in daily_financials]
        transport_costs = [d['transport_costs'] for d in daily_financials]
        total_costs = [d['total_costs'] for d in daily_financials]
        
        total_operating = _sum_obs(operating_costs)
        total_materials = _sum_obs(material_costs)
        total_general = _sum_obs(general_expenses)
        total_transport = _sum_obs(transport_costs)
        total_all_costs = _sum_obs(total_costs)
        
        # Una participación sobre un total no observado es indefinida, no 0%.
        cost_structure = {
            'operating': _ratio(total_operating, total_all_costs),
            'materials': _ratio(total_materials, total_all_costs),
            'general': _ratio(total_general, total_all_costs)
        }
        
        # Variable vs fijo: sólo con ambos componentes observados.
        variable_costs = _sum_obs(
            [(d['material_costs'] + d['transport_costs'])
             if d['material_costs'] is not None and d['transport_costs'] is not None
             else None
             for d in daily_financials]
        )
        fixed_costs = (total_all_costs - variable_costs
                       if total_all_costs is not None and variable_costs is not None
                       else None)
        
        cost_to_revenue_ratios = _observed(d['cost_ratio'] for d in daily_financials)
        total_sales_volume = _sum_obs(d['sales_volume'] for d in daily_financials)
        
        return {
            'total_costs': total_all_costs,
            'observed_days': len(_observed(total_costs)),
            'total_days': len(daily_financials),
            'average_daily_cost': _mean_obs(total_costs),
            'cost_structure': cost_structure,
            'cost_breakdown': {
                'operating': total_operating,
                'materials': total_materials,
                'general': total_general,
                'transport': total_transport,
                'storage': _sum_obs(d['storage_costs'] for d in daily_financials),
                'wastage': _sum_obs(d['wastage_costs'] for d in daily_financials)
            },
            'variable_vs_fixed': {
                'variable_costs': variable_costs,
                'fixed_costs': fixed_costs,
                'variable_ratio': _ratio(variable_costs, total_all_costs)
            },
            'cost_efficiency': {
                'average_cost_ratio': _mean_obs(cost_to_revenue_ratios),
                'best_cost_ratio': _min_obs(cost_to_revenue_ratios),
                'worst_cost_ratio': _max_obs(cost_to_revenue_ratios)
            },
            'cost_per_unit': {
                'average': _ratio(total_all_costs, total_sales_volume)
            }
        }
    
    def _analyze_efficiency(self, daily_financials: List[Dict]) -> Dict[str, Any]:
        """Analyze operational and financial efficiency"""
        if not daily_financials:
            return {}
        
        cost_efficiencies = [d['cost_efficiency'] for d in daily_financials]
        
        # Por unidad: sólo con volumen vendido observado y > 0.
        revenue_per_unit = []
        cost_per_unit = []
        for d in daily_financials:
            unit_revenue = _ratio(d['revenue'], d['sales_volume'])
            if unit_revenue is not None:
                revenue_per_unit.append(unit_revenue)
            unit_cost = _ratio(d['total_costs'], d['sales_volume'])
            if unit_cost is not None:
                cost_per_unit.append(unit_cost)
        
        avg_revenue_per_unit = _mean_obs(revenue_per_unit)
        avg_cost_per_unit = _mean_obs(cost_per_unit)
        
        return {
            'cost_efficiency': {
                'average': _mean_obs(cost_efficiencies),
                'trend': self._calculate_trend(_observed(cost_efficiencies))
            },
            'revenue_per_unit': {
                'average': avg_revenue_per_unit,
                'min': _min_obs(revenue_per_unit),
                'max': _max_obs(revenue_per_unit)
            },
            'cost_per_unit': {
                'average': avg_cost_per_unit,
                'trend': (self._calculate_trend(cost_per_unit)
                          if len(cost_per_unit) > 2 else 'insufficient_data')
            },
            'contribution_margin': {
                'per_unit': (avg_revenue_per_unit - avg_cost_per_unit
                             if avg_revenue_per_unit is not None
                             and avg_cost_per_unit is not None else None)
            },
            'operational_leverage': self._calculate_operational_leverage(daily_financials)
        }
    
    def _analyze_trends(self, daily_financials: List[Dict]) -> Dict[str, Any]:
        """Analyze financial trends over the simulation period"""
        if len(daily_financials) < 3:
            return {'status': 'insufficient_data'}
        
        # Las tendencias se calculan sobre la serie observada; una serie con
        # huecos rellenados de ceros inventaba caídas y recuperaciones.
        revenues = _observed(d['revenue'] for d in daily_financials)
        profits = _observed(d['net_profit'] for d in daily_financials)
        costs = _observed(d['total_costs'] for d in daily_financials)
        margins = _observed(d['net_margin'] for d in daily_financials)

        mean_revenue = _mean_obs(revenues)
        mean_profit = _mean_obs(profits)
        
        return {
            'observed_days': len(profits),
            'total_days': len(daily_financials),
            'revenue_trend': {
                'direction': self._calculate_trend(revenues),
                'growth_rate': self._calculate_growth_rate(revenues),
                'volatility': (float(np.std(revenues)) / mean_revenue
                               if mean_revenue not in (None, 0) and len(revenues) > 1
                               else None)
            },
            'profit_trend': {
                'direction': self._calculate_trend(profits),
                'improvement_rate': self._calculate_improvement_rate(profits),
                'stability': (1 - (float(np.std(profits)) / (abs(mean_profit) + 0.01))
                              if mean_profit is not None and len(profits) > 1 else None)
            },
            'cost_trend': {
                'direction': self._calculate_trend(costs),
                'growth_rate': self._calculate_growth_rate(costs),
                'as_pct_of_revenue': self._calculate_cost_revenue_trend(
                    [d['total_costs'] for d in daily_financials],
                    [d['revenue'] for d in daily_financials])
            },
            'margin_trend': {
                'direction': self._calculate_trend(margins),
                'improvement': (margins[-1] - margins[0]) if len(margins) > 1 else None,
                'consistency': (1 - float(np.std(margins))) if len(margins) > 1 else None
            },
            'sustainability': self._assess_trend_sustainability(daily_financials)
        }
    
    def _calculate_financial_kpis(self, daily_financials: List[Dict]) -> Dict[str, Any]:
        """Calculate key financial performance indicators"""
        if not daily_financials:
            return {}
        
        revenues = [d['revenue'] for d in daily_financials]
        net_profits = [d['net_profit'] for d in daily_financials]
        all_costs = [d['total_costs'] for d in daily_financials]

        total_revenue = _sum_obs(revenues)
        total_profit = _sum_obs(net_profits)
        total_costs = _sum_obs(all_costs)
        
        margins = _observed(d['net_margin'] for d in daily_financials)
        roi_values = _observed(d['roi'] for d in daily_financials)
        
        # "Mejor" y "peor" día sólo existen si hubo utilidades observadas.
        days_with_profit = [d for d in daily_financials if d['net_profit'] is not None]
        best_day = max(days_with_profit, key=lambda x: x['net_profit']) if days_with_profit else None
        worst_day = min(days_with_profit, key=lambda x: x['net_profit']) if days_with_profit else None

        total_demand = _sum_obs(d['demand'] for d in daily_financials)
        total_sales_volume = _sum_obs(d['sales_volume'] for d in daily_financials)
        
        return {
            'total_revenue': total_revenue,
            'total_profit': total_profit,
            'total_costs': total_costs,
            'observed_days': len(days_with_profit),
            'total_days': len(daily_financials),
            'average_daily_revenue': _mean_obs(revenues),
            'average_daily_profit': _mean_obs(net_profits),
            # Sin ingresos observados el margen es indefinido, no 0%.
            'profit_margin': _ratio(total_profit, total_revenue),
            'average_margin': _mean_obs(margins),
            'roi': _mean_obs(roi_values),
            'best_day_profit': best_day['net_profit'] if best_day else None,
            'best_day_number': best_day['day'] if best_day else None,
            'worst_day_profit': worst_day['net_profit'] if worst_day else None,
            'worst_day_number': worst_day['day'] if worst_day else None,
            'revenue_per_demand': _ratio(total_revenue, total_demand),
            'cost_per_unit_sold': _ratio(total_costs, total_sales_volume)
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
        
        # Sin observaciones no se puede afirmar ni riesgo alto ni bajo.
        if not profitability or profitability.get('observed_days') == 0:
            risks['overall_risk'] = 'unknown'
            risks['risk_factors'].append({
                'factor': 'no_financial_data',
                'description': 'La corrida no registró variables financieras; '
                               'no se puede evaluar el riesgo',
                'severity': 'unknown'
            })
            return risks
        
        risk_score = 0
        
        # Profitability risk. Los umbrales sólo se evalúan sobre métricas
        # observadas: un dato ausente no dispara ni silencia una alerta.
        if _lt(profitability.get('profitability_rate'), 0.7):
            risk_score += 30
            risks['risk_factors'].append({
                'factor': 'low_profitability',
                'description': 'Baja tasa de días rentables',
                'severity': 'high'
            })
        
        # Volatility risk
        if _gt(profitability.get('profit_volatility'), 0.5):
            risk_score += 20
            risks['risk_factors'].append({
                'factor': 'high_volatility',
                'description': 'Alta volatilidad en ganancias',
                'severity': 'medium'
            })
        
        # Cost structure risk
        if _lt(costs.get('variable_vs_fixed', {}).get('variable_ratio'), 0.3):
            risk_score += 15
            risks['risk_factors'].append({
                'factor': 'high_fixed_costs',
                'description': 'Estructura de costos muy rígida',
                'severity': 'medium'
            })
        
        # Margin risk. `.get('average', 0)` devolvía None cuando la clave existía
        # con valor None, y `None < 0.05` reventaba con TypeError.
        if _lt(profitability.get('net_margin', {}).get('average'), 0.05):
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
            # Se propaga None: la vista debe mostrar "no disponible", no Bs 0.00.
            'key_metrics': {
                'total_revenue': kpis.get('total_revenue'),
                'total_profit': kpis.get('total_profit'),
                'profit_margin': kpis.get('profit_margin'),
                'roi': kpis.get('roi'),
                'observed_days': kpis.get('observed_days'),
                'total_days': kpis.get('total_days')
            },
            'highlights': self._generate_highlights(kpis, profitability),
            'concerns': self._generate_concerns(profitability, risk_assessment),
            'outlook': self._generate_outlook(profitability, risk_assessment)
        }
    
    # Helper methods
    
    def _calculate_trend(self, data: List[float]) -> str:
        """Calculate trend direction from time series data"""
        data = _observed(data or [])
        if len(data) < 3:
            return 'insufficient_data'
        # Una serie constante no tiene pendiente definida: linregress devuelve
        # NaN y la comparación posterior mentiría en vez de fallar.
        if len(set(data)) == 1:
            return 'stable'
        
        x = np.arange(len(data))
        slope, _, r_value, p_value, _ = stats.linregress(x, data)
        if p_value is None or np.isnan(p_value):
            return 'stable'
        
        if p_value > 0.05:  # Not statistically significant
            return 'stable'
        elif slope > 0:
            return 'increasing'
        else:
            return 'declining'
    
    def _calculate_growth_rate(self, data: List[float]) -> Optional[float]:
        """Calculate average growth rate"""
        data = _observed(data or [])
        # Sin dos observaciones, o partiendo de cero, la tasa es indefinida —
        # no 0%, que se leía como "no creció".
        if len(data) < 2 or data[0] == 0:
            return None
        base = data[-1] / data[0]
        if base < 0:
            return None
        
        # Compound growth rate
        return ((base) ** (1 / (len(data) - 1)) - 1) * 100
    
    def _calculate_growth_rate_between_values(self, initial: float, final: float) -> float:
        """Calculate growth rate between two specific values"""
        if initial == 0:
            return 0.0 if final == 0 else float('inf')
        return (final - initial) / initial
    
    def _calculate_improvement_rate(self, data: List[float]) -> Optional[float]:
        """Calculate improvement rate for metrics that can be negative"""
        data = _observed(data or [])
        if len(data) < 2:
            return None
        
        return (data[-1] - data[0]) / len(data)
    
    def _calculate_cost_revenue_trend(self, costs: List[float], 
                                    revenues: List[float]) -> str:
        """Analyze trend of costs as percentage of revenue"""
        if len(costs) != len(revenues) or not revenues:
            return 'unknown'
        
        ratios = _observed(_ratio(c, r) for c, r in zip(costs, revenues))
        if not ratios:
            return 'unknown'
        
        return self._calculate_trend(ratios)
    
    def _calculate_operational_leverage(self, daily_financials: List[Dict]) -> Optional[float]:
        """Calculate degree of operational leverage"""
        if len(daily_financials) < 2:
            return None
        
        # Simplified: compare profit changes to revenue changes. Sólo se
        # comparan días consecutivos con AMBOS valores observados; antes un
        # hueco rellenado de ceros producía un salto ficticio.
        leverages = []
        for prev, curr in zip(daily_financials, daily_financials[1:]):
            if None in (prev['revenue'], curr['revenue'],
                        prev['net_profit'], curr['net_profit']):
                continue
            revenue_change = curr['revenue'] - prev['revenue']
            profit_change = curr['net_profit'] - prev['net_profit']
            if revenue_change == 0:
                continue
            leverages.append(abs(profit_change / revenue_change))
        
        # Sin pares comparables el apalancamiento es indefinido. Devolver 1.0
        # afirmaba una relación 1:1 que nadie midió.
        if not leverages:
            return None
        
        return float(np.median(leverages))
    
    def _assess_trend_sustainability(self, daily_financials: List[Dict]) -> str:
        """Assess if current trends are sustainable"""
        if len(daily_financials) < 7:
            return 'insufficient_data'
        
        # Check recent trends (last 7 days)
        recent_profits = _observed(d['net_profit'] for d in daily_financials[-7:])
        recent_margins = _observed(d['net_margin'] for d in daily_financials[-7:])

        if len(recent_margins) < 3 or len(recent_profits) < 2:
            return 'insufficient_data'
        
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
        # Sin ninguna observación financiera no hay salud que calificar. Antes
        # se caía a 'poor'/'fair' por acumulación de ceros, y peor: una serie de
        # ceros inventados tiene volatilidad 0, así que la AUSENCIA de datos
        # sumaba los 20 puntos de "estabilidad".
        observed = profitability.get('observed_days')
        if observed == 0 or (observed is None and not kpis):
            return 'unknown'

        health_score = 0
        
        # Profitability check
        profit_margin = kpis.get('profit_margin')
        if _gt(profit_margin, 0.15):
            health_score += 30
        elif _gt(profit_margin, 0.05):
            health_score += 15
        
        # Stability check — sólo si la volatilidad se midió de verdad.
        if _lt(profitability.get('profit_volatility'), 0.3):
            health_score += 20
        
        # Risk check
        if risk_assessment.get('overall_risk') == 'low':
            health_score += 30
        elif risk_assessment.get('overall_risk') == 'medium':
            health_score += 15
        
        # ROI check
        roi = kpis.get('roi')
        if _gt(roi, 0.2):
            health_score += 20
        elif _gt(roi, 0.1):
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
        
        # Nada se celebra sobre una métrica que no se observó.
        if _gt(kpis.get('profit_margin'), 0.15):
            highlights.append(f"Excelente margen de ganancia: {kpis['profit_margin']:.1%}")
        
        if _gt(profitability.get('profitability_rate'), 0.8):
            rate = profitability['profitability_rate'] * 100
            highlights.append(f"{rate:.0f}% de días fueron rentables")
        
        if _gt(kpis.get('roi'), 0.2):
            highlights.append(f"Alto retorno de inversión: {kpis['roi']:.1%}")
        
        if profitability.get('break_even_day'):
            highlights.append(f"Punto de equilibrio alcanzado en día {profitability['break_even_day']}")
        
        return highlights
    
    def _generate_concerns(self, profitability: Dict, 
                         risk_assessment: Dict) -> List[str]:
        """Generate concerns from analysis"""
        concerns = []
        
        if profitability.get('observed_days') == 0:
            concerns.append(
                "La corrida no registró variables financieras: no hay resultados "
                "económicos que analizar")
            return concerns

        if profitability.get('loss_days', 0) > profitability.get('profitable_days', 1):
            concerns.append("Más días con pérdidas que con ganancias")
        
        if risk_assessment.get('overall_risk') == 'high':
            concerns.append("Nivel de riesgo financiero alto")
        
        if _gt(profitability.get('profit_volatility'), 0.5):
            concerns.append("Alta volatilidad en las ganancias")
        
        if not profitability.get('break_even_day'):
            concerns.append("No se alcanzó el punto de equilibrio")
        
        return concerns
    
    def _generate_outlook(self, profitability: Dict, 
                        risk_assessment: Dict) -> str:
        """Generate business outlook statement"""
        if profitability.get('observed_days') == 0:
            return ('No hay datos financieros en esta corrida; no se puede '
                    'emitir una perspectiva del negocio')
        if risk_assessment.get('overall_risk') == 'high':
            return 'El negocio enfrenta desafíos significativos que requieren acción inmediata'
        elif _gt(profitability.get('profitability_rate'), 0.7):
            return 'El negocio muestra buen desempeño con oportunidades de mejora'
        else:
            return 'Se requieren ajustes operativos para mejorar la rentabilidad'
    
    def _save_recommendations_to_db(self, simulation: Simulation,
                            recommendations: List[Dict],
                            business: Business) -> None:
        """Save financial recommendations to database - CORREGIDO"""
        try:
            logger.info(f"Attempting to save {len(recommendations[:5])} recommendations")
            
            # Importar aquí para evitar importación circular
            from finance.models import FinanceRecommendationSimulation
            
            for i, rec in enumerate(recommendations[:5]):
                logger.info(f"Processing recommendation {i+1}: {rec}")
                
                try:
                    # Preparar datos para creación
                    creation_data = {
                        'fk_simulation': simulation,
                        'category': rec.get('category', 'financial'),
                        'severity': rec.get('severity', 'medium'),
                        'title': rec.get('title', rec.get('name', 'Recomendación Financiera')),
                        'description': rec.get('description', ''),
                        'recommendation': rec.get('recommendation', rec.get('actions', [])),
                        'impact': rec.get('impact', 'medium'),
                        'priority': rec.get('priority', 'medium'),
                        'variable': rec.get('variable', ''),
                        'is_active': True
                    }
                    
                    # Manejar metric_value/data
                    if 'metric_value' in rec:
                        try:
                            metric_value = float(rec['metric_value'])
                            creation_data['metric_value'] = metric_value
                            creation_data['data'] = metric_value  # Para compatibilidad
                            logger.info(f"Using metric_value: {metric_value}")
                        except (ValueError, TypeError) as ve:
                            logger.error(f"Error converting metric_value to float: {rec['metric_value']} - {ve}")
                            creation_data['metric_value'] = 0.0
                            creation_data['data'] = 0.0
                    
                    # Fallback para 'data' si no hay 'metric_value'
                    elif 'data' in rec:
                        try:
                            data_value = float(rec['data'])
                            creation_data['data'] = data_value
                            creation_data['metric_value'] = data_value  # Sincronizar
                            logger.info(f"Using data: {data_value}")
                        except (ValueError, TypeError) as ve:
                            logger.error(f"Error converting data to float: {rec['data']} - {ve}")
                            creation_data['data'] = 0.0
                            creation_data['metric_value'] = 0.0
                    
                    # Manejar campos opcionales
                    if 'threshold' in rec:
                        try:
                            creation_data['threshold'] = float(rec['threshold'])
                        except (ValueError, TypeError):
                            creation_data['threshold'] = None
                    
                    if 'value' in rec:
                        try:
                            creation_data['value'] = float(rec['value'])
                        except (ValueError, TypeError):
                            creation_data['value'] = None
                    
                    # Manejar actions (convertir lista a string si es necesario)
                    if 'actions' in rec:
                        actions = rec['actions']
                        if isinstance(actions, list):
                            creation_data['actions'] = actions
                            # También guardar como texto en recommendation si está vacío
                            if not creation_data.get('recommendation'):
                                creation_data['recommendation'] = '; '.join(actions) if actions else ''
                        elif isinstance(actions, str):
                            creation_data['recommendation'] = actions
                            creation_data['actions'] = [actions]
                    
                    # Crear la instancia
                    sim_rec = FinanceRecommendationSimulation.objects.create(**creation_data)
                    logger.info(f"Successfully created FinanceRecommendationSimulation ID: {sim_rec.id}")
                    
                except Exception as creation_error:
                    logger.error(f"Error creating FinanceRecommendationSimulation: {creation_error}")
                    logger.error(f"Attempted data: {creation_data}")
                    
                    # Crear registro mínimo en caso de error
                    try:
                        minimal_data = {
                            'fk_simulation': simulation,
                            'title': rec.get('title', rec.get('name', 'Error en recomendación')),
                            'description': f"Error al procesar: {str(creation_error)}",
                            'category': 'financial',
                            'severity': 'medium',
                            'is_active': True
                        }
                        FinanceRecommendationSimulation.objects.create(**minimal_data)
                        logger.info("Created minimal recommendation record after error")
                    except Exception as minimal_error:
                        logger.error(f"Failed to create even minimal record: {minimal_error}")
                        
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
                    'roi': analysis['kpis'].get('roi'),
                    'risk_level': analysis['risk_assessment']['overall_risk'],
                    'health_status': analysis['summary']['status']
                })
        
        if not comparisons:
            return {'error': 'No valid simulations for comparison'}
        
        # Find best performer
        best_profit = max(comparisons, key=lambda x: x['total_profit'])
        best_margin = max(comparisons, key=lambda x: x['profit_margin'])
        roi_comparisons = [item for item in comparisons if item.get('roi') is not None]
        best_roi = max(roi_comparisons, key=lambda x: x['roi']) if roi_comparisons else None
        
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
