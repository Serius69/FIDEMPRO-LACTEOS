# questionary_result_data.py - Versión Optimizada con Respuestas Dinámicas
import random
import numpy as np
from datetime import datetime, timedelta

# Funciones para generar respuestas dinámicas basadas en contexto
def generar_demanda_historica(base, dias=30, producto='Leche', contexto=None):
    """Genera datos históricos de demanda realistas con patrones"""
    historico = []
    
    for dia in range(dias):
        # Factor estacional
        dia_año = dia % 365
        factor_estacional = 1.0
        if 152 <= dia_año <= 243:  # Invierno boliviano
            factor_estacional = 1.15 if producto in ['Leche', 'Queso'] else 0.9
        elif 335 <= dia_año or dia_año <= 59:  # Verano
            factor_estacional = 0.85 if producto in ['Leche'] else 1.2 if producto == 'Yogur' else 1.0
        
        # Factor día de semana
        dia_semana = dia % 7
        factor_dia = [0.9, 0.95, 1.0, 1.05, 1.15, 1.25, 1.10][dia_semana]
        
        # Tendencia general (crecimiento o decrecimiento)
        tendencia = 1 + (0.0002 * dia) if contexto and contexto.get('creciendo', True) else 1 - (0.0001 * dia)
        
        # Eventos especiales
        factor_evento = 1.0
        if dia % 30 == 0:  # Fin de mes
            factor_evento = 1.1
        elif dia % 7 == 5:  # Sábados
            factor_evento = 1.2
        
        # Cálculo final con variabilidad
        valor = base * factor_estacional * factor_dia * tendencia * factor_evento
        valor *= np.random.normal(1.0, 0.08)  # Variación aleatoria 8%
        
        historico.append(round(valor, 0))
    
    return historico

def calcular_precio_dinamico(producto, mercado='urbano', competencia='normal'):
    """Calcula precio dinámico según producto y condiciones de mercado"""
    precios_base = {
        'Leche': {'urbano': 7.00, 'rural': 6.50, 'premium': 8.50},
        'Yogur': {'urbano': 12.00, 'rural': 10.00, 'premium': 15.00},
        'Queso': {'urbano': 55.00, 'rural': 48.00, 'premium': 68.00},
        'Mantequilla': {'urbano': 70.00, 'rural': 65.00, 'premium': 85.00},
        'Crema de Leche': {'urbano': 18.00, 'rural': 16.00, 'premium': 22.00},
        'Leche Deslactosada': {'urbano': 12.00, 'rural': 11.00, 'premium': 14.00},
        'Dulce de Leche': {'urbano': 40.00, 'rural': 35.00, 'premium': 48.00}
    }
    
    precio = precios_base.get(producto, {}).get(mercado, 10.00)
    
    # Ajuste por competencia
    if competencia == 'alta':
        precio *= 0.95
    elif competencia == 'baja':
        precio *= 1.05
    
    return precio

def calcular_capacidad_produccion(empleados, tecnologia='media', experiencia_años=5):
    """Calcula capacidad de producción según recursos"""
    capacidad_base_por_empleado = {
        'baja': 150,
        'media': 200,
        'alta': 300
    }
    
    capacidad = empleados * capacidad_base_por_empleado.get(tecnologia, 200)
    
    # Bonus por experiencia (hasta 30% adicional)
    factor_experiencia = 1 + min(0.3, experiencia_años * 0.03)
    
    return int(capacidad * factor_experiencia)

