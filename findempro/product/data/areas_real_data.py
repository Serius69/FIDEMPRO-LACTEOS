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
            
            "optimal_inventory": lambda demanda_diaria, lead_time, costo_faltante, costo_mantener:
                demanda_diaria * lead_time * np.sqrt(costo_faltante / (costo_faltante + costo_mantener))
        },
        "alerts": {
            "low_stock": lambda actual, minimo: actual < minimo * 1.2,
            "expiry_warning": lambda dias_restantes: dias_restantes <= 2,
            "overstock": lambda actual, maximo: actual > maximo * 0.9
        }
    },
    
    {
        "name": "Producción",
        "description": """Centro de producción adaptativo con optimización en tiempo real.
        Ajuste automático de capacidad según demanda proyectada.
        Balanceo de líneas y asignación dinámica de recursos.
        Mantenimiento predictivo basado en horas de operación.""",
        "params": {
            "capacidad_produccion_diaria": 3000,
            "lineas_produccion": 2,
            "turnos_trabajo": 2,
            "horas_por_turno": 8,
            "eficiencia_global": 0.85,
            "automatizacion_nivel": 0.7,
            "flexibilidad_productos": 0.8,
            "mantenimiento_preventivo": True,
            "certificaciones": ["HACCP", "ISO 9001"],
            "costo_hora_produccion": 500
        },
        "kpis": {
            "oee_overall_equipment_effectiveness": 0.85,
            "productividad_mano_obra": 0,
            "costo_unitario_produccion": 0,
            "tasa_defectos": 0.01
        },
        "dynamic_behavior": {
            "production_planning": lambda demanda, inventario, capacidad, eficiencia:
                min(capacidad * eficiencia, max(0, demanda * 1.05 - inventario * 0.2)),
            
            "oee_calculation": lambda disponibilidad, rendimiento, calidad:
                disponibilidad * rendimiento * calidad,
            
            "labor_productivity": lambda produccion, horas_trabajadas, empleados:
                produccion / (horas_trabajadas * empleados) if horas_trabajadas > 0 else 0,
            
            "production_cost": lambda costo_fijo, costo_variable, volumen, eficiencia:
                (costo_fijo + costo_variable * volumen) / (volumen * eficiencia) if volumen > 0 else costo_fijo,
            
            "defect_rate": lambda temperatura_desviacion, tiempo_proceso, experiencia_operador:
                0.01 * (1 + temperatura_desviacion * 0.1) * (2 - experiencia_operador),
            
            "capacity_adjustment": lambda demanda_actual, capacidad_nominal, factor_tiempo:
                capacidad_nominal * (0.8 + 0.4 * min(1, demanda_actual / capacidad_nominal)) * factor_tiempo
        },
        "optimization_strategies": {
            "batch_sizing": lambda setup_time, demanda_diaria, holding_cost:
                np.sqrt(2 * demanda_diaria * setup_time / holding_cost),
            
            "line_balancing": lambda tareas, tiempo_ciclo, estaciones:
                sum(tareas) / (tiempo_ciclo * estaciones),
            
            "preventive_maintenance": lambda horas_operacion, mtbf:
                horas_operacion % (mtbf * 0.8) < 8  # Mantener al 80% del MTBF
        }
    },
    
    {
        "name": "Control de Calidad",
        "description": """Sistema de calidad dinámico con análisis predictivo.
        Muestreo adaptativo según histórico de defectos.
        Trazabilidad completa con blockchain interno.
        Predicción de problemas mediante machine learning.""",
        "params": {
            "laboratorio_propio": True,
            "frecuencia_muestreo": "cada lote",
            "parametros_analizados": 15,
            "tiempo_resultado_analisis": 2,
            "costo_analisis_unitario": 50,
            "equipos_calibrados": True,
            "personal_certificado": 3,
            "trazabilidad_completa": True,
            "sistema_gestion_calidad": "ISO 9001:2015"
        },
        "kpis": {
            "conformidad_producto": 0.98,
            "tiempo_liberacion_lote": 0,
            "costo_no_calidad": 0,
            "satisfaccion_auditoria": 0.95
        },
        "dynamic_behavior": {
            "sampling_frequency": lambda defect_history, production_volume, risk_level:
                min(1.0, 0.05 * (1 + defect_history * 10) * risk_level),
            
            "conformity_rate": lambda passed_tests, total_tests:
                passed_tests / total_tests if total_tests > 0 else 0,
            
            "quality_cost": lambda prevention_cost, appraisal_cost, failure_cost:
                prevention_cost + appraisal_cost + failure_cost,
            
            "release_time": lambda analysis_time, queue_time, documentation_time:
                analysis_time + queue_time + documentation_time,
            
            "risk_assessment": lambda severity, occurrence, detectability:
                severity * occurrence * detectability,
            
            "predictive_quality": lambda temperatura, humedad, tiempo_proceso, historico:
                0.98 * (1 - abs(temperatura - 4) * 0.02) * (1 - abs(humedad - 85) * 0.001) * historico
        },
        "quality_metrics": {
            "cp_capability": lambda spec_width, process_std:
                spec_width / (6 * process_std) if process_std > 0 else 0,
            
            "cpk_capability": lambda spec_limit, process_mean, process_std:
                min(abs(spec_limit[1] - process_mean), abs(process_mean - spec_limit[0])) / (3 * process_std),
            
            "dpmo": lambda defects, opportunities:
                (defects / opportunities) * 1000000 if opportunities > 0 else 0
        }
    },
    
    {
        "name": "Distribución",
        "description": """Red logística inteligente con optimización de rutas en tiempo real.
        Sistema de tracking GPS con alertas de temperatura.
        Planificación dinámica según demanda y tráfico.
        Gestión de flota con mantenimiento predictivo.""",
        "params": {
            "vehiculos_propios": 5,
            "capacidad_vehiculo_litros": 2000,
            "costo_km_recorrido": 3.5,
            "radio_distribucion_km": 50,
            "entregas_diarias_promedio": 30,
            "tiempo_entrega_promedio": 45,
            "sistema_ruteo": "optimizado",
            "tracking_gps": True,
            "temperatura_transporte": 4,
            "seguro_mercancia": True
        },
        "kpis": {
            "entregas_tiempo": 0.96,
            "costo_distribucion_unitario": 0,
            "utilizacion_flota": 0.85,
            "satisfaccion_entrega": 0.94
        },
        "dynamic_behavior": {
            "route_optimization": lambda puntos_entrega, distancia_matriz, capacidad_vehiculo:
                {
                    'rutas': puntos_entrega // capacidad_vehiculo + 1,
                    'distancia_total': sum(distancia_matriz) * 0.8,  # Factor optimización
                    'tiempo_total': sum(distancia_matriz) / 40 * 60  # minutos a 40 km/h promedio
                },
            
            "delivery_cost": lambda distancia, volumen, precio_combustible, eficiencia_vehiculo:
                (distancia * precio_combustible / eficiencia_vehiculo) + (volumen * 0.1),
            
            "fleet_utilization": lambda entregas_realizadas, capacidad_total_flota:
                entregas_realizadas / capacidad_total_flota if capacidad_total_flota > 0 else 0,
            
            "on_time_delivery": lambda entregas_puntuales, entregas_totales:
                entregas_puntuales / entregas_totales if entregas_totales > 0 else 0,
            
            "temperature_monitoring": lambda temp_actual, temp_objetivo, duracion_viaje:
                1 - min(1, abs(temp_actual - temp_objetivo) * duracion_viaje * 0.01),
            
            "dynamic_scheduling": lambda demanda_hora, vehiculos_disponibles, trafico_factor:
                min(vehiculos_disponibles, int(demanda_hora / (50 * trafico_factor)) + 1)
        },
        "optimization_algorithms": {
            "vrp_solver": lambda clientes, deposito, capacidad:
                "Algoritmo de ruteo de vehículos con ventanas de tiempo",
            
            "load_balancing": lambda pedidos, vehiculos:
                "Distribución equitativa de carga entre vehículos",
            
            "fuel_optimization": lambda rutas, consumo_base:
                consumo_base * 0.85  # 15% ahorro por optimización
        }
    },
    
    {
        "name": "Ventas",
        "description": """Gestión comercial adaptativa con pricing dinámico.
        CRM integrado con análisis predictivo de clientes.
        Sistema de recomendaciones personalizadas.
        Pronóstico de ventas con machine learning.""",
        "params": {
            "vendedores_campo": 5,
            "vendedores_mostrador": 3,
            "canales_venta": ["directa", "distribuidores", "retail"],
            "clientes_activos": 150,
            "ticket_promedio": 350,
            "frecuencia_visita_cliente": "semanal",
            "sistema_crm": True,
            "comision_ventas": 0.03,
            "meta_mensual": 500000,
            "descuentos_autorizados": 0.10
        },
        "kpis": {
            "cumplimiento_meta": 0,
            "crecimiento_ventas": 0,
            "retencion_clientes": 0.90,
            "nuevos_clientes_mes": 0
        },
        "dynamic_behavior": {
            "dynamic_pricing": lambda precio_base, demanda, inventario, competencia, elasticidad:
                precio_base * (1 + elasticidad * (demanda - inventario) / demanda) * (competencia / precio_base) ** 0.3,
            
            "sales_forecast": lambda historico, tendencia, estacionalidad, eventos:
                sum(historico[-30:]) / 30 * tendencia * estacionalidad * eventos,
            
            "customer_lifetime_value": lambda ticket_promedio, frecuencia_compra, años_retencion:
                ticket_promedio * frecuencia_compra * 12 * años_retencion,
            
            "conversion_rate": lambda visitas, ventas:
                ventas / visitas if visitas > 0 else 0,
            
            "cross_selling_index": lambda productos_por_venta, productos_totales:
                productos_por_venta / productos_totales,
            
            "churn_prediction": lambda dias_sin_compra, frecuencia_normal, valor_cliente:
                min(1, (dias_sin_compra / frecuencia_normal - 1) * 0.2) if frecuencia_normal > 0 else 0
        },
        "sales_strategies": {
            "segmentation": lambda rfm_score:
                "VIP" if rfm_score > 8 else "Regular" if rfm_score > 5 else "En riesgo",
            
            "recommendation_engine": lambda historial_compras, productos_disponibles:
                "Productos complementarios basados en patrones de compra",
            
            "promotional_impact": lambda descuento, elasticidad_precio:
                1 + (descuento * abs(elasticidad_precio))
        }
    },
    
    {
        "name": "Marketing",
        "description": """Marketing digital y tradicional con ROI medible.
        Campañas adaptativas basadas en respuesta del mercado.
        Análisis de sentimiento y gestión de reputación online.
        Attribution modeling para optimización de presupuesto.""",
        "params": {
            "presupuesto_mensual": 15000,
            "canales_comunicacion": ["redes sociales", "radio", "punto de venta"],
            "campanas_activas": 2,
            "inversion_digital": 0.40,
            "inversion_tradicional": 0.60,
            "frecuencia_promociones": "quincenal",
            "programa_fidelidad": True,
            "estudios_mercado": "trimestral",
            "agencia_publicidad": False
        },
        "kpis": {
            "roi_marketing": 0,
            "alcance_campanas": 0,
            "engagement_rate": 0.05,
            "top_of_mind": 0.25
        },
        "dynamic_behavior": {
            "campaign_effectiveness": lambda inversion, alcance, conversion, precio_promedio:
                (alcance * conversion * precio_promedio - inversion) / inversion if inversion > 0 else 0,
            
            "optimal_budget_allocation": lambda canales, performance_historico, presupuesto:
                {canal: presupuesto * performance / sum(performance_historico.values()) 
                 for canal, performance in zip(canales, performance_historico.values())},
            
            "customer_acquisition_cost": lambda gasto_marketing, nuevos_clientes:
                gasto_marketing / nuevos_clientes if nuevos_clientes > 0 else gasto_marketing,
            
            "brand_health_score": lambda awareness, consideracion, preferencia, recomendacion:
                (awareness * 0.2 + consideracion * 0.3 + preferencia * 0.3 + recomendacion * 0.2),
            
            "content_virality": lambda vistas, compartidos, tiempo_promedio:
                (compartidos / vistas) * tiempo_promedio if vistas > 0 else 0,
            
            "attribution_model": lambda touchpoints, conversion_value:
                {touchpoint: value / len(touchpoints) for touchpoint, value in touchpoints.items()}
        },
        "marketing_automation": {
            "email_segmentation": lambda comportamiento, demograficos:
                "Segmentación basada en comportamiento y datos demográficos",
            
            "social_listening": lambda menciones, sentimiento:
                sentimiento / menciones if menciones > 0 else 0,
            
            "personalization_engine": lambda historial, preferencias:
                "Contenido personalizado basado en interacciones previas"
        }
    },
    
    {
        "name": "Competencia",
        "description": """Inteligencia competitiva con análisis predictivo.
        Monitoreo automático de precios y promociones.
        Análisis de gaps y oportunidades de mercado.
        Benchmarking continuo de mejores prácticas.""",
        "params": {
            "competidores_directos": 8,
            "participacion_mercado_actual": 0.15,
            "posicion_mercado": 3,
            "precio_relativo": 1.05,
            "diferenciacion_producto": "calidad",
            "monitoreo_precios": "semanal",
            "analisis_competencia": "mensual",
            "fuentes_informacion": ["mercado", "clientes", "proveedores"],
            "ventaja_competitiva": "frescura y calidad"
        },
        "kpis": {
            "indice_competitividad": 0,
            "share_of_voice": 0.12,
            "precio_vs_competencia": 0,
            "percepcion_marca": 0.85
        },
        "dynamic_behavior": {
            "competitive_response": lambda accion_competidor, impacto_estimado, recursos_disponibles:
                {
                    'respuesta': 'agresiva' if impacto_estimado > 0.1 else 'moderada',
                    'inversion': recursos_disponibles * min(1, impacto_estimado * 2),
                    'tiempo_respuesta': 7 if impacto_estimado > 0.1 else 14
                },
            
            "market_share_dynamics": lambda share_actual, crecimiento_mercado, crecimiento_propio:
                share_actual * (1 + crecimiento_propio) / (1 + crecimiento_mercado),
            
            "price_elasticity_cross": lambda precio_propio, precio_competidor, elasticidad:
                elasticidad * (precio_competidor - precio_propio) / precio_propio,
            
            "competitive_advantage_score": lambda diferenciadores, importancia_cliente:
                sum(dif * imp for dif, imp in zip(diferenciadores, importancia_cliente)),
            
            "market_positioning": lambda atributos_propios, atributos_ideales:
                1 - np.mean([abs(p - i) for p, i in zip(atributos_propios, atributos_ideales)])
        },
        "strategic_analysis": {
            "swot_dynamic": lambda fortalezas, debilidades, oportunidades, amenazas:
                (fortalezas + oportunidades) / (debilidades + amenazas + 1),
            
            "blue_ocean_index": lambda competidores, diferenciacion:
                diferenciacion / (competidores + 1),
            
            "porter_five_forces": lambda proveedores, compradores, sustitutos, entrantes, rivalidad:
                5 - sum([proveedores, compradores, sustitutos, entrantes, rivalidad]) / 5
        }
    },
    
    {
        "name": "Contabilidad",
        "description": """Gestión financiera inteligente con analytics avanzado.
        Costeo ABC dinámico y análisis de rentabilidad por producto/cliente.
        Forecasting financiero con escenarios múltiples.
        Optimización fiscal y gestión de flujo de caja.""",
        "params": {
            "sistema_contable": "SAP Business One",
            "facturacion_electronica": True,
            "periodo_cobranza_dias": 30,
            "periodo_pago_dias": 45,
            "control_presupuestario": "mensual",
            "auditoria_externa": "anual",
            "reportes_gerenciales": "semanal",
            "centros_costo": 12,
            "moneda_operacion": "BOB",
            "tipo_cambio_referencia": 6.96
        },
        "kpis": {
            "liquidez_corriente": 1.5,
            "rotacion_cuentas_cobrar": 0,
            "margen_ebitda": 0,
            "roe_return_on_equity": 0
        },
        "dynamic_behavior": {
            "cash_flow_projection": lambda ingresos, egresos, cobranzas, pagos, dias:
                sum([ingresos[i] * cobranzas[i] - egresos[i] * pagos[i] for i in range(dias)]),
            
            "working_capital_optimization": lambda activo_corriente, pasivo_corriente, ventas_diarias:
                (activo_corriente - pasivo_corriente) / ventas_diarias,
            
            "cost_allocation_abc": lambda actividades, cost_drivers, productos:
                {prod: sum(act * driver[prod] for act, driver in zip(actividades, cost_drivers)) 
                 for prod in productos},
            
            "financial_health_score": lambda liquidez, endeudamiento, rentabilidad, eficiencia:
                (liquidez * 0.25 + (1 - endeudamiento) * 0.25 + rentabilidad * 0.25 + eficiencia * 0.25),
            
            "tax_optimization": lambda ingresos, gastos_deducibles, tasa_impuesto:
                (ingresos - gastos_deducibles) * tasa_impuesto,
            
            "dupont_analysis": lambda margen_neto, rotacion_activos, multiplicador_capital:
                margen_neto * rotacion_activos * multiplicador_capital
        },
        "financial_controls": {
            "budget_variance": lambda real, presupuesto:
                (real - presupuesto) / presupuesto if presupuesto != 0 else 0,
            
            "fraud_detection": lambda transacciones, patrones_normales:
                "Análisis de anomalías en transacciones",
            
            "credit_scoring": lambda historial_pagos, capacidad_pago, garantias:
                historial_pagos * 0.5 + capacidad_pago * 0.3 + garantias * 0.2
        }
    },
    
    {
        "name": "Recursos Humanos",
        "description": """Gestión del talento con people analytics.
        Predicción de rotación y planes de retención personalizados.
        Optimización de productividad y bienestar laboral.
        Learning & Development con rutas de carrera dinámicas.""",
        "params": {
            "total_empleados": 45,
            "empleados_produccion": 25,
            "empleados_administrativos": 12,
            "empleados_comerciales": 8,
            "rotacion_anual": 0.15,
            "horas_capacitacion_anual": 40,
            "evaluaciones_desempeno": "semestral",
            "programa_incentivos": True,
            "seguro_salud": True,
            "salario_promedio": 3500
        },
        "kpis": {
            "clima_laboral": 0.82,
            "productividad_empleado": 0,
            "ausentismo": 0.03,
            "accidentes_laborales": 0
        },
        "dynamic_behavior": {
            "turnover_prediction": lambda satisfaccion, salario_mercado, desarrollo, antiguedad:
                (1 - satisfaccion) * 0.4 + max(0, salario_mercado - 1) * 0.3 + 
                (1 - desarrollo) * 0.2 + (1 / (antiguedad + 1)) * 0.1,
            
            "productivity_optimization": lambda skills, motivacion, herramientas, procesos:
                skills * motivacion * herramientas * procesos,
            
            "compensation_benchmarking": lambda puesto, experiencia, mercado, performance:
                mercado * (0.8 + experiencia * 0.02 + performance * 0.2),
            
            "engagement_score": lambda satisfaccion, compromiso, desarrollo, reconocimiento:
                (satisfaccion + compromiso + desarrollo + reconocimiento) / 4,
            
            "training_roi": lambda mejora_productividad, costo_capacitacion, duracion_impacto:
                (mejora_productividad * duracion_impacto - costo_capacitacion) / costo_capacitacion,
            
            "workforce_planning": lambda demanda_futura, capacidad_actual, rotacion_esperada:
                max(0, demanda_futura - capacidad_actual * (1 - rotacion_esperada))
        },
        "hr_analytics": {
            "performance_distribution": lambda evaluaciones:
                np.histogram(evaluaciones, bins=[0, 0.6, 0.7, 0.8, 0.9, 1.0]),
            
            "succession_planning": lambda competencias_requeridas, competencias_actuales:
                sum(1 for req, act in zip(competencias_requeridas, competencias_actuales) if act >= req * 0.8),
            
            "diversity_index": lambda categorias_diversidad:
                1 - sum((cat / sum(categorias_diversidad)) ** 2 for cat in categorias_diversidad)
        }
    },
    
    {
        "name": "Mantenimiento",
        "description": """Mantenimiento predictivo con IoT y analytics.
        Optimización de inventario de repuestos con ML.
        Gestión de vida útil de activos y renovación.
        RCM (Reliability Centered Maintenance) dinámico.""",
        "params": {
            "equipos_criticos": 15,
            "plan_mantenimiento_preventivo": True,
            "frecuencia_preventivo": "mensual",
            "stock_repuestos_criticos": True,
            "tecnicos_mantenimiento": 3,
            "sistema_gmao": True,
            "presupuesto_mensual": 8000,
            "contratos_servicio": 5,
            "tiempo_respuesta_horas": 2,
            "mantenimiento_predictivo": "vibraciones y termografía"
        },
        "kpis": {
            "disponibilidad_equipos": 0.96,
            "mtbf_mean_time_between_failures": 720,
            "mttr_mean_time_to_repair": 2,
            "costo_mantenimiento_ventas": 0.02
        },
        "dynamic_behavior": {
            "failure_prediction": lambda horas_operacion, condicion_actual, historico_fallas:
                1 - np.exp(-(horas_operacion / historico_fallas) ** 2) * condicion_actual,
            
            "maintenance_scheduling": lambda criticidad, probabilidad_falla, costo_falla, costo_preventivo:
                probabilidad_falla * costo_falla > costo_preventivo,
            
            "spare_parts_optimization": lambda consumo_historico, lead_time, criticidad, costo:
                consumo_historico * lead_time * criticidad * (1 + 0.5 / np.sqrt(costo)),
            
            "reliability_growth": lambda mejoras_implementadas, fallas_iniciales:
                fallas_iniciales * np.exp(-0.1 * mejoras_implementadas),
            
            "total_productive_maintenance": lambda disponibilidad, rendimiento, calidad:
                disponibilidad * rendimiento * calidad,
            
            "lifecycle_cost": lambda costo_adquisicion, costo_operacion_anual, costo_mantenimiento_anual, años:
                costo_adquisicion + sum([(costo_operacion_anual + costo_mantenimiento_anual) * 
                                       (1.05 ** i) / (1.1 ** i) for i in range(años)])
        },
        "predictive_techniques": {
            "vibration_analysis": lambda frecuencia, amplitud, referencia:
                abs(frecuencia - referencia) / referencia + amplitud / 10,
            
            "thermography": lambda temperatura_actual, temperatura_normal:
                abs(temperatura_actual - temperatura_normal) / temperatura_normal,
            
            "oil_analysis": lambda viscosidad, contaminantes, desgaste:
                (abs(viscosidad - 1) + contaminantes + desgaste) / 3
        }
    },
    
    {
        "name": "Inventario Productos Finales",
        "description": """Gestión inteligente de productos terminados con AI.
        Optimización multi-objetivo: frescura, costos y servicio.
        Predicción de demanda por SKU con estacionalidad.
        Sistema de asignación dinámica y cross-docking.""",
        "params": {
            "capacidad_camaras_frio": 5000,
            "temperatura_conservacion": 4,
            "zonas_almacenamiento": 3,
            "sistema_rotacion": "FEFO",
            "picking_system": "por zonas",
            "nivel_inventario_actual": 0,
            "punto_reorden": 0,
            "stock_seguridad": 0,
            "costo_almacenamiento_diario": 100,
            "sistema_inventario": "FIFO",
            "frecuencia_inventario_fisico": "semanal"
        },
        "kpis": {
            "exactitud_inventario": 0.99,
            "costo_mantenimiento_inventario": 0,
            "rotacion_inventario": 0,
            "merma_porcentaje": 0.02
        },
        "dynamic_behavior": {
            "optimal_stock_level": lambda demanda_media, demanda_std, lead_time, service_level:
                demanda_media * lead_time + norm.ppf(service_level) * demanda_std * np.sqrt(lead_time),
            
            "freshness_index": lambda edad_promedio, vida_util:
                max(0, 1 - (edad_promedio / vida_util) ** 2),
            
            "allocation_priority": lambda demanda_cliente, valor_cliente, urgencia, inventario_disponible:
                (demanda_cliente * valor_cliente * urgencia) / inventario_disponible,
            
            "storage_optimization": lambda productos, espacios, restricciones:
                "Optimización 3D de espacios con restricciones de temperatura y acceso",
            
            "waste_prediction": lambda edad_inventario, temperatura_promedio, rotacion:
                (edad_inventario / 5) * (1 + max(0, temperatura_promedio - 4) * 0.1) * (1 / rotacion),
            
            "dynamic_pricing_perishables": lambda precio_base, dias_restantes, vida_util:
                precio_base * (0.5 + 0.5 * (dias_restantes / vida_util)) if dias_restantes < vida_util * 0.3 else precio_base
        },
        "inventory_strategies": {
            "abc_analysis": lambda valores, volumenes:
                "Clasificación ABC dinámica por valor y rotación",
            
            "eoq_perishable": lambda demanda, costo_pedido, costo_mantener, vida_util:
                min(np.sqrt(2 * demanda * costo_pedido / costo_mantener), demanda * vida_util * 0.5),
            
            "cross_docking_feasibility": lambda tiempo_transito, vida_util, demanda_inmediata:
                tiempo_transito < vida_util * 0.1 and demanda_inmediata > 0.8
        }
    }
]

