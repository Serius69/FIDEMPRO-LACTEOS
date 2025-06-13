# equations_data.py - Versión Optimizada con Ecuaciones Dinámicas Basadas en Demanda
import numpy as np
from datetime import datetime

# Funciones auxiliares para comportamiento dinámico
def factor_estacional_bolivia(dia):
    """Calcula factor estacional específico para Bolivia"""
    dia_año = dia % 365
    # Temporadas en Bolivia (hemisferio sur)
    if 152 <= dia_año <= 243:  # Invierno (jun-ago)
        return {
            'demanda': 1.20,  # +20% demanda en invierno
            'precio': 1.05,   # +5% precios
            'costo': 1.08     # +8% costos (calefacción, etc)
        }
    elif 335 <= dia_año or dia_año <= 59:  # Verano (dic-feb)
        return {
            'demanda': 0.85,  # -15% demanda en verano
            'precio': 0.95,   # -5% precios
            'costo': 0.92     # -8% costos
        }
    else:  # Otoño/Primavera
        return {
            'demanda': 1.0,
            'precio': 1.0,
            'costo': 1.0
        }

def factor_dia_semana(dia):
    """Factor según día de la semana"""
    dia_semana = dia % 7
    # 0=Lunes, 6=Domingo
    factores = [0.9, 0.95, 1.0, 1.05, 1.15, 1.25, 1.10]  # Viernes/Sábado más alto
    return factores[dia_semana]

def factor_volumen_economia_escala(volumen, volumen_optimo=2500):
    """Economías de escala según volumen de producción"""
    ratio = volumen / volumen_optimo
    if ratio < 0.5:
        return 1.25  # Muy ineficiente
    elif ratio < 0.8:
        return 1.10
    elif ratio < 1.2:
        return 1.00  # Óptimo
    elif ratio < 1.5:
        return 0.95  # Economías de escala
    else:
        return 0.92  # Máximas economías

