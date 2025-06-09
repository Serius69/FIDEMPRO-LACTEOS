# simulate_data.py - Versión Actualizada
"""
Datos de configuración para simulaciones de demanda en el sector lácteo.
Utiliza los datos del questionary_result_data para generar simulaciones realistas.
"""

from datetime import datetime, timedelta
import numpy as np
from questionary.data.questionary_result_data import get_realistic_answers, questionary_result_data

def extract_answer_value(answers, variable_name):
    """Extrae el valor de una respuesta específica por nombre de variable"""
    for answer in answers:
        if answer.get('variable_name') == variable_name:
            return answer['answer']
    return None

def generate_simulation_from_questionary(product_type, scenario_type="optimista"):
    """
    Genera configuración de simulación basada en las respuestas del cuestionario
    
    Args:
        product_type: Tipo de producto ('leche', 'queso', 'yogur')
        scenario_type: Tipo de escenario ('optimista', 'conservador', 'pesimista')
    
    Returns:
        Dict con configuración de simulación
    """
    # Obtener respuestas del cuestionario para el producto
    answers = get_realistic_answers(product_type)
    
    # Extraer valores clave
    precio_actual = extract_answer_value(answers, 'precio_actual')
    demanda_historica = extract_answer_value(answers, 'demanda_historica')
    produccion_actual = extract_answer_value(answers, 'produccion_actual')
    demanda_esperada = extract_answer_value(answers, 'demanda_esperada')
    capacidad_inventario = extract_answer_value(answers, 'capacidad_inventario')
    estacionalidad = extract_answer_value(answers, 'estacionalidad')
    capacidad_produccion = extract_answer_value(answers, 'capacidad_produccion')
    numero_empleados = extract_answer_value(answers, 'numero_empleados')
    
    # Calcular estadísticas de la demanda histórica
    if demanda_historica:
        demanda_mean = np.mean(demanda_historica)
        demanda_std = np.std(demanda_historica)
    else:
        demanda_mean = produccion_actual
        demanda_std = produccion_actual * 0.1  # 10% de variación por defecto
    
    # Configurar parámetros según el escenario
    scenario_params = {
        "optimista": {
            "growth_rate": 0.05,
            "price_elasticity": -0.3,
            "market_share_growth": 0.02,
            "customer_retention": 0.95,
            "production_efficiency": 0.92,
            "waste_percentage": 0.02,
            "seasonality_factor": 1.1 if estacionalidad == 'Sí' else 1.0
        },
        "conservador": {
            "growth_rate": 0.02,
            "price_elasticity": -0.5,
            "market_share_growth": 0.01,
            "customer_retention": 0.90,
            "production_efficiency": 0.88,
            "waste_percentage": 0.03,
            "seasonality_factor": 1.05 if estacionalidad == 'Sí' else 1.0
        },
        "pesimista": {
            "growth_rate": -0.02,
            "price_elasticity": -0.8,
            "market_share_growth": -0.01,
            "customer_retention": 0.85,
            "production_efficiency": 0.82,
            "waste_percentage": 0.05,
            "seasonality_factor": 0.95 if estacionalidad == 'Sí' else 1.0
        }
    }
    
    params = scenario_params[scenario_type.lower()]
    
    # Generar proyección de demanda según escenario
    days = 30
    if scenario_type.lower() == "optimista":
        # Tendencia creciente
        demand_projection = [demanda_mean * (1 + params["growth_rate"] * (i/days)) 
                           for i in range(days)]
    elif scenario_type.lower() == "conservador":
        # Tendencia estable con ligero crecimiento
        demand_projection = [demanda_mean * (1 + params["growth_rate"] * (i/days) * 0.5) 
                           for i in range(days)]
    else:  # pesimista
        # Tendencia decreciente
        demand_projection = [demanda_mean * (1 + params["growth_rate"] * (i/days)) 
                           for i in range(days)]
    
    # Añadir variabilidad
    demand_history_sim = [
        max(0, d + np.random.normal(0, demanda_std * 0.5)) 
        for d in demand_projection
    ]
    
    return {
        "name": f"Simulación {scenario_type.title()} - {product_type.title()}",
        "product": product_type.title(),
        "scenario": scenario_type.title(),
        "description": f"Escenario {scenario_type} basado en datos reales del cuestionario",
        "unit_time": "days",
        "quantity_time": 30,
        "confidence_level": 0.95,
        "random_seed": np.random.randint(1, 100),
        "demand_history": demand_history_sim,
        "parameters": params,
        "expected_results": {
            "demand_mean": demanda_mean * (1 + params["growth_rate"]),
            "demand_std_deviation": demanda_std,
            "revenue_growth": params["growth_rate"] * 3,
            "profit_margin": 0.25 if scenario_type == "optimista" else (0.20 if scenario_type == "conservador" else 0.15),
            "roi": 0.35 if scenario_type == "optimista" else (0.25 if scenario_type == "conservador" else 0.18)
        },
        "questionary_data": {
            "precio_actual": precio_actual,
            "produccion_actual": produccion_actual,
            "demanda_esperada": demanda_esperada,
            "capacidad_inventario": capacidad_inventario,
            "capacidad_produccion": capacidad_produccion,
            "numero_empleados": numero_empleados
        }
    }

