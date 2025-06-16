# utils/chart_utils.py
"""
Enhanced chart generation utilities for simulation results.
Focuses on daily comparisons and trend analysis.
"""
import base64
import logging
from io import BytesIO
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
import seaborn as sns
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


class ChartGenerator:
    """Enhanced chart generator for simulation visualization"""
    
    def __init__(self):
        self.default_figsize = (12, 6)
        self.dpi = 100
        self.color_palette = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e',
            'success': '#2ca02c',
            'danger': '#d62728',
            'warning': '#ff9800',
            'info': '#17a2b8',
            'historical': '#7f7f7f',
            'simulated': '#1f77b4',
            'real': '#2ca02c'
        }
    
    def generate_all_charts(self, simulation_id: int, 
                          simulation_instance: Any,
                          results: List[Any],
                          historical_demand: List[float]) -> Dict[str, Any]:
        """Generate all charts for simulation results"""
        try:
            # Extract data for charts
            dates = [r.date for r in results]
            daily_data = self._extract_daily_data(results)
            
            # Calculate accumulated totals
            totales_acumulativos = self._calculate_accumulated_totals(daily_data)
            
            # Generate various charts
            charts = {
                'image_data_simulation': self._generate_simulation_overview_chart(
                    dates, daily_data, historical_demand
                ),
                'image_data_ingresos_gastos': self._generate_income_expenses_chart(
                    dates, daily_data
                ),
                'image_data_produccion_ventas': self._generate_production_sales_chart(
                    dates, daily_data
                ),
                'image_data_inventarios': self._generate_inventory_chart(
                    dates, daily_data
                ),
                'image_data_eficiencia': self._generate_efficiency_chart(
                    dates, daily_data
                ),
                'image_data_rentabilidad': self._generate_profitability_chart(
                    dates, daily_data
                ),
                'image_data_demanda_comparativa': self._generate_demand_comparison_chart(
                    dates, daily_data, historical_demand
                ),
                'image_data_kpis': self._generate_kpi_dashboard(
                    daily_data, totales_acumulativos
                )
            }
            
            # Add chart images to return dict
            return {
                'chart_images': charts,
                'totales_acumulativos': totales_acumulativos,
                'all_variables_extracted': daily_data
            }
            
        except Exception as e:
            logger.error(f"Error generating charts: {str(e)}")
            return {
                'chart_images': {},
                'totales_acumulativos': {},
                'all_variables_extracted': []
            }
    
    def _extract_daily_data(self, results: List[Any]) -> List[Dict[str, Any]]:
        """Extract daily data from results"""
        daily_data = []
        
        for idx, result in enumerate(results):
            day_data = {
                'day': idx + 1,
                'date': result.date,
                'demand_mean': float(result.demand_mean),
                'demand_std': float(result.demand_std_deviation)
            }
            
            # Add all variables
            if hasattr(result, 'variables') and result.variables:
                for key, value in result.variables.items():
                    if not key.startswith('_'):
                        try:
                            day_data[key] = float(value) if isinstance(value, (int, float)) else value
                        except:
                            day_data[key] = 0.0
            
            daily_data.append(day_data)
        
        return daily_data
    
    def _calculate_accumulated_totals(self, daily_data: List[Dict]) -> Dict[str, Dict]:
        """Calculate accumulated totals for key variables"""
        totals = {}
        
        # Variables to accumulate
        accumulate_vars = [
            'IT', 'GT', 'GO', 'TG', 'TPV', 'TPPRO', 'DI',
            'CTAI', 'CTTL', 'CA', 'MP', 'MI'
        ]
        
        for var in accumulate_vars:
            total = sum(day.get(var, 0) for day in daily_data)
            avg = total / len(daily_data) if daily_data else 0
            
            totals[var] = {
                'total': total,
                'average': avg,
                'count': len(daily_data)
            }
        
        # Add descriptive names
        var_names = {
            'IT': 'INGRESOS TOTALES',
            'GT': 'GANANCIAS TOTALES',
            'GO': 'GASTOS OPERATIVOS',
            'TG': 'GASTOS TOTALES',
            'TPV': 'TOTAL PRODUCTOS VENDIDOS',
            'TPPRO': 'TOTAL PRODUCTOS PRODUCIDOS',
            'DI': 'DEMANDA INSATISFECHA'
        }
        
        for code, name in var_names.items():
            if code in totals:
                totals[name] = totals[code]
        
        return totals
    
    def _generate_simulation_overview_chart(self, dates: List, 
                                          daily_data: List[Dict],
                                          historical_demand: List[float]) -> str:
        """Generate overview chart showing key metrics"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        days = list(range(1, len(daily_data) + 1))
        
        # 1. Demand Evolution
        demands = [d['demand_mean'] for d in daily_data]
        ax1.plot(days, demands, 'b-', linewidth=2, label='Demanda Simulada')
        
        if historical_demand:
            hist_days = list(range(-len(historical_demand), 0))
            ax1.plot(hist_days, historical_demand, 'gray', alpha=0.7, 
                    linewidth=2, label='Demanda Histórica')
            ax1.axvline(x=0, color='red', linestyle='--', alpha=0.5)
        
        ax1.set_xlabel('Días')
        ax1.set_ylabel('Demanda (L)')
        ax1.set_title('Evolución de la Demanda')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Sales Performance
        sales = [d.get('TPV', 0) for d in daily_data]
        service_level = [d.get('NSC', 0) * 100 for d in daily_data]
        
        ax2_twin = ax2.twinx()
        l1 = ax2.plot(days, sales, 'g-', linewidth=2, label='Ventas')
        l2 = ax2_twin.plot(days, service_level, 'r--', linewidth=2, label='Nivel Servicio %')
        
        ax2.set_xlabel('Días')
        ax2.set_ylabel('Ventas (L)', color='g')
        ax2_twin.set_ylabel('Nivel Servicio (%)', color='r')
        ax2.set_title('Desempeño de Ventas')
        
        # Combine legends
        lns = l1 + l2
        labs = [l.get_label() for l in lns]
        ax2.legend(lns, labs, loc='best')
        ax2.grid(True, alpha=0.3)
        
        # 3. Financial Performance
        revenue = [d.get('IT', 0) for d in daily_data]
        profit = [d.get('GT', 0) for d in daily_data]
        
        ax3.plot(days, revenue, 'b-', linewidth=2, label='Ingresos')
        ax3.plot(days, profit, 'g-', linewidth=2, label='Ganancias')
        ax3.fill_between(days, 0, profit, where=[p > 0 for p in profit],
                        color='green', alpha=0.3, label='Ganancia')
        ax3.fill_between(days, profit, 0, where=[p < 0 for p in profit],
                        color='red', alpha=0.3, label='Pérdida')
        
        ax3.set_xlabel('Días')
        ax3.set_ylabel('Monto (Bs)')
        ax3.set_title('Desempeño Financiero')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. Efficiency Metrics
        production_eff = [d.get('EP', 0) * 100 for d in daily_data]
        overall_eff = [d.get('EOG', 0) * 100 for d in daily_data]
        
        ax4.plot(days, production_eff, 'b-', linewidth=2, label='Eficiencia Producción')
        ax4.plot(days, overall_eff, 'r-', linewidth=2, label='Eficiencia Global')
        ax4.axhline(y=80, color='green', linestyle='--', alpha=0.5, label='Meta 80%')
        
        ax4.set_xlabel('Días')
        ax4.set_ylabel('Eficiencia (%)')
        ax4.set_title('Indicadores de Eficiencia')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        ax4.set_ylim(0, 110)
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _generate_income_expenses_chart(self, dates: List, 
                                      daily_data: List[Dict]) -> str:
        """Generate income vs expenses chart"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.default_figsize, 
                                       sharex=True)
        
        days = list(range(1, len(daily_data) + 1))
        
        # Daily values
        income = [d.get('IT', 0) for d in daily_data]
        expenses = [d.get('TG', 0) for d in daily_data]
        profit = [d.get('GT', 0) for d in daily_data]
        
        # Plot daily
        ax1.plot(days, income, 'b-', linewidth=2, label='Ingresos')
        ax1.plot(days, expenses, 'r-', linewidth=2, label='Gastos')
        ax1.fill_between(days, income, expenses, 
                        where=[i > e for i, e in zip(income, expenses)],
                        color='green', alpha=0.3)
        ax1.fill_between(days, income, expenses,
                        where=[i <= e for i, e in zip(income, expenses)],
                        color='red', alpha=0.3)
        
        ax1.set_ylabel('Monto Diario (Bs)')
        ax1.set_title('Ingresos vs Gastos Diarios')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Cumulative profit
        cumulative_profit = np.cumsum(profit)
        ax2.plot(days, cumulative_profit, 'g-', linewidth=3)
        ax2.fill_between(days, 0, cumulative_profit,
                        where=[p > 0 for p in cumulative_profit],
                        color='green', alpha=0.3)
        ax2.fill_between(days, cumulative_profit, 0,
                        where=[p < 0 for p in cumulative_profit],
                        color='red', alpha=0.3)
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        
        ax2.set_xlabel('Días')
        ax2.set_ylabel('Ganancia Acumulada (Bs)')
        ax2.set_title('Ganancia Acumulada')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _generate_production_sales_chart(self, dates: List,
                                       daily_data: List[Dict]) -> str:
        """Generate production vs sales analysis"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.default_figsize)
        
        days = list(range(1, len(daily_data) + 1))
        
        # Production and sales
        production = [d.get('QPL', 0) for d in daily_data]
        sales = [d.get('TPV', 0) for d in daily_data]
        demand = [d.get('demand_mean', 0) for d in daily_data]
        
        # Daily comparison
        ax1.plot(days, demand, 'gray', linewidth=2, alpha=0.7, label='Demanda')
        ax1.plot(days, production, 'b-', linewidth=2, label='Producción')
        ax1.plot(days, sales, 'g-', linewidth=2, label='Ventas')
        
        ax1.fill_between(days, sales, demand,
                        where=[s < d for s, d in zip(sales, demand)],
                        color='red', alpha=0.2, label='Demanda Insatisfecha')
        
        ax1.set_xlabel('Días')
        ax1.set_ylabel('Cantidad (L)')
        ax1.set_title('Producción vs Ventas vs Demanda')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Efficiency analysis
        utilization = [d.get('FU', 0) * 100 for d in daily_data]
        productivity = [d.get('PE', 0) * 100 for d in daily_data]
        
        ax2.plot(days, utilization, 'b-', linewidth=2, label='Utilización Capacidad')
        ax2.plot(days, productivity, 'g-', linewidth=2, label='Productividad')
        ax2.axhline(y=85, color='red', linestyle='--', alpha=0.5, label='Meta 85%')
        
        ax2.set_xlabel('Días')
        ax2.set_ylabel('Porcentaje (%)')
        ax2.set_title('Indicadores de Producción')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(0, 110)
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _generate_inventory_chart(self, dates: List,
                                daily_data: List[Dict]) -> str:
        """Generate inventory analysis chart"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.default_figsize)
        
        days = list(range(1, len(daily_data) + 1))
        
        # Inventory levels
        finished_inv = [d.get('IPF', 0) for d in daily_data]
        raw_inv = [d.get('II', 0) for d in daily_data]
        
        # Optimal levels
        optimal_finished = [d.get('IOP', 0) for d in daily_data]
        optimal_raw = [d.get('IOI', 0) for d in daily_data]
        
        # Plot finished goods
        ax1.plot(days, finished_inv, 'b-', linewidth=2, label='Inventario Real')
        ax1.plot(days, optimal_finished, 'g--', linewidth=2, label='Inventario Óptimo')
        ax1.fill_between(days, finished_inv, optimal_finished,
                        where=[f > o for f, o in zip(finished_inv, optimal_finished)],
                        color='orange', alpha=0.3, label='Exceso')
        ax1.fill_between(days, finished_inv, optimal_finished,
                        where=[f < o for f, o in zip(finished_inv, optimal_finished)],
                        color='red', alpha=0.3, label='Déficit')
        
        ax1.set_ylabel('Productos Finales (L)')
        ax1.set_title('Inventario de Productos Terminados')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot raw materials
        ax2.plot(days, raw_inv, 'b-', linewidth=2, label='Inventario Real')
        ax2.plot(days, optimal_raw, 'g--', linewidth=2, label='Inventario Óptimo')
        
        # Add reorder points
        reorder_days = [i for i, d in enumerate(daily_data) if d.get('PI', 0) > 0]
        if reorder_days:
            reorder_amounts = [daily_data[i].get('PI', 0) for i in reorder_days]
            ax2.scatter([days[i] for i in reorder_days], 
                       [raw_inv[i] for i in reorder_days],
                       color='red', s=100, marker='v', label='Reorden')
        
        ax2.set_xlabel('Días')
        ax2.set_ylabel('Insumos (L)')
        ax2.set_title('Inventario de Materias Primas')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _generate_efficiency_chart(self, dates: List,
                                 daily_data: List[Dict]) -> str:
        """Generate comprehensive efficiency metrics chart"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        days = list(range(1, len(daily_data) + 1))
        
        # 1. Overall efficiency
        oee = [d.get('EOG', 0) * 100 for d in daily_data]
        ax1.plot(days, oee, 'b-', linewidth=2)
        ax1.fill_between(days, 0, oee, alpha=0.3)
        ax1.axhline(y=85, color='green', linestyle='--', alpha=0.5, label='World Class')
        ax1.set_xlabel('Días')
        ax1.set_ylabel('OEE (%)')
        ax1.set_title('Eficiencia Global del Equipo (OEE)')
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0, 100)
        
        # 2. Service level
        service = [d.get('NSC', 0) * 100 for d in daily_data]
        satisfaction = [d.get('ISC', 0) * 100 for d in daily_data]
        
        ax2.plot(days, service, 'g-', linewidth=2, label='Nivel de Servicio')
        ax2.plot(days, satisfaction, 'b-', linewidth=2, label='Satisfacción Cliente')
        ax2.axhline(y=95, color='red', linestyle='--', alpha=0.5, label='Meta 95%')
        ax2.set_xlabel('Días')
        ax2.set_ylabel('Porcentaje (%)')
        ax2.set_title('Métricas de Servicio al Cliente')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(0, 110)
        
        # 3. Resource utilization
        labor_eff = [(1 - d.get('HO', 0) / 480) * 100 for d in daily_data]
        capacity_util = [d.get('FU', 0) * 100 for d in daily_data]
        
        ax3.plot(days, labor_eff, 'purple', linewidth=2, label='Eficiencia Laboral')
        ax3.plot(days, capacity_util, 'orange', linewidth=2, label='Utilización Capacidad')
        ax3.set_xlabel('Días')
        ax3.set_ylabel('Porcentaje (%)')
        ax3.set_title('Utilización de Recursos')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        ax3.set_ylim(0, 110)
        
        # 4. Cost efficiency
        cost_eff = [d.get('COST_EFFICIENCY', 0) * 100 for d in daily_data]
        margin = [d.get('MB', 0) * 100 for d in daily_data]
        
        ax4.plot(days, cost_eff, 'r-', linewidth=2, label='Eficiencia de Costos')
        ax4.plot(days, margin, 'g-', linewidth=2, label='Margen Bruto')
        ax4.set_xlabel('Días')
        ax4.set_ylabel('Porcentaje (%)')
        ax4.set_title('Eficiencia Financiera')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _generate_profitability_chart(self, dates: List,
                                    daily_data: List[Dict]) -> str:
        """Generate profitability analysis chart"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.default_figsize)
        
        days = list(range(1, len(daily_data) + 1))
        
        # Daily margins
        gross_margin = [d.get('MB', 0) * 100 for d in daily_data]
        net_margin = [d.get('NR', 0) * 100 for d in daily_data]
        
        ax1.plot(days, gross_margin, 'b-', linewidth=2, label='Margen Bruto')
        ax1.plot(days, net_margin, 'g-', linewidth=2, label='Margen Neto')
        ax1.fill_between(days, 0, net_margin, 
                        where=[m > 0 for m in net_margin],
                        color='green', alpha=0.3)
        ax1.fill_between(days, net_margin, 0,
                        where=[m < 0 for m in net_margin],
                        color='red', alpha=0.3)
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        
        ax1.set_xlabel('Días')
        ax1.set_ylabel('Margen (%)')
        ax1.set_title('Evolución de Márgenes')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # ROI and break-even
        roi = [d.get('RI', 0) * 100 for d in daily_data]
        break_even = [d.get('PED', 0) for d in daily_data]
        actual_sales = [d.get('TPV', 0) for d in daily_data]
        
        ax2_twin = ax2.twinx()
        
        l1 = ax2.plot(days, actual_sales, 'b-', linewidth=2, label='Ventas Reales')
        l2 = ax2.plot(days, break_even, 'r--', linewidth=2, label='Punto Equilibrio')
        l3 = ax2_twin.plot(days, roi, 'g-', linewidth=2, label='ROI %')
        
        ax2.set_xlabel('Días')
        ax2.set_ylabel('Unidades (L)', color='b')
        ax2_twin.set_ylabel('ROI (%)', color='g')
        ax2.set_title('Punto de Equilibrio y Retorno de Inversión')
        
        # Combine legends
        lns = l1 + l2 + l3
        labs = [l.get_label() for l in lns]
        ax2.legend(lns, labs, loc='best')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _generate_demand_comparison_chart(self, dates: List,
                                        daily_data: List[Dict],
                                        historical_demand: List[float]) -> str:
        """Generate detailed demand comparison chart"""
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
        
        # Prepare data
        simulated_demand = [d['demand_mean'] for d in daily_data]
        sim_days = list(range(1, len(simulated_demand) + 1))
        
        # 1. Time series comparison
        if historical_demand:
            hist_days = list(range(-len(historical_demand), 0))
            ax1.plot(hist_days, historical_demand, 'gray', linewidth=2, 
                    alpha=0.8, label='Histórico', marker='o', markersize=4)
        
        ax1.plot(sim_days, simulated_demand, 'b-', linewidth=2, 
                label='Simulado', marker='s', markersize=4)
        ax1.axvline(x=0.5, color='red', linestyle='--', alpha=0.5)
        ax1.set_xlabel('Días')
        ax1.set_ylabel('Demanda (L)')
        ax1.set_title('Comparación Temporal: Demanda Histórica vs Simulada')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Distribution comparison
        if historical_demand:
            ax2.hist(historical_demand, bins=20, alpha=0.5, label='Histórico', 
                    color='gray', density=True)
        ax2.hist(simulated_demand, bins=20, alpha=0.5, label='Simulado', 
                color='blue', density=True)
        
        # Add KDE
        if historical_demand and len(historical_demand) > 1:
            from scipy.stats import gaussian_kde
            kde_hist = gaussian_kde(historical_demand)
            x_hist = np.linspace(min(historical_demand), max(historical_demand), 100)
            ax2.plot(x_hist, kde_hist(x_hist), 'gray', linewidth=2, label='KDE Histórico')
        
        if len(simulated_demand) > 1:
            from scipy.stats import gaussian_kde
            kde_sim = gaussian_kde(simulated_demand)
            x_sim = np.linspace(min(simulated_demand), max(simulated_demand), 100)
            ax2.plot(x_sim, kde_sim(x_sim), 'blue', linewidth=2, label='KDE Simulado')
        
        ax2.set_xlabel('Demanda (L)')
        ax2.set_ylabel('Densidad')
        ax2.set_title('Distribución de Probabilidad')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. Statistical comparison
        if historical_demand:
            hist_mean = np.mean(historical_demand)
            hist_std = np.std(historical_demand)
            hist_cv = hist_std / hist_mean if hist_mean > 0 else 0
        else:
            hist_mean = hist_std = hist_cv = 0
        
        sim_mean = np.mean(simulated_demand)
        sim_std = np.std(simulated_demand)
        sim_cv = sim_std / sim_mean if sim_mean > 0 else 0
        
        metrics = ['Media', 'Desv. Est.', 'Coef. Var.', 'Mínimo', 'Máximo']
        if historical_demand:
            hist_values = [hist_mean, hist_std, hist_cv, 
                          min(historical_demand), max(historical_demand)]
        else:
            hist_values = [0, 0, 0, 0, 0]
        
        sim_values = [sim_mean, sim_std, sim_cv, 
                     min(simulated_demand), max(simulated_demand)]
        
        x = np.arange(len(metrics))
        width = 0.35
        
        bars1 = ax3.bar(x - width/2, hist_values, width, label='Histórico', 
                        color='gray', alpha=0.7)
        bars2 = ax3.bar(x + width/2, sim_values, width, label='Simulado', 
                        color='blue', alpha=0.7)
        
        # Add value labels
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}', ha='center', va='bottom', fontsize=9)
        
        ax3.set_ylabel('Valor')
        ax3.set_title('Comparación de Métricas Estadísticas')
        ax3.set_xticks(x)
        ax3.set_xticklabels(metrics)
        ax3.legend()
        ax3.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _generate_kpi_dashboard(self, daily_data: List[Dict],
                              totales_acumulativos: Dict[str, Dict]) -> str:
        """Generate KPI dashboard with key metrics"""
        fig = plt.figure(figsize=(15, 10))
        
        # Create grid
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # Calculate KPIs
        total_days = len(daily_data)
        avg_demand = np.mean([d['demand_mean'] for d in daily_data])
        avg_sales = np.mean([d.get('TPV', 0) for d in daily_data])
        avg_service = np.mean([d.get('NSC', 0) for d in daily_data]) * 100
        total_revenue = sum(d.get('IT', 0) for d in daily_data)
        total_profit = sum(d.get('GT', 0) for d in daily_data)
        avg_margin = np.mean([d.get('NR', 0) for d in daily_data]) * 100
        avg_efficiency = np.mean([d.get('EOG', 0) for d in daily_data]) * 100
        total_unmet = sum(d.get('DI', 0) for d in daily_data)
        
        # KPI 1: Revenue and Profit
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.text(0.5, 0.8, 'Ingresos Totales', ha='center', fontsize=14, 
                fontweight='bold', transform=ax1.transAxes)
        ax1.text(0.5, 0.5, f'Bs {total_revenue:,.0f}', ha='center', fontsize=20,
                color='blue', transform=ax1.transAxes)
        ax1.text(0.5, 0.2, f'Ganancia: Bs {total_profit:,.0f}', ha='center', 
                fontsize=12, color='green' if total_profit > 0 else 'red',
                transform=ax1.transAxes)
        ax1.axis('off')
        
        # KPI 2: Service Level
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.text(0.5, 0.8, 'Nivel de Servicio', ha='center', fontsize=14,
                fontweight='bold', transform=ax2.transAxes)
        color = 'green' if avg_service >= 95 else 'orange' if avg_service >= 85 else 'red'
        ax2.text(0.5, 0.5, f'{avg_service:.1f}%', ha='center', fontsize=24,
                color=color, transform=ax2.transAxes)
        ax2.text(0.5, 0.2, f'Meta: 95%', ha='center', fontsize=10,
                transform=ax2.transAxes)
        ax2.axis('off')
        
        # KPI 3: Efficiency
        ax3 = fig.add_subplot(gs[0, 2])
        ax3.text(0.5, 0.8, 'Eficiencia Global', ha='center', fontsize=14,
                fontweight='bold', transform=ax3.transAxes)
        color = 'green' if avg_efficiency >= 85 else 'orange' if avg_efficiency >= 70 else 'red'
        ax3.text(0.5, 0.5, f'{avg_efficiency:.1f}%', ha='center', fontsize=24,
                color=color, transform=ax3.transAxes)
        ax3.text(0.5, 0.2, f'OEE Target: 85%', ha='center', fontsize=10,
                transform=ax3.transAxes)
        ax3.axis('off')
        
        # Chart 1: Daily profit trend
        ax4 = fig.add_subplot(gs[1, :])
        days = list(range(1, len(daily_data) + 1))
        daily_profit = [d.get('GT', 0) for d in daily_data]
        cumulative_profit = np.cumsum(daily_profit)
        
        ax4.bar(days, daily_profit, alpha=0.5, color=['green' if p > 0 else 'red' for p in daily_profit])
        ax4_twin = ax4.twinx()
        ax4_twin.plot(days, cumulative_profit, 'b-', linewidth=3, label='Acumulado')
        
        ax4.set_xlabel('Días')
        ax4.set_ylabel('Ganancia Diaria (Bs)')
        ax4_twin.set_ylabel('Ganancia Acumulada (Bs)')
        ax4.set_title('Evolución de Ganancias')
        ax4.grid(True, alpha=0.3)
        
        # KPI 4: Demand fulfillment
        ax5 = fig.add_subplot(gs[2, 0])
        fulfillment_rate = (avg_sales / avg_demand * 100) if avg_demand > 0 else 0
        ax5.text(0.5, 0.8, 'Cumplimiento Demanda', ha='center', fontsize=12,
                fontweight='bold', transform=ax5.transAxes)
        ax5.text(0.5, 0.5, f'{fulfillment_rate:.1f}%', ha='center', fontsize=20,
                color='green' if fulfillment_rate >= 95 else 'orange',
                transform=ax5.transAxes)
        ax5.text(0.5, 0.2, f'Insatisfecha: {total_unmet:.0f} L', ha='center',
                fontsize=10, color='red', transform=ax5.transAxes)
        ax5.axis('off')
        
        # KPI 5: Average margin
        ax6 = fig.add_subplot(gs[2, 1])
        ax6.text(0.5, 0.8, 'Margen Promedio', ha='center', fontsize=12,
                fontweight='bold', transform=ax6.transAxes)
        color = 'green' if avg_margin > 15 else 'orange' if avg_margin > 5 else 'red'
        ax6.text(0.5, 0.5, f'{avg_margin:.1f}%', ha='center', fontsize=20,
                color=color, transform=ax6.transAxes)
        ax6.axis('off')
        
        # KPI 6: Health Score
        ax7 = fig.add_subplot(gs[2, 2])
        health_score = np.mean([d.get('HEALTH_SCORE', 50) for d in daily_data])
        ax7.text(0.5, 0.8, 'Salud del Negocio', ha='center', fontsize=12,
                fontweight='bold', transform=ax7.transAxes)
        color = 'green' if health_score >= 75 else 'orange' if health_score >= 50 else 'red'
        ax7.text(0.5, 0.5, f'{health_score:.0f}/100', ha='center', fontsize=20,
                color=color, transform=ax7.transAxes)
        performance = 'Excelente' if health_score >= 90 else 'Bueno' if health_score >= 75 else 'Regular' if health_score >= 50 else 'Crítico'
        ax7.text(0.5, 0.2, performance, ha='center', fontsize=12,
                transform=ax7.transAxes)
        ax7.axis('off')
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def generate_validation_comparison_chart(self, 
                                           variable_name: str,
                                           real_values: List[float],
                                           simulated_values: List[float],
                                           tolerance: float = 0.1) -> str:
        """Generate comparison chart for validation"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        days = list(range(1, len(simulated_values) + 1))
        
        # Time series comparison
        ax1.plot(days, real_values, 'g-', linewidth=2, marker='o', 
                markersize=6, label='Valores Reales')
        ax1.plot(days, simulated_values, 'b--', linewidth=2, marker='s',
                markersize=6, label='Valores Simulados')
        
        # Tolerance bands
        upper_tolerance = [r * (1 + tolerance) for r in real_values]
        lower_tolerance = [r * (1 - tolerance) for r in real_values]
        ax1.fill_between(days, lower_tolerance, upper_tolerance,
                        alpha=0.2, color='green', label=f'±{tolerance*100:.0f}% Tolerancia')
        
        ax1.set_xlabel('Días')
        ax1.set_ylabel('Valor')
        ax1.set_title(f'Comparación: {variable_name}')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Error analysis
        errors = [(s - r) / r * 100 if r != 0 else 0 
                 for s, r in zip(simulated_values, real_values)]
        
        colors = ['green' if abs(e) <= tolerance * 100 else 'red' for e in errors]
        bars = ax2.bar(days, errors, color=colors, alpha=0.7)
        
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        ax2.axhline(y=tolerance*100, color='green', linestyle='--', alpha=0.5)
        ax2.axhline(y=-tolerance*100, color='green', linestyle='--', alpha=0.5)
        
        ax2.set_xlabel('Días')
        ax2.set_ylabel('Error (%)')
        ax2.set_title('Análisis de Error Porcentual')
        ax2.grid(True, alpha=0.3)
        
        # Add statistics
        avg_error = np.mean(np.abs(errors))
        accuracy = sum(1 for e in errors if abs(e) <= tolerance * 100) / len(errors) * 100
        
        stats_text = f'Error Promedio: {avg_error:.1f}%\nPrecisión: {accuracy:.1f}%'
        ax2.text(0.02, 0.98, stats_text, transform=ax2.transAxes,
                verticalalignment='top', bbox=dict(boxstyle='round', 
                facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _fig_to_base64(self, fig: Figure) -> str:
        """Convert matplotlib figure to base64 string"""
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=self.dpi, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        buffer.seek(0)
        image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        buffer.close()
        plt.close(fig)
        return image_data