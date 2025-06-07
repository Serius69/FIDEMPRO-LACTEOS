# simulate_data.py - Versión Final
"""
Datos de configuración para simulaciones de demanda en el sector lácteo.
Incluye configuraciones de funciones de densidad probabilística y parámetros de simulación.
"""

from datetime import datetime, timedelta
import numpy as np

# Datos de funciones de densidad probabilística para análisis de demanda
pdf_data = [
    {
        "name": "Distribución Normal - Demanda Estándar",
        "distribution_type": 1,  # Normal
        "mean_param": 2500.0,  # Demanda promedio diaria en litros
        "std_dev_param": 250.0,  # Desviación estándar
        "cumulative_distribution_function": 0.5,  # CDF en la media
        "description": "Modelo de demanda normal para productos lácteos con variación estándar"
    },
    {
        "name": "Distribución Exponencial - Tiempos Entre Pedidos",
        "distribution_type": 2,  # Exponential
        "lambda_param": 0.2,  # Tasa de llegada (5 días promedio entre pedidos)
        "cumulative_distribution_function": 0.63,  # CDF en λ=1
        "description": "Modela el tiempo entre pedidos de clientes mayoristas"
    },
    {
        "name": "Distribución Log-Normal - Demanda Variable",
        "distribution_type": 3,  # Log-Normal
        "mean_param": 7.5,  # Log(media) ≈ 1800 litros
        "std_dev_param": 0.5,  # Desviación en escala logarítmica
        "cumulative_distribution_function": 0.5,
        "description": "Para productos con demanda altamente variable (yogurt premium)"
    },
    {
        "name": "Distribución Gamma - Demanda Estacional",
        "distribution_type": 4,  # Gamma
        "shape_param": 3.0,  # Parámetro de forma
        "scale_param": 800.0,  # Parámetro de escala
        "cumulative_distribution_function": 0.58,
        "description": "Modela demanda con estacionalidad marcada"
    },
    {
        "name": "Distribución Uniforme - Demanda Constante",
        "distribution_type": 5,  # Uniform
        "min_param": 2000.0,  # Demanda mínima
        "max_param": 3000.0,  # Demanda máxima
        "cumulative_distribution_function": 0.5,
        "description": "Para productos con demanda estable y predecible"
    }
]

