# variables_data.py - Versión Optimizada con Variables Dinámicas
import numpy as np
from datetime import datetime, timedelta

# Funciones auxiliares para cálculos dinámicos
def calcular_factor_temporal(dia):
    """Calcula factor de temporada basado en el día del año"""
    dia_año = dia % 365
    # Invierno boliviano (junio-agosto) = días 152-243
    if 152 <= dia_año <= 243:
        return 1.15  # Mayor consumo de lácteos en invierno
    # Verano (diciembre-febrero) = días 335-365 o 1-59
    elif dia_año >= 335 or dia_año <= 59:
        return 0.85  # Menor consumo en verano
    else:
        return 1.0  # Normal en otoño/primavera

def calcular_costo_dinamico(base, demanda, demanda_promedio):
    """Calcula costo unitario basado en volumen de demanda"""
    factor_volumen = demanda / demanda_promedio if demanda_promedio > 0 else 1
    if factor_volumen > 1.2:  # Alta demanda = economías de escala
        return base * 0.95
    elif factor_volumen < 0.8:  # Baja demanda = costos fijos distribuidos
        return base * 1.1
    return base

def calcular_precio_dinamico(base, dia_semana, factor_competencia=1.0):
    """Precio dinámico según día de la semana y competencia"""
    # Fines de semana tienen precios ligeramente mayores
    factor_dia = 1.05 if dia_semana in [5, 6] else 1.0
    return base * factor_dia * factor_competencia

