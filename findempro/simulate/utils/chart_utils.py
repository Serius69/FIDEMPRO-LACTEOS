# utils/chart_utils.py
"""
Enhanced chart generation utilities for simulation results.
Focuses on daily comparisons and trend analysis.
"""
import base64
import io
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
    
    def _generate_complete_variable_chart(self, var_key, var_data, var_type, all_variables_extracted):
        """
        Genera un gráfico COMPLETO mostrando la evolución de una variable a lo largo de TODOS los días
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            import matplotlib
            matplotlib.use('Agg')
            from io import BytesIO
            import base64
            import numpy as np
            from datetime import datetime
            
            # Extraer datos de TODOS los días para esta variable
            days = []
            simulated_values = []
            real_values = []
            dates = []
            
            # Iterar sobre todos los días de simulación
            for day_idx, day_data in enumerate(all_variables_extracted):
                day_num = day_idx + 1
                date = day_data.get('date_simulation')
                
                # Buscar esta variable en los datos del día
                if 'totales_por_variable' in day_data:
                    for var_name, var_info in day_data['totales_por_variable'].items():
                        if var_name == var_key or var_info.get('initials') == var_key:
                            simulated_value = var_info.get('total', 0)
                            if simulated_value != 0:  # Solo incluir valores no cero
                                days.append(day_num)
                                simulated_values.append(simulated_value)
                                dates.append(date)
                                
                                # Si hay valor real para este día, agregarlo
                                if var_data.get('daily_details', {}).get(str(day_num)):
                                    real_val = var_data['daily_details'][str(day_num)].get('real', 0)
                                    real_values.append(real_val)
                                else:
                                    real_values.append(None)
            
            # Validar que tenemos datos suficientes
            if len(days) < 2:
                logger.warning(f"Insufficient data for chart generation: {var_key}")
                return None
            
            # Crear figura más grande para mejor visualización
            fig, ax = plt.subplots(figsize=(14, 8))
            
            # Plot de valores simulados (línea continua)
            line_sim = ax.plot(days, simulated_values, 
                            marker='o', linewidth=3, markersize=6, 
                            alpha=0.8, color='#3498DB', 
                            markerfacecolor='white', 
                            markeredgecolor='#3498DB', 
                            markeredgewidth=2,
                            label='Valores Simulados')
            
            # Plot de valores reales si existen
            if any(v is not None for v in real_values):
                # Filtrar None values para el plot
                real_days = [d for d, v in zip(days, real_values) if v is not None]
                real_vals = [v for v in real_values if v is not None]
                
                if real_vals:
                    line_real = ax.plot(real_days, real_vals, 
                                    marker='s', linewidth=3, markersize=6,
                                    alpha=0.8, color='#E74C3C',
                                    markerfacecolor='white',
                                    markeredgecolor='#E74C3C',
                                    markeredgewidth=2,
                                    label='Valores Reales')
            
            # Agregar línea de tendencia
            if len(simulated_values) > 3:
                z = np.polyfit(days, simulated_values, 1)
                p = np.poly1d(z)
                ax.plot(days, p(days), "--", alpha=0.7, color='#2ECC71', 
                    linewidth=2, label=f'Tendencia (pendiente: {z[0]:.2f})')
            
            # Configurar título y etiquetas
            title = f"{var_key}: {var_data.get('description', '')}"
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel('Día de Simulación', fontsize=12, fontweight='bold')
            ax.set_ylabel(f"{var_data.get('unit', 'Valor')}", fontsize=12, fontweight='bold')
            
            # Grid mejorado
            ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
            ax.set_axisbelow(True)
            
            # Agregar información estadística
            mean_sim = np.mean(simulated_values)
            std_sim = np.std(simulated_values)
            
            # Área de desviación estándar
            ax.fill_between(days, 
                        [mean_sim - std_sim] * len(days), 
                        [mean_sim + std_sim] * len(days),
                        alpha=0.1, color='#3498DB', 
                        label=f'±1 Desv. Est.')
            
            # Línea de media
            ax.axhline(y=mean_sim, color='#3498DB', linestyle=':', 
                    linewidth=2, alpha=0.7,
                    label=f'Media: {mean_sim:.2f}')
            
            # Box de información
            info_text = f'Error: {var_data.get("error_pct", 0):.1f}%\n'
            info_text += f'Estado: {var_data.get("status", "UNKNOWN")}\n'
            info_text += f'Días: {len(days)}\n'
            info_text += f'Rango: [{min(simulated_values):.1f}, {max(simulated_values):.1f}]'
            
            # Color del box según estado
            box_color = {
                'PRECISA': '#27AE60',
                'ACEPTABLE': '#F39C12',
                'INEXACTA': '#E74C3C'
            }.get(var_data.get('status', 'UNKNOWN'), '#95A5A6')
            
            ax.text(0.02, 0.98, info_text, 
                transform=ax.transAxes, fontsize=11, fontweight='bold',
                verticalalignment='top', 
                bbox=dict(boxstyle='round,pad=0.8', 
                            facecolor=box_color, 
                            alpha=0.8,
                            edgecolor='black', 
                            linewidth=2))
            
            # Leyenda mejorada
            ax.legend(loc='upper right', fontsize=10, framealpha=0.9,
                    edgecolor='black', fancybox=True, shadow=True)
            
            # Ajustar layout
            plt.tight_layout()
            
            # Convertir a base64
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight', 
                    facecolor='white', edgecolor='none')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            logger.info(f"Successfully generated complete chart for {var_key} with {len(days)} days")
            
            return {
                'variable': var_key,
                'description': var_data.get('description', ''),
                'unit': var_data.get('unit', ''),
                'error_pct': var_data.get('error_pct', 0),
                'status': var_data.get('status', 'UNKNOWN'),
                'chart': chart_base64,
                'days_count': len(days),
                'coverage': (len(days) / len(all_variables_extracted)) * 100 if all_variables_extracted else 0,
                'real_value': var_data.get('real_value', 0),
                'simulated_avg': var_data.get('simulated_avg', 0),
                'total_points': len(simulated_values)
            }
            
        except Exception as e:
            logger.error(f"Error in complete chart generation for {var_key}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            plt.close('all')
            return None
    
    
    def generate_additional_analysis_charts(self, all_variables_extracted, totales_acumulativos):
        """
        Genera gráficos adicionales de análisis similar a los charts_generated
        """
        try:
            additional_charts = {}
            
            # Gráfico 1: Análisis de Costos Detallado
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            
            days = list(range(1, len(all_variables_extracted) + 1))
            
            # Extraer costos
            costos_produccion = []
            costos_operativos = []
            costos_totales = []
            
            for day_data in all_variables_extracted:
                costos_produccion.append(day_data.get('CPROD', 0))
                costos_operativos.append(day_data.get('GO', 0))
                costos_totales.append(day_data.get('TG', 0))
            
            # Gráfico de costos apilados
            ax1.fill_between(days, 0, costos_produccion, alpha=0.7, color='#3498DB', label='Costos Producción')
            ax1.fill_between(days, costos_produccion, 
                            [cp + co for cp, co in zip(costos_produccion, costos_operativos)], 
                            alpha=0.7, color='#E74C3C', label='Costos Operativos')
            
            ax1.set_xlabel('Días')
            ax1.set_ylabel('Costos (Bs)')
            ax1.set_title('Estructura de Costos Diarios')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Gráfico de eficiencia de costos
            ingresos = [day_data.get('IT', 0) for day_data in all_variables_extracted]
            margen = [(i - c) / i * 100 if i > 0 else 0 for i, c in zip(ingresos, costos_totales)]
            
            ax2.plot(days, margen, linewidth=2, color='#27AE60', marker='o')
            ax2.axhline(y=0, color='red', linestyle='--', alpha=0.5)
            ax2.fill_between(days, 0, margen, where=[m > 0 for m in margen], 
                            color='green', alpha=0.3, label='Ganancia')
            ax2.fill_between(days, margen, 0, where=[m < 0 for m in margen], 
                            color='red', alpha=0.3, label='Pérdida')
            
            ax2.set_xlabel('Días')
            ax2.set_ylabel('Margen (%)')
            ax2.set_title('Margen de Ganancia Diario')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            additional_charts['analisis_costos_detallado'] = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            # Gráfico 2: Análisis de Eficiencia Operativa
            fig, ax = plt.subplots(figsize=(12, 6))
            
            eficiencia_produccion = []
            utilizacion_capacidad = []
            
            for day_data in all_variables_extracted:
                ef_prod = day_data.get('EP', 0) * 100 if day_data.get('EP', 0) else 0
                util_cap = day_data.get('FU', 0) * 100 if day_data.get('FU', 0) else 0
                
                eficiencia_produccion.append(ef_prod)
                utilizacion_capacidad.append(util_cap)
            
            ax.plot(days, eficiencia_produccion, 'b-', linewidth=2, 
                    marker='o', label='Eficiencia Producción', markersize=4)
            ax.plot(days, utilizacion_capacidad, 'r-', linewidth=2, 
                    marker='s', label='Utilización Capacidad', markersize=4)
            
            # Líneas de referencia
            ax.axhline(y=80, color='green', linestyle='--', alpha=0.5, label='Meta 80%')
            ax.axhline(y=100, color='gray', linestyle='-', alpha=0.3)
            
            ax.set_xlabel('Días')
            ax.set_ylabel('Porcentaje (%)')
            ax.set_title('Indicadores de Eficiencia Operativa')
            ax.legend()
            ax.grid(True, alpha=0.3)
            ax.set_ylim(0, 110)
            
            plt.tight_layout()
            
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            additional_charts['eficiencia_operativa'] = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            return additional_charts
            
        except Exception as e:
            logger.error(f"Error generating additional charts: {str(e)}")
            return {}
    
    def generate_endogenous_variables_charts(self, all_variables_extracted, totales_acumulativos):
        """Generate comprehensive charts for endogenous variables"""
        endogenous_charts = {}
        
        try:
            # Variables principales para gráficos individuales
            key_variables = ['IT', 'GT', 'TG', 'TPV', 'NSC', 'EOG', 'NR']
            
            for var in key_variables:
                if self._has_variable_data(all_variables_extracted, var):
                    chart = self._generate_variable_time_series(all_variables_extracted, var)
                    if chart:
                        endogenous_charts[f'{var}_time_series'] = chart
            
            # Gráfico de correlaciones entre variables financieras
            financial_vars = ['IT', 'GT', 'TG', 'NR']
            correlation_chart = self._generate_correlation_matrix(all_variables_extracted, financial_vars)
            if correlation_chart:
                endogenous_charts['financial_correlations'] = correlation_chart
            
            # Gráfico de eficiencia operativa vs satisfacción
            efficiency_chart = self._generate_efficiency_satisfaction_scatter(all_variables_extracted)
            if efficiency_chart:
                endogenous_charts['efficiency_satisfaction'] = efficiency_chart
            
            # Gráfico de tendencias comparativas
            trends_chart = self._generate_comparative_trends(all_variables_extracted, key_variables)
            if trends_chart:
                endogenous_charts['comparative_trends'] = trends_chart
            
            # Gráfico de distribuciones
            distribution_chart = self._generate_variables_distribution(all_variables_extracted, key_variables)
            if distribution_chart:
                endogenous_charts['variables_distribution'] = distribution_chart
            
            logger.info(f"Generated {len(endogenous_charts)} endogenous variable charts")
            return endogenous_charts
            
        except Exception as e:
            logger.error(f"Error generating endogenous charts: {str(e)}")
            return {}

    def _has_variable_data(self, data, variable):
        """Check if variable has data across days"""
        if not data:
            return False
        
        values = [day.get(variable) for day in data if day.get(variable) is not None]
        return len(values) > 1
    
    def _generate_variable_time_series(self, data, variable):
        """Generate time series chart for a specific variable"""
        try:
            days = []
            values = []
            
            for i, day_data in enumerate(data):
                if variable in day_data and day_data[variable] is not None:
                    days.append(i + 1)
                    values.append(float(day_data[variable]))
            
            if len(values) < 2:
                return None
            
            plt.figure(figsize=(12, 6))
            plt.plot(days, values, marker='o', linewidth=2, markersize=6)
            plt.title(f'Evolución de {variable} a lo largo del tiempo', fontsize=14, fontweight='bold')
            plt.xlabel('Día de Simulación', fontsize=12)
            plt.ylabel(self._get_variable_unit(variable), fontsize=12)
            plt.grid(True, alpha=0.3)
            
            # Agregar línea de tendencia
            if len(values) > 3:
                z = np.polyfit(days, values, 1)
                p = np.poly1d(z)
                plt.plot(days, p(days), "--", alpha=0.8, color='red', label='Tendencia')
                plt.legend()
            
            # Mejorar el formato
            plt.tight_layout()
            
            # Convertir a base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return image_base64
            
        except Exception as e:
            logger.error(f"Error generating time series for {variable}: {str(e)}")
            plt.close()
            return None
    
    def _generate_correlation_matrix(self, data, variables):
        """Generate correlation matrix heatmap for specified variables"""
        try:
            # Extraer datos de variables
            var_data = {}
            for var in variables:
                values = []
                for day_data in data:
                    if var in day_data and day_data[var] is not None:
                        values.append(float(day_data[var]))
                    else:
                        values.append(0)
                var_data[var] = values
            
            if len(var_data) < 2:
                return None
            
            # Crear DataFrame para correlación
            df = pd.DataFrame(var_data)
            correlation_matrix = df.corr()
            
            plt.figure(figsize=(10, 8))
            sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0,
                       square=True, fmt='.2f', cbar_kws={'shrink': 0.8})
            plt.title('Matriz de Correlación - Variables Financieras', fontsize=14, fontweight='bold')
            plt.tight_layout()
            
            # Convertir a base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return image_base64
            
        except Exception as e:
            logger.error(f"Error generating correlation matrix: {str(e)}")
            plt.close()
            return None
    
    def _generate_efficiency_satisfaction_scatter(self, data):
        """Generate scatter plot of efficiency vs satisfaction"""
        try:
            efficiency = []
            satisfaction = []
            days = []
            
            for i, day_data in enumerate(data):
                if 'EOG' in day_data and 'NSC' in day_data:
                    if day_data['EOG'] is not None and day_data['NSC'] is not None:
                        efficiency.append(float(day_data['EOG']) * 100)
                        satisfaction.append(float(day_data['NSC']) * 100)
                        days.append(i + 1)
            
            if len(efficiency) < 3:
                return None
            
            plt.figure(figsize=(10, 8))
            scatter = plt.scatter(efficiency, satisfaction, c=days, cmap='viridis', 
                                s=60, alpha=0.7, edgecolors='white', linewidth=1)
            
            plt.xlabel('Eficiencia Operativa (%)', fontsize=12)
            plt.ylabel('Satisfacción del Cliente (%)', fontsize=12)
            plt.title('Relación: Eficiencia Operativa vs Satisfacción del Cliente', 
                     fontsize=14, fontweight='bold')
            
            # Agregar colorbar
            cbar = plt.colorbar(scatter)
            cbar.set_label('Día de Simulación', fontsize=10)
            
            # Agregar línea de tendencia
            if len(efficiency) > 3:
                z = np.polyfit(efficiency, satisfaction, 1)
                p = np.poly1d(z)
                x_trend = np.linspace(min(efficiency), max(efficiency), 100)
                plt.plot(x_trend, p(x_trend), "--", alpha=0.8, color='red', 
                        linewidth=2, label='Tendencia')
                plt.legend()
            
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # Convertir a base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return image_base64
            
        except Exception as e:
            logger.error(f"Error generating efficiency-satisfaction scatter: {str(e)}")
            plt.close()
            return None
    
    def _generate_comparative_trends(self, data, variables):
        """Generate comparative trends chart for multiple variables"""
        try:
            plt.figure(figsize=(14, 8))
            
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']
            
            for i, var in enumerate(variables):
                if not self._has_variable_data(data, var):
                    continue
                
                days = []
                values = []
                
                for j, day_data in enumerate(data):
                    if var in day_data and day_data[var] is not None:
                        days.append(j + 1)
                        # Normalizar valores para comparación
                        value = float(day_data[var])
                        if var in ['NSC', 'EOG', 'NR']:  # Variables porcentuales
                            value *= 100
                        values.append(value)
                
                if len(values) > 1:
                    # Normalizar para comparación visual
                    if max(values) != min(values):
                        normalized_values = [(v - min(values)) / (max(values) - min(values)) * 100 
                                           for v in values]
                    else:
                        normalized_values = [50] * len(values)
                    
                    plt.plot(days, normalized_values, marker='o', linewidth=2, 
                            markersize=4, label=var, color=colors[i % len(colors)])
            
            plt.title('Tendencias Comparativas de Variables Clave (Normalizadas)', 
                     fontsize=14, fontweight='bold')
            plt.xlabel('Día de Simulación', fontsize=12)
            plt.ylabel('Valor Normalizado (%)', fontsize=12)
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # Convertir a base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return image_base64
            
        except Exception as e:
            logger.error(f"Error generating comparative trends: {str(e)}")
            plt.close()
            return None
    
    def _generate_variables_distribution(self, data, variables):
        """Generate distribution plots for key variables"""
        try:
            # Calcular número de subplots
            n_vars = len([v for v in variables if self._has_variable_data(data, v)])
            if n_vars == 0:
                return None
            
            cols = min(3, n_vars)
            rows = (n_vars + cols - 1) // cols
            
            fig, axes = plt.subplots(rows, cols, figsize=(15, 5 * rows))
            if rows == 1 and cols == 1:
                axes = [axes]
            elif rows == 1:
                axes = axes
            else:
                axes = axes.flatten()
            
            plot_idx = 0
            
            for var in variables:
                if not self._has_variable_data(data, var):
                    continue
                
                values = []
                for day_data in data:
                    if var in day_data and day_data[var] is not None:
                        value = float(day_data[var])
                        if var in ['NSC', 'EOG', 'NR']:  # Variables porcentuales
                            value *= 100
                        values.append(value)
                
                if len(values) > 1:
                    ax = axes[plot_idx]
                    ax.hist(values, bins=min(10, len(values)//2 + 1), alpha=0.7, 
                           color='skyblue', edgecolor='black')
                    ax.set_title(f'Distribución: {var}', fontweight='bold')
                    ax.set_xlabel(self._get_variable_unit(var))
                    ax.set_ylabel('Frecuencia')
                    ax.grid(True, alpha=0.3)
                    
                    # Agregar estadísticas
                    mean_val = np.mean(values)
                    std_val = np.std(values)
                    ax.axvline(mean_val, color='red', linestyle='--', alpha=0.8, 
                              label=f'Media: {mean_val:.2f}')
                    ax.legend()
                    
                    plot_idx += 1
            
            # Ocultar subplots no utilizados
            for i in range(plot_idx, len(axes)):
                axes[i].set_visible(False)
            
            plt.suptitle('Distribuciones de Variables Endógenas', fontsize=16, fontweight='bold')
            plt.tight_layout()
            
            # Convertir a base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return image_base64
            
        except Exception as e:
            logger.error(f"Error generating variables distribution: {str(e)}")
            plt.close()
            return None
    
    def _get_variable_unit(self, variable):
        """Get appropriate unit for variable"""
        units = {
            'IT': 'Bolivianos (Bs.)',
            'GT': 'Bolivianos (Bs.)',
            'TG': 'Bolivianos (Bs.)',
            'TPV': 'Litros',
            'NSC': 'Porcentaje (%)',
            'EOG': 'Porcentaje (%)',
            'NR': 'Porcentaje (%)',
            'PVP': 'Bs./Litro',
            'DPH': 'Litros'
        }
        return units.get(variable, 'Unidades')
    
    def _generate_endogenous_variable_chart(self, var_key, days, values, dates, total_info):
        """
        Genera un gráfico individual para una variable endógena
        """
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            from io import BytesIO
            import base64
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Determinar el tipo de gráfico según la variable
            if var_key in ['IT', 'GT', 'GO', 'TG', 'CTAI', 'CTTL']:
                # Variables financieras - usar gráfico de área
                ax.fill_between(days, 0, values, alpha=0.3, color='#3498DB')
                ax.plot(days, values, linewidth=3, marker='o', markersize=5, 
                    color='#2980B9', label=var_key)
                
                # Agregar línea de cero si hay valores negativos
                if min(values) < 0:
                    ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
                    
            elif var_key in ['TPV', 'TPPRO', 'DI']:
                # Variables de producción/ventas - usar barras
                colors = ['#27AE60' if v >= 0 else '#E74C3C' for v in values]
                bars = ax.bar(days, values, color=colors, alpha=0.8, edgecolor='black', linewidth=1)
                
                # Agregar valores en las barras
                for bar, val in zip(bars, values):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{val:.0f}', ha='center', va='bottom' if height >= 0 else 'top',
                        fontsize=8)
            else:
                # Otras variables - línea simple
                ax.plot(days, values, linewidth=2, marker='s', markersize=4,
                    color='#8E44AD', label=var_key)
            
            # Agregar tendencia si hay suficientes puntos
            if len(values) > 5:
                z = np.polyfit(days, values, 1)
                p = np.poly1d(z)
                ax.plot(days, p(days), '--', alpha=0.7, color='#E74C3C', 
                    linewidth=2, label=f'Tendencia: {z[0]:.2f}x')
            
            # Estadísticas
            mean_val = np.mean(values)
            ax.axhline(y=mean_val, color='#F39C12', linestyle=':', 
                    linewidth=2, alpha=0.7,
                    label=f'Media: {mean_val:.2f}')
            
            # Configuración
            ax.set_xlabel('Día de Simulación', fontsize=12, fontweight='bold')
            ax.set_ylabel(total_info.get('unit', 'Valor'), fontsize=12, fontweight='bold')
            
            # Título descriptivo
            var_names = {
                'IT': 'INGRESOS TOTALES',
                'GT': 'GANANCIAS TOTALES',
                'GO': 'GASTOS OPERATIVOS',
                'TG': 'GASTOS TOTALES',
                'TPV': 'TOTAL PRODUCTOS VENDIDOS',
                'TPPRO': 'TOTAL PRODUCTOS PRODUCIDOS',
                'DI': 'DEMANDA INSATISFECHA',
                'CTAI': 'COSTO TOTAL ALMACENAMIENTO INSUMOS',
                'CTTL': 'COSTO TOTAL TRANSPORTE Y LOGÍSTICA',
                'CA': 'CLIENTES ATENDIDOS',
                'MP': 'MATERIA PRIMA',
                'MI': 'MANO DE OBRA INDIRECTA'
            }
            
            title = var_names.get(var_key, var_key)
            ax.set_title(f'{title} - Evolución Completa', fontsize=14, fontweight='bold', pad=20)
            
            # Grid y estilo
            ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
            ax.set_axisbelow(True)
            
            # Información adicional
            info_text = f'Total Acumulado: {total_info.get("total", sum(values)):.2f}\n'
            info_text += f'Promedio: {mean_val:.2f}\n'
            info_text += f'Mín/Máx: {min(values):.1f} / {max(values):.1f}'
            
            ax.text(0.02, 0.98, info_text, 
                transform=ax.transAxes, fontsize=10,
                verticalalignment='top', 
                bbox=dict(boxstyle='round,pad=0.5', 
                            facecolor='wheat', 
                            alpha=0.8))
            
            # Leyenda
            ax.legend(loc='upper right', fontsize=10, framealpha=0.9)
            
            # Layout
            plt.tight_layout()
            
            # Convertir a base64
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            return {
                'variable': var_key,
                'name': var_names.get(var_key, var_key),
                'chart': chart_base64,
                'total': total_info.get('total', sum(values)),
                'unit': total_info.get('unit', ''),
                'data_points': len(values)
            }
            
        except Exception as e:
            logger.error(f"Error creating endogenous chart: {str(e)}")
            plt.close('all')
            return None
    
    def _generate_validation_charts_for_variables(self, by_variable, results_simulation, all_variables_extracted):
        """Genera gráficos de validación optimizados para cada variable"""
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')
        import base64
        import numpy as np
        from io import BytesIO
        
        validation_charts = {}
        
        # CORRECCIÓN: Adaptar a la estructura real de datos
        # all_variables_extracted es una lista de diccionarios con las variables directamente
        
        # Pre-filtrar variables válidas
        variables_to_chart = {}
        for var_key, var_data in by_variable.items():
            # Verificar que la variable tiene datos simulados en all_variables_extracted
            has_data = False
            for day_data in all_variables_extracted:
                if var_key in day_data and day_data[var_key] != 0:
                    has_data = True
                    break
            
            if has_data and var_data.get('status') != 'NO_DATA':
                variables_to_chart[var_key] = var_data
        
        logger.info(f"Variables to chart after validation: {len(variables_to_chart)} of {len(by_variable)} total")
        
        # Limitar número de gráficos
        MAX_CHARTS_PER_TYPE = 20
        
        # Agrupar por tipo
        variables_by_type = {}
        for var_key, var_data in variables_to_chart.items():
            var_type = var_data.get('type', 'Otra')
            if var_type not in variables_by_type:
                variables_by_type[var_type] = {}
            variables_by_type[var_type][var_key] = var_data
        
        # Generar gráficos
        plt.rcParams['figure.max_open_warning'] = 0
        plt.rcParams['figure.dpi'] = 100
        
        for var_type, variables in variables_by_type.items():
            type_charts = []
            
            # Ordenar por error y tomar los más relevantes
            sorted_vars = sorted(variables.items(), 
                            key=lambda x: abs(x[1].get('error_pct', 0)), 
                            reverse=True)[:MAX_CHARTS_PER_TYPE]
            
            for var_key, var_data in sorted_vars:
                try:
                    # Generar gráfico completo con la estructura correcta
                    chart_data = self._generate_complete_variable_chart_corrected(
                        var_key, var_data, var_type, all_variables_extracted
                    )
                    
                    if chart_data:
                        type_charts.append(chart_data)
                        
                except Exception as e:
                    logger.error(f"Error generating chart for {var_key}: {str(e)}")
                    continue
            
            if type_charts:
                validation_charts[var_type] = type_charts
        
        # Generar gráfico resumen
        summary_chart = self._generate_compact_summary_chart(variables_by_type)
        if summary_chart:
            validation_charts['summary'] = summary_chart
        
        total_charts = sum(len(charts) for charts in validation_charts.values() if isinstance(charts, list))
        logger.info(f"Generated {total_charts} validation charts across {len(validation_charts)} types")
        
        return validation_charts

    def _generate_complete_variable_chart_corrected(self, var_key, var_data, var_type, all_variables_extracted):
        """
        Genera un gráfico completo con la estructura correcta de datos
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            from io import BytesIO
            import base64
            import numpy as np
            
            # Extraer datos de la estructura correcta
            days = []
            simulated_values = []
            dates = []
            
            # all_variables_extracted es una lista donde cada elemento tiene las variables directamente
            for day_idx, day_data in enumerate(all_variables_extracted):
                day_num = day_idx + 1
                
                # La variable está directamente en day_data
                if var_key in day_data:
                    value = day_data[var_key]
                    if value is not None and value != 0:
                        days.append(day_num)
                        simulated_values.append(float(value))
                        dates.append(day_data.get('date', f'Día {day_num}'))
            
            # Validar datos
            if len(days) < 2:
                logger.warning(f"Insufficient data for {var_key}: only {len(days)} points")
                return None
            
            # Crear figura
            fig, ax = plt.subplots(figsize=(14, 8))
            
            # Plot principal - valores simulados
            ax.plot(days, simulated_values, 
                    marker='o', linewidth=3, markersize=6, 
                    alpha=0.8, color='#3498DB', 
                    markerfacecolor='white', 
                    markeredgecolor='#3498DB', 
                    markeredgewidth=2,
                    label='Valores Simulados')
            
            # Si hay valor real constante, dibujarlo
            real_value = var_data.get('real_value', 0)
            if real_value != 0:
                ax.axhline(y=real_value, color='#E74C3C', linestyle='-', linewidth=3, 
                        alpha=0.8, label=f'Valor Real: {real_value:.2f}')
            
            # Línea de tendencia
            if len(simulated_values) > 3:
                z = np.polyfit(days, simulated_values, 1)
                p = np.poly1d(z)
                ax.plot(days, p(days), "--", alpha=0.7, color='#2ECC71', 
                    linewidth=2, label=f'Tendencia: {z[0]:.2f}x')
            
            # Estadísticas
            mean_sim = np.mean(simulated_values)
            std_sim = np.std(simulated_values)
            
            # Banda de desviación estándar
            ax.fill_between(days, 
                        [mean_sim - std_sim] * len(days), 
                        [mean_sim + std_sim] * len(days),
                        alpha=0.1, color='#3498DB')
            
            # Línea de media
            ax.axhline(y=mean_sim, color='#3498DB', linestyle=':', 
                    linewidth=2, alpha=0.7,
                    label=f'Media: {mean_sim:.2f}')
            
            # Configuración
            ax.set_xlabel('Día de Simulación', fontsize=12, fontweight='bold')
            ax.set_ylabel(f"{var_data.get('unit', 'Valor')}", fontsize=12, fontweight='bold')
            ax.set_title(f"{var_key}: {var_data.get('description', '')}", 
                        fontsize=16, fontweight='bold', pad=20)
            
            # Grid
            ax.grid(True, alpha=0.3)
            ax.set_axisbelow(True)
            
            # Box de información
            error_pct = var_data.get('error_pct', 0)
            status = var_data.get('status', 'UNKNOWN')
            
            info_text = f'Error: {error_pct:.1f}%\n'
            info_text += f'Estado: {status}\n'
            info_text += f'Puntos: {len(days)}\n'
            info_text += f'Rango: [{min(simulated_values):.1f}, {max(simulated_values):.1f}]'
            
            box_color = {
                'PRECISA': '#27AE60',
                'ACEPTABLE': '#F39C12',
                'INEXACTA': '#E74C3C'
            }.get(status, '#95A5A6')
            
            ax.text(0.02, 0.98, info_text, 
                transform=ax.transAxes, fontsize=11, fontweight='bold',
                verticalalignment='top', 
                bbox=dict(boxstyle='round,pad=0.8', 
                            facecolor=box_color, 
                            alpha=0.8,
                            edgecolor='black', 
                            linewidth=2))
            
            # Leyenda
            ax.legend(loc='upper right', fontsize=10, framealpha=0.9)
            
            plt.tight_layout()
            
            # Convertir a base64
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            return {
                'variable': var_key,
                'description': var_data.get('description', ''),
                'unit': var_data.get('unit', ''),
                'error_pct': error_pct,
                'status': status,
                'chart': chart_base64,
                'days_count': len(days),
                'coverage': (len(days) / len(all_variables_extracted)) * 100,
                'real_value': real_value,
                'simulated_avg': mean_sim,
                'total_points': len(simulated_values)
            }
            
        except Exception as e:
            logger.error(f"Error in chart generation for {var_key}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            plt.close('all')
            return None
    
    def _generate_compact_summary_chart(self, variables_by_type):
        """Genera un gráfico resumen compacto de validación"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            import numpy as np
            
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Preparar datos por tipo
            types = []
            avg_errors = []
            counts = []
            colors = []
            
            for var_type, variables in variables_by_type.items():
                if variables:
                    types.append(var_type)
                    errors = [v.get('error_pct', 0) for v in variables.values() if v.get('error_pct') is not None]
                    avg_error = np.mean(errors) if errors else 0
                    avg_errors.append(avg_error)
                    counts.append(len(variables))
                    
                    # Color según error promedio
                    if avg_error < 5:
                        colors.append('#27AE60')
                    elif avg_error < 15:
                        colors.append('#F39C12')
                    else:
                        colors.append('#E74C3C')
            
            if not types:
                plt.close(fig)
                return None
            
            # Crear gráfico de barras
            bars = ax.bar(types, avg_errors, color=colors, alpha=0.8, edgecolor='black', linewidth=1)
            
            # Agregar valores y conteos en las barras
            for bar, error, count in zip(bars, avg_errors, counts):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + max(avg_errors) * 0.01,
                        f'{error:.1f}%\n({count} vars)', 
                        ha='center', va='bottom', fontsize=10, fontweight='bold')
            
            # Líneas de referencia
            ax.axhline(y=5, color='green', linestyle='--', linewidth=2, alpha=0.7, label='Preciso (≤5%)')
            ax.axhline(y=15, color='orange', linestyle='--', linewidth=2, alpha=0.7, label='Aceptable (≤15%)')
            
            # Configuración
            ax.set_xlabel('Tipo de Variable', fontsize=12, fontweight='bold')
            ax.set_ylabel('Error Promedio (%)', fontsize=12, fontweight='bold')
            ax.set_title('Resumen de Validación por Tipo de Variable', fontsize=14, fontweight='bold', pad=20)
            ax.legend(loc='upper right', fontsize=10)
            ax.grid(True, alpha=0.3, axis='y')
            ax.set_ylim(0, max(avg_errors) * 1.3 if avg_errors else 20)
            
            # Mejorar etiquetas del eje x
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
            
            plt.tight_layout()
            
            # Convertir a base64
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight', facecolor='white')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            return chart_base64
            
        except Exception as e:
            logger.error(f"Error generating summary chart: {str(e)}")
            plt.close('all')
            return None

    def generate_validation_charts_context(self, validation_results):
        """
        Extrae los gráficos de validación y los prepara para el contexto HTML
        Retorna un diccionario con las imágenes en base64 listas para usar en HTML
        """
        context_charts = {}
        
        # Obtener los gráficos de validación
        validation_charts = validation_results.get('validation_charts', {})
        
        if not validation_charts:
            logger.warning("No validation charts found in results")
            return context_charts
        
        # 1. Gráfico resumen si existe
        if 'summary' in validation_charts and validation_charts['summary']:
            context_charts['validation_summary'] = {
                'image_data': validation_charts['summary'],
                'title': 'Resumen de Validación por Tipo de Variable',
                'description': 'Gráfico resumen mostrando el error promedio por tipo de variable'
            }
        
        # 2. Gráficos individuales por variable
        chart_counter = 1
        individual_charts = {}
        
        for var_type, charts_list in validation_charts.items():
            if var_type == 'summary':  # Skip summary, already handled
                continue
                
            if isinstance(charts_list, list):
                for chart_data in charts_list:
                    if chart_data and chart_data.get('chart'):
                        variable = chart_data.get('variable', f'var_{chart_counter}')
                        
                        # Crear clave única para cada gráfico
                        chart_key = f'validation_chart_{chart_counter}'
                        
                        individual_charts[chart_key] = {
                            'image_data': chart_data.get('chart', ''),
                            'variable': variable,
                            'title': f'Validación: {variable}',
                            'description': chart_data.get('description', 'Gráfico de validación'),
                            'error_pct': chart_data.get('error_pct', 0),
                            'status': chart_data.get('status', 'UNKNOWN'),
                            'unit': chart_data.get('unit', ''),
                            'days_count': chart_data.get('days_count', 0),
                            'coverage': chart_data.get('coverage', 0),
                            'var_type': var_type
                        }
                        chart_counter += 1
        
        # Agregar gráficos individuales al contexto
        if individual_charts:
            context_charts['individual_charts'] = individual_charts
            context_charts['total_charts'] = len(individual_charts)
        
        logger.info(f"Prepared {len(context_charts)} chart contexts for HTML rendering")
        
        return context_charts

    def _generate_single_validation_chart(self, var_key, var_data, var_type):
        """
        Generate single validation chart - VERSIÓN CORREGIDA Y OPTIMIZADA
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            import matplotlib
            matplotlib.use('Agg')
            from io import BytesIO
            import base64
            import numpy as np
            from datetime import datetime
            
            # CORRECCIÓN: Usar 'daily_details' correctamente
            daily_details = var_data.get('daily_details', {})
            
            if not daily_details:
                logger.warning(f"No daily_details found for {var_key}")
                return None
            
            # Extract and validate data for plotting
            days = []
            values = []
            
            for day, detail in daily_details.items():
                simulated_value = detail.get('simulated')
                if simulated_value is not None and simulated_value != 0:
                    days.append(day)
                    values.append(simulated_value)
            
            # Debug logging
            logger.info(f"Chart data for {var_key}: {len(days)} valid days, values range: {min(values) if values else 0}-{max(values) if values else 0}")
            
            if not days or not values or len(values) < 2:
                logger.warning(f"Insufficient valid data for chart generation: {var_key}")
                return None
            
            # Convert days to datetime objects if they're strings
            datetime_days = []
            for day in days:
                if isinstance(day, str):
                    try:
                        # Try different date formats
                        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']:
                            try:
                                datetime_days.append(datetime.strptime(day, fmt))
                                break
                            except ValueError:
                                continue
                        else:
                            # If no format works, use original string
                            datetime_days.append(day)
                    except:
                        datetime_days.append(day)
                else:
                    datetime_days.append(day)
            
            # Create figure and axis with better size
            fig, ax = plt.subplots(figsize=(14, 8))
            
            # Plot based on variable type with better styling
            if var_type in ['continuous', 'numeric', 'Numérica', 'Continua', 'Continuous', 'Numeric']:
                # Line plot for continuous variables
                line = ax.plot(datetime_days, values, marker='o', linewidth=3, markersize=6, 
                            alpha=0.8, color='#3498DB', markerfacecolor='white', 
                            markeredgecolor='#3498DB', markeredgewidth=2)
                ax.set_ylabel(f"{var_data.get('unit', 'Valor')}", fontsize=12, fontweight='bold')
                
                # Add trend line if enough data points
                if len(values) > 3:
                    x_numeric = np.arange(len(datetime_days))
                    z = np.polyfit(x_numeric, values, 1)
                    p = np.poly1d(z)
                    ax.plot(datetime_days, p(x_numeric), "--", alpha=0.7, color='#E74C3C', 
                        linewidth=2, label='Tendencia')
                    
            elif var_type in ['categorical', 'discrete', 'Categórica', 'Discreta', 'Categorical', 'Discrete']:
                # Bar plot for categorical variables
                bars = ax.bar(datetime_days, values, alpha=0.7, width=0.8, color='#F39C12', 
                            edgecolor='black', linewidth=1)
                ax.set_ylabel('Conteo/Frecuencia', fontsize=12, fontweight='bold')
                
                # Add value labels on bars
                for bar, value in zip(bars, values):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{value:.1f}', ha='center', va='bottom', fontsize=9)
                    
            else:
                # Default to line plot with different styling
                ax.plot(datetime_days, values, marker='s', linewidth=3, markersize=6, 
                    alpha=0.8, color='#27AE60', markerfacecolor='white',
                    markeredgecolor='#27AE60', markeredgewidth=2)
                ax.set_ylabel('Valor', fontsize=12, fontweight='bold')
            
            # Format x-axis for dates
            if len(datetime_days) > 1:
                try:
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                    ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(datetime_days)//8)))
                    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
                except:
                    # Fallback for non-datetime objects
                    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
            
            # Set title and labels with better formatting
            title = f"{var_key}"
            if var_data.get('description'):
                title += f"\n{var_data.get('description', '')[:60]}..."
                
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            ax.set_xlabel('Fecha', fontsize=12, fontweight='bold')
            
            # Add grid for better readability
            ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
            
            # Add status background color
            status = var_data.get('status', 'UNKNOWN')
            ylim = ax.get_ylim()
            if status == 'PRECISA':
                ax.axhspan(ylim[0], ylim[1], alpha=0.05, color='green')
            elif status == 'INEXACTA':
                ax.axhspan(ylim[0], ylim[1], alpha=0.05, color='red')
            elif status == 'ACEPTABLE':
                ax.axhspan(ylim[0], ylim[1], alpha=0.05, color='orange')
            
            # Add error percentage annotation with better styling
            error_pct = var_data.get('error_pct', 0)
            if error_pct > 0:
                color = '#E74C3C' if error_pct > 15 else '#F39C12' if error_pct > 5 else '#27AE60'
                ax.text(0.02, 0.98, f'Error: {error_pct:.1f}%\nEstado: {status}', 
                    transform=ax.transAxes, fontsize=11, fontweight='bold',
                    verticalalignment='top', 
                    bbox=dict(boxstyle='round,pad=0.5', facecolor=color, alpha=0.8, 
                            edgecolor='black', linewidth=1))
            
            # Add real value reference line if available
            real_value = var_data.get('real_value', 0)
            simulated_avg = var_data.get('simulated_avg', 0)
            
            if real_value != 0:
                ax.axhline(y=real_value, color='#E74C3C', linestyle='-', linewidth=3, 
                        alpha=0.8, label=f'Valor Real: {real_value:.2f}')
            
            if simulated_avg != 0 and simulated_avg != real_value:
                ax.axhline(y=simulated_avg, color='#3498DB', linestyle='--', linewidth=2, 
                        alpha=0.8, label=f'Promedio Simulado: {simulated_avg:.2f}')
            
            # Add legend if there are reference lines
            if real_value != 0 or simulated_avg != 0:
                ax.legend(loc='upper right', fontsize=10, framealpha=0.9)
            
            # Improve layout
            plt.tight_layout()
            
            # Convert to base64 with higher quality
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight', 
                    facecolor='white', edgecolor='none')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            logger.info(f"Successfully generated chart for {var_key}")
            
            return {
                'variable': var_key,
                'description': var_data.get('description', '')[:100],  # Más descripción
                'unit': var_data.get('unit', ''),
                'error_pct': var_data.get('error_pct', 0),
                'status': var_data.get('status', 'UNKNOWN'),
                'chart': chart_base64,
                'days_count': len(days),
                'coverage': var_data.get('coverage', 0),
                'real_value': var_data.get('real_value', 0),
                'simulated_avg': var_data.get('simulated_avg', 0)
            }
            
        except Exception as e:
            logger.error(f"Error in single chart generation for {var_key}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            plt.close('all')
            return None

    def get_html_ready_charts(self, validation_results):
        """
        Método adicional para obtener gráficos en formato HTML-ready
        Retorna HTML completo con las imágenes embebidas
        """
        context_charts = self.generate_validation_charts_context(validation_results)
        
        if not context_charts:
            return "<p>No se generaron gráficos de validación.</p>"
        
        html_content = []
        
        # Gráfico resumen
        if 'validation_summary' in context_charts:
            summary = context_charts['validation_summary']
            html_content.append(f"""
            <div class="chart-container">
                <h3>{summary['title']}</h3>
                <p>{summary['description']}</p>
                <img src="data:image/png;base64,{summary['image_data']}" 
                    alt="Gráfico Resumen de Validación" 
                    style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 8px;">
            </div>
            """)
        
        # Gráficos individuales
        if 'individual_charts' in context_charts:
            html_content.append("<h3>Gráficos Individuales de Validación</h3>")
            
            for chart_key, chart_info in context_charts['individual_charts'].items():
                status_color = {
                    'PRECISA': '#27AE60',
                    'ACEPTABLE': '#F39C12', 
                    'INEXACTA': '#E74C3C'
                }.get(chart_info['status'], '#7F8C8D')
                
                html_content.append(f"""
                <div class="chart-container" style="margin-bottom: 20px; padding: 15px; border: 2px solid {status_color}; border-radius: 10px;">
                    <h4 style="color: {status_color};">{chart_info['title']}</h4>
                    <div style="display: flex; gap: 10px; margin-bottom: 10px;">
                        <span style="background-color: {status_color}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 12px;">
                            {chart_info['status']}
                        </span>
                        <span style="background-color: #BDC3C7; color: #2C3E50; padding: 3px 8px; border-radius: 4px; font-size: 12px;">
                            Error: {chart_info['error_pct']:.1f}%
                        </span>
                        <span style="background-color: #BDC3C7; color: #2C3E50; padding: 3px 8px; border-radius: 4px; font-size: 12px;">
                            Días: {chart_info['days_count']}
                        </span>
                    </div>
                    <p style="font-size: 14px; color: #7F8C8D;">{chart_info['description']}</p>
                    <img src="data:image/png;base64,{chart_info['image_data']}" 
                        alt="Gráfico de Validación para {chart_info['variable']}" 
                        style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 8px;">
                </div>
                """)
        
        return ''.join(html_content)

    def debug_chart_generation(self, by_variable):
        """Debug method to check data structure"""
        logger.info("=== DEBUGGING CHART GENERATION ===")
        for var_key, var_data in by_variable.items():
            logger.info(f"\nVariable: {var_key}")
            logger.info(f"  Status: {var_data.get('status')}")
            logger.info(f"  Type: {var_data.get('type')}")
            logger.info(f"  Real value: {var_data.get('real_value')}")
            logger.info(f"  Simulated avg: {var_data.get('simulated_avg')}")
            logger.info(f"  Error pct: {var_data.get('error_pct')}")
            logger.info(f"  Simulated values count: {var_data.get('simulated_values_count')}")
            
            # Check daily_details structure
            daily_details = var_data.get('daily_details', {})
            logger.info(f"  Daily details keys: {list(daily_details.keys())[:3]}...")  # First 3 days
            
            if daily_details:
                first_day = list(daily_details.keys())[0]
                first_detail = daily_details[first_day]
                logger.info(f"  First day detail structure: {first_detail}")
                
                # Check if we have simulated values
                simulated_values = [d.get('simulated', 0) for d in daily_details.values()]
                logger.info(f"  Simulated values sample: {simulated_values[:5]}...")
                logger.info(f"  All zeros?: {all(v == 0 for v in simulated_values)}")
        logger.info("=== END DEBUG ===")
    
    def _generate_variable_comparison_charts(self, by_variable, real_values):
        """Genera gráficos comparativos para las variables validadas"""
        charts = {}
        
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            import base64
            from io import BytesIO
            
            # Gráfico 1: Comparación Real vs Simulado por Variable
            fig, ax = plt.subplots(figsize=(14, 8))
            
            variables = []
            real_vals = []
            sim_vals = []
            colors = []
            
            for var_key, var_data in by_variable.items():
                if var_data.get('status') != 'NO_DATA':
                    variables.append(var_data['description'][:20] + '...' if len(var_data['description']) > 20 else var_data['description'])
                    real_vals.append(var_data.get('real_value', 0))
                    sim_vals.append(var_data.get('simulated_avg', 0))
                    
                    # Color según estado
                    if var_data['status'] == 'PRECISA':
                        colors.append('green')
                    elif var_data['status'] == 'ACEPTABLE':
                        colors.append('orange')
                    else:
                        colors.append('red')
            
            if variables:
                x = range(len(variables))
                width = 0.35
                
                bars1 = ax.bar([i - width/2 for i in x], real_vals, width, 
                            label='Valor Real', alpha=0.8, color='steelblue')
                bars2 = ax.bar([i + width/2 for i in x], sim_vals, width,
                            label='Valor Simulado', alpha=0.8)
                
                # Colorear barras simuladas según precisión
                for bar, color in zip(bars2, colors):
                    bar.set_color(color)
                
                ax.set_xlabel('Variables', fontsize=12)
                ax.set_ylabel('Valor', fontsize=12)
                ax.set_title('Comparación de Variables: Real vs Simulado', fontsize=16, fontweight='bold')
                ax.set_xticks(x)
                ax.set_xticklabels(variables, rotation=45, ha='right')
                ax.legend()
                ax.grid(True, alpha=0.3, axis='y')
                
                plt.tight_layout()
                
                # Convertir a base64
                buffer = BytesIO()
                fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
                buffer.seek(0)
                charts['comparison_bar'] = base64.b64encode(buffer.getvalue()).decode('utf-8')
                plt.close(fig)
            
            # Gráfico 2: Distribución de Errores
            fig2, ax2 = plt.subplots(figsize=(10, 6))
            
            errors = []
            labels = []
            colors_pie = []
            
            precise = sum(1 for v in by_variable.values() if v.get('status') == 'PRECISA')
            acceptable = sum(1 for v in by_variable.values() if v.get('status') == 'ACEPTABLE')
            inaccurate = sum(1 for v in by_variable.values() if v.get('status') == 'INEXACTA')
            
            if precise > 0:
                errors.append(precise)
                labels.append(f'Precisas ({precise})')
                colors_pie.append('green')
            
            if acceptable > 0:
                errors.append(acceptable)
                labels.append(f'Aceptables ({acceptable})')
                colors_pie.append('orange')
            
            if inaccurate > 0:
                errors.append(inaccurate)
                labels.append(f'Inexactas ({inaccurate})')
                colors_pie.append('red')
            
            if errors:
                ax2.pie(errors, labels=labels, colors=colors_pie, autopct='%1.1f%%',
                    startangle=90, textprops={'fontsize': 12})
                ax2.set_title('Distribución de Precisión de Variables', fontsize=16, fontweight='bold')
                
                # Convertir a base64
                buffer2 = BytesIO()
                fig2.savefig(buffer2, format='png', dpi=100, bbox_inches='tight')
                buffer2.seek(0)
                charts['error_distribution'] = base64.b64encode(buffer2.getvalue()).decode('utf-8')
                plt.close(fig2)
            
        except Exception as e:
            logger.error(f"Error generating comparison charts: {str(e)}")
        
        return charts
    
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
    
    def create_enhanced_chart_data(self, results_simulation, historical_demand):
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
    
    def generate_validation_comparison_chart(self, real_values, projected_values, simulated_values, dates=None):
        """
        Generate validation comparison chart with proper overlay of three lines
        """
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), 
                                        gridspec_kw={'height_ratios': [3, 1]})
            
            # Clean data
            real_values = [float(v) for v in real_values if v is not None] if real_values else []
            projected_values = [float(v) for v in projected_values if v is not None] if projected_values else []
            simulated_values = [float(v) for v in simulated_values if v is not None] if simulated_values else []
            
            logger.info(f"Generating chart - Real: {len(real_values)}, Projected: {len(projected_values)}, Simulated: {len(simulated_values)}")
            
            if not any([real_values, simulated_values]):
                plt.close(fig)
                return None
            
            # IMPORTANT: Create unified time axis
            # The key is that simulated values should start at period 1, same as historical
            
            # Plot 1: Historical/Real demand (blue solid line)
            if real_values:
                hist_periods = list(range(1, len(real_values) + 1))
                ax1.plot(hist_periods, real_values, 'b-', marker='o', markersize=6, 
                        linewidth=2.5, label='Demanda Real Histórica', alpha=0.9, zorder=2)
                
                # Add mean line for historical
                hist_mean = np.mean(real_values)
                ax1.axhline(y=hist_mean, color='blue', linestyle=':', alpha=0.4,
                        label=f'Media Real: {hist_mean:.1f}')
            
            # Plot 2: Projected demand (red solid line) - starts after historical
            if projected_values and real_values:
                # Projection starts right after historical data
                proj_start = len(real_values)
                proj_periods = list(range(proj_start + 1, proj_start + 1 + len(projected_values)))
                
                # Connect last historical to first projected
                ax1.plot([hist_periods[-1], proj_periods[0]], 
                        [real_values[-1], projected_values[0]], 
                        'r-', linewidth=2, alpha=0.7)
                
                # Plot projection
                ax1.plot(proj_periods, projected_values, 'r-', marker='s', markersize=5,
                        linewidth=2.5, label='Demanda Proyectada', alpha=0.9, zorder=2)
                
                # Add mean line for projected
                proj_mean = np.mean(projected_values)
                ax1.axhline(y=proj_mean, color='red', linestyle=':', alpha=0.4,
                        label=f'Media Proyectada: {proj_mean:.1f}')
            
            # Plot 3: Simulated demand (green dashed line) - OVERLAYS everything
            if simulated_values:
                # CRITICAL: Simulated values start at period 1, same as historical
                sim_periods = list(range(1, len(simulated_values) + 1))
                
                # Split simulated into historical period and future period for different styling
                if real_values:
                    hist_length = len(real_values)
                    
                    # Part 1: Overlay on historical period (thicker line for validation)
                    if len(simulated_values) >= hist_length:
                        sim_hist_periods = sim_periods[:hist_length]
                        sim_hist_values = simulated_values[:hist_length]
                        ax1.plot(sim_hist_periods, sim_hist_values, 'g--', marker='^', markersize=5,
                                linewidth=3, label='Demanda Simulada (validación)', alpha=0.8, zorder=3)
                        
                        # Part 2: Continue into future (if simulation extends beyond historical)
                        if len(simulated_values) > hist_length:
                            sim_future_periods = sim_periods[hist_length-1:]  # Include connection point
                            sim_future_values = simulated_values[hist_length-1:]
                            ax1.plot(sim_future_periods, sim_future_values, 'g--', marker='^', markersize=4,
                                    linewidth=2.5, alpha=0.7, zorder=3)
                    else:
                        # Simulation shorter than historical
                        ax1.plot(sim_periods, simulated_values, 'g--', marker='^', markersize=5,
                                linewidth=3, label='Demanda Simulada', alpha=0.8, zorder=3)
                else:
                    # No historical data, just plot simulated
                    ax1.plot(sim_periods, simulated_values, 'g--', marker='^', markersize=5,
                            linewidth=2.5, label='Demanda Simulada', alpha=0.8, zorder=3)
                
                # Add mean line for simulated
                sim_mean = np.mean(simulated_values)
                ax1.axhline(y=sim_mean, color='green', linestyle=':', alpha=0.4,
                        label=f'Media Simulada: {sim_mean:.1f}')
            
            # Add vertical line to mark end of historical period
            if real_values:
                ax1.axvline(x=len(real_values), color='gray', linestyle=':', alpha=0.5,
                        label='Inicio Proyección', linewidth=2)
            
            # Configure main plot
            ax1.set_xlabel('Período de Tiempo', fontsize=12)
            ax1.set_ylabel('Demanda (Litros)', fontsize=12)
            ax1.set_title('Validación del Modelo: Comparación Real vs Simulada vs Proyectada', 
                        fontsize=16, fontweight='bold', pad=20)
            
            # Improve legend
            ax1.legend(loc='best', frameon=True, fancybox=True, shadow=True, ncol=2)
            ax1.grid(True, alpha=0.3, linestyle='--')
            ax1.set_facecolor('#fafafa')
            
            # Set appropriate axis limits
            all_values = []
            if real_values: all_values.extend(real_values)
            if projected_values: all_values.extend(projected_values)
            if simulated_values: all_values.extend(simulated_values)
            
            if all_values:
                y_margin = (max(all_values) - min(all_values)) * 0.1
                ax1.set_ylim(min(all_values) - y_margin, max(all_values) + y_margin)
            
            # Error plot (bottom) - Compare real vs simulated in overlapping period
            if real_values and simulated_values:
                min_len = min(len(real_values), len(simulated_values))
                if min_len > 0:
                    errors = []
                    error_periods = []
                    
                    for i in range(min_len):
                        if real_values[i] != 0:
                            error = ((simulated_values[i] - real_values[i]) / real_values[i]) * 100
                            errors.append(error)
                            error_periods.append(i + 1)
                    
                    if errors:
                        # Color bars based on error magnitude
                        colors = []
                        for e in errors:
                            if abs(e) < 5:
                                colors.append('darkgreen')
                            elif abs(e) < 10:
                                colors.append('green')
                            elif abs(e) < 15:
                                colors.append('orange')
                            else:
                                colors.append('red')
                        
                        bars = ax2.bar(error_periods, errors, color=colors, alpha=0.7, width=0.8)
                        
                        # Add value labels on bars
                        for bar, err in zip(bars, errors):
                            if abs(err) > 2:  # Only show label if error is significant
                                height = bar.get_height()
                                ax2.text(bar.get_x() + bar.get_width()/2., height,
                                        f'{err:.1f}%', ha='center', 
                                        va='bottom' if height >= 0 else 'top',
                                        fontsize=8)
                        
                        # Reference lines
                        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
                        ax2.axhline(y=10, color='orange', linestyle='--', alpha=0.3, label='±10%')
                        ax2.axhline(y=-10, color='orange', linestyle='--', alpha=0.3)
                        ax2.axhline(y=20, color='red', linestyle='--', alpha=0.3, label='±20%')
                        ax2.axhline(y=-20, color='red', linestyle='--', alpha=0.3)
                        
                        # Calculate and display MAPE
                        mape = np.mean(np.abs(errors))
                        ax2.text(0.02, 0.95, f'MAPE: {mape:.2f}%', transform=ax2.transAxes,
                                verticalalignment='top', fontsize=11, fontweight='bold',
                                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
                        
                        # Add accuracy interpretation
                        accuracy_text = ""
                        if mape < 5:
                            accuracy_text = "Excelente"
                            text_color = 'darkgreen'
                        elif mape < 10:
                            accuracy_text = "Muy Buena"
                            text_color = 'green'
                        elif mape < 15:
                            accuracy_text = "Buena"
                            text_color = 'orange'
                        elif mape < 20:
                            accuracy_text = "Aceptable"
                            text_color = 'darkorange'
                        else:
                            accuracy_text = "Mejorable"
                            text_color = 'red'
                        
                        ax2.text(0.98, 0.95, f'Precisión: {accuracy_text}', transform=ax2.transAxes,
                                verticalalignment='top', horizontalalignment='right',
                                fontsize=11, fontweight='bold', color=text_color)
                    
                    ax2.set_xlabel('Período de Tiempo', fontsize=12)
                    ax2.set_ylabel('Error (%)', fontsize=12)
                    ax2.set_title('Error Porcentual: Simulado vs Real', fontsize=14)
                    ax2.legend(loc='upper right')
                    ax2.grid(True, alpha=0.3, axis='y')
                    ax2.set_facecolor('#fafafa')
                    
                    # Set x-axis to match main plot
                    ax2.set_xlim(ax1.get_xlim())
            else:
                ax2.text(0.5, 0.5, 'No hay suficientes datos para calcular errores', 
                        transform=ax2.transAxes, ha='center', va='center',
                        fontsize=12, color='gray')
                ax2.set_facecolor('#fafafa')
            
            plt.tight_layout()
            
            # Convert to base64
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight', 
                    facecolor='white', edgecolor='none')
            buffer.seek(0)
            image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
            buffer.close()
            plt.close(fig)
            
            logger.info("Validation comparison chart generated successfully")
            return image_data
            
        except Exception as e:
            logger.error(f"Error generating validation comparison chart: {str(e)}")
            logger.exception("Full traceback:")
            if 'fig' in locals():
                plt.close(fig)
            return None
    
    def generate_enhanced_demand_comparison(self, historical_demand, simulated_results, real_values=None):
        """
        Generate enhanced demand comparison with historical, simulated and optionally real validation data
        """
        try:
            # Create figure with subplots
            fig = plt.figure(figsize=(16, 12))
            gs = fig.add_gridspec(3, 2, height_ratios=[2, 1, 1], hspace=0.3, wspace=0.3)
            
            # Main comparison plot
            ax_main = fig.add_subplot(gs[0, :])
            
            # Extract data
            simulated_demand = [float(r.demand_mean) for r in simulated_results]
            
            # Time periods
            if historical_demand:
                hist_time = list(range(1, len(historical_demand) + 1))
                sim_start = len(historical_demand) + 1
            else:
                sim_start = 1
            
            sim_time = list(range(sim_start, sim_start + len(simulated_demand)))
            
            # Plot historical demand
            if historical_demand:
                ax_main.plot(hist_time, historical_demand, 'b-', marker='o', markersize=5,
                            linewidth=2.5, label='Demanda Histórica', alpha=0.9)
                
                # Historical statistics
                hist_mean = np.mean(historical_demand)
                ax_main.axhline(y=hist_mean, color='blue', linestyle=':', alpha=0.4,
                            label=f'Media Histórica: {hist_mean:.1f}')
            
            # Plot simulated demand
            ax_main.plot(sim_time, simulated_demand, 'r-', marker='s', markersize=5,
                        linewidth=2.5, label='Demanda Simulada', alpha=0.9)
            
            # Simulated statistics
            sim_mean = np.mean(simulated_demand)
            ax_main.axhline(y=sim_mean, color='red', linestyle=':', alpha=0.4,
                        label=f'Media Simulada: {sim_mean:.1f}')
            
            # If real values provided, overlay them
            if real_values:
                real_time = list(range(1, len(real_values) + 1))
                ax_main.plot(real_time, real_values, 'g--', marker='^', markersize=4,
                            linewidth=2, label='Valores Reales (Validación)', alpha=0.8)
                
                real_mean = np.mean(real_values)
                ax_main.axhline(y=real_mean, color='green', linestyle=':', alpha=0.4,
                            label=f'Media Real: {real_mean:.1f}')
            
            # Transition line
            if historical_demand:
                ax_main.axvline(x=len(historical_demand) + 0.5, color='gray', 
                            linestyle='--', alpha=0.5, label='Inicio Simulación')
            
            # Configure main plot
            ax_main.set_xlabel('Período de Tiempo (días)', fontsize=12)
            ax_main.set_ylabel('Demanda (Litros)', fontsize=12)
            ax_main.set_title('Análisis Completo de Demanda: Histórica, Simulada y Validación', 
                            fontsize=16, fontweight='bold', pad=20)
            ax_main.legend(loc='best', frameon=True, fancybox=True, shadow=True)
            ax_main.grid(True, alpha=0.3, linestyle='--')
            ax_main.set_facecolor('#f8f9fa')
            
            # Distribution comparison (bottom left)
            ax_dist = fig.add_subplot(gs[1, 0])
            
            # Create histograms
            if historical_demand:
                ax_dist.hist(historical_demand, bins=20, alpha=0.5, label='Histórico',
                            color='blue', density=True, edgecolor='black')
            ax_dist.hist(simulated_demand, bins=20, alpha=0.5, label='Simulado',
                        color='red', density=True, edgecolor='black')
            if real_values:
                ax_dist.hist(real_values, bins=20, alpha=0.5, label='Real',
                            color='green', density=True, edgecolor='black')
            
            ax_dist.set_xlabel('Demanda (Litros)')
            ax_dist.set_ylabel('Densidad')
            ax_dist.set_title('Distribución de Probabilidad')
            ax_dist.legend()
            ax_dist.grid(True, alpha=0.3)
            
            # Box plots comparison (bottom right)
            ax_box = fig.add_subplot(gs[1, 1])
            
            box_data = []
            box_labels = []
            
            if historical_demand:
                box_data.append(historical_demand)
                box_labels.append('Histórico')
            box_data.append(simulated_demand)
            box_labels.append('Simulado')
            if real_values:
                box_data.append(real_values)
                box_labels.append('Real')
            
            bp = ax_box.boxplot(box_data, labels=box_labels, patch_artist=True)
            colors = ['lightblue', 'lightcoral', 'lightgreen'][:len(box_data)]
            for patch, color in zip(bp['boxes'], colors):
                patch.set_facecolor(color)
            
            ax_box.set_ylabel('Demanda (Litros)')
            ax_box.set_title('Comparación de Rangos')
            ax_box.grid(True, alpha=0.3)
            
            # Metrics comparison (bottom)
            ax_metrics = fig.add_subplot(gs[2, :])
            ax_metrics.axis('off')
            
            # Calculate metrics
            metrics_text = "📊 **MÉTRICAS DE VALIDACIÓN**\n\n"
            
            if historical_demand and simulated_demand:
                # Compare last historical with first simulated
                if len(historical_demand) > 0 and len(simulated_demand) > 0:
                    transition_error = abs(historical_demand[-1] - simulated_demand[0])
                    metrics_text += f"Error de transición: {transition_error:.2f} litros\n"
            
            if real_values and simulated_demand:
                # Calculate validation metrics
                min_len = min(len(real_values), len(simulated_demand))
                if min_len > 0:
                    real_compare = real_values[:min_len]
                    sim_compare = simulated_demand[:min_len]
                    
                    mape = np.mean(np.abs((np.array(real_compare) - np.array(sim_compare)) / np.array(real_compare))) * 100
                    rmse = np.sqrt(np.mean((np.array(real_compare) - np.array(sim_compare))**2))
                    mae = np.mean(np.abs(np.array(real_compare) - np.array(sim_compare)))
                    
                    metrics_text += f"\nMAPE: {mape:.2f}%\n"
                    metrics_text += f"RMSE: {rmse:.2f} litros\n"
                    metrics_text += f"MAE: {mae:.2f} litros\n"
                    
                    if mape < 10:
                        metrics_text += "\n✅ Precisión: EXCELENTE"
                    elif mape < 20:
                        metrics_text += "\n✅ Precisión: BUENA"
                    elif mape < 30:
                        metrics_text += "\n⚠️ Precisión: ACEPTABLE"
                    else:
                        metrics_text += "\n❌ Precisión: MEJORABLE"
            
            ax_metrics.text(0.5, 0.5, metrics_text, transform=ax_metrics.transAxes,
                        fontsize=12, ha='center', va='center',
                        bbox=dict(boxstyle='round,pad=1', facecolor='wheat', alpha=0.8))
            
            plt.suptitle('Sistema de Validación de Simulación de Demanda', 
                        fontsize=18, fontweight='bold', y=0.98)
            
            # Convert to base64
            image_data = self._save_plot_as_base64(fig)
            plt.close(fig)
            
            return image_data
            
        except Exception as e:
            logger.error(f"Error generating enhanced demand comparison: {str(e)}")
            if 'fig' in locals():
                plt.close(fig)
            return None    

    
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