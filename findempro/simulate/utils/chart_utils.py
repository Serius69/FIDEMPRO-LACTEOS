# utils/chart_utils.py
import base64
import logging
from io import BytesIO
from typing import Dict, List, Any, Optional
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta

matplotlib.use('Agg')
logger = logging.getLogger(__name__)

class ChartGenerator:
    """Generador mejorado de gráficos con soporte completo para todas las variables"""
    
    def __init__(self):
        self.setup_matplotlib_style()
        
    def setup_matplotlib_style(self):
        """Configurar estilo consistente para todos los gráficos"""
        plt.style.use('seaborn-v0_8-darkgrid')
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['figure.dpi'] = 100
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.labelsize'] = 12
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['legend.fontsize'] = 10
        
    def generate_all_charts(self, simulation_id: int, simulation_instance, 
                          results_simulation: List, historical_demand: List = None) -> Dict[str, Any]:
        """Generar todos los gráficos de la simulación"""
        try:
            logger.info(f"Generating all charts for simulation {simulation_id}")
            
            # Extraer todas las variables y totales
            all_variables_extracted, totales_acumulativos = self._extract_all_variables(results_simulation)
            
            # Generar todos los gráficos
            chart_images = {}
            
            # 1. Gráfico de tendencia de demanda diaria
            chart_images['image_data_line'] = self._generate_demand_trend_chart(
                results_simulation, historical_demand
            )
            
            # 2. Gráficos financieros
            chart_images['image_data_0'] = self._generate_income_vs_profit_chart(
                all_variables_extracted
            )
            
            chart_images['image_data_1'] = self._generate_sales_vs_unsatisfied_demand_chart(
                all_variables_extracted
            )
            
            chart_images['image_data_2'] = self._generate_expense_analysis_chart(
                all_variables_extracted
            )
            
            chart_images['image_data_3'] = self._generate_production_costs_chart(
                all_variables_extracted
            )
            
            # 3. Gráficos operativos
            chart_images['image_data_4'] = self._generate_inventory_chart(
                all_variables_extracted
            )
            
            chart_images['image_data_5'] = self._generate_operational_costs_chart(
                all_variables_extracted
            )
            
            chart_images['image_data_6'] = self._generate_production_vs_sales_chart(
                all_variables_extracted
            )
            
            chart_images['image_data_7'] = self._generate_average_costs_chart(
                all_variables_extracted
            )
            
            # 4. Gráficos de análisis avanzado
            chart_images['image_data_8'] = self._generate_roi_and_profit_chart(
                all_variables_extracted
            )
            
            chart_images['image_data_9'] = self._generate_hr_analysis_chart(
                all_variables_extracted
            )
            
            chart_images['image_data_10'] = self._generate_cost_structure_chart(
                totales_acumulativos
            )
            
            chart_images['image_data_11'] = self._generate_price_vs_sales_correlation_chart(
                all_variables_extracted
            )
            
            chart_images['image_data_12'] = self._generate_key_financial_indicators_chart(
                totales_acumulativos
            )
            
            # Log de variables extraídas para debugging
            logger.info(f"Total variables extracted: {len(totales_acumulativos)}")
            logger.info(f"Variables available: {list(totales_acumulativos.keys())[:10]}...")
            
            return {
                'all_variables_extracted': all_variables_extracted,
                'totales_acumulativos': totales_acumulativos,
                'chart_images': chart_images,
                'total_charts': len(chart_images)
            }
            
        except Exception as e:
            logger.error(f"Error generating charts: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'all_variables_extracted': [],
                'totales_acumulativos': {},
                'chart_images': {},
                'error': str(e)
            }
    
    def _extract_all_variables(self, results_simulation: List) -> tuple:
        """Extraer todas las variables de los resultados de simulación"""
        all_variables_extracted = []
        totales_acumulativos = {}
        
        for idx, result in enumerate(results_simulation):
            # Obtener variables del resultado
            variables = result.get_variables() if hasattr(result, 'get_variables') else result.variables
            
            # Estructurar datos para el día
            day_data = {
                'date_simulation': result.date if hasattr(result, 'date') else datetime.now().date() + timedelta(days=idx),
                'demand_mean': float(result.demand_mean) if hasattr(result, 'demand_mean') else 0,
                'demand_std': float(result.demand_std_deviation) if hasattr(result, 'demand_std_deviation') else 0,
                'totales_por_variable': {}
            }
            
            # Procesar cada variable
            for var_name, var_value in variables.items():
                # Skip metadata
                if var_name.startswith('_'):
                    continue
                    
                # Convertir valor a float
                try:
                    value = float(var_value) if var_value is not None else 0.0
                except (ValueError, TypeError):
                    value = 0.0
                
                # Determinar unidad basada en el nombre de la variable
                unit = self._determine_unit(var_name)
                
                # Agregar a datos del día
                day_data['totales_por_variable'][var_name] = {
                    'total': value,
                    'unit': unit
                }
                
                # Acumular totales
                if var_name not in totales_acumulativos:
                    totales_acumulativos[var_name] = {
                        'total': 0,
                        'unit': unit,
                        'daily_values': []
                    }
                
                totales_acumulativos[var_name]['total'] += value
                totales_acumulativos[var_name]['daily_values'].append(value)
            
            all_variables_extracted.append(day_data)
        
        # Calcular tendencias para totales acumulativos
        for var_name, data in totales_acumulativos.items():
            if len(data['daily_values']) > 1:
                data['trend'] = self._calculate_trend(data['daily_values'])
                data['average'] = np.mean(data['daily_values'])
                data['std_dev'] = np.std(data['daily_values'])
        
        return all_variables_extracted, totales_acumulativos
    
    def _determine_unit(self, variable_name: str) -> str:
        """Determinar la unidad basada en el nombre de la variable"""
        var_upper = variable_name.upper()
        
        if any(term in var_upper for term in ['INGRESO', 'COSTO', 'GASTO', 'GANANCIA', 'PRECIO']):
            return 'BS'
        elif any(term in var_upper for term in ['PRODUCTO', 'LITRO', 'INVENTARIO', 'CAPACIDAD']):
            return 'L'
        elif any(term in var_upper for term in ['CLIENTE', 'EMPLEADO']):
            return 'CLIENTES' if 'CLIENTE' in var_upper else 'EMPLEADOS'
        elif any(term in var_upper for term in ['PORCENTAJE', 'MARGEN', 'RENTABILIDAD', 'ROI']):
            return '%'
        elif any(term in var_upper for term in ['HORA', 'TIEMPO']):
            return 'Horas'
        elif any(term in var_upper for term in ['DIA', 'DÍAS']):
            return 'DIAS'
        else:
            return ''
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calcular tendencia de una serie de valores"""
        if len(values) < 2:
            return 'stable'
        
        x = np.arange(len(values))
        z = np.polyfit(x, values, 1)
        
        if z[0] > 0.01:
            return 'increasing'
        elif z[0] < -0.01:
            return 'decreasing'
        else:
            return 'stable'
    
    def _generate_demand_trend_chart(self, results_simulation: List, 
                                    historical_demand: Optional[List] = None) -> str:
        """Generar gráfico de tendencia de demanda diaria"""
        try:
            fig, ax = plt.subplots(figsize=(14, 8))
            
            # Extraer datos de demanda simulada
            days = []
            simulated_demand = []
            confidence_upper = []
            confidence_lower = []
            
            for idx, result in enumerate(results_simulation):
                days.append(idx + 1)
                demand = float(result.demand_mean) if hasattr(result, 'demand_mean') else 0
                std = float(result.demand_std_deviation) if hasattr(result, 'demand_std_deviation') else 0
                
                simulated_demand.append(demand)
                confidence_upper.append(demand + 2 * std)
                confidence_lower.append(max(0, demand - 2 * std))
            
            # Graficar demanda simulada
            ax.plot(days, simulated_demand, 'b-', linewidth=2.5, 
                   label='Demanda Simulada', marker='o', markersize=4)
            
            # Banda de confianza
            ax.fill_between(days, confidence_lower, confidence_upper, 
                          alpha=0.2, color='blue', label='Intervalo de Confianza 95%')
            
            # Si hay demanda histórica, mostrar referencia
            if historical_demand and len(historical_demand) > 0:
                hist_mean = np.mean(historical_demand)
                hist_std = np.std(historical_demand)
                
                ax.axhline(y=hist_mean, color='green', linestyle='--', 
                          label=f'Media Histórica: {hist_mean:.2f}')
                ax.axhspan(hist_mean - hist_std, hist_mean + hist_std, 
                          alpha=0.1, color='green', label='Desv. Est. Histórica')
            
            # Calcular y mostrar tendencia
            if len(simulated_demand) > 1:
                z = np.polyfit(days, simulated_demand, 1)
                p = np.poly1d(z)
                ax.plot(days, p(days), 'r--', alpha=0.8, linewidth=2,
                       label=f'Tendencia: {z[0]:.2f} L/día')
            
            # Promedios móviles
            if len(simulated_demand) >= 7:
                ma7 = pd.Series(simulated_demand).rolling(window=7, center=True).mean()
                ax.plot(days, ma7, 'g-', alpha=0.7, linewidth=2, 
                       label='Media Móvil 7 días')
            
            # Configuración del gráfico
            ax.set_xlabel('Día de Simulación', fontsize=12)
            ax.set_ylabel('Demanda (Litros)', fontsize=12)
            ax.set_title('Tendencia de Demanda Diaria - Análisis Completo', 
                        fontsize=16, fontweight='bold', pad=20)
            
            # Grid y leyenda
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.legend(loc='best', frameon=True, fancybox=True, shadow=True)
            
            # Ajustar límites del eje Y
            if simulated_demand:
                y_min = min(min(confidence_lower), 0)
                y_max = max(confidence_upper) * 1.1
                ax.set_ylim(y_min, y_max)
            
            # Estadísticas en el gráfico
            if simulated_demand:
                stats_text = (f'Media: {np.mean(simulated_demand):.2f} L\n'
                            f'Desv. Est.: {np.std(simulated_demand):.2f} L\n'
                            f'Mín: {min(simulated_demand):.2f} L\n'
                            f'Máx: {max(simulated_demand):.2f} L')
                
                props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
                ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
                       verticalalignment='top', bbox=props)
            
            plt.tight_layout()
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating demand trend chart: {str(e)}")
            return self._create_error_chart("Error en gráfico de tendencia de demanda")
    
    def _generate_income_vs_profit_chart(self, all_variables: List[Dict]) -> str:
        """Generar gráfico de ingresos vs ganancias"""
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), 
                                          gridspec_kw={'height_ratios': [3, 1]})
            
            days = []
            incomes = []
            profits = []
            expenses = []
            
            for idx, day_data in enumerate(all_variables):
                days.append(idx + 1)
                
                vars_dict = day_data['totales_por_variable']
                income = vars_dict.get('INGRESOS TOTALES', {}).get('total', 0) or vars_dict.get('IT', {}).get('total', 0)
                profit = vars_dict.get('GANANCIAS TOTALES', {}).get('total', 0) or vars_dict.get('GT', {}).get('total', 0)
                expense = vars_dict.get('GASTOS TOTALES', {}).get('total', 0) or vars_dict.get('TG', {}).get('total', 0)
                
                incomes.append(income)
                profits.append(profit)
                expenses.append(expense)
            
            # Gráfico principal
            ax1.plot(days, incomes, 'g-', linewidth=2.5, marker='o', 
                    markersize=6, label='Ingresos Totales')
            ax1.plot(days, profits, 'b-', linewidth=2.5, marker='s', 
                    markersize=6, label='Ganancias Totales')
            ax1.plot(days, expenses, 'r--', linewidth=2, marker='^', 
                    markersize=5, label='Gastos Totales', alpha=0.8)
            
            # Área de ganancias/pérdidas
            ax1.fill_between(days, 0, profits, where=[p >= 0 for p in profits], 
                           alpha=0.3, color='green', label='Zona de Ganancias')
            ax1.fill_between(days, profits, 0, where=[p < 0 for p in profits], 
                           alpha=0.3, color='red', label='Zona de Pérdidas')
            
            ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            ax1.set_ylabel('Monto (Bs.)', fontsize=12)
            ax1.set_title('Análisis Financiero: Ingresos vs Ganancias vs Gastos', 
                         fontsize=16, fontweight='bold')
            ax1.legend(loc='upper left', frameon=True, fancybox=True)
            ax1.grid(True, alpha=0.3)
            
            # Gráfico de margen de ganancia
            margins = []
            for i, p in zip(incomes, profits):
                if i > 0:
                    margins.append((p / i) * 100)
                else:
                    margins.append(0)
            
            ax2.bar(days, margins, color=['green' if m >= 0 else 'red' for m in margins], 
                   alpha=0.7)
            ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            ax2.set_xlabel('Día de Simulación', fontsize=12)
            ax2.set_ylabel('Margen (%)', fontsize=12)
            ax2.set_title('Margen de Ganancia Diario', fontsize=14)
            ax2.grid(True, alpha=0.3, axis='y')
            
            # Agregar línea de margen objetivo (20%)
            ax2.axhline(y=20, color='orange', linestyle='--', linewidth=2, 
                       label='Margen Objetivo (20%)')
            ax2.legend()
            
            plt.tight_layout()
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating income vs profit chart: {str(e)}")
            return self._create_error_chart("Error en gráfico de ingresos vs ganancias")
    
    def _generate_sales_vs_unsatisfied_demand_chart(self, all_variables: List[Dict]) -> str:
        """Generar gráfico de ventas vs demanda insatisfecha"""
        try:
            fig, ax = plt.subplots(figsize=(14, 8))
            
            days = []
            sales = []
            unsatisfied = []
            total_demand = []
            
            for idx, day_data in enumerate(all_variables):
                days.append(idx + 1)
                
                vars_dict = day_data['totales_por_variable']
                sale = vars_dict.get('TOTAL PRODUCTOS VENDIDOS', {}).get('total', 0) or vars_dict.get('TPV', {}).get('total', 0)
                unsat = vars_dict.get('DEMANDA INSATISFECHA', {}).get('total', 0) or vars_dict.get('DI', {}).get('total', 0)
                
                sales.append(sale)
                unsatisfied.append(unsat)
                total_demand.append(sale + unsat)
            
            # Gráfico de barras apiladas
            width = 0.6
            p1 = ax.bar(days, sales, width, label='Productos Vendidos', color='#2ecc71')
            p2 = ax.bar(days, unsatisfied, width, bottom=sales, 
                       label='Demanda Insatisfecha', color='#e74c3c')
            
            # Línea de demanda total
            ax.plot(days, total_demand, 'k--', linewidth=2, marker='o', 
                   markersize=5, label='Demanda Total')
            
            # Porcentaje de satisfacción
            for i, (s, t) in enumerate(zip(sales, total_demand)):
                if t > 0:
                    pct = (s / t) * 100
                    ax.text(days[i], t + max(total_demand) * 0.02, f'{pct:.0f}%', 
                           ha='center', va='bottom', fontsize=8)
            
            ax.set_xlabel('Día de Simulación', fontsize=12)
            ax.set_ylabel('Cantidad (Litros)', fontsize=12)
            ax.set_title('Análisis de Ventas vs Demanda Insatisfecha', 
                        fontsize=16, fontweight='bold')
            ax.legend(loc='upper right')
            ax.grid(True, alpha=0.3, axis='y')
            
            # Estadísticas
            if sales and unsatisfied:
                total_sales = sum(sales)
                total_unsatisfied = sum(unsatisfied)
                satisfaction_rate = (total_sales / (total_sales + total_unsatisfied)) * 100
                
                stats_text = (f'Total Vendido: {total_sales:,.0f} L\n'
                            f'Total Insatisfecho: {total_unsatisfied:,.0f} L\n'
                            f'Tasa de Satisfacción: {satisfaction_rate:.1f}%')
                
                props = dict(boxstyle='round', facecolor='lightblue', alpha=0.8)
                ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
                       verticalalignment='top', bbox=props)
            
            plt.tight_layout()
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating sales vs demand chart: {str(e)}")
            return self._create_error_chart("Error en gráfico de ventas vs demanda")
    
    def _generate_roi_and_profit_chart(self, all_variables: List[Dict]) -> str:
        """Generar gráfico de ROI y rentabilidad"""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
            
            days = []
            roi_values = []
            profit_margins = []
            profits = []
            
            for idx, day_data in enumerate(all_variables):
                days.append(idx + 1)
                
                vars_dict = day_data['totales_por_variable']
                roi = vars_dict.get('Retorno Inversión', {}).get('total', 0) or vars_dict.get('RI', {}).get('total', 0)
                margin = vars_dict.get('Nivel de Rentabilidad', {}).get('total', 0) or vars_dict.get('NR', {}).get('total', 0)
                profit = vars_dict.get('GANANCIAS TOTALES', {}).get('total', 0) or vars_dict.get('GT', {}).get('total', 0)
                
                roi_values.append(roi * 100)  # Convertir a porcentaje
                profit_margins.append(margin * 100)  # Convertir a porcentaje
                profits.append(profit)
            
            # Gráfico de ROI
            ax1.plot(days, roi_values, 'b-', linewidth=2.5, marker='o', markersize=6)
            ax1.fill_between(days, 0, roi_values, alpha=0.3, color='blue')
            ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            ax1.axhline(y=15, color='green', linestyle='--', linewidth=2, 
                       label='ROI Objetivo (15%)')
            
            ax1.set_xlabel('Día de Simulación', fontsize=12)
            ax1.set_ylabel('ROI (%)', fontsize=12)
            ax1.set_title('Retorno de Inversión (ROI)', fontsize=14, fontweight='bold')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Gráfico de margen de rentabilidad
            colors = ['green' if m >= 0 else 'red' for m in profit_margins]
            bars = ax2.bar(days, profit_margins, color=colors, alpha=0.7)
            
            # Línea de tendencia
            if len(profit_margins) > 1:
                z = np.polyfit(days, profit_margins, 1)
                p = np.poly1d(z)
                ax2.plot(days, p(days), 'r--', linewidth=2, 
                        label=f'Tendencia: {z[0]:.2f}%/día')
            
            ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            ax2.axhline(y=20, color='orange', linestyle='--', linewidth=2, 
                       label='Margen Objetivo (20%)')
            
            ax2.set_xlabel('Día de Simulación', fontsize=12)
            ax2.set_ylabel('Margen de Rentabilidad (%)', fontsize=12)
            ax2.set_title('Margen de Rentabilidad', fontsize=14, fontweight='bold')
            ax2.legend()
            ax2.grid(True, alpha=0.3, axis='y')
            
            # Agregar valores en las barras
            for bar, value in zip(bars, profit_margins):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{value:.1f}%', ha='center', 
                        va='bottom' if height >= 0 else 'top', fontsize=8)
            
            plt.tight_layout()
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating ROI chart: {str(e)}")
            return self._create_error_chart("Error en gráfico de ROI")
    
    def _generate_production_vs_sales_chart(self, all_variables: List[Dict]) -> str:
        """Generar gráfico de producción vs ventas"""
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), 
                                          gridspec_kw={'height_ratios': [3, 1]})
            
            days = []
            production = []
            sales = []
            inventory = []
            
            for idx, day_data in enumerate(all_variables):
                days.append(idx + 1)
                
                vars_dict = day_data['totales_por_variable']
                prod = vars_dict.get('TOTAL PRODUCTOS PRODUCIDOS', {}).get('total', 0) or vars_dict.get('TPPRO', {}).get('total', 0)
                sale = vars_dict.get('TOTAL PRODUCTOS VENDIDOS', {}).get('total', 0) or vars_dict.get('TPV', {}).get('total', 0)
                inv = vars_dict.get('INVENTARIO PRODUCTOS FINALES', {}).get('total', 0) or vars_dict.get('IPF', {}).get('total', 0)
                
                production.append(prod)
                sales.append(sale)
                inventory.append(inv)
            
            # Gráfico principal
            ax1.plot(days, production, 'b-', linewidth=2.5, marker='s', 
                    markersize=6, label='Producción')
            ax1.plot(days, sales, 'g-', linewidth=2.5, marker='o', 
                    markersize=6, label='Ventas')
            ax1.plot(days, inventory, 'orange', linewidth=2, marker='^', 
                    markersize=5, label='Inventario', linestyle='--')
            
            # Área de exceso/déficit
            difference = [p - s for p, s in zip(production, sales)]
            ax1.fill_between(days, 0, difference, where=[d >= 0 for d in difference], 
                           alpha=0.2, color='blue', label='Exceso de Producción')
            ax1.fill_between(days, difference, 0, where=[d < 0 for d in difference], 
                           alpha=0.2, color='red', label='Déficit de Producción')
            
            ax1.set_ylabel('Cantidad (Litros)', fontsize=12)
            ax1.set_title('Análisis de Producción vs Ventas e Inventario', 
                         fontsize=16, fontweight='bold')
            ax1.legend(loc='upper left')
            ax1.grid(True, alpha=0.3)
            
            # Gráfico de eficiencia
            efficiency = []
            for p, s in zip(production, sales):
                if p > 0:
                    efficiency.append((s / p) * 100)
                else:
                    efficiency.append(0)
            
            colors = ['green' if e >= 80 else 'orange' if e >= 60 else 'red' for e in efficiency]
            bars = ax2.bar(days, efficiency, color=colors, alpha=0.7)
            
            ax2.axhline(y=80, color='green', linestyle='--', linewidth=2, 
                       label='Objetivo (80%)')
            ax2.set_xlabel('Día de Simulación', fontsize=12)
            ax2.set_ylabel('Eficiencia (%)', fontsize=12)
            ax2.set_title('Eficiencia de Ventas (Ventas/Producción)', fontsize=14)
            ax2.set_ylim(0, 120)
            ax2.legend()
            ax2.grid(True, alpha=0.3, axis='y')
            
            plt.tight_layout()
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating production vs sales chart: {str(e)}")
            return self._create_error_chart("Error en gráfico de producción vs ventas")
    
    def _generate_cost_structure_chart(self, totales_acumulativos: Dict) -> str:
        """Generar gráfico de estructura de costos"""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
            
            # Extraer componentes de costos
            cost_components = {
                'Costos Operativos': totales_acumulativos.get('GASTOS OPERATIVOS', {}).get('total', 0) or 
                                    totales_acumulativos.get('GO', {}).get('total', 0),
                'Costos de Insumos': totales_acumulativos.get('COSTO TOTAL ADQUISICIÓN INSUMOS', {}).get('total', 0) or
                                     totales_acumulativos.get('CTAI', {}).get('total', 0),
                'Costos de Marketing': totales_acumulativos.get('GASTO TOTAL MARKETING', {}).get('total', 0) or
                                      totales_acumulativos.get('GMM', {}).get('total', 0),
                'Costos de Transporte': totales_acumulativos.get('COSTO TOTAL TRANSPORTE', {}).get('total', 0) or
                                       totales_acumulativos.get('CTTL', {}).get('total', 0),
                'Otros Costos': totales_acumulativos.get('GASTOS GENERALES', {}).get('total', 0) or
                               totales_acumulativos.get('GG', {}).get('total', 0)
            }
            
            # Filtrar componentes con valor > 0
            cost_components = {k: v for k, v in cost_components.items() if v > 0}
            
            if cost_components:
                # Gráfico de pastel
                colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc']
                wedges, texts, autotexts = ax1.pie(cost_components.values(), 
                                                   labels=cost_components.keys(),
                                                   colors=colors[:len(cost_components)],
                                                   autopct='%1.1f%%',
                                                   startangle=90,
                                                   explode=[0.05] * len(cost_components))
                
                ax1.set_title('Estructura de Costos - Distribución Porcentual', 
                             fontsize=14, fontweight='bold')
                
                # Mejorar apariencia
                for text in texts:
                    text.set_fontsize(10)
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontsize(10)
                    autotext.set_weight('bold')
                
                # Gráfico de barras horizontales
                sorted_costs = sorted(cost_components.items(), key=lambda x: x[1], reverse=True)
                categories = [item[0] for item in sorted_costs]
                values = [item[1] for item in sorted_costs]
                
                bars = ax2.barh(categories, values, color=colors[:len(categories)])
                
                # Agregar valores en las barras
                for bar, value in zip(bars, values):
                    ax2.text(bar.get_width() + max(values) * 0.01, bar.get_y() + bar.get_height()/2,
                            f'Bs. {value:,.0f}', ha='left', va='center')
                
                ax2.set_xlabel('Monto (Bs.)', fontsize=12)
                ax2.set_title('Estructura de Costos - Valores Absolutos', 
                             fontsize=14, fontweight='bold')
                ax2.grid(True, alpha=0.3, axis='x')
                
                # Calcular y mostrar total
                total_costs = sum(cost_components.values())
                fig.suptitle(f'Análisis de Estructura de Costos - Total: Bs. {total_costs:,.0f}', 
                            fontsize=16, fontweight='bold')
            else:
                ax1.text(0.5, 0.5, 'No hay datos de costos disponibles', 
                        ha='center', va='center', transform=ax1.transAxes)
                ax2.text(0.5, 0.5, 'No hay datos de costos disponibles', 
                        ha='center', va='center', transform=ax2.transAxes)
            
            plt.tight_layout()
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating cost structure chart: {str(e)}")
            return self._create_error_chart("Error en gráfico de estructura de costos")
    
    def _generate_expense_analysis_chart(self, all_variables: List[Dict]) -> str:
        """Generar gráfico de análisis de gastos"""
        try:
            fig, ax = plt.subplots(figsize=(14, 8))
            
            days = []
            operational = []
            general = []
            total = []
            
            for idx, day_data in enumerate(all_variables):
                days.append(idx + 1)
                
                vars_dict = day_data['totales_por_variable']
                op = vars_dict.get('GASTOS OPERATIVOS', {}).get('total', 0) or vars_dict.get('GO', {}).get('total', 0)
                gen = vars_dict.get('GASTOS GENERALES', {}).get('total', 0) or vars_dict.get('GG', {}).get('total', 0)
                tot = vars_dict.get('GASTOS TOTALES', {}).get('total', 0) or vars_dict.get('TG', {}).get('total', 0)
                
                operational.append(op)
                general.append(gen)
                total.append(tot)
            
            # Gráfico de áreas apiladas
            ax.fill_between(days, 0, operational, alpha=0.7, color='#e74c3c', label='Gastos Operativos')
            ax.fill_between(days, operational, [o+g for o,g in zip(operational, general)], 
                          alpha=0.7, color='#f39c12', label='Gastos Generales')
            
            # Línea de gastos totales
            ax.plot(days, total, 'k-', linewidth=2.5, marker='o', markersize=5, label='Gastos Totales')
            
            # Promedio móvil
            if len(total) >= 7:
                ma7 = pd.Series(total).rolling(window=7, center=True).mean()
                ax.plot(days, ma7, 'b--', linewidth=2, alpha=0.8, label='Media Móvil 7 días')
            
            ax.set_xlabel('Día de Simulación', fontsize=12)
            ax.set_ylabel('Gastos (Bs.)', fontsize=12)
            ax.set_title('Análisis de Gastos - Operativos y Generales', 
                        fontsize=16, fontweight='bold')
            ax.legend(loc='upper left')
            ax.grid(True, alpha=0.3)
            
            # Estadísticas
            if total:
                avg_total = np.mean(total)
                avg_op = np.mean(operational)
                avg_gen = np.mean(general)
                
                stats_text = (f'Promedio Total: Bs. {avg_total:,.0f}\n'
                            f'Promedio Operativo: Bs. {avg_op:,.0f}\n'
                            f'Promedio General: Bs. {avg_gen:,.0f}\n'
                            f'% Operativo: {(avg_op/avg_total*100):.1f}%')
                
                props = dict(boxstyle='round', facecolor='lightyellow', alpha=0.8)
                ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
                       verticalalignment='top', bbox=props)
            
            plt.tight_layout()
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating expense analysis chart: {str(e)}")
            return self._create_error_chart("Error en análisis de gastos")
    
    def _generate_production_costs_chart(self, all_variables: List[Dict]) -> str:
        """Generar gráfico de costos de producción"""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
            
            days = []
            unit_costs = []
            total_costs = []
            production_volumes = []
            
            for idx, day_data in enumerate(all_variables):
                days.append(idx + 1)
                
                vars_dict = day_data['totales_por_variable']
                unit = vars_dict.get('COSTO UNITARIO PRODUCCIÓN', {}).get('total', 0) or vars_dict.get('CUP', {}).get('total', 0)
                total = vars_dict.get('COSTO TOTAL ADQUISICIÓN INSUMOS', {}).get('total', 0) or vars_dict.get('CTAI', {}).get('total', 0)
                volume = vars_dict.get('TOTAL PRODUCTOS PRODUCIDOS', {}).get('total', 0) or vars_dict.get('TPPRO', {}).get('total', 0)
                
                unit_costs.append(unit)
                total_costs.append(total)
                production_volumes.append(volume)
            
            # Gráfico de costo unitario
            ax1.plot(days, unit_costs, 'b-', linewidth=2.5, marker='o', markersize=6)
            ax1.fill_between(days, 0, unit_costs, alpha=0.3, color='blue')
            
            # Línea de costo objetivo
            if unit_costs:
                avg_unit_cost = np.mean(unit_costs)
                ax1.axhline(y=avg_unit_cost, color='red', linestyle='--', linewidth=2,
                           label=f'Promedio: Bs. {avg_unit_cost:.2f}')
            
            ax1.set_xlabel('Día de Simulación', fontsize=12)
            ax1.set_ylabel('Costo Unitario (Bs./L)', fontsize=12)
            ax1.set_title('Evolución del Costo Unitario de Producción', 
                         fontsize=14, fontweight='bold')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Gráfico de relación costo-volumen
            if production_volumes and total_costs:
                scatter = ax2.scatter(production_volumes, total_costs, c=days, 
                                    cmap='viridis', s=100, alpha=0.7)
                
                # Línea de tendencia
                if len(production_volumes) > 1:
                    z = np.polyfit(production_volumes, total_costs, 1)
                    p = np.poly1d(z)
                    ax2.plot(sorted(production_volumes), p(sorted(production_volumes)), 
                            'r--', linewidth=2, label=f'Tendencia: {z[0]:.2f} Bs./L')
                
                ax2.set_xlabel('Volumen de Producción (L)', fontsize=12)
                ax2.set_ylabel('Costo Total (Bs.)', fontsize=12)
                ax2.set_title('Relación Costo-Volumen de Producción', 
                             fontsize=14, fontweight='bold')
                ax2.legend()
                ax2.grid(True, alpha=0.3)
                
                # Colorbar
                cbar = plt.colorbar(scatter, ax=ax2)
                cbar.set_label('Día', fontsize=10)
            
            plt.tight_layout()
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating production costs chart: {str(e)}")
            return self._create_error_chart("Error en costos de producción")
    
    def _generate_inventory_chart(self, all_variables: List[Dict]) -> str:
        """Generar gráfico de inventarios"""
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10),
                                          gridspec_kw={'height_ratios': [3, 1]})
            
            days = []
            inventory_final = []
            inventory_raw = []
            rotation = []
            
            for idx, day_data in enumerate(all_variables):
                days.append(idx + 1)
                
                vars_dict = day_data['totales_por_variable']
                final = vars_dict.get('INVENTARIO PRODUCTOS FINALES', {}).get('total', 0) or vars_dict.get('IPF', {}).get('total', 0)
                raw = vars_dict.get('INVENTARIO INSUMOS', {}).get('total', 0) or vars_dict.get('II', {}).get('total', 0)
                rot = vars_dict.get('ROTACION INVENTARIO', {}).get('total', 0) or vars_dict.get('RTI', {}).get('total', 0)
                
                inventory_final.append(final)
                inventory_raw.append(raw)
                rotation.append(rot)
            
            # Gráfico de inventarios
            ax1.plot(days, inventory_final, 'b-', linewidth=2.5, marker='o', 
                    markersize=6, label='Productos Finales')
            ax1.plot(days, inventory_raw, 'g-', linewidth=2.5, marker='s', 
                    markersize=6, label='Insumos')
            
            # Zonas de inventario
            if inventory_final:
                max_inv = max(inventory_final + inventory_raw)
                ax1.axhspan(0, max_inv * 0.2, alpha=0.1, color='red', label='Zona Crítica')
                ax1.axhspan(max_inv * 0.2, max_inv * 0.5, alpha=0.1, color='yellow', label='Zona Alerta')
                ax1.axhspan(max_inv * 0.5, max_inv * 0.8, alpha=0.1, color='green', label='Zona Óptima')
            
            ax1.set_ylabel('Inventario (Litros)', fontsize=12)
            ax1.set_title('Gestión de Inventarios', fontsize=16, fontweight='bold')
            ax1.legend(loc='upper left')
            ax1.grid(True, alpha=0.3)
            
            # Gráfico de rotación
            bars = ax2.bar(days, rotation, color='purple', alpha=0.7)
            ax2.axhline(y=12, color='green', linestyle='--', linewidth=2, 
                       label='Objetivo (12 veces/mes)')
            
            ax2.set_xlabel('Día de Simulación', fontsize=12)
            ax2.set_ylabel('Rotación (veces)', fontsize=12)
            ax2.set_title('Rotación de Inventario', fontsize=14)
            ax2.legend()
            ax2.grid(True, alpha=0.3, axis='y')
            
            plt.tight_layout()
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating inventory chart: {str(e)}")
            return self._create_error_chart("Error en gráfico de inventarios")
    
    def _generate_operational_costs_chart(self, all_variables: List[Dict]) -> str:
        """Generar gráfico de costos operativos detallados"""
        try:
            fig, ax = plt.subplots(figsize=(14, 8))
            
            days = []
            fixed_costs = []
            variable_costs = []
            labor_costs = []
            
            for idx, day_data in enumerate(all_variables):
                days.append(idx + 1)
                
                vars_dict = day_data['totales_por_variable']
                fixed = vars_dict.get('COSTO FIJO DIARIO', {}).get('total', 0) or vars_dict.get('CFD', {}).get('total', 0)
                variable = vars_dict.get('COSTO TOTAL ADQUISICIÓN INSUMOS', {}).get('total', 0) or vars_dict.get('CTAI', {}).get('total', 0)
                labor = vars_dict.get('SUELDOS EMPLEADOS', {}).get('total', 0) or vars_dict.get('SE', {}).get('total', 0)
                
                fixed_costs.append(fixed)
                variable_costs.append(variable)
                labor_costs.append(labor / 30)  # Convertir mensual a diario
            
            # Crear gráfico de áreas apiladas
            ax.fill_between(days, 0, fixed_costs, alpha=0.7, color='#3498db', label='Costos Fijos')
            ax.fill_between(days, fixed_costs, [f+v for f,v in zip(fixed_costs, variable_costs)], 
                          alpha=0.7, color='#e74c3c', label='Costos Variables')
            ax.fill_between(days, [f+v for f,v in zip(fixed_costs, variable_costs)], 
                          [f+v+l for f,v,l in zip(fixed_costs, variable_costs, labor_costs)], 
                          alpha=0.7, color='#f39c12', label='Costos de Personal')
            
            # Línea de costo total
            total_costs = [f+v+l for f,v,l in zip(fixed_costs, variable_costs, labor_costs)]
            ax.plot(days, total_costs, 'k-', linewidth=2.5, marker='o', 
                   markersize=5, label='Costo Total Operativo')
            
            ax.set_xlabel('Día de Simulación', fontsize=12)
            ax.set_ylabel('Costos (Bs.)', fontsize=12)
            ax.set_title('Desglose de Costos Operativos', fontsize=16, fontweight='bold')
            ax.legend(loc='upper left')
            ax.grid(True, alpha=0.3)
            
            # Estadísticas
            if total_costs:
                avg_total = np.mean(total_costs)
                avg_fixed = np.mean(fixed_costs)
                avg_variable = np.mean(variable_costs)
                avg_labor = np.mean(labor_costs)
                
                stats_text = (f'Promedio Total: Bs. {avg_total:,.0f}\n'
                            f'% Fijo: {(avg_fixed/avg_total*100):.1f}%\n'
                            f'% Variable: {(avg_variable/avg_total*100):.1f}%\n'
                            f'% Personal: {(avg_labor/avg_total*100):.1f}%')
                
                props = dict(boxstyle='round', facecolor='lightcyan', alpha=0.8)
                ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
                       verticalalignment='top', bbox=props)
            
            plt.tight_layout()
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating operational costs chart: {str(e)}")
            return self._create_error_chart("Error en costos operativos")
    
    def _generate_average_costs_chart(self, all_variables: List[Dict]) -> str:
        """Generar gráfico de costos promedio"""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
            
            days = []
            avg_production = []
            avg_sales = []
            avg_inputs = []
            avg_labor = []
            
            for idx, day_data in enumerate(all_variables):
                days.append(idx + 1)
                
                vars_dict = day_data['totales_por_variable']
                prod = vars_dict.get('COSTO PROMEDIO PRODUCCION', {}).get('total', 0) or vars_dict.get('CPP', {}).get('total', 0)
                sales = vars_dict.get('COSTO PROMEDIO VENTA', {}).get('total', 0) or vars_dict.get('CPV', {}).get('total', 0)
                inputs = vars_dict.get('COSTO PROMEDIO INSUMOS', {}).get('total', 0) or vars_dict.get('CPI', {}).get('total', 0)
                labor = vars_dict.get('Costo Promedio Mano Obra', {}).get('total', 0) or vars_dict.get('CPMO', {}).get('total', 0)
                
                avg_production.append(prod)
                avg_sales.append(sales)
                avg_inputs.append(inputs)
                avg_labor.append(labor)
            
            # Gráfico de líneas múltiples
            ax1.plot(days, avg_production, 'b-', linewidth=2.5, marker='o', 
                    markersize=6, label='Costo Promedio Producción')
            ax1.plot(days, avg_sales, 'g-', linewidth=2.5, marker='s', 
                    markersize=6, label='Costo Promedio Venta')
            ax1.plot(days, avg_inputs, 'r-', linewidth=2, marker='^', 
                    markersize=5, label='Costo Promedio Insumos')
            ax1.plot(days, avg_labor, 'orange', linewidth=2, marker='d', 
                    markersize=5, label='Costo Promedio Mano de Obra')
            
            ax1.set_xlabel('Día de Simulación', fontsize=12)
            ax1.set_ylabel('Costo Promedio (Bs.)', fontsize=12)
            ax1.set_title('Evolución de Costos Promedio', fontsize=14, fontweight='bold')
            ax1.legend(loc='best')
            ax1.grid(True, alpha=0.3)
            
            # Gráfico de composición de costos
            if days:
                # Tomar valores del último día
                last_day_costs = {
                    'Producción': avg_production[-1] if avg_production else 0,
                    'Venta': avg_sales[-1] if avg_sales else 0,
                    'Insumos': avg_inputs[-1] if avg_inputs else 0,
                    'Mano de Obra': avg_labor[-1] if avg_labor else 0
                }
                
                # Filtrar valores positivos
                last_day_costs = {k: v for k, v in last_day_costs.items() if v > 0}
                
                if last_day_costs:
                    colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12']
                    wedges, texts, autotexts = ax2.pie(last_day_costs.values(), 
                                                       labels=last_day_costs.keys(),
                                                       colors=colors[:len(last_day_costs)],
                                                       autopct='%1.1f%%',
                                                       startangle=90)
                    
                    ax2.set_title(f'Composición de Costos Promedio - Día {days[-1]}', 
                                 fontsize=14, fontweight='bold')
                else:
                    ax2.text(0.5, 0.5, 'No hay datos de costos disponibles', 
                            ha='center', va='center', transform=ax2.transAxes)
            
            plt.tight_layout()
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating average costs chart: {str(e)}")
            return self._create_error_chart("Error en costos promedio")
    
    def _generate_hr_analysis_chart(self, all_variables: List[Dict]) -> str:
        """Generar gráfico de análisis de recursos humanos"""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
            
            days = []
            productivity = []
            idle_hours = []
            idle_costs = []
            
            for idx, day_data in enumerate(all_variables):
                days.append(idx + 1)
                
                vars_dict = day_data['totales_por_variable']
                prod = vars_dict.get('Productividad Empleados', {}).get('total', 0) or vars_dict.get('PE', {}).get('total', 0)
                idle_h = vars_dict.get('Horas Ociosas', {}).get('total', 0) or vars_dict.get('HO', {}).get('total', 0)
                idle_c = vars_dict.get('Costo Horas Ociosas', {}).get('total', 0) or vars_dict.get('CHO', {}).get('total', 0)
                
                productivity.append(prod)
                idle_hours.append(idle_h / 60)  # Convertir a horas
                idle_costs.append(idle_c)
            
            # Gráfico de productividad
            ax1.plot(days, productivity, 'g-', linewidth=2.5, marker='o', markersize=6)
            ax1.fill_between(days, 0, productivity, alpha=0.3, color='green')
            
            # Línea de productividad objetivo
            if productivity:
                avg_prod = np.mean(productivity)
                ax1.axhline(y=avg_prod, color='red', linestyle='--', linewidth=2,
                           label=f'Promedio: {avg_prod:.1f} L/empleado')
            
            ax1.set_xlabel('Día de Simulación', fontsize=12)
            ax1.set_ylabel('Productividad (L/empleado)', fontsize=12)
            ax1.set_title('Productividad por Empleado', fontsize=14, fontweight='bold')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Gráfico de horas ociosas y costos
            ax2_twin = ax2.twinx()
            
            bars = ax2.bar(days, idle_hours, alpha=0.7, color='orange', label='Horas Ociosas')
            line = ax2_twin.plot(days, idle_costs, 'r-', linewidth=2.5, marker='s', 
                               markersize=5, label='Costo Horas Ociosas')
            
            ax2.set_xlabel('Día de Simulación', fontsize=12)
            ax2.set_ylabel('Horas Ociosas', fontsize=12, color='orange')
            ax2_twin.set_ylabel('Costo (Bs.)', fontsize=12, color='red')
            ax2.set_title('Análisis de Tiempo Ocioso', fontsize=14, fontweight='bold')
            
            # Combinar leyendas
            lines1, labels1 = ax2.get_legend_handles_labels()
            lines2, labels2 = ax2_twin.get_legend_handles_labels()
            ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
            
            ax2.grid(True, alpha=0.3, axis='y')
            
            # Colorear ejes
            ax2.tick_params(axis='y', labelcolor='orange')
            ax2_twin.tick_params(axis='y', labelcolor='red')
            
            plt.tight_layout()
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating HR analysis chart: {str(e)}")
            return self._create_error_chart("Error en análisis de RRHH")
    
    def _generate_price_vs_sales_correlation_chart(self, all_variables: List[Dict]) -> str:
        """Generar gráfico de correlación precio vs ventas"""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
            
            prices = []
            sales = []
            revenues = []
            days = []
            
            for idx, day_data in enumerate(all_variables):
                vars_dict = day_data['totales_por_variable']
                price = vars_dict.get('PRECIO DE VENTA DEL PRODUCTO', {}).get('total', 0) or vars_dict.get('PVP', {}).get('total', 0)
                sale = vars_dict.get('TOTAL PRODUCTOS VENDIDOS', {}).get('total', 0) or vars_dict.get('TPV', {}).get('total', 0)
                revenue = vars_dict.get('INGRESOS TOTALES', {}).get('total', 0) or vars_dict.get('IT', {}).get('total', 0)
                
                if price > 0:  # Solo incluir si hay precio
                    prices.append(price)
                    sales.append(sale)
                    revenues.append(revenue)
                    days.append(idx + 1)
            
            if prices and sales:
                # Gráfico de dispersión
                scatter = ax1.scatter(prices, sales, c=days, cmap='viridis', 
                                    s=100, alpha=0.7, edgecolors='black', linewidth=1)
                
                # Línea de tendencia
                if len(prices) > 1:
                    z = np.polyfit(prices, sales, 1)
                    p = np.poly1d(z)
                    ax1.plot(sorted(prices), p(sorted(prices)), 'r--',
                            linewidth=2, label=f'Elasticidad: {z[0]:.2f}')
                
                ax1.set_xlabel('Precio de Venta (Bs./L)', fontsize=12)
                ax1.set_ylabel('Productos Vendidos (L)', fontsize=12)
                ax1.set_title('Correlación Precio vs Ventas', fontsize=14, fontweight='bold')
                ax1.legend()
                ax1.grid(True, alpha=0.3)
                
                # Colorbar
                cbar = plt.colorbar(scatter, ax=ax1)
                cbar.set_label('Día', fontsize=10)
                
                # Gráfico de ingresos vs precio
                scatter2 = ax2.scatter(prices, revenues, c=days, cmap='plasma', 
                                     s=100, alpha=0.7, edgecolors='black', linewidth=1)
                
                # Curva de ingresos
                if len(prices) > 2:
                    # Ajuste polinomial de segundo grado para curva de ingresos
                    z2 = np.polyfit(prices, revenues, 2)
                    p2 = np.poly1d(z2)
                    x_smooth = np.linspace(min(prices), max(prices), 100)
                    ax2.plot(x_smooth, p2(x_smooth), 'g-', linewidth=2, 
                            label='Curva de Ingresos')
                
                ax2.set_xlabel('Precio de Venta (Bs./L)', fontsize=12)
                ax2.set_ylabel('Ingresos Totales (Bs.)', fontsize=12)
                ax2.set_title('Optimización de Ingresos por Precio', fontsize=14, fontweight='bold')
                ax2.legend()
                ax2.grid(True, alpha=0.3)
                
                # Colorbar
                cbar2 = plt.colorbar(scatter2, ax=ax2)
                cbar2.set_label('Día', fontsize=10)
            else:
                ax1.text(0.5, 0.5, 'No hay datos suficientes para correlación', 
                        ha='center', va='center', transform=ax1.transAxes)
                ax2.text(0.5, 0.5, 'No hay datos suficientes para correlación', 
                        ha='center', va='center', transform=ax2.transAxes)
            
            plt.tight_layout()
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating price vs sales chart: {str(e)}")
            return self._create_error_chart("Error en correlación precio-ventas")
    
    def _generate_key_financial_indicators_chart(self, totales_acumulativos: Dict) -> str:
        """Generar gráfico de indicadores financieros clave"""
        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            
            # Extraer indicadores
            indicators = {
                'ROI': totales_acumulativos.get('Retorno Inversión', {}).get('total', 0) or 
                       totales_acumulativos.get('RI', {}).get('total', 0),
                'Margen Bruto': totales_acumulativos.get('Margen Bruto', {}).get('total', 0) or 
                               totales_acumulativos.get('MB', {}).get('total', 0),
                'Rentabilidad': totales_acumulativos.get('Nivel de Rentabilidad', {}).get('total', 0) or 
                               totales_acumulativos.get('NR', {}).get('total', 0),
                'Rotación Inventario': totales_acumulativos.get('Rotación Inventario', {}).get('total', 0) or 
                                     totales_acumulativos.get('RTI', {}).get('total', 0),
                'Factor Utilización': totales_acumulativos.get('Factor Utilización', {}).get('total', 0) or 
                                    totales_acumulativos.get('FU', {}).get('total', 0),
                'Productividad': totales_acumulativos.get('Productividad Empleados', {}).get('total', 0) or 
                                totales_acumulativos.get('PE', {}).get('total', 0)
            }
            
            # Convertir valores a porcentajes donde sea apropiado
            indicators_pct = {
                'ROI': indicators['ROI'] * 100,
                'Margen Bruto': indicators['Margen Bruto'] * 100,
                'Rentabilidad': indicators['Rentabilidad'] * 100,
                'Factor Utilización': indicators['Factor Utilización'] * 100
            }
            
            # Gráfico 1: Indicadores de rentabilidad
            rent_indicators = ['ROI', 'Margen Bruto', 'Rentabilidad']
            rent_values = [indicators_pct.get(i, 0) for i in rent_indicators]
            colors1 = ['#3498db', '#2ecc71', '#f39c12']
            
            bars1 = ax1.bar(rent_indicators, rent_values, color=colors1)
            ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            ax1.set_ylabel('Porcentaje (%)', fontsize=12)
            ax1.set_title('Indicadores de Rentabilidad', fontsize=14, fontweight='bold')
            ax1.grid(True, alpha=0.3, axis='y')
            
            # Agregar valores en las barras
            for bar, value in zip(bars1, rent_values):
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{value:.1f}%', ha='center', 
                        va='bottom' if height >= 0 else 'top')
            
            # Gráfico 2: Eficiencia operativa
            if indicators['Factor Utilización'] > 0:
                # Gauge chart para factor de utilización
                utilization = indicators['Factor Utilización'] * 100
                
                # Crear semicírculo
                theta = np.linspace(0, np.pi, 100)
                r_inner = 0.7
                r_outer = 1.0
                
                # Zonas de color
                zones = [(0, 60, '#e74c3c'), (60, 80, '#f39c12'), (80, 100, '#2ecc71')]
                
                for start, end, color in zones:
                    mask = (theta >= start * np.pi / 100) & (theta <= end * np.pi / 100)
                    theta_zone = theta[mask]
                    if len(theta_zone) > 0:
                        x_outer = r_outer * np.cos(theta_zone)
                        y_outer = r_outer * np.sin(theta_zone)
                        x_inner = r_inner * np.cos(theta_zone)
                        y_inner = r_inner * np.sin(theta_zone)
                        
                        vertices = list(zip(x_outer, y_outer)) + list(zip(x_inner[::-1], y_inner[::-1]))
                        poly = plt.Polygon(vertices, color=color, alpha=0.7)
                        ax2.add_patch(poly)
                
                # Aguja indicadora
                angle = utilization * np.pi / 100
                ax2.arrow(0, 0, 0.85 * np.cos(angle), 0.85 * np.sin(angle),
                         head_width=0.05, head_length=0.05, fc='black', ec='black')
                
                ax2.text(0, -0.3, f'{utilization:.1f}%', ha='center', va='center', 
                        fontsize=20, fontweight='bold')
                ax2.set_xlim(-1.2, 1.2)
                ax2.set_ylim(-0.5, 1.2)
                ax2.set_aspect('equal')
                ax2.axis('off')
                ax2.set_title('Factor de Utilización de Capacidad', fontsize=14, fontweight='bold')
            
            # Gráfico 3: Rotación de inventario
            rotation_value = indicators['Rotación Inventario']
            target_rotation = 12  # Objetivo mensual
            
            ax3.barh(['Real', 'Objetivo'], [rotation_value, target_rotation], 
                    color=['#3498db' if rotation_value >= target_rotation else '#e74c3c', '#2ecc71'])
            ax3.set_xlabel('Veces/Mes', fontsize=12)
            ax3.set_title('Rotación de Inventario', fontsize=14, fontweight='bold')
            ax3.grid(True, alpha=0.3, axis='x')
            
            # Agregar valores
            ax3.text(rotation_value + 0.5, 0, f'{rotation_value:.1f}', va='center')
            ax3.text(target_rotation + 0.5, 1, f'{target_rotation}', va='center')
            
            # Gráfico 4: Productividad
            productivity = indicators['Productividad']
            num_employees = totales_acumulativos.get('NUMERO DE EMPLEADOS', {}).get('total', 15) or 15
            
            # Crear visualización de productividad por empleado
            employee_prod = productivity / num_employees if num_employees > 0 else 0
            
            # Gráfico de dona
            sizes = [employee_prod, 100 - min(employee_prod, 100)]
            colors4 = ['#2ecc71', '#ecf0f1']
            explode = (0.05, 0)
            
            wedges, texts = ax4.pie(sizes, colors=colors4, explode=explode, 
                                   startangle=90, counterclock=False)
            
            # Círculo central
            centre_circle = plt.Circle((0, 0), 0.70, fc='white')
            ax4.add_artist(centre_circle)
            
            # Texto central
            ax4.text(0, 0, f'{employee_prod:.0f}\nL/empleado', 
                    ha='center', va='center', fontsize=16, fontweight='bold')
            
            ax4.set_title('Productividad por Empleado', fontsize=14, fontweight='bold')
            ax4.axis('equal')
            
            # Título general
            fig.suptitle('Dashboard de Indicadores Financieros Clave', 
                        fontsize=18, fontweight='bold', y=0.98)
            
            plt.tight_layout()
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating financial indicators chart: {str(e)}")
            return self._create_error_chart("Error en indicadores financieros")
    
    def _fig_to_base64(self, fig) -> str:
        """Convertir figura matplotlib a base64"""
        try:
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            buffer.seek(0)
            image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
            buffer.close()
            plt.close(fig)
            return image_data
        except Exception as e:
            logger.error(f"Error converting figure to base64: {str(e)}")
            plt.close(fig)
            return ""
    
    def _create_error_chart(self, error_message: str) -> str:
        """Crear un gráfico de error cuando falla la generación"""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, f'Error: {error_message}', 
                   ha='center', va='center', transform=ax.transAxes,
                   fontsize=14, color='red')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            return self._fig_to_base64(fig)
        except:
            return ""