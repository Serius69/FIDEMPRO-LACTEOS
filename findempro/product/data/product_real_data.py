# products_data.py - Versión Optimizada con Comportamiento Dinámico por Demanda
import numpy as np
from datetime import datetime, timedelta

# Funciones para comportamiento dinámico de productos
def calcular_costo_produccion_dinamico(base, volumen, dia):
    """Costo de producción que varía con volumen y tiempo"""
    # Economías de escala
    factor_volumen = 1.0
    if volumen > 1000:
        factor_volumen = 0.95  # 5% descuento por volumen
    elif volumen > 2000:
        factor_volumen = 0.92  # 8% descuento
    elif volumen > 3000:
        factor_volumen = 0.90  # 10% descuento
    
    # Inflación gradual
    factor_inflacion = 1 + (0.00015 * dia)  # 0.015% diario = 5.5% anual
    
    # Variación estacional en costos de insumos
    dia_año = dia % 365
    factor_estacional = 1.0
    if 152 <= dia_año <= 243:  # Invierno
        factor_estacional = 1.05  # Insumos más caros en invierno
    elif 335 <= dia_año or dia_año <= 59:  # Verano
        factor_estacional = 0.98  # Ligeramente más baratos en verano
    
    return base * factor_volumen * factor_inflacion * factor_estacional

def calcular_precio_venta_dinamico(base, demanda, demanda_promedio, competencia, dia):
    """Precio que responde a demanda, competencia y temporada"""
    # Elasticidad precio-demanda
    elasticidad = -0.5  # Productos lácteos son relativamente inelásticos
    factor_demanda = 1 + elasticidad * (demanda - demanda_promedio) / demanda_promedio
    
    # Respuesta a competencia
    factor_competencia = 1.0
    if competencia < base * 0.95:  # Competencia agresiva
        factor_competencia = 0.97  # Bajar precio ligeramente
    elif competencia > base * 1.05:  # Competencia cara
        factor_competencia = 1.02  # Subir precio moderadamente
    
    # Factor día de semana (viernes-domingo más caro)
    dia_semana = dia % 7
    factor_dia = 1.0
    if dia_semana >= 4:  # Viernes a domingo
        factor_dia = 1.03
    
    return base * factor_demanda * factor_competencia * factor_dia

def calcular_margen_dinamico(precio_venta, costo_produccion, volumen):
    """Margen de ganancia que varía con volumen y eficiencia"""
    margen_base = ((precio_venta - costo_produccion) / precio_venta) * 100
    
    # Bonus por volumen alto
    if volumen > 2000:
        margen_base += 2  # +2% margen adicional
    
    return max(0, min(60, margen_base))  # Entre 0% y 60%

def calcular_desperdicio_dinamico(produccion, ventas, dias_inventario, tipo_producto):
    """Desperdicio basado en vida útil y manejo de inventario"""
    desperdicio_base = max(0, produccion - ventas)
    
    # Factor por días en inventario
    factor_caducidad = 0.0
    vidas_utiles = {
        'Leche': 5,
        'Yogur': 21,
        'Queso': 15,
        'Mantequilla': 60,
        'Crema de Leche': 10,
        'Leche Deslactosada': 7,
        'Dulce de Leche': 180
    }
    
    vida_util = vidas_utiles.get(tipo_producto, 7)
    if dias_inventario > vida_util:
        factor_caducidad = 0.9  # 90% se pierde
    elif dias_inventario > vida_util * 0.8:
        factor_caducidad = 0.3  # 30% se pierde
    elif dias_inventario > vida_util * 0.6:
        factor_caducidad = 0.1  # 10% se pierde
    
    return desperdicio_base * factor_caducidad