# Relaciones dinámicas entre áreas basadas en flujo de demanda
area_relationships = {
    "Ventas": {
        "afecta": ["Producción", "Inventario Productos Finales", "Distribución"],
        "factor_impacto": lambda ventas_delta: {
            "Producción": ventas_delta * 1.05,  # Producir 5% más que ventas
            "Inventario Productos Finales": ventas_delta * 0.2,  # Mantener 20% como buffer
            "Distribución": ventas_delta * 1.0  # Distribuir lo vendido
        }
    },
    "Producción": {
        "afecta": ["Abastecimiento", "Inventario Insumos", "Control de Calidad", "Mantenimiento"],
        "factor_impacto": lambda produccion_delta: {
            "Abastecimiento": produccion_delta * 1.1,  # Pedir 10% más de insumos
            "Inventario Insumos": produccion_delta * 0.15,  # Buffer de seguridad
            "Control de Calidad": produccion_delta * 0.05,  # Muestreo proporcional
            "Mantenimiento": produccion_delta * 0.001  # Desgaste por uso
        }
    },
    "Marketing": {
        "afecta": ["Ventas", "Competencia"],
        "factor_impacto": lambda inversion_marketing: {
            "Ventas": np.log(1 + inversion_marketing / 10000) * 0.1,  # ROI decreciente
            "Competencia": inversion_marketing / 50000  # Impacto en share of voice
        }
    },
    "Competencia": {
        "afecta": ["Ventas", "Marketing", "Contabilidad"],
        "factor_impacto": lambda intensidad_competitiva: {
            "Ventas": -intensidad_competitiva * 0.1,  # Reducción de ventas
            "Marketing": intensidad_competitiva * 1.5,  # Mayor inversión requerida
            "Contabilidad": -intensidad_competitiva * 0.05  # Presión en márgenes
        }
    },
    "Abastecimiento": {
        "afecta": ["Inventario Insumos", "Contabilidad", "Producción"],
        "factor_impacto": lambda eficiencia_compras: {
            "Inventario Insumos": eficiencia_compras * 1.0,
            "Contabilidad": -eficiencia_compras * 0.02,  # Ahorro por mejores precios
            "Producción": eficiencia_compras * 0.98  # Calidad de insumos afecta producción
        }
    },
    "Control de Calidad": {
        "afecta": ["Inventario Productos Finales", "Ventas", "Competencia"],
        "factor_impacto": lambda nivel_calidad: {
            "Inventario Productos Finales": nivel_calidad * 0.98,  # Menos mermas
            "Ventas": (nivel_calidad - 0.95) * 2,  # Impacto en reputación
            "Competencia": nivel_calidad * 0.1  # Diferenciación por calidad
        }
    },
    "Recursos Humanos": {
        "afecta": ["Todas las áreas"],
        "factor_impacto": lambda productividad_empleados: {
            area: productividad_empleados * 0.05 for area in 
            ["Producción", "Ventas", "Distribución", "Control de Calidad", "Mantenimiento"]
        }
    },
    "Contabilidad": {
        "afecta": ["Todas las áreas"],
        "factor_impacto": lambda salud_financiera: {
            area: salud_financiera * 0.02 for area in areas_data
        }
    }
}

