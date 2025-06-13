"""
Configuración de productos lácteos para el sistema FindEMPro.
Define los productos disponibles con sus características y parámetros iniciales.
"""

products_data = [
    {
        'name': 'Leche',
        'description': '''La leche entera es un producto lácteo fundamental con alto valor nutricional. 
        Contiene 3.5% de grasa, proteínas de alta calidad, vitaminas A, D, B12, calcio y otros minerales esenciales. 
        Es la base para la elaboración de otros productos lácteos y tiene alta demanda en el mercado boliviano.
        Ideal para consumo directo y como materia prima para derivados lácteos.''',
        'type': 1,  # Producto lácteo
        'unit': 'litros',
        'profit_margin': 25.0,  # Margen de ganancia típico
        'production_cost': 5.50,  # Costo por litro en Bs
        'selling_price': 7.00,  # Precio de venta por litro
        'min_stock': 500,  # Stock mínimo recomendado
        'max_stock': 5000,  # Capacidad máxima de almacenamiento
        'shelf_life_days': 5,  # Vida útil en días
        'production_time_hours': 2,  # Tiempo de procesamiento
        'quality_parameters': {
            'fat_content': 3.5,
            'protein': 3.2,
            'lactose': 4.8,
            'ph_range': [6.6, 6.8],
            'temperature_storage': 4  # °C
        }
    },
    {
        'name': 'Yogur',
        'description': '''El yogurt natural es un producto lácteo fermentado con cultivos probióticos vivos. 
        Rico en proteínas, calcio y bacterias beneficiosas para la salud digestiva. 
        Proceso de fermentación controlada que transforma la lactosa en ácido láctico.
        Versátil para consumo directo o como base para yogures saborizados.
        Alta demanda en el mercado de productos saludables.''',
        'type': 1,  # Producto lácteo
        'unit': 'litros',
        'profit_margin': 35.0,  # Mayor margen por valor agregado
        'production_cost': 8.00,  # Costo por litro
        'selling_price': 12.00,  # Precio de venta por litro
        'min_stock': 300,
        'max_stock': 2000,
        'shelf_life_days': 21,  # Mayor vida útil
        'production_time_hours': 8,  # Incluye fermentación
        'quality_parameters': {
            'fat_content': 3.0,
            'protein': 4.0,
            'ph_range': [4.0, 4.6],
            'live_cultures_cfu': 1e8,  # UFC por gramo
            'temperature_storage': 4
        }
    },
    {
        'name': 'Queso',
        'description': '''Queso fresco tradicional, no madurado, de pasta blanda y alto contenido de humedad.
        Elaborado mediante coagulación enzimática de la leche y posterior desuerado.
        Popular en la gastronomía boliviana para consumo directo y preparaciones culinarias.
        Requiere cadena de frío continua y tiene rotación rápida.
        Excelente margen de rentabilidad por su valor agregado.''',
        'type': 1,  # Producto lácteo
        'unit': 'kilogramos',
        'profit_margin': 40.0,  # Alto margen
        'production_cost': 35.00,  # Costo por kg
        'selling_price': 55.00,  # Precio de venta por kg
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
        }
    },
    {
        'name': 'Mantequilla',
        'description': '''Mantequilla de primera calidad elaborada a partir de crema de leche pasteurizada.
        Producto de alto valor con 82% de contenido graso mínimo.
        Proceso incluye separación de crema, maduración, batido y amasado.
        Demanda estable en panaderías, restaurantes y consumo doméstico.
        Excelente vida útil cuando se mantiene refrigerada.''',
        'type': 1,  # Producto lácteo
        'unit': 'kilogramos',
        'profit_margin': 45.0,
        'production_cost': 45.00,
        'selling_price': 70.00,
        'min_stock': 30,
        'max_stock': 300,
        'shelf_life_days': 60,  # Refrigerada
        'production_time_hours': 3,
        'quality_parameters': {
            'fat_content': 82.0,
            'moisture_max': 16.0,
            'salt_content': 2.0,  # Para mantequilla con sal
            'ph_range': [6.1, 6.4],
            'temperature_storage': 4
        }
    },
    {
        'name': 'Crema de Leche',
        'description': '''Crema de leche con 30% de contenido graso, ideal para uso culinario y repostería.
        Obtenida por separación centrífuga de leche entera pasteurizada.
        Producto versátil con múltiples aplicaciones en gastronomía.
        Base para elaboración de mantequilla y otros derivados.
        Demanda constante en el sector de servicios alimenticios.''',
        'type': 1,  # Producto lácteo
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
        }
    },
    {
        'name': 'Leche Deslactosada',
        'description': '''Leche especial tratada con enzima lactasa para descomponer la lactosa.
        Dirigida a personas con intolerancia a la lactosa, mercado en crecimiento.
        Mantiene todas las propiedades nutricionales de la leche regular.
        Mayor precio de venta por ser producto especializado.
        Requiere proceso adicional pero genera mayor margen de ganancia.''',
        'type': 1,  # Producto lácteo
        'unit': 'litros',
        'profit_margin': 50.0,  # Producto premium
        'production_cost': 7.50,
        'selling_price': 12.00,
        'min_stock': 200,
        'max_stock': 1500,
        'shelf_life_days': 7,
        'production_time_hours': 3,
        'quality_parameters': {
            'lactose_content': 0.1,  # Menos del 0.1%
            'fat_content': 3.5,
            'protein': 3.2,
            'enzyme_activity': 'completa',
            'temperature_storage': 4
        }
    },
    {
        'name': 'Dulce de Leche',
        'description': '''Dulce de leche artesanal elaborado por concentración de leche con azúcar.
        Producto tradicional con alta demanda en repostería y consumo directo.
        Proceso de cocción lenta que carameliza los azúcares naturales.
        Excelente vida útil y alto margen de rentabilidad.
        Potencial de exportación y diversificación en presentaciones.''',
        'type': 1,  # Producto lácteo
        'unit': 'kilogramos',
        'profit_margin': 55.0,  # Muy alto margen
        'production_cost': 20.00,
        'selling_price': 40.00,
        'min_stock': 50,
        'max_stock': 400,
        'shelf_life_days': 180,  # 6 meses
        'production_time_hours': 5,
        'quality_parameters': {
            'sugar_content': 55.0,
            'moisture': 30.0,
            'fat_content': 6.0,
            'color': 'caramelo',
            'temperature_storage': 20  # Temperatura ambiente
        }
    }
]

# Configuración de categorías de productos
product_categories = {
    'frescos': ['Leche', 'Queso', 'Crema de Leche'],
    'procesados': ['Yogurt', 'Mantequilla', 'Dulce de Leche'],
    'especializados': ['Leche Deslactosada'],
    'mayor_margen': ['Dulce de Leche', 'Leche Deslactosada', 'Mantequilla'],
    'alta_rotacion': ['Leche', 'Yogurt'],
    'larga_vida': ['Dulce de Leche', 'Mantequilla']
}

# Métricas de rendimiento por producto
product_metrics = {
    'Leche': {
        'market_share': 0.35,
        'growth_rate': 0.05,
        'customer_satisfaction': 0.92,                                                                                 
        'production_efficiency': 0.88
    },
    'Yogurt': {
        'market_share': 0.25,
        'growth_rate': 0.12,
        'customer_satisfaction': 0.89,
        'production_efficiency': 0.85
    },
    'Queso': {
        'market_share': 0.20,
        'growth_rate': 0.08,
        'customer_satisfaction': 0.91,
        'production_efficiency': 0.82
    }
}