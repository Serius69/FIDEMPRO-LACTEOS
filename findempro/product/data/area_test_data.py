"""
Configuración de áreas operativas para empresas lácteas.
Define las áreas funcionales con sus parámetros y métricas clave.
"""

areas_data = [
    {
        "name": "Abastecimiento",
        "description": """Gestión integral de la cadena de suministro de materias primas e insumos.
        Incluye relaciones con proveedores, negociación de precios, control de calidad en recepción,
        y planificación de compras basada en pronósticos de demanda.""",
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
        }
    },
    {
        "name": "Inventario Insumos",
        "description": """Control y optimización de inventarios de materias primas e insumos.
        Sistema de gestión FIFO, control de caducidades, optimización de espacios de almacenamiento,
        y mantenimiento de condiciones óptimas de conservación.""",
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
        }
    },
    {
        "name": "Distribución",
        "description": """Red logística para entrega de productos a clientes finales.
        Optimización de rutas, gestión de flota, cadena de frío ininterrumpida
        y seguimiento en tiempo real de entregas.""",
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
        }
    },
    {
        "name": "Ventas",
        "description": """Gestión comercial y atención al cliente.
        Incluye fuerza de ventas, gestión de pedidos, atención postventa
        y desarrollo de relaciones comerciales a largo plazo.""",
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
        }
    },
    {
        "name": "Competencia",
        "description": """Análisis y monitoreo del entorno competitivo.
        Benchmarking de precios, productos y estrategias. Identificación de
        oportunidades de mercado y amenazas competitivas.""",
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
        }
    },
    {
        "name": "Marketing",
        "description": """Estrategias de posicionamiento y promoción de marca.
        Gestión de imagen corporativa, publicidad, promociones y desarrollo
        de nuevos productos según tendencias del mercado.""",
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
        }
    },
    {
        "name": "Contabilidad",
        "description": """Gestión financiera y contable de la empresa.
        Control de costos, facturación, cobranzas, pagos y reportes financieros.
        Cumplimiento de obligaciones tributarias y análisis de rentabilidad.""",
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
        }
    },
    {
        "name": "Recursos Humanos",
        "description": """Gestión del talento humano y desarrollo organizacional.
        Reclutamiento, capacitación, evaluación de desempeño, clima laboral
        y cumplimiento de normativas laborales.""",
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
        }
    },
    {
        "name": "Mantenimiento",
        "description": """Gestión del mantenimiento de equipos e instalaciones.
        Mantenimiento preventivo, correctivo y predictivo. Gestión de repuestos
        y optimización de la disponibilidad de equipos productivos.""",
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
        }
    },
    {   
        "name": "Producción",
        "description": """Centro de transformación de materias primas en productos lácteos terminados.
        Incluye procesos de pasteurización, fermentación, elaboración y envasado.
        Control de calidad en proceso y optimización de recursos productivos.""",
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
        }
    },
    {
        "name": "Control de Calidad",
        "description": """Aseguramiento de la calidad en todas las etapas del proceso productivo.
        Análisis microbiológicos, fisicoquímicos y organolépticos. Cumplimiento de normativas
        sanitarias y estándares de calidad internos y externos.""",
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
        }
    },
    {
        "name": "Inventario Productos Finales",
        "description": """Gestión de productos terminados listos para distribución.
        Control de fechas de vencimiento, rotación FEFO, condiciones de almacenamiento
        y preparación de pedidos para despacho.""",
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
        }
    },
    # NUEVAS ÁREAS IDENTIFICADAS EN EQUATION_TEST_DATA
    {
        "name": "Análisis Demanda",
        "description": """Estudio y análisis de patrones de demanda histórica y proyecciones.
        Incluye análisis estadístico de tendencias, estacionalidad, variabilidad
        y proyecciones de demanda futura basadas en datos históricos.""",
        "params": {
            "datos_historicos_dias": 365,
            "ventana_analisis": 30,
            "metodo_proyeccion": "media_movil_ponderada",
            "factor_estacionalidad": 1.1,
            "confiabilidad_datos": 0.95,
            "frecuencia_actualizacion": "diaria",
            "variables_externas": ["clima", "eventos", "competencia"],
            "sistema_forecasting": "advanced_analytics",
            "precision_proyeccion": 0.85,
            "alertas_desviacion": True
        },
        "kpis": {
            "precision_forecast": 0.85,
            "error_absoluto_medio": 0.12,
            "coeficiente_variacion": 0.15,
            "tendencia_mensual": 0.05
        }
    },
    {
        "name": "Indicadores Generales",
        "description": """Dashboard de indicadores clave de desempeño integral.
        Consolidación de métricas de todas las áreas para evaluación
        del desempeño global de la empresa.""",
        "params": {
            "frecuencia_medicion": "diaria",
            "dashboard_tiempo_real": True,
            "alertas_automaticas": True,
            "benchmarks_industria": True,
            "reportes_ejecutivos": "semanal",
            "indicadores_criticos": 15,
            "umbrales_alerta": {"critico": 0.7, "atencion": 0.85},
            "historico_tendencias": 90,
            "segmentacion_analisis": ["producto", "cliente", "canal"],
            "integracion_sistemas": True
        },
        "kpis": {
            "indice_desempeno_global": 0,
            "cumplimiento_objetivos": 0,
            "eficiencia_operativa_global": 0,
            "satisfaccion_stakeholders": 0.85
        }
    }
]

