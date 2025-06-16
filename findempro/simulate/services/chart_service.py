from venv import logger
from simulate.utils.chart_base_utils import ChartBase
from simulate.utils.chart_demand_utils import ChartDemand
import numpy as np
import matplotlib.pyplot as plt

from utils.chart_utils import get_simulation_data, get_historical_demand_data, get_real_values_data
from utils.chart_utils import get_simulation_results, get_historical_demand, get_real_values
from simulate.utils.chart_base_utils import ChartBase
from simulate.utils.chart_demand_utils import ChartDemand

class ChartService:
    """Unified chart generation service"""
    
    def __init__(self):
        self.base_generator = ChartBase()
        self.demand_generator = ChartDemand()
        self.cache_timeout = 3600
    
    def generate_simulation_charts(self, simulation, results, historical_demand, real_values):
        """Generate all charts for simulation results"""
        charts = {}
        
        # Extract data
        dates = [r.date for r in results]
        daily_data = self._extract_daily_data(results)
        
        # Generate each chart type
        charts['demand_comparison'] = self.generate_demand_comparison_chart(
            historical_demand, results
        )
        
        charts['financial_overview'] = self._generate_financial_overview(
            dates, daily_data
        )
        
        charts['production_efficiency'] = self._generate_production_efficiency(
            dates, daily_data
        )
        
        charts['inventory_analysis'] = self._generate_inventory_analysis(
            dates, daily_data
        )
        
        charts['kpi_dashboard'] = self._generate_kpi_dashboard(
            daily_data
        )
        
        # Add validation charts if real values available
        if real_values:
            charts['validation_comparison'] = self._generate_validation_charts(
                daily_data, real_values
            )
        
        return charts
    
    def generate_demand_comparison_chart(self, historical_demand, simulated_results):
        """Generate unified demand comparison chart"""
        try:
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
            
            # Extract simulated demand - USING DAILY VALUES, NOT AVERAGES
            simulated_demand = [float(r.demand_mean) for r in simulated_results]
            sim_days = list(range(1, len(simulated_demand) + 1))
            
            # Plot historical vs simulated
            if historical_demand:
                hist_days = list(range(-len(historical_demand), 0))
                ax1.plot(hist_days, historical_demand, 'gray', linewidth=2, 
                        marker='o', label='Demanda Histórica')
                
                # Statistics for historical
                hist_mean = np.mean(historical_demand)
                hist_std = np.std(historical_demand)
                ax1.axhline(y=hist_mean, color='gray', linestyle=':', 
                           label=f'Media Histórica: {hist_mean:.1f}')
            
            # Plot simulated with daily variation
            ax1.plot(sim_days, simulated_demand, 'b-', linewidth=2, 
                    marker='s', label='Demanda Simulada Diaria')
            
            # Add transition line
            ax1.axvline(x=0.5, color='red', linestyle='--', alpha=0.5)
            
            ax1.set_xlabel('Días')
            ax1.set_ylabel('Demanda (Litros)')
            ax1.set_title('Comparación: Demanda Histórica vs Simulada (Valores Diarios)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Distribution comparison
            if historical_demand:
                ax2.hist(historical_demand, bins=20, alpha=0.5, label='Histórico', 
                        color='gray', density=True)
            ax2.hist(simulated_demand, bins=20, alpha=0.5, label='Simulado', 
                    color='blue', density=True)
            
            ax2.set_xlabel('Demanda (Litros)')
            ax2.set_ylabel('Densidad')
            ax2.set_title('Distribución de Probabilidad')
            ax2.legend()
            
            # Daily variation analysis
            if len(simulated_demand) > 1:
                daily_changes = [simulated_demand[i] - simulated_demand[i-1] 
                               for i in range(1, len(simulated_demand))]
                ax3.bar(range(1, len(daily_changes) + 1), daily_changes, 
                       color=['green' if c > 0 else 'red' for c in daily_changes])
                ax3.axhline(y=0, color='black', linestyle='-')
                ax3.set_xlabel('Días')
                ax3.set_ylabel('Cambio en Demanda')
                ax3.set_title('Variación Diaria de Demanda')
            
            plt.tight_layout()
            return self._fig_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error generating demand comparison chart: {str(e)}")
            return None