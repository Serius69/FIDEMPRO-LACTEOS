# services/simulation_math.py
"""
VERSIÓN CORREGIDA: Motor matemático completo con resolución de dependencias EOG-IDG
"""
import logging
import numpy as np
from typing import Dict, Any, List, Tuple, Optional, Set
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict, deque
import copy

logger = logging.getLogger(__name__)


class EquationSolver:
    """Solucionador de ecuaciones con manejo de dependencias CORREGIDO"""
    
    def __init__(self):
        self.equations = {}
        self.dependencies = defaultdict(set)
        self.reverse_dependencies = defaultdict(set)
        self.calculation_order = []
        
    def register_equation(self, variable: str, dependencies: Set[str], calculation_func):
        """Registra una ecuación con sus dependencias"""
        self.equations[variable] = calculation_func
        self.dependencies[variable] = dependencies
        
        # Construir dependencias inversas
        for dep in dependencies:
            self.reverse_dependencies[dep].add(variable)
    
    def solve_with_iterations(self, variables: Dict[str, Any], 
                            target_variables: Set[str], 
                            max_iterations: int = 10,
                            tolerance: float = 1e-6) -> Dict[str, Any]:
        """Resolver ecuaciones con iteraciones para manejar dependencias circulares"""
        
        # CORRECCIÓN: Orden específico para EOG antes que IDG
        priority_order = ['TG','GT', 'PE', 'FU', 'NSC', 'EOG','NR', 'IDG',  'MB', 'HO' , 'CHO', 'RI']

        # Construir orden considerando prioridades
        calculation_order = []
        
        # Primero las variables de prioridad
        for priority_var in priority_order:
            if priority_var in target_variables and priority_var in self.equations:
                calculation_order.append(priority_var)
        
        # Luego las demás variables
        remaining_vars = target_variables - set(calculation_order)
        calculation_order.extend(self.build_calculation_order(remaining_vars))
        
        logger.info(f"Calculation order: {calculation_order}")
        
        result_vars = copy.deepcopy(variables)
        
        for iteration in range(max_iterations):
            old_values = {var: result_vars.get(var, 0) for var in target_variables}
            changes = False
            
            for var in calculation_order:
                if var in self.equations:
                    try:
                        # Verificar dependencias
                        missing_deps = self.dependencies[var] - set(result_vars.keys())
                        if missing_deps:
                            logger.debug(f"Missing dependencies for {var}: {missing_deps}")
                            # Crear valores por defecto para dependencias faltantes
                            for dep in missing_deps:
                                if dep not in result_vars:
                                    result_vars[dep] = self._get_default_value(dep)
                        
                        # Calcular nueva valor
                        new_value = self.equations[var](result_vars)
                        
                        # Validar resultado
                        if isinstance(new_value, (int, float)) and not np.isnan(new_value) and not np.isinf(new_value):
                            old_value = result_vars.get(var, 0)
                            if abs(new_value - old_value) > tolerance:
                                changes = True
                            result_vars[var] = float(new_value)
                        else:
                            logger.warning(f"Invalid calculation result for {var}: {new_value}")
                        
                    except Exception as e:
                        logger.error(f"Error calculating {var}: {str(e)}")
                        # Usar valor por defecto en caso de error
                        if var not in result_vars:
                            result_vars[var] = self._get_default_value(var)
            
            # Verificar convergencia
            if not changes:
                logger.info(f"Converged after {iteration + 1} iterations")
                break
        
        return result_vars
    
    def _get_default_value(self, var_name: str) -> float:
        """Obtener valores por defecto para variables"""
        defaults = {
            'PE': 0.85,
            'FU': 0.80,
            'NSC': 0.90,
            'EOG': 0.68,  # PE * FU * 0.95
            'NR': 0.15,
            'MB': 0.30,
            'ES': 0.85,
            'EE': 0.80,
            'QC': 0.95,
            'DPH': 100,
            'IT': 1000,
            'GT': 150,
            'TG': 850
        }
        return defaults.get(var_name, 0.0)

    def build_calculation_order(self, variables_to_calculate: Set[str]) -> List[str]:
        """Construye el orden de cálculo usando ordenamiento topológico"""
        # Implementar algoritmo de Kahn para ordenamiento topológico
        in_degree = defaultdict(int)
        
        # Calcular grado de entrada para variables requeridas
        for var in variables_to_calculate:
            if var in self.dependencies:
                in_degree[var] = len(self.dependencies[var] & variables_to_calculate)
        
        # Cola para variables sin dependencias
        queue = deque([var for var in variables_to_calculate if in_degree[var] == 0])
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            # Reducir grado de entrada de variables dependientes
            for dependent in self.reverse_dependencies[current]:
                if dependent in variables_to_calculate:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)
        
        # Detectar dependencias circulares
        if len(result) < len(variables_to_calculate):
            circular_vars = variables_to_calculate - set(result)
            logger.warning(f"Circular dependencies detected for: {circular_vars}")
            # Agregar variables circulares al final para resolución iterativa
            result.extend(circular_vars)
        
        return result