# Simulaciones para LECHE
simulation_data_leche = [
    {
        "name": "Simulación Optimista - Leche",
        "product": "Leche",
        "scenario": "Optimista",
        "description": "Escenario con crecimiento sostenido y condiciones favorables del mercado",
        "unit_time": "days",
        "quantity_time": 30,
        "confidence_level": 0.95,
        "random_seed": 42,
        "demand_history": [2450, 2480, 2520, 2560, 2590, 2610, 2640, 2670, 2690, 2720,
                          2740, 2760, 2780, 2800, 2820, 2830, 2850, 2870, 2880, 2900,
                          2910, 2920, 2930, 2940, 2950, 2960, 2970, 2980, 2990, 3000],
        "parameters": {
            "growth_rate": 0.05,  # 5% crecimiento mensual
            "price_elasticity": -0.3,  # Baja elasticidad
            "market_share_growth": 0.02,  # 2% crecimiento participación
            "customer_retention": 0.95,  # 95% retención
            "production_efficiency": 0.92,  # 92% eficiencia
            "waste_percentage": 0.02,  # 2% desperdicio
            "seasonality_factor": 1.1  # 10% aumento estacional
        },
        "expected_results": {
            "demand_mean": 2850.0,
            "demand_std_deviation": 180.0,
            "revenue_growth": 0.15,
            "profit_margin": 0.25,
            "roi": 0.35
        }
    },
    {
        "name": "Simulación Conservadora - Leche",
        "product": "Leche",
        "scenario": "Conservador",
        "description": "Escenario con crecimiento moderado y condiciones estables",
        "unit_time": "days",
        "quantity_time": 30,
        "confidence_level": 0.95,
        "random_seed": 43,
        "demand_history": [2450, 2460, 2470, 2480, 2490, 2500, 2510, 2520, 2530, 2540,
                          2550, 2560, 2570, 2580, 2590, 2600, 2610, 2620, 2630, 2640,
                          2650, 2660, 2670, 2680, 2690, 2700, 2710, 2720, 2730, 2740],
        "parameters": {
            "growth_rate": 0.02,  # 2% crecimiento mensual
            "price_elasticity": -0.5,  # Elasticidad moderada
            "market_share_growth": 0.01,  # 1% crecimiento
            "customer_retention": 0.90,  # 90% retención
            "production_efficiency": 0.88,  # 88% eficiencia
            "waste_percentage": 0.03,  # 3% desperdicio
            "seasonality_factor": 1.05  # 5% variación estacional
        },
        "expected_results": {
            "demand_mean": 2600.0,
            "demand_std_deviation": 120.0,
            "revenue_growth": 0.08,
            "profit_margin": 0.20,
            "roi": 0.25
        }
    },
    {
        "name": "Simulación Pesimista - Leche",
        "product": "Leche",
        "scenario": "Pesimista",
        "description": "Escenario con competencia agresiva y condiciones adversas",
        "unit_time": "days",
        "quantity_time": 30,
        "confidence_level": 0.95,
        "random_seed": 44,
        "demand_history": [2450, 2440, 2430, 2420, 2410, 2400, 2390, 2380, 2370, 2360,
                          2350, 2340, 2330, 2320, 2310, 2300, 2290, 2280, 2270, 2260,
                          2250, 2240, 2230, 2220, 2210, 2200, 2190, 2180, 2170, 2160],
        "parameters": {
            "growth_rate": -0.02,  # -2% decrecimiento
            "price_elasticity": -0.8,  # Alta elasticidad
            "market_share_growth": -0.01,  # Pérdida de mercado
            "customer_retention": 0.85,  # 85% retención
            "production_efficiency": 0.82,  # 82% eficiencia
            "waste_percentage": 0.05,  # 5% desperdicio
            "seasonality_factor": 0.95  # -5% caída estacional
        },
        "expected_results": {
            "demand_mean": 2300.0,
            "demand_std_deviation": 150.0,
            "revenue_growth": -0.05,
            "profit_margin": 0.15,
            "roi": 0.18
        }
    }
]

