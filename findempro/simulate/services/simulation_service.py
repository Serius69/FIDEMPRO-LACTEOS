from venv import logger
from simulate.services.simulation_core import SimulationCore
from simulate.services.simulation_financial import SimulationFinancialAnalyzer
from simulate.services.statistical_service import StatisticalService
from simulate.services.validation_service import SimulationValidationService
from simulate.validators.simulation_validators import SimulationValidator


class SimulationService:
    """Unified simulation service that coordinates all simulation operations"""
    
    def __init__(self):
        self.core = SimulationCore()
        self.validator = SimulationValidator()
        self.statistical = StatisticalService()
        self.financial = SimulationFinancialAnalyzer()
        self.validation = SimulationValidationService()
    
    def prepare_simulation_analysis(self, questionary_id, user, quantity_time, unit_time):
        """Prepare all data needed for simulation configuration"""
        try:
            # Get questionary data
            questionary_result = self._get_questionary_with_data(questionary_id)
            
            # Extract and validate demand history
            demand_history = self._extract_demand_history(questionary_result)
            if not demand_history:
                return {'error': 'No se encontraron datos históricos de demanda'}
            
            # Perform statistical analysis
            analysis_results = self.statistical.analyze_demand_history(
                questionary_result.id, user
            )
            
            # Get related data
            product = questionary_result.fk_questionary.fk_product
            areas = self._get_product_areas(product)
            fdps = self._get_available_fdps(product.fk_business)
            
            # Generate initial charts
            charts = self._generate_analysis_charts(demand_history, analysis_results)
            
            return {
                'questionary_result_instance': questionary_result,
                'areas': areas,
                'fdps': fdps,
                'demand_history': demand_history,
                'selected_quantity_time': quantity_time,
                'selected_unit_time': unit_time,
                **analysis_results,
                **charts
            }
            
        except Exception as e:
            logger.error(f"Error preparing simulation analysis: {str(e)}")
            return {'error': 'Error al preparar el análisis de simulación'}