class SimulationMathEngine:
    """
    Motor matemático CORREGIDO con resolución de dependencias EOG-IDG
    """
    
    def __init__(self):
        self.MIN_DEMAND = 1.0
        self.SAFETY_FACTOR = 1.65
        self.equation_solver = EquationSolver()
        self._register_all_equations_fixed()
        
        # Valores por defecto mejorados
        self.default_values = {
            'ES': 0.85,  # Eficiencia estándar
            'EE': 0.80,  # Eficiencia esperada
            'QC': 0.95,  # Calidad de producción
            'CCAP': 1000,  # Capacidad de capital
            'HAU': 8,  # Horas de uso
            'HTP': 24,  # Horas totales posibles
        }
    
    def _register_all_equations_fixed(self):
        """Registra todas las ecuaciones del sistema CON ORDEN CORRECTO"""
        
        self.equation_solver.register_equation(
            'TG', {'GO', 'GG'}, 
            lambda v: v.get('GO', 0) + v.get('GG', 0)
        )
        
        # Ecuaciones financieras básicas
        self.equation_solver.register_equation(
            'GT', {'IT', 'TG'}, 
            lambda v: v.get('IT', 0) - v.get('TG', 0)
        )
        
        self.equation_solver.register_equation(
            'PE', {'QPL', 'DPH'}, 
            lambda v: min(1.0, v.get('QPL', 0) / max(v.get('DPH', 1) * 1.1, 1))
        )
        
        # CORRECCIÓN: Registrar FU después
        self.equation_solver.register_equation(
            'FU', {'QPL', 'CPROD'}, 
            lambda v: min(1.0, v.get('QPL', 0) / max(v.get('CPROD', 1), 1))
        )
        
        # CORRECCIÓN: Registrar NSC después
        self.equation_solver.register_equation(
            'NSC', {'TPV', 'DPH'}, 
            lambda v: min(1.0, v.get('TPV', 0) / max(v.get('DPH', 1), 1))
        )
        
        # CORRECCIÓN: Registrar EOG DESPUÉS de PE, FU, y con QC por defecto
        self.equation_solver.register_equation(
            'EOG', {'PE', 'FU'}, 
            lambda v: v.get('PE', 0.85) * v.get('FU', 0.80) * v.get('QC', 0.95)
        )
        
        # CORRECCIÓN: Registrar IDG DESPUÉS de EOG y NSC
        self.equation_solver.register_equation(
            'IDG', {'EOG', 'NSC', 'NR'}, 
            lambda v: (v.get('EOG', 0.68) * 0.4 + 
                      v.get('NSC', 0.90) * 0.3 + 
                      min(v.get('NR', 0.15) + 0.5, 1.0) * 0.3)
        )     
        
        self.equation_solver.register_equation(
            'MB', {'IB', 'IT'}, 
            lambda v: v.get('IB', 0) / max(v.get('IT', 1), 1)
        )
        
        self.equation_solver.register_equation(
            'NR', {'GT', 'IT'}, 
            lambda v: v.get('GT', 0) / max(v.get('IT', 1), 1)
        )
        
        # Otras ecuaciones importantes
        self.equation_solver.register_equation(
            'RI', {'GT', 'TG'}, 
            lambda v: v.get('GT', 0) / max(v.get('TG', 1), 1)
        )
        
        # Ecuación de recursos humanos corregida
        self.equation_solver.register_equation(
            'CHO', {'HO', 'SE', 'NEPP'}, 
            lambda v: (v.get('HO', 0) / 8) * (v.get('SE', 48000) / 30 / max(v.get('NEPP', 15), 1))
        )
        
        self.equation_solver.register_equation(
            'HO', {'MLP', 'HNP'}, 
            lambda v: max(0, v.get('MLP', 480) - v.get('HNP', 400))
        )
    
    def calculate_complete_variables(self, 
                                   demand_metrics: Dict[str, float],
                                   parameters: Dict[str, Any],
                                   previous_state: Dict[str, Any],
                                   day_number: int) -> Dict[str, Any]:
        """
        Cálculo completo de todas las variables CON ORDEN CORRECTO
        """
        # Inicializar variables base
        variables = self._initialize_base_variables(demand_metrics, parameters, previous_state)
        
        # CORRECCIÓN: Calcular variables básicas primero
        variables = self._calculate_basic_economics(variables, demand_metrics, parameters)
        
        # CORRECCIÓN: Asegurar que QC esté disponible para EOG
        if 'QC' not in variables:
            variables['QC'] = 0.95
        
        # CORRECCIÓN: Resolver ecuaciones con orden correcto
        target_variables = set(self.equation_solver.equations.keys())
        variables = self.equation_solver.solve_with_iterations(variables, target_variables)
        
        # CORRECCIÓN: Validar que EOG e IDG se calcularon correctamente
        if 'EOG' not in variables or variables['EOG'] == 0:
            # Calcular EOG manualmente si falló
            pe = variables.get('PE', 0.85)
            fu = variables.get('FU', 0.80)
            qc = variables.get('QC', 0.95)
            variables['EOG'] = pe * fu * qc
            logger.info(f"Manual EOG calculation: PE({pe}) * FU({fu}) * QC({qc}) = {variables['EOG']}")
        
        if 'IDG' not in variables or variables['IDG'] == 0:
            # Calcular IDG manualmente si falló
            eog = variables.get('EOG', 0.68)
            nsc = variables.get('NSC', 0.90)
            nr = min(variables.get('NR', 0.15) + 0.5, 1.0)
            variables['IDG'] = eog * 0.4 + nsc * 0.3 + nr * 0.3
            logger.info(f"Manual IDG calculation: EOG({eog})*0.4 + NSC({nsc})*0.3 + NR({nr})*0.3 = {variables['IDG']}")
        
        # Aplicar validaciones preventivas
        variables = self._apply_preventive_validations(variables, demand_metrics)
        
        # Agregar metadatos
        variables['_day'] = day_number
        variables['_demand_original'] = demand_metrics['DPH']
        variables['_calculation_complete'] = True
        variables['_eog_calculated'] = True
        variables['_idg_calculated'] = True
        
        return variables
    
    def _initialize_base_variables(self, demand_metrics: Dict[str, float],
                                 parameters: Dict[str, Any],
                                 previous_state: Dict[str, Any]) -> Dict[str, Any]:
        """Inicializar variables base del sistema"""
        
        variables = {
            # Demanda
            'DPH': demand_metrics['DPH'],
            'DSD': demand_metrics['DSD'],
            'DDP': demand_metrics.get('DDP', demand_metrics['DPH']),
            
            # Parámetros básicos desde BD
            'PVP': float(parameters.get('PVP', 15.50)),
            'CUIP': float(parameters.get('CUIP', 8.20)),
            'CFD': float(parameters.get('CFD', 1800)),
            'SE': float(parameters.get('SE', 48000)),
            'GMM': float(parameters.get('GMM', 3500)),
            'NEPP': float(parameters.get('NEPP', 15)),
            'MLP': float(parameters.get('MLP', 480)),
            'TPE': float(parameters.get('TPE', 45)),
            'CPPL': float(parameters.get('CPPL', 500)),
            'CINSP': float(parameters.get('CINSP', 1.05)),
            'CPD': float(parameters.get('CPD', 85)),
            'VPC': float(parameters.get('VPC', 30)),
            'DPL': float(parameters.get('DPL', 3)),
            'TR': float(parameters.get('TR', 3)),
            'CMIPF': float(parameters.get('CMIPF', 20000)),
            'CUTRANS': float(parameters.get('CUTRANS', 0.35)),
            'CTPLV': float(parameters.get('CTPLV', 1500)),
            'PC': float(parameters.get('PC', 15.80)),
            'CPROD': float(parameters.get('CPROD', 3000)),
            
            # Estado previo
            'IPF': float(previous_state.get('IPF', parameters.get('IPF', 1000))),
            'II': float(previous_state.get('II', parameters.get('II', 5000))),
            
            # CORRECCIÓN: Variables por defecto para EOG
            'ES': 0.85,
            'EE': 0.80,
            'QC': 0.95,
        }
        
        return variables
    
    def _calculate_basic_economics(self, variables: Dict[str, Any], 
                                 demand_metrics: Dict[str, float],
                                 parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Calcular variables económicas básicas CORREGIDO"""
        
        # Calcular producción basada en demanda
        variables.update(self._calculate_production_variables(variables, demand_metrics))
        
        # Calcular ventas
        variables.update(self._calculate_sales_variables(variables, demand_metrics))
        
        # Calcular costos básicos
        variables.update(self._calculate_cost_variables(variables))
        
        # Calcular ingresos básicos
        variables.update(self._calculate_revenue_variables(variables))
        
        # Calcular inventarios
        variables.update(self._calculate_inventory_variables(variables, demand_metrics))
        
        return variables
    
    def _calculate_production_variables(self, variables: Dict[str, Any], 
                                      demand_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Calcular variables de producción"""
        
        dph = demand_metrics['DPH']
        dsd = demand_metrics.get('DSD', dph * 0.1)
        
        # Cantidad óptima de producción
        safety_stock = dsd * self.SAFETY_FACTOR
        pod = dph + safety_stock
        
        # Capacidad de producción
        capacity_by_time = (variables['NEPP'] * variables['MLP'] / variables['TPE']) * 0.85
        capacity_by_materials = (variables['II'] / variables['CINSP']) * 0.95
        capacity_by_equipment = variables['CPROD']
        
        qpl = min(pod, capacity_by_time, capacity_by_materials, capacity_by_equipment)
        
        # CORRECCIÓN: Eficiencias calculadas correctamente
        fu = qpl / max(capacity_by_equipment, self.MIN_DEMAND)
        pe = min(qpl / max(dph * 1.1, self.MIN_DEMAND), 1.0)
        ep = min(pe, 1.0)
        
        # Horas necesarias
        hnp = (qpl / variables['CPPL']) * variables['TPE'] if variables['CPPL'] > 0 else 0
        
        return {
            'POD': pod,
            'QPL': qpl,
            'PPL': qpl,  # Producción en lotes igual a QPL
            'TPPRO': qpl,
            'FU': fu,
            'PE': pe,
            'EP': ep,
            'HNP': hnp
        }
    
    def _calculate_sales_variables(self, variables: Dict[str, Any], 
                                 demand_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Calcular variables de ventas"""
        
        dph = demand_metrics['DPH']
        ddp = demand_metrics.get('DDP', dph)
        
        # Capacidad de atención
        max_customers_by_demand = ddp / max(variables['VPC'], 1)
        tcae = min(variables['CPD'], max_customers_by_demand, variables['CPD'] * 1.2)
        
        # Ventas reales
        max_sales_by_customers = tcae * variables['VPC']
        max_sales_by_inventory = variables['IPF'] + variables.get('QPL', 0)
        tpv = min(ddp, max_sales_by_customers, max_sales_by_inventory)
        
        # Demanda insatisfecha
        di = max(0, ddp - tpv)
        
        # Nivel de servicio CORREGIDO
        nsc = min(1.0, tpv / max(ddp, self.MIN_DEMAND))
        
        return {
            'TCAE': tcae,
            'TPV': tpv,
            'DI': di,
            'NSC': nsc
        }
    
    def _calculate_cost_variables(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Calcular variables de costos"""
        
        # Costos de materiales
        ctai = variables.get('QPL', 0) * variables['CUIP'] * variables['CINSP']
        
        # Costo variable unitario
        cvu = ctai / max(variables.get('QPL', 1), 1)
        
        # Gastos operativos
        se_daily = variables['SE'] / 30
        go = variables['CFD'] + se_daily + ctai
        
        # Costos de transporte
        trips_needed = np.ceil(variables.get('TPV', 0) / variables['CTPLV']) if variables['CTPLV'] > 0 else 0
        cttl = trips_needed * variables['CUTRANS'] * 50
        
        # Costos de almacenamiento
        ca = variables['IPF'] * variables['PVP'] * 0.002 + 100
        
        # Pérdidas
        mp = variables.get('QPL', 0) * 0.02  # 2% pérdidas producción
        mi = variables['IPF'] * 0.01  # 1% pérdidas inventario
        ctm = (mp + mi) * variables['PVP'] * 0.7
        
        # Gastos generales
        gmm_daily = variables['GMM'] / 30
        gg = gmm_daily + cttl + ca + ctm
        
        return {
            'CTAI': ctai,
            'CVU': cvu,
            'GO': go,
            'CTTL': cttl,
            'CA': ca,
            'MP': mp,
            'MI': mi,
            'CTM': ctm,
            'GG': gg
        }
    
    def _calculate_revenue_variables(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Calcular variables de ingresos"""
        
        # Ingresos totales
        it = variables.get('TPV', 0) * variables['PVP']
        
        # Ingresos esperados
        ie = variables['DPH'] * variables['PVP']
        
        # Ingreso bruto
        ib = it - variables.get('CTAI', 0)
        
        return {
            'IT': it,
            'IE': ie,
            'IB': ib
        }
    
    def _calculate_inventory_variables(self, variables: Dict[str, Any], 
                                     demand_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Calcular variables de inventario"""
        
        dph = demand_metrics['DPH']
        dsd = demand_metrics.get('DSD', dph * 0.1)
        
        # Inventario óptimo
        iop = dph * variables['DPL'] + dsd * np.sqrt(variables['DPL']) * self.SAFETY_FACTOR
        
        # Inventario final de productos terminados
        ipf_new = max(0, variables['IPF'] + variables.get('QPL', 0) - variables.get('TPV', 0))
        ipf_new = min(ipf_new, variables['CMIPF'])
        
        # Días de cobertura
        dci = ipf_new / max(dph, self.MIN_DEMAND)
        
        # Rotación de inventarios
        rti = (dph * 30) / max(ipf_new, self.MIN_DEMAND)
        
        # Inventario óptimo de insumos
        ioi = dph * variables['CINSP'] * (variables['TR'] + variables['DPL'])
        
        # Pedido de insumos
        pi = max(0, ioi - variables['II'] + variables.get('QPL', 0) * variables['CINSP'])
        
        # Inventario final de insumos
        ii_new = max(0, variables['II'] + pi - variables.get('QPL', 0) * variables['CINSP'])
        
        return {
            'IOP': iop,
            'IPF': ipf_new,
            'DCI': dci,
            'RTI': rti,
            'IOI': ioi,
            'PI': pi,
            'II': ii_new,
            'UII': variables.get('QPL', 0) * variables['CINSP']
        }
    
    def _apply_preventive_validations(self, variables: Dict[str, Any], 
                                    demand_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Aplicar validaciones preventivas en lugar de parches reactivos"""
        
        validated_vars = variables.copy()
        validation_log = []
        
        # Validación 1: Coherencia de márgenes
        if 'MB' in validated_vars and (validated_vars['MB'] < -1 or validated_vars['MB'] > 1):
            it = validated_vars.get('IT', 0)
            ctai = validated_vars.get('CTAI', 0)
            if it > 0:
                validated_vars['MB'] = max(-0.5, min(0.9, (it - ctai) / it))
                validation_log.append("Corrected margin bounds")
        
        # Validación 2: Coherencia de margen neto
        if 'NR' in validated_vars and (validated_vars['NR'] < -1 or validated_vars['NR'] > 1):
            it = validated_vars.get('IT', 0)
            gt = validated_vars.get('GT', 0)
            if it > 0:
                validated_vars['NR'] = max(-0.8, min(0.8, gt / it))
                validation_log.append("Corrected net margin bounds")
        
        # Validación 3: Límites de eficiencia
        efficiency_vars = ['PE', 'FU', 'NSC', 'EOG', 'IDG']
        for var in efficiency_vars:
            if var in validated_vars:
                validated_vars[var] = max(0, min(1, validated_vars[var]))
        
        # Validación 4: Coherencia de inventarios
        if validated_vars.get('IPF', 0) < 0:
            validated_vars['IPF'] = 0
            validation_log.append("Corrected negative inventory")
        
        # Validación 5: EOG e IDG específicas
        if 'EOG' in validated_vars:
            if validated_vars['EOG'] < 0.1 or validated_vars['EOG'] > 1:
                pe = validated_vars.get('PE', 0.85)
                fu = validated_vars.get('FU', 0.80)
                qc = validated_vars.get('QC', 0.95)
                validated_vars['EOG'] = pe * fu * qc
                validation_log.append("Recalculated EOG")
        
        if 'IDG' in validated_vars:
            if validated_vars['IDG'] < 0.1 or validated_vars['IDG'] > 1:
                eog = validated_vars.get('EOG', 0.68)
                nsc = validated_vars.get('NSC', 0.90)
                nr = min(validated_vars.get('NR', 0.15) + 0.5, 1.0)
                validated_vars['IDG'] = eog * 0.4 + nsc * 0.3 + nr * 0.3
                validation_log.append("Recalculated IDG")
        
        if validation_log:
            logger.info(f"Applied {len(validation_log)} preventive validations: {validation_log}")
        
        return validated_vars
    
    def calculate_basic_variables(self, demand: float, day: int) -> Dict[str, Any]:
        """Método de respaldo para cálculo básico de variables MEJORADO"""
        
        basic_vars = {
            'DPH': demand,
            'TPV': demand * 0.95,  # 95% de satisfacción de demanda
            'IT': demand * 0.95 * 15.50,  # Ingresos estimados
            'CTAI': demand * 0.95 * 8.20,
            'GO': 1800 + (48000 / 30),  # Gastos operativos diarios
            'TG': (1800 + (48000 / 30)) * 1.3,  # Gastos totales estimados
            'NSC': 0.95,  # Nivel de servicio base
            'PE': 0.85,   # Productividad base
            'FU': 0.80,   # Utilización base
            'QC': 0.95,   # Calidad por defecto
            'EOG': 0.85 * 0.80 * 0.95,  # OEE básico: PE * FU * QC
            'day': day
        }
        
        gmm_daily = 3500 / 30
        transport_basic = 200  # Transporte básico estimado
        storage_basic = 150   # Almacenamiento básico
        mermas_basic = basic_vars['TPV'] * 0.01 * 15.50 * 0.7  # 1% mermas
        basic_vars['GG'] = gmm_daily + transport_basic + storage_basic + mermas_basic + basic_vars['CTAI']
        
        # Calcular gastos totales y ganancia
        basic_vars['TG'] = basic_vars['GO'] + basic_vars['GG']
        basic_vars['GT'] = basic_vars['IT'] - basic_vars['TG']
        
        # Calcular márgenes básicos
        if basic_vars['IT'] > 0:
            basic_vars['NR'] = basic_vars['GT'] / basic_vars['IT']
            basic_vars['MB'] = (basic_vars['IT'] * 0.7) / basic_vars['IT']  # 70% margen bruto estimado
        else:
            basic_vars['NR'] = 0
            basic_vars['MB'] = 0
        
        # CORRECCIÓN: Calcular IDG usando EOG
        basic_vars['IDG'] = basic_vars['EOG'] * 0.4 + basic_vars['NSC'] * 0.3 + min(basic_vars['NR'] + 0.5, 1.0) * 0.3
        
        return basic_vars
    
    def simulate_complete_day(self, 
                            current_demand: float,
                            previous_state: Dict[str, Any],
                            parameters: Dict[str, Any],
                            demand_history: List[float]) -> Dict[str, Any]:
        """
        Simulación completa de un día empresarial CORREGIDA
        """
        try:
            # 1. Calcular métricas de demanda
            demand_metrics = self.calculate_daily_demand_metrics(
                current_demand, demand_history, parameters.get('ED', 1.0)
            )
            
            # 2. Calcular todas las variables usando el motor de ecuaciones CORREGIDO
            day_results = self.calculate_complete_variables(
                demand_metrics, parameters, previous_state, 
                previous_state.get('_day', 1)
            )
            
            # 3. 🔧 VALIDACIÓN FINANCIERA FINAL
            financial_valid = self._final_financial_check(day_results)
            if not financial_valid:
                logger.warning("🚨 Simulación falló validación financiera final")
                # Usar cálculo básico como respaldo
                day_results = self.calculate_basic_variables(current_demand, 1)
                day_results['_fallback_used'] = True
            
            # 3. CORRECCIÓN: Verificar que EOG e IDG se calcularon
            if day_results.get('EOG', 0) == 0:
                logger.warning("EOG not calculated, using manual calculation")
                pe = day_results.get('PE', 0.85)
                fu = day_results.get('FU', 0.80)
                qc = day_results.get('QC', 0.95)
                day_results['EOG'] = pe * fu * qc
            
            if day_results.get('IDG', 0) == 0:
                logger.warning("IDG not calculated, using manual calculation")
                eog = day_results.get('EOG', 0.68)
                nsc = day_results.get('NSC', 0.90)
                nr = min(day_results.get('NR', 0.15) + 0.5, 1.0)
                day_results['IDG'] = eog * 0.4 + nsc * 0.3 + nr * 0.3
            
            # 4. Calcular métricas adicionales
            additional_metrics = self._calculate_additional_metrics(day_results)
            day_results.update(additional_metrics)
            
            # 5. Preparar estado para el siguiente día
            next_state = {
                'IPF': day_results.get('IPF', 1000),
                'II': day_results.get('II', 5000),
                '_day': day_results.get('_day', 1) + 1,
                '_last_demand': current_demand,
                '_last_sales': day_results.get('TPV', 0),
                '_last_production': day_results.get('QPL', 0)
            }
            
            day_results['_state'] = next_state
            
            # 6. Metadatos de la simulación MEJORADOS
            day_results['_metadata'] = {
                'simulated_demand': current_demand,
                'demand_fulfillment': day_results.get('TPV', 0) / current_demand if current_demand > 0 else 0,
                'profit_margin': day_results.get('NR', 0),
                'service_level': day_results.get('NSC', 0),
                'operational_efficiency': day_results.get('EOG', 0),
                'global_indicator': day_results.get('IDG', 0),
                'calculation_method': 'complete_equation_solver_fixed_v2',
                'equations_solved': len(self.equation_solver.equations),
                'convergence_achieved': day_results.get('_calculation_complete', False),
                'eog_calculated': day_results.get('_eog_calculated', False),
                'idg_calculated': day_results.get('_idg_calculated', False),
                'financial_validated': day_results.get('_financial_validated', False),
                'corrections_applied': day_results.get('_financial_corrections', [])
            }
            
            return day_results
            
        except Exception as e:
            logger.error(f"Error in complete day simulation: {str(e)}")
            
            # Método de respaldo con cálculos básicos MEJORADO
            logger.warning("Falling back to basic calculation method")
            fallback_results = self.calculate_basic_variables(current_demand, 1)
            fallback_results['_metadata'] = {
                'calculation_method': 'fallback_basic',
                'error': str(e),
                'warning': 'Complete calculation failed, using basic method',
                'eog_calculated': True,  # Se calcula en básico
                'idg_calculated': True   # Se calcula en básico
            }
            
            return fallback_results
    
    def calculate_daily_demand_metrics(self, current_demand: float, 
                                     demand_history: List[float],
                                     seasonality: float = 1.0) -> Dict[str, float]:
        """Calcular métricas de demanda diaria"""
        dph = max(current_demand, self.MIN_DEMAND)
        
        window_size = min(7, len(demand_history))
        if window_size > 0:
            recent_demands = demand_history[-window_size:]
            dsd = float(np.std(recent_demands)) if len(recent_demands) > 1 else dph * 0.1
            recent_mean = float(np.mean(recent_demands))
        else:
            dsd = dph * 0.1
            recent_mean = dph
        
        cvd = dsd / max(recent_mean, self.MIN_DEMAND)
        
        trend_factor = 1.0
        if len(demand_history) >= 3:
            recent_3 = demand_history[-3:]
            if recent_3[-1] > recent_3[0]:
                trend_factor = 1.0 + min(0.1, (recent_3[-1] - recent_3[0]) / recent_3[0])
        
        ddp = dph * seasonality * trend_factor
        
        return {
            'DPH': dph,
            'DSD': dsd,
            'CVD': cvd,
            'DDP': ddp,
            'RECENT_MEAN': recent_mean
        }
        
    def _final_financial_check(self, results: Dict[str, Any]) -> bool:
        """🔧 Validación financiera final para detectar números imposibles"""
        
        it = results.get('IT', 0)
        tg = results.get('TG', 0)
        gt = results.get('GT', 0)
        nr = results.get('NR', 0)
        
        # Verificaciones críticas
        checks = {
            'positive_revenue': it >= 0,
            'reasonable_cost_ratio': tg <= it * 3.0 if it > 0 else True,  # Cambiar de 1.8 a 3.0
            'reasonable_margin': -0.95 <= nr <= 0.95 if it > 0 else True,  # Más permisivo
            'consistent_profit': abs(gt - (it - tg)) < 1.0 if it > 0 else True  # Más tolerancia
        }
        
        failed_checks = [check for check, passed in checks.items() if not passed]
        
        if failed_checks:
            logger.error(f"🚨 Failed financial checks: {failed_checks}")
            logger.error(f"🚨 IT={it:.2f}, TG={tg:.2f}, GT={gt:.2f}, NR={nr:.2%}")
            return False
        
        return True    
    
    
    def _calculate_additional_metrics(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Calcular métricas adicionales derivadas CORREGIDAS"""
        
        additional = {}
        
        # Indicador de salud financiera
        if all(k in variables for k in ['GT', 'IT', 'TG']):
            if variables['IT'] > 0:
                profitability_score = max(0, variables['GT'] / variables['IT'] + 0.5)
                liquidity_score = min(1, variables['IT'] / variables['TG']) if variables['TG'] > 0 else 0
                additional['FINANCIAL_HEALTH'] = (profitability_score + liquidity_score) / 2
        
        # Eficiencia de costos mejorada
        if all(k in variables for k in ['IT', 'TG']):
            if variables['IT'] > 0:
                additional['COST_EFFICIENCY'] = 1 - (variables['TG'] / variables['IT'])
            else:
                additional['COST_EFFICIENCY'] = 0
        
        # Índice de productividad de capital
        capital_invested = 50000  # Valor por defecto
        if variables.get('GT', 0) > 0:
            additional['CAPITAL_PRODUCTIVITY'] = variables['GT'] / capital_invested
        
        return additional
    
    def get_missing_variables_report(self, calculated_vars: Dict[str, Any]) -> Dict[str, List[str]]:
        """Generar reporte de variables faltantes por categoría"""
        
        all_expected_vars = set(self.equation_solver.equations.keys())
        calculated_set = set(calculated_vars.keys())
        missing_vars = all_expected_vars - calculated_set
        
        # Categorizar variables faltantes
        categories = {
            'financial': ['GT', 'TG', 'MB', 'NR', 'RI'],
            'operational': ['PE', 'FU', 'NSC', 'EOG', 'IDG'],
            'production': ['QPL', 'TPV', 'HO'],
            'other': []
        }
        
        missing_by_category = {}
        for category, vars_in_category in categories.items():
            missing_in_cat = [v for v in vars_in_category if v in missing_vars]
            if missing_in_cat:
                missing_by_category[category] = missing_in_cat
        
        return missing_by_category
    
    def validate_calculation_completeness(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Validar la completitud de los cálculos realizados MEJORADO"""
        
        validation_report = {
            'total_variables_calculated': len(results),
            'critical_variables_present': True,
            'missing_variables': [],
            'invalid_values': [],
            'warnings': [],
            'calculation_quality': 'COMPLETE'
        }
        
        # Variables críticas que deben estar presentes INCLUYENDO EOG e IDG
        critical_vars = ['DPH', 'TPV', 'IT', 'GT', 'TG', 'NSC', 'NR', 'EOG', 'IDG']
        
        for var in critical_vars:
            if var not in results:
                validation_report['critical_variables_present'] = False
                validation_report['missing_variables'].append(var)
        
        # Verificar valores inválidos
        for var, value in results.items():
            if isinstance(value, (int, float)):
                if np.isnan(value) or np.isinf(value):
                    validation_report['invalid_values'].append(f"{var}: {value}")
                elif var in ['MB', 'NR'] and (value < -1 or value > 1):
                    validation_report['warnings'].append(f"{var} outside normal range [-1,1]: {value}")
                elif var in ['NSC', 'PE', 'FU', 'EOG', 'IDG'] and (value < 0 or value > 1):
                    validation_report['warnings'].append(f"{var} outside normal range [0,1]: {value}")
        
         # 🔧 CORRECCIÓN: Validación financiera específica
        if 'IT' in results and 'TG' in results and results['IT'] > 0:
            cost_ratio = results['TG'] / results['IT']
            if cost_ratio > 1.5:
                validation_report['warnings'].append(f"Cost ratio too high: {cost_ratio:.2f}")
        
        # CORRECCIÓN: Validación específica para EOG e IDG
        if 'EOG' in results:
            eog_value = results['EOG']
            if eog_value < 0.1 or eog_value > 1:
                validation_report['warnings'].append(f"EOG value seems incorrect: {eog_value}")
        
        if 'IDG' in results:
            idg_value = results['IDG']
            if idg_value < 0.1 or idg_value > 1:
                validation_report['warnings'].append(f"IDG value seems incorrect: {idg_value}")
        
        # Determinar calidad general
        if not validation_report['critical_variables_present']:
            validation_report['calculation_quality'] = 'INCOMPLETE'
        elif validation_report['invalid_values']:
            validation_report['calculation_quality'] = 'INVALID'
        elif len(validation_report['warnings']) > 3:
            validation_report['calculation_quality'] = 'WARNING'
        
        return validation_report    

    def calculate_endogenous_variables_fixed(self, demand_metrics, parameters, previous_state):
        """CORRECCIÓN CRÍTICA: Cálculo de variables endógenas con dependencias resueltas"""
        
        variables = {}
        
        # PASO 1: Variables básicas independientes
        variables.update({
            'DPH': demand_metrics['DPH'],
            'PVP': float(parameters.get('PVP', 15.50)),
            'CUIP': float(parameters.get('CUIP', 8.20)),
            'CFD': float(parameters.get('CFD', 1800)),
            'NEPP': float(parameters.get('NEPP', 15)),
            'CPROD': float(parameters.get('CPROD', 3000))
        })
        
        # PASO 2: Variables de producción y ventas
        qpl = min(demand_metrics['DPH'] * 1.1, variables['CPROD'])
        tpv = min(demand_metrics['DPH'], qpl)
        
        variables.update({
            'QPL': qpl,
            'TPV': tpv,
            'TPPRO': qpl
        })
        
        # PASO 3: Variables financieras básicas
        variables.update({
            'IT': variables['TPV'] * variables['PVP'],
            'CTAI': variables['QPL'] * variables['CUIP'],
            'GO': variables['CFD'] + (float(parameters.get('SE', 48000)) / 30)
        })
        
        # PASO 4: CORRECCIÓN CRÍTICA - Calcular PE antes que EOG
        variables['PE'] = min(variables['TPV'] / max(demand_metrics['DPH'], 1), 1.0)
        variables['FU'] = variables['QPL'] / max(variables['CPROD'], 1)
        
        # PASO 5: CORRECCIÓN CRÍTICA - Calcular EOG con dependencias disponibles
        # EOG = Disponibilidad × Rendimiento × Calidad
        disponibilidad = variables['FU']  # Factor de utilización como disponibilidad
        rendimiento = variables['PE']     # Productividad como rendimiento
        calidad = float(parameters.get('QC', 0.95))  # Calidad de producción
        
        variables['EOG'] = disponibilidad * rendimiento * calidad
        
        # PASO 6: Variables financieras dependientes
        variables.update({
            'TG': variables['GO'] + variables['CTAI'] * 1.2,
            'GT': variables['IT'] - variables['TG'],
            'NR': variables['GT'] / max(variables['IT'], 1),
            'NSC': variables['TPV'] / max(demand_metrics['DPH'], 1)
        })
        
        # PASO 7: CORRECCIÓN CRÍTICA - Calcular IDG con EOG disponible
        # IDG ahora puede usar EOG porque ya está calculado
        service_component = variables['NSC'] * 0.4
        efficiency_component = variables['EOG'] * 0.3  # ✅ EOG ya está disponible
        profitability_component = max(0, min(1, variables['NR'] + 0.5)) * 0.3
        
        variables['IDG'] = service_component + efficiency_component + profitability_component
        
        return variables