# Generar simulaciones para cada producto usando datos del cuestionario
simulation_data_leche = [
    generate_simulation_from_questionary("leche", "optimista"),
    generate_simulation_from_questionary("leche", "conservador"),
    generate_simulation_from_questionary("leche", "pesimista")
]

simulation_data_queso = [
    generate_simulation_from_questionary("queso", "optimista"),
    generate_simulation_from_questionary("queso", "conservador"),
    generate_simulation_from_questionary("queso", "pesimista")
]

simulation_data_yogur = [
    generate_simulation_from_questionary("yogur", "optimista"),
    generate_simulation_from_questionary("yogur", "conservador"),
    generate_simulation_from_questionary("yogur", "pesimista")
]

# Función para generar resultados de simulación dinámicos
def generate_simulation_results(simulation_config, days=30):
    """
    Genera resultados de simulación basados en la configuración proporcionada
    """
    np.random.seed(simulation_config.get("random_seed", 42))
    
    results = []
    base_demand = simulation_config["expected_results"]["demand_mean"]
    std_dev = simulation_config["expected_results"]["demand_std_deviation"]
    params = simulation_config["parameters"]
    questionary = simulation_config.get("questionary_data", {})
    
    # Extraer datos adicionales del cuestionario
    precio = questionary.get("precio_actual", 15.5)
    capacidad_prod = questionary.get("capacidad_produccion", base_demand * 1.2)
    num_empleados = questionary.get("numero_empleados", 15)
    
    for day in range(days):
        # Calcular demanda con tendencia y variabilidad
        trend = (1 + params["growth_rate"]) ** (day / 30)
        seasonal = params["seasonality_factor"] if (day % 7) in [5, 6] else 1.0
        daily_demand = base_demand * trend * seasonal + np.random.normal(0, std_dev * 0.3)
        daily_demand = max(0, daily_demand)  # Asegurar que no sea negativa
        
        # Calcular otras variables basadas en la demanda y datos del cuestionario
        daily_result = {
            "date": datetime.now().date() + timedelta(days=day),
            "demand_mean": daily_demand,
            "demand_std_deviation": std_dev * (1 + np.random.normal(0, 0.02)),
            "variables": {
                # Variables de producción y ventas
                "TPV": daily_demand * (1 - params["waste_percentage"]),
                "TPPRO": min(daily_demand * 1.1, capacidad_prod),  # Limitado por capacidad
                "DI": max(0, daily_demand - capacidad_prod) if daily_demand > capacidad_prod else 0,
                "VPC": daily_demand / max(1, questionary.get("clientes_diarios", 85)),
                
                # Variables financieras
                "IT": daily_demand * precio,
                "GT": daily_demand * precio * params["profit_margin"],
                "NR": params["profit_margin"],
                "MB": params["profit_margin"] * 1.2,
                "RI": simulation_config["expected_results"]["roi"],
                
                # Variables de eficiencia
                "FU": min(daily_demand / capacidad_prod, 1.0),  # Utilización de capacidad
                "PE": daily_demand / num_empleados,
                "PM": 0.15 + params["market_share_growth"],
                
                # Variables de inventario
                "IPF": min(daily_demand * 1.5, questionary.get("capacidad_inventario", daily_demand * 2)),
                "RTI": 365 / (questionary.get("dias_reabastecimiento", 3)),
                
                # Variables operativas
                "CPROD": capacidad_prod,
                "ED": params.get("seasonality_factor", 1.0),
                "NCM": params.get("competition_intensity", 0.5),
                
                # Variables de costos (usando datos del cuestionario)
                "CFD": questionary.get("costo_fijo_diario", 1800),
                "CUT": questionary.get("costo_transporte", 0.35),
                "CUI": questionary.get("costo_unitario_insumo", 8.20),
            },
            "efficiency_metrics": {
                "overall_efficiency": params["production_efficiency"],
                "waste_reduction": 1 - params["waste_percentage"],
                "customer_satisfaction": params["customer_retention"],
                "market_position": 1 + params["market_share_growth"],
                "capacity_utilization": min(daily_demand / capacidad_prod, 1.0)
            }
        }
        
        results.append(daily_result)
    
    return results

