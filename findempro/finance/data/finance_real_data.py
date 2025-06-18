# finance_data.py - Versión Optimizada con Recomendaciones Dinámicas basadas en Demanda
import numpy as np
from datetime import datetime, timedelta

# Funciones para análisis financiero dinámico
def calcular_umbral_dinamico(base, demanda_actual, demanda_promedio, factor_riesgo=1.0):
    """Calcula umbrales dinámicos que se ajustan a la demanda"""
    factor_demanda = demanda_actual / demanda_promedio if demanda_promedio > 0 else 1.0
    factor_estacional = 1.1 if demanda_actual > demanda_promedio * 1.1 else 0.9 if demanda_actual < demanda_promedio * 0.9 else 1.0
    return base * factor_demanda * factor_estacional * factor_riesgo

def evaluar_salud_financiera(metricas, umbrales):
    """Evalúa la salud financiera basada en métricas dinámicas"""
    score = 0
    alertas = []
    
    for metrica, valor in metricas.items():
        if metrica in umbrales:
            umbral = umbrales[metrica]
            if isinstance(umbral, dict):
                if valor < umbral.get('min', float('-inf')):
                    alertas.append(f"{metrica} por debajo del mínimo: {valor:.2f}")
                    score -= 1
                elif valor > umbral.get('max', float('inf')):
                    alertas.append(f"{metrica} por encima del máximo: {valor:.2f}")
                    score -= 1
                else:
                    score += 1
            else:
                if valor < umbral:
                    alertas.append(f"{metrica} crítico: {valor:.2f} < {umbral:.2f}")
                    score -= 2
    
    return score, alertas

def generar_recomendacion_contextual(variable, valor_actual, umbral, contexto):
    """Genera recomendaciones específicas basadas en el contexto actual"""
    brecha = ((umbral - valor_actual) / umbral * 100) if umbral > 0 else 0
    
    recomendaciones_contextuales = {
        'INGRESOS TOTALES': {
            'alta_demanda': f"Aproveche la demanda alta: incremente producción en {brecha:.1f}% y ajuste precios +3-5%",
            'baja_demanda': f"Demanda baja: enfoque en promociones 2x1 y descuentos del {min(brecha, 15):.0f}%",
            'normal': f"Optimice mix de productos. Meta: incrementar ticket promedio {brecha/2:.1f}%"
        },
        'COSTO TOTAL PRODUCCIÓN': {
            'alto_volumen': f"Negocie descuentos por volumen con proveedores. Potencial ahorro: {brecha*0.3:.1f}%",
            'bajo_volumen': f"Consolide pedidos para mejorar economías de escala. Agrupe compras semanalmente",
            'normal': f"Implemente sistema de costeo ABC. Identifique el 20% de insumos que representan 80% del costo"
        },
        'MARGEN BRUTO': {
            'competencia_alta': f"Diferénciese por calidad/servicio antes que precio. Valor agregado objetivo: +{brecha:.1f}%",
            'competencia_baja': f"Oportunidad de capturar mercado. Incremente precios gradualmente {brecha*0.2:.1f}% mensual",
            'normal': f"Balance precio-volumen. Pruebe elasticidad con incrementos del {brecha*0.1:.1f}%"
        },
        'FACTOR UTILIZACIÓN': {
            'sobreutilizado': "Riesgo de burnout. Contrate {int(brecha/10)} empleados temporales o implemente 3er turno",
            'subutilizado': f"Capacidad ociosa del {brecha:.1f}%. Explore nuevos productos o maquila para terceros",
            'normal': f"Optimice programación de producción. Implemente OEE para mejorar {brecha:.1f}%"
        }
    }
    
    tipo_contexto = contexto.get('tipo', 'normal')
    recomendaciones = recomendaciones_contextuales.get(variable, {})
    
    return recomendaciones.get(tipo_contexto, f"Ajuste {variable} en {brecha:.1f}% para alcanzar objetivo")