# Interrelaciones entre áreas (actualizado con nuevas áreas)
area_relationships = {
    "Abastecimiento": ["Inventario Insumos", "Contabilidad"],
    "Inventario Insumos": ["Producción", "Contabilidad"],
    "Producción": ["Control de Calidad", "Inventario Productos Finales", "Mantenimiento"],
    "Control de Calidad": ["Inventario Productos Finales", "Ventas"],
    "Inventario Productos Finales": ["Distribución", "Ventas"],
    "Distribución": ["Ventas", "Marketing"],
    "Ventas": ["Marketing", "Contabilidad", "Competencia", "Análisis Demanda"],
    "Competencia": ["Marketing", "Ventas"],
    "Marketing": ["Ventas", "Contabilidad"],
    "Contabilidad": ["Todas las áreas"],
    "Recursos Humanos": ["Todas las áreas"],
    "Mantenimiento": ["Producción", "Distribución"],
    "Análisis Demanda": ["Ventas", "Producción", "Inventario Productos Finales", "Marketing"],
    "Indicadores Generales": ["Todas las áreas"]
}

# Métricas de desempeño por área (actualizado)
area_performance_benchmarks = {
    "Abastecimiento": {
        "excelente": {"nivel_servicio": 0.98, "costo_variacion": 0.02},
        "bueno": {"nivel_servicio": 0.95, "costo_variacion": 0.05},
        "regular": {"nivel_servicio": 0.90, "costo_variacion": 0.10},
        "malo": {"nivel_servicio": 0.85, "costo_variacion": 0.15}
    },
    "Producción": {
        "excelente": {"oee": 0.85, "defectos_ppm": 100},
        "bueno": {"oee": 0.75, "defectos_ppm": 500},
        "regular": {"oee": 0.65, "defectos_ppm": 1000},
        "malo": {"oee": 0.55, "defectos_ppm": 2000}
    },
    "Ventas": {
        "excelente": {"cumplimiento": 1.10, "crecimiento": 0.15},
        "bueno": {"cumplimiento": 1.00, "crecimiento": 0.10},
        "regular": {"cumplimiento": 0.90, "crecimiento": 0.05},
        "malo": {"cumplimiento": 0.80, "crecimiento": 0.00}
    },
    "Control de Calidad": {
        "excelente": {"conformidad": 0.99, "tiempo_liberacion": 1.5},
        "bueno": {"conformidad": 0.97, "tiempo_liberacion": 2.0},
        "regular": {"conformidad": 0.95, "tiempo_liberacion": 2.5},
        "malo": {"conformidad": 0.92, "tiempo_liberacion": 3.0}
    },
    "Inventario Productos Finales": {
        "excelente": {"rotacion": 12, "exactitud": 0.99},
        "bueno": {"rotacion": 10, "exactitud": 0.97},
        "regular": {"rotacion": 8, "exactitud": 0.95},
        "malo": {"rotacion": 6, "exactitud": 0.92}
    },
    "Inventario Insumos": {
        "excelente": {"fill_rate": 0.98, "costo_mantenimiento": 0.02},
        "bueno": {"fill_rate": 0.95, "costo_mantenimiento": 0.03},
        "regular": {"fill_rate": 0.92, "costo_mantenimiento": 0.04},
        "malo": {"fill_rate": 0.88, "costo_mantenimiento": 0.06}
    },
    "Distribución": {
        "excelente": {"entregas_tiempo": 0.98, "costo_unitario": 0.05},
        "bueno": {"entregas_tiempo": 0.95, "costo_unitario": 0.07},
        "regular": {"entregas_tiempo": 0.90, "costo_unitario": 0.10},
        "malo": {"entregas_tiempo": 0.85, "costo_unitario": 0.15}
    },
    "Marketing": {
        "excelente": {"roi": 4.0, "top_of_mind": 0.35},
        "bueno": {"roi": 3.0, "top_of_mind": 0.28},
        "regular": {"roi": 2.0, "top_of_mind": 0.20},
        "malo": {"roi": 1.0, "top_of_mind": 0.15}
    },
    "Competencia": {
        "excelente": {"indice_competitividad": 0.90, "participacion_mercado": 0.20},
        "bueno": {"indice_competitividad": 0.80, "participacion_mercado": 0.15},
        "regular": {"indice_competitividad": 0.70, "participacion_mercado": 0.12},
        "malo": {"indice_competitividad": 0.60, "participacion_mercado": 0.08}
    },
    "Contabilidad": {
        "excelente": {"margen_ebitda": 0.20, "liquidez": 2.0},
        "bueno": {"margen_ebitda": 0.15, "liquidez": 1.5},
        "regular": {"margen_ebitda": 0.10, "liquidez": 1.2},
        "malo": {"margen_ebitda": 0.05, "liquidez": 1.0}
    },
    "Recursos Humanos": {
        "excelente": {"clima_laboral": 0.90, "rotacion": 0.08},
        "bueno": {"clima_laboral": 0.85, "rotacion": 0.12},
        "regular": {"clima_laboral": 0.80, "rotacion": 0.16},
        "malo": {"clima_laboral": 0.75, "rotacion": 0.22}
    },
    "Mantenimiento": {
        "excelente": {"disponibilidad": 0.98, "mtbf": 800},
        "bueno": {"disponibilidad": 0.95, "mtbf": 650},
        "regular": {"disponibilidad": 0.92, "mtbf": 500},
        "malo": {"disponibilidad": 0.88, "mtbf": 350}
    },
    "Análisis Demanda": {
        "excelente": {"precision_forecast": 0.92, "error_medio": 0.08},
        "bueno": {"precision_forecast": 0.87, "error_medio": 0.12},
        "regular": {"precision_forecast": 0.80, "error_medio": 0.18},
        "malo": {"precision_forecast": 0.72, "error_medio": 0.25}
    },
    "Indicadores Generales": {
        "excelente": {"desempeno_global": 0.90, "cumplimiento_objetivos": 0.95},
        "bueno": {"desempeno_global": 0.80, "cumplimiento_objetivos": 0.85},
        "regular": {"desempeno_global": 0.70, "cumplimiento_objetivos": 0.75},
        "malo": {"desempeno_global": 0.60, "cumplimiento_objetivos": 0.65}
    }
}

