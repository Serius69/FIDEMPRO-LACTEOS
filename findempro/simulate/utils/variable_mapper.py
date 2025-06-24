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
            # Variables financieras básicas
            'PVP': ['precio_venta', 'precio_unitario', 'precio'],
            'CUIP': ['costo_unitario', 'costo_insumo', 'costo_material'],
            'CFD': ['costos_fijos', 'gastos_fijos_diarios'],
            'SE': ['salarios', 'sueldos_empleados', 'nomina'],
            'GMM': ['gastos_marketing', 'marketing_mensual'],
            
            # Variables operativas
            'NEPP': ['numero_empleados', 'empleados_produccion'],
            'MLP': ['minutos_laborables', 'tiempo_trabajo_dia'],
            'TPE': ['tiempo_por_unidad', 'tiempo_produccion_unitario'],
            'CPPL': ['capacidad_lote', 'unidades_por_lote'],
            'CINSP': ['conversion_insumos', 'factor_conversion'],
            'CPROD': ['capacidad_produccion', 'capacidad_maxima'],
            
            # Variables de clientes y mercado
            'CPD': ['clientes_por_dia', 'clientes_diarios'],
            'VPC': ['ventas_por_cliente', 'unidades_por_cliente'],
            'PC': ['precio_competencia', 'precio_mercado'],
            
            # Variables de inventario
            'IPF': ['inventario_inicial', 'stock_inicial_terminados'],
            'II': ['inventario_insumos', 'stock_inicial_materias'],
            'DPL': ['dias_plazo_entrega', 'lead_time'],
            'TR': ['tiempo_reposicion', 'ciclo_reposicion'],
            'CMIPF': ['capacidad_maxima_inventario', 'limite_almacen'],
            
            # Variables de transporte y logística
            'CUTRANS': ['costo_transporte_unitario', 'costo_logistica'],
            'CTPLV': ['capacidad_transporte', 'vehiculos_capacidad'],
            
            # Variables de eficiencia esperadas
            'ES': ['eficiencia_estandar', 'eficiencia_objetivo'],
            'EE': ['eficiencia_esperada', 'eficiencia_meta'],
            'CCAP': ['costo_capital', 'inversion_capital'],
            'HAU': ['horas_uso_diario', 'tiempo_operacion'],
            'HTP': ['horas_totales_posibles', 'tiempo_maximo'],
            
            # Variables de materiales
            'MRE': ['material_requerido_esperado', 'consumo_esperado'],
            'MRA': ['material_requerido_actual', 'consumo_actual'],
            
            # Variables de costos detallados
            'CDP': ['costo_produccion_directo', 'costo_directo'],
            'CCP': ['costo_calidad_produccion', 'costo_control_calidad'],
            'CSP': ['costo_servicio_produccion', 'costo_soporte'],
            'ICC': ['inversion_capital_trabajo', 'capital_trabajo'],
            'CC': ['costo_capital_financiero', 'costo_financiamiento'],
            'CTI': ['costo_total_inversion', 'inversion_total'],
            'CAL': ['costo_almacenamiento', 'costo_bodega'],
            
            # Variables de componentes
            'CMP1': ['costo_componente_1', 'material_1'],
            'V1': ['volumen_componente_1', 'cantidad_material_1'],
            'CMP2': ['costo_componente_2', 'material_2'],
            'V2': ['volumen_componente_2', 'cantidad_material_2'],
            'CMP3': ['costo_componente_3', 'material_3'],
            'V3': ['volumen_componente_3', 'cantidad_material_3'],
            
            # Variables de inversión
            'IIF': ['inversion_inicial_fija', 'activos_fijos'],
            
            # Variables de recursos humanos
            'EAT': ['empleados_tiempo_completo', 'personal_fijo'],
            'TTEP': ['tiempo_total_programado', 'horas_programadas'],
            'TP': ['tiempo_productivo', 'horas_efectivas'],
            
            # Variables de calidad
            'QC': ['calidad_produccion', 'porcentaje_calidad'],
            
            # Variables de logística avanzada
            'ALC': ['almacenamiento_logistico', 'costo_logistica_almacen'],
            'NC': ['numero_clientes', 'base_clientes'],
            'LG': ['logistica_general', 'gastos_logistica'],
            
            # Demanda histórica
            'DH': ['demanda_historica', 'datos_historicos_demanda', 'historial_ventas'],
            
            # Variables de eficiencia - AGREGADAS PARA EOG
            'EOG': ['eficiencia_operativa_global', 'oee', 'overall_equipment_effectiveness']
        }
        
        # Valores por defecto mejorados (AGREGADO EOG)
        self.enhanced_defaults = {
            # Financieros
            'PVP': 15.50, 'CUIP': 8.20, 'CFD': 1800, 'SE': 48000, 'GMM': 3500,
            
            # Operativos
            'NEPP': 15, 'MLP': 480, 'TPE': 45, 'CPPL': 500, 'CINSP': 1.05, 'CPROD': 3000,
            
            # Clientes
            'CPD': 85, 'VPC': 30, 'PC': 15.80,
            
            # Inventario
            'IPF': 1000, 'II': 5000, 'DPL': 3, 'TR': 3, 'CMIPF': 20000,
            
            # Transporte
            'CUTRANS': 0.35, 'CTPLV': 1500,
            
            # Eficiencia
            'ES': 0.85, 'EE': 0.80, 'CCAP': 1000, 'HAU': 8, 'HTP': 24,
            'EOG': 0.80,  # AGREGADO: Eficiencia Operativa Global por defecto
            
            # Materiales
            'MRE': 100, 'MRA': 95,
            
            # Costos detallados
            'CDP': 50, 'CCP': 30, 'CSP': 20, 'ICC': 1000, 'CC': 500, 'CTI': 200, 'CAL': 100,
            
            # Componentes
            'CMP1': 50, 'V1': 100, 'CMP2': 60, 'V2': 120, 'CMP3': 40, 'V3': 80,
            
            # Inversión
            'IIF': 10000,
            
            # RRHH
            'EAT': 8, 'TTEP': 2000, 'TP': 1800,
            
            # Calidad
            'QC': 0.95,
            
            # Logística
            'ALC': 500, 'NC': 50, 'LG': 1000
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
            # Obtener producto y negocio del cuestionario
            product = questionary_result.fk_questionary.fk_product
            business = product.fk_business
            
            # CORREGIDO: Consulta sin fk_business directo
            # Buscar variables activas (sin filtro por business específico por ahora)
            system_variables = Variable.objects.filter(
                is_active=True
            )
            
            # Alternativamente, si Variable tiene relación con Product:
            # system_variables = Variable.objects.filter(
            #     fk_product=product,  # Si existe esta relación
            #     is_active=True
            # )
            
            for sys_var in system_variables:
                if sys_var.initials in self.variable_mapping:
                    # Intentar obtener valor por defecto o calculado
                    if hasattr(sys_var, 'default_value') and sys_var.default_value:
                        try:
                            value = float(sys_var.default_value)
                            variables[sys_var.initials] = value
                        except (ValueError, TypeError):
                            pass
            
            logger.info(f"Extracted {len(variables)} variables from variable system")
            
        except Exception as e:
            logger.error(f"Error extracting from variable system: {str(e)}")
            # NO fallar completamente, continuar con valores por defecto
        
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
        """Aplicar valores por defecto mejorados para variables faltantes"""
        
        complete_vars = extracted_variables.copy()
        defaults_applied = 0
        
        for var_code, default_value in self.enhanced_defaults.items():
            if var_code not in complete_vars or complete_vars[var_code] is None:
                complete_vars[var_code] = default_value
                defaults_applied += 1
        
        # Ajustes contextuales de defaults
        complete_vars = self._apply_contextual_adjustments(complete_vars)
        
        logger.info(f"Applied {defaults_applied} default values")
        return complete_vars
    
    def _apply_contextual_adjustments(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Aplicar ajustes contextuales a los valores por defecto"""
        
        adjusted_vars = variables.copy()
        
        # Ajustar capacidad de producción según número de empleados
        if adjusted_vars.get('NEPP', 0) > 0:
            base_capacity = adjusted_vars.get('CPROD', 3000)
            employee_factor = adjusted_vars['NEPP'] / 15  # 15 empleados base
            adjusted_vars['CPROD'] = base_capacity * employee_factor
        
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
            if 'PVP' not in variables:  # Solo si no fue definido explícitamente
                adjusted_vars['PVP'] = comp_price * 0.95  # 5% más barato
        
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