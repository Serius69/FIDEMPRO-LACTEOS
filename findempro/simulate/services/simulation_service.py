# services/simulation_service.py
import json
import logging
import random
import statistics
from datetime import timedelta
from typing import Dict, List, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import sympy as sp
from sympy import symbols, Eq, solve
from scipy import stats

from django.core.cache import cache
from django.db import transaction
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404

from ..models import (
    Simulation, ResultSimulation, Demand, DemandBehavior,
    ProbabilisticDensityFunction
)
from ..validators.simulation_validators import SimulationValidator
from ..utils.data_parsers import DataParser

from business.models import Business
from finance.models import FinanceRecommendation, FinanceRecommendationSimulation
from product.models import Product, Area
from questionary.models import QuestionaryResult, Answer, Question
from variable.models import Variable, Equation

logger = logging.getLogger(__name__)


class SimulationService:
    """Enhanced service class for handling simulation business logic"""
    
    def __init__(self):
        self.validator = SimulationValidator()
        self.cache_timeout = 3600  # 1 hour cache
        self.batch_size = 100  # For bulk operations
        
        # Mapeo completo de variables desde questionary a variables del sistema
        self.variable_mapping = {
            # Mapeo desde questionary_result_data.py a variables_data.py
            'precio_actual': 'PVP',
            'demanda_historica': 'DH',
            'produccion_actual': 'QPL',
            'demanda_esperada': 'DE',
            'capacidad_inventario': 'CIP',
            'estacionalidad': 'ED',
            'costo_unitario_insumo': 'CUIP',
            'tiempo_entre_compras': 'TPC',
            'clientes_diarios': 'CPD',
            'numero_empleados': 'NEPP',
            'capacidad_produccion': 'CPROD',
            'sueldos_salarios': 'SE',
            'precio_competencia': 'PC',
            'costo_fijo_diario': 'CFD',
            'costo_transporte': 'CUTRANS',
            'gastos_marketing': 'GMM',
            'tiempo_reabastecimiento': 'TR',
            'insumos_por_producto': 'CINSP',
            'capacidad_almacenamiento': 'CMIPF',
            'tiempo_produccion_unitario': 'TPE',
            'cantidad_por_lote': 'CPPL',
            'stock_seguridad': 'SI',
            'dias_reabastecimiento': 'DPL',
            'tiempo_procesamiento_pedidos': 'TMP',
            'cantidad_transporte_viaje': 'CTPLV',
            'numero_proveedores': 'NPD',
            'consumo_diario_proveedor': 'CTL',
            'cantidad_promedio_lote': 'CPL'
        }
        
    @transaction.atomic
    def create_simulation(self, form_data: Dict[str, Any]) -> Simulation:
        """Create a new simulation instance with validation and optimization"""
        try:
            logger.info("=== STARTING SIMULATION CREATION ===")
            logger.info(f"Raw form data: {form_data}")
            
            # Validate form data
            validated_data = self.validator.validate_simulation_parameters(form_data)
            logger.info(f"Validated data: {validated_data}")
            
            # Get related instances with select_related for optimization
            fk_fdp_instance = get_object_or_404(
                ProbabilisticDensityFunction.objects.select_related('fk_business'),
                id=validated_data['fk_fdp_id']
            )
            
            fk_questionary_result_instance = get_object_or_404(
                QuestionaryResult.objects.select_related(
                    'fk_questionary__fk_product__fk_business'
                ),
                id=validated_data['fk_questionary_result']
            )
            
            # Create simulation with parsed demand history
            simulation_instance = Simulation.objects.create(
                fk_questionary_result=fk_questionary_result_instance,
                quantity_time=validated_data['quantity_time'],
                unit_time=validated_data['unit_time'],
                demand_history=json.dumps(validated_data['demand_history']),  # Store as JSON
                fk_fdp=fk_fdp_instance,
                is_active=True
            )
            
            logger.info(f"Simulation {simulation_instance.id} created successfully")
            return simulation_instance
            
        except Exception as e:
            logger.error(f"Error creating simulation: {str(e)}")
            raise
    
    def _parse_demand_history(self, demand_history: Any) -> List[float]:
        """Parse demand history string to list of floats"""
        try:
            # Use DataParser for consistent parsing
            parser = DataParser()
            return parser.parse_demand_history(demand_history)
        except Exception as e:
            logger.error(f"Error parsing demand history: {str(e)}")
            # Fallback parsing
            if isinstance(demand_history, str):
                try:
                    return json.loads(demand_history)
                except:
                    cleaned = demand_history.replace('[', '').replace(']', '').split()
                    return [float(x.replace(',', '')) for x in cleaned if x]
            elif isinstance(demand_history, list):
                return [float(x) for x in demand_history]
            else:
                return []
    
    @transaction.atomic
    def execute_simulation(self, simulation_instance: Simulation) -> None:
        """Execute simulation with parallel processing and optimization"""
        try:
            nmd = int(simulation_instance.quantity_time)
            logger.info(f"Starting simulation execution for {nmd} days")
            
            # Get all required data upfront with optimized queries
            simulation_data = self._prepare_simulation_data(simulation_instance)
            
            # Fix equations before processing
            simulation_data['equations'] = self._fix_equations(simulation_data['equations'])
            
            # Sort equations by dependencies
            simulation_data['equations'] = self._sort_equations_by_dependency(simulation_data['equations'])
            
            # Process days sequentially (not in parallel) to maintain state
            results_to_save = []
            
            for day_index in range(nmd):
                try:
                    day_results = self._simulate_single_day_complete(
                        simulation_instance, simulation_data, day_index
                    )
                    results_to_save.append((day_index, day_results))
                except Exception as e:
                    logger.error(f"Error simulating day {day_index}: {str(e)}")
                    continue
            
            # Bulk save results
            self._bulk_save_results(simulation_instance, results_to_save)
            
            logger.info(f"Simulation {simulation_instance.id} executed successfully")
            
        except Exception as e:
            logger.error(f"Error executing simulation {simulation_instance.id}: {str(e)}")
            raise
    
    def _sort_equations_by_dependency(self, equations: List) -> List:
        """Sort equations by area and dependency order"""
        # Define area processing order
        area_order = [
            'Ventas',
            'Producción',
            'Abastecimiento',
            'Inventario Insumos',
            'Inventario Productos Finales',
            'Contabilidad',
            'Distribución',
            'Marketing',
            'Recursos Humanos',
            'Competencia'
        ]
        
        # Group equations by area
        equations_by_area = {}
        for eq in equations:
            area_name = eq.fk_area.name if eq.fk_area else 'Other'
            if area_name not in equations_by_area:
                equations_by_area[area_name] = []
            equations_by_area[area_name].append(eq)
        
        # Build sorted list
        sorted_equations = []
        
        # Add equations in area order
        for area in area_order:
            if area in equations_by_area:
                sorted_equations.extend(equations_by_area[area])
        
        # Add any remaining equations
        for area, eqs in equations_by_area.items():
            if area not in area_order:
                sorted_equations.extend(eqs)
        
        return sorted_equations
    
    def _fix_equations(self, equations: List) -> List:
        """Fix known problematic equations"""
        fixed_equations = []
        
        # Known problematic equations and their fixes
        equation_fixes = {
            'GT = IT - GT': 'GT = IT - GO - GG',
            'II = II + PI - UII': 'II = PI - UII',
            'IPF = IPF + PPL - VPC': 'IPF = PPL - TPV',
            'VPC = TPV / TCAE': 'VPC = TPV / max(TCAE, 1)',  # Avoid division by zero
        }
        
        for equation in equations:
            expression = equation.expression
            
            # Apply fixes
            for problem, fix in equation_fixes.items():
                if expression.strip() == problem:
                    equation.expression = fix
                    logger.info(f"Fixed equation: {problem} -> {fix}")
                    break
            
            fixed_equations.append(equation)
        
        return fixed_equations
    
    
    def _simulate_single_day_complete(
        self, simulation_instance: Simulation, simulation_data: Dict[str, Any], 
        day_index: int
    ) -> Dict[str, Any]:
        """Simulate a single day with complete calculations"""
        
        # Initialize variable dictionary with all answers
        variable_dict = self._initialize_variables_complete(
            simulation_data['answers'], simulation_instance, day_index
        )
        
        # Generate demand prediction
        predicted_demand = self._generate_demand_prediction(
            simulation_instance, variable_dict, day_index
        )
        
        # Update demand-related variables
        variable_dict['DE'] = predicted_demand
        variable_dict['DH'] = predicted_demand
        
        # Add calculated variables that don't depend on equations
        variable_dict = self._add_calculated_variables(variable_dict, day_index)
        
        # Solve all equations
        endogenous_results = self._solve_all_equations(
            simulation_data['equations'], variable_dict
        )
        
        # Ensure all critical variables are in results
        critical_variables = ['DE', 'DH', 'TPV', 'IT', 'GT', 'GO', 'GG', 'TCAE', 'VPC']
        for var in critical_variables:
            if var not in endogenous_results and var in variable_dict:
                endogenous_results[var] = variable_dict[var]
        
        # Log summary of results
        logger.info(f"Day {day_index}: Calculated {len(endogenous_results)} variables")
        logger.debug(f"Results: {list(endogenous_results.keys())}")
        
        return {
            'endogenous_results': endogenous_results,
            'variable_initials_dict': variable_dict,
            'predicted_demand': predicted_demand
        }
    
    def _add_calculated_variables(self, variable_dict: Dict[str, float], day_index: int) -> Dict[str, float]:
        """Add calculated variables that don't depend on equations"""
        
        # Random values for simulation
        variable_dict['ALC'] = random.random()  # Aleatorio llegada clientes
        variable_dict['AV'] = random.random()   # Aleatorio venta
        
        # Time-based calculations
        variable_dict['DIA'] = float(day_index + 1)
        
        # Ensure TCAE has a value
        if 'TCAE' not in variable_dict or variable_dict['TCAE'] == 0:
            variable_dict['TCAE'] = variable_dict.get('CPD', 85) * variable_dict.get('ALC', 0.9)
        
        return variable_dict
    
    def _solve_all_equations(
        self, equations: List, variable_dict: Dict[str, float]
    ) -> Dict[str, float]:
        """Solve all equations with multiple passes"""
        endogenous_results = {}
        max_iterations = 10
        
        for iteration in range(max_iterations):
            equations_solved = 0
            
            for equation in equations:
                try:
                    # Get output variable
                    output_var = self._get_output_variable(equation)
                    if not output_var:
                        continue
                    
                    # Skip if already solved
                    if output_var in endogenous_results:
                        continue
                    
                    # Try to solve
                    combined_dict = {**variable_dict, **endogenous_results}
                    result = self._solve_equation_robust(equation, combined_dict)
                    
                    if result is not None:
                        endogenous_results[output_var] = result
                        variable_dict[output_var] = result
                        equations_solved += 1
                        logger.debug(f"Solved {output_var} = {result}")
                        
                except Exception as e:
                    logger.error(f"Error solving equation {equation.expression}: {e}")
                    continue
            
            # If no progress, break
            if equations_solved == 0:
                break
            
            logger.info(f"Iteration {iteration}: Solved {equations_solved} equations")
        
        # Calculate any missing critical variables manually
        if 'TPV' not in endogenous_results:
            endogenous_results['TPV'] = variable_dict.get('TCAE', 85) * variable_dict.get('VPC', 30)
        
        if 'IT' not in endogenous_results:
            endogenous_results['IT'] = endogenous_results.get('TPV', 0) * variable_dict.get('PVP', 15.50)
        
        if 'CTAI' not in endogenous_results:
            endogenous_results['CTAI'] = variable_dict.get('CUIP', 8.20) * variable_dict.get('CPROD', 3000)
        
        if 'GO' not in endogenous_results:
            endogenous_results['GO'] = (
                variable_dict.get('CFD', 1800) + 
                variable_dict.get('SE', 48000) / 30 +  # Monthly to daily
                endogenous_results.get('CTAI', 0)
            )
        
        if 'GG' not in endogenous_results:
            endogenous_results['GG'] = (
                endogenous_results.get('GO', 0) + 
                variable_dict.get('GMM', 3500) / 30  # Monthly to daily
            )
        
        if 'TG' not in endogenous_results:
            endogenous_results['TG'] = endogenous_results.get('GO', 0) + endogenous_results.get('GG', 0)
        
        if 'GT' not in endogenous_results:
            endogenous_results['GT'] = endogenous_results.get('IT', 0) - endogenous_results.get('TG', 0)
        
        return endogenous_results
    
    def _solve_equation_robust(self, equation: Equation, variable_dict: Dict[str, float]) -> Optional[float]:
        """Robustly solve a single equation"""
        try:
            expression = equation.expression
            
            if '=' not in expression:
                return None
            
            lhs, rhs = expression.split('=', 1)
            lhs = lhs.strip()
            rhs = rhs.strip()
            
            # Handle special cases
            rhs = rhs.replace('∑', '')
            rhs = rhs.replace('random()', str(random.random()))
            
            # Replace all variables with their values
            for var, val in sorted(variable_dict.items(), key=lambda x: len(x[0]), reverse=True):
                if var in rhs:
                    # Use word boundaries for exact matches
                    pattern = r'\b' + re.escape(var) + r'\b'
                    rhs = re.sub(pattern, str(val), rhs)
            
            # Evaluate the expression
            try:
                # Safe evaluation
                safe_dict = {
                    '__builtins__': {},
                    'min': min,
                    'max': max,
                    'abs': abs,
                    'round': round,
                }
                
                result = eval(rhs, safe_dict)
                return float(result)
                
            except ZeroDivisionError:
                logger.warning(f"Division by zero in equation: {expression}")
                return 0.0
            except Exception as e:
                logger.debug(f"Could not evaluate {lhs} = {rhs}: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Error in solve_equation_robust: {e}")
            return None
    
    def _initialize_variables_complete(
        self, answers: List[Dict], simulation_instance: Simulation, day_index: int
    ) -> Dict[str, float]:
        """Initialize all variables from answers with complete mapping"""
        variable_dict = {}
        
        # Parse demand history
        demand_history = self._parse_demand_history(simulation_instance.demand_history)
        demand_mean = np.mean(demand_history) if demand_history else 2500.0
        
        # Process each answer
        for answer_data in answers:
            var_initials = answer_data.get('fk_question__fk_variable__initials')
            answer_value = answer_data.get('answer')
            
            if not var_initials or answer_value is None:
                continue
            
            # Apply variable mapping if needed
            if var_initials in self.variable_mapping:
                var_initials = self.variable_mapping[var_initials]
            
            # Process the value
            try:
                if var_initials == 'DH':
                    variable_dict['DH'] = demand_mean
                elif answer_value == 'Sí':
                    variable_dict[var_initials] = 1.0
                elif answer_value == 'No':
                    variable_dict[var_initials] = 0.0
                elif isinstance(answer_value, (list, tuple)):
                    # For array values, use mean
                    variable_dict[var_initials] = float(np.mean(answer_value))
                else:
                    # Clean and convert string values
                    if isinstance(answer_value, str):
                        cleaned = answer_value.replace(',', '').replace('$', '').replace('%', '')
                        variable_dict[var_initials] = float(cleaned)
                    else:
                        variable_dict[var_initials] = float(answer_value)
            except Exception as e:
                logger.warning(f"Could not process {var_initials}={answer_value}: {e}")
                continue
        
        # Add system variables
        variable_dict['NMD'] = float(simulation_instance.quantity_time)
        variable_dict['random'] = lambda: random.random()
        variable_dict['MLP'] = 480.0  # Minutos laborables por día (8 horas)
        
        # Add critical default values if missing
        defaults = {
            'PVP': 15.50,      # Precio de venta
            'CPD': 85,         # Clientes por día
            'VPC': 30,         # Ventas por cliente
            'TCAE': 85,        # Total clientes atendidos
            'SE': 48000,       # Sueldos empleados
            'CFD': 1800,       # Costo fijo diario
            'GMM': 3500,       # Gastos marketing
            'CUIP': 8.20,      # Costo unitario insumo
            'CPROD': 3000,     # Capacidad producción
            'NEPP': 15,        # Número empleados
            'CPPL': 500,       # Cantidad por lote
            'CPL': 2500,       # Cantidad promedio lote
            'QPL': 2500,       # Cantidad producida
            'CUTRANS': 0.35,   # Costo transporte
            'CTPLV': 1500,     # Cantidad transportada
            'TPE': 45,         # Tiempo producción
            'ED': 1.0,         # Estacionalidad
            'PC': 15.80,       # Precio competencia
            'TPC': 2,          # Tiempo entre compras
            'TR': 3,           # Tiempo reabastecimiento
            'CINSP': 1.05,     # Insumos por producto
            'SI': 3000,        # Stock seguridad
            'DPL': 3,          # Días reabastecimiento
            'TMP': 1,          # Tiempo procesamiento
            'NPD': 3,          # Número proveedores
            'CTL': 2800,       # Consumo diario
        }
        
        for var, default_val in defaults.items():
            if var not in variable_dict:
                variable_dict[var] = default_val
        
        return variable_dict
    
    def _prepare_simulation_data(self, simulation_instance: Simulation) -> Dict[str, Any]:
        """Prepare all simulation data with optimized queries"""
        product = simulation_instance.fk_questionary_result.fk_questionary.fk_product
        
        # Use select_related and prefetch_related for optimization
        areas = Area.objects.filter(
            is_active=True,
            fk_product=product
        ).prefetch_related(
            Prefetch(
                'area_equation',
                queryset=Equation.objects.filter(is_active=True).select_related(
                    'fk_variable1', 'fk_variable2', 'fk_variable3',
                    'fk_variable4', 'fk_variable5'
                )
            )
        ).order_by('id')
        
        equations = Equation.objects.filter(
            is_active=True,
            fk_area__in=areas
        ).select_related(
            'fk_variable1', 'fk_variable2', 'fk_variable3',
            'fk_variable4', 'fk_variable5', 'fk_area'
        ).order_by('fk_area_id')
        
        variables = Variable.objects.filter(
            is_active=True,
            fk_product=product
        ).values('id', 'name', 'initials', 'unit')
        
        answers = Answer.objects.filter(
            fk_questionary_result=simulation_instance.fk_questionary_result
        ).select_related('fk_question__fk_variable').values(
            'fk_question_id', 'fk_question__fk_variable__initials', 'answer'
        )
        
        return {
            'areas': list(areas),
            'equations': list(equations),
            'variables': {v['initials']: v for v in variables},
            'answers': list(answers),
            'product': product
        }
    
    def _simulate_single_day_optimized(
        self, simulation_instance: Simulation, simulation_data: Dict[str, Any], 
        day_index: int
    ) -> Dict[str, Any]:
        """Simulate a single day with optimizations"""
        # Process answers into variable dictionary
        variable_initials_dict = self._process_answers_optimized(
            simulation_data['answers'], simulation_instance
        )
        
        # Generate demand prediction using FDP
        predicted_demand = self._generate_demand_prediction(
            simulation_instance, variable_initials_dict, day_index
        )
        
        # Update variables with predicted demand
        variable_initials_dict['DE'] = predicted_demand  # Demanda Esperada
        variable_initials_dict['DH'] = predicted_demand  # También actualizar DH para ecuaciones
        
        # Add random variables for simulation
        variable_initials_dict['random()'] = random.random()
        
        # Solve equations with proper order
        endogenous_results = self._solve_equations_with_dependencies(
            simulation_data['equations'], variable_initials_dict
        )
        
        # Ensure predicted demand is in results
        endogenous_results['DE'] = predicted_demand
        endogenous_results['DH'] = predicted_demand
        
        return {
            'endogenous_results': endogenous_results,
            'variable_initials_dict': variable_initials_dict,
            'predicted_demand': predicted_demand
        }
    
    def _solve_equations_with_dependencies(
        self, equations: List, variable_dict: Dict[str, float]
    ) -> Dict[str, float]:
        """Solve equations considering dependencies and order"""
        endogenous_results = {}
        
        # Separate equations by area for proper ordering
        equations_by_area = {}
        for eq in equations:
            area_name = eq.fk_area.name if eq.fk_area else 'Other'
            if area_name not in equations_by_area:
                equations_by_area[area_name] = []
            equations_by_area[area_name].append(eq)
        
        # Define solving order by area
        area_order = [
            'Ventas',
            'Producción',
            'Abastecimiento',
            'Inventario Insumos',
            'Inventario Productos Finales',
            'Contabilidad',
            'Distribución',
            'Marketing',
            'Recursos Humanos',
            'Competencia'
        ]
        
        # Add any areas not in the predefined order
        for area in equations_by_area:
            if area not in area_order:
                area_order.append(area)
        
        # Solve equations by area in order
        for area in area_order:
            if area in equations_by_area:
                for equation in equations_by_area[area]:
                    result = self._solve_single_equation(
                        equation, {**variable_dict, **endogenous_results}
                    )
                    if result is not None:
                        var_name = self._get_output_variable(equation)
                        if var_name:
                            endogenous_results[var_name] = result
                            variable_dict[var_name] = result
        
        # Second pass for equations that depend on others
        max_iterations = 5
        for iteration in range(max_iterations):
            changes_made = False
            
            for area in area_order:
                if area in equations_by_area:
                    for equation in equations_by_area[area]:
                        var_name = self._get_output_variable(equation)
                        if var_name and var_name not in endogenous_results:
                            result = self._solve_single_equation(
                                equation, {**variable_dict, **endogenous_results}
                            )
                            if result is not None:
                                endogenous_results[var_name] = result
                                variable_dict[var_name] = result
                                changes_made = True
            
            if not changes_made:
                break
        
        return endogenous_results
    
    def _solve_single_equation(
        self, equation: Equation, variable_dict: Dict[str, float]
    ) -> Optional[float]:
        """Solve a single equation with better error handling"""
        try:
            expression = equation.expression
            
            # Get output variable (left side of equation)
            if '=' not in expression:
                return None
                
            lhs, rhs = expression.split('=', 1)
            output_var = lhs.strip()
            rhs = rhs.strip()
            
            # Handle special cases
            if '∑' in rhs:
                # Handle summation - for now, simplify
                rhs = rhs.replace('∑', '')
                # If it's a multiplication sum, evaluate it
                if '*' in rhs:
                    parts = rhs.split('*')
                    total = 1
                    for part in parts:
                        part = part.strip()
                        if part in variable_dict:
                            total *= variable_dict[part]
                        else:
                            try:
                                total *= float(part)
                            except:
                                return None
                    return float(total)
            
            # Handle random function
            rhs = rhs.replace('random()', str(random.random()))
            
            # Substitute all known variables
            for var_name, var_value in variable_dict.items():
                if var_name in rhs:
                    # Use word boundaries to avoid partial replacements
                    rhs = re.sub(r'\b' + re.escape(var_name) + r'\b', str(var_value), rhs)
            
            # Try to evaluate the expression
            try:
                # Safe evaluation context
                safe_dict = {
                    '__builtins__': {},
                    'min': min,
                    'max': max,
                    'abs': abs,
                    'round': round,
                    'random': random.random
                }
                
                result = eval(rhs, safe_dict)
                return float(result)
                
            except Exception as e:
                logger.debug(f"Could not evaluate {output_var} = {rhs}: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Error solving equation {equation.expression}: {str(e)}")
            return None
    
    def _generate_demand_prediction(
        self, simulation_instance: Simulation, variable_dict: Dict[str, float], 
        day_index: int
    ) -> float:
        """Generate demand prediction using the selected FDP"""
        try:
            fdp = simulation_instance.fk_fdp
            demand_history = self._parse_demand_history(simulation_instance.demand_history)
            
            # Calculate base statistics
            mean_demand = np.mean(demand_history)
            std_demand = np.std(demand_history)
            
            # Generate prediction based on distribution type
            if fdp.distribution_type == 1:  # Normal
                # Use FDP parameters if available, otherwise use historical
                mean_param = fdp.mean_param if fdp.mean_param else mean_demand
                std_param = fdp.std_dev_param if fdp.std_dev_param else std_demand
                prediction = np.random.normal(mean_param, std_param)
                
            elif fdp.distribution_type == 2:  # Exponential
                lambda_param = fdp.lambda_param if fdp.lambda_param else 1/mean_demand
                prediction = np.random.exponential(1/lambda_param)
                
            elif fdp.distribution_type == 3:  # Log-Normal
                mean_param = fdp.mean_param if fdp.mean_param else np.log(mean_demand)
                std_param = fdp.std_dev_param if fdp.std_dev_param else std_demand/mean_demand
                prediction = np.random.lognormal(mean_param, std_param)
                
            elif fdp.distribution_type == 4:  # Gamma
                shape = fdp.shape_param if fdp.shape_param else (mean_demand/std_demand)**2
                scale = fdp.scale_param if fdp.scale_param else std_demand**2/mean_demand
                prediction = np.random.gamma(shape, scale)
                
            elif fdp.distribution_type == 5:  # Uniform
                min_param = fdp.min_param if fdp.min_param else mean_demand - std_demand
                max_param = fdp.max_param if fdp.max_param else mean_demand + std_demand
                prediction = np.random.uniform(min_param, max_param)
                
            else:
                # Default to normal distribution
                prediction = np.random.normal(mean_demand, std_demand)
            
            # Add trend component
            trend_factor = 1 + (day_index * 0.001)  # Small daily growth
            prediction *= trend_factor
            
            # Ensure positive demand
            return max(0.1, float(prediction))
            
        except Exception as e:
            logger.error(f"Error generating demand prediction: {str(e)}")
            # Fallback to historical mean with some randomness
            demand_history = self._parse_demand_history(simulation_instance.demand_history)
            mean_demand = np.mean(demand_history)
            return max(0.1, mean_demand * (0.9 + random.random() * 0.2))
    
    
    def _get_output_variable(self, equation: Equation) -> Optional[str]:
        """Get the output variable from an equation"""
        try:
            if '=' in equation.expression:
                lhs = equation.expression.split('=')[0].strip()
                return lhs
            return None
        except:
            return None
    
    def _process_answers_optimized(
        self, answers: List[Dict], simulation_instance: Simulation
    ) -> Dict[str, float]:
        """Process questionary answers into variable dictionary with optimization"""
        variable_dict = {}
        nmd = int(simulation_instance.quantity_time)
        
        # Parse demand history once
        demand_history_str = simulation_instance.demand_history
        if isinstance(demand_history_str, str):
            try:
                demand_values = json.loads(demand_history_str)
            except:
                demand_values = self._parse_demand_history(demand_history_str)
        else:
            demand_values = demand_history_str
        
        # Process each answer
        for answer_data in answers:
            variable_name = answer_data.get('fk_question__fk_variable__initials')
            if not variable_name:
                continue
                
            answer_value = answer_data['answer']
            
            # Map answer values to corresponding variable names from variables_data.py
            variable_mapping = {
                'precio_actual': 'PVP',
                'demanda_historica': 'DH',
                'produccion_actual': 'QPL',
                'demanda_esperada': 'DE',
                'capacidad_inventario': 'CIP',
                'estacionalidad': 'ED',
                'costo_unitario_insumo': 'CUIP',
                'tiempo_entre_compras': 'TPC',
                'clientes_diarios': 'CPD',
                'numero_empleados': 'NEPP',
                'capacidad_produccion': 'CPROD',
                'sueldos_salarios': 'SE',
                'precio_competencia': 'PC',
                'costo_fijo_diario': 'CFD',
                'costo_transporte': 'CUTRANS',
                'gastos_marketing': 'GMM',
                'tiempo_reabastecimiento': 'TR',
                'insumos_por_producto': 'CINSP',
                'capacidad_almacenamiento': 'CMIPF',
                'tiempo_produccion_unitario': 'TPE',
                'cantidad_por_lote': 'CPPL',
                'stock_seguridad': 'SI',
                'dias_reabastecimiento': 'DPL',
                'tiempo_procesamiento_pedidos': 'TMP',
                'cantidad_transporte_viaje': 'CTPLV',
                'numero_proveedores': 'NPD',
                'consumo_diario_proveedor': 'CTL',
                'minutos_laborables': 'MLP',
                'cantidad_promedio_lote': 'CPL'
            }
            
            # Use mapping if available
            if variable_name in variable_mapping:
                variable_name = variable_mapping[variable_name]
            
            # Process the answer value
            if variable_name == "DH" or answer_value == demand_values:
                # Handle demand history - use mean
                if demand_values:
                    variable_dict["DH"] = round(np.mean(demand_values), 2)
                else:
                    variable_dict["DH"] = 0.0
            elif answer_value == "Sí":
                variable_dict[variable_name] = 1.0
            elif answer_value == "No":
                variable_dict[variable_name] = 0.0
            else:
                try:
                    # Clean and convert the value
                    if isinstance(answer_value, str):
                        answer_value = answer_value.replace(',', '').replace('$', '').replace('%', '')
                    variable_dict[variable_name] = float(answer_value)
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert {answer_value} to float for variable {variable_name}")
                    continue
        
        # Add calculated and default values
        variable_dict["NMD"] = float(nmd)
        variable_dict["MLP"] = 480.0  # 8 hours * 60 minutes default
        
        # Add any missing critical variables with defaults
        defaults = {
            'VPC': 30.0,  # Ventas por cliente
            'TCAE': 85.0,  # Total clientes atendidos en el día
            'QPL': 2500.0,  # Cantidad producida
            'CPPL': 500.0,  # Cantidad promedio por lote
            'CPL': 2500.0,  # Cantidad promedio producida por lote
        }
        
        for var, default_val in defaults.items():
            if var not in variable_dict:
                variable_dict[var] = default_val
        
        return variable_dict
    
    def _solve_equations_optimized(
        self, equations: List, variable_dict: Dict[str, float]
    ) -> Dict[str, float]:
        """Solve equations with caching and optimization"""
        endogenous_results = {}
        pending_equations = []
        
        # First pass: solve equations that can be solved immediately
        for equation in equations:
            result = self._try_solve_equation(equation, variable_dict)
            if result is not None:
                variables = self._get_equation_variables(equation)
                if variables:
                    endogenous_results[variables[0]] = result  # First variable is the output
                    variable_dict[variables[0]] = result  # Update dict for dependent equations
            else:
                pending_equations.append(equation)
        
        # Second pass: try to solve pending equations
        if pending_equations:
            self._solve_pending_equations_optimized(
                pending_equations, variable_dict, endogenous_results
            )
        
        return endogenous_results
    
    def _try_solve_equation(
        self, equation: Equation, variable_dict: Dict[str, float]
    ) -> Optional[float]:
        """Try to solve a single equation"""
        try:
            variables = self._get_equation_variables(equation)
            if not variables:
                return None
                
            expression = equation.expression
            
            # Handle special functions
            expression = expression.replace('random()', str(random.random()))
            
            # Parse equation
            if '=' in expression:
                lhs, rhs = expression.split('=', 1)
                lhs = lhs.strip()
                rhs = rhs.strip()
                
                # Remove summation symbol if present
                rhs = rhs.replace('∑', '')
                
                # Substitute known variables
                for var, value in variable_dict.items():
                    if var in rhs:
                        rhs = rhs.replace(var, str(value))
                
                # Check if we can evaluate the right side
                try:
                    # Create safe evaluation context
                    safe_dict = {
                        '__builtins__': {},
                        'random': random.random,
                        'min': min,
                        'max': max,
                        'abs': abs,
                        'round': round
                    }
                    
                    result = eval(rhs, safe_dict)
                    return float(result)
                except:
                    # Try symbolic solving if direct evaluation fails
                    try:
                        # Check if all variables in RHS are known
                        unknown_vars = []
                        for var in variables[1:]:  # Skip the first (output) variable
                            if var not in variable_dict and var != lhs:
                                unknown_vars.append(var)
                        
                        if not unknown_vars:
                            # All variables known, solve symbolically
                            symbol = symbols(lhs)
                            equation_expr = sp.sympify(rhs)
                            return float(equation_expr)
                    except:
                        pass
            
            return None
            
        except Exception as e:
            logger.debug(f"Could not solve equation {equation.id}: {e}")
            return None
    
    def _get_equation_variables(self, equation: Equation) -> List[str]:
        """Get variables used in an equation in order"""
        variables = []
        for var_attr in ['fk_variable1', 'fk_variable2', 'fk_variable3', 
                        'fk_variable4', 'fk_variable5']:
            var = getattr(equation, var_attr)
            if var is not None:
                variables.append(var.initials)
        return variables
    
    def _solve_pending_equations_optimized(
        self, pending_equations: List, variable_dict: Dict[str, float],
        endogenous_results: Dict[str, float]
    ) -> None:
        """Solve pending equations with iteration"""
        max_iterations = 10
        iteration = 0
        
        while pending_equations and iteration < max_iterations:
            iteration += 1
            newly_solved = []
            
            # Update variable dict with newly solved values
            combined_dict = {**variable_dict, **endogenous_results}
            
            for equation in pending_equations:
                result = self._try_solve_equation(equation, combined_dict)
                if result is not None:
                    variables = self._get_equation_variables(equation)
                    if variables:
                        endogenous_results[variables[0]] = result
                        combined_dict[variables[0]] = result
                        newly_solved.append(equation)
            
            # Remove solved equations
            pending_equations = [eq for eq in pending_equations if eq not in newly_solved]
            
            # If no progress, stop
            if not newly_solved:
                break
    
    def _bulk_save_results(
        self, simulation_instance: Simulation, results: List[Tuple[int, Dict]]
    ) -> None:
        """Bulk save simulation results for better performance"""
        result_objects = []
        
        # Sort results by day index
        results.sort(key=lambda x: x[0])
        
        # Parse demand history once
        demand_history_numeric = self._parse_demand_history(
            simulation_instance.demand_history
        )
        
        for day_index, day_data in results:
            endogenous_results = day_data['endogenous_results']
            variable_dict = day_data['variable_initials_dict']
            predicted_demand = day_data.get('predicted_demand', 0)
            
            # Use predicted demand as the main demand value
            demand_total = predicted_demand if predicted_demand > 0 else endogenous_results.get('DE', variable_dict.get('DH', 0))
            
            # Calculate standard deviation
            all_demands = demand_history_numeric + [demand_total]
            demand_std_dev = np.std(all_demands)
            
            # Serialize results
            serializable_results = {}
            for k, v in endogenous_results.items():
                try:
                    serializable_results[k] = float(v) if isinstance(v, (int, float, np.number)) else str(v)
                except:
                    serializable_results[k] = 0.0
            
            result_objects.append(
                ResultSimulation(
                    fk_simulation=simulation_instance,
                    demand_mean=demand_total,
                    demand_std_deviation=demand_std_dev,
                    date=simulation_instance.date_created + timedelta(days=day_index + 1),
                    variables=serializable_results,
                )
            )
            
            # Bulk create in batches
            if len(result_objects) >= self.batch_size:
                ResultSimulation.objects.bulk_create(result_objects)
                result_objects = []
        
        # Save remaining results
        if result_objects:
            ResultSimulation.objects.bulk_create(result_objects)
        
    def analyze_financial_results(self, simulation_id: int, totales_acumulativos: Dict[str, Dict]) -> Dict[str, Any]:
        """Analyze financial results with enhanced insights"""
        try:
            # Get simulation instance
            simulation = Simulation.objects.select_related(
                'fk_questionary_result__fk_questionary__fk_product__fk_business'
            ).get(id=simulation_id)
            
            # Get business instance
            business_instance = simulation.fk_questionary_result.fk_questionary.fk_product.fk_business
            
            # Get demand data from results
            results = ResultSimulation.objects.filter(
                fk_simulation_id=simulation_id,
                is_active=True
            ).order_by('date')
            
            if results.exists():
                # Use first and last result for comparison
                first_result = results.first()
                last_result = results.last()
                initial_demand = float(first_result.demand_mean)
                predicted_demand = float(last_result.demand_mean)
            else:
                # Fallback to demand history statistics
                demand_stats = simulation.get_demand_statistics()
                initial_demand = demand_stats['mean']
                predicted_demand = demand_stats['mean']  # Same as initial if no simulation run
            
            # Calculate metrics
            growth_rate = self._calculate_growth_rate(initial_demand, predicted_demand)
            error_permisible = self._calculate_error(initial_demand, predicted_demand)
            
            # Generate financial recommendations
            recommendations = []
            try:
                recommendations = self._generate_financial_recommendations_optimized(
                    business_instance, totales_acumulativos, simulation
                )
            except Exception as e:
                logger.warning(f"Could not generate recommendations: {str(e)}")
            
            # Calculate additional insights
            insights = self._calculate_additional_insights(
                totales_acumulativos, growth_rate, error_permisible
            )
            
            # Create simple objects for template compatibility
            class DemandData:
                def __init__(self, quantity):
                    self.quantity = quantity
            
            return {
                'demand_initial': DemandData(initial_demand),
                'demand_predicted': DemandData(predicted_demand),
                'growth_rate': growth_rate,
                'error_permisible': error_permisible,
                'financial_recommendations_to_show': recommendations,
                'insights': insights,
                # Additional data for debugging
                'has_results': results.exists(),
                'results_count': results.count(),
            }
            
        except Simulation.DoesNotExist:
            logger.error(f"Simulation {simulation_id} not found")
            raise
        except Exception as e:
            logger.error(f"Error analyzing financial results: {str(e)}")
            # Return safe defaults
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
    
    def _generate_financial_recommendations_optimized(
        self, business_instance: Business, totales_acumulativos: Dict[str, Dict],
        simulation_instance: Simulation
    ) -> List[Dict[str, Any]]:
        """Generate financial recommendations with batch processing"""
        # Get all recommendations at once
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
                            fk_finance_recommendation=recommendation,
                        )
                    )
        
        # Bulk create recommendations
        if recommendations_to_save:
            FinanceRecommendationSimulation.objects.bulk_create(recommendations_to_save)
        
        # Sort by severity
        recommendations_to_show.sort(key=lambda x: x['severity'], reverse=True)
        
        return recommendations_to_show
    
    def _calculate_severity(self, value: float, threshold: float) -> float:
        """Calculate severity score for recommendations"""
        if threshold == 0:
            return 0.0
        excess_percentage = ((value - threshold) / threshold) * 100
        return min(100, excess_percentage)
    
    def _calculate_additional_insights(
        self, totales_acumulativos: Dict[str, Dict], growth_rate: float, 
        error_permisible: float
    ) -> Dict[str, Any]:
        """Calculate additional business insights"""
        insights = {
            'efficiency_score': 0,
            'profitability_index': 0,
            'risk_level': 'low',
            'opportunities': []
        }
        
        # Calculate efficiency score
        if 'INGRESOS TOTALES' in totales_acumulativos and 'GASTOS TOTALES' in totales_acumulativos:
            income = totales_acumulativos['INGRESOS TOTALES']['total']
            expenses = totales_acumulativos['GASTOS TOTALES']['total']
            
            if income > 0:
                insights['efficiency_score'] = round((1 - expenses / income) * 100, 2)
                insights['profitability_index'] = round(income / expenses, 2)
        
        # Determine risk level
        if error_permisible > 15 or growth_rate < -10:
            insights['risk_level'] = 'high'
        elif error_permisible > 10 or growth_rate < 0:
            insights['risk_level'] = 'medium'
        
        # Identify opportunities
        if growth_rate > 20:
            insights['opportunities'].append('Expansión rápida detectada')
        if insights['efficiency_score'] > 30:
            insights['opportunities'].append('Alta eficiencia operativa')
        
        return insights
    
    def create_random_result_simulations(self, instance: Simulation) -> None:
        """Create random result simulations for testing (optimized version)"""
        current_date = instance.date_created
        
        # Parse demand history
        demand_history = self._parse_demand_history(instance.demand_history)
        
        # Pre-calculate statistics
        demand_mean_historical = np.mean(demand_history)
        demand_std_historical = np.std(demand_history)
        
        # Generate all results at once
        result_objects = []
        
        for day in range(int(instance.quantity_time)):
            current_date += timedelta(days=1)
            
            # Generate variables efficiently
            variables_means = self._generate_random_variables_optimized(
                demand_mean_historical, demand_std_historical
            )
            
            # Create result
            result_objects.append(
                ResultSimulation(
                    demand_mean=variables_means['DH'],
                    demand_std_deviation=random.normalvariate(5, 20),
                    date=current_date,
                    variables=variables_means,
                    fk_simulation=instance,
                    is_active=True
                )
            )
        
        # Bulk create all results
        ResultSimulation.objects.bulk_create(result_objects, batch_size=self.batch_size)
        
        # Create demand instances
        self._create_demand_instances_bulk(instance, demand_mean_historical)
    
    def _generate_random_variables_optimized(
        self, demand_mean: float, demand_std: float
    ) -> Dict[str, float]:
        """Generate random variables efficiently"""
        # Pre-defined variable configurations
        var_configs = {
            "DH": (demand_mean, demand_std),
            "CTR": (1000, 5000),
            "CTAI": (5000, 20000),
            "TPV": (1000, 5000),
            "TPPRO": (800, 4000),
            "DI": (50, 200),
            "VPC": (500, 1500),
            "IT": (5000, 20000),
            "GT": (3000, 12000),
            "TCA": (500, 2000),
            "NR": (0.1, 0.5),
            "GO": (1000, 5000),
            "GG": (1000, 5000),
            "CTTL": (1000, 5000),
            "CPP": (500, 2000),
            "CPV": (500, 2000),
            "CPI": (500, 2000),
            "CPMO": (500, 2000),
            "CUP": (500, 2000),
            "FU": (0.1, 0.5),
            "TG": (2000, 8000),
            "IB": (3000, 12000),
            "MB": (2000, 8000),
            "RI": (1000, 5000),
            "RTI": (1000, 5000),
            "RTC": (0.1, 0.5),
            "PM": (500, 1500),
            "PE": (1000, 5000),
            "HO": (10, 50),
            "CHO": (1000, 5000),
            "CA": (1000, 5000),
        }
        
        # Generate means efficiently
        return {
            var: max(0, np.mean([
                random.normalvariate(mean, std) for _ in range(10)
            ]))
            for var, (mean, std) in var_configs.items()
        }
    
    def _create_demand_instances_bulk(
        self, simulation_instance: Simulation, demand_mean: float
    ) -> None:
        """Create demand instances efficiently"""
        product = simulation_instance.fk_questionary_result.fk_questionary.fk_product
        
        demands_to_create = []
        
        # Initial demand
        if not Demand.objects.filter(
            fk_simulation=simulation_instance, is_predicted=False
        ).exists():
            demand_history = self._parse_demand_history(simulation_instance.demand_history)
            initial_demand = Demand(
                quantity=demand_history[0] if demand_history else demand_mean,
                is_predicted=False,
                fk_simulation=simulation_instance,
                fk_product=product,
                is_active=True
            )
            demands_to_create.append(initial_demand)
        
        # Predicted demand
        if not Demand.objects.filter(
            fk_simulation=simulation_instance, is_predicted=True
        ).exists():
            predicted_demand = Demand(
                quantity=demand_mean,
                is_predicted=True,
                fk_simulation=simulation_instance,
                fk_product=product,
                is_active=True,
                confidence_score=0.85
            )
            demands_to_create.append(predicted_demand)
        
        # Bulk create demands
        if demands_to_create:
            created_demands = Demand.objects.bulk_create(demands_to_create)
            
            # Create demand behavior if both demands exist
            if len(created_demands) == 2:
                DemandBehavior.objects.create(
                    current_demand=created_demands[0],
                    predicted_demand=created_demands[1],
                    is_active=True
                )
    
    # Additional utility methods
    
    def get_simulation_statistics(self, simulation_id: int) -> Dict[str, Any]:
        """Get comprehensive statistics for a simulation"""
        try:
            simulation = Simulation.objects.get(id=simulation_id)
            results = ResultSimulation.objects.filter(fk_simulation=simulation)
            
            if not results.exists():
                return {
                    'status': 'no_results',
                    'message': 'No se encontraron resultados para esta simulación'
                }
            
            # Extract demand values
            demand_values = [r.demand_mean for r in results]
            
            # Calculate statistics
            stats = {
                'total_days': results.count(),
                'demand': {
                    'mean': np.mean(demand_values),
                    'std': np.std(demand_values),
                    'min': np.min(demand_values),
                    'max': np.max(demand_values),
                    'median': np.median(demand_values),
                    'cv': np.std(demand_values) / np.mean(demand_values) if np.mean(demand_values) > 0 else 0
                },
                'variables': self._aggregate_variable_statistics(results),
                'trends': self._calculate_trends(demand_values),
                'status': 'success'
            }
            
            return stats
            
        except Simulation.DoesNotExist:
            return {
                'status': 'error',
                'message': 'Simulación no encontrada'
            }
        except Exception as e:
            logger.error(f"Error getting simulation statistics: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _aggregate_variable_statistics(self, results) -> Dict[str, Dict[str, float]]:
        """Aggregate statistics for all variables across simulation results"""
        variable_data = {}
        
        for result in results:
            for var_name, var_value in result.variables.items():
                if var_name not in variable_data:
                    variable_data[var_name] = []
                try:
                    variable_data[var_name].append(float(var_value))
                except (ValueError, TypeError):
                    continue
        
        # Calculate statistics for each variable
        variable_stats = {}
        for var_name, values in variable_data.items():
            if values:
                variable_stats[var_name] = {
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values),
                    'total': np.sum(values)
                }
        
        return variable_stats
    
    def _calculate_trends(self, values: List[float]) -> Dict[str, Any]:
        """Calculate trend information for a series of values"""
        if len(values) < 2:
            return {'trend': 'insufficient_data'}
        
        x = np.arange(len(values))
        
        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
        
        # Calculate percentage change
        pct_change = ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0
        
        return {
            'slope': slope,
            'intercept': intercept,
            'r_squared': r_value ** 2,
            'p_value': p_value,
            'direction': 'increasing' if slope > 0 else 'decreasing',
            'percentage_change': pct_change,
            'trend_strength': 'strong' if abs(r_value) > 0.8 else 'moderate' if abs(r_value) > 0.5 else 'weak'
        }
    
    def validate_simulation_results(self, simulation_id: int) -> Dict[str, Any]:
        """Validate simulation results for consistency and accuracy"""
        try:
            simulation = Simulation.objects.get(id=simulation_id)
            results = ResultSimulation.objects.filter(fk_simulation=simulation)
            
            validation_report = {
                'is_valid': True,
                'warnings': [],
                'errors': [],
                'statistics': {}
            }
            
            if not results.exists():
                validation_report['is_valid'] = False
                validation_report['errors'].append('No se encontraron resultados')
                return validation_report
            
            # Check for missing dates
            expected_dates = set()
            start_date = simulation.date_created
            for i in range(int(simulation.quantity_time)):
                expected_dates.add(start_date + timedelta(days=i))
            
            actual_dates = set(r.date for r in results)
            missing_dates = expected_dates - actual_dates
            
            if missing_dates:
                validation_report['warnings'].append(
                    f"Faltan resultados para {len(missing_dates)} días"
                )
            
            # Check for negative values in key variables
            for result in results:
                for var_name, var_value in result.variables.items():
                    try:
                        val = float(var_value)
                        if val < 0 and var_name not in ['DI', 'GT']:  # Some vars can be negative
                            validation_report['warnings'].append(
                                f"Valor negativo encontrado: {var_name}={val} en fecha {result.date}"
                            )
                    except:
                        continue
            
            # Check demand consistency
            demand_values = [r.demand_mean for r in results]
            if any(d <= 0 for d in demand_values):
                validation_report['errors'].append('Valores de demanda no válidos (≤ 0)')
                validation_report['is_valid'] = False
            
            # Add statistics
            validation_report['statistics'] = {
                'total_results': results.count(),
                'expected_results': int(simulation.quantity_time),
                'completeness': results.count() / int(simulation.quantity_time) * 100
            }
            
            return validation_report
            
        except Exception as e:
            logger.error(f"Error validating simulation: {str(e)}")
            return {
                'is_valid': False,
                'errors': [str(e)],
                'warnings': [],
                'statistics': {}
            }
    
    def export_simulation_data(self, simulation_id: int, format: str = 'csv') -> Any:
        """Export simulation data in various formats"""
        try:
            import pandas as pd
            from io import StringIO, BytesIO
            
            simulation = Simulation.objects.get(id=simulation_id)
            results = ResultSimulation.objects.filter(
                fk_simulation=simulation
            ).order_by('date')
            
            # Prepare data for export
            data = []
            for result in results:
                row = {
                    'date': result.date,
                    'demand_mean': result.demand_mean,
                    'demand_std': result.demand_std_deviation,
                }
                # Add all variables
                row.update(result.variables)
                data.append(row)
            
            df = pd.DataFrame(data)
            
            if format == 'csv':
                output = StringIO()
                df.to_csv(output, index=False)
                return output.getvalue()
            elif format == 'excel':
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, sheet_name='Simulation Results', index=False)
                return output.getvalue()
            elif format == 'json':
                return df.to_json(orient='records', date_format='iso')
            else:
                raise ValueError(f"Format {format} not supported")
                
        except Exception as e:
            logger.error(f"Error exporting simulation data: {str(e)}")
            raise

    def _bulk_save_results(
        self, simulation_instance: Simulation, results: List[Tuple[int, Dict]]
    ) -> None:
        """Bulk save simulation results for better performance"""
        result_objects = []
        
        # Sort results by day index
        results.sort(key=lambda x: x[0])
        
        # Parse demand history once
        demand_history_numeric = self._parse_demand_history(
            simulation_instance.demand_history
        )
        
        for day_index, day_data in results:
            endogenous_results = day_data['endogenous_results']
            variable_dict = day_data['variable_initials_dict']
            predicted_demand = day_data.get('predicted_demand', 0)
            
            # Use predicted demand as the main demand value
            demand_total = predicted_demand if predicted_demand > 0 else endogenous_results.get('DE', variable_dict.get('DH', 0))
            
            # Calculate standard deviation including new prediction
            all_demands = demand_history_numeric + [demand_total]
            demand_std_dev = np.std(all_demands)
            
            # Serialize results - ensure all values are serializable
            serializable_results = {}
            for k, v in endogenous_results.items():
                try:
                    serializable_results[k] = float(v) if isinstance(v, (int, float, np.number)) else str(v)
                except:
                    serializable_results[k] = str(v)
            
            result_objects.append(
                ResultSimulation(
                    fk_simulation=simulation_instance,
                    demand_mean=demand_total,
                    demand_std_deviation=demand_std_dev,
                    date=simulation_instance.date_created + timedelta(days=day_index + 1),
                    variables=serializable_results,
                )
            )
            
            # Bulk create in batches
            if len(result_objects) >= self.batch_size:
                ResultSimulation.objects.bulk_create(result_objects)
                result_objects = []
        
        # Save remaining results
        if result_objects:
            ResultSimulation.objects.bulk_create(result_objects)