# Datos de recomendaciones financieras con comportamiento dinámico
recommendation_data = [
    {
        'name': 'Optimización de Ingresos',
        'variable_name': 'INGRESOS TOTALES',
        'threshold_value': 1000000,
        'recommendation': 'Estrategia dinámica de precios basada en demanda y competencia',
        'dynamic_threshold': lambda demanda, precio_promedio, dias_mes=30: 
            demanda * precio_promedio * dias_mes * 0.95,  # 95% de ventas potenciales
        'priority': 'alta',
        'implementation_time': '7-14 días',
        'expected_impact': '+5-15% en ingresos',
        'action_items': [
            'Implementar pricing dinámico por hora del día',
            'Crear bundles de productos complementarios',
            'Programa de fidelización con descuentos escalonados',
            'Análisis de elasticidad precio-demanda por producto'
        ],
        'kpi_tracking': {
            'ticket_promedio': 'daily',
            'conversion_rate': 'daily',
            'customer_retention': 'weekly'
        }
    },
    
    {
        'name': 'Control de Costos de Producción',
        'variable_name': 'COSTO TOTAL PRODUCCIÓN',
        'threshold_value': 500000,
        'recommendation': 'Optimización de costos mediante economías de escala y eficiencia',
        'dynamic_threshold': lambda produccion, costo_unitario, dias_mes=30:
            produccion * costo_unitario * dias_mes * 1.05,  # Máximo 5% sobre costo ideal
        'priority': 'alta',
        'implementation_time': '14-30 días',
        'expected_impact': '-8-12% en costos',
        'action_items': [
            'Negociar contratos anuales con proveedores clave',
            'Implementar sistema de compras just-in-time',
            'Auditoría de procesos para eliminar desperdicios',
            'Programa de mejora continua (Kaizen)',
            'Análisis make-or-buy para insumos secundarios'
        ],
        'cost_reduction_strategies': {
            'corto_plazo': ['Renegociación proveedores', 'Reducción mermas'],
            'mediano_plazo': ['Automatización parcial', 'Capacitación personal'],
            'largo_plazo': ['Inversión en tecnología', 'Integración vertical']
        }
    },
    
    {
        'name': 'Gestión de Almacenamiento',
        'variable_name': 'COSTO ALMACENAMIENTO',
        'threshold_value': 300000,
        'recommendation': 'Optimización de inventarios y reducción de costos de mantención',
        'dynamic_threshold': lambda inventario_promedio, costo_m2, vida_util_producto:
            inventario_promedio * 0.02 * (8 - vida_util_producto) * 30,  # Ajustado por perecibilidad
        'priority': 'media',
        'implementation_time': '7-21 días',
        'expected_impact': '-15-25% en costos de almacenamiento',
        'action_items': [
            'Implementar sistema FEFO estricto (First Expired, First Out)',
            'Optimizar layout de almacén por rotación ABC',
            'Negociar tarifas eléctricas para refrigeración',
            'Sistema de alertas tempranas para productos próximos a vencer',
            'Cross-docking para productos de alta rotación'
        ],
        'inventory_optimization': {
            'safety_stock': lambda demanda_std, lead_time: 2 * demanda_std * np.sqrt(lead_time),
            'reorder_point': lambda demanda_diaria, lead_time, safety_stock: demanda_diaria * lead_time + safety_stock,
            'eoq': lambda demanda_anual, costo_pedido, costo_mantener: np.sqrt(2 * demanda_anual * costo_pedido / costo_mantener)
        }
    },
    
    {
        'name': 'Satisfacción de Demanda',
        'variable_name': 'DEMANDA INSATISFECHA',
        'threshold_value': 10000,
        'recommendation': 'Incrementar capacidad y mejorar planificación para cubrir demanda',
        'dynamic_threshold': lambda demanda_total: demanda_total * 0.02,  # Máximo 2% de demanda insatisfecha
        'priority': 'crítica',
        'implementation_time': '1-7 días',
        'expected_impact': '+10-20% en satisfacción cliente',
        'action_items': [
            'Análisis de cuellos de botella en producción',
            'Implementar forecasting con machine learning',
            'Acuerdos de respaldo con co-packers',
            'Programa de producción flexible por turnos',
            'Stock de seguridad dinámico por SKU'
        ],
        'demand_strategies': {
            'immediate': 'Horas extra y tercer turno',
            'short_term': 'Contratar personal temporal',
            'medium_term': 'Expandir capacidad instalada',
            'long_term': 'Nueva planta o tercerización'
        }
    },
    
    {
        'name': 'Utilización de Capacidad',
        'variable_name': 'FACTOR UTILIZACIÓN',
        'threshold_value': 30,
        'recommendation': 'Mejorar eficiencia operativa y utilización de activos',
        'dynamic_threshold': lambda capacidad_instalada, demanda_promedio:
            min(95, (demanda_promedio / capacidad_instalada) * 100),  # Target 85-95%
        'priority': 'alta',
        'implementation_time': '14-45 días',
        'expected_impact': '+20-30% en productividad',
        'action_items': [
            'Implementar OEE (Overall Equipment Effectiveness)',
            'Mantenimiento predictivo con IoT',
            'Balanceo de líneas de producción',
            'Reducción de tiempos de setup (SMED)',
            'Capacitación cruzada de operadores'
        ],
        'efficiency_metrics': {
            'availability': 0.90,  # Target
            'performance': 0.95,   # Target
            'quality': 0.99,       # Target
            'oee_target': 0.85     # 90% * 95% * 99%
        }
    },
    
    {
        'name': 'Control de Gastos Generales',
        'variable_name': 'GASTOS GENERALES',
        'threshold_value': 300000,
        'recommendation': 'Optimización de gastos administrativos y generales',
        'dynamic_threshold': lambda ingresos: ingresos * 0.15,  # Máximo 15% de ingresos
        'priority': 'media',
        'implementation_time': '30-60 días',
        'expected_impact': '-10-20% en gastos generales',
        'action_items': [
            'Auditoría de gastos recurrentes',
            'Renegociación de contratos de servicios',
            'Digitalización de procesos administrativos',
            'Implementar política de gastos con aprobaciones',
            'Consolidar compras corporativas'
        ],
        'cost_categories': {
            'eliminables': ['Suscripciones no usadas', 'Servicios duplicados'],
            'reducibles': ['Telefonía', 'Papelería', 'Viajes'],
            'optimizables': ['Seguros', 'Servicios profesionales', 'Energía']
        }
    },
    
    {
        'name': 'Optimización de Gastos Operativos',
        'variable_name': 'GASTOS OPERATIVOS',
        'threshold_value': 300000,
        'recommendation': 'Reducción sistemática de costos operativos',
        'dynamic_threshold': lambda costo_produccion: costo_produccion * 0.25,  # Máximo 25% adicional a producción
        'priority': 'alta',
        'implementation_time': '21-45 días',
        'expected_impact': '-12-18% en gastos operativos',
        'action_items': [
            'Mapeo de procesos para identificar ineficiencias',
            'Implementar 5S en todas las áreas',
            'Sistema de sugerencias de empleados',
            'Benchmarking con industria',
            'Programa de reducción de desperdicios'
        ],
        'lean_tools': [
            'Value Stream Mapping',
            'Kanban para inventarios',
            'Poka-yoke para prevenir errores',
            'TPM (Total Productive Maintenance)',
            'Six Sigma para reducir variabilidad'
        ]
    },
    
    {
        'name': 'Gestión de Gastos Totales',
        'variable_name': 'GASTOS TOTALES',
        'threshold_value': 500000,
        'recommendation': 'Control integral de gastos con enfoque en ROI',
        'dynamic_threshold': lambda ingresos, margen_objetivo=0.25:
            ingresos * (1 - margen_objetivo),  # Gastos máximos para margen objetivo
        'priority': 'crítica',
        'implementation_time': '30-90 días',
        'expected_impact': '-15-25% en gastos totales',
        'action_items': [
            'Implementar presupuesto base cero',
            'Comité de gastos con aprobaciones escalonadas',
            'Dashboard de gastos en tiempo real',
            'Análisis de gastos por centro de costo',
            'Programa de incentivos por ahorro'
        ],
        'control_framework': {
            'preventivo': 'Presupuestos y límites de aprobación',
            'detectivo': 'Monitoreo y alertas automáticas',
            'correctivo': 'Planes de acción y seguimiento'
        }
    },
    
    {
        'name': 'Reducción de Tiempo Improductivo',
        'variable_name': 'HORAS OCIOSAS',
        'threshold_value': 3000,
        'recommendation': 'Minimizar tiempos muertos y mejorar productividad',
        'dynamic_threshold': lambda horas_totales_disponibles:
            horas_totales_disponibles * 0.05,  # Máximo 5% de tiempo ocioso
        'priority': 'media',
        'implementation_time': '7-30 días',
        'expected_impact': '+15-25% en productividad',
        'action_items': [
            'Análisis de tiempos y movimientos',
            'Planificación de producción optimizada',
            'Reducción de cambios de formato',
            'Mantenimiento preventivo programado',
            'Sistema de gestión visual (Andon)'
        ],
        'productivity_boosters': {
            'quick_wins': ['Organización 5S', 'Instrucciones visuales'],
            'medium_term': ['Automatización parcial', 'Células de trabajo'],
            'long_term': ['Rediseño de planta', 'Industria 4.0']
        }
    },
    
    {
        'name': 'Mejora de Margen Bruto',
        'variable_name': 'MARGEN BRUTO',
        'threshold_value': 500000,
        'recommendation': 'Optimización integral de precios, costos y mix de productos',
        'dynamic_threshold': lambda ingresos, tipo_producto='lacteos':
            ingresos * (0.35 if tipo_producto == 'lacteos' else 0.30),  # 35% para lácteos
        'priority': 'alta',
        'implementation_time': '14-60 días',
        'expected_impact': '+5-10 puntos porcentuales',
        'action_items': [
            'Análisis de rentabilidad por SKU',
            'Reingeniería de productos de bajo margen',
            'Pricing strategy basada en valor',
            'Optimización de formulaciones',
            'Eliminación de SKUs no rentables'
        ],
        'margin_improvement_levers': {
            'pricing': {
                'estrategia': 'Value-based pricing',
                'herramientas': ['Análisis conjoint', 'Test A/B precios'],
                'impacto_esperado': '+3-5%'
            },
            'cost': {
                'estrategia': 'Lean manufacturing',
                'herramientas': ['VSM', 'Kaizen events'],
                'impacto_esperado': '-5-8%'
            },
            'mix': {
                'estrategia': 'Portfolio optimization',
                'herramientas': ['Análisis Pareto', 'BCG Matrix'],
                'impacto_esperado': '+2-4%'
            }
        }
    },
    
    {
        'name': 'Mejora de Rentabilidad',
        'variable_name': 'NIVEL DE RENTABILIDAD',
        'threshold_value': 0.3,
        'recommendation': 'Estrategia integral para mejorar ROA y ROE',
        'dynamic_threshold': lambda industria='lacteos', tamaño='pyme':
            0.15 if tamaño == 'pyme' else 0.20,  # Benchmark industria
        'priority': 'crítica',
        'implementation_time': '30-180 días',
        'expected_impact': '+30-50% en rentabilidad',
        'action_items': [
            'Optimización de estructura de capital',
            'Mejora en rotación de activos',
            'Reducción de capital de trabajo',
            'Desinversión en activos improductivos',
            'Mejora en márgenes operativos'
        ],
        'dupont_analysis': {
            'margen_neto': 'Enfoque en eficiencia operativa',
            'rotacion_activos': 'Maximizar uso de activos',
            'apalancamiento': 'Optimizar estructura deuda/capital',
            'formula': 'ROE = Margen × Rotación × Apalancamiento'
        }
    },
    
    {
        'name': 'Productividad del Personal',
        'variable_name': 'PRODUCTIVIDAD EMPLEADOS',
        'threshold_value': 300000,
        'recommendation': 'Incrementar output por empleado mediante capacitación y tecnología',
        'dynamic_threshold': lambda ventas_totales, num_empleados:
            ventas_totales / num_empleados * 0.9,  # 90% del ideal
        'priority': 'alta',
        'implementation_time': '30-120 días',
        'expected_impact': '+20-40% en productividad',
        'action_items': [
            'Programa de capacitación técnica continua',
            'Sistema de incentivos por productividad',
            'Automatización de tareas repetitivas',
            'Rediseño de puestos de trabajo',
            'Implementar KPIs individuales'
        ],
        'people_strategies': {
            'desarrollo': ['Planes de carrera', 'Mentoring', 'Certificaciones'],
            'motivacion': ['Bonos variables', 'Reconocimientos', 'Ambiente laboral'],
            'herramientas': ['ERP', 'Tablets', 'IoT sensors'],
            'medicion': ['Output/hora', 'Calidad', 'Ausentismo']
        }
    },
    
    {
        'name': 'Participación de Mercado',
        'variable_name': 'PARTICIPACIÓN MERCADO',
        'threshold_value': 100,
        'recommendation': 'Estrategia de crecimiento para ganar market share',
        'dynamic_threshold': lambda mercado_total, ventas_propias:
            (ventas_propias / mercado_total) * 100 * 1.2,  # Target: +20% share
        'priority': 'media',
        'implementation_time': '60-365 días',
        'expected_impact': '+2-5 puntos de participación',
        'action_items': [
            'Análisis de whitespaces en el mercado',
            'Desarrollo de nuevos canales',
            'Innovación en productos',
            'Campañas de captación de clientes',
            'Alianzas estratégicas'
        ],
        'growth_strategies': {
            'penetracion': 'Aumentar frecuencia y ticket en clientes actuales',
            'desarrollo_mercado': 'Expansión geográfica y nuevos segmentos',
            'desarrollo_producto': 'Innovación y line extensions',
            'diversificacion': 'Nuevas categorías relacionadas'
        }
    },
    
    {
        'name': 'Retorno sobre Inversión',
        'variable_name': 'RETORNO INVERSIÓN',
        'threshold_value': 300000,
        'recommendation': 'Maximizar ROI mediante inversiones estratégicas',
        'dynamic_threshold': lambda inversion_total, tasa_minima=0.15:
            inversion_total * tasa_minima,  # ROI mínimo 15%
        'priority': 'alta',
        'implementation_time': '90-365 días',
        'expected_impact': '+25-40% en ROI',
        'action_items': [
            'Priorización de proyectos por VAN',
            'Post-auditoría de inversiones',
            'Optimización de CAPEX',
            'Gestión activa de portfolio',
            'Desinversión de proyectos no rentables'
        ],
        'investment_criteria': {
            'payback': '< 3 años',
            'tir': '> 20%',
            'van': '> 0 con tasa 12%',
            'riesgo': 'Análisis de sensibilidad'
        }
    },
    
    {
        'name': 'Control de Gastos Totales',
        'variable_name': 'TOTAL GASTOS',
        'threshold_value': 500000,
        'recommendation': 'Gestión holística de gastos con enfoque en valor',
        'dynamic_threshold': lambda ingresos_proyectados, ebitda_objetivo=0.20:
            ingresos_proyectados * (1 - ebitda_objetivo),
        'priority': 'crítica',
        'implementation_time': '30-120 días',
        'expected_impact': '-20-30% en gastos totales',
        'action_items': [
            'Implementar Activity Based Costing',
            'Eliminar actividades que no agregan valor',
            'Consolidación de proveedores',
            'Renegociación integral de contratos',
            'Transformación digital de procesos'
        ],
        'saving_waves': {
            'wave_1': {
                'tiempo': '0-30 días',
                'foco': 'Quick wins y gastos discrecionales',
                'ahorro': '5-8%'
            },
            'wave_2': {
                'tiempo': '31-90 días',
                'foco': 'Optimización de procesos',
                'ahorro': '8-12%'
            },
            'wave_3': {
                'tiempo': '91-180 días',
                'foco': 'Transformación estructural',
                'ahorro': '10-15%'
            }
        }
    }
]

