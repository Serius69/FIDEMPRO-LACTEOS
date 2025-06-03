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

# Configuración base para simulación
simulation_data = {
    "unit_time": "day",
    "quantity_time": 30,  # 30 días de simulación
    "confidence_level": 0.95,  # Nivel de confianza del 95%
    "random_seed": 42,  # Para reproducibilidad
    "fk_fdp": 1,  # ID de función de densidad (se asignará dinámicamente)
    "demand_history": None,  # Se generará dinámicamente
    "fk_questionary_result": None,  # Se asignará dinámicamente
}

# Generador de demanda histórica realista
def generate_realistic_demand_history(days=30, base_demand=2500, seasonality=True):
    """
    Genera datos históricos de demanda realistas para productos lácteos.
    
    Args:
        days: Número de días de historia
        base_demand: Demanda base diaria en litros
        seasonality: Si incluir patrones estacionales
    
    Returns:
        Lista de valores de demanda diaria
    """
    np.random.seed(42)  # Para reproducibilidad
    
    # Componente base
    demand = np.ones(days) * base_demand
    
    # Tendencia ligera (crecimiento del 0.1% diario)
    trend = np.linspace(0, 0.03 * base_demand, days)
    demand += trend
    
    # Componente estacional (si está habilitado)
    if seasonality:
        # Patrón semanal (mayor demanda los fines de semana)
        weekly_pattern = np.array([0.9, 0.95, 1.0, 1.0, 1.1, 1.2, 1.15])
        for i in range(days):
            demand[i] *= weekly_pattern[i % 7]
    
    # Ruido aleatorio (±10%)
    noise = np.random.normal(0, 0.1 * base_demand, days)
    demand += noise
    
    # Eventos especiales (picos ocasionales)
    n_events = int(days / 10)  # Un evento cada 10 días aproximadamente
    event_days = np.random.choice(days, n_events, replace=False)
    for day in event_days:
        demand[day] *= np.random.uniform(1.2, 1.5)  # Incremento del 20-50%
    
    # Asegurar que no hay valores negativos
    demand = np.maximum(demand, base_demand * 0.5)
    
    return demand.round().astype(int).tolist()

# Actualizar simulation_data con demanda histórica realista
simulation_data["demand_history"] = generate_realistic_demand_history()