# Ecuaciones dinámicas del sistema
equations_data = [
    # ECUACIONES DE DEMANDA Y VENTAS
    {
        "name": "Demanda Diaria Proyectada",
        "description": "Proyección de demanda con factores estacionales, tendencia y aleatoriedad",
        "expression": "DE = DH * factor_estacional * factor_dia * (1 + tendencia) * random_factor",
        "variable1": "DE",
        "variable2": "DH",
        "area": "Ventas",
        "dynamic_calculation": lambda TPPRO, CPROD, dias_sin_mantenimiento=0, experiencia=1.0:
            min(1.0, (TPPRO / CPROD if CPROD > 0 else 0) * 
                (1 - 0.002 * dias_sin_mantenimiento) *  # -0.2% por día sin mantenimiento
                (0.8 + 0.2 * min(1.0, experiencia)))  # 80-100% según experiencia
    },
    
    {
        "name": "Capacidad Efectiva con Degradación",
        "description": "Capacidad que se degrada sin mantenimiento",
        "expression": "CPROD_efectiva = CPROD * (1 - degradacion) * factor_turno",
        "variable1": "CPROD",
        "variable2": "QPL",
        "variable3": "NEPP",
        "area": "Producción",
        "dynamic_calculation": lambda QPL, NEPP, dias_operacion, turnos=1:
            QPL * NEPP * (1 - 0.0001 * dias_operacion) * turnos
    },
    
    {
        "name": "Productividad con Curva Aprendizaje",
        "description": "Productividad que mejora con experiencia",
        "expression": "PE = (TPV / NEPP) * curva_aprendizaje * factor_motivacion",
        "variable1": "PE",
        "variable2": "TPV",
        "variable3": "NEPP",
        "area": "Recursos Humanos",
        "dynamic_calculation": lambda TPV, NEPP, dias_experiencia, salario_promedio=3500:
            (TPV / NEPP if NEPP > 0 else 0) * 
            (1 + 0.3 * (1 - np.exp(-dias_experiencia / 100))) *  # Curva aprendizaje
            (0.8 + 0.4 * min(1.0, salario_promedio / 4000))  # Factor motivación por salario
    },
    
    # ECUACIONES FINANCIERAS DINÁMICAS
    {
        "name": "Precio Dinámico con Elasticidad",
        "description": "Precio que responde a demanda, competencia y costos",
        "expression": "PVP = PVP_base * (1 + elasticidad_demanda + ajuste_competencia + margen_objetivo)",
        "variable1": "PVP",
        "variable2": "PC",
        "variable3": "DE",
        "area": "Ventas",
        "dynamic_calculation": lambda PVP_base, PC, DE, DE_promedio=2500, costo_unitario=8.2:
            PVP_base * 
            (1 + 0.1 * (DE - DE_promedio) / DE_promedio) *  # Elasticidad demanda
            (0.95 + 0.1 * (PC - PVP_base) / PVP_base) *  # Ajuste competencia
            max(1.0, costo_unitario / PVP_base + 0.25)  # Margen mínimo 25%
    },
    
    {
        "name": "Costo Unitario Variable",
        "description": "Costo que varía con volumen, eficiencia y factores externos",
        "expression": "CUIP = CUIP_base * factor_volumen * factor_estacional * inflacion",
        "variable1": "CUIP",
        "variable2": "TPPRO",
        "area": "Contabilidad",
        "dynamic_calculation": lambda CUIP_base, TPPRO, dia:
            CUIP_base * 
            factor_volumen_economia_escala(TPPRO) *
            factor_estacional_bolivia(dia)['costo'] *
            (1 + 0.00015 * dia)  # Inflación 0.015% diaria (5.5% anual)
    },
    
    {
        "name": "Ingresos con Descuentos por Volumen",
        "description": "Ingresos que incluyen descuentos dinámicos",
        "expression": "IT = TPV * PVP * (1 - descuento_volumen - descuento_pronto_pago)",
        "variable1": "IT",
        "variable2": "TPV",
        "variable3": "PVP",
        "area": "Contabilidad",
        "dynamic_calculation": lambda TPV, PVP, dias_credito=0:
            TPV * PVP * 
            (1 - (0.05 if TPV > 3000 else 0.03 if TPV > 2000 else 0)) *  # Descuento volumen
            (1 - (0.02 if dias_credito < 15 else 0))  # Descuento pronto pago
    },
    
    {
        "name": "Gastos Operativos Adaptativos",
        "description": "Gastos que se ajustan al nivel de actividad",
        "expression": "GO = CFD + CTAI + SE_ajustado + costos_variables",
        "variable1": "GO",
        "variable2": "CFD",
        "variable3": "CTAI",
        "variable4": "SE",
        "area": "Contabilidad",
        "dynamic_calculation": lambda CFD, CTAI, SE, TPPRO, dia:
            CFD * factor_estacional_bolivia(dia)['costo'] +  # Costos fijos estacionales
            CTAI +
            SE / 30 * (1 + 0.1 * max(0, TPPRO - 2500) / 2500) +  # Horas extra si produce más
            TPPRO * 0.15  # Otros costos variables (energía, agua, etc)
    },
    
    {
        "name": "Ganancia con Impuestos Progresivos",
        "description": "Utilidad neta después de impuestos variables",
        "expression": "GT = (IT - TG) * (1 - tasa_impuesto_efectiva)",
        "variable1": "GT",
        "variable2": "IT",
        "variable3": "TG",
        "area": "Contabilidad",
        "dynamic_calculation": lambda IT, TG:
            max(0, IT - TG) * (1 - (0.25 if IT - TG > 50000 else 0.15))  # Tasa progresiva
    },
    
    # ECUACIONES DE INVENTARIO Y LOGÍSTICA
    {
        "name": "Inventario con Caducidad y Mermas",
        "description": "Inventario que considera vida útil y pérdidas",
        "expression": "IPF = IPF_anterior + TPPRO - TPV - mermas - caducados",
        "variable1": "IPF",
        "variable2": "TPPRO",
        "variable3": "TPV",
        "area": "Inventario Productos Finales",
        "dynamic_calculation": lambda IPF_anterior, TPPRO, TPV, dias_almacenado, temp_promedio=4:
            max(0, IPF_anterior + TPPRO - TPV - 
                IPF_anterior * 0.002 * dias_almacenado -  # Merma 0.2% diario
                IPF_anterior * (0.1 if dias_almacenado > 5 else 0) *  # 10% caduca después de 5 días
                (1.5 if temp_promedio > 6 else 1.0))  # Factor temperatura
    },
    
    {
        "name": "Costo Almacenamiento Refrigerado",
        "description": "Costo que varía con volumen, tiempo y temperatura",
        "expression": "CA = IPF * costo_dia * factor_ocupacion * factor_energia",
        "variable1": "CA",
        "variable2": "IPF",
        "variable3": "CUI",
        "area": "Inventario Productos Finales",
        "dynamic_calculation": lambda IPF, capacidad_max=15000, tarifa_kwh=0.8, temp_exterior=20:
            IPF * 0.05 *  # Costo base por litro/día
            (1 + max(0, IPF - 10000) / 10000) *  # Sobrecosto por alta ocupación
            (1 + 0.02 * max(0, temp_exterior - 20))  # Mayor costo en días calurosos
    },
    
    {
        "name": "Costo Transporte Optimizado",
        "description": "Logística con rutas optimizadas y combustible variable",
        "expression": "CTTL = distancia * costo_km * factor_carga * factor_combustible",
        "variable1": "CTTL",
        "variable2": "CUTRANS",
        "variable3": "TPV",
        "area": "Distribución",
        "dynamic_calculation": lambda CUTRANS, TPV, distancia_promedio=25, precio_diesel=3.74:
            CUTRANS * TPV * 
            (0.8 + 0.4 * distancia_promedio / 50) *  # Factor distancia
            (0.7 + 0.6 * min(1.0, TPV / 2000)) *  # Mejor eficiencia con carga completa
            (precio_diesel / 3.74)  # Ajuste por precio combustible
    },
    
    # ECUACIONES DE COMPETITIVIDAD Y MERCADO
    {
        "name": "Participación Mercado Dinámica",
        "description": "Cuota que varía con precio, calidad y servicio",
        "expression": "PM = (TPV / mercado_total) * factor_competitividad",
        "variable1": "PM",
        "variable2": "TPV",
        "variable3": "DH",
        "area": "Competencia",
        "dynamic_calculation": lambda TPV, DH, PVP, PC, calidad=0.9, servicio=0.85:
            (TPV / (DH * 50) if DH > 0 else 0) *  # Asumiendo 50 competidores
            (2 - PVP / PC) *  # Mejor participación con precio competitivo
            calidad * servicio  # Factores de diferenciación
    },
    
    {
        "name": "Nivel Competencia Ponderado",
        "description": "Intensidad competitiva del mercado",
        "expression": "NCM = factor_precio * factor_nuevos_entrantes * factor_productos_sustitutos",
        "variable1": "NCM",
        "variable2": "PVP",
        "variable3": "PC",
        "area": "Competencia",
        "dynamic_calculation": lambda PVP, PC, num_competidores=8, dias_mercado=0:
            abs(PVP - PC) / PC *  # Diferencia de precios
            (1 + 0.1 * num_competidores / 10) *  # Más competidores = más intensidad
            (1 + 0.05 * min(1.0, dias_mercado / 365))  # Mercado más maduro = más competencia
    },
    
    # ECUACIONES DE MARKETING Y CLIENTES
    {
        "name": "ROI Marketing Dinámico",
        "description": "Retorno de inversión en marketing variable",
        "expression": "ROI_MKT = (clientes_nuevos * valor_cliente - GMM) / GMM",
        "variable1": "CUAC",
        "variable2": "GMM",
        "variable3": "CPD",
        "area": "Marketing",
        "dynamic_calculation": lambda GMM, CPD, CPD_anterior, VPC, margen=0.25:
            ((max(0, CPD - CPD_anterior) * VPC * 30 * margen - GMM / 30) / 
             (GMM / 30) if GMM > 0 else 0)
    },
    
    {
        "name": "Frecuencia Compra Adaptativa",
        "description": "Frecuencia que varía con satisfacción y promociones",
        "expression": "FC = 1 / (TPC * factor_fidelidad * factor_promocion)",
        "variable1": "FC",
        "variable2": "TPC",
        "area": "Ventas",
        "dynamic_calculation": lambda TPC, satisfaccion=0.9, tiene_promocion=False:
            1 / (TPC * 
                 (2 - satisfaccion) *  # Alta satisfacción = mayor frecuencia
                 (0.8 if tiene_promocion else 1.0))  # Promociones aumentan frecuencia
    },
    
    # ECUACIONES DE RECURSOS HUMANOS
    {
        "name": "Horas Extra Necesarias",
        "description": "Cálculo dinámico de horas extra según demanda",
        "expression": "HE = max(0, (TPPRO_necesaria - CPROD_normal) / productividad_hora)",
        "variable1": "HO",
        "variable2": "TPPRO",
        "variable3": "NEPP",
        "area": "Recursos Humanos",
        "dynamic_calculation": lambda TPPRO_objetivo, CPROD_normal, PE, NEPP:
            max(0, (TPPRO_objetivo - CPROD_normal) / (PE / 8) * NEPP if PE > 0 else 0)
    },
    
    {
        "name": "Costo Mano Obra Variable",
        "description": "Costo que incluye base, extras y bonificaciones",
        "expression": "CMO = SE_base + horas_extra * 1.5 + bonos_productividad",
        "variable1": "SE",
        "variable2": "NEPP",
        "variable3": "PE",
        "area": "Recursos Humanos",
        "dynamic_calculation": lambda SE_base, NEPP, PE, PE_objetivo=180, horas_extra=0:
            SE_base + 
            horas_extra * (SE_base / 160) * 1.5 +  # 50% recargo horas extra
            SE_base * 0.1 * min(1.0, PE / PE_objetivo)  # Hasta 10% bono productividad
    },
    
    # ECUACIÓN MAESTRA - DEMANDA TOTAL SISTEMA
    {
        "name": "Demanda Total Sistema Integrado",
        "description": "Demanda total considerando todos los factores del sistema",
        "expression": "DT = DE * factor_mercado + DI_acumulada + demanda_latente",
        "variable1": "DT",
        "variable2": "DE",
        "variable3": "DI",
        "area": "Ventas",
        "dynamic_calculation": lambda DE, DI, PM, satisfaccion=0.9, dia=0:
            DE * (1 + PM / 100) +  # Demanda base ajustada por participación
            DI * 0.3 +  # 30% de demanda insatisfecha se acumula
            DE * 0.1 * (1 - satisfaccion) *  # Demanda latente por insatisfacción
            (1 + 0.0001 * dia)  # Crecimiento natural del mercado
    }
]