# Métricas de desempeño dinámicas por área
area_performance_benchmarks = {
    "Abastecimiento": {
        "excelente": lambda kpis: kpis["nivel_servicio_proveedores"] >= 0.98 and kpis["costo_total_abastecimiento"] < 100000,
        "bueno": lambda kpis: kpis["nivel_servicio_proveedores"] >= 0.95 and kpis["costo_total_abastecimiento"] < 120000,
        "regular": lambda kpis: kpis["nivel_servicio_proveedores"] >= 0.90 and kpis["costo_total_abastecimiento"] < 150000,
        "malo": lambda kpis: kpis["nivel_servicio_proveedores"] < 0.90 or kpis["costo_total_abastecimiento"] > 150000
    },
    "Producción": {
        "excelente": lambda kpis: kpis["oee_overall_equipment_effectiveness"] >= 0.85 and kpis["tasa_defectos"] < 0.01,
        "bueno": lambda kpis: kpis["oee_overall_equipment_effectiveness"] >= 0.75 and kpis["tasa_defectos"] < 0.02,
        "regular": lambda kpis: kpis["oee_overall_equipment_effectiveness"] >= 0.65 and kpis["tasa_defectos"] < 0.03,
        "malo": lambda kpis: kpis["oee_overall_equipment_effectiveness"] < 0.65 or kpis["tasa_defectos"] > 0.03
    },
    "Ventas": {
        "excelente": lambda kpis: kpis["cumplimiento_meta"] >= 1.10 and kpis["crecimiento_ventas"] > 0.15,
        "bueno": lambda kpis: kpis["cumplimiento_meta"] >= 1.00 and kpis["crecimiento_ventas"] > 0.10,
        "regular": lambda kpis: kpis["cumplimiento_meta"] >= 0.90 and kpis["crecimiento_ventas"] > 0.05,
        "malo": lambda kpis: kpis["cumplimiento_meta"] < 0.90 or kpis["crecimiento_ventas"] < 0.05
    },
    "Control de Calidad": {
        "excelente": lambda kpis: kpis["conformidad_producto"] >= 0.99 and kpis["costo_no_calidad"] < 5000,
        "bueno": lambda kpis: kpis["conformidad_producto"] >= 0.98 and kpis["costo_no_calidad"] < 10000,
        "regular": lambda kpis: kpis["conformidad_producto"] >= 0.95 and kpis["costo_no_calidad"] < 20000,
        "malo": lambda kpis: kpis["conformidad_producto"] < 0.95 or kpis["costo_no_calidad"] > 20000
    },
    "Distribución": {
        "excelente": lambda kpis: kpis["entregas_tiempo"] >= 0.98 and kpis["utilizacion_flota"] >= 0.90,
        "bueno": lambda kpis: kpis["entregas_tiempo"] >= 0.95 and kpis["utilizacion_flota"] >= 0.80,
        "regular": lambda kpis: kpis["entregas_tiempo"] >= 0.90 and kpis["utilizacion_flota"] >= 0.70,
        "malo": lambda kpis: kpis["entregas_tiempo"] < 0.90 or kpis["utilizacion_flota"] < 0.70
    }
}