# Datos de cuestionarios específicos por empresa y producto
questionary_result_data = [
    {
        'name': 'Respuestas PIL Andina - Leche',
        'product': 'Leche',
        'business_type': 'Empresa láctea industrial',
        'location': 'La Paz, Bolivia',
        'employees': 45,
        'years_in_business': 15,
        'market_position': 'líder',
        'technology_level': 'alta'
    },
    {
        'name': 'Respuestas Delizia - Yogur',
        'product': 'Yogur',
        'business_type': 'Mediana empresa procesadora',
        'location': 'Santa Cruz, Bolivia',
        'employees': 25,
        'years_in_business': 10,
        'market_position': 'competidor',
        'technology_level': 'media'
    },
    {
        'name': 'Respuestas Quesería Suiza - Queso',
        'product': 'Queso',
        'business_type': 'Empresa artesanal premium',
        'location': 'Cochabamba, Bolivia',
        'employees': 18,
        'years_in_business': 8,
        'market_position': 'nicho',
        'technology_level': 'media'
    },
    {
        'name': 'Respuestas La Campiña - Mantequilla',
        'product': 'Mantequilla',
        'business_type': 'Cooperativa lechera',
        'location': 'Tarija, Bolivia',
        'employees': 12,
        'years_in_business': 6,
        'market_position': 'regional',
        'technology_level': 'media'
    },
    {
        'name': 'Respuestas Lácteos del Valle - Crema',
        'product': 'Crema de Leche',
        'business_type': 'PYME láctea',
        'location': 'Sucre, Bolivia',
        'employees': 8,
        'years_in_business': 4,
        'market_position': 'local',
        'technology_level': 'baja'
    },
    {
        'name': 'Respuestas Prolac - Leche Deslactosada',
        'product': 'Leche Deslactosada',
        'business_type': 'Empresa especializada',
        'location': 'Santa Cruz, Bolivia',
        'employees': 15,
        'years_in_business': 5,
        'market_position': 'especialista',
        'technology_level': 'alta'
    },
    {
        'name': 'Respuestas Tradición - Dulce de Leche',
        'product': 'Dulce de Leche',
        'business_type': 'Empresa familiar tradicional',
        'location': 'Potosí, Bolivia',
        'employees': 10,
        'years_in_business': 12,
        'market_position': 'tradicional',
        'technology_level': 'baja'
    }
]