# Simulaciones para QUESO
simulation_data_queso = [
    {
        "name": "Simulación Expansión - Queso",
        "product": "Queso",
        "scenario": "Expansión",
        "description": "Apertura de nuevos mercados y líneas de productos premium",
        "unit_time": "days",
        "quantity_time": 30,
        "confidence_level": 0.95,
        "random_seed": 45,
        "demand_history": [180, 185, 190, 195, 200, 205, 210, 215, 220, 225,
                          230, 235, 240, 245, 250, 255, 260, 265, 270, 275,
                          280, 285, 290, 295, 300, 305, 310, 315, 320, 325],
        "parameters": {
            "growth_rate": 0.08,  # 8% crecimiento por expansión
            "price_elasticity": -0.4,  # Producto premium
            "market_share_growth": 0.03,  # 3% nuevos mercados
            "customer_retention": 0.93,  # Alta fidelidad
            "production_efficiency": 0.90,  # Buena eficiencia
            "waste_percentage": 0.025,  # Control de calidad
            "seasonality_factor": 1.15,  # Demanda festiva
            "new_product_lines": 3  # 3 nuevas variedades
        },
        "expected_results": {
            "demand_mean": 252.0,
            "demand_std_deviation": 45.0,
            "revenue_growth": 0.25,
            "profit_margin": 0.30,
            "roi": 0.40
        }
    },
    {
        "name": "Simulación Estabilidad - Queso",
        "product": "Queso",
        "scenario": "Estable",
        "description": "Mantenimiento de operaciones actuales con mejoras incrementales",
        "unit_time": "days",
        "quantity_time": 30,
        "confidence_level": 0.95,
        "random_seed": 46,
        "demand_history": [180, 182, 184, 186, 188, 190, 192, 194, 196, 198,
                          200, 198, 196, 194, 192, 190, 188, 186, 184, 182,
                          180, 182, 184, 186, 188, 190, 192, 194, 196, 198],
        "parameters": {
            "growth_rate": 0.01,  # 1% crecimiento estable
            "price_elasticity": -0.6,  # Elasticidad normal
            "market_share_growth": 0.0,  # Sin cambios
            "customer_retention": 0.88,  # Retención estable
            "production_efficiency": 0.85,  # Eficiencia promedio
            "waste_percentage": 0.04,  # 4% desperdicio
            "seasonality_factor": 1.0,  # Sin estacionalidad
            "quality_consistency": 0.95  # 95% consistencia
        },
        "expected_results": {
            "demand_mean": 190.0,
            "demand_std_deviation": 8.0,
            "revenue_growth": 0.03,
            "profit_margin": 0.22,
            "roi": 0.28
        }
    },
    {
        "name": "Simulación Crisis - Queso",
        "product": "Queso",
        "scenario": "Crisis",
        "description": "Escasez de materia prima y aumento de costos de producción",
        "unit_time": "days",
        "quantity_time": 30,
        "confidence_level": 0.95,
        "random_seed": 47,
        "demand_history": [180, 175, 170, 165, 160, 155, 150, 145, 140, 135,
                          130, 125, 120, 115, 110, 105, 100, 105, 110, 115,
                          120, 125, 130, 135, 140, 145, 150, 155, 160, 165],
        "parameters": {
            "growth_rate": -0.03,  # -3% contracción
            "price_elasticity": -1.0,  # Alta sensibilidad al precio
            "market_share_growth": -0.02,  # Pérdida de mercado
            "customer_retention": 0.80,  # Baja retención
            "production_efficiency": 0.75,  # Baja eficiencia
            "waste_percentage": 0.06,  # Mayor desperdicio
            "seasonality_factor": 0.90,  # Caída de demanda
            "raw_material_shortage": 0.20  # 20% escasez
        },
        "expected_results": {
            "demand_mean": 140.0,
            "demand_std_deviation": 25.0,
            "revenue_growth": -0.15,
            "profit_margin": 0.10,
            "roi": 0.12
        }
    }
]