# Mapeo de áreas con ecuaciones (para validación cruzada)
area_equation_mapping = {
    "Análisis Demanda": ["DPH", "DSD", "CVD"],
    "Ventas": ["DDP", "TCAE", "VPC", "TPV", "DI", "NSC", "DT", "ISC", "FC"],
    "Producción": ["POD", "CPROD", "QPL", "PPL", "TPPRO", "FU", "EP", "EOG"],
    "Inventario Productos Finales": ["IOP", "IPF", "DCI", "RTI", "CA", "MI"],
    "Inventario Insumos": ["IOI", "PI", "UII", "II"],
    "Contabilidad": ["IT", "IE", "CTAI", "CVU", "GO", "GG", "TG", "GT", "IB", "MB", "NR", "RVE", "CPP", "CPV", "CUP", "CHO", "PED", "RI"],
    "Distribución": ["CTTL"],
    "Control de Calidad": ["MP", "CTM"],
    "Marketing": ["EM", "CUAC"],
    "Recursos Humanos": ["PE", "HNP", "HO"],
    "Competencia": ["PM", "IC"],
    "Indicadores Generales": ["IDG", "PVR"]
}

# Función auxiliar para obtener área por nombre
def get_area_by_name(area_name):
    """Retorna la configuración de un área específica"""
    for area in areas_data:
        if area["name"] == area_name:
            return area
    return None

# Función para validar completitud del modelo
def validate_model_completeness():
    """Valida que todas las áreas mencionadas en las ecuaciones estén definidas"""
    equation_areas = set()
    for area_name, equations in area_equation_mapping.items():
        equation_areas.add(area_name)
    
    defined_areas = set(area["name"] for area in areas_data)
    
    missing_areas = equation_areas - defined_areas
    extra_areas = defined_areas - equation_areas
    
    return {
        "complete": len(missing_areas) == 0,
        "missing_areas": list(missing_areas),
        "extra_areas": list(extra_areas),
        "total_areas": len(defined_areas)
    }

# Configuración de simulación por defecto
default_simulation_config = {
    "periodo_simulacion_dias": 30,
    "datos_historicos_requeridos": 90,
    "frecuencia_actualizacion": "diaria",
    "alertas_desviacion": True,
    "precision_minima": 0.80
}