# Datos de productos lácteos bolivianos con comportamiento dinámico
products_data = [
    {
        'name': 'Leche',
        'description': '''Leche entera pasteurizada, producto estrella del sector lácteo boliviano.
        Alta rotación y demanda constante pero con marcada estacionalidad.
        Mayor consumo en época escolar (marzo-noviembre) y menor en vacaciones.
        Producto sensible al precio con competencia intensa entre marcas locales.''',
        'type': 1,  # Producto lácteo
        'unit': 'litros',
        'profit_margin': 25.0,  # Margen base
        'production_cost': 5.50,  # Costo base por litro
        'selling_price': 7.00,  # Precio base
        'min_stock': 500,
        'max_stock': 5000,
        'shelf_life_days': 5,
        'production_time_hours': 2,
        'quality_parameters': {
            'fat_content': 3.5,
            'protein': 3.2,
            'lactose': 4.8,
            'ph_range': [6.6, 6.8],
            'temperature_storage': 4
        },
        # Parámetros dinámicos
        'dynamic_parameters': {
            'base_demand': 2500,  # Litros/día
            'demand_volatility': 0.15,  # 15% variación
            'seasonal_factor': {
                'school': 1.2,  # +20% en época escolar
                'vacation': 0.8,  # -20% en vacaciones
                'winter': 1.15,  # +15% en invierno
                'summer': 0.85   # -15% en verano
            },
            'price_elasticity': -0.8,  # Relativamente elástica
            'competition_response': 0.7,  # Responde rápido a competencia
            'production_efficiency': lambda dia: min(0.95, 0.85 + 0.001 * dia),  # Mejora con el tiempo
            'waste_factors': {
                'handling': 0.02,  # 2% pérdida por manejo
                'expiration': 0.05,  # 5% por caducidad
                'temperature': 0.03  # 3% por cadena de frío
            }
        },
        # Ecuaciones específicas del producto
        'dynamic_equations': {
            'daily_demand': lambda base, dia: 
                base * (1.2 if 60 <= dia % 365 <= 300 else 0.8) *  # Época escolar
                (1.15 if 152 <= dia % 365 <= 243 else 0.85 if dia % 365 >= 335 or dia % 365 <= 59 else 1.0) *  # Estacional
                np.random.normal(1.0, 0.15),  # Variación diaria
            
            'production_cost': lambda base, volumen, dia:
                calcular_costo_produccion_dinamico(base, volumen, dia),
            
            'selling_price': lambda base, demanda, demanda_prom, precio_comp, dia:
                calcular_precio_venta_dinamico(base, demanda, demanda_prom, precio_comp, dia),
            
            'daily_production': lambda capacidad, demanda, inventario:
                min(capacidad, max(0, demanda * 1.1 - inventario * 0.2)),  # Produce 110% demanda menos 20% inventario
            
            'waste': lambda produccion, ventas, dias_inv:
                calcular_desperdicio_dinamico(produccion, ventas, dias_inv, 'Leche')
        }
    },
    
    {
        'name': 'Yogur',
        'description': '''Yogur natural y saborizado, producto de valor agregado con crecimiento sostenido.
        Demanda influenciada por tendencias de salud y bienestar.
        Mayor consumo en ciudades principales (La Paz, Santa Cruz, Cochabamba).
        Oportunidad de diferenciación con sabores locales (maracuyá, tumbo, achachairú).''',
        'type': 1,
        'unit': 'litros',
        'profit_margin': 35.0,
        'production_cost': 8.00,
        'selling_price': 12.00,
        'min_stock': 300,
        'max_stock': 2000,
        'shelf_life_days': 21,
        'production_time_hours': 8,  # Incluye fermentación
        'quality_parameters': {
            'fat_content': 3.0,
            'protein': 4.0,
            'ph_range': [4.0, 4.6],
            'live_cultures_cfu': 1e8,
            'temperature_storage': 4
        },
        'dynamic_parameters': {
            'base_demand': 800,
            'demand_volatility': 0.20,
            'seasonal_factor': {
                'summer': 1.3,  # Mayor consumo en verano
                'winter': 0.9,
                'health_campaigns': 1.25  # Picos por campañas de salud
            },
            'price_elasticity': -0.6,
            'market_growth': 0.0003,  # 0.03% crecimiento diario = 11% anual
            'target_market': {
                'health_conscious': 0.4,
                'families': 0.35,
                'young_adults': 0.25
            }
        },
        'dynamic_equations': {
            'daily_demand': lambda base, dia:
                base * (1 + 0.0003 * dia) *  # Crecimiento tendencial
                (1.3 if dia % 365 >= 335 or dia % 365 <= 59 else 0.9 if 152 <= dia % 365 <= 243 else 1.0) *
                (1.25 if dia % 30 == 15 else 1.0) *  # Pico quincenal (campañas)
                np.random.normal(1.0, 0.20),
            
            'production_cost': lambda base, volumen, dia:
                base * (1 + 0.0002 * dia) *  # Inflación
                (0.92 if volumen > 500 else 1.0),  # Economía de escala
            
            'profit_margin': lambda precio, costo, volumen:
                calcular_margen_dinamico(precio, costo, volumen) + 5,  # +5% por valor agregado
            
            'innovation_factor': lambda dia:
                1 + 0.1 * (1 if dia % 90 == 0 else 0)  # Nuevo sabor cada 3 meses
        }
    },
    
    {
        'name': 'Queso',
        'description': '''Queso fresco y madurado, producto tradicional con alto valor.
        Fuerte demanda en mercados locales y restaurantes.
        Producción artesanal compite con industrial.
        Oportunidades en quesos especiales (cabra, condimentados).''',
        'type': 1,
        'unit': 'kilogramos',
        'profit_margin': 40.0,
        'production_cost': 35.00,
        'selling_price': 55.00,
        'min_stock': 50,
        'max_stock': 500,
        'shelf_life_days': 15,
        'production_time_hours': 4,
        'quality_parameters': {
            'fat_content': 20.0,
            'protein': 18.0,
            'moisture': 55.0,
            'salt_content': 1.5,
            'ph_range': [5.2, 5.6],
            'temperature_storage': 4
        },
        'dynamic_parameters': {
            'base_demand': 350,
            'demand_volatility': 0.25,
            'seasonal_factor': {
                'holidays': 1.5,  # Fiestas patrias, navidad
                'lent': 0.7,      # Cuaresma
                'winter': 1.2     # Más consumo en invierno
            },
            'b2b_percentage': 0.6,  # 60% ventas a restaurantes
            'artisanal_premium': 1.15  # 15% más por artesanal
        },
        'dynamic_equations': {
            'daily_demand': lambda base, dia:
                base * 
                (1.5 if dia % 365 in [195, 359, 360] else 1.0) *  # Fiestas específicas
                (0.7 if 40 <= dia % 365 <= 85 else 1.0) *  # Cuaresma
                (1.2 if 152 <= dia % 365 <= 243 else 1.0) *
                np.random.normal(1.0, 0.25),
            
            'b2b_demand': lambda total_demand, dia_semana:
                total_demand * 0.6 * (1.3 if dia_semana in [4, 5, 6] else 0.9),  # Más en fin de semana
            
            'production_cost': lambda base, tipo_leche, volumen, dia:
                base * (1.2 if tipo_leche == 'cabra' else 1.0) *
                (0.9 if volumen > 200 else 1.0) *
                (1 + 0.00018 * dia),  # Inflación
            
            'maturation_bonus': lambda dias_madurado:
                1 + min(0.5, dias_madurado * 0.05)  # Hasta 50% más por maduración
        }
    },
    
    {
        'name': 'Mantequilla',
        'description': '''Mantequilla de primera calidad, demanda estable con picos estacionales.
        Mayor consumo en panaderías y repostería.
        Competencia con mantequilla importada (Argentina).
        Potencial en mantequilla saborizada y clarificada.''',
        'type': 1,
        'unit': 'kilogramos',
        'profit_margin': 45.0,
        'production_cost': 45.00,
        'selling_price': 70.00,
        'min_stock': 30,
        'max_stock': 300,
        'shelf_life_days': 60,
        'production_time_hours': 3,
        'quality_parameters': {
            'fat_content': 82.0,
            'moisture_max': 16.0,
            'salt_content': 2.0,
            'ph_range': [6.1, 6.4],
            'temperature_storage': 4
        },
        'dynamic_parameters': {
            'base_demand': 150,
            'demand_volatility': 0.18,
            'seasonal_factor': {
                'baking_season': 1.4,  # Julio-Diciembre
                'carnival': 1.6,       # Carnaval
                'regular': 0.9
            },
            'b2b_bakery': 0.7,  # 70% a panaderías
            'import_competition': 0.15  # 15% del mercado es importado
        },
        'dynamic_equations': {
            'daily_demand': lambda base, dia:
                base * 
                (1.4 if 180 <= dia % 365 <= 365 else 0.9) *  # Temporada horneo
                (1.6 if 35 <= dia % 365 <= 42 else 1.0) *    # Carnaval
                np.random.normal(1.0, 0.18),
            
            'bakery_demand': lambda total, dia_semana:
                total * 0.7 * (1.2 if dia_semana in [0, 1, 2] else 0.85),  # Lun-Mié preparación
            
            'price_competition': lambda precio_local, precio_importado:
                precio_local * (0.95 if precio_importado < precio_local * 0.9 else 1.0),
            
            'production_efficiency': lambda volumen_crema, rendimiento_base=0.4:
                volumen_crema * rendimiento_base * (1.05 if volumen_crema > 500 else 1.0)
        }
    },
    
    {
        'name': 'Crema de Leche',
        'description': '''Crema para uso culinario y repostería, demanda creciente.
        Producto versátil con múltiples aplicaciones.
        Mayor consumo en sector HORECA (hoteles, restaurantes, cafeterías).
        Oportunidad en presentaciones UHT para mayor duración.''',
        'type': 1,
        'unit': 'litros',
        'profit_margin': 38.0,
        'production_cost': 12.00,
        'selling_price': 18.00,
        'min_stock': 100,
        'max_stock': 800,
        'shelf_life_days': 10,
        'production_time_hours': 1.5,
        'quality_parameters': {
            'fat_content': 30.0,
            'protein': 2.5,
            'ph_range': [6.4, 6.7],
            'viscosity': 'alta',
            'temperature_storage': 4
        },
        'dynamic_parameters': {
            'base_demand': 300,
            'demand_volatility': 0.22,
            'horeca_percentage': 0.65,
            'retail_percentage': 0.35,
            'uht_premium': 1.25,
            'seasonal_peaks': {
                'holidays': 1.45,
                'regular': 0.95
            }
        },
        'dynamic_equations': {
            'daily_demand': lambda base, dia:
                base * 
                (1.45 if dia % 365 in range(350, 366) or dia % 365 in range(0, 10) else 0.95) *
                (1 + 0.0004 * dia) *  # Crecimiento 0.04% diario
                np.random.normal(1.0, 0.22),
            
            'horeca_demand': lambda total, dia_semana:
                total * 0.65 * (1.4 if dia_semana >= 4 else 0.8),  # Pico fin de semana
            
            'uht_production': lambda demanda_total, vida_util_requerida:
                demanda_total * 0.3 if vida_util_requerida > 30 else 0,  # 30% UHT si necesitan duración
            
            'separation_efficiency': lambda volumen_leche:
                volumen_leche * 0.1 * (1.08 if volumen_leche > 3000 else 1.0)  # 10% rendimiento
        }
    },
    
    {
        'name': 'Leche Deslactosada',
        'description': '''Producto especializado con demanda creciente por intolerancia a lactosa.
        Mayor precio y margen que leche regular.
        Mercado en expansión con poca competencia local.
        Requiere tecnología enzimática (lactasa).''',
        'type': 1,
        'unit': 'litros',
        'profit_margin': 50.0,
        'production_cost': 7.50,
        'selling_price': 12.00,
        'min_stock': 200,
        'max_stock': 1500,
        'shelf_life_days': 7,
        'production_time_hours': 3,
        'quality_parameters': {
            'lactose_content': 0.1,
            'fat_content': 3.5,
            'protein': 3.2,
            'enzyme_activity': 'completa',
            'temperature_storage': 4
        },
        'dynamic_parameters': {
            'base_demand': 400,
            'demand_volatility': 0.15,
            'market_growth': 0.0005,  # 0.05% diario = 18% anual
            'intolerant_population': 0.15,  # 15% población
            'awareness_factor': 0.6,  # 60% conoce el producto
            'enzyme_cost': 1.5  # Bs/litro adicional
        },
        'dynamic_equations': {
            'daily_demand': lambda base, dia:
                base * (1 + 0.0005 * dia) *  # Crecimiento acelerado
                (1 + 0.1 * min(1, dia / 365)) *  # Mayor conocimiento con tiempo
                np.random.normal(1.0, 0.15),
            
            'production_cost': lambda base, volumen_enzima, dia:
                (base + 1.5) * (0.95 if volumen_enzima > 1000 else 1.0) *  # Descuento volumen enzima
                (1 + 0.00012 * dia),  # Inflación
            
            'market_penetration': lambda poblacion_objetivo, awareness, precio_ratio:
                poblacion_objetivo * awareness * (2 - precio_ratio),  # Sensible al precio
            
            'conversion_efficiency': lambda lactasa_calidad:
                0.98 if lactasa_calidad == 'premium' else 0.95  # 95-98% conversión
        }
    },
    
    {
        'name': 'Dulce de Leche',
        'description': '''Producto tradicional boliviano con demanda estable.
        Alto margen y larga vida útil.
        Consumo en repostería y directo.
        Potencial exportación a países vecinos.
        Competencia con dulce argentino.''',
        'type': 1,
        'unit': 'kilogramos',
        'profit_margin': 55.0,
        'production_cost': 20.00,
        'selling_price': 40.00,
        'min_stock': 50,
        'max_stock': 400,
        'shelf_life_days': 180,
        'production_time_hours': 5,
        'quality_parameters': {
            'sugar_content': 55.0,
            'moisture': 30.0,
            'fat_content': 6.0,
            'color': 'caramelo',
            'temperature_storage': 20  # Temperatura ambiente
        },
        'dynamic_parameters': {
            'base_demand': 200,
            'demand_volatility': 0.12,
            'export_percentage': 0.25,
            'seasonal_factor': {
                'school': 1.3,
                'holidays': 1.4,
                'regular': 0.85
            },
            'sugar_price_impact': 0.4  # 40% del costo es azúcar
        },
        'dynamic_equations': {
            'daily_demand': lambda base, dia:
                base * 
                (1.3 if 60 <= dia % 365 <= 300 else 0.85) *  # Época escolar
                (1.4 if dia % 365 in [195, 359, 360] else 1.0) *  # Fiestas
                np.random.normal(1.0, 0.12),
            
            'export_demand': lambda total, tipo_cambio, precio_competencia:
                total * 0.25 * (tipo_cambio / 6.96) * (precio_competencia / 40),  # Sensible a tipo cambio
            
            'production_cost': lambda base, precio_azucar, volumen, dia:
                (base * 0.6 + precio_azucar * 0.4) *  # 40% costo es azúcar
                (0.93 if volumen > 300 else 1.0) *    # Economía escala
                (1 + 0.0001 * dia),  # Inflación
            
            'caramelization_yield': lambda temperatura, tiempo_coccion:
                0.5 * (1 + 0.1 * min(0, 120 - temperatura))  # 50% rendimiento óptimo a 120°C
        }
    }
]