# Consolidar todas las simulaciones
all_simulations = {
    "leche": simulation_data_leche,
    "queso": simulation_data_queso,
    "yogur": simulation_data_yogur
}

# Función para obtener simulaciones por producto
def get_simulations_by_product(product_name):
    """Retorna las 3 simulaciones para un producto específico"""
    return all_simulations.get(product_name.lower(), [])

# Configuración para inicialización de PDF por producto basada en datos del cuestionario
def get_pdf_config_by_product(product_name):
    """Genera configuración PDF basada en datos del cuestionario"""
    answers = get_realistic_answers(product_name.lower())
    demanda_historica = extract_answer_value(answers, 'demanda_historica')
    
    if demanda_historica:
        mean_demand = np.mean(demanda_historica)
        std_demand = np.std(demanda_historica)
    else:
        mean_demand = extract_answer_value(answers, 'produccion_actual') or 100
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
            "shape_param": (mean_demand / std_demand) ** 2,
            "scale_param": std_demand ** 2 / mean_demand,
            "name": f"Distribución Gamma - {product_name.title()}"
        },
        "yogur": {
            "distribution_type": 3,  # Log-Normal
            "mean_param": np.log(mean_demand / np.sqrt(1 + (std_demand/mean_demand)**2)),
            "std_dev_param": np.sqrt(np.log(1 + (std_demand/mean_demand)**2)),
            "name": f"Distribución Log-Normal - {product_name.title()}"
        }
    }
    
    return configs.get(product_name.lower(), configs["leche"])

# Función helper para crear simulación completa
def create_complete_simulation(product_name, scenario_index=0):
    """
    Crea una configuración completa de simulación para un producto y escenario
    """
    simulations = get_simulations_by_product(product_name)
    if not simulations or scenario_index >= len(simulations):
        return None
    
    simulation = simulations[scenario_index].copy()
    pdf_config = get_pdf_config_by_product(product_name)
    
    return {
        "simulation_config": simulation,
        "pdf_config": pdf_config,
        "product": product_name
    }

# Datos de ejemplo para ResultSimulation basados en el cuestionario
def get_result_simulation_data(product_name):
    """Genera datos de resultado basados en respuestas del cuestionario"""
    answers = get_realistic_answers(product_name.lower())
    
    precio = extract_answer_value(answers, 'precio_actual')
    demanda_historica = extract_answer_value(answers, 'demanda_historica')
    
    if demanda_historica:
        mean_demand = np.mean(demanda_historica)
        std_demand = np.std(demanda_historica)
    else:
        mean_demand = extract_answer_value(answers, 'produccion_actual') or 100
        std_demand = mean_demand * 0.1
    
    # Determinar unidad según producto
    units = {
        "leche": "Litros",
        "queso": "Kilogramos",
        "yogur": "Litros"
    }
    
    return {
        "demand_mean": mean_demand,
        "demand_std_deviation": std_demand,
        "price_per_unit": precio,
        "unit": units.get(product_name.lower(), "Unidades"),
        "currency": "Bs"
    }

# Datos de funciones de densidad probabilística
pdf_data = [
    {
        "name": "Distribución Normal - Demanda Estándar",
        "distribution_type": 1,
        "mean_param": 2500.0,
        "std_dev_param": 250.0,
        "cumulative_distribution_function": 0.5,
        "description": "Modelo de demanda normal para productos lácteos con variación estándar"
    },
    {
        "name": "Distribución Exponencial - Tiempos Entre Pedidos",
        "distribution_type": 2,
        "lambda_param": 0.2,
        "cumulative_distribution_function": 0.63,
        "description": "Modela el tiempo entre pedidos de clientes mayoristas"
    },
    {
        "name": "Distribución Log-Normal - Demanda Variable",
        "distribution_type": 3,
        "mean_param": 7.5,
        "std_dev_param": 0.5,
        "cumulative_distribution_function": 0.5,
        "description": "Para productos con demanda altamente variable"
    },
    {
        "name": "Distribución Gamma - Demanda Estacional",
        "distribution_type": 4,
        "shape_param": 3.0,
        "scale_param": 800.0,
        "cumulative_distribution_function": 0.58,
        "description": "Modela demanda con estacionalidad marcada"
    },
    {
        "name": "Distribución Uniforme - Demanda Constante",
        "distribution_type": 5,
        "min_param": 2000.0,
        "max_param": 3000.0,
        "cumulative_distribution_function": 0.5,
        "description": "Para productos con demanda estable y predecible"
    }
]