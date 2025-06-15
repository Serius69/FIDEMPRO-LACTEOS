# services/simulation_core.py - Versión Mejorada
import logging
import random
import json
import re
import numpy as np
from datetime import timedelta
from typing import Dict, Any, List, Optional

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
    """Servicio mejorado para la ejecución de simulaciones"""
    
    def __init__(self):
        self.validator = SimulationValidator()
        self.cache_timeout = 3600
        self.batch_size = 100
        
        # Mapeo mejorado y completo de preguntas a variables
        self.question_to_variable_mapping = {
            # Precios
            'precio_actual': 'PVP',
            'precio_venta': 'PVP',
            'precio_producto': 'PVP',
            'precio de venta': 'PVP',
            
            # Demanda
            'demanda_historica': 'DH',
            'demanda_promedio': 'DH',
            'demanda_esperada': 'DE',
            'demanda esperada': 'DE',
            
            # Producción
            'produccion_actual': 'QPL',
            'cantidad_produccion': 'QPL',
            'cantidad producida': 'QPL',
            'producción': 'CPROD',
            'capacidad_produccion': 'CPROD',
            'capacidad de producción': 'CPROD',
            'capacidad producción diaria': 'CPROD',
            
            # Inventario
            'capacidad_inventario': 'CIP',
            'capacidad inventario productos': 'CIP',
            'capacidad del inventario': 'CIP',
            'capacidad_almacenamiento': 'CMIPF',
            'capacidad máxima almacenamiento': 'CMIPF',
            'stock_seguridad': 'SI',
            'stock inventario mínimo': 'SI',
            
            # Costos
            'costo_unitario_insumo': 'CUIP',
            'costo_insumos': 'CUIP',
            'costo unitario': 'CUIP',
            'costo unitario del insumo': 'CUIP',
            'costo_fijo_diario': 'CFD',
            'costos_fijos': 'CFD',
            'costos fijos': 'CFD',
            'costo fijo diario': 'CFD',
            'costo_transporte': 'CUTRANS',
            'costo unitario transporte': 'CUTRANS',
            
            # Clientes
            'clientes_diarios': 'CPD',
            'clientes_por_dia': 'CPD',
            'clientes por día': 'CPD',
            'clientes llegan diariamente': 'CPD',
            
            # Empleados
            'numero_empleados': 'NEPP',
            'empleados': 'NEPP',
            'número de empleados': 'NEPP',
            'sueldos_salarios': 'SE',
            'salarios': 'SE',
            'sueldos empleados': 'SE',
            
            # Marketing y competencia
            'precio_competencia': 'PC',
            'precio promedio competencia': 'PC',
            'gastos_marketing': 'GMM',
            'marketing': 'GMM',
            'gastos de marketing': 'GMM',
            'gastos marketing mensuales': 'GMM',
            
            # Tiempos
            'tiempo_entre_compras': 'TPC',
            'tiempo promedio compras': 'TPC',
            'tiempo_reabastecimiento': 'TR',
            'tiempo reabastece insumos': 'TR',
            'tiempo_produccion_unitario': 'TPE',
            'tiempo producir unidad': 'TPE',
            'dias_reabastecimiento': 'DPL',
            'días promedio reabastecimiento': 'DPL',
            'tiempo_procesamiento_pedidos': 'TMP',
            'tiempo medio procesamiento': 'TMP',
            
            # Cantidades
            'insumos_por_producto': 'CINSP',
            'litros insumo fabricar': 'CINSP',
            'cantidad_por_lote': 'CPPL',
            'cantidad promedio lote': 'CPPL',
            'cantidad_transporte_viaje': 'CTPLV',
            'litros transportan viaje': 'CTPLV',
            
            # Otros
            'estacionalidad': 'ED',
            'estacionalidad demanda': 'ED',
            'numero_proveedores': 'NPD',
            'proveedores leche': 'NPD',
            'consumo_diario_proveedor': 'CTL',
            'consumo diario promedio': 'CTL'
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

    def _prepare_simulation_data(self, simulation_instance):
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
        
        # Get complete answer data including question text
        answers = Answer.objects.filter(
            fk_questionary_result=simulation_instance.fk_questionary_result
        ).select_related(
            'fk_question__fk_variable'
        ).values(
            'fk_question_id', 
            'fk_question__fk_variable__initials', 
            'fk_question__question',
            'answer'
        )
        
        logger.info(f"Loaded {len(list(answers))} answers from questionnaire")
        
        return {
            'areas': list(areas),
            'equations': list(equations),
            'variables': {v['initials']: v for v in variables},
            'answers': list(answers),
            'product': product
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
        
        # Generate demand prediction for current day
        predicted_demand = self._generate_demand_prediction(
            simulation_instance, variable_dict, day_index
        )
        print (f"Predicted demand for day {day_index + 1}: {predicted_demand}")
        
        # CORRECCIÓN: Usar demanda simulada del día actual
        variable_dict['DE'] = predicted_demand
        variable_dict['DH'] = predicted_demand  # Demanda del día actual
        
        # Calcular DPH dinámico basado en histórico y días anteriores
        if day_index == 0:
            # Primer día: usar promedio del histórico real
            demand_history = self._parse_demand_history(simulation_instance.demand_history)
            if demand_history:
                variable_dict['DPH'] = float(np.mean(demand_history))
                variable_dict['DSD'] = float(np.std(demand_history))
                variable_dict['CVD'] = variable_dict['DSD'] / max(variable_dict['DPH'], 1)
            else:
                # Fallback si no hay histórico
                variable_dict['DPH'] = predicted_demand
                variable_dict['DSD'] = predicted_demand * 0.1  # 10% de variación estimada
                variable_dict['CVD'] = 0.1
        else:
            # Días posteriores: usar promedio móvil de días anteriores simulados
            window_size = min(7, day_index)  # Ventana de hasta 7 días
            previous_demands = []
            
            # Obtener demandas de días anteriores desde los resultados almacenados
            if 'previous_results' in simulation_data:
                start_idx = max(0, day_index - window_size)
                for i in range(start_idx, day_index):
                    if i < len(simulation_data['previous_results']):
                        prev_result = simulation_data['previous_results'][i]
                        if 'DE' in prev_result:
                            previous_demands.append(float(prev_result['DE']))
            
            if previous_demands:
                variable_dict['DPH'] = float(np.mean(previous_demands))
                variable_dict['DSD'] = float(np.std(previous_demands)) if len(previous_demands) > 1 else variable_dict.get('DSD', predicted_demand * 0.1)
                variable_dict['CVD'] = variable_dict['DSD'] / max(variable_dict['DPH'], 1)
            else:
                # Fallback: usar demanda actual
                variable_dict['DPH'] = predicted_demand
                variable_dict['DSD'] = variable_dict.get('DSD', predicted_demand * 0.1)
                variable_dict['CVD'] = 0.1
        
        # Actualizar DDP (Demanda Diaria Proyectada) con el nuevo DPH dinámico
        if 'ED' in variable_dict:  # Factor de estacionalidad
            variable_dict['DDP'] = variable_dict['DPH'] * (1 + (variable_dict['DE'] - variable_dict['DPH']) / max(variable_dict['DPH'], 1) * 0.2) * variable_dict['ED']
        else:
            variable_dict['DDP'] = variable_dict['DPH']
        
        # Calculate all equations in proper order
        endogenous_results = self._calculate_all_equations(
            simulation_data['equations'], 
            variable_dict
        )
        
        # Ensure all variables are in results
        final_results = self._merge_results(variable_dict, endogenous_results)
        
        # Store results for next iterations
        if 'previous_results' not in simulation_data:
            simulation_data['previous_results'] = []
        
        # Guardar resultado completo del día
        day_complete_result = {**variable_dict, **endogenous_results}
        simulation_data['previous_results'].append(day_complete_result)
        
        # Validate results
        self._validate_simulation_results(final_results, variable_dict)
        
        logger.debug(f"Day {day_index}: Calculated {len(final_results)} total variables")
        logger.debug(f"Day {day_index}: DPH={variable_dict.get('DPH', 0):.2f}, DE={predicted_demand:.2f}, DDP={variable_dict.get('DDP', 0):.2f}")
        
        return {
            'endogenous_results': final_results,
            'variable_initials_dict': variable_dict,
            'predicted_demand': predicted_demand,
            'dynamic_dph': variable_dict.get('DPH', 0),
            'demand_std': variable_dict.get('DSD', 0)
        }

    def _initialize_variables_from_questionnaire(self, answers, simulation_instance, day_index):
        """Initialize variables PRIMARILY from questionnaire data"""
        
        variable_dict = {}
        
        # Add essential system variables
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
        
        for answer_data in answers:
            var_initials = answer_data.get('fk_question__fk_variable__initials')
            answer_value = answer_data.get('answer')
            question_text = answer_data.get('fk_question__question', '')
            
            if not answer_value:
                continue
            
            # Method 1: Direct variable mapping
            if var_initials:
                processed_value = self._process_answer_value(answer_value, var_initials)
                if processed_value is not None:
                    variable_dict[var_initials] = processed_value
                    questionnaire_values_loaded += 1
                    logger.debug(f"Direct mapping: {var_initials} = {processed_value}")
            
            # Method 2: Text-based mapping from question content
            if question_text:
                mapped_var = self._map_question_to_variable(question_text)
                if mapped_var and mapped_var not in variable_dict:
                    processed_value = self._process_answer_value(answer_value, mapped_var)
                    if processed_value is not None:
                        variable_dict[mapped_var] = processed_value
                        questionnaire_values_loaded += 1
                        logger.debug(f"Text mapping: {mapped_var} = {processed_value} (from '{question_text[:50]}...')")
        
        logger.info(f"Successfully loaded {questionnaire_values_loaded} values from questionnaire")
        
        # Calculate derived variables from questionnaire data
        self._calculate_derived_variables(variable_dict)
        
        # Add minimal defaults for missing ESSENTIAL variables only
        self._add_minimal_defaults(variable_dict)
        
        return variable_dict

    def _map_question_to_variable(self, question_text: str) -> Optional[str]:
        """Map question text to variable initials using comprehensive mapping"""
        question_lower = question_text.lower()
        
        # Try exact phrase matching first
        for key_phrase, var_initials in self.question_to_variable_mapping.items():
            if key_phrase in question_lower:
                return var_initials
        
        # Try word-based matching
        words_to_vars = {
            'precio': {'venta': 'PVP', 'competencia': 'PC'},
            'demanda': {'histórica': 'DH', 'esperada': 'DE'},
            'capacidad': {'producción': 'CPROD', 'inventario': 'CIP', 'almacenamiento': 'CMIPF'},
            'costo': {'fijo': 'CFD', 'unitario': 'CUIP', 'transporte': 'CUTRANS'},
            'clientes': {'diariamente': 'CPD', 'día': 'CPD'},
            'empleados': {'número': 'NEPP', 'sueldos': 'SE'},
            'tiempo': {'compras': 'TPC', 'reabastecimiento': 'TR', 'procesamiento': 'TMP'},
            'gastos': {'marketing': 'GMM'},
            'cantidad': {'producida': 'QPL', 'lote': 'CPPL', 'transporte': 'CTPLV'}
        }
        
        for main_word, sub_words in words_to_vars.items():
            if main_word in question_lower:
                for sub_word, var in sub_words.items():
                    if sub_word in question_lower:
                        return var
        
        return None

    def _process_answer_value(self, answer_value, variable_name):
        """Process and clean answer values from questionnaire"""
        try:
            # Handle special cases
            if variable_name == 'ED':  # Estacionalidad
                if isinstance(answer_value, str):
                    return 1.0 if answer_value.lower() in ['sí', 'si', 'yes', 'true'] else 0.5
                return float(answer_value) if answer_value else 1.0
            
            # Handle list/array values (like historical demand)
            if isinstance(answer_value, (list, tuple)):
                if len(answer_value) > 0:
                    # For demand history, keep the full list
                    if variable_name == 'DH':
                        return answer_value
                    # For other variables, use the mean
                    return float(np.mean([float(x) for x in answer_value if x is not None]))
                return None
            
            # Handle string values
            if isinstance(answer_value, str):
                # Remove common formatting
                cleaned = answer_value.replace(',', '').replace('$', '').replace('%', '').replace(' ', '')
                cleaned = cleaned.replace('Bs', '').replace('bs', '').replace('L', '').replace('litros', '')
                cleaned = cleaned.replace('kg', '').replace('kilogramos', '').strip()
                
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
        """Calculate important derived variables from questionnaire data"""
        
        # Ensure VPC (Ventas Por Cliente) is calculated properly
        if 'VPC' not in variable_dict or variable_dict.get('VPC', 0) == 0:
            if 'DE' in variable_dict and 'CPD' in variable_dict and variable_dict['CPD'] > 0:
                variable_dict['VPC'] = variable_dict['DE'] / variable_dict['CPD']
            else:
                # Use price-based estimation
                pvp = variable_dict.get('PVP', 15.50)
                if pvp < 5:  # Likely milk or yogurt
                    variable_dict['VPC'] = 2.5
                elif pvp < 25:  # Mid-range products
                    variable_dict['VPC'] = 15
                else:  # High-value products like cheese
                    variable_dict['VPC'] = 5
        
        # Calculate TCAE (Total Clientes Atendidos Efectivamente)
        if 'TCAE' not in variable_dict:
            cpd = variable_dict.get('CPD', 85)
            variable_dict['TCAE'] = cpd * 0.95  # 95% efficiency
        
        # Ensure production capacity is set
        if 'CPROD' not in variable_dict:
            qpl = variable_dict.get('QPL', 100)
            variable_dict['CPROD'] = qpl * 1.2  # 20% extra capacity
        
        # Calculate monthly values to daily
        if 'SE' in variable_dict:
            # If it's a monthly value (> 1000), convert to daily
            if variable_dict['SE'] > 1000:
                variable_dict['SE_daily'] = variable_dict['SE'] / 30
            else:
                variable_dict['SE_daily'] = variable_dict['SE']
        
        if 'GMM' in variable_dict:
            # If it's a monthly value (> 100), convert to daily
            if variable_dict['GMM'] > 100:
                variable_dict['GMM_daily'] = variable_dict['GMM'] / 30
            else:
                variable_dict['GMM_daily'] = variable_dict['GMM']

    def _add_minimal_defaults(self, variable_dict):
        """Add only absolutely essential missing variables with realistic defaults"""
        
        # Only add defaults for variables that are truly missing and essential
        essential_defaults = {
            'CPROD': variable_dict.get('QPL', 100) * 1.2 if 'QPL' in variable_dict else 3000,
            'ED': 1.0,  # No seasonality by default
            'TPC': 2,   # Days between purchases
            'TR': 3,    # Restocking time
            'TMP': 1,   # Order processing time
            'NPD': 3,   # Number of suppliers
            'MLP': 480, # Working minutes per day (8 hours)
            'CINSP': 1.05,  # Input conversion factor
            'SI': 100,  # Safety stock
            'DPL': 3,   # Lead time days
            'CTPLV': 200,  # Transport capacity per trip
            'CPPL': 100,  # Batch size
            'TPE': 60,  # Production time per unit
        }
        
        added_defaults = []
        for var, default_val in essential_defaults.items():
            if var not in variable_dict:
                variable_dict[var] = default_val
                added_defaults.append(var)
        
        if added_defaults:
            logger.debug(f"Added minimal defaults for: {added_defaults}")

    def _calculate_all_equations(self, equations, variable_dict):
        """Calculate all equations with improved dependency resolution"""
        
        endogenous_results = {}
        
        # Define calculation order by area priority
        area_priority = [
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
        
        # Process equations in priority order
        for area in area_priority:
            if area in equations_by_area:
                logger.debug(f"Processing {len(equations_by_area[area])} equations for area: {area}")
                for equation in equations_by_area[area]:
                    self._solve_single_equation(
                        equation, variable_dict, endogenous_results
                    )
        
        # Process remaining areas
        for area, eqs in equations_by_area.items():
            if area not in area_priority:
                for equation in eqs:
                    self._solve_single_equation(
                        equation, variable_dict, endogenous_results
                    )
        
        # Calculate critical missing variables
        self._calculate_missing_critical_variables(variable_dict, endogenous_results)
        
        return endogenous_results

    def _solve_single_equation(self, equation, variable_dict, endogenous_results):
        """Solve a single equation with improved error handling"""
        
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
            
            # Preprocess expression
            rhs = self._preprocess_expression(rhs)
            
            # Evaluate
            result = self._evaluate_expression(rhs, all_variables)
            
            if result is not None:
                endogenous_results[output_var] = result
                variable_dict[output_var] = result
                logger.debug(f"Calculated {output_var} = {result:.2f}")
        
        except Exception as e:
            logger.debug(f"Could not solve equation {equation.expression}: {e}")

    def _preprocess_expression(self, expression):
        """Preprocess expression to handle special cases"""
        
        # Remove summation symbol
        expression = expression.replace('∑', '')
        
        # Replace random() with actual value
        expression = expression.replace('random()', str(random.random()))
        
        # Handle max/min functions
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
        """Calculate critical variables using questionnaire data"""
        
        # Get values from questionnaire
        cpd = variable_dict.get('CPD', 85)
        pvp = variable_dict.get('PVP', 15.50)
        vpc = variable_dict.get('VPC', 30)
        cuip = variable_dict.get('CUIP', 8.20)
        cprod = variable_dict.get('CPROD', 3000)
        cfd = variable_dict.get('CFD', 1800)
        se_monthly = variable_dict.get('SE', 48000)
        gmm_monthly = variable_dict.get('GMM', 3500)
        de = variable_dict.get('DE', 2650)
        
        # Convert monthly to daily
        se_daily = se_monthly / 30 if se_monthly > 1000 else se_monthly
        gmm_daily = gmm_monthly / 30 if gmm_monthly > 100 else gmm_monthly
        
        # Calculate TCAE realistically
        if 'TCAE' not in endogenous_results:
            max_clients_by_demand = de / vpc if vpc > 0 else cpd
            endogenous_results['TCAE'] = min(cpd * 0.95, max_clients_by_demand)
        
        # Calculate TPV (Total Productos Vendidos)
        if 'TPV' not in endogenous_results:
            tcae = endogenous_results.get('TCAE', cpd * 0.95)
            tpv = min(tcae * vpc, de, cprod * 0.9)  # Limited by demand and production
            endogenous_results['TPV'] = tpv
        
        # Calculate TPPRO (Total Productos Producidos)
        if 'TPPRO' not in endogenous_results:
            tpv = endogenous_results.get('TPV', de)
            endogenous_results['TPPRO'] = min(tpv * 1.05, cprod)  # 5% safety margin
        
        # Financial calculations
        if 'IT' not in endogenous_results:
            tpv = endogenous_results.get('TPV', 2550)
            endogenous_results['IT'] = tpv * pvp
        
        if 'CTAI' not in endogenous_results:
            tppro = endogenous_results.get('TPPRO', cprod * 0.85)
            endogenous_results['CTAI'] = cuip * tppro
        
        if 'GO' not in endogenous_results:
            ctai = endogenous_results.get('CTAI', cuip * cprod * 0.85)
            endogenous_results['GO'] = cfd + se_daily + ctai
        
        if 'GG' not in endogenous_results:
            endogenous_results['GG'] = gmm_daily
        
        if 'TG' not in endogenous_results:
            go = endogenous_results.get('GO', 10000)
            gg = endogenous_results.get('GG', 116)
            endogenous_results['TG'] = go + gg
        
        if 'GT' not in endogenous_results:
            it = endogenous_results.get('IT', 39525)
            tg = endogenous_results.get('TG', 10116)
            endogenous_results['GT'] = it - tg
        
        # Efficiency metrics
        if 'FU' not in endogenous_results:
            tppro = endogenous_results.get('TPPRO', 2550)
            endogenous_results['FU'] = min(tppro / cprod, 1.0) if cprod > 0 else 0
        
        if 'PE' not in endogenous_results:
            tpv = endogenous_results.get('TPV', 2550)
            nepp = variable_dict.get('NEPP', 15)
            endogenous_results['PE'] = tpv / nepp if nepp > 0 else 0
        
        # ROI and profitability
        if 'NR' not in endogenous_results:
            gt = endogenous_results.get('GT', 0)
            it = endogenous_results.get('IT', 1)
            endogenous_results['NR'] = gt / it if it > 0 else 0
        
        if 'MB' not in endogenous_results:
            it = endogenous_results.get('IT', 1)
            ctai = endogenous_results.get('CTAI', 0)
            endogenous_results['MB'] = (it - ctai) / it if it > 0 else 0
        
        if 'RI' not in endogenous_results:
            gt = endogenous_results.get('GT', 0)
            investment = cfd * 30 + se_monthly  # Monthly investment approximation
            endogenous_results['RI'] = (gt * 30) / investment if investment > 0 else 0
        
        # Inventory metrics
        if 'IPF' not in endogenous_results:
            tppro = endogenous_results.get('TPPRO', cprod * 0.85)
            tpv = endogenous_results.get('TPV', 2550)
            endogenous_results['IPF'] = max(0, tppro - tpv)
        
        if 'DI' not in endogenous_results:
            de = variable_dict.get('DE', 2650)
            tpv = endogenous_results.get('TPV', 2550)
            endogenous_results['DI'] = max(0, de - tpv)
        
        if 'RTI' not in endogenous_results:
            ipf = endogenous_results.get('IPF', 100)
            tpv = endogenous_results.get('TPV', 2550)
            endogenous_results['RTI'] = (365 * tpv) / max(ipf, 1)
        
        # Other important metrics
        if 'PM' not in endogenous_results:
            tpv = endogenous_results.get('TPV', 2550)
            de = variable_dict.get('DE', 2650)
            endogenous_results['PM'] = tpv / de if de > 0 else 0
        
        if 'NCM' not in endogenous_results:
            pvp = variable_dict.get('PVP', 15.50)
            pc = variable_dict.get('PC', 15.80)
            endogenous_results['NCM'] = abs(pvp - pc) / max(pc, 1)

    def _validate_simulation_results(self, endogenous_results, variable_dict):
        """Validate simulation results for coherence and realism"""
        validations = []
        
        # Get key metrics
        tpv = endogenous_results.get('TPV', 0)
        tppro = endogenous_results.get('TPPRO', 0)
        it = endogenous_results.get('IT', 0)
        gt = endogenous_results.get('GT', 0)
        de = variable_dict.get('DE', 0)
        pvp = variable_dict.get('PVP', 1)
        cprod = variable_dict.get('CPROD', 0)
        
        # Validation 1: Sales cannot exceed production
        if tpv > tppro * 1.1:  # Allow 10% tolerance
            endogenous_results['TPV'] = tppro
            logger.warning(f'Sales ({tpv}) exceed production ({tppro}), capping sales')
        
        # Validation 2: Production cannot exceed capacity
        if tppro > cprod:
            endogenous_results['TPPRO'] = cprod
            logger.warning(f'Production ({tppro}) exceeds capacity ({cprod}), capping production')
        
        # Validation 3: Revenue should match sales
        expected_revenue = tpv * pvp
        if abs(it - expected_revenue) > expected_revenue * 0.01:  # 1% tolerance
            endogenous_results['IT'] = expected_revenue
            logger.debug(f'Revenue mismatch corrected: {it} -> {expected_revenue}')
        
        # Validation 4: Profit margins should be realistic
        if it > 0:
            margin = gt / it
            if margin < -0.5:  # Losing more than 50%
                # Cap losses at 30% of revenue
                endogenous_results['TG'] = it * 1.3
                endogenous_results['GT'] = it - endogenous_results['TG']
                logger.warning(f'Unrealistic loss margin {margin:.2%}, adjusted to -30%')
            elif margin > 0.8:  # More than 80% profit
                logger.info(f'High profit margin detected: {margin:.2%}')

    def _generate_demand_prediction(self, simulation_instance, variable_dict, day_index):
        """Generate realistic demand prediction using FDP"""
        try:
            fdp = simulation_instance.fk_fdp
            demand_history = self._parse_demand_history(simulation_instance.demand_history)
            
            # Calculate base statistics from REAL data
            if demand_history and len(demand_history) > 0:
                mean_demand = np.mean(demand_history)
                std_demand = np.std(demand_history)
                cv = std_demand / mean_demand if mean_demand > 0 else 0.1
                
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
                cv = 0.1
                last_historical_value = mean_demand
                historical_trend = 0
            
            # Add seasonality from questionnaire
            seasonality = variable_dict.get('ED', 1.0)
            
            # Limit standard deviation to avoid extreme values
            max_std = mean_demand * 0.2  # Maximum 20% variation
            std_to_use = min(std_demand, max_std)
            
            # Generate prediction based on distribution type
            if fdp.distribution_type == 1:  # Normal
                base_prediction = np.random.normal(mean_demand, std_to_use)
                
            elif fdp.distribution_type == 2:  # Exponential
                scale = mean_demand  # Use mean as scale
                base_prediction = np.random.exponential(scale)
                
            elif fdp.distribution_type == 3:  # Log-Normal
                if mean_demand > 0 and cv > 0:
                    sigma = np.sqrt(np.log(1 + cv**2))
                    mu = np.log(mean_demand) - sigma**2 / 2
                    base_prediction = np.random.lognormal(mu, sigma)
                else:
                    base_prediction = mean_demand
                    
            elif fdp.distribution_type == 4:  # Gamma
                if std_to_use > 0:
                    shape = (mean_demand / std_to_use) ** 2
                    scale = std_to_use ** 2 / mean_demand
                    base_prediction = np.random.gamma(shape, scale)
                else:
                    base_prediction = mean_demand
                    
            elif fdp.distribution_type == 5:  # Uniform
                min_val = mean_demand - std_to_use
                max_val = mean_demand + std_to_use
                base_prediction = np.random.uniform(min_val, max_val)
                
            else:
                base_prediction = np.random.normal(mean_demand, std_to_use)
            
            # Apply continuity adjustment for first days
            if day_index < 7:
                continuity_factor = 0.7 - (day_index * 0.1)  # Decreasing weight
                base_prediction = (continuity_factor * last_historical_value + 
                                (1 - continuity_factor) * base_prediction)
            
            # Apply seasonality
            prediction = base_prediction * seasonality
            
            # Apply trend with dampening
            trend_dampening = 0.3  # Reduce trend impact
            trend_factor = 1 + (historical_trend / mean_demand) * trend_dampening * (day_index / 30)
            prediction *= trend_factor
            
            # Add small random walk
            random_walk = np.random.normal(0, std_to_use * 0.05)
            prediction += random_walk
            
            # Validate prediction within reasonable bounds
            lower_bound = mean_demand * 0.7
            upper_bound = mean_demand * 1.3
            
            prediction = np.clip(prediction, lower_bound, upper_bound)
            
            # Ensure positive demand
            prediction = max(1.0, float(prediction))
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error generating demand prediction: {str(e)}")
            # Fallback to mean with small randomness
            demand_history = self._parse_demand_history(simulation_instance.demand_history)
            mean_demand = np.mean(demand_history) if demand_history else 2500
            return max(1.0, mean_demand * (0.95 + random.random() * 0.1))

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

    def _merge_results(self, variable_dict, endogenous_results):
        """Merge all results ensuring completeness"""
        
        # Start with endogenous results
        final_results = endogenous_results.copy()
        
        # Add important variables from variable_dict if not in results
        important_vars = [
            'DE', 'DH', 'PVP', 'CPD', 'NEPP', 'SE', 'CFD', 'GMM',
            'CUIP', 'CPROD', 'PC', 'ED', 'TPC', 'TR', 'MLP', 'NMD',
            'VPC', 'TCAE', 'DIA'
        ]
        
        for var in important_vars:
            if var not in final_results and var in variable_dict:
                final_results[var] = variable_dict[var]
        
        return final_results

    def _bulk_save_results(self, simulation_instance, results):
        """Bulk save simulation results with validation"""
        result_objects = []
        
        results.sort(key=lambda x: x[0])
        
        demand_history_numeric = self._parse_demand_history(
            simulation_instance.demand_history
        )
        
        # Calculate historical statistics
        hist_mean = np.mean(demand_history_numeric) if demand_history_numeric else 0
        hist_std = np.std(demand_history_numeric) if demand_history_numeric else 0
        
        for day_index, day_data in results:
            endogenous_results = day_data['endogenous_results']
            predicted_demand = day_data.get('predicted_demand', 0)
            
            # Check demand prediction validity
            if hist_mean > 0:
                demand_deviation = abs(predicted_demand - hist_mean) / hist_mean
                if demand_deviation > 0.5:  # More than 50% deviation
                    logger.warning(f"Day {day_index}: High demand deviation {demand_deviation:.2%}")
            
            demand_total = predicted_demand if predicted_demand > 0 else endogenous_results.get('DE', 2500)
            
            all_demands = demand_history_numeric + [demand_total]
            demand_std_dev = np.std(all_demands)
            
            # Ensure all values are serializable
            serializable_results = {}
            for k, v in endogenous_results.items():
                try:
                    value = float(v) if isinstance(v, (int, float, np.number)) else 0.0
                    # Validate no extreme values
                    if abs(value) > 1e9:  # Billion threshold
                        logger.warning(f"Extreme value detected for {k}: {value}")
                        value = 0.0
                    serializable_results[k] = value
                except:
                    serializable_results[k] = 0.0
            
            # Add metadata
            serializable_results['_metadata'] = {
                'day_index': day_index,
                'demand_prediction': predicted_demand,
                'questionnaire_loaded': True
            }
            
            result_objects.append(
                ResultSimulation(
                    fk_simulation=simulation_instance,
                    demand_mean=demand_total,
                    demand_std_deviation=demand_std_dev,
                    date=simulation_instance.date_created + timedelta(days=day_index + 1),
                    variables=serializable_results,
                    confidence_intervals={
                        'demand_lower': max(0, demand_total - 2 * demand_std_dev),
                        'demand_upper': demand_total + 2 * demand_std_dev
                    }
                )
            )
            
            if len(result_objects) >= self.batch_size:
                ResultSimulation.objects.bulk_create(result_objects)
                result_objects = []
        
        if result_objects:
            ResultSimulation.objects.bulk_create(result_objects)
        
        logger.info(f"Saved {len(results)} simulation results successfully")

    def execute_simulation_with_progress(self, simulation_instance, progress_callback=None):
        """Execute simulation with progress callback support"""
        try:
            nmd = int(simulation_instance.quantity_time)
            simulation_data = self._prepare_simulation_data(simulation_instance)
            results_to_save = []
            
            for day_index in range(nmd):
                # Update progress
                if progress_callback:
                    progress_callback(day_index + 1)
                
                # Simulate day
                day_results = self._simulate_single_day_complete(
                    simulation_instance, simulation_data, day_index
                )
                results_to_save.append((day_index, day_results))
            
            # Save results
            self._bulk_save_results(simulation_instance, results_to_save)
            
        except Exception as e:
            logger.error(f"Error in simulation with progress: {str(e)}")
            raise