# Función para simular comportamiento de producto durante N días
def simular_producto(nombre_producto, dias=30, contexto_inicial=None):
    """
    Simula el comportamiento dinámico de un producto durante N días
    
    Args:
        nombre_producto: Nombre del producto a simular
        dias: Número de días a simular
        contexto_inicial: Condiciones iniciales (inventario, precios, etc)
    
    Returns:
        Lista con resultados diarios
    """
    producto = next((p for p in products_data if p['name'] == nombre_producto), None)
    if not producto:
        return None
    
    resultados = []
    contexto = contexto_inicial or {
        'inventario': producto['min_stock'],
        'precio_competencia': producto['selling_price'] * 1.02,
        'dias_inventario': 0,
        'ventas_acumuladas': 0,
        'ganancias_acumuladas': 0
    }
    
    for dia in range(dias):
        resultado_dia = {
            'dia': dia + 1,
            'fecha': datetime.now() + timedelta(days=dia)
        }
        
        # Calcular demanda del día
        ecuaciones = producto['dynamic_equations']
        if 'daily_demand' in ecuaciones:
            base_demand = producto['dynamic_parameters']['base_demand']
            resultado_dia['demanda'] = ecuaciones['daily_demand'](base_demand, dia)
        
        # Calcular producción necesaria
        if 'daily_production' in ecuaciones:
            capacidad = producto['max_stock'] / 2  # Capacidad diaria aprox
            resultado_dia['produccion'] = ecuaciones['daily_production'](
                capacidad, 
                resultado_dia['demanda'], 
                contexto['inventario']
            )
        
        # Calcular costos
        if 'production_cost' in ecuaciones:
            resultado_dia['costo_unitario'] = ecuaciones['production_cost'](
                producto['production_cost'],
                resultado_dia.get('produccion', 0),
                dia
            )
        
        # Calcular precio de venta
        if 'selling_price' in ecuaciones:
            resultado_dia['precio_venta'] = ecuaciones['selling_price'](
                producto['selling_price'],
                resultado_dia['demanda'],
                base_demand,
                contexto['precio_competencia'],
                dia
            )
        
        # Calcular ventas reales (limitadas por inventario + producción)
        disponible = contexto['inventario'] + resultado_dia.get('produccion', 0)
        resultado_dia['ventas'] = min(resultado_dia['demanda'], disponible)
        
        # Calcular desperdicio
        if 'waste' in ecuaciones:
            resultado_dia['desperdicio'] = ecuaciones['waste'](
                resultado_dia.get('produccion', 0),
                resultado_dia['ventas'],
                contexto['dias_inventario']
            )
        
        # Actualizar inventario
        contexto['inventario'] = disponible - resultado_dia['ventas'] - resultado_dia.get('desperdicio', 0)
        contexto['dias_inventario'] = 1 if contexto['inventario'] > 0 else 0
        
        # Calcular métricas financieras
        resultado_dia['ingresos'] = resultado_dia['ventas'] * resultado_dia.get('precio_venta', producto['selling_price'])
        resultado_dia['costos'] = resultado_dia.get('produccion', 0) * resultado_dia.get('costo_unitario', producto['production_cost'])
        resultado_dia['ganancia'] = resultado_dia['ingresos'] - resultado_dia['costos']
        resultado_dia['margen'] = (resultado_dia['ganancia'] / resultado_dia['ingresos'] * 100) if resultado_dia['ingresos'] > 0 else 0
        
        # Actualizar acumulados
        contexto['ventas_acumuladas'] += resultado_dia['ventas']
        contexto['ganancias_acumuladas'] += resultado_dia['ganancia']
        
        resultados.append(resultado_dia)
    
    return resultados