# Variables base del sistema con capacidad de evolución dinámica
variables_data = [
    # VARIABLES EXÓGENAS (TIPO 1) - Con comportamiento dinámico
    {
        'name': 'PRECIO DE VENTA DEL PRODUCTO',
        'initials': 'PVP',
        'type': 1,
        'unit': 'BS',
        'description': 'PRECIO DE VENTA DINÁMICO SEGÚN DEMANDA Y TEMPORADA',
        'default_value': 15.50,
        'dynamic_formula': lambda base, dia, demanda: calcular_precio_dinamico(
            base, 
            dia % 7, 
            1.0 + (demanda - 2500) / 10000  # Ajuste por demanda
        ),
        'min_value': 12.00,
        'max_value': 20.00
    },
    
    {
        'name': 'DEMANDA HISTÓRICA',
        'initials': 'DH',
        'type': 1,
        'unit': 'L',
        'description': 'DEMANDA CON VARIACIÓN ESTACIONAL Y ALEATORIA',
        'default_value': 2500,
        'dynamic_formula': lambda base, dia: base * calcular_factor_temporal(dia) * np.random.normal(1.0, 0.08),
        'min_value': 1500,
        'max_value': 4000
    },
    
    {
        'name': 'DEMANDA ESPERADA',
        'initials': 'DE',
        'type': 1,
        'unit': 'L',
        'description': 'PROYECCIÓN DE DEMANDA CON TENDENCIA',
        'default_value': 2650,
        'dynamic_formula': lambda base, dia: base * (1 + 0.0002 * dia) * calcular_factor_temporal(dia),
        'min_value': 2000,
        'max_value': 3500
    },
    
    {
        'name': 'CAPACIDAD INVENTARIO PRODUCTOS',
        'initials': 'CIP',
        'type': 1,
        'unit': 'L',
        'description': 'CAPACIDAD MÁXIMA DE ALMACENAMIENTO REFRIGERADO',
        'default_value': 15000,
        'dynamic_formula': lambda base, dia: base,  # Fija pero puede expandirse
        'expansion_cost': 50000  # Costo por cada 1000L adicionales
    },
    
    {
        'name': 'ESTACIONALIDAD DE LA DEMANDA',
        'initials': 'ED',
        'type': 1,
        'unit': '[0-1]',
        'description': 'FACTOR DE ESTACIONALIDAD DINÁMICO',
        'default_value': 1.0,
        'dynamic_formula': lambda base, dia: calcular_factor_temporal(dia)
    },
    
    {
        'name': 'COSTO UNITARIO INSUMO PRODUCCIÓN',
        'initials': 'CUIP',
        'type': 1,
        'unit': 'BS/L',
        'description': 'COSTO DINÁMICO SEGÚN VOLUMEN Y TEMPORADA',
        'default_value': 8.20,
        'dynamic_formula': lambda base, dia, volumen: calcular_costo_dinamico(
            base * (1 + 0.0001 * dia),  # Inflación gradual
            volumen,
            2500
        ),
        'min_value': 7.00,
        'max_value': 10.00
    },
    
    {
        'name': 'TIEMPO PROMEDIO ENTRE COMPRAS',
        'initials': 'TPC',
        'type': 1,
        'unit': 'DÍAS',
        'description': 'FRECUENCIA DINÁMICA DE COMPRA',
        'default_value': 2,
        'dynamic_formula': lambda base, satisfaccion_cliente: max(1, base - (satisfaccion_cliente - 0.8) * 2),
        'min_value': 1,
        'max_value': 7
    },
    
    {
        'name': 'CLIENTES POR DÍA',
        'initials': 'CPD',
        'type': 1,
        'unit': 'CLIENTES',
        'description': 'CLIENTES CON VARIACIÓN POR DÍA Y MARKETING',
        'default_value': 85,
        'dynamic_formula': lambda base, dia, inversion_marketing: int(
            base * (1 + 0.0003 * dia) * (1 + inversion_marketing / 10000) * np.random.normal(1, 0.1)
        ),
        'min_value': 50,
        'max_value': 150
    },
    
    {
        'name': 'NUMERO DE EMPLEADOS',
        'initials': 'NEPP',
        'type': 1,
        'unit': 'EMPLEADOS',
        'description': 'PLANTILLA AJUSTABLE SEGÚN PRODUCCIÓN',
        'default_value': 15,
        'dynamic_formula': lambda base, produccion_promedio: max(10, int(produccion_promedio / 200)),
        'costo_contratacion': 3000,
        'costo_despido': 5000
    },
    
    {
        'name': 'CANTIDAD PROMEDIO PRODUCCIÓN POR LOTE',
        'initials': 'CPPL',
        'type': 1,
        'unit': 'L',
        'description': 'TAMAÑO DE LOTE OPTIMIZADO',
        'default_value': 500,
        'dynamic_formula': lambda base, demanda_diaria: int(demanda_diaria / 5) * 5,  # Múltiplos de 5
        'min_value': 100,
        'max_value': 1000
    },
    
    {
        'name': 'TIEMPO PRODUCCIÓN POR EMPLEADO',
        'initials': 'TPE',
        'type': 1,
        'unit': 'minutos/100L',
        'description': 'EFICIENCIA VARIABLE POR EXPERIENCIA',
        'default_value': 45,
        'dynamic_formula': lambda base, dias_experiencia: max(30, base - dias_experiencia * 0.05),
        'min_value': 30,
        'max_value': 60
    },
    
    {
        'name': 'SUELDOS EMPLEADOS',
        'initials': 'SE',
        'type': 1,
        'unit': 'BS/MES',
        'description': 'NÓMINA CON BONOS POR PRODUCTIVIDAD',
        'default_value': 48000,
        'dynamic_formula': lambda base, productividad, num_empleados: base + (productividad - 100) * 50 * num_empleados,
        'bono_maximo': 0.2  # 20% máximo de bono
    },
    
    {
        'name': 'PRECIO DE VENTA DE LA COMPETENCIA',
        'initials': 'PC',
        'type': 1,
        'unit': 'BS',
        'description': 'PRECIO COMPETENCIA CON REACCIÓN AL MERCADO',
        'default_value': 15.80,
        'dynamic_formula': lambda base, precio_propio: base + (precio_propio - base) * 0.3,  # Sigue parcialmente
        'retraso_dias': 7  # Reacciona con 7 días de retraso
    },
    
    {
        'name': 'COSTO FIJO DIARIO',
        'initials': 'CFD',
        'type': 1,
        'unit': 'BS/DÍA',
        'description': 'COSTOS FIJOS CON AJUSTES ESTACIONALES',
        'default_value': 1800,
        'dynamic_formula': lambda base, dia: base * (1.1 if calcular_factor_temporal(dia) > 1 else 1.0),
        'componentes': {
            'alquiler': 800,
            'servicios': 400,
            'seguros': 300,
            'otros': 300
        }
    },
    
    {
        'name': 'COSTO UNITARIO POR TRANSPORTE',
        'initials': 'CUTRANS',
        'type': 1,
        'unit': 'BS/L',
        'description': 'COSTO LOGÍSTICO VARIABLE POR DISTANCIA Y VOLUMEN',
        'default_value': 0.35,
        'dynamic_formula': lambda base, volumen, distancia_km: base * (1 - min(0.2, volumen / 10000)) * (1 + distancia_km / 100),
        'combustible_factor': 0.6  # 60% del costo es combustible
    },
    
    {
        'name': 'GASTO TOTAL MARKETING',
        'initials': 'GMM',
        'type': 1,
        'unit': 'BS/MES',
        'description': 'INVERSIÓN MARKETING ADAPTATIVA',
        'default_value': 3500,
        'dynamic_formula': lambda base, ventas_mes_anterior, objetivo_ventas: base * max(0.5, min(2.0, objetivo_ventas / ventas_mes_anterior)),
        'roi_esperado': 3.0  # Retorno esperado 3:1
    },
    
    # VARIABLES DE ESTADO (TIPO 2) - Evolucionan durante la simulación
    {
        'name': 'CANTIDAD PRODUCIDA DE PRODUCTOS LÁCTEOS',
        'initials': 'QPL',
        'type': 2,
        'unit': 'L',
        'description': 'PRODUCCIÓN DIARIA AJUSTADA A DEMANDA',
        'default_value': 2500,
        'dynamic_formula': lambda capacidad, demanda_esperada, inventario_actual: min(
            capacidad,
            max(0, demanda_esperada * 1.05 - inventario_actual * 0.1)
        ),
        'eficiencia_base': 0.85
    },
    
    {
        'name': 'CAPACIDAD DE PRODUCCIÓN',
        'initials': 'CPROD',
        'type': 2,
        'unit': 'L/DIA',
        'description': 'CAPACIDAD CON MANTENIMIENTO Y MEJORAS',
        'default_value': 3000,
        'dynamic_formula': lambda base, dias_sin_mantenimiento, inversion_mejoras: base * (1 - dias_sin_mantenimiento * 0.001) * (1 + inversion_mejoras / 100000),
        'degradacion_diaria': 0.001,
        'costo_mantenimiento': 500
    },
    
    {
        'name': 'VENTAS POR CLIENTE',
        'initials': 'VPC',
        'type': 2,
        'unit': 'L',
        'description': 'TICKET PROMEDIO VARIABLE',
        'default_value': 30,
        'dynamic_formula': lambda base, satisfaccion, promociones: base * satisfaccion * (1 + promociones * 0.2),
        'min_value': 10,
        'max_value': 100
    },
    
    {
        'name': 'INVENTARIO PRODUCTOS FINALES',
        'initials': 'IPF',
        'type': 2,
        'unit': 'L',
        'description': 'INVENTARIO CON CADUCIDAD Y MERMAS',
        'default_value': 1000,
        'dynamic_formula': lambda anterior, produccion, ventas, dias_almacenado: max(0, anterior + produccion - ventas - (anterior * 0.002 * dias_almacenado)),
        'vida_util_dias': 5,
        'merma_diaria': 0.002
    },
    
    # VARIABLES ENDÓGENAS (TIPO 3) - Calculadas a partir de otras
    {
        'name': 'DEMANDA INSATISFECHA',
        'initials': 'DI',
        'type': 3,
        'unit': 'L',
        'description': 'VENTAS PERDIDAS POR FALTA DE STOCK',
        'default_value': 0,
        'dynamic_formula': lambda demanda, ventas_reales: max(0, demanda - ventas_reales),
        'costo_oportunidad': 5.0  # BS por litro no vendido
    },
    
    {
        'name': 'INGRESOS TOTALES',
        'initials': 'IT',
        'type': 3,
        'unit': 'BS',
        'description': 'INGRESOS CON DESCUENTOS POR VOLUMEN',
        'default_value': 0,
        'dynamic_formula': lambda precio, ventas: precio * ventas * (0.95 if ventas > 3000 else 1.0),
        'descuentos': {
            1000: 0.0,
            2000: 0.02,
            3000: 0.05,
            5000: 0.08
        }
    },
    
    {
        'name': 'GANANCIAS TOTALES',
        'initials': 'GT',
        'type': 3,
        'unit': 'BS',
        'description': 'UTILIDAD NETA DESPUÉS DE TODOS LOS COSTOS',
        'default_value': 0,
        'dynamic_formula': lambda ingresos, costos_totales, impuestos: ingresos - costos_totales - (ingresos * impuestos),
        'tasa_impuesto': 0.25
    },
    
    {
        'name': 'NIVEL DE RENTABILIDAD',
        'initials': 'NR',
        'type': 3,
        'unit': '%',
        'description': 'MARGEN DE GANANCIA DINÁMICO',
        'default_value': 0,
        'dynamic_formula': lambda ganancias, ingresos: (ganancias / ingresos * 100) if ingresos > 0 else 0,
        'objetivo_minimo': 15,
        'objetivo_optimo': 25
    },
    
    {
        'name': 'PRODUCTIVIDAD EMPLEADOS',
        'initials': 'PE',
        'type': 3,
        'unit': 'L/EMPLEADO',
        'description': 'EFICIENCIA CON CURVA DE APRENDIZAJE',
        'default_value': 0,
        'dynamic_formula': lambda produccion, empleados, dias_experiencia: (produccion / empleados) * (1 + min(0.3, dias_experiencia * 0.001)),
        'mejora_maxima': 0.3
    },
    
    {
        'name': 'FACTOR UTILIZACIÓN',
        'initials': 'FU',
        'type': 3,
        'unit': '%',
        'description': 'USO EFICIENTE DE CAPACIDAD INSTALADA',
        'default_value': 0,
        'dynamic_formula': lambda produccion_real, capacidad_maxima: (produccion_real / capacidad_maxima * 100) if capacidad_maxima > 0 else 0,
        'optimo': 85,
        'alerta_baja': 60,
        'alerta_alta': 95
    },
    
    {
        'name': 'MARGEN BRUTO',
        'initials': 'MB',
        'type': 3,
        'unit': '%',
        'description': 'MARGEN ANTES DE GASTOS OPERATIVOS',
        'default_value': 0,
        'dynamic_formula': lambda ingresos, costo_produccion: ((ingresos - costo_produccion) / ingresos * 100) if ingresos > 0 else 0,
        'benchmark_industria': 35
    },
    
    {
        'name': 'PARTICIPACIÓN MERCADO',
        'initials': 'PM',
        'type': 3,
        'unit': '%',
        'description': 'CUOTA DE MERCADO DINÁMICA',
        'default_value': 0,
        'dynamic_formula': lambda ventas_propias, mercado_total: (ventas_propias / mercado_total * 100) if mercado_total > 0 else 0,
        'mercado_total_la_paz': 150000  # Litros/día
    },
    
    {
        'name': 'ROTACIÓN INVENTARIO',
        'initials': 'RTI',
        'type': 3,
        'unit': 'VECES',
        'description': 'VELOCIDAD DE ROTACIÓN DE PRODUCTOS',
        'default_value': 0,
        'dynamic_formula': lambda ventas_periodo, inventario_promedio: (ventas_periodo / inventario_promedio) if inventario_promedio > 0 else 0,
        'optimo_lacteos': 73  # 73 veces al año (cada 5 días)
    },
    
    {
        'name': 'COSTO ALMACENAMIENTO',
        'initials': 'CA',
        'type': 3,
        'unit': 'BS',
        'description': 'COSTO DE MANTENER INVENTARIO REFRIGERADO',
        'default_value': 0,
        'dynamic_formula': lambda inventario, dias_almacenado, costo_kwh: inventario * 0.02 * dias_almacenado * costo_kwh,
        'costo_refrigeracion_kwh': 0.8
    },
    
    {
        'name': 'RETORNO INVERSIÓN',
        'initials': 'RI',
        'type': 3,
        'unit': '%',
        'description': 'ROI CON HORIZONTE TEMPORAL',
        'default_value': 0,
        'dynamic_formula': lambda ganancia_acumulada, inversion_total, dias: (ganancia_acumulada / inversion_total * 365 / dias * 100) if inversion_total > 0 and dias > 0 else 0,
        'periodo_recuperacion_objetivo': 365  # días
    }
]

