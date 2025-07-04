# utils/variable_mapper.py
"""
NUEVO ARCHIVO: Sistema de mapeo completo de variables desde base de datos.
Extrae y mapea todas las variables necesarias para las ecuaciones.
"""
import logging
import json
from typing import Dict, Any, List, Optional
from decimal import Decimal
from django.db.models import Q
from questionary.models import Answer, QuestionaryResult
from variable.models import Variable

logger = logging.getLogger(__name__)


class VariableMapper:
    """Mapeador completo de variables desde base de datos"""
    
    def __init__(self):
        # Mapeo de variables críticas con sus nombres alternativos
        self.variable_mapping = {
            # ================================================================
            # VARIABLES FINANCIERAS BÁSICAS
            # ================================================================
            'PVP': ['precio_venta', 'precio_unitario', 'precio'],
            'CUIP': ['costo_unitario', 'costo_insumo', 'costo_material'],
            'CFD': ['costos_fijos', 'gastos_fijos_diarios'],
            'SE': ['salarios', 'sueldos_empleados', 'nomina'],
            'GMM': ['gastos_marketing', 'marketing_mensual'],
            'PC': ['precio_competencia', 'precio_mercado'],
            
            # ================================================================
            # VARIABLES FINANCIERAS CALCULADAS (CRÍTICAS)
            # ================================================================
            'GT': ['ganancias_totales', 'ganancia_total', 'utilidad_neta', 'profit'],
            'IT': ['ingresos_totales', 'ventas_totales', 'revenue'],
            'TG': ['total_gastos', 'gastos_totales', 'costos_totales'],
            'NR': ['nivel_rentabilidad', 'margen_neto', 'rentabilidad', 'profit_margin'],
            'MB': ['margen_bruto', 'gross_margin', 'margen_contribucion'],
            'RI': ['retorno_inversion', 'roi', 'return_investment'],
            'IE': ['ingresos_esperados', 'expected_revenue', 'ingresos_proyectados'],
            'IB': ['ingreso_bruto', 'gross_income', 'margen_bruto_total'],
            'CVU': ['costo_variable_unitario', 'variable_cost_per_unit'],
            'RVE': ['rentabilidad_vs_esperada', 'performance_vs_expected'],
            
            # ================================================================
            # COSTOS CALCULADOS (CRÍTICOS)
            # ================================================================
            'CTAI': ['costo_total_adquisicion_insumos', 'gasto_materias_primas'],
            'GO': ['gastos_operativos', 'costos_operacion_diaria'],
            'GG': ['gastos_generales', 'overhead_costs'],
            'CTTL': ['costo_total_transporte', 'gastos_distribucion'],
            'CA': ['costo_almacenamiento', 'storage_cost'],
            'CHO': ['costo_horas_ociosas', 'idle_time_cost'],
            'CPP': ['costo_promedio_produccion', 'average_production_cost'],
            'CPV': ['costo_promedio_venta', 'average_selling_cost'],
            'CUP': ['costo_unitario_produccion', 'unit_production_cost'],
            'PVR': ['precio_venta_recomendado', 'recommended_selling_price'],
            'CTM': ['costo_total_mermas', 'total_waste_cost'],
            'MP': ['merma_produccion', 'production_waste'],
            'MI': ['merma_inventario', 'inventory_waste'],
            
            # ================================================================
            # VARIABLES OPERATIVAS BÁSICAS
            # ================================================================
            'NEPP': ['numero_empleados', 'empleados_produccion'],
            'MLP': ['minutos_laborables', 'tiempo_trabajo_dia'],
            'TPE': ['tiempo_por_unidad', 'tiempo_produccion_unitario'],
            'CPPL': ['capacidad_lote', 'unidades_por_lote'],
            'CINSP': ['conversion_insumos', 'factor_conversion'],
            'CPROD': ['capacidad_produccion', 'capacidad_maxima'],
            'CPD': ['clientes_por_dia', 'clientes_diarios'],
            'VPC': ['ventas_por_cliente', 'unidades_por_cliente'],
            'VPC_BASE': ['ventas_cliente_base', 'base_sales_per_customer'],
            
            # ================================================================
            # VARIABLES DE PRODUCCIÓN Y VENTAS (CRÍTICAS)
            # ================================================================
            'TPV': ['total_productos_vendidos', 'ventas_productos', 'productos_vendidos'],
            'QPL': ['cantidad_producida', 'produccion_diaria', 'litros_producidos'],
            'PPL': ['productos_producidos_lote', 'production_per_batch'],
            'TCAE': ['total_clientes_atendidos', 'customers_served'],
            'TPPRO': ['total_productos_producidos', 'total_production'],
            'NSC': ['nivel_servicio_cliente', 'service_level', 'satisfaccion_demanda'],
            'PE': ['productividad_empleados', 'eficiencia_personal', 'productivity'],
            'FU': ['factor_utilizacion', 'utilizacion_capacidad', 'capacity_utilization'],
            'EP': ['eficiencia_produccion', 'production_efficiency'],
            'EOG': ['eficiencia_operativa_global', 'oee', 'overall_equipment_effectiveness'],
            'IDG': ['indice_desempeno_global', 'kpi_global', 'global_performance_index'],
            'DI': ['demanda_insatisfecha', 'unmet_demand'],
            
            # ================================================================
            # VARIABLES DE INVENTARIO (CRÍTICAS)
            # ================================================================
            'IPF': ['inventario_productos_finales', 'finished_goods_inventory'],
            'II': ['inventario_insumos', 'raw_materials_inventory'],
            'IOP': ['inventario_objetivo_productos', 'target_finished_inventory'],
            'IOI': ['inventario_objetivo_insumos', 'target_raw_inventory'],
            'PI': ['pedido_insumos', 'raw_materials_order'],
            'UII': ['uso_inventario_insumos', 'raw_materials_usage'],
            'RTI': ['rotacion_inventario', 'inventory_turnover'],
            'DPL': ['dias_plazo_entrega', 'lead_time'],
            'TR': ['tiempo_reposicion', 'ciclo_reposicion'],
            'CMIPF': ['capacidad_maxima_inventario', 'limite_almacen'],
            
            # ================================================================
            # VARIABLES DE DEMANDA (CRÍTICAS)
            # ================================================================
            'DH': ['demanda_historica', 'datos_historicos_demanda', 'historial_ventas'],
            'DPH': ['demanda_promedio_historica', 'demanda_media', 'average_demand'],
            'DSD': ['desviacion_estandar_demanda', 'variabilidad_demanda'],
            'DDP': ['demanda_diaria_proyectada', 'demanda_esperada_dia'],
            'DE': ['demanda_esperada', 'expected_demand'],
            'ED': ['estacionalidad_demanda', 'seasonal_factor'],
            'CVD': ['coeficiente_variacion_demanda', 'demand_cv'],
            'POD': ['produccion_objetivo_diaria', 'daily_target_production'],
            'DT': ['demanda_total', 'total_demand'],
            
            # ================================================================
            # VARIABLES DE RECURSOS HUMANOS
            # ================================================================
            'HO': ['horas_ociosas', 'tiempo_improductivo'],
            'HNP': ['horas_necesarias_produccion', 'tiempo_requerido'],
            'ES': ['eficiencia_estandar', 'eficiencia_objetivo'],
            'EE': ['eficiencia_esperada', 'eficiencia_meta'],
            'HAU': ['horas_uso_diario', 'tiempo_operacion'],
            'HTP': ['horas_totales_posibles', 'tiempo_maximo'],
            'HTO': ['horas_totales_operacion', 'total_operating_hours'],
            'IRP': ['indice_rotacion_personal', 'employee_turnover'],
            'PPE': ['productividad_por_empleado', 'productivity_per_employee'],
            'CCE': ['costo_capacitacion_empleado', 'training_cost_per_employee'],
            'TAU': ['tasa_ausentismo', 'absenteeism_rate'],
            'CLL': ['costo_laboral_litro', 'labor_cost_per_liter'],
            
            # ================================================================
            # VARIABLES DE CALIDAD Y EFICIENCIA
            # ================================================================
            'QC': ['calidad_produccion', 'porcentaje_calidad'],
            'QMAX': ['cantidad_maxima_producible', 'max_production_capacity'],
            'ISC': ['indice_satisfaccion_cliente', 'customer_satisfaction_index'],
            'PED': ['punto_equilibrio_diario', 'daily_breakeven_point'],
            
            # ================================================================
            # VARIABLES DE TRANSPORTE Y LOGÍSTICA
            # ================================================================
            'CUTRANS': ['costo_transporte_unitario', 'costo_logistica'],
            'CTPLV': ['capacidad_transporte', 'vehiculos_capacidad'],
            
            # ================================================================
            # VARIABLES DE MARKETING
            # ================================================================
            'EM': ['efectividad_marketing', 'marketing_effectiveness'],
            'CUAC': ['costo_unitario_adquisicion_clientes', 'customer_acquisition_cost'],
            'FC': ['frecuencia_compra', 'purchase_frequency'],
            'PM': ['participacion_mercado', 'market_share'],
            'IC': ['indice_competitividad', 'competitiveness_index'],
            'ROIA': ['roi_inversion_publicitaria', 'advertising_roi'],
            'CPL_MKT': ['costo_por_lead', 'cost_per_lead'],
            'LG': ['leads_generados', 'generated_leads'],
            'TCL': ['tasa_conversion_leads', 'lead_conversion_rate'],
            'NC': ['nuevos_clientes', 'new_customers'],
            'AEC': ['alcance_efectivo_campanas', 'effective_campaign_reach'],
            'ALC': ['alcance_campanas', 'campaign_reach'],
            'RMI': ['reconocimiento_marca_indice', 'brand_recognition_index'],
            'MRE': ['marca_reconocimiento_espontaneo', 'spontaneous_brand_recognition'],
            'MRA': ['marca_reconocimiento_asistido', 'assisted_brand_recognition'],
            
            # ================================================================
            # VARIABLES DE COMPETENCIA
            # ================================================================
            'VCP': ['ventaja_competitiva_precio', 'price_competitive_advantage'],
            'PMR': ['participacion_mercado_relativa', 'relative_market_share'],
            'PMC': ['participacion_mercado_competidor', 'competitor_market_share'],
            'IDP': ['indice_diferenciacion_producto', 'product_differentiation_index'],
            'CDP': ['calidad_diferenciada_producto', 'differentiated_product_quality'],
            'CCP': ['costo_competitivo_producto', 'competitive_product_cost'],
            'CSP': ['servicio_competitivo_producto', 'competitive_product_service'],
            'EEC': ['efectividad_estrategia_competitiva', 'competitive_strategy_effectiveness'],
            'AMEN': ['amenaza_competitiva', 'competitive_threat'],
            'NPC': ['numero_productos_competencia', 'number_competing_products'],
            'ICC': ['intensidad_campanas_competencia', 'competitor_campaign_intensity'],
            
            # ================================================================
            # VARIABLES DE MANTENIMIENTO
            # ================================================================
            'DISP': ['disponibilidad_equipos', 'equipment_availability'],
            'TP': ['tiempo_parada', 'downtime'],
            'OEE': ['efectividad_general_equipos', 'overall_equipment_effectiveness'],
            'CML': ['costo_mantenimiento_litro', 'maintenance_cost_per_liter'],
            'CRP': ['costo_reparaciones', 'repair_costs'],
            'CREP': ['costo_repuestos', 'spare_parts_cost'],
            'CMOM': ['costo_mano_obra_mantenimiento', 'maintenance_labor_cost'],
            'NF': ['numero_fallas', 'number_failures'],
            'FF': ['frecuencia_fallas', 'failure_frequency'],
            'RMP': ['ratio_mantenimiento_preventivo', 'preventive_maintenance_ratio'],
            'HMP': ['horas_mantenimiento_preventivo', 'preventive_maintenance_hours'],
            'HMC': ['horas_mantenimiento_correctivo', 'corrective_maintenance_hours'],
            
            # ================================================================
            # VARIABLES DE ABASTECIMIENTO
            # ================================================================
            'CTA': ['costo_total_adquisicion', 'total_acquisition_cost'],
            'CC': ['costo_compra', 'purchase_cost'],
            'CTI': ['costo_transporte_insumos', 'raw_materials_transport_cost'],
            'CAL': ['costo_almacenamiento', 'storage_cost'],
            'TPEP': ['tiempo_promedio_entrega_proveedores', 'average_supplier_delivery_time'],
            'TE1': ['tiempo_entrega_proveedor_1', 'supplier_1_delivery_time'],
            'TE2': ['tiempo_entrega_proveedor_2', 'supplier_2_delivery_time'],
            'TE3': ['tiempo_entrega_proveedor_3', 'supplier_3_delivery_time'],
            'P1': ['peso_proveedor_1', 'supplier_1_weight'],
            'P2': ['peso_proveedor_2', 'supplier_2_weight'],
            'P3': ['peso_proveedor_3', 'supplier_3_weight'],
            'ICP': ['indice_calidad_proveedores', 'supplier_quality_index'],
            'RIMP': ['rotacion_inventario_materias_primas', 'raw_materials_inventory_turnover'],
            'IIF': ['inventario_final_insumos', 'final_raw_materials_inventory'],
            'CDE': ['cumplimiento_entregas', 'delivery_compliance'],
            'EAT': ['entregas_tiempo', 'on_time_deliveries'],
            'TTEP': ['total_entregas_programadas', 'total_scheduled_deliveries'],
            
            # ================================================================
            # VARIABLES DE DISTRIBUCIÓN
            # ================================================================
            'ERE': ['eficiencia_rutas_entrega', 'delivery_route_efficiency'],
            'KMT': ['kilometros_totales', 'total_kilometers'],
            'CDL': ['costo_distribucion_litro', 'distribution_cost_per_liter'],
            'CCF': ['costo_cadena_frio', 'cold_chain_cost'],
            'CLOG': ['costo_logistico', 'logistics_cost'],
            'TPEC': ['tiempo_promedio_entrega_cliente', 'average_customer_delivery_time'],
            'TTED': ['tiempo_total_entregas_distribucion', 'total_distribution_delivery_time'],
            'NE': ['numero_entregas', 'number_deliveries'],
            'ICE': ['indice_calidad_entrega', 'delivery_quality_index'],
            'TCFO': ['temperatura_cadena_frio_objetivo', 'target_cold_chain_temperature'],
            'TCF': ['temperatura_cadena_frio', 'cold_chain_temperature'],
            'TEO': ['tiempo_entrega_objetivo', 'target_delivery_time'],
            'TER': ['tiempo_entrega_real', 'actual_delivery_time'],
            'TD': ['tasa_devoluciones', 'return_rate'],
            'PD': ['productos_devueltos', 'returned_products'],
            
            # ================================================================
            # VARIABLES DE COMPONENTES Y MATERIALES
            # ================================================================
            'CMP1': ['costo_componente_1', 'component_1_cost'],
            'V1': ['volumen_componente_1', 'component_1_volume'],
            'CMP2': ['costo_componente_2', 'component_2_cost'],
            'V2': ['volumen_componente_2', 'component_2_volume'],
            'CMP3': ['costo_componente_3', 'component_3_cost'],
            'V3': ['volumen_componente_3', 'component_3_volume'],
            
            # ================================================================
            # VARIABLES DE CAPITAL Y INVERSIÓN
            # ================================================================
            'CCAP': ['costo_capital', 'inversion_capital'],
        }
        
        # Valores por defecto mejorados (AGREGADO EOG)
        self.enhanced_defaults = {
            # FINANCIERAS BÁSICAS
            'PVP': 15.50, 'CUIP': 8.20, 'CFD': 1800, 'SE': 48000, 'GMM': 3500, 'PC': 15.80,
            
            # FINANCIERAS CALCULADAS
            'GT': 32600, 'IT': 37200, 'TG': 4600, 'NR': 0.876, 'MB': 0.43, 'RI': 7.09,
            'IE': 38750, 'IB': 15950, 'CVU': 8.50, 'RVE': 1.0,
            
            # COSTOS CALCULADOS
            'CTAI': 21250, 'GO': 3400, 'GG': 1200, 'CTTL': 350, 'CA': 150, 'CHO': 80,
            'CPP': 1.36, 'CPV': 1.92, 'CUP': 1.45, 'PVR': 16.20, 'CTM': 125,
            'MP': 50, 'MI': 20,
            
            # OPERATIVAS BÁSICAS
            'NEPP': 15, 'MLP': 480, 'TPE': 45, 'CPPL': 500, 'CINSP': 1.05, 'CPROD': 3000,
            'CPD': 85, 'VPC': 30, 'VPC_BASE': 29.5,
            
            # PRODUCCIÓN Y VENTAS
            'TPV': 2400, 'QPL': 2500, 'PPL': 2500, 'TCAE': 80, 'TPPRO': 2500,
            'NSC': 0.96, 'PE': 0.85, 'FU': 0.83, 'EP': 0.91, 'EOG': 0.68, 'IDG': 0.78,
            'DI': 100,
            
            # INVENTARIO
            'IPF': 1000, 'II': 5000, 'IOP': 2000, 'IOI': 7500, 'PI': 2625, 'UII': 2625,
            'RTI': 36.5, 'DPL': 3, 'TR': 3, 'CMIPF': 20000,
            
            # DEMANDA
            'DH': [2400, 2500, 2600, 2450, 2550], 'DPH': 2500, 'DSD': 250,
            'DDP': 2500, 'DE': 2650, 'ED': 1.0, 'CVD': 0.10, 'POD': 2600, 'DT': 2500,
            
            # RECURSOS HUMANOS
            'HO': 62, 'HNP': 318, 'ES': 0.85, 'EE': 0.80, 'HAU': 8, 'HTP': 24,
            'HTO': 24, 'IRP': 8.0, 'PPE': 166.7, 'CCE': 133.3, 'TAU': 33.3, 'CLL': 0.64,
            
            # CALIDAD Y EFICIENCIA
            'QC': 0.95, 'QMAX': 3000, 'ISC': 0.85, 'PED': 1800,
            
            # TRANSPORTE
            'CUTRANS': 0.35, 'CTPLV': 1500,
            
            # MARKETING
            'EM': 1.2, 'CUAC': 70, 'FC': 1.0, 'PM': 8.5, 'IC': 0.7, 'ROIA': 250,
            'CPL_MKT': 60, 'LG': 50, 'TCL': 30, 'NC': 15, 'AEC': 3000, 'ALC': 10000,
            'RMI': 35, 'MRE': 25, 'MRA': 45,
            
            # COMPETENCIA
            'VCP': -1.9, 'PMR': 0.28, 'PMC': 30, 'IDP': 8.0, 'CDP': 7.5, 'CCP': 8.0,
            'CSP': 8.5, 'EEC': 7.8, 'AMEN': 6, 'NPC': 12, 'ICC': 6,
            
            # MANTENIMIENTO
            'DISP': 0.92, 'TP': 2, 'OEE': 0.62, 'CML': 0.48, 'CRP': 500, 'CREP': 300,
            'CMOM': 400, 'NF': 1, 'FF': 41.7, 'RMP': 0.75, 'HMP': 1.5, 'HMC': 0.5,
            
            # ABASTECIMIENTO
            'CTA': 19000, 'CC': 18000, 'CTI': 500, 'CAL': 200, 'TPEP': 2.7,
            'TE1': 2, 'TE2': 3, 'TE3': 4, 'P1': 0.5, 'P2': 0.3, 'P3': 0.2,
            'ICP': 8.2, 'RIMP': 52.6, 'IIF': 8000, 'CDE': 93.3, 'EAT': 28, 'TTEP': 30,
            
            # DISTRIBUCIÓN
            'ERE': 9.6, 'KMT': 250, 'CDL': 0.46, 'CCF': 300, 'CLOG': 200,
            'TPEC': 0.32, 'TTED': 8, 'NE': 25, 'ICE': 0.90, 'TCFO': 4.0, 'TCF': 4.2,
            'TEO': 0.3, 'TER': 0.32, 'TD': 1.04, 'PD': 25,
            
            # COMPONENTES
            'CMP1': 8.5, 'V1': 1250, 'CMP2': 7.8, 'V2': 750, 'CMP3': 8.2, 'V3': 500,
            
            # CAPITAL
            'CCAP': 1000,
        }
    
    
    
    
    
    def extract_all_variables(self, questionary_result: QuestionaryResult) -> Dict[str, Any]:
        """Extraer todas las variables necesarias desde la base de datos"""
        
        extracted_vars = {}
        
        # 1. Extraer desde respuestas del cuestionario
        questionary_vars = self._extract_from_questionary(questionary_result)
        extracted_vars.update(questionary_vars)
        
        # 2. Extraer desde variables del sistema (SIN fk_business)
        system_vars = self._extract_from_variable_system_fixed(questionary_result)
        extracted_vars.update(system_vars)
        
        # 3. Calcular variables derivadas
        derived_vars = self._calculate_derived_variables(extracted_vars)
        extracted_vars.update(derived_vars)
        
        # 4. Aplicar valores por defecto para variables faltantes
        complete_vars = self._apply_enhanced_defaults(extracted_vars)
        
        # 5. Validar y limpiar variables
        validated_vars = self._validate_and_clean_variables(complete_vars)
        
        logger.info(f"Extracted {len(validated_vars)} variables from database")
        return validated_vars
    
    def _extract_from_questionary(self, questionary_result: QuestionaryResult) -> Dict[str, Any]:
        """Extraer variables desde las respuestas del cuestionario"""
        
        variables = {}
        
        try:
            answers = Answer.objects.filter(
                fk_questionary_result=questionary_result,
                is_active=True
            ).select_related('fk_question__fk_variable')
            
            for answer in answers:
                # Extraer por variable asociada
                if answer.fk_question.fk_variable:
                    var_initials = answer.fk_question.fk_variable.initials
                    value = self._parse_answer_value(answer.answer, var_initials)
                    if value is not None:
                        variables[var_initials] = value
                
                # Extraer por texto de pregunta
                question_text = answer.fk_question.question.lower()
                mapped_var = self._map_question_to_variable(question_text)
                if mapped_var and mapped_var not in variables:
                    value = self._parse_answer_value(answer.answer, mapped_var)
                    if value is not None:
                        variables[mapped_var] = value
            
            logger.info(f"Extracted {len(variables)} variables from questionary answers")
            
        except Exception as e:
            logger.error(f"Error extracting from questionary: {str(e)}")
        
        return variables
    
    def _extract_from_variable_system_fixed(self, questionary_result: QuestionaryResult) -> Dict[str, Any]:
        """CORREGIDO: Extraer variables del sistema SIN usar fk_business"""
        
        variables = {}
        
        try:
            # NUEVO: Cargar variables desde variable_test_data
            from variable.data.variable_test_data import variables_data
            logger.info(f"Cargando {len(variables_data)} variables desde variable_test_data")
            
            for var_data in variables_data:
                initials = var_data['initials']
                default_value = var_data.get('default_value', 0)
                
                if initials in self.variable_mapping:
                    try:
                        value = float(default_value) if default_value is not None else 0.0
                        variables[initials] = value
                    except (ValueError, TypeError):
                        variables[initials] = 0.0
            
            logger.info(f"Cargadas {len(variables)} variables desde variable_test_data")
            
        except ImportError:
            logger.warning("No se pudo cargar variable_test_data")
            # Fallback al código original
            try:
                product = questionary_result.fk_questionary.fk_product
                business = product.fk_business
                
                system_variables = Variable.objects.filter(is_active=True)
                
                for sys_var in system_variables:
                    if sys_var.initials in self.variable_mapping:
                        if hasattr(sys_var, 'default_value') and sys_var.default_value:
                            try:
                                value = float(sys_var.default_value)
                                variables[sys_var.initials] = value
                            except (ValueError, TypeError):
                                pass
                
                logger.info(f"Extracted {len(variables)} variables from variable system")
                
            except Exception as e:
                logger.error(f"Error extracting from variable system: {str(e)}")
        
        return variables
    
    def _map_question_to_variable(self, question_text: str) -> Optional[str]:
        """Mapear texto de pregunta a variable usando nuestro diccionario"""
        
        question_lower = question_text.lower()
        
        for var_code, alternative_names in self.variable_mapping.items():
            for alt_name in alternative_names:
                if alt_name.lower() in question_lower:
                    return var_code
        
        # Mapeos específicos adicionales
        specific_mappings = {
            'precio': 'PVP',
            'costo': 'CUIP',
            'empleados': 'NEPP',
            'clientes': 'CPD',
            'inventario': 'IPF',
            'capacidad': 'CPROD',
            'demanda': 'DH',
            'marketing': 'GMM',
            'salarios': 'SE',
            'eficiencia': 'EOG'  # AGREGADO
        }
        
        for keyword, var_code in specific_mappings.items():
            if keyword in question_lower:
                return var_code
        
        return None
    
    def _parse_answer_value(self, answer_value: Any, variable_type: str) -> Optional[float]:
        """Parsear valor de respuesta según el tipo de variable"""
        
        if answer_value is None:
            return None
        
        try:
            # Si es una lista (como demanda histórica)
            if isinstance(answer_value, str) and (answer_value.startswith('[') or ',' in answer_value):
                if variable_type == 'DH':
                    # Para demanda histórica, retornar la lista parseada
                    parsed_list = self._parse_list_value(answer_value)
                    return parsed_list if parsed_list else None
                else:
                    # Para otras variables, tomar el primer valor o promedio
                    parsed_list = self._parse_list_value(answer_value)
                    return parsed_list[0] if parsed_list else None
            
            # Si es un string numérico
            if isinstance(answer_value, str):
                # Limpiar string
                cleaned = answer_value.strip().replace(',', '').replace('$', '').replace('%', '')
                
                # Buscar número en el string
                import re
                numbers = re.findall(r'[-+]?\d*\.?\d+', cleaned)
                if numbers:
                    value = float(numbers[0])
                    
                    # Ajustar según tipo de variable
                    if variable_type in ['ES', 'EE', 'QC', 'EOG'] and value > 1:
                        value = value / 100  # Convertir porcentaje a decimal
                    
                    return value
                return None
            
            # Si ya es un número
            if isinstance(answer_value, (int, float, Decimal)):
                value = float(answer_value)
                
                # Validar rangos según tipo
                if variable_type in ['ES', 'EE', 'QC', 'EOG'] and value > 1:
                    value = value / 100
                
                return value
            
            return None
            
        except (ValueError, TypeError, AttributeError) as e:
            logger.debug(f"Could not parse value '{answer_value}' for {variable_type}: {e}")
            return None
    
    def _parse_list_value(self, list_string: str) -> Optional[List[float]]:
        """Parsear string que contiene una lista de valores"""
        
        try:
            # Intentar JSON parse primero
            if list_string.strip().startswith('['):
                import json
                parsed = json.loads(list_string)
                return [float(x) for x in parsed if x is not None]
            
            # Parsear como CSV
            cleaned = list_string.replace('[', '').replace(']', '').strip()
            if ',' in cleaned:
                values = [x.strip() for x in cleaned.split(',')]
            elif ' ' in cleaned:
                values = [x.strip() for x in cleaned.split()]
            elif '\n' in cleaned:
                values = [x.strip() for x in cleaned.split('\n')]
            else:
                return None
            
            # Convertir a float
            numeric_values = []
            for val in values:
                if val:
                    try:
                        numeric_values.append(float(val))
                    except ValueError:
                        continue
            
            return numeric_values if numeric_values else None
            
        except Exception as e:
            logger.debug(f"Could not parse list value '{list_string}': {e}")
            return None
    
    def _calculate_derived_variables(self, base_variables: Dict[str, Any]) -> Dict[str, Any]:
        """Calcular variables derivadas desde las variables base"""
        
        derived = {}
        
        try:
            # AGREGADO: Calcular EOG si no existe
            if 'EOG' not in base_variables:
                # EOG = Disponibilidad × Rendimiento × Calidad
                availability = base_variables.get('ES', 0.85)  # Eficiencia estándar como disponibilidad
                performance = base_variables.get('PE', 0.85)   # Productividad como rendimiento  
                quality = base_variables.get('QC', 0.95)       # Calidad de producción
                
                derived['EOG'] = availability * performance * quality
                logger.info(f"Calculated EOG = {derived['EOG']:.3f}")
            
            # Resto de cálculos derivados existentes...
            # Capacidad de producción diaria si no está definida
            if 'CPROD' not in base_variables and all(k in base_variables for k in ['NEPP', 'MLP', 'TPE']):
                derived['CPROD'] = (base_variables['NEPP'] * base_variables['MLP'] / base_variables['TPE']) * 0.8
            
            # Más cálculos derivados...
            
            logger.info(f"Calculated {len(derived)} derived variables")
            
        except Exception as e:
            logger.error(f"Error calculating derived variables: {str(e)}")
        
        return derived

    def _apply_enhanced_defaults(self, extracted_variables: Dict[str, Any]) -> Dict[str, Any]:
        """✅ MEJORADO: Aplicar defaults asegurando que NR esté presente"""
        
        complete_vars = extracted_variables.copy()
        defaults_applied = 0
        
        # ✅ PRIORIDAD CRÍTICA: Asegurar variables financieras básicas primero
        critical_financial_vars = ['IT', 'TG', 'GT', 'NR']
        
        for var_code, default_value in self.enhanced_defaults.items():
            value_from_db = extracted_variables.get(var_code)
            if value_from_db is not None and value_from_db > 0:
                complete_vars[var_code] = value_from_db  # ✅ PRIORIZAR BD
            elif var_code not in complete_vars:
                complete_vars[var_code] = default_value  # Solo default si BD vacía
                
                # Log especial para variables críticas
                if var_code in critical_financial_vars:
                    logger.info(f"✅ Aplicado default crítico {var_code}: {default_value}")
        
        # ✅ VERIFICACIÓN FINAL: Recalcular NR si hay inconsistencias
        if 'NR' in complete_vars and complete_vars.get('GT') is not None and complete_vars.get('IT') is not None:
            calculated_nr = complete_vars['GT'] / max(complete_vars['IT'], 1)
            if abs(calculated_nr - complete_vars['NR']) > 0.1:  # Si hay gran diferencia
                complete_vars['NR'] = calculated_nr
                logger.info(f"✅ NR recalculado por consistencia: {calculated_nr}")
        
        # Ajustes contextuales
        complete_vars = self._apply_contextual_adjustments(complete_vars)
        
        logger.info(f"✅ Aplicados {defaults_applied} valores por defecto")
        return complete_vars
    
    def _apply_contextual_adjustments(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Aplicar ajustes contextuales a los valores por defecto"""
        
        adjusted_vars = variables.copy()
        
        # CORRECCIÓN CRÍTICA: Ajustar capacidad de producción según demanda
        if 'DPH' in adjusted_vars or 'DE' in adjusted_vars:
            expected_demand = adjusted_vars.get('DPH', adjusted_vars.get('DE', 2500))
            
            # Capacidad debe ser al menos 110% de la demanda esperada
            min_capacity = expected_demand * 1.1
            current_capacity = adjusted_vars.get('CPROD', 3000)
            
            if current_capacity < min_capacity:
                adjusted_vars['CPROD'] = min_capacity
                logger.info(f"Ajustada CPROD de {current_capacity} a {min_capacity} para cubrir demanda")
        
        # Ajustar capacidad de producción según número de empleados
        if adjusted_vars.get('NEPP', 0) > 0:
            required_capacity = adjusted_vars.get('CPROD', 3000)
            current_employees = adjusted_vars['NEPP']
            mLP = adjusted_vars.get('MLP', 480)
            tpe = adjusted_vars.get('TPE', 30)
            
            # Calcular empleados necesarios
            nepp_from_db = variables.get('NEPP')
            if nepp_from_db is not None and nepp_from_db > 0:
                adjusted_vars['NEPP'] = nepp_from_db  # ✅ USAR BD
            else:
                # Solo calcular si BD está vacía
                required_employees = max(10, int((required_capacity * tpe) / mLP))
                adjusted_vars['NEPP'] = required_employees
        
        # Ajustar costos fijos según tamaño de operación
        if adjusted_vars.get('NEPP', 0) > 20:  # Operación grande
            adjusted_vars['CFD'] = adjusted_vars.get('CFD', 1800) * 1.5
            adjusted_vars['GMM'] = adjusted_vars.get('GMM', 3500) * 1.3
        elif adjusted_vars.get('NEPP', 0) < 10:  # Operación pequeña
            adjusted_vars['CFD'] = adjusted_vars.get('CFD', 1800) * 0.7
            adjusted_vars['GMM'] = adjusted_vars.get('GMM', 3500) * 0.8
        
        # Ajustar inventarios según capacidad de producción
        if adjusted_vars.get('CPROD', 0) > 0:
            daily_production = adjusted_vars['CPROD']
            adjusted_vars['IPF'] = max(daily_production * 2, adjusted_vars.get('IPF', 1000))
            adjusted_vars['II'] = max(daily_production * 5, adjusted_vars.get('II', 5000))
        
        # Ajustar precios según contexto competitivo
        if adjusted_vars.get('PC', 0) > 0:  # Si hay precio de competencia
            comp_price = adjusted_vars['PC']
            # ✅ SOLUCIÓN: Verificar BD primero
            pvp_from_db = variables.get('PVP')
            if pvp_from_db is not None and pvp_from_db > 0:
                adjusted_vars['PVP'] = pvp_from_db  # ✅ USAR BD
            elif 'PVP' not in variables:
                adjusted_vars['PVP'] = comp_price * 0.98  # Solo ajustar si BD vacía
        
        return adjusted_vars
    
    def _validate_and_clean_variables(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Validar y limpiar variables extraídas"""
        
        cleaned_vars = {}
        validation_issues = []
        
        for var_code, value in variables.items():
            try:
                # Convertir a float si es posible
                if isinstance(value, (int, float, Decimal)):
                    clean_value = float(value)
                elif isinstance(value, list):
                    # Mantener listas para variables como DH
                    clean_value = [float(x) for x in value if x is not None]
                else:
                    clean_value = float(value)
                
                # Validaciones específicas por tipo de variable
                if var_code in ['ES', 'EE', 'QC', 'NSC']:  # Porcentajes/ratios
                    if clean_value < 0:
                        clean_value = 0
                    elif clean_value > 1:
                        clean_value = 1
                    
                elif var_code in ['NEPP', 'CPD', 'NC']:  # Enteros positivos
                    clean_value = max(1, int(clean_value))
                
                elif var_code in ['PVP', 'CUIP', 'CFD', 'SE', 'GMM']:  # Valores monetarios
                    clean_value = max(0, clean_value)
                
                elif var_code in ['MLP', 'TPE', 'HAU', 'HTP']:  # Tiempos
                    clean_value = max(0, clean_value)
                
                elif var_code in ['IPF', 'II', 'CPROD']:  # Inventarios/capacidades
                    clean_value = max(0, clean_value)
                
                # Validaciones de rango específicas
                if var_code == 'MLP' and clean_value > 1440:  # Máximo minutos por día
                    clean_value = 1440
                    validation_issues.append(f"{var_code} capped to daily maximum")
                
                if var_code == 'HAU' and clean_value > 24:  # Máximo horas por día
                    clean_value = 24
                    validation_issues.append(f"{var_code} capped to daily maximum")
                
                if var_code == 'TPE' and clean_value > 480:  # Tiempo por unidad muy alto
                    clean_value = 480
                    validation_issues.append(f"{var_code} seems excessive, capped")
                
                cleaned_vars[var_code] = clean_value
                
            except (ValueError, TypeError) as e:
                validation_issues.append(f"Could not clean {var_code}: {e}")
                # Usar valor por defecto si existe
                if var_code in self.enhanced_defaults:
                    cleaned_vars[var_code] = self.enhanced_defaults[var_code]
        
        # Log validation issues
        if validation_issues:
            logger.warning(f"Variable validation issues: {validation_issues}")
        
        return cleaned_vars
    
    def get_variable_metadata(self, variable_code: str) -> Dict[str, Any]:
        """Obtener metadata de una variable específica"""
        
        metadata = {
            'code': variable_code,
            'alternative_names': self.variable_mapping.get(variable_code, []),
            'default_value': self.enhanced_defaults.get(variable_code),
            'category': self._get_variable_category(variable_code),
            'data_type': self._get_variable_data_type(variable_code),
            'validation_rules': self._get_validation_rules(variable_code)
        }
        
        return metadata
    
    def _get_variable_category(self, variable_code: str) -> str:
        """Determinar categoría de la variable"""
        
        categories = {
            'financial': ['PVP', 'CUIP', 'CFD', 'SE', 'GMM', 'CC', 'CTI', 'IIF'],
            'operational': ['NEPP', 'MLP', 'TPE', 'CPPL', 'CPROD', 'ES', 'EE'],
            'inventory': ['IPF', 'II', 'DPL', 'TR', 'CMIPF', 'MRE', 'MRA'],
            'customer': ['CPD', 'VPC', 'PC', 'NC'],
            'logistics': ['CUTRANS', 'CTPLV', 'ALC', 'LG'],
            'quality': ['QC', 'CCP'],
            'resources': ['HAU', 'HTP', 'EAT', 'TTEP', 'TP'],
            'components': ['CMP1', 'V1', 'CMP2', 'V2', 'CMP3', 'V3'],
            'demand': ['DH']
        }
        
        for category, vars_in_cat in categories.items():
            if variable_code in vars_in_cat:
                return category
        
        return 'other'
    
    def _get_variable_data_type(self, variable_code: str) -> str:
        """Determinar tipo de datos de la variable"""
        
        if variable_code in ['NEPP', 'CPD', 'NC', 'EAT']:
            return 'integer'
        elif variable_code in ['ES', 'EE', 'QC', 'NSC']:
            return 'percentage'
        elif variable_code == 'DH':
            return 'list'
        else:
            return 'float'
    
    def _get_validation_rules(self, variable_code: str) -> Dict[str, Any]:
        """Obtener reglas de validación para la variable"""
        
        rules = {'min_value': 0}
        
        if variable_code in ['ES', 'EE', 'QC', 'NSC']:
            rules.update({'min_value': 0, 'max_value': 1})
        elif variable_code == 'MLP':
            rules.update({'min_value': 0, 'max_value': 1440})
        elif variable_code in ['HAU', 'HTP']:
            rules.update({'min_value': 0, 'max_value': 24})
        elif variable_code in ['NEPP', 'CPD', 'NC']:
            rules.update({'min_value': 1, 'data_type': 'integer'})
        
        return rules
    
    def generate_extraction_report(self, extracted_vars: Dict[str, Any]) -> Dict[str, Any]:
        """Generar reporte del proceso de extracción"""
        
        report = {
            'total_variables_extracted': len(extracted_vars),
            'variables_by_category': {},
            'variables_with_defaults': [],
            'potential_issues': [],
            'coverage_analysis': {}
        }
        
        # Agrupar por categoría
        for var_code in extracted_vars.keys():
            category = self._get_variable_category(var_code)
            if category not in report['variables_by_category']:
                report['variables_by_category'][category] = []
            report['variables_by_category'][category].append(var_code)
        
        # Identificar variables con valores por defecto
        for var_code, value in extracted_vars.items():
            if var_code in self.enhanced_defaults and value == self.enhanced_defaults[var_code]:
                report['variables_with_defaults'].append(var_code)
        
        # Análisis de cobertura
        total_expected = len(self.enhanced_defaults)
        extracted_count = len(extracted_vars)
        report['coverage_analysis'] = {
            'coverage_percentage': (extracted_count / total_expected) * 100,
            'missing_critical_vars': [
                var for var in ['PVP', 'CUIP', 'NEPP', 'CPROD', 'CPD'] 
                if var not in extracted_vars
            ]
        }
        
        # Identificar problemas potenciales
        if report['coverage_analysis']['coverage_percentage'] < 80:
            report['potential_issues'].append("Low variable coverage - many defaults used")
        
        if report['coverage_analysis']['missing_critical_vars']:
            report['potential_issues'].append("Missing critical business variables")
        
        return report