# Función para obtener parámetros óptimos de un producto
def obtener_parametros_optimos(nombre_producto, condiciones_mercado):
    """
    Calcula parámetros óptimos de operación para un producto
    
    Args:
        nombre_producto: Nombre del producto
        condiciones_mercado: Dict con condiciones actuales del mercado
    
    Returns:
        Dict con parámetros optimizados
    """
    producto = next((p for p in products_data if p['name'] == nombre_producto), None)
    if not producto:
        return None
    
    # Análisis de punto de equilibrio
    costo_fijo_diario = condiciones_mercado.get('costo_fijo_diario', 1000)
    costo_variable = producto['production_cost']
    precio_venta = producto['selling_price']
    
    punto_equilibrio = costo_fijo_diario / (precio_venta - costo_variable)
    
    # Producción óptima considerando demanda esperada
    demanda_esperada = producto['dynamic_parameters']['base_demand']
    factor_seguridad = 1.1  # 10% adicional
    produccion_optima = demanda_esperada * factor_seguridad
    
    # Inventario óptimo (días de cobertura)
    dias_cobertura = min(3, producto['shelf_life_days'] * 0.4)  # Máximo 40% de vida útil
    inventario_optimo = demanda_esperada * dias_cobertura
    
    # Precio óptimo considerando elasticidad
    elasticidad = producto['dynamic_parameters'].get('price_elasticity', -0.5)
    margen_deseado = 0.25  # 25% margen mínimo
    precio_optimo = costo_variable * (1 + margen_deseado) / (1 + elasticidad)
    
    return {
        'punto_equilibrio': punto_equilibrio,
        'produccion_optima': produccion_optima,
        'inventario_optimo': inventario_optimo,
        'precio_optimo': precio_optimo,
        'dias_cobertura': dias_cobertura,
        'margen_esperado': (precio_optimo - costo_variable) / precio_optimo * 100
    }