# Función para generar recomendaciones dinámicas
def generar_recomendaciones_dinamicas(metricas_actuales, contexto_empresa):
    """
    Genera recomendaciones personalizadas basadas en métricas y contexto
    
    Args:
        metricas_actuales: Dict con valores actuales de variables
        contexto_empresa: Dict con información de la empresa
    
    Returns:
        Lista de recomendaciones priorizadas
    """
    recomendaciones_personalizadas = []
    
    for rec in recommendation_data:
        variable = rec['variable_name']
        valor_actual = metricas_actuales.get(variable, 0)
        
        # Calcular umbral dinámico si existe
        if 'dynamic_threshold' in rec:
            # Preparar parámetros para el cálculo dinámico
            if variable == 'INGRESOS TOTALES':
                umbral = rec['dynamic_threshold'](
                    metricas_actuales.get('demanda_diaria', 2500),
                    metricas_actuales.get('precio_promedio', 15.50)
                )
            elif variable == 'COSTO TOTAL PRODUCCIÓN':
                umbral = rec['dynamic_threshold'](
                    metricas_actuales.get('produccion_diaria', 2500),
                    metricas_actuales.get('costo_unitario', 8.20)
                )
            else:
                umbral = rec['threshold_value']
        else:
            umbral = rec['threshold_value']
        
        # Evaluar si se necesita la recomendación
        necesita_accion = False
        urgencia = 'baja'
        
        if variable in ['INGRESOS TOTALES', 'MARGEN BRUTO', 'NIVEL DE RENTABILIDAD']:
            # Variables que queremos maximizar
            if valor_actual < umbral:
                necesita_accion = True
                brecha = (umbral - valor_actual) / umbral
                urgencia = 'crítica' if brecha > 0.3 else 'alta' if brecha > 0.15 else 'media'
        else:
            # Variables que queremos minimizar (costos, gastos)
            if valor_actual > umbral:
                necesita_accion = True
                exceso = (valor_actual - umbral) / umbral
                urgencia = 'crítica' if exceso > 0.3 else 'alta' if exceso > 0.15 else 'media'
        
        if necesita_accion:
            # Determinar contexto para recomendación específica
            contexto = {
                'tipo': 'alta_demanda' if metricas_actuales.get('demanda_diaria', 0) > 3000 else
                        'baja_demanda' if metricas_actuales.get('demanda_diaria', 0) < 2000 else 'normal',
                'competencia': contexto_empresa.get('nivel_competencia', 'normal'),
                'tamaño': contexto_empresa.get('tamaño', 'pyme'),
                'recursos': contexto_empresa.get('recursos_disponibles', 'limitados')
            }
            
            recomendacion_contextual = generar_recomendacion_contextual(
                variable, valor_actual, umbral, contexto
            )
            
            recomendacion_personalizada = {
                'nombre': rec['name'],
                'variable': variable,
                'valor_actual': valor_actual,
                'umbral_dinamico': umbral,
                'brecha': abs(valor_actual - umbral),
                'urgencia': urgencia,
                'recomendacion_general': rec['recommendation'],
                'recomendacion_especifica': recomendacion_contextual,
                'acciones': rec.get('action_items', [])[:3],  # Top 3 acciones
                'tiempo_implementacion': rec.get('implementation_time', 'Por definir'),
                'impacto_esperado': rec.get('expected_impact', 'Por evaluar'),
                'roi_estimado': calcular_roi_estimado(variable, valor_actual, umbral, contexto_empresa)
            }
            
            recomendaciones_personalizadas.append(recomendacion_personalizada)
    
    # Ordenar por urgencia y ROI
    recomendaciones_personalizadas.sort(
        key=lambda x: (
            {'crítica': 0, 'alta': 1, 'media': 2, 'baja': 3}[x['urgencia']], 
            -x['roi_estimado']
        )
    )
    
    return recomendaciones_personalizadas