# Simulaciones para YOGUR
simulation_data_yogur = [
    {
        "name": "Simulación Innovación - Yogur",
        "product": "Yogur",
        "scenario": "Innovación",
        "description": "Lanzamiento de línea probiótica y sabores exóticos",
        "unit_time": "days",
        "quantity_time": 30,
        "confidence_level": 0.95,
        "random_seed": 48,
        "demand_history": [320, 330, 340, 350, 360, 370, 380, 390, 400, 410,
                          420, 430, 440, 450, 460, 470, 480, 490, 500, 510,
                          520, 530, 540, 550, 560, 570, 580, 590, 600, 610],
        "parameters": {
            "growth_rate": 0.10,  # 10% crecimiento por innovación
            "price_elasticity": -0.3,  # Premium positioning
            "market_share_growth": 0.04,  # 4% captura de mercado
            "customer_retention": 0.92,  # Alta satisfacción
            "production_efficiency": 0.88,  # Buena eficiencia
            "waste_percentage": 0.03,  # Control estricto
            "seasonality_factor": 1.20,  # Alta demanda verano
            "innovation_index": 0.85,  # Alto nivel innovación
            "health_trend_factor": 1.15  # Tendencia saludable
        },
        "expected_results": {
            "demand_mean": 465.0,
            "demand_std_deviation": 80.0,
            "revenue_growth": 0.35,
            "profit_margin": 0.28,
            "roi": 0.45
        }
    },
    {
        "name": "Simulación Competencia - Yogur",
        "product": "Yogur",
        "scenario": "Competitivo",
        "description": "Mercado saturado con múltiples competidores",
        "unit_time": "days",
        "quantity_time": 30,
        "confidence_level": 0.95,
        "random_seed": 49,
        "demand_history": [320, 318, 316, 314, 312, 310, 308, 306, 304, 302,
                          300, 302, 304, 306, 308, 310, 312, 314, 316, 318,
                          320, 318, 316, 314, 312, 310, 308, 306, 304, 302],
        "parameters": {
            "growth_rate": -0.01,  # Ligera contracción
            "price_elasticity": -0.9,  # Alta sensibilidad precio
            "market_share_growth": -0.005,  # Pérdida marginal
            "customer_retention": 0.85,  # Retención media
            "production_efficiency": 0.83,  # Eficiencia regular
            "waste_percentage": 0.04,  # Desperdicio normal
            "seasonality_factor": 1.05,  # Leve estacionalidad
            "competition_intensity": 0.80,  # Alta competencia
            "price_pressure": 0.15  # 15% presión en precios
        },
        "expected_results": {
            "demand_mean": 310.0,
            "demand_std_deviation": 8.0,
            "revenue_growth": -0.02,
            "profit_margin": 0.18,
            "roi": 0.20
        }
    },
    {
        "name": "Simulación Nicho - Yogur",
        "product": "Yogur",
        "scenario": "Nicho Premium",
        "description": "Enfoque en segmento premium con productos especializados",
        "unit_time": "days",
        "quantity_time": 30,
        "confidence_level": 0.95,
        "random_seed": 50,
        "demand_history": [320, 325, 330, 335, 340, 345, 350, 355, 360, 365,
                          370, 375, 380, 385, 390, 395, 400, 405, 410, 415,
                          420, 425, 430, 435, 440, 445, 450, 455, 460, 465],
        "parameters": {
            "growth_rate": 0.06,  # 6% crecimiento nicho
            "price_elasticity": -0.2,  # Baja elasticidad
            "market_share_growth": 0.02,  # Segmento específico
            "customer_retention": 0.95,  # Muy alta fidelidad
            "production_efficiency": 0.85,  # Producción artesanal
            "waste_percentage": 0.02,  # Mínimo desperdicio
            "seasonality_factor": 1.10,  # Moderada estacionalidad
            "premium_factor": 1.40,  # 40% precio premium
            "exclusivity_index": 0.90  # Alta exclusividad
        },
        "expected_results": {
            "demand_mean": 392.0,
            "demand_std_deviation": 45.0,
            "revenue_growth": 0.20,
            "profit_margin": 0.35,
            "roi": 0.50
        }
    }
]