# Función para calcular todas las ecuaciones en orden
def calcular_sistema_ecuaciones(variables_estado, dia, contexto_adicional=None):
    """
    Calcula todas las ecuaciones del sistema en orden de dependencia
    
    Args:
        variables_estado: Dict con valores actuales de variables
        dia: Día de simulación
        contexto_adicional: Parámetros extra del contexto
    
    Returns:
        Dict con valores calculados
    """
    resultados = variables_estado.copy()
    contexto = {**variables_estado, **(contexto_adicional or {}), 'dia': dia}
    
    # Calcular ecuaciones en orden de dependencia
    for ecuacion in equations_data:
        if 'dynamic_calculation' in ecuacion:
            try:
                # Obtener función de cálculo
                calc_func = ecuacion['dynamic_calculation']
                
                # Preparar argumentos
                import inspect
                params = inspect.signature(calc_func).parameters
                args = {k: contexto.get(k, 0) for k in params if k in contexto}
                
                # Calcular y almacenar resultado
                resultado = calc_func(**args)
                variable_resultado = ecuacion['variable1']
                resultados[variable_resultado] = resultado
                contexto[variable_resultado] = resultado
                
            except Exception as e:
                print(f"Error en ecuación {ecuacion['name']}: {e}")
    
    return resultados