def calcular_roi_estimado(variable, valor_actual, umbral, contexto):
    """Estima el ROI de implementar la recomendación"""
    
    # ROI base por tipo de variable
    roi_base = {
        'INGRESOS TOTALES': 3.0,
        'COSTO TOTAL PRODUCCIÓN': 2.5,
        'MARGEN BRUTO': 4.0,
        'GASTOS OPERATIVOS': 2.0,
        'PRODUCTIVIDAD EMPLEADOS': 3.5,
        'DEMANDA INSATISFECHA': 5.0,  # Alto ROI por recuperar ventas perdidas
        'FACTOR UTILIZACIÓN': 2.8
    }.get(variable, 1.5)
    
    # Ajustar por tamaño de la brecha
    brecha = abs(valor_actual - umbral) / umbral if umbral > 0 else 0
    factor_brecha = 1 + min(brecha, 1.0)  # Hasta 2x si la brecha es grande
    
    # Ajustar por contexto de empresa
    factor_contexto = 1.0
    if contexto.get('tamaño') == 'pyme':
        factor_contexto = 1.2  # Mayor impacto relativo en PYMEs
    
    return roi_base * factor_brecha * factor_contexto

def simular_impacto_recomendaciones(metricas_actuales, recomendaciones, dias=30):
    """
    Simula el impacto de implementar las recomendaciones
    
    Args:
        metricas_actuales: Estado actual de las métricas
        recomendaciones: Lista de recomendaciones a implementar
        dias: Período de simulación
    
    Returns:
        Proyección de métricas con recomendaciones implementadas
    """
    proyeccion = []
    metricas = metricas_actuales.copy()
    
    for dia in range(dias):
        metricas_dia = metricas.copy()
        metricas_dia['dia'] = dia + 1
        
        # Aplicar impacto gradual de cada recomendación
        for rec in recomendaciones[:3]:  # Top 3 recomendaciones
            variable = rec['variable']
            impacto = rec.get('impacto_esperado', '0%')
            
            # Extraer porcentaje de impacto
            try:
                porcentaje = float(impacto.split('%')[0].split('+')[-1].split('-')[-1]) / 100
            except:
                porcentaje = 0.1  # 10% default
            
            # Aplicar impacto gradualmente
            factor_tiempo = min(1.0, dia / 30)  # Impacto completo en 30 días
            
            if variable in ['INGRESOS TOTALES', 'MARGEN BRUTO', 'PRODUCTIVIDAD EMPLEADOS']:
                # Variables a maximizar
                metricas[variable] *= (1 + porcentaje * factor_tiempo / 30)
            else:
                # Variables a minimizar
                metricas[variable] *= (1 - porcentaje * factor_tiempo / 30)
        
        # Calcular métricas derivadas
        if 'INGRESOS TOTALES' in metricas and 'GASTOS TOTALES' in metricas:
            metricas['MARGEN BRUTO'] = metricas['INGRESOS TOTALES'] - metricas['GASTOS TOTALES']
            metricas['NIVEL DE RENTABILIDAD'] = metricas['MARGEN BRUTO'] / metricas['INGRESOS TOTALES'] if metricas['INGRESOS TOTALES'] > 0 else 0
        
        proyeccion.append(metricas_dia)
    
    return proyeccion

