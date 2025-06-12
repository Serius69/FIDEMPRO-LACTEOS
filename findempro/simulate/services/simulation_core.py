# services/simulation_core.py
import logging
import random
import json
import re
import numpy as np
from datetime import timedelta
from typing import Dict, Any

from django.db import transaction
from django.shortcuts import get_object_or_404

from ..models import (
    Simulation, ResultSimulation, ProbabilisticDensityFunction
)
from ..validators.simulation_validators import SimulationValidator
from ..utils.data_parsers import DataParser
from product.models import Area
from questionary.models import Answer, QuestionaryResult
from variable.models import Variable, Equation

logger = logging.getLogger(__name__)

class SimulationCore:
    def __init__(self):
        self.validator = SimulationValidator()
        self.cache_timeout = 3600
        self.batch_size = 100
        
        # Mapeo mejorado desde respuestas del cuestionario a variables
        self.question_to_variable_mapping = {
            # Mapeo desde textos de preguntas a iniciales de variables
            'precio_actual': 'PVP',
            'precio_venta': 'PVP',
            'precio_producto': 'PVP',
            'precio de venta': 'PVP',
            'demanda_historica': 'DH',
            'demanda_promedio': 'DH',
            'produccion_actual': 'QPL',
            'cantidad_produccion': 'QPL',
            'producción': 'CPROD',
            'demanda_esperada': 'DE',
            'capacidad_inventario': 'CIP',
            'estacionalidad': 'ED',
            'costo_unitario_insumo': 'CUIP',
            'costo_insumos': 'CUIP',
            'costo unitario': 'CUIP',
            'tiempo_entre_compras': 'TPC',
            'clientes_diarios': 'CPD',
            'clientes_por_dia': 'CPD',
            'clientes por día': 'CPD',
            'numero_empleados': 'NEPP',
            'empleados': 'NEPP',
            'número de empleados': 'NEPP',
            'capacidad_produccion': 'CPROD',
            'capacidad de producción': 'CPROD',
            'sueldos_salarios': 'SE',
            'salarios': 'SE',
            'precio_competencia': 'PC',
            'costo_fijo_diario': 'CFD',
            'costos_fijos': 'CFD',
            'costos fijos': 'CFD',
            'costo_transporte': 'CUTRANS',
            'gastos_marketing': 'GMM',
            'marketing': 'GMM',
            'gastos de marketing': 'GMM',
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
        
        # Función para obtener defaults según producto
        def get_product_defaults(product_type):
            """Get default values based on product type"""
            
            # Base defaults that apply to all products
            base = {
                'ED': 1.0,  # Seasonality factor
                'NMD': 30,  # Number of days
                'TPC': 2,   # Time between purchases
                'TR': 3,    # Restocking time
                'TMP': 1,   # Order processing time
                'NPD': 3,   # Number of suppliers
            }
            
            # Product-specific defaults
            product_defaults = {
                'MILK': {  # Leche
                    'PVP': 1.50,      # Precio venta
                    'CPD': 200,       # Clientes por día 
                    'VPC': 2,         # Ventas por cliente
                    'CUIP': 0.80,     # Costo unitario insumo
                    'CPROD': 5000,    # Capacidad producción
                    'NEPP': 10,       # Número empleados
                    'SE': 35000,      # Sueldos
                    'CFD': 1200,      # Costos fijos
                    'GMM': 2500,      # Marketing
                    'DH': 4800,       # Demanda histórica
                    'DE': 5000,       # Demanda esperada
                },
                'CHEESE': {  # Queso
                    'PVP': 4.50,
                    'CPD': 150,
                    'VPC': 3,
                    'CUIP': 2.20,
                    'CPROD': 3000,
                    'NEPP': 12,
                    'SE': 40000,
                    'CFD': 1500,
                    'GMM': 3000,
                    'DH': 2800,
                    'DE': 3000,
                },
                'YOGURT': {  # Yogurt
                    'PVP': 2.50,
                    'CPD': 180,
                    'VPC': 4,
                    'CUIP': 1.20,
                    'CPROD': 4000,
                    'NEPP': 8,
                    'SE': 30000,
                    'CFD': 1000,
                    'GMM': 2000,
                    'DH': 3500,
                    'DE': 3800,
                },
                'DEFAULT': {  # Default values if product type not found
                    'PVP': 15.50,
                    'CPD': 85,
                    'VPC': 30,
                    'CUIP': 8.20,
                    'CPROD': 3000,
                    'NEPP': 15,
                    'SE': 48000,
                    'CFD': 1800,
                    'GMM': 3500,
                    'DH': 2500,
                    'DE': 2650,
                }
            }
            
            # Get specific defaults or use DEFAULT if not found
            specific = product_defaults.get(product_type, product_defaults['DEFAULT'])
            
            # Merge base with specific defaults
            return {**base, **specific}
            
        # Store the function to get defaults based on product
        self.get_product_defaults = get_product_defaults
        # Initialize with empty defaults
        self.default_values = {}

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

    def _prepare_simulation_data(self, simulation_instance):
        """Prepare all simulation data with optimized queries"""
        product = simulation_instance.fk_questionary_result.fk_questionary.fk_product
        
        # Determine product type for defaults
        product_type = 'DEFAULT'
        product_name_lower = product.name.lower()
        if 'leche' in product_name_lower or 'milk' in product_name_lower:
            product_type = 'MILK'
        elif 'queso' in product_name_lower or 'cheese' in product_name_lower:
            product_type = 'CHEESE'
        elif 'yogur' in product_name_lower or 'yogurt' in product_name_lower:
            product_type = 'YOGURT'
        
        # Update defaults based on product type
        self.default_values = self.get_product_defaults(product_type)
        logger.info(f"Using product type: {product_type}")
        
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
        
        # Get complete answer data including question text and variable mapping
        answers = Answer.objects.filter(
            fk_questionary_result=simulation_instance.fk_questionary_result
        ).select_related(
            'fk_question__fk_variable'
        ).values(
            'fk_question_id', 
            'fk_question__fk_variable__initials', 
            'fk_question__question',  # Get full question text
            'answer'
        )
        
        logger.info(f"Loaded {len(list(answers))} answers from questionnaire")
        
        return {
            'areas': list(areas),
            'equations': list(equations),
            'variables': {v['initials']: v for v in variables},
            'answers': list(answers),
            'product': product,
            'product_type': product_type
        }

    def _simulate_single_day_complete(self, simulation_instance, simulation_data, day_index):
        """Simulate a single day with complete variable initialization and calculation"""
        
        # Initialize ALL variables with REAL data from questionnaire
        variable_dict = self._initialize_variables_from_questionnaire(
            simulation_data['answers'], 
            simulation_instance, 
            day_index
        )
        
        # Log what we actually loaded
        logger.info(f"Day {day_index}: Loaded {len(variable_dict)} variables from questionnaire")
        
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

    def _initialize_variables_from_questionnaire(self, answers, simulation_instance, day_index):
        """Initialize variables PRIMARILY from questionnaire data, defaults as fallback"""
        
        # Start with empty dict - NO defaults initially
        variable_dict = {}
        
        # Add only essential system variables
        variable_dict['NMD'] = float(simulation_instance.quantity_time)
        variable_dict['DIA'] = float(day_index + 1)
        variable_dict['random'] = lambda: random.random()
        
        # Parse demand history first
        demand_history = self._parse_demand_history(simulation_instance.demand_history)
        if demand_history:
            variable_dict['DH'] = float(np.mean(demand_history))
            logger.info(f"Loaded demand history average: {variable_dict['DH']}")
        
        # Process ALL answers from questionnaire
        questionnaire_values_loaded = 0
        
        logger.info(f"Processing {len(answers)} answers from questionnaire...")
        
        for answer_data in answers:
            var_initials = answer_data.get('fk_question__fk_variable__initials')
            answer_value = answer_data.get('answer')
            question_text = answer_data.get('fk_question__question', '')
            
            if not answer_value:
                continue
            
            logger.debug(f"Processing answer: {var_initials} = {answer_value} (question: {question_text[:50]}...)")
            
            # Method 1: Direct variable mapping (variable already has correct initials)
            if var_initials:
                processed_value = self._process_answer_value(answer_value, var_initials)
                if processed_value is not None:
                    variable_dict[var_initials] = processed_value
                    questionnaire_values_loaded += 1
                    logger.info(f"LOADED from questionnaire: {var_initials} = {processed_value}")
                    continue
            
            # Method 2: Text-based mapping from question content
            question_lower = question_text.lower() if question_text else ''
            mapped = False
            for key_phrase, mapped_var in self.question_to_variable_mapping.items():
                if key_phrase in question_lower:
                    processed_value = self._process_answer_value(answer_value, mapped_var)
                    if processed_value is not None:
                        variable_dict[mapped_var] = processed_value
                        questionnaire_values_loaded += 1
                        logger.info(f"MAPPED from questionnaire: {mapped_var} = {processed_value} (from '{key_phrase}')")
                        mapped = True
                        break
            
            # Method 3: Try to extract variable from question text directly
            if not mapped and not var_initials:
                # Look for specific patterns in questions
                if 'precio' in question_lower and 'venta' in question_lower:
                    processed_value = self._process_answer_value(answer_value, 'PVP')
                    if processed_value is not None:
                        variable_dict['PVP'] = processed_value
                        questionnaire_values_loaded += 1
                        logger.info(f"PATTERN MATCHED: PVP = {processed_value}")
                elif 'clientes' in question_lower and ('día' in question_lower or 'diario' in question_lower):
                    processed_value = self._process_answer_value(answer_value, 'CPD')
                    if processed_value is not None:
                        variable_dict['CPD'] = processed_value
                        questionnaire_values_loaded += 1
                        logger.info(f"PATTERN MATCHED: CPD = {processed_value}")
                elif 'empleados' in question_lower:
                    processed_value = self._process_answer_value(answer_value, 'NEPP')
                    if processed_value is not None:
                        variable_dict['NEPP'] = processed_value
                        questionnaire_values_loaded += 1
                        logger.info(f"PATTERN MATCHED: NEPP = {processed_value}")
        
        logger.info(f"Successfully loaded {questionnaire_values_loaded} values from questionnaire")
        
        # Now add defaults ONLY for missing essential variables
        essential_missing = []
        for var, default_val in self.default_values.items():
            if var not in variable_dict:
                variable_dict[var] = default_val
                essential_missing.append(var)
        
        if essential_missing:
            logger.warning(f"Used defaults for missing variables: {essential_missing[:10]}...")
        
        # Special calculations for derived variables
        self._calculate_derived_variables(variable_dict)
        
        return variable_dict

    def _process_answer_value(self, answer_value, variable_name):
        """Process and clean answer values from questionnaire"""
        try:
            # Handle special cases
            if variable_name == 'ED':  # Estacionalidad
                if isinstance(answer_value, str):
                    return 1.0 if answer_value.lower() in ['sí', 'si', 'yes', 'true'] else 0.5
                return float(answer_value) if answer_value else 1.0
            
            # Handle list/array values
            if isinstance(answer_value, (list, tuple)):
                if len(answer_value) > 0:
                    return float(np.mean([float(x) for x in answer_value if x is not None]))
                return None
            
            # Handle string values
            if isinstance(answer_value, str):
                # Remove common formatting
                cleaned = answer_value.replace(',', '').replace('$', '').replace('%', '').replace(' ', '')
                cleaned = cleaned.replace('Bs', '').replace('bs', '').replace('L', '').replace('litros', '')
                
                # Handle empty strings
                if not cleaned:
                    return None
                
                # Handle boolean-like strings
                if cleaned.lower() in ['sí', 'si', 'yes', 'true']:
                    return 1.0
                elif cleaned.lower() in ['no', 'false']:
                    return 0.0
                
                # Try to convert to float
                try:
                    return float(cleaned)
                except ValueError:
                    # Try to extract number from string
                    import re
                    numbers = re.findall(r'[-+]?\d*\.?\d+', answer_value)
                    if numbers:
                        return float(numbers[0])
                    logger.warning(f"Could not convert string '{answer_value}' to number for {variable_name}")
                    return None
            
            # Handle numeric values
            if isinstance(answer_value, (int, float)):
                return float(answer_value)
            
            logger.warning(f"Unknown answer type {type(answer_value)} for {variable_name}: {answer_value}")
            return None
            
        except Exception as e:
            logger.error(f"Error processing answer value {answer_value} for {variable_name}: {e}")
            return None

    def _calculate_derived_variables(self, variable_dict):
        """Calculate important derived variables"""
        
        # Calculate TCAE if not set (Total Clientes Atendidos Efectivamente)
        if 'TCAE' not in variable_dict or variable_dict['TCAE'] == 0:
            cpd = variable_dict.get('CPD', 85)
            variable_dict['TCAE'] = cpd * 0.95  # 95% of daily clients served effectively
            logger.info(f"Calculated TCAE = {variable_dict['TCAE']} (from CPD = {cpd})")
        
        # Calculate VPC if not set (Ventas Por Cliente)
        if 'VPC' not in variable_dict or variable_dict['VPC'] == 0:
            pvp = variable_dict.get('PVP', 15.50)
            # Better calculation based on product type
            if pvp < 2:  # Likely milk
                variable_dict['VPC'] = 2
            elif pvp < 3:  # Likely yogurt
                variable_dict['VPC'] = 4
            elif pvp < 5:  # Likely cheese
                variable_dict['VPC'] = 3
            else:  # Default
                variable_dict['VPC'] = 30
            logger.info(f"Calculated VPC = {variable_dict['VPC']} (from PVP = {pvp})")

    def _calculate_all_equations(self, equations, variable_dict):
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
                logger.debug(f"Processing {len(equations_by_area[area])} equations for area: {area}")
                for equation in equations_by_area[area]:
                    self._solve_single_equation(
                        equation, variable_dict, endogenous_results
                    )
        
        # Process any remaining areas
        for area, eqs in equations_by_area.items():
            if area not in area_order:
                logger.debug(f"Processing {len(eqs)} equations for remaining area: {area}")
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
        
        logger.info(f"Calculated {len(endogenous_results)} endogenous variables")
        
        return endogenous_results

    def _solve_single_equation(self, equation, variable_dict, endogenous_results):
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

    def _preprocess_expression(self, expression):
        """Preprocess expression to handle special cases"""
        
        # Remove summation symbol
        expression = expression.replace('∑', '')
        
        # Replace random() with actual value
        expression = expression.replace('random()', str(random.random()))
        
        # Handle max/min functions - ensure they're properly formatted
        expression = re.sub(r'max\s*\(', 'max(', expression)
        expression = re.sub(r'min\s*\(', 'min(', expression)
        
        return expression

    def _evaluate_expression(self, expression, variables):
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

    def _calculate_missing_critical_variables(self, variable_dict, endogenous_results):
        """Calculate critical variables that might be missing using REAL questionnaire data"""
        
        # Use real values from questionnaire instead of hardcoded defaults
        cpd = variable_dict.get('CPD', 85)
        pvp = variable_dict.get('PVP', 15.50)
        vpc = variable_dict.get('VPC', 30)
        cuip = variable_dict.get('CUIP', 8.20)
        cprod = variable_dict.get('CPROD', 3000)
        cfd = variable_dict.get('CFD', 1800)
        se = variable_dict.get('SE', 48000)
        gmm = variable_dict.get('GMM', 3500)
        nepp = variable_dict.get('NEPP', 15)
        
        # Ensure TCAE is calculated
        if 'TCAE' not in endogenous_results:
            endogenous_results['TCAE'] = variable_dict.get('TCAE', cpd * 0.95)
        
        # Calculate TPV if missing
        if 'TPV' not in endogenous_results:
            tcae = endogenous_results.get('TCAE', variable_dict.get('TCAE', cpd * 0.95))
            endogenous_results['TPV'] = tcae * vpc
        
        # Calculate IT if missing
        if 'IT' not in endogenous_results:
            tpv = endogenous_results.get('TPV', 2550)
            endogenous_results['IT'] = tpv * pvp
        
        # Calculate CTAI if missing
        if 'CTAI' not in endogenous_results:
            tppro = endogenous_results.get('TPPRO', variable_dict.get('CPROD', cprod))
            endogenous_results['CTAI'] = cuip * tppro
        
        # Calculate GO if missing
        if 'GO' not in endogenous_results:
            se_daily = se / 30
            ctai = endogenous_results.get('CTAI', cuip * cprod)
            endogenous_results['GO'] = cfd + se_daily + ctai
        
        # Calculate GG if missing
        if 'GG' not in endogenous_results:
            go = endogenous_results.get('GO', 28000)
            gmm_daily = gmm / 30
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
        
        # Calculate other important metrics using real data
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
            if nepp > 0:endogenous_results['PE'] = tpv / nepp
       
        if 'PM' not in endogenous_results:
            tpv = endogenous_results.get('TPV', 2550)
            dh = variable_dict.get('DH', 2500)
            if dh > 0:
                endogenous_results['PM'] = tpv / dh
        
        if 'FU' not in endogenous_results:
            tpv = endogenous_results.get('TPV', 2550)
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

    def _merge_results(self, variable_dict, endogenous_results):
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

    def _generate_demand_prediction(self, simulation_instance, variable_dict, day_index):
        """Generate demand prediction using the selected FDP with continuity from historical data"""
        try:
            fdp = simulation_instance.fk_fdp
            demand_history = self._parse_demand_history(simulation_instance.demand_history)
            
            # Calculate base statistics from REAL data
            if demand_history and len(demand_history) > 0:
                mean_demand = np.mean(demand_history)
                std_demand = np.std(demand_history)
                
                # Get last historical value for continuity
                last_historical_value = demand_history[-1]
                
                # Calculate trend from historical data
                if len(demand_history) > 1:
                    x = np.arange(len(demand_history))
                    z = np.polyfit(x, demand_history, 1)
                    historical_trend = z[0]  # Slope of historical trend
                else:
                    historical_trend = 0
            else:
                mean_demand = variable_dict.get('DH', 2500)
                std_demand = mean_demand * 0.1
                last_historical_value = mean_demand
                historical_trend = 0
            
            # Add seasonality factor from questionnaire
            seasonality = variable_dict.get('ED', 1.0)
            
            # Generate prediction based on distribution type
            if fdp.distribution_type == 1:  # Normal
                mean_param = fdp.mean_param if fdp.mean_param else mean_demand
                std_param = fdp.std_dev_param if fdp.std_dev_param else std_demand
                base_prediction = np.random.normal(mean_param, std_param)
                
            elif fdp.distribution_type == 2:  # Exponential
                lambda_param = fdp.lambda_param if fdp.lambda_param else 1/mean_demand
                base_prediction = np.random.exponential(1/lambda_param)
                
            elif fdp.distribution_type == 3:  # Log-Normal
                mean_param = fdp.mean_param if fdp.mean_param else np.log(mean_demand)
                std_param = fdp.std_dev_param if fdp.std_dev_param else std_demand/mean_demand
                base_prediction = np.random.lognormal(mean_param, std_param)
                
            elif fdp.distribution_type == 4:  # Gamma
                shape = fdp.shape_param if fdp.shape_param else (mean_demand/std_demand)**2
                scale = fdp.scale_param if fdp.scale_param else std_demand**2/mean_demand
                base_prediction = np.random.gamma(shape, scale)
                
            elif fdp.distribution_type == 5:  # Uniform
                min_param = fdp.min_param if fdp.min_param else mean_demand - std_demand
                max_param = fdp.max_param if fdp.max_param else mean_demand + std_demand
                base_prediction = np.random.uniform(min_param, max_param)
                
            else:
                # Default to normal distribution
                base_prediction = np.random.normal(mean_demand, std_demand)
            
            # Apply continuity adjustment for first day of simulation
            if day_index == 0:
                # Smooth transition from last historical value
                continuity_factor = 0.7  # Weight for historical continuity
                base_prediction = (continuity_factor * last_historical_value + 
                                (1 - continuity_factor) * base_prediction)
            
            # Apply seasonality
            prediction = base_prediction * seasonality
            
            # Apply trend component with historical continuity
            trend_factor = 1 + (historical_trend / mean_demand) * (day_index + 1)
            prediction *= trend_factor
            
            # Add small random walk component for realism
            random_walk = np.random.normal(0, std_demand * 0.05)
            prediction += random_walk
            
            # Ensure positive demand
            return max(1.0, float(prediction))
            
        except Exception as e:
            logger.error(f"Error generating demand prediction: {str(e)}")
            # Fallback to mean with randomness
            demand_history = self._parse_demand_history(simulation_instance.demand_history)
            mean_demand = np.mean(demand_history) if demand_history else 2500
            return max(1.0, mean_demand * (0.9 + random.random() * 0.2))

    def _get_output_variable(self, equation):
        """Get the output variable from an equation"""
        try:
            if hasattr(equation, 'expression') and '=' in equation.expression:
                lhs = equation.expression.split('=')[0].strip()
                return lhs
            return None
        except:
            return None

    def _parse_demand_history(self, demand_history):
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

    def _bulk_save_results(self, simulation_instance, results):
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