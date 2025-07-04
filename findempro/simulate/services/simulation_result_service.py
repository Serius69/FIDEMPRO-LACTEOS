import logging
from simulate.models import ResultSimulation
from simulate.services.chart_service import ChartService
from simulate.utils.simulation_math_utils import SimulationMathEngine
from simulate.utils.simulation_financial_utils import SimulationFinancialAnalyzer
from services.validation_service import SimulationValidationService

logger = logging.getLogger(__name__)
class SimulationResultService:
    """Service for handling simulation results and analysis"""
    
    def __init__(self):
        self.validation_service = SimulationValidationService()
        self.financial_analyzer = SimulationFinancialAnalyzer()
        self.chart_service = ChartService()
        self.math_engine = SimulationMathEngine()
    
    def get_complete_simulation_analysis(self, simulation_id, page=1):
        """Get complete analysis for simulation results"""
        try:
            # Get simulation
            simulation = self._get_simulation_with_data(simulation_id)
            
            # Get paginated results
            results_page = self._get_paginated_results(simulation_id, page)
            
            # Get all results for analysis
            all_results = list(ResultSimulation.objects.filter(
                fk_simulation_id=simulation_id,
                is_active=True
            ).order_by('date'))
            
            # Extract key data
            historical_demand = self._extract_historical_demand(simulation)
            real_values = self._extract_real_values(simulation)
            
            # Perform analyses
            validation_results = self.validation_service.validate_simulation(simulation_id)
            financial_analysis = self.financial_analyzer.analyze_financial_results(simulation_id)
            
            # Generate all charts through unified service
            chart_data = self.chart_service.generate_simulation_charts(
                simulation, all_results, historical_demand, real_values
            )
            
            # Calculate summaries
            summary_stats = self._calculate_comprehensive_summary(
                all_results, historical_demand, validation_results, financial_analysis
            )
            
            return {
                'simulation': simulation,
                'results': results_page,
                'historical_demand': historical_demand,
                'real_values': real_values,
                'validation_results': validation_results,
                'financial_analysis': financial_analysis,
                'charts': chart_data,
                'summary': summary_stats,
                'product': simulation.fk_questionary_result.fk_questionary.fk_product,
                'business': simulation.fk_questionary_result.fk_questionary.fk_product.fk_business,
            }
            
        except Exception as e:
            logger.error(f"Error getting simulation analysis: {str(e)}")
            return {'error': 'Error al obtener análisis de simulación'}