# Exportar elementos principales
__all__ = ['equations_data', 'calcular_sistema_ecuaciones', 'factor_estacional_bolivia', 
           'factor_dia_semana', 'factor_volumen_economia_escala']

equations_data = [
    # ECUACIONES DE DEMANDA Y VENTAS
    {
        "name": "Demanda Diaria Proyectada",
        "description": "Proyección de demanda con factores estacionales, tendencia y aleatoriedad",
        "expression": "DE = DH * factor_estacional * factor_dia * (1 + tendencia) * random_factor",
        "variable1": "DE",
        "variable2": "DH",
        "area": "Ventas",
        "dynamic_calculation": lambda DH, dia: 
            DH * factor_estacional_bolivia(dia)['demanda'] * 
            factor_dia_semana(dia) * 
            (1 + 0.0002 * dia) *  # Tendencia crecimiento 0.02% diario
            np.random.normal(1.0, 0.05)  # Variación aleatoria ±5%
    },
    
    {
        "name": "Clientes Atendidos Dinámico",
        "description": "Clientes que varían según día, marketing y satisfacción",
        "expression": "TCAE = CPD * factor_dia * efecto_marketing * satisfaccion",
        "variable1": "TCAE",
        "variable2": "CPD",
        "area": "Ventas",
        "dynamic_calculation": lambda CPD, dia, GMM, satisfaccion=0.9:
            int(CPD * factor_dia_semana(dia) * 
                (1 + GMM / 50000) *  # Efecto marketing
                satisfaccion *
                np.random.normal(1.0, 0.1))
    },
    
    {
        "name": "Ventas Reales con Restricciones",
        "description": "Ventas limitadas por demanda, producción e inventario",
        "expression": "TPV = min(DE, TPPRO + IPF, TCAE * VPC)",
        "variable1": "TPV",
        "variable2": "DE",
        "variable3": "TPPRO",
        "variable4": "IPF",
        "area": "Ventas",
        "dynamic_calculation": lambda DE, TPPRO, IPF, TCAE, VPC:
            min(DE, TPPRO + IPF * 0.8, TCAE * VPC)  # 80% del inventario disponible
    },
    
    {
        "name": "Demanda Insatisfecha con Costo Oportunidad",
        "description": "Ventas perdidas y su impacto económico",
        "expression": "DI = max(0, DE - TPV) * (1 + factor_insatisfaccion)",
        "variable1": "DI",
        "variable2": "DE",
        "variable3": "TPV",
        "area": "Ventas",
        "dynamic_calculation": lambda DE, TPV, dias_consecutivos_faltante=0:
            max(0, DE - TPV) * (1 + 0.1 * dias_consecutivos_faltante)  # Penalización acumulativa
    },
    
    # ECUACIONES DE PRODUCCIÓN
    {
        "name": "Producción Adaptativa a Demanda",
        "description": "Producción que se ajusta a demanda proyectada y nivel de inventario",
        "expression": "TPPRO = min(CPROD * FU, DE * factor_seguridad - IPF * factor_inventario)",
        "variable1": "TPPRO",
        "variable2": "CPROD",
        "variable3": "DE",
        "variable4": "IPF",
        "area": "Producción",
        "dynamic_calculation": lambda CPROD, DE, IPF, FU=0.85:
            min(CPROD * FU,  # Capacidad efectiva
                max(0, DE * 1.1 - IPF * 0.2))  # Producir 110% demanda menos 20% inventario
    },
    
    {
        "name": "Factor Utilización Dinámico",
        "description": "Utilización que varía con eficiencia y mantenimiento",
        "expression": "FU = base_efficiency * factor_mantenimiento * factor_experiencia",
        "variable1": "FU",
        "variable2": "TPPRO",
        "variable3": "CPROD",
        "area": "Producción",
        "dynamic_calculation" : lambda base_efficiency, factor_mantenimiento, factor_experiencia=1.0:
            base_efficiency * factor_mantenimiento * factor_experiencia
    },
    
    {
        "name": "Capacidad de Producción Efectiva",
        "description": "Capacidad que se ajusta por mantenimiento y eficiencia",
        "expression": "CPROD = CPROD_base * factor_mantenimiento * factor_eficiencia",
        "variable1": "CPROD",
        "variable2": "CPROD_base",
        "area": "Producción",
        "dynamic_calculation": lambda CPROD_base, factor_mantenimiento, factor_eficiencia=1.0:
            CPROD_base * factor_mantenimiento * factor_eficiencia
    },  
    {
        "name": "Tiempo de Producción Necesario",
        "description": "Tiempo requerido para cumplir con la producción proyectada",
        "expression": "TPPRO_necesaria = TPPRO / NEPP",
        "variable1": "TPPRO_necesaria",
        "variable2": "TPPRO",
        "variable3": "NEPP",
        "area": "Producción",
        "dynamic_calculation": lambda TPPRO, NEPP:
            TPPRO / NEPP if NEPP > 0 else 0
    },
    {
        "name": "Eficiencia de Producción",
        "description": "Eficiencia que varía con experiencia y mantenimiento",
        "expression": "EP = (TPPRO / CPROD) * factor_experiencia * factor_mantenimiento",
        "variable1": "EP",
        "variable2": "TPPRO",
        "variable3": "CPROD",
        "area": "Producción",
        "dynamic_calculation": lambda TPPRO, CPROD, factor_experiencia=1.0, factor_mantenimiento=1.0:
            (TPPRO / CPROD if CPROD > 0 else 0) * factor_experiencia * factor_mantenimiento
    },
    # ECUACIONES DE CALIDAD Y MEJORA CONTINUA
    {
        "name": "Índice de Calidad con Mejora Continua",
        "description": "Calidad que mejora con experiencia y reducción de defectos",
        "expression": "IQ = base_quality * (1 + 0.1 * experiencia - 0.05 * defectos)",
        "variable1": "IQ",
        "variable2": "base_quality",
        "variable3": "experiencia",
        "area": "Calidad",
        "dynamic_calculation": lambda base_quality, experiencia, defectos=0:
            base_quality * (1 + 0.1 * experiencia - 0.05 * defectos)
    },
    
    {
        "name": "Tasa de Defectos Ajustada",
        "description": "Defectos que se reducen con mejoras y capacitación",
        "expression": "TD = TD_base * (1 - 0.02 * capacitacion)",
        "variable1": "TD",
        "variable2": "TD_base",
        "variable3": "capacitacion",
        "area": "Calidad",
        "dynamic_calculation": lambda TD_base, capacitacion=0:
            TD_base * (1 - 0.02 * capacitacion)
    }
]

# Función para crear una ecuación a partir de datos
def crear_ecuacion(name, description, expression, variables, area, calc_func):
  """
  Crea una nueva ecuación en el formato estándar
  
  Args:
    name: Nombre de la ecuación
    description: Descripción detallada
    expression: Expresión matemática como string
    variables: Lista de nombres de variables
    area: Área funcional
    calc_func: Función lambda para cálculo dinámico
  
  Returns:
    Dict con la ecuación formateada
  """
  ecuacion = {
    "name": name,
    "description": description, 
    "expression": expression,
    "area": area,
    "dynamic_calculation": calc_func
  }
  
  # Agregar variables numeradas
  for i, var in enumerate(variables, 1):
    ecuacion[f"variable{i}"] = var
    
  return ecuacion
        