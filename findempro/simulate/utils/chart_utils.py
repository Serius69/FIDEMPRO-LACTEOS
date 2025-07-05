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
import scipy.stats as stats

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
import seaborn as sns
from datetime import datetime, timedelta
from django.db.models import Q

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
    
    def _set_smart_x_ticks(self, ax, data_length, max_ticks=10):
        """
        Establece ticks del eje X de forma inteligente para evitar errores
        """
        try:
            if data_length <= max_ticks:
                tick_positions = list(range(data_length))
                tick_labels = [f'D{i+1}' for i in range(data_length)]
            else:
                interval = max(1, data_length // max_ticks)
                tick_positions = list(range(0, data_length, interval))
                if tick_positions[-1] != data_length - 1:
                    tick_positions.append(data_length - 1)
                tick_labels = [f'D{i+1}' for i in tick_positions]
            
            ax.set_xticks(tick_positions)
            ax.set_xticklabels(tick_labels, rotation=45, ha='right')
            return True
        except Exception as e:
            logger.error(f"Error setting smart ticks: {e}")
            return False
    
    def _apply_safe_layout(self, fig=None):
        """
        CORRECCIÓN: Aplicar layout seguro sin warnings de matplotlib
        """
        try:
            if fig is not None:
                fig.tight_layout(pad=1.0)
            else:
                import matplotlib.pyplot as plt
                plt.tight_layout(pad=1.0)
        except Exception as e:
            # Fallback a subplots_adjust manual
            try:
                if fig is not None:
                    fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.15, 
                                    hspace=0.3, wspace=0.3)
                else:
                    import matplotlib.pyplot as plt
                    plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.15, 
                                    hspace=0.3, wspace=0.3)
            except Exception as e2:
                logger.warning(f"Could not apply layout adjustments: {e2}")
    
    
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
            
            try:
                plt.tight_layout()
            except:
                plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
            
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
                
            logger.info(f"Available variables in first day: {list(all_variables_extracted[0].keys()) if all_variables_extracted else 'No data'}")           
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
            try:
                plt.tight_layout()
            except:
                plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
            
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
            try:
                plt.tight_layout()
            except:
                plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
            
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

                # SOLUCIÓN: Agregar validación
                if len(efficiency) > 1 and np.var(efficiency) > 1e-10:
                    z = np.polyfit(efficiency, satisfaction, 1)
                else:
                    z = [0, np.mean(satisfaction) if satisfaction else 0]
                p = np.poly1d(z)
                x_trend = np.linspace(min(efficiency), max(efficiency), 100)
                plt.plot(x_trend, p(x_trend), "--", alpha=0.8, color='red', 
                        linewidth=2, label='Tendencia')
                plt.legend()
            
            plt.grid(True, alpha=0.3)
            try:
                plt.tight_layout()
            except:
                plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
            
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
            try:
                plt.tight_layout()
            except:
                plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
            
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
            try:
                plt.tight_layout()
            except:
                plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
            
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
            try:
                plt.tight_layout()
            except:
                plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
            
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
            
            try:
                plt.tight_layout()
            except:
                plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
            
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
            
            try:
                plt.tight_layout()
            except:
                plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
            
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
            
            try:
                plt.tight_layout()
            except:
                plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
            
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
                
                try:
                    plt.tight_layout()
                except:
                    plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
                
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
        
        try:
            plt.tight_layout()
        except:
            plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
            
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
    
    def _apply_safe_layout(self, fig=None):
        """
        CORRECCIÓN: Aplicar layout seguro sin warnings de matplotlib
        """
        try:
            if fig is not None:
                fig.tight_layout(pad=1.0)
            else:
                import matplotlib.pyplot as plt
                plt.tight_layout(pad=1.0)
        except Exception as e:
            # Fallback a subplots_adjust manual
            try:
                if fig is not None:
                    fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1, 
                                    hspace=0.3, wspace=0.3)
                else:
                    import matplotlib.pyplot as plt
                    plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1, 
                                    hspace=0.3, wspace=0.3)
            except Exception as e2:
                logger.warning(f"Could not apply layout adjustments: {e2}")
    
    
    def generate_dashboard_charts_fixed(self, all_variables_extracted, totales_acumulativos):
        """CORRECCIÓN: Generar gráficos del dashboard con datos reales"""
        
        charts = {}
        
        try:
            # CORRECCIÓN 1: Verificar que hay datos
            if not all_variables_extracted or len(all_variables_extracted) == 0:
                logger.warning("No data available for chart generation")
                return {}
            
            # CORRECCIÓN 2: Extraer datos de forma segura
            days = [d.get('day', i+1) for i, d in enumerate(all_variables_extracted)]
            
            # CORRECCIÓN 3: Gráfico financiero con validación
            revenues = []
            profits = []
            for day_data in all_variables_extracted:
                revenues.append(float(day_data.get('IT', 0)))
                profits.append(float(day_data.get('GT', 0)))
            
            if any(revenues) or any(profits):
                charts['financial_overview'] = self._create_financial_chart(days, revenues, profits)
            
            # CORRECCIÓN 4: Gráfico de eficiencia con validación
            efficiencies = []
            service_levels = []
            for day_data in all_variables_extracted:
                efficiencies.append(float(day_data.get('EOG', 0.8)) * 100)
                service_levels.append(float(day_data.get('NSC', 0.85)) * 100)
            
            if any(efficiencies) or any(service_levels):
                charts['efficiency_overview'] = self._create_efficiency_chart(days, efficiencies, service_levels)
            
            # CORRECCIÓN 5: Gráfico de producción
            production = [float(d.get('QPL', 0)) for d in all_variables_extracted]
            sales = [float(d.get('TPV', 0)) for d in all_variables_extracted]
            
            if any(production) or any(sales):
                charts['production_overview'] = self._create_production_chart(days, production, sales)
            
            logger.info(f"Generated {len(charts)} dashboard charts successfully")
            return charts
            
        except Exception as e:
            logger.error(f"Error generating dashboard charts: {str(e)}")
            return {}
    
    
    def _safe_fig_to_base64(self, fig):
        """Convertir figura a base64 de forma segura"""
        try:
            from io import BytesIO
            import base64
            
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
            buffer.seek(0)
            image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
            buffer.close()
            
            import matplotlib.pyplot as plt
            plt.close(fig)
            
            return image_data
            
        except Exception as e:
            logger.error(f"Error converting figure to base64: {str(e)}")
            import matplotlib.pyplot as plt
            plt.close(fig)
            return None
    
    
    def _process_accumulated_variables_safely(self, all_variables_extracted):
        """
        CORRECCIÓN: Procesar variables acumuladas con manejo de errores robusto
        """
        try:
            # Lista de variables esperadas (verificar que existan)
            expected_variables = [
                'PVP', 'TPV', 'IT', 'TG', 'GT', 'NR', 'NSC', 'EOG', 
                'CFD', 'CVU', 'DPH', 'CPROD', 'NEPP', 'RI', 'IPF'
            ]
            
            totales_acumulativos = {}
            
            # Verificar qué variables están realmente disponibles
            available_variables = set()
            for day_data in all_variables_extracted:
                if isinstance(day_data, dict):
                    available_variables.update(day_data.keys())
            
            logger.info(f"Available variables: {list(available_variables)}")
            
            # Procesar solo variables que existen
            for var_name in expected_variables:
                if var_name in available_variables:
                    try:
                        var_data = self._calculate_variable_totals_safe(all_variables_extracted, var_name)
                        if var_data['total'] != 0 or var_data['count'] > 0:
                            totales_acumulativos[var_name] = var_data
                    except Exception as e:
                        logger.warning(f"Error processing variable {var_name}: {e}")
                        continue
                else:
                    logger.debug(f"Variable {var_name} not found in extracted data")
            
            logger.info(f"Successfully processed {len(totales_acumulativos)} accumulated variables")
            return totales_acumulativos
            
        except Exception as e:
            logger.error(f"Error processing accumulated variables: {e}")
            return {}
    
    def _calculate_variable_totals_safe(self, all_variables_extracted, var_name):
        """
        CORRECCIÓN: Calcular totales de variable con manejo de errores
        """
        try:
            values = []
            
            for day_data in all_variables_extracted:
                if isinstance(day_data, dict) and var_name in day_data:
                    try:
                        value = day_data[var_name]
                        if value is not None:
                            # Intentar conversión a float
                            numeric_value = float(value)
                            values.append(numeric_value)
                    except (ValueError, TypeError) as e:
                        logger.debug(f"Could not convert {var_name} value '{value}' to float: {e}")
                        continue
            
            # Calcular estadísticas
            if values:
                total = sum(values)
                count = len(values)
                average = total / count
                min_val = min(values)
                max_val = max(values)
                
                # Calcular tendencia simple
                if len(values) >= 3:
                    first_half = values[:len(values)//2]
                    second_half = values[len(values)//2:]
                    first_avg = sum(first_half) / len(first_half) if first_half else 0
                    second_avg = sum(second_half) / len(second_half) if second_half else 0
                    
                    if second_avg > first_avg * 1.05:  # 5% threshold
                        trend = 'increasing'
                    elif second_avg < first_avg * 0.95:
                        trend = 'decreasing'
                    else:
                        trend = 'stable'
                else:
                    trend = 'stable'
            else:
                total = count = average = min_val = max_val = 0
                trend = 'stable'
            
            return {
                'total': total,
                'count': count,
                'average': average,
                'min_value': min_val,
                'max_value': max_val,
                'trend': trend,
                'unit': self._get_safe_variable_unit(var_name)
            }
            
        except Exception as e:
            logger.error(f"Error calculating totals for {var_name}: {e}")
            return {
                'total': 0,
                'count': 0,
                'average': 0,
                'min_value': 0,
                'max_value': 0,
                'trend': 'stable',
                'unit': ''
            }
    
    def _get_safe_variable_unit(self, var_name):
        """Obtener unidad de variable de forma segura"""
        units = {
            'PVP': 'Bs./L',
            'TPV': 'L',
            'IT': 'Bs.',
            'TG': 'Bs.',
            'GT': 'Bs.',
            'NR': '%',
            'NSC': '%',
            'EOG': '%',
            'CFD': 'Bs.',
            'CVU': 'Bs./L',
            'DPH': 'L/día',
            'CPROD': 'L/día',
            'NEPP': 'empleados',
            'RI': '%',
            'IPF': 'L'
        }
        return units.get(var_name, '')
    
    
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
            image_data = self._fig_to_base64(fig)
            plt.close(fig)
            
            return image_data
            
        except Exception as e:
            logger.error(f"Error generating enhanced demand comparison: {str(e)}")
            if 'fig' in locals():
                plt.close(fig)
            return None    

    
    def generate_cost_distribution_chart(self, all_variables_extracted):
        """
        Genera gráfico de distribución de costos con análisis detallado
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            from io import BytesIO
            import base64
            import numpy as np
            
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            
            # Extraer datos de costos
            days = list(range(1, len(all_variables_extracted) + 1))
            costos_produccion = [d.get('CPROD', 0) for d in all_variables_extracted]
            costos_operativos = [d.get('GO', 0) for d in all_variables_extracted]
            costos_materiales = [d.get('MP', 0) for d in all_variables_extracted]
            costos_transporte = [d.get('CTTL', 0) for d in all_variables_extracted]
            costos_totales = [d.get('TG', 0) for d in all_variables_extracted]
            
            # 1. Gráfico de barras apiladas - Composición de costos por día
            ax1.bar(days, costos_produccion, label='Producción', alpha=0.8, color='#3498DB')
            ax1.bar(days, costos_operativos, bottom=costos_produccion, 
                    label='Operativos', alpha=0.8, color='#E74C3C')
            
            bottom_so_far = [p + o for p, o in zip(costos_produccion, costos_operativos)]
            ax1.bar(days, costos_materiales, bottom=bottom_so_far, 
                    label='Materiales', alpha=0.8, color='#F39C12')
            
            bottom_final = [b + m for b, m in zip(bottom_so_far, costos_materiales)]
            ax1.bar(days, costos_transporte, bottom=bottom_final, 
                    label='Transporte', alpha=0.8, color='#9B59B6')
            
            ax1.set_xlabel('Días', fontsize=12, fontweight='bold')
            ax1.set_ylabel('Costos (Bs)', fontsize=12, fontweight='bold')
            ax1.set_title('Composición Diaria de Costos', fontsize=14, fontweight='bold')
            ax1.legend(loc='upper right')
            ax1.grid(True, alpha=0.3, axis='y')
            
            # 2. Gráfico circular - Distribución promedio de costos
            costos_promedio = {
                'Producción': np.mean(costos_produccion) if costos_produccion else 0,
                'Operativos': np.mean(costos_operativos) if costos_operativos else 0,
                'Materiales': np.mean(costos_materiales) if costos_materiales else 0,
                'Transporte': np.mean(costos_transporte) if costos_transporte else 0
            }
            
            # Filtrar costos no nulos
            costos_filtered = {k: v for k, v in costos_promedio.items() if v > 0}
            
            if costos_filtered:
                colors = ['#3498DB', '#E74C3C', '#F39C12', '#9B59B6'][:len(costos_filtered)]
                wedges, texts, autotexts = ax2.pie(
                    costos_filtered.values(), 
                    labels=costos_filtered.keys(),
                    colors=colors,
                    autopct='%1.1f%%',
                    startangle=90,
                    explode=[0.05] * len(costos_filtered)
                )
                
                # Mejorar el texto
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
                    autotext.set_fontsize(10)
            
            ax2.set_title('Distribución Promedio de Costos', fontsize=14, fontweight='bold')
            
            # 3. Evolución de costos unitarios
            ingresos = [d.get('IT', 0) for d in all_variables_extracted]
            ventas = [d.get('TPV', 0) for d in all_variables_extracted]
            
            # Calcular costo por unidad vendida
            costo_unitario = []
            for i, (costo, venta) in enumerate(zip(costos_totales, ventas)):
                if venta > 0:
                    costo_unitario.append(costo / venta)
                else:
                    costo_unitario.append(0)
            
            ax3.plot(days, costo_unitario, 'b-', linewidth=3, marker='o', 
                    markersize=5, label='Costo Unitario')
            
            # Agregar línea de tendencia
            if len(costo_unitario) > 3:
                z = np.polyfit(days, costo_unitario, 1)
                p = np.poly1d(z)
                ax3.plot(days, p(days), '--', alpha=0.7, color='red', 
                        linewidth=2, label=f'Tendencia: {z[0]:.3f}')
            
            ax3.set_xlabel('Días', fontsize=12, fontweight='bold')
            ax3.set_ylabel('Costo por Unidad (Bs/L)', fontsize=12, fontweight='bold')
            ax3.set_title('Evolución del Costo Unitario', fontsize=14, fontweight='bold')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            
            # 4. Análisis de eficiencia de costos
            margen_bruto = []
            eficiencia_costos = []
            
            for ingreso, costo in zip(ingresos, costos_totales):
                if ingreso > 0:
                    margen = ((ingreso - costo) / ingreso) * 100
                    margen_bruto.append(margen)
                    eficiencia = (ingreso / costo) * 100 if costo > 0 else 0
                    eficiencia_costos.append(eficiencia)
                else:
                    margen_bruto.append(0)
                    eficiencia_costos.append(0)
            
            # Gráfico dual
            ax4_twin = ax4.twinx()
            
            line1 = ax4.plot(days, margen_bruto, 'g-', linewidth=3, marker='s', 
                            markersize=4, label='Margen Bruto %')
            line2 = ax4_twin.plot(days, eficiencia_costos, 'orange', linewidth=3, 
                                marker='^', markersize=4, label='Eficiencia Costos %')
            
            # Líneas de referencia
            ax4.axhline(y=20, color='green', linestyle='--', alpha=0.5, label='Meta Margen 20%')
            ax4_twin.axhline(y=150, color='orange', linestyle='--', alpha=0.5, label='Meta Eficiencia 150%')
            
            ax4.set_xlabel('Días', fontsize=12, fontweight='bold')
            ax4.set_ylabel('Margen Bruto (%)', color='green', fontsize=12, fontweight='bold')
            ax4_twin.set_ylabel('Eficiencia de Costos (%)', color='orange', fontsize=12, fontweight='bold')
            ax4.set_title('Análisis de Rentabilidad y Eficiencia', fontsize=14, fontweight='bold')
            
            # Combinar leyendas
            lines = line1 + line2
            labels = [l.get_label() for l in lines]
            ax4.legend(lines, labels, loc='upper left')
            ax4.grid(True, alpha=0.3)
            
            plt.suptitle('ANÁLISIS INTEGRAL DE COSTOS', fontsize=18, fontweight='bold', y=0.98)
            plt.tight_layout()
            
            # Convertir a base64
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight', 
                        facecolor='white', edgecolor='none')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            logger.info("Cost distribution chart generated successfully")
            return chart_base64
            
        except Exception as e:
            logger.error(f"Error generating cost distribution chart: {str(e)}")
            plt.close('all')
            return None
    
    
    def generate_production_vs_sales_evolution_chart(self, all_variables_extracted):
        """
        Genera gráfico de evolución de producción vs ventas con análisis detallado
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            from io import BytesIO
            import base64
            import numpy as np
            
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            
            days = list(range(1, len(all_variables_extracted) + 1))
            
            # Extraer datos de producción y ventas
            produccion = [d.get('QPL', 0) for d in all_variables_extracted]
            ventas = [d.get('TPV', 0) for d in all_variables_extracted]
            demanda = [d.get('demand_mean', 0) for d in all_variables_extracted]
            inventario = [d.get('IPF', 0) for d in all_variables_extracted]
            demanda_insatisfecha = [d.get('DI', 0) for d in all_variables_extracted]
            
            # 1. Evolución temporal de Producción vs Ventas vs Demanda
            ax1.plot(days, demanda, 'gray', linewidth=3, marker='o', markersize=5, 
                    alpha=0.7, label='Demanda', linestyle='--')
            ax1.plot(days, produccion, 'b-', linewidth=3, marker='s', markersize=6, 
                    label='Producción', alpha=0.8)
            ax1.plot(days, ventas, 'g-', linewidth=3, marker='^', markersize=6,
                    label='Ventas', alpha=0.8)
            
            # Áreas de análisis
            ax1.fill_between(days, ventas, produccion, 
                            where=[v < p for v, p in zip(ventas, produccion)],
                            color='blue', alpha=0.2, label='Inventario Generado')
            ax1.fill_between(days, ventas, demanda,
                            where=[v < d for v, d in zip(ventas, demanda)],
                            color='red', alpha=0.3, label='Demanda Insatisfecha')
            
            ax1.set_xlabel('Días', fontsize=12, fontweight='bold')
            ax1.set_ylabel('Cantidad (Litros)', fontsize=12, fontweight='bold')
            ax1.set_title('Evolución: Producción vs Ventas vs Demanda', fontsize=14, fontweight='bold')
            ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            ax1.grid(True, alpha=0.3)
            
            # 2. Análisis de eficiencia de conversión
            eficiencia_ventas = []  # Ventas / Producción
            satisfaccion_demanda = []  # Ventas / Demanda
            
            for prod, vent, dem in zip(produccion, ventas, demanda):
                efic_vent = (vent / prod * 100) if prod > 0 else 0
                eficiencia_ventas.append(min(efic_vent, 100))  # Cap at 100%
                
                satisf_dem = (vent / dem * 100) if dem > 0 else 100
                satisfaccion_demanda.append(min(satisf_dem, 100))  # Cap at 100%
            
            # Gráfico de barras agrupadas
            x_pos = np.arange(len(days))
            width = 0.35
            
            bars1 = ax2.bar(x_pos - width/2, eficiencia_ventas, width, 
                        alpha=0.7, color='steelblue', label='Eficiencia Ventas (%)')
            bars2 = ax2.bar(x_pos + width/2, satisfaccion_demanda, width, 
                        alpha=0.7, color='darkgreen', label='Satisfacción Demanda (%)')
            
            # Líneas de referencia
            ax2.axhline(y=95, color='green', linestyle='--', alpha=0.7, label='Meta 95%')
            ax2.axhline(y=85, color='orange', linestyle='--', alpha=0.7, label='Mínimo 85%')
            
            ax2.set_xlabel('Días', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Porcentaje (%)', fontsize=12, fontweight='bold')
            ax2.set_title('Eficiencia de Conversión y Satisfacción', fontsize=14, fontweight='bold')
            ax2.set_ylim(0, 110)
            ax2.set_xticks(x_pos[::max(1, len(days)//10)])
            ax2.set_xticklabels([f'D{d}' for d in days[::max(1, len(days)//10)]], rotation=45)
            ax2.legend()
            ax2.grid(True, alpha=0.3, axis='y')
            
            # 3. Gestión de inventarios y flujo
            inventario_optimo = [d.get('IOP', 0) for d in all_variables_extracted]
            rotacion_inventario = []
            
            for i, (vent, inv) in enumerate(zip(ventas, inventario)):
                if inv > 0:
                    # Rotación = Ventas / Inventario promedio (aproximación)
                    rotacion = (vent / inv) * 30  # Proyección mensual
                    rotacion_inventario.append(rotacion)
                else:
                    rotacion_inventario.append(0)
            
            ax3_twin = ax3.twinx()
            
            # Inventario actual vs óptimo
            line1 = ax3.plot(days, inventario, 'b-', linewidth=3, marker='o', markersize=5, 
                            label='Inventario Real')
            line2 = ax3.plot(days, inventario_optimo, 'r--', linewidth=3, marker='s', markersize=5, 
                            label='Inventario Óptimo')
            
            # Rotación de inventario
            line3 = ax3_twin.plot(days, rotacion_inventario, 'purple', linewidth=3, 
                                marker='^', markersize=5, alpha=0.8, label='Rotación (veces/mes)')
            
            # Área de exceso/déficit
            ax3.fill_between(days, inventario, inventario_optimo,
                            where=[i > o for i, o in zip(inventario, inventario_optimo)],
                            color='red', alpha=0.2, label='Exceso de Inventario')
            ax3.fill_between(days, inventario, inventario_optimo,
                            where=[i < o for i, o in zip(inventario, inventario_optimo)],
                            color='orange', alpha=0.2, label='Déficit de Inventario')
            
            ax3.set_xlabel('Días', fontsize=12, fontweight='bold')
            ax3.set_ylabel('Inventario (Litros)', color='blue', fontsize=12, fontweight='bold')
            ax3_twin.set_ylabel('Rotación (veces/mes)', color='purple', fontsize=12, fontweight='bold')
            ax3.set_title('Gestión de Inventarios y Rotación', fontsize=14, fontweight='bold')
            
            # Combinar leyendas
            lines = line1 + line2 + line3
            labels = [l.get_label() for l in lines]
            ax3.legend(lines, labels, loc='upper left')
            ax3.grid(True, alpha=0.3)
            
            # 4. Dashboard de productividad y tendencias
            productividad_diaria = [d.get('PE', 0) * 100 for d in all_variables_extracted]
            
            # Calcular tendencias usando promedio móvil
            window = min(7, len(days))  # Ventana de 7 días o menos
            
            def moving_average(data, window):
                if len(data) < window:
                    return data
                result = []
                for i in range(len(data)):
                    start = max(0, i - window + 1)
                    end = i + 1
                    result.append(np.mean(data[start:end]))
                return result
            
            trend_produccion = moving_average(produccion, window)
            trend_ventas = moving_average(ventas, window)
            trend_productividad = moving_average(productividad_diaria, window)
            
            # Gráfico de múltiples métricas normalizadas
            # Normalizar para comparación visual
            def normalize_data(data):
                if max(data) == min(data):
                    return [50] * len(data)
                return [(x - min(data)) / (max(data) - min(data)) * 100 for x in data]
            
            norm_prod = normalize_data(trend_produccion)
            norm_ventas = normalize_data(trend_ventas)
            norm_productividad = trend_productividad  # Ya está en porcentaje
            
            ax4.plot(days, norm_prod, 'b-', linewidth=3, marker='o', markersize=4, 
                    alpha=0.8, label='Tendencia Producción (norm.)')
            ax4.plot(days, norm_ventas, 'g-', linewidth=3, marker='s', markersize=4, 
                    alpha=0.8, label='Tendencia Ventas (norm.)')
            ax4.plot(days, norm_productividad, 'purple', linewidth=3, marker='^', markersize=4, 
                    alpha=0.8, label='Productividad (%)')
            
            # Zonas de rendimiento
            ax4.axhspan(80, 100, alpha=0.1, color='green', label='Alto Rendimiento')
            ax4.axhspan(60, 80, alpha=0.1, color='yellow', label='Rendimiento Medio')
            ax4.axhspan(0, 60, alpha=0.1, color='red', label='Bajo Rendimiento')
            
            # Calcular correlación entre producción y ventas
            if len(produccion) > 3:
                correlation = np.corrcoef(produccion, ventas)[0, 1]
                correlation_text = f'Correlación Prod-Ventas: {correlation:.3f}'
            else:
                correlation_text = 'Correlación: N/A'
            
            ax4.text(0.02, 0.98, correlation_text, transform=ax4.transAxes,
                    verticalalignment='top', fontsize=11, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='wheat', alpha=0.8))
            
            ax4.set_xlabel('Días', fontsize=12, fontweight='bold')
            ax4.set_ylabel('Índice Normalizado / Productividad (%)', fontsize=12, fontweight='bold')
            ax4.set_title('Dashboard de Productividad y Tendencias', fontsize=14, fontweight='bold')
            ax4.set_ylim(0, 105)
            ax4.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            ax4.grid(True, alpha=0.3)
            
            plt.suptitle('EVOLUCIÓN: PRODUCCIÓN vs VENTAS', fontsize=18, fontweight='bold', y=0.98)
            plt.tight_layout()
            
            # Convertir a base64
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight', 
                        facecolor='white', edgecolor='none')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            logger.info("Production vs sales evolution chart generated successfully")
            return chart_base64
            
        except Exception as e:
            logger.error(f"Error generating production vs sales evolution chart: {str(e)}")
            plt.close('all')
            return None

    
    
    def generate_financial_efficiency_indicators_chart(self, all_variables_extracted):
        """
        Genera gráfico de indicadores de eficiencia financiera
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            from io import BytesIO
            import base64
            import numpy as np
            
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            
            days = list(range(1, len(all_variables_extracted) + 1))
            
            # Extraer datos financieros
            ingresos = [d.get('IT', 0) for d in all_variables_extracted]
            gastos = [d.get('TG', 0) for d in all_variables_extracted]
            ganancias = [d.get('GT', 0) for d in all_variables_extracted]
            margen_neto = [d.get('NR', 0) * 100 for d in all_variables_extracted]
            roi = [d.get('RI', 0) * 100 for d in all_variables_extracted]
            
            # 1. ROI y Margen Neto Evolution
            ax1_twin = ax1.twinx()
            
            line1 = ax1.plot(days, roi, 'g-', linewidth=3, marker='o', markersize=6, 
                            label='ROI (%)', alpha=0.8)
            line2 = ax1_twin.plot(days, margen_neto, 'b-', linewidth=3, marker='s', markersize=6, 
                                label='Margen Neto (%)', alpha=0.8)
            
            # Zonas de rendimiento
            ax1.axhspan(15, 100, alpha=0.1, color='green', label='ROI Excelente')
            ax1.axhspan(8, 15, alpha=0.1, color='yellow', label='ROI Bueno')
            ax1.axhspan(0, 8, alpha=0.1, color='red', label='ROI Bajo')
            
            ax1.set_xlabel('Días', fontsize=12, fontweight='bold')
            ax1.set_ylabel('ROI (%)', color='green', fontsize=12, fontweight='bold')
            ax1_twin.set_ylabel('Margen Neto (%)', color='blue', fontsize=12, fontweight='bold')
            ax1.set_title('Rentabilidad: ROI y Margen Neto', fontsize=14, fontweight='bold')
            
            # Combinar leyendas
            lines = line1 + line2
            labels = [l.get_label() for l in lines]
            ax1.legend(lines, labels, loc='upper left')
            ax1.grid(True, alpha=0.3)
            
            # 2. Análisis de Cash Flow y Liquidez
            cash_flow_acumulado = np.cumsum(ganancias)
            ingresos_acumulados = np.cumsum(ingresos)
            gastos_acumulados = np.cumsum(gastos)
            
            ax2.plot(days, cash_flow_acumulado, 'g-', linewidth=4, label='Cash Flow Acumulado')
            ax2.fill_between(days, 0, cash_flow_acumulado, 
                            where=[cf > 0 for cf in cash_flow_acumulado],
                            color='green', alpha=0.3, label='Zona Positiva')
            ax2.fill_between(days, cash_flow_acumulado, 0,
                            where=[cf < 0 for cf in cash_flow_acumulado],
                            color='red', alpha=0.3, label='Zona Negativa')
            
            ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
            ax2.set_xlabel('Días', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Cash Flow Acumulado (Bs)', fontsize=12, fontweight='bold')
            ax2.set_title('Evolución del Cash Flow', fontsize=14, fontweight='bold')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # 3. Ratios de Eficiencia Financiera
            ratio_ingresos_gastos = [i/g if g > 0 else 0 for i, g in zip(ingresos, gastos)]
            punto_equilibrio = [d.get('PED', 0) for d in all_variables_extracted]
            ventas_reales = [d.get('TPV', 0) for d in all_variables_extracted]
            
            # Gráfico de barras comparativo
            x_pos = np.arange(len(days))
            width = 0.35
            
            bars1 = ax3.bar(x_pos - width/2, ratio_ingresos_gastos, width, 
                        alpha=0.7, color='steelblue', label='Ratio Ingresos/Gastos')
            
            # Línea de referencia para break-even
            ax3_twin = ax3.twinx()
            line3 = ax3_twin.plot(days, [v/pe if pe > 0 else 0 for v, pe in zip(ventas_reales, punto_equilibrio)], 
                                'r-', linewidth=3, marker='^', markersize=5, 
                                label='Ratio Ventas/Punto Equilibrio')
            
            ax3.axhline(y=1.2, color='green', linestyle='--', alpha=0.7, label='Meta Ratio 1.2')
            ax3_twin.axhline(y=1.0, color='red', linestyle='--', alpha=0.7, label='Break-Even Point')
            
            ax3.set_xlabel('Días', fontsize=12, fontweight='bold')
            ax3.set_ylabel('Ratio Ingresos/Gastos', color='steelblue', fontsize=12, fontweight='bold')
            ax3_twin.set_ylabel('Ratio vs Break-Even', color='red', fontsize=12, fontweight='bold')
            ax3.set_title('Ratios de Eficiencia Financiera', fontsize=14, fontweight='bold')
            ax3.set_xticks(x_pos)
            ax3.set_xticklabels([f'D{d}' for d in days[::max(1, len(days)//10)]], rotation=45)
            
            # Combinar leyendas
            lines1, labels1 = ax3.get_legend_handles_labels()
            lines2, labels2 = ax3_twin.get_legend_handles_labels()
            ax3.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
            ax3.grid(True, alpha=0.3, axis='y')
            
            # 4. Dashboard de Salud Financiera
            # Calcular score de salud financiera
            health_scores = []
            for i, (ing, gast, marg, r) in enumerate(zip(ingresos, gastos, margen_neto, roi)):
                score = 0
                
                # Componente de rentabilidad (40%)
                if marg > 15:
                    score += 40
                elif marg > 10:
                    score += 30
                elif marg > 5:
                    score += 20
                elif marg > 0:
                    score += 10
                
                # Componente de ROI (30%)
                if r > 15:
                    score += 30
                elif r > 10:
                    score += 22
                elif r > 5:
                    score += 15
                elif r > 0:
                    score += 8
                
                # Componente de solvencia (30%)
                ratio = ing / gast if gast > 0 else 0
                if ratio > 1.3:
                    score += 30
                elif ratio > 1.15:
                    score += 22
                elif ratio > 1.05:
                    score += 15
                elif ratio > 1.0:
                    score += 8
                
                health_scores.append(score)
            
            # Gráfico de área para health score
            ax4.fill_between(days, 0, health_scores, alpha=0.3, color='lightblue')
            ax4.plot(days, health_scores, 'b-', linewidth=3, marker='o', markersize=6)
            
            # Zonas de salud financiera
            ax4.axhspan(80, 100, alpha=0.1, color='green', label='Salud Excelente')
            ax4.axhspan(60, 80, alpha=0.1, color='yellow', label='Salud Buena')
            ax4.axhspan(40, 60, alpha=0.1, color='orange', label='Salud Regular')
            ax4.axhspan(0, 40, alpha=0.1, color='red', label='Salud Crítica')
            
            # Promedio móvil
            if len(health_scores) >= 5:
                window = min(5, len(health_scores))
                moving_avg = []
                for i in range(len(health_scores)):
                    start = max(0, i - window + 1)
                    end = i + 1
                    moving_avg.append(np.mean(health_scores[start:end]))
                
                ax4.plot(days, moving_avg, 'r--', linewidth=2, alpha=0.8, 
                        label=f'Promedio Móvil ({window} días)')
            
            ax4.set_xlabel('Días', fontsize=12, fontweight='bold')
            ax4.set_ylabel('Score de Salud Financiera', fontsize=12, fontweight='bold')
            ax4.set_title('Dashboard de Salud Financiera', fontsize=14, fontweight='bold')
            ax4.set_ylim(0, 105)
            ax4.legend(loc='lower right')
            ax4.grid(True, alpha=0.3)
            
            plt.suptitle('INDICADORES DE EFICIENCIA FINANCIERA', fontsize=18, fontweight='bold', y=0.98)
            plt.tight_layout()
            
            # Convertir a base64
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight', 
                        facecolor='white', edgecolor='none')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            logger.info("Financial efficiency indicators chart generated successfully")
            return chart_base64
            
        except Exception as e:
            logger.error(f"Error generating financial efficiency indicators chart: {str(e)}")
            plt.close('all')
            return None
    
    
    def generate_capacity_vs_demand_chart(self, all_variables_extracted):
        """
        Genera gráfico de análisis de capacidad vs demanda con utilización
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            from io import BytesIO
            import base64
            import numpy as np
            
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            
            days = list(range(1, len(all_variables_extracted) + 1))
            
            # Extraer datos
            demanda = [d.get('demand_mean', 0) for d in all_variables_extracted]
            capacidad_prod = [d.get('CPROD', 0) for d in all_variables_extracted]
            produccion_real = [d.get('QPL', 0) for d in all_variables_extracted]
            ventas = [d.get('TPV', 0) for d in all_variables_extracted]
            inventario = [d.get('IPF', 0) for d in all_variables_extracted]
            
            # 1. Comparación Demanda vs Capacidad vs Producción
            ax1.plot(days, demanda, 'b-', linewidth=3, marker='o', markersize=5, 
                    label='Demanda', alpha=0.8)
            ax1.plot(days, capacidad_prod, 'r--', linewidth=3, marker='s', markersize=5, 
                    label='Capacidad Máxima', alpha=0.8)
            ax1.plot(days, produccion_real, 'g-', linewidth=3, marker='^', markersize=5, 
                    label='Producción Real', alpha=0.8)
            
            # Área de capacidad no utilizada
            ax1.fill_between(days, produccion_real, capacidad_prod, 
                            where=[p < c for p, c in zip(produccion_real, capacidad_prod)],
                            color='red', alpha=0.2, label='Capacidad No Utilizada')
            
            # Área de demanda insatisfecha
            ax1.fill_between(days, ventas, demanda,
                            where=[v < d for v, d in zip(ventas, demanda)],
                            color='orange', alpha=0.3, label='Demanda Insatisfecha')
            
            ax1.set_xlabel('Días', fontsize=12, fontweight='bold')
            ax1.set_ylabel('Cantidad (Litros)', fontsize=12, fontweight='bold')
            ax1.set_title('Análisis de Capacidad vs Demanda', fontsize=14, fontweight='bold')
            ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            ax1.grid(True, alpha=0.3)
            
            # 2. Utilización de capacidad y level de servicio
            utilizacion_capacidad = []
            nivel_servicio = []
            
            for prod, cap, dem, vent in zip(produccion_real, capacidad_prod, demanda, ventas):
                util = (prod / cap * 100) if cap > 0 else 0
                utilizacion_capacidad.append(util)
                
                servicio = (vent / dem * 100) if dem > 0 else 100
                nivel_servicio.append(min(servicio, 100))  # Cap at 100%
            
            ax2_twin = ax2.twinx()
            
            bars1 = ax2.bar([d - 0.2 for d in days], utilizacion_capacidad, 
                        width=0.4, alpha=0.7, color='steelblue', 
                        label='Utilización Capacidad %')
            bars2 = ax2_twin.bar([d + 0.2 for d in days], nivel_servicio, 
                                width=0.4, alpha=0.7, color='darkgreen', 
                                label='Nivel de Servicio %')
            
            # Líneas de referencia
            ax2.axhline(y=85, color='blue', linestyle='--', alpha=0.5, label='Meta Utilización 85%')
            ax2_twin.axhline(y=95, color='green', linestyle='--', alpha=0.5, label='Meta Servicio 95%')
            
            ax2.set_xlabel('Días', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Utilización Capacidad (%)', color='steelblue', fontsize=12, fontweight='bold')
            ax2_twin.set_ylabel('Nivel de Servicio (%)', color='darkgreen', fontsize=12, fontweight='bold')
            ax2.set_title('Indicadores de Utilización', fontsize=14, fontweight='bold')
            ax2.set_ylim(0, 110)
            ax2_twin.set_ylim(0, 110)
            
            # Combinar leyendas
            lines1, labels1 = ax2.get_legend_handles_labels()
            lines2, labels2 = ax2_twin.get_legend_handles_labels()
            ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
            ax2.grid(True, alpha=0.3, axis='y')
            
            # 3. Análisis de brechas (Gap Analysis)
            brecha_capacidad = [c - p for c, p in zip(capacidad_prod, produccion_real)]
            brecha_demanda = [d - v for d, v in zip(demanda, ventas)]
            
            ax3.bar([d - 0.2 for d in days], brecha_capacidad, width=0.4, 
                alpha=0.7, color='red', label='Capacidad No Utilizada')
            ax3.bar([d + 0.2 for d in days], brecha_demanda, width=0.4, 
                alpha=0.7, color='orange', label='Demanda Insatisfecha')
            
            ax3.set_xlabel('Días', fontsize=12, fontweight='bold')
            ax3.set_ylabel('Brecha (Litros)', fontsize=12, fontweight='bold')
            ax3.set_title('Análisis de Brechas Operativas', fontsize=14, fontweight='bold')
            ax3.legend()
            ax3.grid(True, alpha=0.3, axis='y')
            
            # 4. Eficiencia operativa integral
            eficiencia_global = [d.get('EOG', 0) * 100 for d in all_variables_extracted]
            eficiencia_produccion = [d.get('EP', 0) * 100 for d in all_variables_extracted]
            factor_utilizacion = [d.get('FU', 0) * 100 for d in all_variables_extracted]
            
            ax4.plot(days, eficiencia_global, 'purple', linewidth=3, marker='o', 
                    markersize=5, label='Eficiencia Global (OEE)')
            ax4.plot(days, eficiencia_produccion, 'blue', linewidth=3, marker='s', 
                    markersize=5, label='Eficiencia Producción')
            ax4.plot(days, factor_utilizacion, 'green', linewidth=3, marker='^', 
                    markersize=5, label='Factor Utilización')
            
            # Zona de excelencia
            ax4.axhspan(85, 100, alpha=0.1, color='green', label='Zona Excelencia')
            ax4.axhspan(70, 85, alpha=0.1, color='yellow', label='Zona Aceptable')
            ax4.axhspan(0, 70, alpha=0.1, color='red', label='Zona Crítica')
            
            ax4.set_xlabel('Días', fontsize=12, fontweight='bold')
            ax4.set_ylabel('Eficiencia (%)', fontsize=12, fontweight='bold')
            ax4.set_title('Dashboard de Eficiencia Operativa', fontsize=14, fontweight='bold')
            ax4.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            ax4.grid(True, alpha=0.3)
            ax4.set_ylim(0, 105)
            
            plt.suptitle('ANÁLISIS INTEGRAL: CAPACIDAD vs DEMANDA', fontsize=18, fontweight='bold', y=0.98)
            plt.tight_layout()
            
            # Convertir a base64
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight', 
                        facecolor='white', edgecolor='none')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            logger.info("Capacity vs demand chart generated successfully")
            return chart_base64
            
        except Exception as e:
            logger.error(f"Error generating capacity vs demand chart: {str(e)}")
            plt.close('all')
            return None
    
    
    def generate_all_charts_enhanced(self, simulation_id: int, 
                      simulation_instance: Any,
                      results: List[Any],
                      historical_demand: List[float]) -> Dict[str, Any]:
        """Generate all charts including new advanced charts"""
        try:
            # Extract data for charts
            dates = [r.date for r in results]
            daily_data = self._extract_daily_data(results)
            
            # Calculate accumulated totals
            totales_acumulativos = self._calculate_accumulated_totals(daily_data)
            
            # Generate existing charts
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
                ),
                
                # NUEVOS GRÁFICOS AVANZADOS
                'image_data_cost_distribution': self.generate_cost_distribution_chart(daily_data),
                'image_data_capacity_vs_demand': self.generate_capacity_vs_demand_chart(daily_data),
                'image_data_financial_efficiency': self.generate_financial_efficiency_indicators_chart(daily_data),
                'image_data_production_evolution': self.generate_production_vs_sales_evolution_chart(daily_data)
            }
            
            # Add chart images to return dict
            return {
                'chart_images': charts,
                'totales_acumulativos': totales_acumulativos,
                'all_variables_extracted': daily_data
            }
            
        except Exception as e:
            logger.error(f"Error generating enhanced charts: {str(e)}")
            return {
                'chart_images': {},
                'totales_acumulativos': {},
                'all_variables_extracted': []
            }
    
    
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
    
    def _generate_histogram_chart(self, data):
        """Generar histograma con ajuste de distribución"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            from scipy import stats
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
            
            # Histograma principal
            n, bins, patches = ax1.hist(data, bins=20, density=True, alpha=0.7, 
                                    color='skyblue', edgecolor='black')
            
            # Ajustar distribución normal
            mu, sigma = np.mean(data), np.std(data)
            x = np.linspace(min(data), max(data), 100)
            normal_dist = stats.norm.pdf(x, mu, sigma)
            ax1.plot(x, normal_dist, 'r-', linewidth=2, label=f'Normal (μ={mu:.2f}, σ={sigma:.2f})')
            
            # Líneas de estadísticas
            ax1.axvline(mu, color='red', linestyle='--', alpha=0.7, label=f'Media: {mu:.2f}')
            ax1.axvline(np.median(data), color='orange', linestyle='--', alpha=0.7, 
                    label=f'Mediana: {np.median(data):.2f}')
            
            ax1.set_xlabel('Demanda (Litros)')
            ax1.set_ylabel('Densidad')
            ax1.set_title('Distribución de la Demanda Simulada')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Box plot
            bp = ax2.boxplot(data, patch_artist=True, boxprops=dict(facecolor='lightblue'))
            ax2.set_ylabel('Demanda (Litros)')
            ax2.set_title('Diagrama de Cajas')
            ax2.grid(True, alpha=0.3)
            
            # Estadísticas en el box plot
            q1, median, q3 = np.percentile(data, [25, 50, 75])
            iqr = q3 - q1
            ax2.text(1.1, median, f'Q2: {median:.1f}', va='center')
            ax2.text(1.1, q3, f'Q3: {q3:.1f}', va='center')
            ax2.text(1.1, q1, f'Q1: {q1:.1f}', va='center')
            
            plt.tight_layout()
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating histogram chart: {e}")
            return None
        
    def _generate_comparative_boxplot(self, historical_data, simulated_data):
        """Generar box plot comparativo"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Preparar datos
            min_len = min(len(historical_data), len(simulated_data))
            hist_data = historical_data[:min_len]
            sim_data = simulated_data[:min_len]
            
            # Box plots lado a lado
            bp1 = ax.boxplot([hist_data], positions=[1], widths=0.6, patch_artist=True,
                            boxprops=dict(facecolor='lightblue', alpha=0.7),
                            medianprops=dict(color='red', linewidth=2))
            
            bp2 = ax.boxplot([sim_data], positions=[2], widths=0.6, patch_artist=True,
                            boxprops=dict(facecolor='lightcoral', alpha=0.7),
                            medianprops=dict(color='red', linewidth=2))
            
            # Etiquetas y formato
            ax.set_xticklabels(['Histórico', 'Simulado'])
            ax.set_ylabel('Demanda (Litros)')
            ax.set_title('Comparación de Distribuciones: Histórico vs Simulado')
            ax.grid(True, alpha=0.3)
            
            # Agregar estadísticas
            hist_stats = f'Media: {np.mean(hist_data):.1f}\nMediana: {np.median(hist_data):.1f}\nStd: {np.std(hist_data):.1f}'
            sim_stats = f'Media: {np.mean(sim_data):.1f}\nMediana: {np.median(sim_data):.1f}\nStd: {np.std(sim_data):.1f}'
            
            ax.text(0.7, 0.95, hist_stats, transform=ax.transAxes, va='top',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
            ax.text(0.7, 0.7, sim_stats, transform=ax.transAxes, va='top',
                bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.7))
            
            plt.tight_layout()
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating comparative boxplot: {e}")
            return None
    
    def _generate_scatter_plot(self, historical_data, simulated_data):
        """Generar scatter plot con línea de regresión"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            from scipy import stats
            
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Ajustar longitudes
            min_len = min(len(historical_data), len(simulated_data))
            hist_data = np.array(historical_data[:min_len])
            sim_data = np.array(simulated_data[:min_len])
            
            # Scatter plot
            ax.scatter(hist_data, sim_data, alpha=0.6, s=50, color='blue')
            
            # Línea de referencia (x=y)
            min_val = min(np.min(hist_data), np.min(sim_data))
            max_val = max(np.max(hist_data), np.max(sim_data))
            ax.plot([min_val, max_val], [min_val, max_val], 'r--', 
                label='Línea de referencia (y=x)', linewidth=2)
            
            # Línea de regresión
            slope, intercept, r_value, p_value, std_err = stats.linregress(hist_data, sim_data)
            line = slope * hist_data + intercept
            ax.plot(hist_data, line, 'g-', label=f'Regresión (R²={r_value**2:.3f})', linewidth=2)
            
            # Formato y etiquetas
            ax.set_xlabel('Demanda Histórica (Litros)')
            ax.set_ylabel('Demanda Simulada (Litros)')
            ax.set_title('Correlación: Demanda Histórica vs Simulada')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Estadísticas en el gráfico
            stats_text = f'R² = {r_value**2:.3f}\nR = {r_value:.3f}\np-valor = {p_value:.4f}'
            ax.text(0.05, 0.95, stats_text, transform=ax.transAxes, va='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            plt.tight_layout()
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating scatter plot: {e}")
            return None
        
    def _generate_residuals_plot(self, historical_data, simulated_data):
        """Generar gráfico de residuos"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            from scipy import stats
            
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
            
            # Ajustar longitudes
            min_len = min(len(historical_data), len(simulated_data))
            hist_data = np.array(historical_data[:min_len])
            sim_data = np.array(simulated_data[:min_len])
            
            # Calcular residuos
            residuals = sim_data - hist_data
            fitted = hist_data  # En este caso, los valores "fitted" son los históricos
            
            # 1. Residuos vs Valores ajustados
            ax1.scatter(fitted, residuals, alpha=0.6)
            ax1.axhline(y=0, color='red', linestyle='--', alpha=0.7)
            ax1.set_xlabel('Valores Históricos')
            ax1.set_ylabel('Residuos (Simulado - Histórico)')
            ax1.set_title('Residuos vs Valores Históricos')
            ax1.grid(True, alpha=0.3)
            
            # 2. Histograma de residuos
            ax2.hist(residuals, bins=15, density=True, alpha=0.7, color='skyblue', edgecolor='black')
            
            # Superponer distribución normal
            mu, sigma = np.mean(residuals), np.std(residuals)
            x = np.linspace(np.min(residuals), np.max(residuals), 100)
            ax2.plot(x, stats.norm.pdf(x, mu, sigma), 'r-', linewidth=2, label='Normal')
            
            ax2.set_xlabel('Residuos')
            ax2.set_ylabel('Densidad')
            ax2.set_title('Distribución de Residuos')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # 3. Q-Q plot de residuos
            stats.probplot(residuals, dist="norm", plot=ax3)
            ax3.set_title('Q-Q Plot de Residuos')
            ax3.grid(True, alpha=0.3)
            
            # 4. Residuos vs Orden (temporal)
            order = np.arange(len(residuals))
            ax4.plot(order, residuals, 'o-', alpha=0.6)
            ax4.axhline(y=0, color='red', linestyle='--', alpha=0.7)
            ax4.set_xlabel('Orden Temporal')
            ax4.set_ylabel('Residuos')
            ax4.set_title('Residuos vs Tiempo')
            ax4.grid(True, alpha=0.3)
            
            plt.tight_layout()
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating residuals plot: {e}")
            return None
        
    def _generate_qq_plot(self, data):
        """Generar Q-Q plot para prueba de normalidad"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            from scipy import stats
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            
            # Q-Q plot normal
            stats.probplot(data, dist="norm", plot=ax1)
            ax1.set_title('Q-Q Plot vs Distribución Normal')
            ax1.grid(True, alpha=0.3)
            
            # Prueba de normalidad con histograma
            ax2.hist(data, bins=20, density=True, alpha=0.7, color='lightblue', edgecolor='black')
            
            # Superponer distribución normal teórica
            mu, sigma = np.mean(data), np.std(data)
            x = np.linspace(np.min(data), np.max(data), 100)
            ax2.plot(x, stats.norm.pdf(x, mu, sigma), 'r-', linewidth=2, label='Normal teórica')
            
            # Prueba de Shapiro-Wilk
            if len(data) <= 5000:
                shapiro_stat, shapiro_p = stats.shapiro(data)
                interpretation = "Normal" if shapiro_p > 0.05 else "No Normal"
                ax2.text(0.05, 0.95, f'Shapiro-Wilk:\nEstadístico: {shapiro_stat:.4f}\np-valor: {shapiro_p:.4f}\nInterpretación: {interpretation}',
                        transform=ax2.transAxes, va='top',
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            ax2.set_xlabel('Valores')
            ax2.set_ylabel('Densidad')
            ax2.set_title('Prueba de Normalidad')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating Q-Q plot: {e}")
            return None
        
    def _generate_correlation_heatmap(self, correlation_matrix, variables):
        """Generar mapa de calor de correlaciones"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Construir matriz numérica
            n_vars = len(variables)
            corr_array = np.zeros((n_vars, n_vars))
            
            for i, var1 in enumerate(variables):
                for j, var2 in enumerate(variables):
                    if var1 in correlation_matrix and var2 in correlation_matrix[var1]:
                        corr_array[i, j] = correlation_matrix[var1][var2]['coefficient']
                    elif i == j:
                        corr_array[i, j] = 1.0
            
            # Crear heatmap
            im = ax.imshow(corr_array, cmap='RdBu_r', aspect='auto', vmin=-1, vmax=1)
            
            # Configurar ticks y etiquetas
            ax.set_xticks(np.arange(n_vars))
            ax.set_yticks(np.arange(n_vars))
            ax.set_xticklabels(variables, rotation=45, ha='right')
            ax.set_yticklabels(variables)
            
            # Agregar valores de correlación
            for i in range(n_vars):
                for j in range(n_vars):
                    text = ax.text(j, i, f'{corr_array[i, j]:.2f}',
                                ha="center", va="center", color="black", fontsize=8)
            
            ax.set_title('Matriz de Correlación entre Variables')
            
            # Colorbar
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label('Coeficiente de Correlación')
            
            plt.tight_layout()
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating correlation heatmap: {e}")
            return None
        
    def _generate_autocorrelation_plot(self, data, max_lags=20):
        """Generar gráfico de autocorrelación"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            
            # Calcular autocorrelación manual
            def autocorrelation(x, max_lags):
                n = len(x)
                x = np.array(x) - np.mean(x)
                autocorr = np.correlate(x, x, mode='full')
                autocorr = autocorr[autocorr.size // 2:]
                autocorr = autocorr / autocorr[0]  # Normalizar
                return autocorr[:max_lags+1]
            
            # ACF
            lags = np.arange(min(max_lags + 1, len(data)))
            acf_values = autocorrelation(data, max_lags)[:len(lags)]
            
            ax1.bar(lags, acf_values, alpha=0.7, color='blue')
            ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            ax1.axhline(y=0.05, color='red', linestyle='--', alpha=0.5, label='Umbral 5%')
            ax1.axhline(y=-0.05, color='red', linestyle='--', alpha=0.5)
            ax1.set_xlabel('Lag')
            ax1.set_ylabel('Autocorrelación')
            ax1.set_title('Función de Autocorrelación (ACF)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Gráfico de lag-1
            if len(data) > 1:
                ax2.scatter(data[:-1], data[1:], alpha=0.6)
                ax2.set_xlabel('Valor en t')
                ax2.set_ylabel('Valor en t+1')
                ax2.set_title('Gráfico de Lag-1')
                ax2.grid(True, alpha=0.3)
                
                # Línea de regresión
                from scipy import stats
                slope, intercept, r_value, _, _ = stats.linregress(data[:-1], data[1:])
                line = slope * np.array(data[:-1]) + intercept
                ax2.plot(data[:-1], line, 'r-', label=f'R = {r_value:.3f}')
                ax2.legend()
            
            plt.tight_layout()
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating autocorrelation plot: {e}")
            return None
        
    def _generate_performance_dashboard(self, performance_metrics):
        """Generar dashboard de métricas de performance"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            fig = plt.figure(figsize=(15, 10))
            
            # Crear grid de subplots
            gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
            
            # 1. Gauge de MAPE
            ax1 = fig.add_subplot(gs[0, 0])
            mape = performance_metrics.get('mape', 0)
            self._create_gauge_chart(ax1, mape, 'MAPE (%)', max_val=50)
            
            # 2. Gauge de R²
            ax2 = fig.add_subplot(gs[0, 1])
            r_squared = performance_metrics.get('r_squared', 0)
            self._create_gauge_chart(ax2, r_squared * 100, 'R² (%)', max_val=100)
            
            # 3. Gauge de Nash-Sutcliffe
            ax3 = fig.add_subplot(gs[0, 2])
            nash = performance_metrics.get('nash_sutcliffe', 0)
            self._create_gauge_chart(ax3, nash * 100, 'Nash-Sutcliffe (%)', max_val=100)
            
            # 4. Barras de métricas de error
            ax4 = fig.add_subplot(gs[1, :])
            metrics = ['MAE', 'RMSE', 'MAPE']
            values = [
                performance_metrics.get('mae', 0),
                performance_metrics.get('rmse', 0),
                performance_metrics.get('mape', 0)
            ]
            colors = ['#FF9999', '#66B2FF', '#99FF99']
            
            bars = ax4.bar(metrics, values, color=colors, alpha=0.7, edgecolor='black')
            ax4.set_ylabel('Valor')
            ax4.set_title('Métricas de Error del Modelo')
            ax4.grid(True, alpha=0.3, axis='y')
            
            # Agregar valores en las barras
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax4.text(bar.get_x() + bar.get_width()/2., height,
                        f'{value:.2f}', ha='center', va='bottom')
            
            # 5. Texto de interpretación
            ax5 = fig.add_subplot(gs[2, :])
            ax5.axis('off')
            
            accuracy_level = performance_metrics.get('accuracy_level', 'N/A')
            model_quality = performance_metrics.get('model_quality', 'N/A')
            
            interpretation_text = f"""
            INTERPRETACIÓN DE RESULTADOS:
            
            Nivel de Precisión: {accuracy_level}
            Calidad del Modelo: {model_quality}
            
            MAPE: {mape:.2f}% - {'Excelente' if mape < 10 else 'Bueno' if mape < 20 else 'Regular'}
            R²: {r_squared:.3f} - {'Muy bueno' if r_squared > 0.8 else 'Bueno' if r_squared > 0.6 else 'Regular'}
            
            RECOMENDACIONES:
            {'• El modelo muestra excelente precisión' if mape < 10 else '• Considerar ajustes para mejorar precisión'}
            {'• Alta capacidad explicativa del modelo' if r_squared > 0.8 else '• Revisar variables explicativas'}
            """
            
            ax5.text(0.05, 0.95, interpretation_text, transform=ax5.transAxes, va='top',
                    fontfamily='monospace', fontsize=10,
                    bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
            
            plt.suptitle('Dashboard de Performance del Modelo', fontsize=16, fontweight='bold')
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating performance dashboard: {e}")
            return None
        
    def _create_gauge_chart(self, ax, value, title, max_val=100):
        """Crear gráfico de gauge (medidor)"""
        try:
            import matplotlib.patches as patches
            import numpy as np
            
            # Configurar el gauge
            ax.set_xlim(-1.1, 1.1)
            ax.set_ylim(-1.1, 1.1)
            ax.set_aspect('equal')
            
            # Crear semicírculo
            theta = np.linspace(0, np.pi, 100)
            x = np.cos(theta)
            y = np.sin(theta)
            
            # Colorear segmentos según el valor
            if 'MAPE' in title:
                # Para MAPE, menor es mejor
                if value < 10:
                    color = 'green'
                elif value < 20:
                    color = 'orange'
                else:
                    color = 'red'
            else:
                # Para R² y Nash-Sutcliffe, mayor es mejor
                if value > 80:
                    color = 'green'
                elif value > 60:
                    color = 'orange'
                else:
                    color = 'red'
            
            # Dibujar el arco del gauge
            arc = patches.Arc((0, 0), 2, 2, angle=0, theta1=0, theta2=180, 
                            linewidth=10, color='lightgray', alpha=0.3)
            ax.add_patch(arc)
            
            # Dibujar el valor actual
            angle = np.pi * (1 - value / max_val) if max_val > 0 else np.pi/2
            ax.plot([0, np.cos(angle)], [0, np.sin(angle)], 
                color=color, linewidth=8, solid_capstyle='round')
            
            # Agregar texto
            ax.text(0, -0.3, f'{value:.1f}', ha='center', va='center', 
                fontsize=14, fontweight='bold')
            ax.text(0, -0.5, title, ha='center', va='center', fontsize=10)
            
            ax.axis('off')
            
        except Exception as e:
            logger.error(f"Error creating gauge chart: {e}")
            
    
    def generate_validation_charts_complete(self, validation_results: Dict) -> Dict[str, Any]:
        """
        MÉTODO PRINCIPAL para generar todos los gráficos de validación
        """
        try:
            logger.info("Iniciando generación completa de gráficos de validación")
            
            by_variable = validation_results.get('by_variable', {})
            all_variables_extracted = validation_results.get('all_variables_extracted', [])
            
            if not by_variable:
                logger.error("Sin variables para validar en by_variable")
                return {}
            
            if not all_variables_extracted:
                logger.error("Sin datos extraídos en all_variables_extracted")
                return {}
            
            # Generar gráficos por tipo de variable
            charts_by_type = {}
            
            # Agrupar variables por tipo
            variables_by_type = {}
            for var_key, var_data in by_variable.items():
                var_type = var_data.get('type', 'Otra')
                if var_type not in variables_by_type:
                    variables_by_type[var_type] = {}
                variables_by_type[var_type][var_key] = var_data
            
            logger.info(f"Variables agrupadas en {len(variables_by_type)} tipos")
            
            # Generar gráficos para cada tipo
            total_charts_generated = 0
            
            for var_type, variables in variables_by_type.items():
                type_charts = []
                
                # Limitar a máximo 15 variables por tipo
                variables_limited = dict(list(variables.items())[:15])
                
                for var_key, var_data in variables_limited.items():
                    try:
                        # Generar gráfico individual
                        chart_data = self._generate_complete_variable_chart_corrected(
                            var_key, var_data, var_type, all_variables_extracted
                        )
                        
                        if chart_data and chart_data.get('chart'):
                            type_charts.append(chart_data)
                            total_charts_generated += 1
                            logger.debug(f"Gráfico generado para {var_key}")
                        else:
                            logger.warning(f"No se pudo generar gráfico para {var_key}")
                            
                    except Exception as e:
                        logger.error(f"Error generando gráfico para {var_key}: {str(e)}")
                        continue
                
                if type_charts:
                    charts_by_type[var_type] = type_charts
                    logger.info(f"Generados {len(type_charts)} gráficos para tipo {var_type}")
            
            # Generar gráfico resumen
            summary_chart = self._generate_validation_summary_chart(variables_by_type)
            if summary_chart:
                charts_by_type['summary'] = summary_chart
                total_charts_generated += 1
            
            logger.info(f"TOTAL: {total_charts_generated} gráficos de validación generados")
            
            return charts_by_type
            
        except Exception as e:
            logger.error(f"Error en generación completa de gráficos: {str(e)}")
            return {}
        
    def _generate_validation_summary_chart(self, variables_by_type: Dict) -> str:
        """
        Generar gráfico resumen de validación
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            import numpy as np
            from io import BytesIO
            import base64
            
            if not variables_by_type:
                return None
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
            
            # Gráfico 1: Distribución por estado
            all_statuses = []
            for var_type, variables in variables_by_type.items():
                for var_key, var_data in variables.items():
                    status = var_data.get('status', 'UNKNOWN')
                    all_statuses.append(status)
            
            status_counts = {}
            for status in all_statuses:
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Colores para estados
            status_colors = {
                'PRECISE': '#27AE60',
                'ACCEPTABLE': '#F39C12', 
                'MARGINAL': '#E67E22',
                'INACCURATE': '#E74C3C',
                'NO_DATA': '#7F8C8D'
            }
            
            statuses = list(status_counts.keys())
            counts = list(status_counts.values())
            colors = [status_colors.get(s, '#95A5A6') for s in statuses]
            
            wedges, texts, autotexts = ax1.pie(counts, labels=statuses, colors=colors, 
                                            autopct='%1.1f%%', startangle=90)
            ax1.set_title('Distribución de Estados de Validación', fontsize=14, fontweight='bold')
            
            # Gráfico 2: Error promedio por tipo
            type_errors = {}
            for var_type, variables in variables_by_type.items():
                errors = []
                for var_data in variables.values():
                    error_pct = var_data.get('error_pct', 0)
                    if error_pct is not None:
                        errors.append(error_pct)
                
                if errors:
                    type_errors[var_type] = np.mean(errors)
            
            if type_errors:
                types = list(type_errors.keys())
                avg_errors = list(type_errors.values())
                
                # Colores basados en error
                bar_colors = []
                for error in avg_errors:
                    if error < 5:
                        bar_colors.append('#27AE60')
                    elif error < 15:
                        bar_colors.append('#F39C12')
                    else:
                        bar_colors.append('#E74C3C')
                
                bars = ax2.bar(types, avg_errors, color=bar_colors, alpha=0.8, edgecolor='black')
                
                # Agregar valores en barras
                for bar, error in zip(bars, avg_errors):
                    height = bar.get_height()
                    ax2.text(bar.get_x() + bar.get_width()/2., height + max(avg_errors) * 0.01,
                            f'{error:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')
                
                ax2.set_ylabel('Error Promedio (%)', fontsize=12, fontweight='bold')
                ax2.set_title('Error Promedio por Tipo de Variable', fontsize=14, fontweight='bold')
                ax2.set_xticklabels(types, rotation=45, ha='right')
                
                # Líneas de referencia
                ax2.axhline(y=5, color='green', linestyle='--', alpha=0.7, label='Preciso (≤5%)')
                ax2.axhline(y=15, color='orange', linestyle='--', alpha=0.7, label='Aceptable (≤15%)')
                ax2.legend()
            
            ax2.grid(True, alpha=0.3, axis='y')
            
            plt.suptitle('RESUMEN DE VALIDACIÓN DEL MODELO', fontsize=18, fontweight='bold')
            plt.tight_layout()
            
            # Convertir a base64
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            return chart_base64
            
        except Exception as e:
            logger.error(f"Error generando gráfico resumen: {str(e)}")
            plt.close('all')
            return None
        
    def generate_qqplot(self, demand_data: List[float]) -> Optional[str]:
        """
        Generar Q-Q plot usando ChartDemand
        """
        try:
            # Usar ChartDemand para generar el Q-Q plot
            from ..utils.chart_demand_utils import ChartDemand
            chart_demand = ChartDemand()
            return chart_demand.create_qq_plot(demand_data)
        except Exception as e:
            logger.error(f"Error en generate_qqplot: {e}")
            return None

    def create_qq_plot(self, demand_data: List[float]) -> Optional[str]:
        """Método alternativo para crear Q-Q plot"""
        return self.generate_qqplot(demand_data)