# Categorías dinámicas de productos
product_categories = {
    'alta_rotacion': ['Leche', 'Yogur'],  # Vida útil corta, demanda alta
    'valor_agregado': ['Yogur', 'Queso', 'Leche Deslactosada'],  # Mayor margen
    'larga_duracion': ['Dulce de Leche', 'Mantequilla'],  # Vida útil > 30 días
    'estacionales': ['Mantequilla', 'Dulce de Leche'],  # Demanda variable por temporada
    'crecimiento': ['Leche Deslactosada', 'Yogur'],  # Mercados en expansión
    'tradicionales': ['Queso', 'Dulce de Leche'],  # Productos arraigados
    'b2b_focus': ['Mantequilla', 'Crema de Leche', 'Queso'],  # Ventas a negocios
    'b2c_focus': ['Leche', 'Yogur', 'Leche Deslactosada']  # Ventas al consumidor
}

# Métricas de rendimiento por producto (se actualizan dinámicamente)
product_metrics = {
    'Leche': {
        'market_share': lambda ventas, mercado_total: ventas / mercado_total * 100,
        'growth_rate': lambda ventas_actual, ventas_anterior: (ventas_actual - ventas_anterior) / ventas_anterior * 100,
        'customer_satisfaction': lambda demanda_satisfecha, demanda_total: demanda_satisfecha / demanda_total,
        'production_efficiency': lambda produccion, capacidad: produccion / capacidad
    },
    'Yogur': {
        'innovation_index': lambda nuevos_sabores, total_sabores: nuevos_sabores / total_sabores,
        'health_perception': lambda sin_azucar, total: sin_azucar / total,
        'premium_ratio': lambda ventas_premium, ventas_total: ventas_premium / ventas_total,
        'repeat_purchase': lambda clientes_recurrentes, clientes_total: clientes_recurrentes / clientes_total
    },
    'Queso': {
        'artisanal_premium': lambda precio_artesanal, precio_industrial: precio_artesanal / precio_industrial - 1,
        'maturation_value': lambda precio_madurado, precio_fresco: precio_madurado / precio_fresco,
        'restaurant_penetration': lambda restaurantes_cliente, restaurantes_total: restaurantes_cliente / restaurantes_total,
        'quality_score': lambda parametros_cumplidos, parametros_total: parametros_cumplidos / parametros_total
    }
}

# Exportar funciones y datos
__all__ = ['products_data', 'product_categories', 'product_metrics', 
           'simular_producto', 'obtener_parametros_optimos',
           'calcular_costo_produccion_dinamico', 'calcular_precio_venta_dinamico',
           'calcular_margen_dinamico', 'calcular_desperdicio_dinamico']