# Funciones de análisis financiero avanzado
def analisis_sensibilidad(metricas_base, variables_criticas, rango_variacion=0.2):
    """
    Análisis de sensibilidad sobre variables críticas
    
    Args:
        metricas_base: Métricas actuales
        variables_criticas: Lista de variables a analizar
        rango_variacion: ±% de variación
    
    Returns:
        Matriz de sensibilidad
    """
    resultados = {}
    
    for variable in variables_criticas:
        valor_base = metricas_base.get(variable, 0)
        if valor_base == 0:
            continue
            
        resultados[variable] = {}
        
        # Simular variaciones
        for variacion in [-rango_variacion, -rango_variacion/2, 0, rango_variacion/2, rango_variacion]:
            metricas_sim = metricas_base.copy()
            metricas_sim[variable] = valor_base * (1 + variacion)
            
            # Recalcular métricas financieras clave
            if variable in ['INGRESOS TOTALES', 'GASTOS TOTALES']:
                margen = metricas_sim.get('INGRESOS TOTALES', 0) - metricas_sim.get('GASTOS TOTALES', 0)
                rentabilidad = margen / metricas_sim.get('INGRESOS TOTALES', 1) if metricas_sim.get('INGRESOS TOTALES', 0) > 0 else 0
                
                resultados[variable][f"{variacion*100:+.0f}%"] = {
                    'margen': margen,
                    'rentabilidad': rentabilidad * 100,
                    'impacto_margen': ((margen - metricas_base.get('MARGEN BRUTO', 0)) / metricas_base.get('MARGEN BRUTO', 1)) * 100
                }
    
    return resultados

def calcular_punto_equilibrio(costos_fijos, precio_venta, costo_variable_unitario):
    """Calcula el punto de equilibrio en unidades y valor"""
    if precio_venta <= costo_variable_unitario:
        return float('inf'), float('inf')
    
    punto_equilibrio_unidades = costos_fijos / (precio_venta - costo_variable_unitario)
    punto_equilibrio_valor = punto_equilibrio_unidades * precio_venta
    
    return punto_equilibrio_unidades, punto_equilibrio_valor

# Exportar elementos principales
__all__ = ['recommendation_data', 'generar_recomendaciones_dinamicas', 
           'simular_impacto_recomendaciones', 'analisis_sensibilidad',
           'calcular_punto_equilibrio', 'evaluar_salud_financiera',
           'generar_recomendacion_contextual', 'calcular_roi_estimado']