# Función para generar resultados de simulación dinámicos
def generate_simulation_results(simulation_config, days=30):
    """
    Genera resultados de simulación basados en la configuración proporcionada
    
    Args:
        simulation_config: Diccionario con parámetros de simulación
        days: Número de días a simular
    
    Returns:
        Lista de resultados diarios con todas las variables calculadas
    """
    np.random.seed(simulation_config.get("random_seed", 42))
    
    results = []
    base_demand = simulation_config["expected_results"]["demand_mean"]
    std_dev = simulation_config["expected_results"]["demand_std_deviation"]
    params = simulation_config["parameters"]
    
    for day in range(days):
        # Calcular demanda con tendencia y variabilidad
        trend = (1 + params["growth_rate"]) ** (day / 30)
        seasonal = params["seasonality_factor"] if (day % 7) in [5, 6] else 1.0
        daily_demand = base_demand * trend * seasonal + np.random.normal(0, std_dev)
        
        # Calcular otras variables basadas en la demanda
        daily_result = {
            "date": datetime.now().date() + timedelta(days=day),
            "demand_mean": daily_demand,
            "demand_std_deviation": std_dev * (1 + np.random.normal(0, 0.02)),
            "variables": {
                # Variables de producción y ventas
                "TPV": daily_demand * (1 - params["waste_percentage"]),
                "TPPRO": daily_demand * 1.1,  # 10% más producción que demanda
                "DI": max(0, daily_demand * 0.05),  # 5% demanda insatisfecha
                "VPC": daily_demand / 85,  # Ventas por cliente
                
                # Variables financieras
                "IT": daily_demand * simulation_config.get("price", 15.5),
                "GT": daily_demand * simulation_config.get("price", 15.5) * params["profit_margin"],
                "NR": params["profit_margin"],
                "MB": params["profit_margin"] * 1.2,
                "RI": simulation_config["expected_results"]["roi"],
                
                # Variables de eficiencia
                "FU": params["production_efficiency"],
                "PE": daily_demand / 15,  # Productividad por empleado
                "PM": 0.15 + params["market_share_growth"],
                
                # Variables de inventario
                "IPF": daily_demand * 1.5,  # 1.5 días de inventario
                "RTI": 0.67,  # Rotación cada 1.5 días
                
                # Otras variables relevantes
                "CPROD": daily_demand * 1.2,  # Capacidad 20% mayor
                "ED": params.get("seasonality_factor", 1.0),
                "NCM": params.get("competition_intensity", 0.5),
            },
            "efficiency_metrics": {
                "overall_efficiency": params["production_efficiency"],
                "waste_reduction": 1 - params["waste_percentage"],
                "customer_satisfaction": params["customer_retention"],
                "market_position": 1 + params["market_share_growth"]
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

# Configuración para inicialización de PDF por producto
pdf_config_by_product = {
    "leche": {
        "distribution_type": 1,  # Normal
        "mean_param": 2500.0,
        "std_dev_param": 250.0,
        "name": "Distribución Normal - Leche"
    },
    "queso": {
        "distribution_type": 4,  # Gamma
        "shape_param": 3.0,
        "scale_param": 60.0,  # Ajustado para queso
        "name": "Distribución Gamma - Queso"
    },
    "yogur": {
        "distribution_type": 3,  # Log-Normal
        "mean_param": 5.8,  # log(330) ≈ 5.8
        "std_dev_param": 0.15,
        "name": "Distribución Log-Normal - Yogur"
    }
}

# Función helper para crear simulación completa
def create_complete_simulation(product_name, scenario_index=0):
    """
    Crea una configuración completa de simulación para un producto y escenario
    
    Args:
        product_name: Nombre del producto ('leche', 'queso', 'yogur')
        scenario_index: Índice del escenario (0=optimista/expansión, 1=conservador/estable, 2=pesimista/crisis)
    
    Returns:
        Dict con configuración completa de simulación
    """
    simulations = get_simulations_by_product(product_name)
    if not simulations or scenario_index >= len(simulations):
        return None
    
    simulation = simulations[scenario_index].copy()
    pdf_config = pdf_config_by_product.get(product_name.lower(), {})
    
    return {
        "simulation_config": simulation,
        "pdf_config": pdf_config,
        "product": product_name
    }

# Datos de ejemplo para ResultSimulation mejorado por producto
result_simulation_data_by_product = {
    "leche": {
        "demand_mean": 2500.0,
        "demand_std_deviation": 250.0,
        "price_per_unit": 15.50,
        "unit": "Litros",
        "currency": "Bs"
    },
    "queso": {
        "demand_mean": 185.0,
        "demand_std_deviation": 20.0,
        "price_per_unit": 85.00,
        "unit": "Kilogramos",
        "currency": "Bs"
    },
    "yogur": {
        "demand_mean": 330.0,
        "demand_std_deviation": 35.0,
        "price_per_unit": 22.00,
        "unit": "Litros",
        "currency": "Bs"
    }
}