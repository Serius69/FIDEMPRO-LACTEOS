# simulate_data.py - Versión Refactorizada como Orquestador
"""
Orquestador de datos de simulación que utiliza los datos reales del cuestionario
y coordina con los módulos existentes de simulación.
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from questionary.data.questionary_result_test_data import get_realistic_answers

class SimulationDataOrchestrator:
    """Orquestador principal para datos de simulación"""
    
    def __init__(self):
        self.simulation_cache = {}
        
    def generate_simulation_from_questionary(self, product_type: str, scenario_type: str = "optimista") -> Dict[str, Any]:
        """
        Genera configuración de simulación basada en las respuestas del cuestionario
        
        Args:
            product_type: Tipo de producto ('leche', 'queso', 'yogur', etc.)
            scenario_type: Tipo de escenario ('optimista', 'conservador', 'pesimista')
        
        Returns:
            Dict con configuración completa de simulación
        """
        # Obtener respuestas reales del cuestionario
        answers = get_realistic_answers(product_type)
        
        # Extraer valores del cuestionario
        questionary_data = self._extract_questionary_values(answers)
        
        # Generar configuración base
        base_config = self._create_base_configuration(product_type, scenario_type, questionary_data)
        
        # Aplicar modificadores según escenario
        scenario_config = self._apply_scenario_modifiers(base_config, scenario_type)
        
        # Generar proyección de demanda realista
        demand_projection = self._generate_demand_projection(
            questionary_data['demanda_historica'],
            scenario_config['parameters'],
            base_config['quantity_time']
        )
        
        # Compilar configuración final
        final_config = {
            **scenario_config,
            'demand_history': demand_projection,
            'questionary_data': questionary_data,
            'expected_results': self._calculate_expected_results(questionary_data, scenario_config['parameters'])
        }
        
        return final_config
    
    def _extract_questionary_values(self, answers: List[Dict]) -> Dict[str, Any]:
        """Extrae y estructura los valores del cuestionario"""
        extracted = {}
        
        for answer in answers:
            var_name = answer.get('variable_name', '')
            value = answer.get('answer')
            
            # Mapear nombres de variables a claves internas
            if var_name and value is not None:
                extracted[var_name] = value
        
        # Asegurar que todos los valores críticos estén presentes
        required_fields = [
            'precio_actual', 'demanda_historica', 'produccion_actual',
            'demanda_esperada', 'capacidad_inventario', 'costo_unitario_insumo',
            'clientes_por_dia', 'numero_empleados', 'capacidad_produccion',
            'sueldos_empleados', 'precio_competencia', 'costo_fijo_diario',
            'gastos_marketing_mensuales'
        ]
        
        for field in required_fields:
            if field not in extracted:
                extracted[field] = self._get_default_value(field)
        
        return extracted
    
    def _create_base_configuration(self, product_type: str, scenario_type: str, 
                                  questionary_data: Dict) -> Dict[str, Any]:
        """Crea la configuración base de simulación"""
        return {
            "name": f"Simulación {scenario_type.title()} - {product_type.title()}",
            "product": product_type.title(),
            "scenario": scenario_type.title(),
            "description": f"Escenario {scenario_type} basado en datos reales del cuestionario",
            "unit_time": "days",
            "quantity_time": 30,
            "confidence_level": 0.95,
            "random_seed": np.random.randint(1, 1000),
            "base_demand": np.mean(questionary_data['demanda_historica']) if questionary_data['demanda_historica'] else 100,
            "demand_std": np.std(questionary_data['demanda_historica']) if questionary_data['demanda_historica'] else 10
        }
    
    def _apply_scenario_modifiers(self, base_config: Dict, scenario_type: str) -> Dict[str, Any]:
        """Aplica modificadores según el tipo de escenario"""
        scenario_params = {
            "optimista": {
                "growth_rate": 0.05,
                "price_elasticity": -0.3,
                "market_share_growth": 0.02,
                "customer_retention": 0.95,
                "production_efficiency": 0.92,
                "waste_percentage": 0.02,
                "seasonality_factor": 1.1,
                "competition_intensity": 0.3
            },
            "conservador": {
                "growth_rate": 0.02,
                "price_elasticity": -0.5,
                "market_share_growth": 0.01,
                "customer_retention": 0.90,
                "production_efficiency": 0.88,
                "waste_percentage": 0.03,
                "seasonality_factor": 1.05,
                "competition_intensity": 0.5
            },
            "pesimista": {
                "growth_rate": -0.02,
                "price_elasticity": -0.8,
                "market_share_growth": -0.01,
                "customer_retention": 0.85,
                "production_efficiency": 0.82,
                "waste_percentage": 0.05,
                "seasonality_factor": 0.95,
                "competition_intensity": 0.7
            }
        }
        
        config = base_config.copy()
        config['parameters'] = scenario_params.get(scenario_type.lower(), scenario_params['conservador'])
        
        return config
    
    def _generate_demand_projection(self, historical_demand: List[float], 
                                   parameters: Dict, days: int) -> List[float]:
        """Genera proyección de demanda realista basada en datos históricos"""
        if not historical_demand:
            return [100] * days
        
        # Estadísticas base
        hist_mean = np.mean(historical_demand)
        hist_std = np.std(historical_demand)
        
        # Calcular tendencia histórica
        if len(historical_demand) > 1:
            x = np.arange(len(historical_demand))
            z = np.polyfit(x, historical_demand, 1)
            historical_trend = z[0]
        else:
            historical_trend = 0
        
        # Generar proyección
        projection = []
        last_value = historical_demand[-1] if historical_demand else hist_mean
        
        for day in range(days):
            # Componente de tendencia
            trend_factor = 1 + (parameters['growth_rate'] * (day / days))
            
            # Componente estacional (fin de semana)
            seasonal_factor = parameters['seasonality_factor'] if (day % 7) in [5, 6] else 1.0
            
            # Componente aleatorio con límites
            random_factor = np.random.normal(0, hist_std * 0.1)
            
            # Continuidad con el último valor
            continuity_weight = max(0, 1 - (day / 10))  # Decae en 10 días
            
            # Valor proyectado
            base_value = continuity_weight * last_value + (1 - continuity_weight) * hist_mean
            projected_value = base_value * trend_factor * seasonal_factor + random_factor
            
            # Limitar variación máxima
            max_change = hist_mean * 0.1  # Máximo 10% de cambio diario
            if abs(projected_value - last_value) > max_change:
                projected_value = last_value + np.sign(projected_value - last_value) * max_change
            
            # Asegurar valor positivo y dentro de límites razonables
            projected_value = max(hist_mean * 0.5, min(hist_mean * 1.5, projected_value))
            
            projection.append(projected_value)
            last_value = projected_value
        
        return projection
    
    def _calculate_expected_results(self, questionary_data: Dict, parameters: Dict) -> Dict[str, float]:
        """Calcula resultados esperados basados en datos del cuestionario"""
        base_demand = np.mean(questionary_data['demanda_historica']) if questionary_data['demanda_historica'] else 100
        
        # Cálculos realistas basados en el cuestionario
        expected_demand = base_demand * (1 + parameters['growth_rate'])
        expected_sales = expected_demand * parameters['production_efficiency']
        expected_revenue = expected_sales * questionary_data['precio_actual']
        
        # Costos basados en datos reales
        production_cost = expected_sales * questionary_data['costo_unitario_insumo']
        fixed_costs = questionary_data['costo_fijo_diario'] * 30
        labor_costs = questionary_data['sueldos_empleados']
        marketing_costs = questionary_data['gastos_marketing_mensuales']
        
        total_costs = production_cost + fixed_costs + labor_costs + marketing_costs
        expected_profit = expected_revenue - total_costs
        
        return {
            "demand_mean": expected_demand,
            "demand_std_deviation": np.std(questionary_data['demanda_historica']) if questionary_data['demanda_historica'] else 10,
            "revenue_growth": parameters['growth_rate'] * parameters['production_efficiency'],
            "profit_margin": expected_profit / expected_revenue if expected_revenue > 0 else 0,
            "roi": expected_profit / total_costs if total_costs > 0 else 0,
            "capacity_utilization": expected_sales / questionary_data['capacidad_produccion'] if questionary_data['capacidad_produccion'] > 0 else 0
        }
    
    def _get_default_value(self, field: str) -> Any:
        """Obtiene valor por defecto para campos faltantes"""
        defaults = {
            'precio_actual': 15.50,
            'demanda_historica': [100] * 30,
            'produccion_actual': 100,
            'demanda_esperada': 110,
            'capacidad_inventario': 1000,
            'costo_unitario_insumo': 8.0,
            'clientes_por_dia': 50,
            'numero_empleados': 10,
            'capacidad_produccion': 150,
            'sueldos_empleados': 30000,
            'precio_competencia': 16.0,
            'costo_fijo_diario': 1000,
            'gastos_marketing_mensuales': 2000
        }
        return defaults.get(field, 0)
    
    def generate_simulation_results(self, simulation_config: Dict, days: int = 30) -> List[Dict]:
        """
        Genera resultados de simulación día por día utilizando la configuración
        """
        results = []
        questionary_data = simulation_config['questionary_data']
        parameters = simulation_config['parameters']
        demand_history = simulation_config['demand_history']
        
        # Variables acumulativas
        inventory = questionary_data.get('capacidad_inventario', 0) * 0.5  # Empezar con 50% inventario
        accumulated_profit = 0
        customers_served_total = 0
        
        for day in range(days):
            # Demanda del día
            daily_demand = demand_history[day] if day < len(demand_history) else np.mean(demand_history)
            
            # Cálculos diarios basados en el cuestionario
            daily_result = self._calculate_daily_variables(
                day, daily_demand, questionary_data, parameters, 
                inventory, accumulated_profit
            )
            
            # Actualizar acumulativos
            inventory = daily_result['variables']['IPF']
            accumulated_profit += daily_result['variables']['GT']
            customers_served_total += daily_result['variables']['TCAE']
            
            # Agregar metadatos
            daily_result['date'] = datetime.now().date() + timedelta(days=day)
            daily_result['demand_mean'] = daily_demand
            daily_result['demand_std_deviation'] = questionary_data.get('demand_std', 10)
            
            results.append(daily_result)
        
        return results
    
    def _calculate_daily_variables(self, day: int, demand: float, questionary_data: Dict,
                                  parameters: Dict, inventory: float, 
                                  accumulated_profit: float) -> Dict[str, Any]:
        """Calcula todas las variables para un día específico"""
        
        # Variables del cuestionario
        precio = questionary_data['precio_actual']
        capacidad_prod = questionary_data['capacidad_produccion']
        costo_insumo = questionary_data['costo_unitario_insumo']
        clientes_dia = questionary_data['clientes_por_dia']
        num_empleados = questionary_data['numero_empleados']
        costo_fijo = questionary_data['costo_fijo_diario']
        
        # Aplicar eficiencias del escenario
        produccion_real = min(capacidad_prod * parameters['production_efficiency'], demand * 1.1)
        clientes_atendidos = clientes_dia * parameters['customer_retention']
        
        # Ventas limitadas por demanda, producción e inventario
        ventas_posibles = min(demand, produccion_real + inventory)
        ventas_reales = ventas_posibles * (1 - parameters['waste_percentage'])
        
        # Variables calculadas
        variables = {
            # Demanda y Ventas
            'DE': demand,
            'DH': demand,
            'TPV': ventas_reales,
            'TCAE': clientes_atendidos,
            'VPC': ventas_reales / max(clientes_atendidos, 1),
            'DI': max(0, demand - ventas_reales),
            
            # Producción
            'TPPRO': produccion_real,
            'CPROD': capacidad_prod,
            'FU': produccion_real / capacidad_prod if capacidad_prod > 0 else 0,
            'PE': ventas_reales / num_empleados if num_empleados > 0 else 0,
            
            # Inventarios
            'IPF': inventory + produccion_real - ventas_reales,
            'II': costo_insumo * produccion_real * 1.1,  # 10% extra de seguridad
            
            # Financieros - Ingresos
            'IT': ventas_reales * precio,
            'PVP': precio,
            
            # Financieros - Costos
            'CTAI': costo_insumo * produccion_real,
            'CFD': costo_fijo,
            'SE': questionary_data['sueldos_empleados'] / 30,  # Diario
            'GMM': questionary_data['gastos_marketing_mensuales'] / 30,  # Diario
            
            # Totales
            'GO': costo_fijo + (questionary_data['sueldos_empleados'] / 30) + (costo_insumo * produccion_real),
            'GG': questionary_data['gastos_marketing_mensuales'] / 30,
            'TG': 0,  # Se calcula después
            'GT': 0,  # Se calcula después
            
            # Indicadores
            'NR': 0,  # Se calcula después
            'MB': 0,  # Se calcula después
            'RI': 0,  # Se calcula después
            'RTI': 365 / max(questionary_data.get('dias_reabastecimiento', 3), 1),
            'PM': ventas_reales / demand if demand > 0 else 0,
            'NCM': parameters['competition_intensity'],
            
            # Otros
            'DIA': day + 1,
            'NMD': 30,
            'PC': questionary_data['precio_competencia'],
            'ED': parameters['seasonality_factor']
        }
        
        # Calcular totales
        variables['TG'] = variables['GO'] + variables['GG']
        variables['GT'] = variables['IT'] - variables['TG']
        
        # Calcular indicadores
        if variables['IT'] > 0:
            variables['NR'] = variables['GT'] / variables['IT']
            variables['MB'] = (variables['IT'] - variables['CTAI']) / variables['IT']
        
        if variables['TG'] > 0:
            variables['RI'] = variables['GT'] / variables['TG']
        
        return {
            'variables': variables,
            'efficiency_metrics': {
                'overall_efficiency': parameters['production_efficiency'],
                'waste_reduction': 1 - parameters['waste_percentage'],
                'customer_satisfaction': parameters['customer_retention'],
                'market_position': 1 + parameters['market_share_growth'],
                'capacity_utilization': variables['FU']
            }
        }


# Instancia global del orquestador
orchestrator = SimulationDataOrchestrator()

# Funciones de conveniencia para mantener compatibilidad
def get_simulations_by_product(product_name: str) -> List[Dict]:
    """Retorna las 3 simulaciones para un producto específico"""
    scenarios = ['optimista', 'conservador', 'pesimista']
    return [orchestrator.generate_simulation_from_questionary(product_name, scenario) 
            for scenario in scenarios]

def get_pdf_config_by_product(product_name: str) -> Dict:
    """Genera configuración PDF basada en datos del cuestionario"""
    answers = get_realistic_answers(product_name.lower())
    questionary_data = orchestrator._extract_questionary_values(answers)
    
    if questionary_data['demanda_historica']:
        mean_demand = np.mean(questionary_data['demanda_historica'])
        std_demand = np.std(questionary_data['demanda_historica'])
    else:
        mean_demand = questionary_data.get('produccion_actual', 100)
        std_demand = mean_demand * 0.1
    
    configs = {
        "leche": {
            "distribution_type": 1,  # Normal
            "mean_param": mean_demand,
            "std_dev_param": std_demand,
            "name": f"Distribución Normal - {product_name.title()}"
        },
        "queso": {
            "distribution_type": 4,  # Gamma
            "shape_param": (mean_demand / std_demand) ** 2 if std_demand > 0 else 2,
            "scale_param": std_demand ** 2 / mean_demand if mean_demand > 0 else 1,
            "name": f"Distribución Gamma - {product_name.title()}"
        },
        "yogur": {
            "distribution_type": 3,  # Log-Normal
            "mean_param": np.log(mean_demand / np.sqrt(1 + (std_demand/mean_demand)**2)) if mean_demand > 0 else 0,
            "std_dev_param": np.sqrt(np.log(1 + (std_demand/mean_demand)**2)) if mean_demand > 0 else 0.1,
            "name": f"Distribución Log-Normal - {product_name.title()}"
        }
    }
    
    # Usar configuración específica o default
    return configs.get(product_name.lower(), configs["leche"])

def create_complete_simulation(product_name: str, scenario_index: int = 0) -> Optional[Dict]:
    """Crea una configuración completa de simulación para un producto y escenario"""
    scenarios = ['optimista', 'conservador', 'pesimista']
    
    if scenario_index >= len(scenarios):
        return None
    
    simulation_config = orchestrator.generate_simulation_from_questionary(
        product_name, scenarios[scenario_index]
    )
    pdf_config = get_pdf_config_by_product(product_name)
    
    return {
        "simulation_config": simulation_config,
        "pdf_config": pdf_config,
        "product": product_name
    }

def get_result_simulation_data(product_name: str) -> Dict:
    """Genera datos de resultado basados en respuestas del cuestionario"""
    answers = get_realistic_answers(product_name.lower())
    questionary_data = orchestrator._extract_questionary_values(answers)
    
    if questionary_data['demanda_historica']:
        mean_demand = np.mean(questionary_data['demanda_historica'])
        std_demand = np.std(questionary_data['demanda_historica'])
    else:
        mean_demand = questionary_data.get('produccion_actual', 100)
        std_demand = mean_demand * 0.1
    
    # Determinar unidad según producto
    units = {
        "leche": "Litros",
        "queso": "Kilogramos", 
        "yogur": "Litros",
        "mantequilla": "Kilogramos",
        "crema de leche": "Litros",
        "leche deslactosada": "Litros",
        "dulce de leche": "Kilogramos"
    }
    
    return {
        "demand_mean": mean_demand,
        "demand_std_deviation": std_demand,
        "price_per_unit": questionary_data['precio_actual'],
        "unit": units.get(product_name.lower(), "Unidades"),
        "currency": "Bs"
    }

  
def _calculate_expected_results(self, questionary_data: Dict, parameters: Dict) -> Dict[str, float]:
    """Calcula resultados esperados basados en datos del cuestionario"""
    base_demand = np.mean(questionary_data['demanda_historica']) if questionary_data['demanda_historica'] else 100
    
    # Cálculos realistas basados en el cuestionario
    expected_demand = base_demand * (1 + parameters['growth_rate'])
    expected_sales = expected_demand * parameters['production_efficiency']
    expected_revenue = expected_sales * questionary_data['precio_actual']
    
    # Costos basados en datos reales
    production_cost = expected_sales * questionary_data['costo_unitario_insumo']
    fixed_costs = questionary_data['costo_fijo_diario'] * 30
    labor_costs = questionary_data['sueldos_empleados']
    marketing_costs = questionary_data['gastos_marketing_mensuales']
    
    total_costs = production_cost + fixed_costs + labor_costs + marketing_costs
    expected_profit = expected_revenue - total_costs
    
    return {
        "demand_mean": expected_demand,
        "demand_std_deviation": np.std(questionary_data['demanda_historica']) if questionary_data['demanda_historica'] else 10,
        "revenue_growth": parameters['growth_rate'] * parameters['production_efficiency'],
        "profit_margin": expected_profit / expected_revenue if expected_revenue > 0 else 0,
        "roi": expected_profit / total_costs if total_costs > 0 else 0,
        "capacity_utilization": expected_sales / questionary_data['capacidad_produccion'] if questionary_data['capacidad_produccion'] > 0 else 0
    }

def _get_default_value(self, field: str) -> Any:
    """Obtiene valor por defecto para campos faltantes"""
    defaults = {
        'precio_actual': 15.50,
        'demanda_historica': [100] * 30,
        'produccion_actual': 100,
        'demanda_esperada': 110,
        'capacidad_inventario': 1000,
        'costo_unitario_insumo': 8.0,
        'clientes_por_dia': 50,
        'numero_empleados': 10,
        'capacidad_produccion': 150,
        'sueldos_empleados': 30000,
        'precio_competencia': 16.0,
        'costo_fijo_diario': 1000,
        'gastos_marketing_mensuales': 2000
    }
    return defaults.get(field, 0)

def generate_simulation_results(self, simulation_config: Dict, days: int = 30) -> List[Dict]:
    """
    Genera resultados de simulación día por día utilizando la configuración
    """
    results = []
    questionary_data = simulation_config['questionary_data']
    parameters = simulation_config['parameters']
    demand_history = simulation_config['demand_history']
    
    # Variables acumulativas
    inventory = questionary_data.get('capacidad_inventario', 0) * 0.5  # Empezar con 50% inventario
    accumulated_profit = 0
    customers_served_total = 0
    
    for day in range(days):
        # Demanda del día
        daily_demand = demand_history[day] if day < len(demand_history) else np.mean(demand_history)
        
        # Cálculos diarios basados en el cuestionario
        daily_result = self._calculate_daily_variables(
            day, daily_demand, questionary_data, parameters, 
            inventory, accumulated_profit
        )
        
        # Actualizar acumulativos
        inventory = daily_result['variables']['IPF']
        accumulated_profit += daily_result['variables']['GT']
        customers_served_total += daily_result['variables']['TCAE']
        
        # Agregar metadatos
        daily_result['date'] = datetime.now().date() + timedelta(days=day)
        daily_result['demand_mean'] = daily_demand
        daily_result['demand_std_deviation'] = questionary_data.get('demand_std', 10)
        
        results.append(daily_result)
    
    return results

def _calculate_daily_variables(self, day: int, demand: float, questionary_data: Dict,
                                parameters: Dict, inventory: float, 
                                accumulated_profit: float) -> Dict[str, Any]:
    """Calcula todas las variables para un día específico"""
    
    # Variables del cuestionario
    precio = questionary_data['precio_actual']
    capacidad_prod = questionary_data['capacidad_produccion']
    costo_insumo = questionary_data['costo_unitario_insumo']
    clientes_dia = questionary_data['clientes_por_dia']
    num_empleados = questionary_data['numero_empleados']
    costo_fijo = questionary_data['costo_fijo_diario']
    
    # Aplicar eficiencias del escenario
    produccion_real = min(capacidad_prod * parameters['production_efficiency'], demand * 1.1)
    clientes_atendidos = clientes_dia * parameters['customer_retention']
    
    # Ventas limitadas por demanda, producción e inventario
    ventas_posibles = min(demand, produccion_real + inventory)
    ventas_reales = ventas_posibles * (1 - parameters['waste_percentage'])
    
    # Variables calculadas
    variables = {
        # Demanda y Ventas
        'DE': demand,
        'DH': demand,
        'TPV': ventas_reales,
        'TCAE': clientes_atendidos,
        'VPC': ventas_reales / max(clientes_atendidos, 1),
        'DI': max(0, demand - ventas_reales),
        
        # Producción
        'TPPRO': produccion_real,
        'CPROD': capacidad_prod,
        'FU': produccion_real / capacidad_prod if capacidad_prod > 0 else 0,
        'PE': ventas_reales / num_empleados if num_empleados > 0 else 0,
        
        # Inventarios
        'IPF': inventory + produccion_real - ventas_reales,
        'II': costo_insumo * produccion_real * 1.1,  # 10% extra de seguridad
        
        # Financieros - Ingresos
        'IT': ventas_reales * precio,
        'PVP': precio,
        
        # Financieros - Costos
        'CTAI': costo_insumo * produccion_real,
        'CFD': costo_fijo,
        'SE': questionary_data['sueldos_empleados'] / 30,  # Diario
        'GMM': questionary_data['gastos_marketing_mensuales'] / 30,  # Diario
        
        # Totales
        'GO': costo_fijo + (questionary_data['sueldos_empleados'] / 30) + (costo_insumo * produccion_real),
        'GG': questionary_data['gastos_marketing_mensuales'] / 30,
        'TG': 0,  # Se calcula después
        'GT': 0,  # Se calcula después
        
        # Indicadores
        'NR': 0,  # Se calcula después
        'MB': 0,  # Se calcula después
        'RI': 0,  # Se calcula después
        'RTI': 365 / max(questionary_data.get('dias_reabastecimiento', 3), 1),
        'PM': ventas_reales / demand if demand > 0 else 0,
        'NCM': parameters['competition_intensity'],
        
        # Otros
        'DIA': day + 1,
        'NMD': 30,
        'PC': questionary_data['precio_competencia'],
        'ED': parameters['seasonality_factor']
    }
    
    # Calcular totales
    variables['TG'] = variables['GO'] + variables['GG']
    variables['GT'] = variables['IT'] - variables['TG']
    
    # Calcular indicadores
    if variables['IT'] > 0:
        variables['NR'] = variables['GT'] / variables['IT']
        variables['MB'] = (variables['IT'] - variables['CTAI']) / variables['IT']
    
    if variables['TG'] > 0:
        variables['RI'] = variables['GT'] / variables['TG']
    
    return {
        'variables': variables,
        'efficiency_metrics': {
            'overall_efficiency': parameters['production_efficiency'],
            'waste_reduction': 1 - parameters['waste_percentage'],
            'customer_satisfaction': parameters['customer_retention'],
            'market_position': 1 + parameters['market_share_growth'],
            'capacity_utilization': variables['FU']
        }
    }