# Función auxiliar para obtener valor dinámico de una variable
def obtener_valor_dinamico(variable, dia, contexto=None):
    """
    Calcula el valor dinámico de una variable para un día específico
    
    Args:
        variable: Diccionario con la definición de la variable
        dia: Día de simulación
        contexto: Diccionario con valores de otras variables necesarias
    
    Returns:
        Valor calculado para la variable
    """
    if 'dynamic_formula' not in variable:
        return variable['default_value']
    
    formula = variable['dynamic_formula']
    base = variable['default_value']
    
    # Aplicar la fórmula con los parámetros disponibles
    try:
        # Determinar qué parámetros necesita la fórmula
        import inspect
        params = inspect.signature(formula).parameters
        args = {'base': base, 'dia': dia}
        
        # Agregar parámetros del contexto si están disponibles
        if contexto:
            args.update(contexto)
        
        # Filtrar solo los parámetros que la fórmula acepta
        valid_args = {k: v for k, v in args.items() if k in params}
        
        # Calcular el valor
        valor = formula(**valid_args)
        
        # Aplicar límites si existen
        if 'min_value' in variable:
            valor = max(variable['min_value'], valor)
        if 'max_value' in variable:
            valor = min(variable['max_value'], valor)
        
        return valor
        
    except Exception as e:
        # Si hay error, retornar el valor por defecto
        print(f"Error calculando {variable['name']}: {e}")
        return base