# Función para generar respuestas dinámicas completas
def generar_respuestas_dinamicas(producto, contexto_empresa):
    """Genera un set completo de respuestas dinámicas para el cuestionario"""
    
    # Extraer información del contexto
    empleados = contexto_empresa.get('employees', 15)
    años_experiencia = contexto_empresa.get('years_in_business', 5)
    tecnologia = contexto_empresa.get('technology_level', 'media')
    posicion_mercado = contexto_empresa.get('market_position', 'competidor')
    ubicacion = contexto_empresa.get('location', 'La Paz, Bolivia')
    
    # Determinar parámetros base según posición de mercado
    factor_mercado = {
        'líder': 1.3,
        'competidor': 1.0,
        'nicho': 0.8,
        'regional': 0.9,
        'local': 0.7,
        'especialista': 1.1,
        'tradicional': 0.85
    }.get(posicion_mercado, 1.0)
    
    # Calcular valores dinámicos
    precio_actual = calcular_precio_dinamico(producto, 'urbano' if 'La Paz' in ubicacion or 'Santa Cruz' in ubicacion else 'rural')
    capacidad_produccion = calcular_capacidad_produccion(empleados, tecnologia, años_experiencia)
    demanda_base = capacidad_produccion * 0.85 * factor_mercado  # 85% utilización promedio
    
    respuestas = [
        {
            'answer': round(precio_actual * (0.95 + random.random() * 0.1), 2),
            'question': '¿Cuál es el precio actual del producto?',
            'unit': 'Bs/L' if producto != 'Queso' else 'Bs/kg',
            'initials_variable': 'PVP',
            'justification': f'Precio competitivo en mercado {ubicacion.split(",")[0]}',
            'variable_name': 'precio_actual',
            'dynamic_update': lambda dia, demanda: precio_actual * (1 + 0.1 * (demanda - demanda_base) / demanda_base)
        },
        {
            'answer': generar_demanda_historica(demanda_base, 30, producto, {'creciendo': posicion_mercado in ['líder', 'especialista']}),
            'question': 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).',
            'unit': 'Litros/día' if producto != 'Queso' else 'kg/día',
            'initials_variable': 'DH',
            'justification': f'Datos reales con estacionalidad de {producto}',
            'variable_name': 'demanda_historica',
            'analisis': {
                'tendencia': 'creciente' if posicion_mercado in ['líder', 'especialista'] else 'estable',
                'volatilidad': np.std(generar_demanda_historica(demanda_base, 30, producto)) / demanda_base,
                'estacionalidad': True if producto in ['Leche', 'Yogur'] else False
            }
        },
        {
            'answer': int(demanda_base),
            'question': '¿Cuál es la cantidad producida diariamente?',
            'unit': 'Litros/día' if producto != 'Queso' else 'kg/día',
            'initials_variable': 'QPL',
            'justification': f'Producción optimizada para demanda actual',
            'variable_name': 'cantidad_producida_diaria',
            'dynamic_update': lambda demanda, inventario: min(capacidad_produccion, max(0, demanda * 1.05 - inventario * 0.1))
        },
        {
            'answer': int(demanda_base * 1.15),
            'question': '¿Cuál es la demanda esperada para los productos lácteos?',
            'unit': 'Litros/día' if producto != 'Queso' else 'kg/día',
            'initials_variable': 'DE',
            'justification': f'Proyección con crecimiento del {int((1.15 - 1) * 100)}%',
            'variable_name': 'demanda_esperada',
            'factores_proyeccion': {
                'crecimiento_mercado': 0.05,
                'expansion_planificada': 0.05,
                'marketing_adicional': 0.05
            }
        },
        {
            'answer': int(capacidad_produccion * 5),  # 5 días de capacidad
            'question': '¿Cuál es la capacidad del inventario de productos?',
            'unit': 'Litros' if producto != 'Queso' else 'kg',
            'initials_variable': 'CIP',
            'justification': f'Capacidad para {5} días de producción máxima',
            'variable_name': 'capacidad_inventario_productos',
            'costo_expansion': 500  # Bs por unidad adicional de capacidad
        },
        {
            'answer': 'Sí' if producto in ['Leche', 'Yogur', 'Mantequilla'] else 'No',
            'question': '¿Existe estacionalidad en la demanda?',
            'initials_variable': 'ED',
            'justification': f'{producto} {"presenta" if producto in ["Leche", "Yogur", "Mantequilla"] else "no presenta"} variaciones estacionales',
            'variable_name': 'estacionalidad_demanda',
            'patron_estacional': {
                'invierno': 1.15 if producto == 'Leche' else 0.9,
                'verano': 0.85 if producto == 'Leche' else 1.2 if producto == 'Yogur' else 1.0
            }
        },
        {
            'answer': round(4.0 + (empleados / 10) + (1 if tecnologia == 'alta' else 2), 2),
            'question': '¿Cuál es el costo unitario del insumo para la producción?',
            'unit': 'Bs/L' if producto != 'Queso' else 'Bs/L leche',
            'initials_variable': 'CUIP',
            'justification': f'Costo negociado con {3 + int(empleados/15)} proveedores',
            'variable_name': 'costo_unitario_insumo_produccion',
            'dynamic_update': lambda volumen, dia: (4.0 + (empleados / 10)) * (0.95 if volumen > 2000 else 1.0) * (1 + 0.00015 * dia)
        },
        {
            'answer': 3 if posicion_mercado in ['líder', 'competidor'] else 2,
            'question': '¿Tiempo promedio entre compras de los clientes?',
            'unit': 'días',
            'initials_variable': 'TPC',
            'justification': f'Frecuencia típica para {producto} en {ubicacion.split(",")[0]}',
            'variable_name': 'tiempo_promedio_compras',
            'factores_frecuencia': {
                'fidelidad': 0.8 if posicion_mercado == 'líder' else 0.6,
                'conveniencia': 0.7,
                'precio': 0.9 if precio_actual < 10 else 0.7
            }
        },
        {
            'answer': int(demanda_base / 30),  # Clientes según volumen
            'question': '¿Cuántos clientes llegan diariamente?',
            'unit': 'clientes/día',
            'initials_variable': 'CPD',
            'justification': f'Base de clientes {"B2B y B2C" if producto in ["Mantequilla", "Crema de Leche"] else "principalmente B2C"}',
            'variable_name': 'clientes_por_dia',
            'segmentacion': {
                'b2b': 0.6 if producto in ['Mantequilla', 'Crema de Leche', 'Queso'] else 0.2,
                'b2c': 0.4 if producto in ['Mantequilla', 'Crema de Leche', 'Queso'] else 0.8
            }
        },
        {
            'answer': empleados,
            'question': '¿Cuál es el número de empleados?',
            'unit': 'empleados',
            'initials_variable': 'NEPP',
            'justification': f'Plantilla actual de {contexto_empresa["business_type"]}',
            'variable_name': 'numero_empleados_produccion',
            'distribucion': {
                'produccion': 0.6,
                'administracion': 0.2,
                'ventas': 0.15,
                'otros': 0.05
            }
        },
        {
            'answer': capacidad_produccion,
            'question': '¿Cuál es la capacidad de producción diaria?',
            'unit': 'Litros/día' if producto != 'Queso' else 'kg/día',
            'initials_variable': 'CPROD',
            'justification': f'Capacidad instalada con tecnología {tecnologia}',
            'variable_name': 'capacidad_produccion_diaria',
            'utilizacion_actual': 0.85,
            'potencial_expansion': 1.3
        },
        {
            'answer': empleados * 3500 * (1.2 if tecnologia == 'alta' else 1.0),
            'question': '¿Cuáles son los sueldos y salarios totales de los empleados?',
            'unit': 'Bs/mes',
            'initials_variable': 'SE',
            'justification': f'Salarios competitivos para retener talento en {ubicacion.split(",")[0]}',
            'variable_name': 'sueldos_empleados',
            'componentes': {
                'basico': 0.7,
                'bonos': 0.15,
                'beneficios': 0.15
            }
        },
        {
            'answer': round(precio_actual * 1.02, 2),
            'question': '¿Cuál es el precio promedio actual de los productos lácteos de la competencia?',
            'unit': 'Bs/L' if producto != 'Queso' else 'Bs/kg',
            'initials_variable': 'PC',
            'justification': f'Precio promedio de {5 + int(random.random() * 5)} competidores directos',
            'variable_name': 'precio_competencia',
            'competidores_principales': ['PIL', 'Delizia', 'Pil Andina'] if producto == 'Leche' else ['Local 1', 'Local 2', 'Regional']
        },
        {
            'answer': int(800 + empleados * 50 + (200 if tecnologia == 'alta' else 0)),
            'question': '¿Cuál es el costo fijo diario?',
            'unit': 'Bs/día',
            'initials_variable': 'CFD',
            'justification': 'Incluye alquiler, servicios, seguros y mantenimiento',
            'variable_name': 'costo_fijo_diario',
            'desglose': {
                'alquiler': 0.4,
                'servicios': 0.25,
                'seguros': 0.15,
                'mantenimiento': 0.1,
                'otros': 0.1
            }
        },
        {
            'answer': round(0.3 + 0.05 * (1 if ubicacion.split(",")[0] in ['La Paz', 'Santa Cruz'] else 2), 2),
            'question': '¿Cuál es el costo unitario por transporte?',
            'unit': 'Bs/L' if producto != 'Queso' else 'Bs/kg',
            'initials_variable': 'CUTRANS',
            'justification': f'Costo logístico en {ubicacion.split(",")[0]} con distancia promedio {25 if "urbano" in ubicacion else 50}km',
            'variable_name': 'costo_unitario_transporte',
            'factores_costo': {
                'combustible': 0.6,
                'mantenimiento': 0.2,
                'personal': 0.2
            }
        },
        {
            'answer': int(1500 + demanda_base * 0.5),
            'question': '¿Cuáles son los gastos de marketing mensuales?',
            'unit': 'Bs/mes',
            'initials_variable': 'GMM',
            'justification': f'Inversión para mantener posición de {posicion_mercado}',
            'variable_name': 'gastos_marketing_mensuales',
            'distribucion': {
                'digital': 0.4,
                'tradicional': 0.3,
                'promociones': 0.2,
                'eventos': 0.1
            }
        },
        {
            'answer': 2 if tecnologia == 'alta' else 3,
            'question': '¿Cada cuánto tiempo se reabastece de insumos?',
            'unit': 'días',
            'initials_variable': 'TR',
            'justification': f'Frecuencia óptima con {3 + int(empleados/15)} proveedores',
            'variable_name': 'tiempo_reabastecimiento',
            'factores_decision': {
                'capacidad_almacenamiento': 0.4,
                'flujo_caja': 0.3,
                'confiabilidad_proveedores': 0.3
            }
        },
        {
            'answer': 1.05 if producto == 'Leche' else 1.15 if producto == 'Yogur' else 10.5 if producto == 'Queso' else 1.1,
            'question': '¿Cuántos litros de insumo se utilizan para fabricar un litro de producto?',
            'unit': 'L insumo/L producto',
            'initials_variable': 'CINSP',
            'justification': f'Rendimiento estándar para {producto}',
            'variable_name': 'conversion_insumo_producto',
            'factores_eficiencia': {
                'calidad_insumo': 0.95,
                'proceso': 0.98 if tecnologia == 'alta' else 0.95,
                'mermas': 0.02
            }
        },
        {
            'answer': int(capacidad_produccion * 7),  # 7 días de capacidad
            'question': '¿Cuál es la capacidad máxima de almacenamiento en inventario de productos lácteos?',
            'unit': 'Litros' if producto != 'Queso' else 'kg',
            'initials_variable': 'CMIPF',
            'justification': f'Almacén refrigerado para {7} días de producción',
            'variable_name': 'capacidad_maxima_inventario_productos_finales',
            'condiciones': {
                'temperatura': 4,
                'humedad': 85,
                'rotacion': 'FIFO'
            }
        },
        {
            'answer': 60 - int(años_experiencia * 1.5),
            'question': '¿Cuánto tiempo tarda cada empleado en producir una unidad de producto?',
            'unit': 'minutos/100L',
            'initials_variable': 'TPE',
            'justification': f'Eficiencia mejorada por {años_experiencia} años de experiencia',
            'variable_name': 'tiempo_produccion_empleado',
            'curva_aprendizaje': lambda dias: max(30, 60 - dias * 0.05)
        },
        {
            'answer': int(capacidad_produccion / 5),
            'question': '¿Cuánto es la cantidad promedio producida por lote?',
            'unit': 'Litros/lote' if producto != 'Queso' else 'kg/lote',
            'initials_variable': 'CPPL',
            'justification': f'Lotes optimizados para tecnología {tecnologia}',
            'variable_name': 'cantidad_promedio_por_lote',
            'optimizacion': {
                'setup_time': 30,  # minutos
                'eficiencia_lote': 0.95
            }
        },
        {
            'answer': int(demanda_base * 1.5),  # 1.5 días de demanda
            'question': '¿Cuál es el stock de inventario mínimo de seguridad?',
            'unit': 'Litros' if producto != 'Queso' else 'kg',
            'initials_variable': 'SI',
            'justification': f'Stock para cubrir {1.5} días de demanda promedio',
            'variable_name': 'stock_inventario_seguridad',
            'calculo_dinamico': lambda demanda_promedio, variabilidad, lead_time: 
                demanda_promedio * lead_time + 2 * np.sqrt(lead_time) * variabilidad
        },
        {
            'answer': 2 if tecnologia == 'alta' else 3,
            'question': '¿Días promedio de reabastecimiento?',
            'unit': 'días',
            'initials_variable': 'DPL',
            'justification': f'Lead time con proveedores {"locales" if ubicacion.split(",")[0] in ["La Paz", "Santa Cruz"] else "regionales"}',
            'variable_name': 'dias_promedio_lead_time',
            'componentes_lead_time': {
                'procesamiento_pedido': 0.5,
                'preparacion': 0.5,
                'transporte': 1 if tecnologia == 'alta' else 2
            }
        },
        {
            'answer': 1,
            'question': '¿Cuál es el tiempo medio de procesamiento de pedidos?',
            'unit': 'días',
            'initials_variable': 'TMP',
            'justification': f'Proceso {"automatizado" if tecnologia == "alta" else "semi-automatizado"}',
            'variable_name': 'tiempo_medio_procesamiento',
            'mejoras_posibles': {
                'digitalizacion': 0.5,
                'automatizacion': 0.3,
                'capacitacion': 0.2
            }
        },
        {
            'answer': int(capacidad_produccion * 0.4),
            'question': '¿Cuántos litros se transportan por viaje?',
            'unit': 'Litros/viaje' if producto != 'Queso' else 'kg/viaje',
            'initials_variable': 'CTPLV',
            'justification': f'Capacidad promedio de flota {"propia" if posicion_mercado == "líder" else "tercerizada"}',
            'variable_name': 'capacidad_transporte_por_viaje',
            'optimizacion_rutas': {
                'factor_carga': 0.85,
                'rutas_diarias': 3 if ubicacion.split(",")[0] in ['La Paz', 'Santa Cruz'] else 2
            }
        }
    ]
    
    # Agregar preguntas específicas según el producto
    if producto == 'Queso':
        respuestas.extend([
            {
                'answer': 3 + int(empleados / 10),
                'question': '¿Cuántos proveedores de leche tiene?',
                'unit': 'proveedores',
                'initials_variable': 'NPD',
                'justification': f'Red diversificada para asegurar calidad y suministro',
                'variable_name': 'numero_proveedores_leche',
                'evaluacion_proveedores': {
                    'calidad': 0.4,
                    'precio': 0.3,
                    'confiabilidad': 0.3
                }
            },
            {
                'answer': int(demanda_base * 10.5),  # Conversión leche a queso
                'question': '¿Cuál es el consumo diario promedio de leche?',
                'unit': 'Litros/día',
                'initials_variable': 'CTL',
                'justification': f'Para producir {demanda_base} kg de queso diarios',
                'variable_name': 'consumo_total_leche',
                'eficiencia_conversion': 0.095  # 9.5% rendimiento
            }
        ])
    
    return respuestas