# Datos de ejemplo para ResultSimulation
result_simulation_data = {
    "demand_mean": 2500.0,
    "demand_std_deviation": 250.0,
    "date": datetime.now().date(),
    "variables": {
        # Variables de costos
        "CTR": 3500.0,      # Costo Total Reorden
        "CTAI": 12000.0,    # Costo Total Adquisición Insumos
        "CPP": 8.5,         # Costo Promedio Producción
        "CPV": 7.2,         # Costo Promedio Venta
        "CPI": 4.3,         # Costo Promedio Insumos
        "CPMO": 2.8,        # Costo Promedio Mano Obra
        "CUP": 15.6,        # Costo Unitario Producción
        "CTTL": 1800.0,     # Costo Total Transporte
        "CUI": 0.5,         # Costo Unitario Inventario
        "CA": 2200.0,       # Costo Almacenamiento
        "CHO": 450.0,       # Costo Horas Ociosas
        
        # Variables de producción
        "TPV": 2450.0,      # Total Productos Vendidos
        "TPPRO": 2600.0,    # Total Productos Producidos
        "CPROD": 3000.0,    # Capacidad Producción
        "PPL": 2600.0,      # Productos Producidos
        "FU": 0.87,         # Factor Utilización
        
        # Variables de inventario
        "II": 8500.0,       # Inventario Insumos
        "IPF": 4200.0,      # Inventario Productos Finales
        "PI": 15000.0,      # Pedido Insumos
        "UII": 12000.0,     # Uso Inventario Insumos
        
        # Variables de ventas y demanda
        "DI": 150.0,        # Demanda Insatisfecha
        "VPC": 35.0,        # Ventas por Cliente
        "DE": 2600.0,       # Demanda Esperada
        "DT": 2600.0,       # Demanda Total
        "TCA": 70.0,        # Total Clientes Atendidos
        "TCAE": 70.0,       # Total Clientes Atendidos en el Día
        
        # Variables financieras
        "IT": 36750.0,      # Ingresos Totales
        "GT": 28600.0,      # Ganancias Totales
        "GO": 18500.0,      # Gastos Operativos
        "GG": 21000.0,      # Gastos Generales
        "TG": 32000.0,      # Total Gastos
        "IB": 4750.0,       # Ingreso Bruto
        "MB": 0.13,         # Margen Bruto
        "NR": 0.22,         # Nivel Rentabilidad
        "RI": 0.17,         # Retorno Inversión
        
        # Variables de recursos humanos
        "NEPP": 12.0,       # Número Empleados
        "SE": 8400.0,       # Sueldos Empleados
        "PE": 0.29,         # Productividad Empleados
        "HO": 16.0,         # Horas Ociosas
        
        # Variables de mercado
        "PM": 0.15,         # Participación Mercado
        "PC": 16.5,         # Precio Competencia
        "NCM": -1.5,        # Nivel Competencia Mercado
        "RTI": 0.71,        # Rotación Inventario
        "RTC": 35.0,        # Rotación Clientes
    },
    "areas": {
        "Abastecimiento": {"efficiency": 0.92, "cost": 15000.0},
        "Inventario Insumos": {"efficiency": 0.88, "cost": 2200.0},
        "Producción": {"efficiency": 0.87, "cost": 18500.0},
        "Inspección": {"efficiency": 0.95, "cost": 1200.0},
        "Inventario Productos Finales": {"efficiency": 0.90, "cost": 2200.0},
        "Distribución": {"efficiency": 0.85, "cost": 1800.0},
        "Ventas": {"efficiency": 0.91, "cost": 3500.0},
        "Competencia": {"market_share": 0.15, "position": "3rd"},
        "Marketing": {"roi": 2.3, "cost": 2500.0},
        "Contabilidad": {"accuracy": 0.99, "cost": 1500.0},
        "Recursos Humanos": {"satisfaction": 0.82, "cost": 800.0},
        "Mantenimiento": {"uptime": 0.96, "cost": 1800.0}
    },
    "confidence_intervals": {
        "demand_mean": {"lower": 2400.0, "upper": 2600.0},
        "IT": {"lower": 35000.0, "upper": 38500.0},
        "GT": {"lower": 27000.0, "upper": 30200.0}
    },
    "unit": {"measurement": "litros", "value": 1},
    "unit_time": {"time_unit": "día", "value": 1},
    "results": {
        "efficiency_score": 89.5,
        "profitability_index": 0.22,
        "market_position": 3,
        "growth_rate": 0.03,
        "risk_score": 0.15
    },
    "fk_simulation": None,  # Se asignará dinámicamente
}

# Función para generar múltiples días de resultados
def generate_simulation_results(simulation_days=30, base_date=None):
    """
    Genera resultados de simulación para múltiples días.
    
    Args:
        simulation_days: Número de días a simular
        base_date: Fecha base para la simulación
    
    Returns:
        Lista de diccionarios con resultados diarios
    """
    if base_date is None:
        base_date = datetime.now().date()
    
    results = []
    base_data = result_simulation_data.copy()
    
    for day in range(simulation_days):
        daily_result = base_data.copy()
        current_date = base_date + timedelta(days=day)
        
        # Variar algunos valores diariamente
        daily_variation = np.random.normal(1.0, 0.05)  # ±5% variación
        
        daily_result["date"] = current_date
        daily_result["demand_mean"] = base_data["demand_mean"] * daily_variation
        daily_result["demand_std_deviation"] = base_data["demand_std_deviation"] * (1 + np.random.normal(0, 0.02))
        
        # Actualizar algunas variables clave
        variables = daily_result["variables"].copy()
        for key in ["TPV", "IT", "GT", "DI", "TCA"]:
            if key in variables:
                variables[key] = variables[key] * daily_variation
        
        daily_result["variables"] = variables
        results.append(daily_result)
    
    return results

# Datos de configuración de demanda para diferentes productos
demand_configurations = {
    "leche": {
        "base_demand": 3000,
        "seasonality": True,
        "growth_rate": 0.02,
        "volatility": 0.1
    },
    "yogurt": {
        "base_demand": 1500,
        "seasonality": True,
        "growth_rate": 0.05,
        "volatility": 0.15
    },
    "queso": {
        "base_demand": 800,
        "seasonality": False,
        "growth_rate": 0.01,
        "volatility": 0.08
    }
}