# Diccionario de interdependencias entre variables
interdependencias = {
    'IT': ['PVP', 'TPV'],  # Ingresos dependen de precio y ventas
    'GT': ['IT', 'TG'],    # Ganancias dependen de ingresos y gastos
    'DI': ['DE', 'TPV'],   # Demanda insatisfecha depende de demanda esperada y ventas
    'PE': ['QPL', 'NEPP'], # Productividad depende de producción y empleados
    'FU': ['QPL', 'CPROD'], # Factor utilización depende de producción y capacidad
    'MB': ['IT', 'CTAI'],  # Margen bruto depende de ingresos y costo insumos
    'NR': ['GT', 'IT'],    # Rentabilidad depende de ganancias e ingresos
    'PM': ['TPV', 'DH'],   # Participación mercado depende de ventas y demanda histórica
    'RTI': ['TPV', 'IPF'], # Rotación inventario depende de ventas e inventario
    'CA': ['IPF', 'CFD'],  # Costo almacenamiento depende de inventario
    'RI': ['GT', 'TG']     # ROI depende de ganancias y gastos totales
}

# Exportar funciones auxiliares
__all__ = ['variables_data', 'obtener_valor_dinamico', 'interdependencias', 
           'calcular_factor_temporal', 'calcular_costo_dinamico', 'calcular_precio_dinamico']