# Función para obtener respuestas realistas según producto
def get_realistic_answers(product_type):
    """Retorna respuestas dinámicas y realistas según el tipo de producto"""
    
    # Buscar contexto de empresa para el producto
    contexto = next((q for q in questionary_result_data if q['product'].lower() == product_type.lower()), None)
    
    if not contexto:
        # Contexto genérico si no se encuentra
        contexto = {
            'product': product_type.title(),
            'employees': 15,
            'years_in_business': 5,
            'technology_level': 'media',
            'market_position': 'competidor',
            'location': 'La Paz, Bolivia',
            'business_type': 'PYME láctea'
        }
    
    return generar_respuestas_dinamicas(product_type.title(), contexto)

# Función para simular evolución de respuestas en el tiempo
def simular_evolucion_respuestas(respuestas_iniciales, dias=30):
    """Simula cómo evolucionan las respuestas del cuestionario en el tiempo"""
    
    evolucion = []
    respuestas_actuales = respuestas_iniciales.copy()
    
    for dia in range(dias):
        respuestas_dia = {}
        
        for respuesta in respuestas_actuales:
            variable = respuesta['variable_name']
            valor_actual = respuesta['answer']
            
            # Aplicar actualización dinámica si existe
            if 'dynamic_update' in respuesta and callable(respuesta['dynamic_update']):
                # Aquí se aplicarían las funciones de actualización con el contexto del día
                valor_nuevo = valor_actual  # Simplificado para el ejemplo
            else:
                valor_nuevo = valor_actual
            
            respuestas_dia[variable] = valor_nuevo
        
        respuestas_dia['dia'] = dia + 1
        respuestas_dia['fecha'] = datetime.now() + timedelta(days=dia)
        evolucion.append(respuestas_dia)
    
    return evolucion

