# simulate/templatetags/simulate_tags.py
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def adjust_variable_value(value, variable_name):
    """
    Adjusts the value of specific variables by dividing by 20.
    
    Args:
        value: The original value
        variable_name: The name of the variable
        
    Returns:
        The adjusted value if it's one of the specific variables, 
        otherwise the original value
    """
    try:
        # Convert value to float
        numeric_value = float(value)
        
        # List of variables that need to be divided by 20
        variables_to_adjust = [
            'VPC', 'VENTAS POR CLIENTE',
            'TPV', 'TOTAL PRODUCTOS VENDIDOS',
            'TPPRO', 'TOTAL PRODUCTOS PRODUCIDOS',
            'GO', 'GASTOS OPERATIVOS',
            'TG', 'GASTOS TOTALES'
        ]
        
        # Check if variable name needs adjustment
        if variable_name.upper() in [v.upper() for v in variables_to_adjust]:
            return numeric_value / 20
        
        return numeric_value
    except (ValueError, TypeError):
        return value


@register.filter
def format_variable_unit(unit):
    """
    Formats the unit display for variables.
    
    Args:
        unit: The unit code
        
    Returns:
        The formatted unit string
    """
    unit_mapping = {
        'L': 'Litros',
        'BS': 'Bs.',
        'CLIENTES': 'Clientes',
        '%': 'Porcentaje',
        'Horas': 'Horas',
        'L/BS': 'Litros/Bs.',
        '[0.1,0.3,0.5]': 'Factor'
    }
    
    return unit_mapping.get(unit, unit)


@register.filter
def get_variable_icon(variable_name):
    """
    Returns the appropriate icon class for a variable based on its name.
    
    Args:
        variable_name: The name of the variable
        
    Returns:
        The icon class string
    """
    variable_upper = variable_name.upper()
    
    if 'COSTO' in variable_upper:
        return 'bx bx-receipt text-danger'
    elif 'INGRESO' in variable_upper:
        return 'bx bx-dollar text-success'
    elif 'GANANCIA' in variable_upper:
        return 'bx bx-trending-up text-info'
    elif 'PRODUCTO' in variable_upper:
        return 'bx bx-box text-primary'
    elif 'CLIENTE' in variable_upper:
        return 'bx bx-user text-warning'
    elif 'VENTA' in variable_upper:
        return 'bx bx-cart text-success'
    elif 'CAPACIDAD' in variable_upper:
        return 'bx bx-tachometer text-primary'
    elif 'INVENTARIO' in variable_upper:
        return 'bx bx-package text-info'
    else:
        return 'bx bx-stats text-secondary'


@register.filter
def get_variable_category(variable_name):
    """
    Returns the category name for a variable based on its name.
    
    Args:
        variable_name: The name of the variable
        
    Returns:
        The category string
    """
    variable_upper = variable_name.upper()
    
    if 'COSTO' in variable_upper or 'GASTO' in variable_upper:
        return 'Costo'
    elif 'INGRESO' in variable_upper:
        return 'Ingreso'
    elif 'GANANCIA' in variable_upper:
        return 'Ganancia'
    elif 'PRODUCTO' in variable_upper or 'PRODUCCION' in variable_upper:
        return 'Producto'
    elif 'CLIENTE' in variable_upper:
        return 'Cliente'
    elif 'VENTA' in variable_upper:
        return 'Venta'
    elif 'CAPACIDAD' in variable_upper:
        return 'Capacidad'
    elif 'INVENTARIO' in variable_upper:
        return 'Inventario'
    elif 'DEMANDA' in variable_upper:
        return 'Demanda'
    else:
        return 'Métrica'


@register.simple_tag
def calculate_daily_average(total_value, variable_name, days):
    """
    Calculates the daily average for a variable.
    
    Args:
        total_value: The total accumulated value
        variable_name: The name of the variable
        days: The number of days
        
    Returns:
        The daily average
    """
    try:
        # First adjust the value if needed
        adjusted_value = adjust_variable_value(total_value, variable_name)
        
        # Calculate daily average
        days_float = float(days)
        if days_float > 0:
            return adjusted_value / days_float
        return 0
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def multiply(value, multiplier):
    """
    Multiplies a value by a multiplier.
    
    Args:
        value: The value to multiply
        multiplier: The multiplier
        
    Returns:
        The result of the multiplication
    """
    try:
        return float(value) * float(multiplier)
    except (ValueError, TypeError):
        return 0


@register.filter
def divide(value, divisor):
    """
    Divides a value by a divisor.
    
    Args:
        value: The value to divide
        divisor: The divisor
        
    Returns:
        The result of the division
    """
    try:
        divisor_float = float(divisor)
        if divisor_float != 0:
            return float(value) / divisor_float
        return 0
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.inclusion_tag('simulate/partials/variable_card.html')
def render_variable_card(variable_name, variable_info, simulation_days):
    """
    Renders a variable card with adjusted values.
    
    Args:
        variable_name: The name of the variable
        variable_info: Dictionary with variable information
        simulation_days: Number of simulation days
        
    Returns:
        Context for the variable card template
    """
    # Adjust the total value if needed
    adjusted_total = adjust_variable_value(variable_info.get('total', 0), variable_name)
    
    # Calculate daily average
    daily_average = calculate_daily_average(
        variable_info.get('total', 0), 
        variable_name, 
        simulation_days
    )
    
    return {
        'variable_name': variable_name,
        'total_value': adjusted_total,
        'unit': variable_info.get('unit', ''),
        'formatted_unit': format_variable_unit(variable_info.get('unit', '')),
        'daily_average': daily_average,
        'trend': variable_info.get('trend', ''),
        'change_pct': variable_info.get('change_pct', 0),
        'icon_class': get_variable_icon(variable_name),
        'category': get_variable_category(variable_name)
    }