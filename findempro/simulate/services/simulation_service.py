# services/simulation_service.py - VERSIÓN COMPLETA MEJORADA
import json
import logging
import random
import statistics
import re
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
            # Mapeo desde respuestas a iniciales de variables
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
        
        # Valores por defecto para variables críticas
        
        self.default_values = {
            'PVP': 15.50,
            'CPD': 85,
            'VPC': 30,
            'TCAE': 85,
            'SE': 48000,
            'CFD': 1800,
            'GMM': 3500,
            'CUIP': 8.20,
            'CPROD': 3000,
            'NEPP': 15,
            'CPPL': 500,
            'CPL': 2500,
            'QPL': 2500,
            'CUTRANS': 0.35,
            'CTPLV': 1500,
            'TPE': 45,
            'ED': 1.0,
            'PC': 15.80,
            'TPC': 2,
            'TR': 3,
            'CINSP': 1.05,
            'SI': 3000,
            'DPL': 3,
            'TMP': 1,
            'NPD': 3,
            'CTL': 2800,
            'MLP': 480,
            'DE': 2650,
            'DH': 2500,
            'CIP': 15000,
            'CMIPF': 20000,
            'II': 5000,
            'IPF': 1000,
            'PI': 3000,
            'UII': 2500,
            'PPL': 500,
            'TPPRO': 3000,
            'TPV': 2550,
            'DI': 100,
            'TCA': 2550,
            'NMD': 30
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
            
            # Get related instances
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
                demand_history=json.dumps(validated_data['demand_history']),
                fk_fdp=fk_fdp_instance,
                is_active=True
            )
            
            logger.info(f"Simulation {simulation_instance.id} created successfully")
            return simulation_instance
            
        except Exception as e:
            logger.error(f"Error creating simulation: {str(e)}")
            raise
    
    @transaction.atomic
    def execute_simulation(self, simulation_instance: Simulation) -> None:
        """Execute simulation with complete equation processing"""
        try:
            nmd = int(simulation_instance.quantity_time)
            logger.info(f"Starting simulation execution for {nmd} days")
            
            # Get all required data
            simulation_data = self._prepare_simulation_data(simulation_instance)
            
            # Process days sequentially
            results_to_save = []
            
            for day_index in range(nmd):
                try:
                    day_results = self._simulate_single_day_complete(
                        simulation_instance, simulation_data, day_index
                    )
                    results_to_save.append((day_index, day_results))
                    logger.info(f"Day {day_index + 1} completed with {len(day_results['endogenous_results'])} variables calculated")
                except Exception as e:
                    logger.error(f"Error simulating day {day_index}: {str(e)}")
                    continue
            
            # Bulk save results
            self._bulk_save_results(simulation_instance, results_to_save)
            
            logger.info(f"Simulation {simulation_instance.id} executed successfully")
            
        except Exception as e:
            logger.error(f"Error executing simulation {simulation_instance.id}: {str(e)}")
            raise
    
    def _simulate_single_day_complete(
        self, simulation_instance: Simulation, simulation_data: Dict[str, Any], 
        day_index: int
    ) -> Dict[str, Any]:
        """Simulate a single day with complete variable initialization and calculation"""
        
        # Initialize ALL variables with defaults and answers
        variable_dict = self._initialize_all_variables(
            simulation_data['answers'], 
            simulation_instance, 
            day_index
        )
        
        # Generate demand prediction
        predicted_demand = self._generate_demand_prediction(
            simulation_instance, variable_dict, day_index
        )
        
        # Update demand variables
        variable_dict['DE'] = predicted_demand
        variable_dict['DH'] = predicted_demand
        
        # Calculate all equations in proper order
        endogenous_results = self._calculate_all_equations(
            simulation_data['equations'], 
            variable_dict
        )
        
        # Ensure all variables are in results
        final_results = self._merge_results(variable_dict, endogenous_results)
        
        logger.debug(f"Day {day_index}: Calculated {len(final_results)} total variables")
        
        return {
            'endogenous_results': final_results,
            'variable_initials_dict': variable_dict,
            'predicted_demand': predicted_demand
        }
    
    def _initialize_all_variables(
        self, answers: List[Dict], simulation_instance: Simulation, day_index: int
    ) -> Dict[str, float]:
        """Initialize ALL variables with proper values"""
        
        # Start with default values
        variable_dict = self.default_values.copy()
        
        # Update NMD with actual simulation days
        variable_dict['NMD'] = float(simulation_instance.quantity_time)
        
        # Parse demand history
        demand_history = self._parse_demand_history(simulation_instance.demand_history)
        if demand_history:
            variable_dict['DH'] = float(np.mean(demand_history))
        
        # Process answers and update variables
        for answer_data in answers:
            var_initials = answer_data.get('fk_question__fk_variable__initials')
            answer_value = answer_data.get('answer')
            
            if not var_initials or answer_value is None:
                continue
            
            # Direct mapping (variable already has correct initials)
            if var_initials in variable_dict:
                try:
                    if var_initials == 'ED':  # Estacionalidad
                        variable_dict[var_initials] = 1.0 if answer_value == 'Sí' else 0.5
                    elif isinstance(answer_value, (list, tuple)):
                        variable_dict[var_initials] = float(np.mean(answer_value))
                    else:
                        # Clean string values
                        if isinstance(answer_value, str):
                            cleaned = answer_value.replace(',', '').replace('$', '').replace('%', '')
                            variable_dict[var_initials] = float(cleaned)
                        else:
                            variable_dict[var_initials] = float(answer_value)
                except Exception as e:
                    logger.warning(f"Could not process {var_initials}={answer_value}: {e}")
            
            # Check if it needs mapping
            elif var_initials in self.variable_mapping.values():
                # Find the key that maps to this variable
                for key, mapped_var in self.variable_mapping.items():
                    if mapped_var == var_initials:
                        try:
                            if isinstance(answer_value, str):
                                cleaned = answer_value.replace(',', '').replace('$', '').replace('%', '')
                                variable_dict[var_initials] = float(cleaned)
                            else:
                                variable_dict[var_initials] = float(answer_value)
                        except:
                            pass
                        break
        
        # Add calculated initial values
        variable_dict['DIA'] = float(day_index + 1)
        variable_dict['random'] = lambda: random.random()
        
        # Initialize state variables if not set
        if 'TCAE' not in variable_dict or variable_dict['TCAE'] == 0:
            variable_dict['TCAE'] = variable_dict['CPD'] * 0.95
        
        if 'VPC' not in variable_dict or variable_dict['VPC'] == 0:
            variable_dict['VPC'] = 30.0
        
        return variable_dict
    
    def _calculate_all_equations(
        self, equations: List, variable_dict: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate all equations in dependency order"""
        
        endogenous_results = {}
        
        # Define calculation order by area
        area_order = [
            'Ventas',
            'Producción',
            'Contabilidad',
            'Inventario Insumos',
            'Inventario Productos Finales',
            'Distribución',
            'Abastecimiento',
            'Marketing',
            'Competencia',
            'Recursos Humanos'
        ]
        
        # Group equations by area
        equations_by_area = {}
        for eq in equations:
            area_name = eq.fk_area.name if eq.fk_area else 'Other'
            if area_name not in equations_by_area:
                equations_by_area[area_name] = []
            equations_by_area[area_name].append(eq)
        
        # Process equations by area in order
        for area in area_order:
            if area in equations_by_area:
                for equation in equations_by_area[area]:
                    self._solve_single_equation(
                        equation, variable_dict, endogenous_results
                    )
        
        # Process any remaining areas
        for area, eqs in equations_by_area.items():
            if area not in area_order:
                for equation in eqs:
                    self._solve_single_equation(
                        equation, variable_dict, endogenous_results
                    )
        
        # Multiple passes for dependencies
        for iteration in range(3):
            initial_count = len(endogenous_results)
            
            for area in area_order:
                if area in equations_by_area:
                    for equation in equations_by_area[area]:
                        if self._get_output_variable(equation) not in endogenous_results:
                            self._solve_single_equation(
                                equation, variable_dict, endogenous_results
                            )
            
            # If no new equations solved, break
            if len(endogenous_results) == initial_count:
                break
        
        # Calculate critical missing variables manually
        self._calculate_missing_critical_variables(variable_dict, endogenous_results)
        
        return endogenous_results
    
    def _solve_single_equation(
        self, equation: Equation, variable_dict: Dict[str, float], 
        endogenous_results: Dict[str, float]
    ) -> None:
        """Solve a single equation and update results"""
        
        try:
            output_var = self._get_output_variable(equation)
            if not output_var or output_var in endogenous_results:
                return
            
            # Combine all known variables
            all_variables = {**variable_dict, **endogenous_results}
            
            # Parse expression
            expression = equation.expression
            if '=' not in expression:
                return
            
            lhs, rhs = expression.split('=', 1)
            lhs = lhs.strip()
            rhs = rhs.strip()
            
            # Handle special functions in RHS
            rhs = self._preprocess_expression(rhs)
            
            # Try to evaluate
            result = self._evaluate_expression(rhs, all_variables)
            
            if result is not None:
                endogenous_results[output_var] = result
                variable_dict[output_var] = result
                logger.debug(f"Calculated {output_var} = {result}")
        
        except Exception as e:
            logger.debug(f"Could not solve equation {equation.expression}: {e}")
    
    def _preprocess_expression(self, expression: str) -> str:
        """Preprocess expression to handle special cases"""
        
        # Remove summation symbol
        expression = expression.replace('∑', '')
        
        # Replace random() with actual value
        expression = expression.replace('random()', str(random.random()))
        
        # Handle max/min functions - ensure they're properly formatted
        expression = re.sub(r'max\s*\(', 'max(', expression)
        expression = re.sub(r'min\s*\(', 'min(', expression)
        
        return expression
    
    def _evaluate_expression(self, expression: str, variables: Dict[str, float]) -> Optional[float]:
        """Safely evaluate mathematical expression"""
        
        try:
            # Replace variables with values
            for var, val in sorted(variables.items(), key=lambda x: len(x[0]), reverse=True):
                if var in expression:
                    # Use word boundaries to avoid partial replacements
                    pattern = r'\b' + re.escape(var) + r'\b'
                    expression = re.sub(pattern, str(val), expression)
            
            # Safe evaluation context
            safe_dict = {
                '__builtins__': {},
                'max': max,
                'min': min,
                'abs': abs,
                'round': round,
                'pow': pow,
                'sum': sum,
            }
            
            # Evaluate
            result = eval(expression, safe_dict)
            return float(result)
            
        except ZeroDivisionError:
            return 0.0
        except Exception as e:
            logger.debug(f"Could not evaluate expression '{expression}': {e}")
            return None
    
    def _calculate_missing_critical_variables(
        self, variable_dict: Dict[str, float], 
        endogenous_results: Dict[str, float]
    ) -> None:
        """Calculate critical variables that might be missing"""
        
        # Ensure TCAE is calculated
        if 'TCAE' not in endogenous_results:
            endogenous_results['TCAE'] = variable_dict.get('CPD', 85) * 0.95
        
        # Calculate TPV if missing
        if 'TPV' not in endogenous_results:
            tcae = endogenous_results.get('TCAE', variable_dict.get('TCAE', 85))
            vpc = variable_dict.get('VPC', 30)
            endogenous_results['TPV'] = tcae * vpc
        
        # Calculate IT if missing
        if 'IT' not in endogenous_results:
            tpv = endogenous_results.get('TPV', 2550)
            pvp = variable_dict.get('PVP', 15.50)
            endogenous_results['IT'] = tpv * pvp
        
        # Calculate CTAI if missing
        if 'CTAI' not in endogenous_results:
            cuip = variable_dict.get('CUIP', 8.20)
            tppro = endogenous_results.get('TPPRO', variable_dict.get('CPROD', 3000))
            endogenous_results['CTAI'] = cuip * tppro
        
        # Calculate GO if missing
        if 'GO' not in endogenous_results:
            cfd = variable_dict.get('CFD', 1800)
            se_daily = variable_dict.get('SE', 48000) / 30
            ctai = endogenous_results.get('CTAI', 24600)
            endogenous_results['GO'] = cfd + se_daily + ctai
        
        # Calculate GG if missing
        if 'GG' not in endogenous_results:
            go = endogenous_results.get('GO', 28000)
            gmm_daily = variable_dict.get('GMM', 3500) / 30
            endogenous_results['GG'] = go + gmm_daily
        
        # Calculate TG if missing
        if 'TG' not in endogenous_results:
            go = endogenous_results.get('GO', 28000)
            gg = endogenous_results.get('GG', 28116)
            endogenous_results['TG'] = go + gg
        
        # Calculate GT if missing
        if 'GT' not in endogenous_results:
            it = endogenous_results.get('IT', 39525)
            tg = endogenous_results.get('TG', 56116)
            endogenous_results['GT'] = it - tg
        
        # Calculate other important metrics
        if 'MB' not in endogenous_results and 'IT' in endogenous_results:
            it = endogenous_results['IT']
            gt = endogenous_results.get('GT', 0)
            if it > 0:
                endogenous_results['MB'] = gt / it
        
        if 'NR' not in endogenous_results and 'IT' in endogenous_results:
            it = endogenous_results['IT']
            gt = endogenous_results.get('GT', 0)
            if it > 0:
                endogenous_results['NR'] = gt / it
        
        if 'PE' not in endogenous_results:
            tpv = endogenous_results.get('TPV', 2550)
            nepp = variable_dict.get('NEPP', 15)
            if nepp > 0:
                endogenous_results['PE'] = tpv / nepp
        
        if 'PM' not in endogenous_results:
            tpv = endogenous_results.get('TPV', 2550)
            dh = variable_dict.get('DH', 2500)
            if dh > 0:
                endogenous_results['PM'] = tpv / dh
        
        if 'FU' not in endogenous_results:
            tpv = endogenous_results.get('TPV', 2550)
            cprod = variable_dict.get('CPROD', 3000)
            if cprod > 0:
                endogenous_results['FU'] = min(tpv / cprod, 1.0)
        
        if 'DI' not in endogenous_results:
            de = variable_dict.get('DE', 2650)
            tpv = endogenous_results.get('TPV', 2550)
            endogenous_results['DI'] = max(0, de - tpv)
        
        # Ensure all variables have reasonable values
        for var in ['TPPRO', 'IPF', 'II', 'RTI', 'CA', 'CTTL']:
            if var not in endogenous_results:
                endogenous_results[var] = 0.0
    
    def _merge_results(
        self, variable_dict: Dict[str, float], 
        endogenous_results: Dict[str, float]
    ) -> Dict[str, float]:
        """Merge all results ensuring completeness"""
        
        # Start with endogenous results
        final_results = endogenous_results.copy()
        
        # Add important variables from variable_dict if not in results
        important_vars = [
            'DE', 'DH', 'PVP', 'CPD', 'NEPP', 'SE', 'CFD', 'GMM',
            'CUIP', 'CPROD', 'PC', 'ED', 'TPC', 'TR', 'MLP', 'NMD'
        ]
        
        for var in important_vars:
            if var not in final_results and var in variable_dict:
                final_results[var] = variable_dict[var]
        
        return final_results
    
    def _generate_demand_prediction(
        self, simulation_instance: Simulation, variable_dict: Dict[str, float], 
        day_index: int
    ) -> float:
        """Generate demand prediction using the selected FDP"""
        try:
            fdp = simulation_instance.fk_fdp
            demand_history = self._parse_demand_history(simulation_instance.demand_history)
            
            # Calculate base statistics
            mean_demand = np.mean(demand_history) if demand_history else variable_dict.get('DH', 2500)
            std_demand = np.std(demand_history) if demand_history else mean_demand * 0.1
            
            # Add seasonality factor
            seasonality = variable_dict.get('ED', 1.0)
            
            # Generate prediction based on distribution type
            if fdp.distribution_type == 1:  # Normal
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
            
            # Apply seasonality
            prediction *= seasonality
            
            # Add trend component
            trend_factor = 1 + (day_index * 0.002)  # 0.2% daily growth
            prediction *= trend_factor
            
            # Ensure positive demand
            return max(1.0, float(prediction))
            
        except Exception as e:
            logger.error(f"Error generating demand prediction: {str(e)}")
            # Fallback to mean with randomness
            demand_history = self._parse_demand_history(simulation_instance.demand_history)
            mean_demand = np.mean(demand_history) if demand_history else 2500
            return max(1.0, mean_demand * (0.9 + random.random() * 0.2))
    
    def _get_output_variable(self, equation: Equation) -> Optional[str]:
        """Get the output variable from an equation"""
        try:
            if hasattr(equation, 'expression') and '=' in equation.expression:
                lhs = equation.expression.split('=')[0].strip()
                return lhs
            return None
        except:
            return None
    
    def _parse_demand_history(self, demand_history: Any) -> List[float]:
        """Parse demand history string to list of floats"""
        try:
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
    
    def _prepare_simulation_data(self, simulation_instance: Simulation) -> Dict[str, Any]:
        """Prepare all simulation data with optimized queries"""
        product = simulation_instance.fk_questionary_result.fk_questionary.fk_product
        
        areas = Area.objects.filter(
            is_active=True,
            fk_product=product
        ).order_by('id')
        
        equations = Equation.objects.filter(
            is_active=True,
            fk_area__fk_product=product
        ).select_related(
            'fk_variable1', 'fk_variable2', 'fk_variable3',
            'fk_variable4', 'fk_variable5', 'fk_area'
        ).order_by('fk_area__name')
        
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
    
    def _bulk_save_results(
        self, simulation_instance: Simulation, results: List[Tuple[int, Dict]]
    ) -> None:
        """Bulk save simulation results"""
        result_objects = []
        
        results.sort(key=lambda x: x[0])
        
        demand_history_numeric = self._parse_demand_history(
            simulation_instance.demand_history
        )
        
        for day_index, day_data in results:
            endogenous_results = day_data['endogenous_results']
            predicted_demand = day_data.get('predicted_demand', 0)
            
            demand_total = predicted_demand if predicted_demand > 0 else endogenous_results.get('DE', 2500)
            
            all_demands = demand_history_numeric + [demand_total]
            demand_std_dev = np.std(all_demands)
            
            # Ensure all values are serializable
            serializable_results = {}
            for k, v in endogenous_results.items():
                try:
                    serializable_results[k] = float(v) if isinstance(v, (int, float, np.number)) else 0.0
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
            
            if len(result_objects) >= self.batch_size:
                ResultSimulation.objects.bulk_create(result_objects)
                result_objects = []
        
        if result_objects:
            ResultSimulation.objects.bulk_create(result_objects)
    
    # Mantener los otros métodos existentes
    def analyze_financial_results(self, simulation_id: int, totales_acumulativos: Dict[str, Dict]) -> Dict[str, Any]:
        """Analyze financial results with enhanced insights"""
        try:
            simulation = Simulation.objects.select_related(
                'fk_questionary_result__fk_questionary__fk_product__fk_business'
            ).get(id=simulation_id)
            
            business_instance = simulation.fk_questionary_result.fk_questionary.fk_product.fk_business
            
            results = ResultSimulation.objects.filter(
                fk_simulation_id=simulation_id,
                is_active=True
            ).order_by('date')
            
            if results.exists():
                first_result = results.first()
                last_result = results.last()
                initial_demand = float(first_result.demand_mean)
                predicted_demand = float(last_result.demand_mean)
            else:
                demand_stats = simulation.get_demand_statistics()
                initial_demand = demand_stats['mean']
                predicted_demand = demand_stats['mean']
            
            growth_rate = self._calculate_growth_rate(initial_demand, predicted_demand)
            error_permisible = self._calculate_error(initial_demand, predicted_demand)
            
            recommendations = []
            try:
                recommendations = self._generate_financial_recommendations_optimized(
                    business_instance, totales_acumulativos, simulation
                )
            except Exception as e:
                logger.warning(f"Could not generate recommendations: {str(e)}")
            
            insights = self._calculate_additional_insights(
                totales_acumulativos, growth_rate, error_permisible
            )
            
            class DemandData:
                def __init__(self, quantity):
                    self.quantity = quantity
            
            return {
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
            raise
        except Exception as e:
            logger.error(f"Error analyzing financial results: {str(e)}")
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
                        )
                    )
        
        if recommendations_to_save:
            FinanceRecommendationSimulation.objects.bulk_create(recommendations_to_save)
        
        recommendations_to_show.sort(key=lambda x: x['severity'], reverse=True)
        
        return recommendations_to_show
    
    def _calculate_severity(self, value: float, threshold: float) -> float:
        if threshold == 0:
            return 0.0
        value = float(value)
        threshold = float(threshold)
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
        
        if 'INGRESOS TOTALES' in totales_acumulativos and 'GASTOS TOTALES' in totales_acumulativos:
            income = totales_acumulativos['INGRESOS TOTALES']['total']
            expenses = totales_acumulativos['GASTOS TOTALES']['total']
            
            if income > 0:
                insights['efficiency_score'] = round((1 - expenses / income) * 100, 2)
                insights['profitability_index'] = round(income / expenses, 2)
        
        if error_permisible > 15 or growth_rate < -10:
            insights['risk_level'] = 'high'
        elif error_permisible > 10 or growth_rate < 0:
            insights['risk_level'] = 'medium'
        
        if growth_rate > 20:
            insights['opportunities'].append('Expansión rápida detectada')
        if insights['efficiency_score'] > 30:
            insights['opportunities'].append('Alta eficiencia operativa')
        
        return insights