# Función para analizar coherencia entre respuestas
def validar_coherencia_respuestas(respuestas):
    """Valida que las respuestas sean coherentes entre sí"""
    
    validaciones = []
    
    # Extraer valores para validación
    valores = {r['variable_name']: r['answer'] for r in respuestas if 'variable_name' in r}
    
    # Validación 1: Capacidad de producción vs producción diaria
    if 'capacidad_produccion_diaria' in valores and 'cantidad_producida_diaria' in valores:
        if valores['cantidad_producida_diaria'] > valores['capacidad_produccion_diaria']:
            validaciones.append({
                'tipo': 'error',
                'mensaje': 'La producción diaria excede la capacidad instalada'
            })
    
    # Validación 2: Demanda vs ventas
    if 'demanda_esperada' in valores and 'cantidad_producida_diaria' in valores:
        utilizacion = valores['cantidad_producida_diaria'] / valores['demanda_esperada']
        if utilizacion < 0.7:
            validaciones.append({
                'tipo': 'advertencia',
                'mensaje': f'Baja utilización de capacidad: {utilizacion:.1%}'
            })
    
    # Validación 3: Precio vs competencia
    if 'precio_actual' in valores and 'precio_competencia' in valores:
        diferencia = abs(valores['precio_actual'] - valores['precio_competencia']) / valores['precio_competencia']
        if diferencia > 0.2:
            validaciones.append({
                'tipo': 'advertencia',
                'mensaje': f'Precio muy diferente a la competencia: {diferencia:.1%}'
            })
    
    # Validación 4: Inventario vs vida útil
    if 'capacidad_inventario_productos' in valores and 'cantidad_producida_diaria' in valores:
        dias_inventario = valores['capacidad_inventario_productos'] / valores['cantidad_producida_diaria']
        if dias_inventario > 7:  # Asumiendo productos lácteos frescos
            validaciones.append({
                'tipo': 'advertencia',
                'mensaje': f'Inventario excesivo para productos perecederos: {dias_inventario:.1f} días'
            })
    
    return validaciones

# Exportar funciones principales
__all__ = ['questionary_result_data', 'get_realistic_answers', 'generar_respuestas_dinamicas',
           'simular_evolucion_respuestas', 'validar_coherencia_respuestas', 
           'generar_demanda_historica', 'calcular_precio_dinamico', 'calcular_capacidad_produccion']