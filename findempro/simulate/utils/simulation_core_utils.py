# services/simulation_core.py - Versión Mejorada
import logging
import random
import json
import re
import numpy as np
import math

from datetime import timedelta
from typing import Dict, Any, List, Optional

from django.db import transaction
from django.shortcuts import get_object_or_404

from ..models import (
    Simulation, ResultSimulation, ProbabilisticDensityFunction
)
from ..validators.simulation_validators import SimulationValidator
from .data_parsers_utils import DataParser
from product.models import Area
from questionary.models import Answer, QuestionaryResult
from variable.models import Variable, Equation

from collections import defaultdict, deque

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
            'precio venta producto': 'PVP',
            'precio unitario': 'PVP',
            
            # Demanda
            'demanda_historica': 'DH',
            'demanda_promedio': 'DH',
            'demanda histórica': 'DH',
            'histórico demanda': 'DH',
            'datos históricos': 'DH',
            'demanda_esperada': 'DE',
            'demanda esperada': 'DE',
            'expectativa demanda': 'DE',
            
            # Producción
            'produccion_actual': 'QPL',
            'cantidad_produccion': 'QPL',
            'cantidad producida': 'QPL',
            'producción diaria': 'QPL',
            'litros producidos': 'QPL',
            'producción': 'CPROD',
            'capacidad_produccion': 'CPROD',
            'capacidad de producción': 'CPROD',
            'capacidad producción diaria': 'CPROD',
            'capacidad máxima producción': 'CPROD',
            'capacidad planta': 'CPROD',
            
            # Inventario
            'capacidad_inventario': 'CIP',
            'capacidad inventario productos': 'CIP',
            'capacidad del inventario': 'CIP',
            'almacén capacidad': 'CIP',
            'capacidad_almacenamiento': 'CMIPF',
            'capacidad máxima almacenamiento': 'CMIPF',
            'capacidad almacén': 'CMIPF',
            'stock_seguridad': 'SI',
            'stock inventario mínimo': 'SI',
            'inventario seguridad': 'SI',
            'stock mínimo': 'SI',
            
            # Costos
            'costo_unitario_insumo': 'CUIP',
            'costo_insumos': 'CUIP',
            'costo unitario': 'CUIP',
            'costo unitario del insumo': 'CUIP',
            'costo materia prima': 'CUIP',
            'precio insumos': 'CUIP',
            'costo_fijo_diario': 'CFD',
            'costos_fijos': 'CFD',
            'costos fijos': 'CFD',
            'costo fijo diario': 'CFD',
            'gastos fijos diarios': 'CFD',
            'costo_transporte': 'CUTRANS',
            'costo unitario transporte': 'CUTRANS',
            'costo distribución': 'CUTRANS',
            'tarifa transporte': 'CUTRANS',
            
            # Clientes
            'clientes_diarios': 'CPD',
            'clientes_por_dia': 'CPD',
            'clientes por día': 'CPD',
            'clientes llegan diariamente': 'CPD',
            'número clientes día': 'CPD',
            'clientes atendidos': 'CPD',
            
            # Empleados
            'numero_empleados': 'NEPP',
            'empleados': 'NEPP',
            'número de empleados': 'NEPP',
            'cantidad empleados': 'NEPP',
            'personal producción': 'NEPP',
            'sueldos_salarios': 'SE',
            'salarios': 'SE',
            'sueldos empleados': 'SE',
            'salarios mensuales': 'SE',
            'nómina mensual': 'SE',
            'planilla': 'SE',
            
            # Marketing y competencia
            'precio_competencia': 'PC',
            'precio promedio competencia': 'PC',
            'precio competidores': 'PC',
            'gastos_marketing': 'GMM',
            'marketing': 'GMM',
            'gastos de marketing': 'GMM',
            'gastos marketing mensuales': 'GMM',
            'inversión marketing': 'GMM',
            'publicidad': 'GMM',
            
            # Tiempos
            'tiempo_entre_compras': 'TPC',
            'tiempo promedio compras': 'TPC',
            'frecuencia compra': 'TPC',
            'tiempo_reabastecimiento': 'TR',
            'tiempo reabastece insumos': 'TR',
            'lead time': 'TR',
            'tiempo entrega proveedores': 'TR',
            'tiempo_produccion_unitario': 'TPE',
            'tiempo producir unidad': 'TPE',
            'minutos por litro': 'TPE',
            'tiempo producción': 'TPE',
            'dias_reabastecimiento': 'DPL',
            'días promedio reabastecimiento': 'DPL',
            'días reposición': 'DPL',
            'tiempo_procesamiento_pedidos': 'TMP',
            'tiempo medio procesamiento': 'TMP',
            
            # Cantidades
            'insumos_por_producto': 'CINSP',
            'litros insumo fabricar': 'CINSP',
            'conversión insumos': 'CINSP',
            'rendimiento insumos': 'CINSP',
            'cantidad_por_lote': 'CPPL',
            'cantidad promedio lote': 'CPPL',
            'tamaño lote': 'CPPL',
            'lote producción': 'CPPL',
            'cantidad_transporte_viaje': 'CTPLV',
            'litros transportan viaje': 'CTPLV',
            'capacidad camión': 'CTPLV',
            'capacidad vehículo': 'CTPLV',
            
            # Otros
            'estacionalidad': 'ED',
            'estacionalidad demanda': 'ED',
            'variación estacional': 'ED',
            'factor estacional': 'ED',
            'numero_proveedores': 'NPD',
            'proveedores leche': 'NPD',
            'cantidad proveedores': 'NPD',
            'consumo_diario_proveedor': 'CTL',
            'consumo diario promedio': 'CTL',
            'consumo promedio': 'CTL',
            
            # Horarios
            'horas_trabajo': 'MLP',
            'jornada laboral': 'MLP',
            'minutos laborables': 'MLP',
            'tiempo trabajo diario': 'MLP',
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
            
            # AGREGAR: Inicializar estado persistente
            simulation_state = {
                'inventories': {
                    'IPF': 1000,  # Inventario inicial productos finales
                    'II': 5000,   # Inventario inicial insumos
                },
                'previous_sales': [],
                'previous_production': [],
                'previous_demands': []
            }
            
            # Process days sequentially
            results_to_save = []
            
            for day_index in range(nmd):
                try:
                    # PASAR el estado a la simulación del día
                    day_results = self._simulate_single_day_complete(
                        simulation_instance, simulation_data, day_index, simulation_state
                    )
                    
                    # ACTUALIZAR el estado con los resultados del día
                    self._update_simulation_state(simulation_state, day_results)
                    
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

    def _update_simulation_state(self, state, day_results):
        """Actualizar el estado de la simulación con los resultados del día"""
        
        results = day_results['endogenous_results']
        
        # CRÍTICO: Actualizar inventarios de forma segura
        if 'IPF' in results and results['IPF'] is not None:
            state['inventories']['IPF'] = max(0, float(results['IPF']))
        
        if 'II' in results and results['II'] is not None:
            state['inventories']['II'] = max(0, float(results['II']))
        
        # Guardar históricos con validación
        if 'TPV' in results and results['TPV'] is not None:
            state['previous_sales'].append(float(results['TPV']))
        
        if 'QPL' in results and results['QPL'] is not None:
            state['previous_production'].append(float(results['QPL']))
        
        if 'predicted_demand' in day_results and day_results['predicted_demand'] is not None:
            state['previous_demands'].append(float(day_results['predicted_demand']))
        
        # Mantener solo los últimos 30 días de histórico
        max_history = 30
        for key in ['previous_sales', 'previous_production', 'previous_demands']:
            if len(state[key]) > max_history:
                state[key] = state[key][-max_history:]
        
        # AGREGAR: Log del estado para debugging
        logger.debug(f"Updated state - IPF: {state['inventories']['IPF']}, "
                    f"II: {state['inventories']['II']}, "
                    f"Sales history: {len(state['previous_sales'])} days")

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

    def _simulate_single_day_complete(self, simulation_instance, simulation_data, day_index, simulation_state):
        """Simulate a single day with complete variable initialization and calculation"""
        
        # Initialize ALL variables with REAL data from questionnaire
        variable_dict = self._initialize_variables_from_questionnaire(
            simulation_data['answers'], 
            simulation_instance, 
            day_index
        )
        
        # CRÍTICO: Gestionar inventarios desde el estado persistente
        if day_index == 0:
            # Primer día: usar valores iniciales del cuestionario o defaults
            variable_dict['IPF'] = variable_dict.get('IPF', 800)
            variable_dict['II'] = variable_dict.get('II', 8000)
            
            # Inicializar estado
            simulation_state['inventories']['IPF'] = variable_dict['IPF']
            simulation_state['inventories']['II'] = variable_dict['II']
        else:
            # Días siguientes: usar estado del día anterior
            variable_dict['IPF'] = simulation_state['inventories']['IPF']
            variable_dict['II'] = simulation_state['inventories']['II']
        
        # Log para debugging
        logger.debug(f"Day {day_index + 1}: Starting with IPF={variable_dict['IPF']}, II={variable_dict['II']}")
        
        # Generate demand prediction for current day
        predicted_demand = self._generate_demand_prediction(
            simulation_instance, variable_dict, day_index
        )
        
        # Set current day's demand
        variable_dict['DE'] = predicted_demand
        variable_dict['DH'] = predicted_demand  # Current day demand
        
        # Calculate DPH dinamically from historical data
        if day_index == 0:
            # First day: use historical average
            demand_history = self._parse_demand_history(simulation_instance.demand_history)
            if demand_history:
                variable_dict['DPH'] = float(np.mean(demand_history))
                variable_dict['DSD'] = float(np.std(demand_history))
                variable_dict['CVD'] = variable_dict['DSD'] / max(variable_dict['DPH'], 1)
            else:
                variable_dict['DPH'] = predicted_demand
                variable_dict['DSD'] = predicted_demand * 0.1
                variable_dict['CVD'] = 0.1
        else:
            # Use moving average from previous days
            if simulation_state['previous_demands']:
                window = simulation_state['previous_demands'][-7:]  # Last 7 days
                variable_dict['DPH'] = float(np.mean(window))
                variable_dict['DSD'] = float(np.std(window)) if len(window) > 1 else variable_dict['DPH'] * 0.1
                variable_dict['CVD'] = variable_dict['DSD'] / max(variable_dict['DPH'], 1)
            else:
                # Fallback
                variable_dict['DPH'] = predicted_demand
                variable_dict['DSD'] = predicted_demand * 0.1
                variable_dict['CVD'] = 0.1
        
        # Calculate DDP with seasonality
        if 'ED' in variable_dict:
            variable_dict['DDP'] = variable_dict['DPH'] * (1 + (variable_dict['DE'] - variable_dict['DPH']) / max(variable_dict['DPH'], 1) * 0.2) * variable_dict['ED']
        else:
            variable_dict['DDP'] = variable_dict['DPH']
        
        # CRÍTICO: Almacenar inventarios iniciales del día para cálculos
        initial_ipf = variable_dict['IPF']
        initial_ii = variable_dict['II']
        
        # Calculate all equations in proper order
        endogenous_results = self._calculate_all_equations(
            simulation_data['equations'], 
            variable_dict
        )
        
        # CORRECCIÓN INVENTARIOS: Calcular correctamente basado en operaciones del día
        qpl = endogenous_results.get('QPL', 0)
        tpv = endogenous_results.get('TPV', 0)
        uii = endogenous_results.get('UII', qpl * variable_dict.get('CINSP', 1.02))
        pi = endogenous_results.get('PI', 0)
        
        # Inventario final productos finales
        final_ipf = max(0, initial_ipf + qpl - tpv)
        final_ipf = min(final_ipf, variable_dict.get('CMIPF', 20000))  # Respetar capacidad máxima
        
        # Inventario final insumos
        final_ii = max(0, initial_ii + pi - uii)
        
        # Actualizar resultados con inventarios finales
        endogenous_results['IPF'] = final_ipf
        endogenous_results['II'] = final_ii
        
        # Validar coherencia de inventarios
        if final_ipf < 0:
            logger.warning(f"Day {day_index + 1}: Negative IPF corrected from {final_ipf} to 0")
            endogenous_results['IPF'] = 0
        
        if final_ii < 0:
            logger.warning(f"Day {day_index + 1}: Negative II corrected from {final_ii} to 0")
            endogenous_results['II'] = 0
        
        # Ensure all variables are in results
        final_results = self._merge_results(variable_dict, endogenous_results)
        
        # Validate results with enhanced checks
        self._validate_simulation_results(final_results, variable_dict)
        
        # Store results for next iterations
        if 'previous_results' not in simulation_data:
            simulation_data['previous_results'] = []
        
        day_complete_result = {**variable_dict, **endogenous_results}
        simulation_data['previous_results'].append(day_complete_result)
        
        logger.debug(f"Day {day_index + 1}: Ending with IPF={final_results['IPF']}, II={final_results['II']}")
        logger.debug(f"Day {day_index + 1}: Production={qpl}, Sales={tpv}, Demand={predicted_demand}")
        
        return {
            'endogenous_results': final_results,
            'variable_initials_dict': variable_dict,
            'predicted_demand': predicted_demand,
            'dynamic_dph': variable_dict.get('DPH', 0),
            'demand_std': variable_dict.get('DSD', 0),
            'inventory_movements': {
                'initial_ipf': initial_ipf,
                'final_ipf': final_results['IPF'],
                'initial_ii': initial_ii,
                'final_ii': final_results['II'],
                'production': qpl,
                'sales': tpv,
                'input_usage': uii,
                'input_purchase': pi
            }
        }

    def _initialize_variables_from_questionnaire(self, answers, simulation_instance, day_index):
        """Initialize variables PRIMARILY from questionnaire data - FIXED DUPLICATES"""
        
        variable_dict = {}
        processed_variables = set()  # Para evitar duplicaciones
        
        # Add essential system variables
        variable_dict['NMD'] = float(simulation_instance.quantity_time)
        variable_dict['DIA'] = float(day_index + 1)
        variable_dict['random'] = lambda: random.random()
        
        # Parse demand history first
        demand_history = self._parse_demand_history(simulation_instance.demand_history)
        if demand_history:
            variable_dict['DH'] = float(np.mean(demand_history))
            processed_variables.add('DH')
            logger.info(f"Loaded demand history average: {variable_dict['DH']}")
        
        # Process ALL answers from questionnaire with deduplication
        questionnaire_values_loaded = 0
        
        for answer_data in answers:
            var_initials = answer_data.get('fk_question__fk_variable__initials')
            answer_value = answer_data.get('answer')
            question_text = answer_data.get('fk_question__question', '')
            
            if not answer_value:
                continue
            
            # Method 1: Direct variable mapping (with deduplication)
            if var_initials and var_initials not in processed_variables:
                processed_value = self._process_answer_value(answer_value, var_initials)
                if processed_value is not None:
                    variable_dict[var_initials] = processed_value
                    processed_variables.add(var_initials)
                    questionnaire_values_loaded += 1
                    logger.debug(f"Direct mapping: {var_initials} = {processed_value}")
            elif var_initials in processed_variables:
                logger.debug(f"Skipping duplicate mapping for {var_initials}")
            
            # Method 2: Text-based mapping (only if not already processed)
            if question_text:
                mapped_var = self._map_question_to_variable(question_text)
                if mapped_var and mapped_var not in processed_variables:
                    processed_value = self._process_answer_value(answer_value, mapped_var)
                    if processed_value is not None:
                        variable_dict[mapped_var] = processed_value
                        processed_variables.add(mapped_var)
                        questionnaire_values_loaded += 1
                        logger.debug(f"Text mapping: {mapped_var} = {processed_value}")
        
        logger.info(f"Successfully loaded {questionnaire_values_loaded} unique values from questionnaire")
        
        # Calculate derived variables from questionnaire data
        self._calculate_derived_variables(variable_dict)
        
        # Add minimal defaults for missing ESSENTIAL variables only
        self._add_minimal_defaults(variable_dict)
        
        # CRUCIAL: Ensure PVP is always present
        if 'PVP' not in variable_dict or variable_dict['PVP'] <= 0:
            variable_dict['PVP'] = 15.50
            logger.warning("PVP was missing or invalid, set to default: 15.50")
        
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
            # CORREGIR: Evitar duplicación de CPROD
            if variable_name == 'CPROD':
                # Si CPROD ya existe, no sobrescribir a menos que sea más confiable
                if hasattr(self, '_cprod_sources'):
                    # Priorizar fuente más confiable
                    pass
                else:
                    self._cprod_sources = []
            
            # Handle special cases
            if variable_name == 'ED':  # Estacionalidad
                if isinstance(answer_value, str):
                    return 1.0 if answer_value.lower() in ['sí', 'si', 'yes', 'true'] else 0.8
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
        
        # CRÍTICO: Definir PVP si falta
        if 'PVP' not in variable_dict:
            # Buscar en respuestas del cuestionario
            pvp_found = False
            # Si no se encuentra, usar valor por defecto razonable
            variable_dict['PVP'] = 15.50
            logger.warning("PVP not found in questionnaire, using default value: 15.50")
        
        essential_defaults = {
            'CPROD': variable_dict.get('QPL', 100) * 1.2 if 'QPL' in variable_dict else 3000,
            'ED': 1.0,  # No seasonality by default
            'TPC': 2,   # Days between purchases
            'TR': 3,    # Restocking time
            'TMP': 1,   # Order processing time
            'NPD': 3,   # Number of suppliers
            'MLP': 480, # Working minutes per day (8 hours)
            'CINSP': 1.02,  # Input conversion factor (CORREGIDO: era 1.05)
            'SI': 500,  # Safety stock (CORREGIDO: era 100)
            'DPL': 3,   # Lead time days
            'CTPLV': 2000,  # Transport capacity per trip (CORREGIDO: era 200)
            'CPPL': 500,  # Batch size
            'TPE': 30,  # Production time per unit (CORREGIDO: era 60)
            'IPF': 800,  # Initial finished goods inventory (CORREGIDO: era 1000)
            'II': 8000,   # Initial raw materials inventory (CORREGIDO: era 5000)
            'VPC': 30,    # Sales per customer default
            'TCAE': 85,   # Total customers served
            'QPL': 2500,  # Default production
            'PPL': 2500,  # Products per batch
            'PI': 0,      # Initial input order
            'UII': 0,     # Initial input usage
            
            # AGREGAR VARIABLES CRÍTICAS FALTANTES:
            'CFD': 1500,    # Daily fixed costs (CORREGIDO: era 1800)
            'SE': 45000,    # Monthly salaries (CORREGIDO: era 48000)
            'GMM': 3000,    # Monthly marketing (CORREGIDO: era 3500)
            'CUIP': 7.50,   # Unit input cost (CORREGIDO: era 8.20)
            'CUTRANS': 0.25, # Transport unit cost (CORREGIDO: era 0.35)
            'CPD': 85,      # Customers per day
            'NEPP': 15,     # Number of employees
            'PC': 15.80,    # Competition price
            'CMIPF': 20000, # Max inventory capacity
        }
        
        added_defaults = []
        for var, default_val in essential_defaults.items():
            if var not in variable_dict:
                variable_dict[var] = default_val
                added_defaults.append(var)
        
        if added_defaults:
            logger.info(f"Added essential defaults for: {added_defaults}")

    def _calculate_all_equations(self, equations, variable_dict):
        """Calculate all equations with improved dependency resolution"""
        
        endogenous_results = {}
        
        # Definir orden de áreas optimizado para resolver dependencias
        area_priority = [
            'Análisis Demanda',      # Primero: DPH, DSD, DDP
            'Ventas',                # Segundo: VPC, TCAE, TPV, NSC, DI
            'Producción',            # Tercero: POD, CPROD, QPL, PPL, FU
            'Inventario Insumos',    # Cuarto: UII, PI, II
            'Inventario Productos Finales',  # Quinto: IPF
            'Distribución',          # Sexto: CTTL
            'Contabilidad',          # Séptimo: IT, CTAI, GO, GG, TG, GT, MB, NR
            'Recursos Humanos',      # Octavo: PE
            'Marketing',             # Noveno: otros indicadores
            'Competencia',           # Décimo: métricas de competencia
            'Indicadores Generales'  # Último: KPIs globales
        ]
        
        # Agrupar ecuaciones por área
        equations_by_area = {}
        for eq in equations:
            area_name = eq.fk_area.name if eq.fk_area else 'Other'
            if area_name not in equations_by_area:
                equations_by_area[area_name] = []
            equations_by_area[area_name].append(eq)
        
        # Resolver ecuaciones críticas primero
        critical_equations = []
        regular_equations = []
        
        # Identificar ecuaciones críticas que deben resolverse primero
        critical_vars = ['DPH', 'DSD', 'DDP', 'VPC', 'CPROD']
        
        for area in area_priority:
            if area in equations_by_area:
                for equation in equations_by_area[area]:
                    output_var = self._get_output_variable(equation)
                    if output_var in critical_vars:
                        critical_equations.append(equation)
                    else:
                        regular_equations.append(equation)
        
        # Procesar primero las críticas
        for equation in critical_equations:
            self._solve_single_equation(
                equation, variable_dict, endogenous_results
            )
        
        # Luego el resto en orden de área
        for area in area_priority:
            if area in equations_by_area:
                logger.debug(f"Processing {len(equations_by_area[area])} equations for area: {area}")
                for equation in equations_by_area[area]:
                    output_var = self._get_output_variable(equation)
                    if output_var and output_var not in critical_vars:  # Ya procesadas
                        self._solve_single_equation(
                            equation, variable_dict, endogenous_results
                        )
        
        # Procesar áreas no prioritarias
        for area, eqs in equations_by_area.items():
            if area not in area_priority:
                for equation in eqs:
                    self._solve_single_equation(
                        equation, variable_dict, endogenous_results
                    )
        
        # Segunda pasada para ecuaciones que dependen de resultados previos
        unresolved_count = 0
        max_iterations = 2
        
        for iteration in range(max_iterations):
            equations_solved = 0
            
            for area in area_priority:
                if area in equations_by_area:
                    for equation in equations_by_area[area]:
                        output_var = self._get_output_variable(equation)
                        if output_var and output_var not in endogenous_results:
                            # Intentar resolver
                            all_vars = {**variable_dict, **endogenous_results}
                            dependencies = self._extract_dependencies(equation.expression)
                            
                            # Verificar si todas las dependencias están disponibles
                            if all(dep in all_vars for dep in dependencies):
                                self._solve_single_equation(
                                    equation, variable_dict, endogenous_results
                                )
                                equations_solved += 1
                                unresolved_count += 1
            
            if equations_solved == 0:
                break  # No se resolvieron más ecuaciones
        
        if unresolved_count > 0:
            logger.info(f"Segunda pasada resolvió {unresolved_count} ecuaciones adicionales")
        
        # Calculate critical missing variables
        self._calculate_missing_critical_variables(variable_dict, endogenous_results)
        
        # Log final de variables calculadas
        logger.debug(f"Total variables calculated: {len(endogenous_results)}")
        
        return endogenous_results

    
    
    def _topological_sort_equations(self, equations, graph):
        """Ordenar ecuaciones según dependencias"""
        # Implementación simple de ordenamiento topológico
        visited = set()
        stack = []
        equation_map = {self._get_output_variable(eq): eq for eq in equations}
        
        def visit(var):
            if var in visited or var not in graph:
                return
            visited.add(var)
            for dep in graph.get(var, []):
                visit(dep)
            stack.append(var)
        
        # Visitar todas las variables
        for var in graph:
            visit(var)
        
        # Construir lista ordenada de ecuaciones
        sorted_equations = []
        for var in reversed(stack):
            if var in equation_map:
                sorted_equations.append(equation_map[var])
        
        # Agregar ecuaciones restantes
        for eq in equations:
            if eq not in sorted_equations:
                sorted_equations.append(eq)
        
        return sorted_equations

    def _can_solve_equation(self, equation, available_vars):
        """Verificar si una ecuación puede resolverse con las variables disponibles"""
        dependencies = self._extract_dependencies(equation.expression)
        return all(dep in available_vars for dep in dependencies)
    
    def _build_dependency_graph(self, equations):
        """Construir grafo de dependencias entre variables"""
        graph = {}
        
        for eq in equations:
            output_var = self._get_output_variable(eq)
            if output_var:
                dependencies = self._extract_dependencies(eq.expression)
                graph[output_var] = dependencies
        
        return graph
    
    def _extract_dependencies(self, expression):
        """Extraer variables que la expresión necesita"""
        if '=' not in expression:
            return []
        
        _, rhs = expression.split('=', 1)
        # Patrón para identificar variables (mayúsculas con números/guiones bajos)
        var_pattern = re.compile(r'\b[A-Z][A-Z0-9_]*\b')
        variables = var_pattern.findall(rhs)
        
        # Filtrar funciones conocidas
        functions = {'max', 'min', 'abs', 'round', 'ceil', 'floor', 'sqrt', 'mean', 'std'}
        return [v for v in variables if v not in functions]
    
    
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
            
            # NUEVO: Verificar que todas las variables necesarias existan
            missing_vars = []
            for var in self._extract_dependencies(expression):
                if var not in all_variables:
                    missing_vars.append(var)
            
            if missing_vars:
                logger.debug(f"Cannot solve {output_var}, missing: {missing_vars}")
                return
            
            # Evaluate
            result = self._evaluate_expression(rhs, all_variables)
            
            if result is not None:
                # NUEVO: Validar resultado antes de guardarlo
                if self._is_valid_result(output_var, result):
                    endogenous_results[output_var] = result
                    variable_dict[output_var] = result
                    logger.debug(f"Calculated {output_var} = {result:.2f}")
                else:
                    logger.warning(f"Invalid result for {output_var}: {result}")
            
        except Exception as e:
            logger.debug(f"Could not solve equation {equation.expression}: {e}")
            
    def _is_valid_result(self, var_name, value):
        """Validar que el resultado sea razonable"""
        # Evitar valores negativos para ciertas variables
        non_negative_vars = [
            'TPV', 'QPL', 'IPF', 'II', 'IT', 'TCAE', 'VPC', 
            'TPPRO', 'DI', 'FU', 'PE', 'NSC', 'PM'
        ]
        
        if var_name in non_negative_vars and value < 0:
            return False
        
        # Evitar valores extremos
        if abs(value) > 1e9:
            return False
        
        # Validar porcentajes
        percentage_vars = ['FU', 'PE', 'NSC', 'PM', 'MB', 'NR']
        if var_name in percentage_vars and (value < -1 or value > 2):
            return False
        
        return True

    def _preprocess_expression(self, expression):
        """Preprocess expression to handle special cases"""
        
        # Remove summation symbol
        expression = expression.replace('∑', '')
        
        # Replace random() with actual value
        expression = expression.replace('random()', str(random.random()))
        
        # AGREGAR: Manejar funciones especiales
        # Reemplazar mean(lista) por el valor calculado
        if 'mean(' in expression:
            # Este es un caso especial que se maneja en el contexto
            pass
        
        # Reemplazar DH si es una lista por su promedio
        if 'mean(DH)' in expression:
            expression = expression.replace('mean(DH)', 'DPH')
        
        # Handle max/min functions
        expression = re.sub(r'max\s*\(', 'max(', expression)
        expression = re.sub(r'min\s*\(', 'min(', expression)
        
        # AGREGAR: Manejar sqrt, ceil, floor
        expression = re.sub(r'sqrt\s*\(', 'sqrt(', expression)
        expression = re.sub(r'ceil\s*\(', 'ceil(', expression)
        expression = re.sub(r'floor\s*\(', 'floor(', expression)
        
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
            
            # Safe evaluation context - EXPANDIR ESTO
            safe_dict = {
                '__builtins__': {},
                'max': max,
                'min': min,
                'abs': abs,
                'round': round,
                'pow': pow,
                'sum': sum,
                # AGREGAR ESTAS FUNCIONES:
                'sqrt': lambda x: x ** 0.5,
                'ceil': lambda x: int(x) + (1 if x > int(x) else 0),
                'floor': lambda x: int(x),
                'mean': lambda x: sum(x) / len(x) if isinstance(x, list) else x,
                'std': lambda x: np.std(x) if isinstance(x, list) else 0,
                'exp': lambda x: 2.71828 ** x,
                'log': lambda x: np.log(x) if x > 0 else 0,
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
        
        
        # AGREGAR: Verificación de variables base antes de calcular
        required_base_vars = ['PVP', 'CPD', 'CUIP', 'CFD', 'SE', 'GMM', 'CPROD']
        missing_base = [v for v in required_base_vars if v not in variable_dict]
        
        if missing_base:
            logger.warning(f"Missing base variables: {missing_base}")
            # Usar defaults mínimos
            defaults = {
                'PVP': 15.50,
                'CPD': 85,
                'CUIP': 8.20,
                'CFD': 1800,
                'SE': 48000,
                'GMM': 3500,
                'CPROD': 3000
            }
            for var in missing_base:
                if var in defaults:
                    variable_dict[var] = defaults[var]
        
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
            tcae = min(cpd * 0.95, max_clients_by_demand)
            # Validar resultado
            if tcae < 0 or tcae > cpd * 1.5:
                tcae = cpd * 0.9
            endogenous_results['TCAE'] = tcae
        
        # Calculate TPV (Total Productos Vendidos)
        if 'TPV' not in endogenous_results:
            tcae = endogenous_results.get('TCAE', cpd * 0.95)
            ipf = variable_dict.get('IPF', 1000)
            ppl = endogenous_results.get('PPL', 0)
            
            # Límites más realistas
            max_by_clients = tcae * vpc
            max_by_inventory = ipf + ppl
            max_by_demand = de
            max_by_capacity = cprod * 0.9
            
            tpv = min(max_by_clients, max_by_inventory, max_by_demand, max_by_capacity)
            tpv = max(0, tpv)  # No negativo
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

    def _validate_critical_variables(self, endogenous_results, variable_dict):
        """Validar coherencia entre variables críticas"""
        
        # TPV no puede exceder inventario + producción
        tpv = endogenous_results.get('TPV', 0)
        ipf = variable_dict.get('IPF', 0)
        ppl = endogenous_results.get('PPL', 0)
        
        if tpv > ipf + ppl:
            endogenous_results['TPV'] = ipf + ppl
            logger.debug(f"Adjusted TPV to match inventory constraints")
        
        # Producción no puede exceder capacidad
        qpl = endogenous_results.get('QPL', 0)
        cprod = variable_dict.get('CPROD', 3000)
        
        if qpl > cprod:
            endogenous_results['QPL'] = cprod
            endogenous_results['PPL'] = cprod
            endogenous_results['TPPRO'] = cprod
            logger.debug(f"Adjusted production to capacity limit")
        
        # Margen de ganancia debe ser razonable
        gt = endogenous_results.get('GT', 0)
        it = endogenous_results.get('IT', 1)
        
        if it > 0:
            margin = gt / it
            if margin < -0.5:  # Pérdida mayor al 50%
                # Ajustar gastos
                max_loss = it * 0.3  # Máximo 30% de pérdida
                endogenous_results['TG'] = it + max_loss
                endogenous_results['GT'] = -max_loss
                logger.debug(f"Adjusted losses to reasonable level")
            elif margin > 0.8:  # Ganancia mayor al 80%
                logger.info(f"High profit margin detected: {margin:.2%}")
    
    def _validate_simulation_results(self, endogenous_results, variable_dict):
        """Validate simulation results for coherence and realism"""
        
        # Validaciones más específicas y correcciones automáticas
        validations = []
        
        # Get key metrics con valores por defecto seguros
        tpv = endogenous_results.get('TPV', 0)
        qpl = endogenous_results.get('QPL', 0)
        it = endogenous_results.get('IT', 0)
        gt = endogenous_results.get('GT', 0)
        tg = endogenous_results.get('TG', 0)
        dph = variable_dict.get('DPH', 2500)
        ddp = endogenous_results.get('DDP', dph)
        pvp = variable_dict.get('PVP', 15.50)
        cprod = variable_dict.get('CPROD', 3000)
        cuip = variable_dict.get('CUIP', 7.50)
        ipf = endogenous_results.get('IPF', 0)
        ii = endogenous_results.get('II', 0)
        
        # Validación 1: Producción debe ser coherente con ventas
        if pvp is None or pvp == 0:
            pvp = 15.50
            variable_dict['PVP'] = pvp
            validations.append("Set default PVP value: 15.50")
            logger.warning("PVP was missing, set to default value")
        
        
        if qpl > 0 and tpv > 0:
            production_sales_ratio = qpl / tpv
            if production_sales_ratio > 2:  # Produciendo más del doble de lo que vende
                logger.warning(f'Alta sobreproducción: QPL={qpl:.0f}, TPV={tpv:.0f}, ratio={production_sales_ratio:.2f}')
                # Ajustar producción a un máximo de 20% sobre ventas
                new_qpl = min(qpl, tpv * 1.2)
                endogenous_results['QPL'] = new_qpl
                endogenous_results['PPL'] = new_qpl
                endogenous_results['TPPRO'] = new_qpl
                validations.append(f"Adjusted QPL from {qpl:.0f} to {new_qpl:.0f}")
        
        # Validación 2: Ventas no pueden exceder producción + inventario inicial
        max_possible_sales = qpl + variable_dict.get('IPF', 0)
        if tpv > max_possible_sales:
            logger.warning(f'Ventas exceden disponibilidad: TPV={tpv:.0f}, Max={max_possible_sales:.0f}')
            endogenous_results['TPV'] = max_possible_sales
            # Recalcular ingresos
            endogenous_results['IT'] = endogenous_results['TPV'] * pvp
            validations.append(f"Capped TPV to available inventory")
        
        # Validación 3: Margen de ganancia realista
        if it > 0:
            margin = gt / it
            
            # Margen esperado entre -10% y 40%
            if margin < -0.1:
                logger.warning(f'Pérdida excesiva: {margin:.2%}')
                # Limitar pérdida al 10%
                max_costs = it * 1.1
                if tg > max_costs:
                    endogenous_results['TG'] = max_costs
                    endogenous_results['GT'] = it - max_costs
                    
                    # Ajustar componentes de costo proporcionalmente
                    go = endogenous_results.get('GO', 0)
                    gg = endogenous_results.get('GG', 0)
                    if go + gg > 0:
                        ratio = max_costs / (go + gg)
                        endogenous_results['GO'] = go * ratio
                        endogenous_results['GG'] = gg * ratio
                    
                    validations.append(f"Limited losses to 10% of revenue")
            
            elif margin > 0.4:
                logger.info(f'Margen alto pero posible: {margin:.2%}')
                # No ajustar, pero registrar
                validations.append(f"High but valid margin: {margin:.2%}")
        
        # Validación 4: Ventas vs Demanda
        if tpv > ddp * 1.2:  # No vender más del 120% de la demanda proyectada
            logger.warning(f'Ventas muy superiores a demanda: TPV={tpv:.0f}, DDP={ddp:.0f}')
            new_tpv = ddp * 1.1  # Máximo 110% de demanda
            endogenous_results['TPV'] = new_tpv
            endogenous_results['IT'] = new_tpv * pvp
            validations.append(f"Adjusted TPV to match demand")
        
        # Validación 5: Coherencia de costos
        ctai = endogenous_results.get('CTAI', 0)
        if it > 0 and ctai > it * 0.7:  # Costo de insumos no debe ser >70% de ingresos
            logger.warning(f'Costo de insumos muy alto: {ctai:.0f} ({ctai/it:.2%} de ingresos)')
            # Verificar si el cálculo es correcto
            expected_ctai = qpl * variable_dict.get('CINSP', 1.02) * cuip
            if abs(ctai - expected_ctai) > 1:
                endogenous_results['CTAI'] = expected_ctai
                validations.append(f"Corrected CTAI calculation")
        
        # Validación 6: Nivel de servicio
        nsc = endogenous_results.get('NSC', 0)
        if nsc < 0.5:
            logger.warning(f'Nivel de servicio muy bajo: {nsc:.2%}')
            # Recalcular basado en ventas y demanda
            if ddp > 0:
                endogenous_results['NSC'] = min(1.0, tpv / ddp)
        elif nsc > 1.0:
            endogenous_results['NSC'] = 1.0
            validations.append("Capped NSC to 100%")
        
        # Validación 7: Inventarios no negativos
        if ipf < 0:
            endogenous_results['IPF'] = 0
            validations.append("Corrected negative IPF")
        
        if ii < 0:
            endogenous_results['II'] = 0
            validations.append("Corrected negative II")
        
        # Validación 8: Capacidad de producción
        if qpl > cprod:
            endogenous_results['QPL'] = cprod
            endogenous_results['PPL'] = cprod
            endogenous_results['TPPRO'] = cprod
            validations.append(f"Capped production to capacity: {cprod:.0f}")
        
        # Validación 9: Factor de utilización
        fu = endogenous_results.get('FU', 0)
        if fu > 1.0:
            endogenous_results['FU'] = 1.0
            validations.append("Capped FU to 100%")
        elif fu < 0:
            endogenous_results['FU'] = 0
            validations.append("Corrected negative FU")
        
        # Validación 10: Productividad por empleado
        pe = endogenous_results.get('PE', 0)
        nepp = variable_dict.get('NEPP', 15)
        if pe < 0:
            endogenous_results['PE'] = qpl / max(nepp, 1)
            validations.append("Corrected PE calculation")
        
        # Validación 11: Demanda insatisfecha
        di = endogenous_results.get('DI', 0)
        expected_di = max(0, ddp - tpv)
        if abs(di - expected_di) > 1:
            endogenous_results['DI'] = expected_di
            validations.append("Corrected DI calculation")
        
        # Validación 12: Márgenes y ratios financieros
        mb = endogenous_results.get('MB', 0)
        nr = endogenous_results.get('NR', 0)
        
        # Margen bruto
        if it > 0:
            expected_mb = (it - ctai) / it
            if abs(mb - expected_mb) > 0.01:
                endogenous_results['MB'] = max(0, min(1, expected_mb))
                validations.append("Corrected MB calculation")
        
        # Margen neto
        if it > 0:
            expected_nr = gt / it
            if abs(nr - expected_nr) > 0.01:
                endogenous_results['NR'] = max(-1, min(1, expected_nr))
                validations.append("Corrected NR calculation")
        
        # Log de validaciones aplicadas
        if validations:
            logger.info(f"Applied {len(validations)} validations:")
            for v in validations:
                logger.debug(f"  - {v}")

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