# Función para simular comportamiento de área durante un período
def simular_area(nombre_area, dias=30, contexto_inicial=None):
    """
    Simula el comportamiento dinámico de un área durante N días
    
    Args:
        nombre_area: Nombre del área a simular
        dias: Número de días a simular
        contexto_inicial: Condiciones iniciales del área
    
    Returns:
        Lista con métricas diarias del área
    """
    area = next((a for a in areas_data if a["name"] == nombre_area), None)
    if not area:
        return None
    
    resultados = []
    contexto = contexto_inicial or {
        'demanda_base': 2500,
        'inventario_inicial': 1000,
        'empleados': 15,
        'presupuesto': 100000
    }
    
    for dia in range(dias):
        resultado_dia = {
            'dia': dia + 1,
            'fecha': datetime.now() + timedelta(days=dia),
            'area': nombre_area
        }
        
        # Calcular KPIs dinámicos del área
        if 'dynamic_behavior' in area:
            comportamiento = area['dynamic_behavior']
            
            # Simular cada métrica según el área
            if nombre_area == "Producción" and 'production_planning' in comportamiento:
                demanda = contexto['demanda_base'] * (1 + 0.1 * np.sin(dia / 7))  # Variación semanal
                inventario = contexto.get('inventario', 1000)
                capacidad = area['params']['capacidad_produccion_diaria']
                eficiencia = area['params']['eficiencia_global']
                
                resultado_dia['produccion_planificada'] = comportamiento['production_planning'](
                    demanda, inventario, capacidad, eficiencia
                )
                
                # Calcular OEE
                disponibilidad = 0.95 - 0.002 * dia  # Degradación gradual
                rendimiento = 0.90 + 0.001 * min(dia, 30)  # Mejora por aprendizaje
                calidad = 0.98 + np.random.normal(0, 0.01)
                
                resultado_dia['oee'] = comportamiento['oee_calculation'](
                    disponibilidad, rendimiento, calidad
                )
            
            elif nombre_area == "Ventas" and 'dynamic_pricing' in comportamiento:
                precio_base = 15.50
                demanda = contexto['demanda_base'] * (1 + 0.05 * np.random.normal())
                inventario = contexto.get('inventario', 1000)
                competencia = precio_base * 1.02
                elasticidad = -0.5
                
                resultado_dia['precio_dinamico'] = comportamiento['dynamic_pricing'](
                    precio_base, demanda, inventario, competencia, elasticidad
                )
                
                # Calcular forecast
                historico = [demanda * (1 + 0.1 * np.random.normal()) for _ in range(30)]
                tendencia = 1.002 ** dia  # Crecimiento exponencial pequeño
                estacionalidad = 1.1 if dia % 7 in [5, 6] else 0.95
                eventos = 1.2 if dia % 30 == 0 else 1.0
                
                resultado_dia['forecast_ventas'] = comportamiento['sales_forecast'](
                    historico, tendencia, estacionalidad, eventos
                )
            
            elif nombre_area == "Inventario Productos Finales" and 'optimal_stock_level' in comportamiento:
                demanda_media = contexto['demanda_base']
                demanda_std = demanda_media * 0.15
                lead_time = 2
                service_level = 0.95
                
                resultado_dia['stock_optimo'] = comportamiento['optimal_stock_level'](
                    demanda_media, demanda_std, lead_time, service_level
                )
                
                # Calcular índice de frescura
                edad_promedio = min(5, dia % 7)  # Resetea semanalmente
                vida_util = 5  # días para productos lácteos
                
                resultado_dia['indice_frescura'] = comportamiento['freshness_index'](
                    edad_promedio, vida_util
                )
            
            elif nombre_area == "Control de Calidad" and 'conformity_rate' in comportamiento:
                # Simular tests de calidad
                total_tests = 100
                defectos_base = 2
                factor_dia = 1 + 0.001 * dia  # Mejora gradual
                defectos = max(0, int(defectos_base / factor_dia + np.random.poisson(0.5)))
                passed_tests = total_tests - defectos
                
                resultado_dia['conformidad'] = comportamiento['conformity_rate'](
                    passed_tests, total_tests
                )
                
                # Calcular costo de calidad
                prevention = 1000 + 10 * dia  # Inversión creciente en prevención
                appraisal = 500
                failure = defectos * 100  # Costo por defecto
                
                resultado_dia['costo_calidad'] = comportamiento['quality_cost'](
                    prevention, appraisal, failure
                )
        
        # Actualizar contexto para siguiente día
        if 'produccion_planificada' in resultado_dia:
            contexto['inventario'] = contexto.get('inventario', 1000) + resultado_dia['produccion_planificada'] - contexto['demanda_base']
        
        resultados.append(resultado_dia)
    
    return resultados

