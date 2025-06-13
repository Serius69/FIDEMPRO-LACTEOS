# areas_data.py - Versión Optimizada con Comportamiento Dinámico por Demanda
import numpy as np
from datetime import datetime, timedelta

# Funciones para cálculo dinámico de KPIs por área
def calcular_kpi_dinamico(base, demanda_actual, demanda_promedio, factor_eficiencia=1.0):
    """Calcula KPI ajustado por demanda y eficiencia"""
    factor_demanda = demanda_actual / demanda_promedio if demanda_promedio > 0 else 1.0
    return base * factor_demanda * factor_eficiencia

def calcular_costo_operativo_area(base, nivel_actividad, dia):
    """Calcula costo operativo que varía con actividad y tiempo"""
    # Factor de actividad (más actividad = economías de escala)
    factor_actividad = 1.0
    if nivel_actividad > 0.8:
        factor_actividad = 0.95
    elif nivel_actividad < 0.5:
        factor_actividad = 1.1
    
    # Inflación gradual
    factor_inflacion = 1 + (0.00012 * dia)  # 0.012% diario
    
    return base * factor_actividad * factor_inflacion

# Datos de áreas operativas con comportamiento dinámico
areas_data = [
    {
        "name": "Abastecimiento",
        "description": """Gestión dinámica de la cadena de suministro adaptada a demanda.
        Sistema predictivo de compras basado en históricos y proyecciones.
        Negociación automática de precios según volumen y temporada.
        Evaluación continua de proveedores con scoring dinámico.""",
        "params": {
            "proveedores_leche": 5,
            "costo_litro_leche": 4.50,
            "volumen_diario_minimo": 1000,
            "volumen_diario_maximo": 5000,
            "lead_time_dias": 1,
            "calidad_minima_requerida": 0.95,
            "frecuencia_evaluacion_proveedores": "mensual",
            "descuento_por_volumen": 0.05,
            "costo_transporte_incluido": True,
            "sistema_pago": "15 días"
        },
        "kpis": {
            "nivel_servicio_proveedores": 0.98,
            "costo_total_abastecimiento": 0,
            "rotacion_proveedores": 0.1,
            "calidad_promedio_recibida": 0.97
        },
        "dynamic_behavior": {
            "cost_calculation": lambda volumen, dia, precio_mercado: 
                precio_mercado * volumen * (1 - min(0.08, volumen / 50000)) * (1 + 0.00012 * dia),
            
            "service_level": lambda entregas_tiempo, total_entregas: 
                entregas_tiempo / total_entregas if total_entregas > 0 else 0,
            
            "volume_optimization": lambda demanda_proyectada, inventario_actual, lead_time:
                max(0, demanda_proyectada * (lead_time + 1) - inventario_actual * 0.8),
            
            "supplier_scoring": lambda calidad, precio, puntualidad, volumen:
                calidad * 0.4 + (1 - precio) * 0.3 + puntualidad * 0.2 + volumen * 0.1,
            
            "seasonal_adjustment": lambda dia:
                1.1 if 152 <= dia % 365 <= 243 else 0.95 if dia % 365 >= 335 or dia % 365 <= 59 else 1.0
        },
        "optimization_rules": {
            "reorder_point": lambda demanda_promedio, lead_time, variabilidad:
                demanda_promedio * lead_time + 2 * np.sqrt(lead_time) * variabilidad,
            
            "economic_order_quantity": lambda demanda_anual, costo_pedido, costo_almacenamiento:
                np.sqrt(2 * demanda_anual * costo_pedido / costo_almacenamiento),
            
            "safety_stock": lambda demanda_std, lead_time, service_level_z:
                service_level_z * demanda_std * np.sqrt(lead_time)
        }
    },
    
    {
        "name": "Inventario Insumos",
        "description": """Control inteligente de inventarios con optimización continua.
        Sistema FIFO automático con alertas de caducidad.
        Predicción de necesidades basada en demanda y estacionalidad.
        Minimización de costos de almacenamiento y mermas.""",
        "params": {
            "capacidad_almacenamiento_litros": 10000,
            "capacidad_almacenamiento_kg": 2000,
            "temperatura_refrigeracion": 4,
            "humedad_relativa": 85,
            "nivel_inventario_actual": 0,
            "capacidad_utilizada": 0,
            "costo_inventario_diario": 80,
            "tiempo_preparacion_pedido": 30,
            "exactitud_despachos": 0.99
        },
        "kpis": {
            "fill_rate": 0.95,
            "nivel_servicio": 0.98,
            "costo_mantenimiento": 0,
            "productos_vencidos": 0.01
        },
        "dynamic_behavior": {
            "inventory_level": lambda inicial, entradas, salidas, mermas:
                max(0, inicial + entradas - salidas - mermas),
            
            "holding_cost": lambda inventario_promedio, costo_unitario, tasa_almacenamiento:
                inventario_promedio * costo_unitario * tasa_almacenamiento / 365,
            
            "spoilage_rate": lambda dias_almacenado, vida_util, temperatura_actual, temp_optima:
                min(1.0, (dias_almacenado / vida_util) * (1 + 0.1 * abs(temperatura_actual - temp_optima))),
            
            "capacity_utilization": lambda inventario_actual, capacidad_maxima:
                inventario_actual / capacidad_maxima if capacidad_maxima > 0 else 0,
            "reorder_point": lambda demanda_diaria, lead_time, seguridad=1.5:
                demanda_diaria * lead_time + seguridad * np.sqrt(demanda_diaria * lead_time)
        },
        "optimization_rules": {
            "economic_order_quantity": lambda demanda_anual, costo_pedido, costo_almacenamiento:
                np.sqrt(2 * demanda_anual * costo_pedido / costo_almacenamiento),
            
            "safety_stock": lambda demanda_std, lead_time, service_level_z:
                service_level_z * demanda_std * np.sqrt(lead_time),
            
            "optimal_reorder_quantity": lambda demanda_diaria, lead_time, costo_pedido, costo_almacenamiento:
                np.sqrt((2 * demanda_diaria * lead_time * costo_pedido) / costo_almacenamiento)
        }
    },
    {
        "name": "Producción",
        "description": """Optimización de procesos productivos con análisis en tiempo real.
        Ajuste automático de parámetros según demanda y eficiencia.
        Mantenimiento predictivo basado en datos operativos.
        Reducción de tiempos muertos y mejora continua.""",
        "params": {
            "capacidad_produccion_diaria_litros": 5000,
            "costo_produccion_litro": 2.50,
            "tiempo_ciclo_produccion_minutos": 60,
            "eficiencia_operativa": 0.85,
            "costo_mantenimiento_maquinaria": 1000,
            "costo_energia_kwh": 0.15,
            "costo_manodeobra_hora": 10,
            "nivel_calidad_producto": 0.98
        },
        "kpis": {
            "eficiencia_produccion": 0.85,
            "costo_total_produccion": 0,
            "tiempo_ciclo_promedio": 60,
            "calidad_producto_final": 0.98
        },
        "dynamic_behavior": {
            "production_efficiency": lambda produccion_real, produccion_teorica:
                produccion_real / produccion_teorica if produccion_teorica > 0 else 0,
            
            "cycle_time_adjustment": lambda tiempo_ciclo, demanda_actual, demanda_promedio:
                tiempo_ciclo * (demanda_actual / demanda_promedio) if demanda_promedio > 0 else tiempo_ciclo,
            
            "maintenance_costs": lambda dias_operativos, costo_mantenimiento_base:
                costo_mantenimiento_base * (1 + (dias_operativos / 30) * 0.02),
            
            "energy_consumption": lambda produccion_litros, consumo_por_litro:
                produccion_litros * consumo_por_litro,
            
            "labor_costs": lambda horas_trabajadas, costo_hora:
                horas_trabajadas * costo_hora
        },
        "optimization_rules": {
            "optimal_batch_size": lambda demanda_diaria, capacidad_maxima, eficiencia:
                min(capacidad_maxima, demanda_diaria / eficiencia),
            
            "cost_per_unit": lambda costo_fijo, costo_variable, volumen_producido:
                (costo_fijo + costo_variable) / volumen_producido if volumen_producido > 0 else 0,
            "production_schedule": lambda demanda_semanal, capacidad_diaria:
                demanda_semanal / capacidad_diaria if capacidad_diaria > 0 else 0,
            "maintenance_schedule": lambda horas_operativas, frecuencia_mantenimiento:
                horas_operativas / frecuencia_mantenimiento if frecuencia_mantenimiento > 0 else 0
        }
    }
]