# Función para calcular impacto entre áreas
def calcular_impacto_entre_areas(area_origen, cambio, areas_afectadas):
    """
    Calcula el impacto de un cambio en un área sobre otras áreas
    
    Args:
        area_origen: Área que origina el cambio
        cambio: Magnitud del cambio (porcentaje)
        areas_afectadas: Lista de áreas a evaluar
    
    Returns:
        Dict con impactos calculados por área
    """
    impactos = {}
    
    if area_origen in area_relationships:
        relacion = area_relationships[area_origen]
        if 'factor_impacto' in relacion:
            impactos_calculados = relacion['factor_impacto'](cambio)
            
            for area in areas_afectadas:
                if area in impactos_calculados:
                    impactos[area] = impactos_calculados[area]
                elif area in relacion.get('afecta', []):
                    impactos[area] = cambio * 0.5  # Impacto default 50%
    
    return impactos

# Función para optimizar configuración de área
def optimizar_area(nombre_area, objetivo, restricciones):
    """
    Optimiza la configuración de un área según objetivo y restricciones
    
    Args:
        nombre_area: Área a optimizar
        objetivo: Métrica a maximizar/minimizar
        restricciones: Dict con restricciones
    
    Returns:
        Configuración optimizada
    """
    area = next((a for a in areas_data if a["name"] == nombre_area), None)
    if not area:
        return None
    
    configuracion_optima = area['params'].copy()
    
    # Aplicar estrategias de optimización según área
    if nombre_area == "Producción" and objetivo == "maximizar_oee":
        # Optimizar turnos y mantenimiento
        configuracion_optima['turnos_trabajo'] = 3 if restricciones.get('presupuesto', 0) > 200000 else 2
        configuracion_optima['mantenimiento_preventivo'] = True
        configuracion_optima['eficiencia_global'] = min(0.95, area['params']['eficiencia_global'] * 1.1)
    
    elif nombre_area == "Inventario Productos Finales" and objetivo == "minimizar_mermas":
        # Optimizar rotación y temperatura
        configuracion_optima['sistema_rotacion'] = "FEFO"
        configuracion_optima['temperatura_conservacion'] = 3.5  # Temperatura óptima
        configuracion_optima['frecuencia_inventario_fisico'] = "diario"
    
    elif nombre_area == "Ventas" and objetivo == "maximizar_ventas":
        # Optimizar fuerza de ventas y descuentos
        presupuesto = restricciones.get('presupuesto', 100000)
        configuracion_optima['vendedores_campo'] = min(10, int(presupuesto / 10000))
        configuracion_optima['descuentos_autorizados'] = min(0.15, restricciones.get('margen_minimo', 0.2) / 2)
        configuracion_optima['comision_ventas'] = 0.05 if presupuesto > 150000 else 0.03
    
    return configuracion_optima

# Exportar elementos principales
__all__ = ['areas_data', 'area_relationships', 'area_performance_benchmarks',
           'simular_area', 'calcular_impacto_entre_areas', 'optimizar_area',
           'calcular_kpi_dinamico', 'calcular_costo_operativo_area']