# simulate/templatetags/math_filters.py
"""
Filtros matemáticos personalizados para templates Django
"""

from django import template
from django.template.defaultfilters import floatformat
import logging

register = template.Library()
logger = logging.getLogger(__name__)

@register.filter
def div(value, divisor):
    """
    Divide dos números de forma segura
    Uso: {{ variable|div:divisor }}
    """
    try:
        if divisor == 0:
            return 0
        return float(value) / float(divisor)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def multiply(value, multiplier):
    """
    Multiplica dos números
    Uso: {{ variable|multiply:multiplier }}
    """
    try:
        return float(value) * float(multiplier)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value):
    """
    Convierte decimal a porcentaje
    Uso: {{ 0.25|percentage }} = 25.0
    """
    try:
        return float(value) * 100
    except (ValueError, TypeError):
        return 0

@register.filter
def safe_float(value, decimal_places=2):
    """
    Convierte a float de forma segura con decimales
    Uso: {{ variable|safe_float:2 }}
    """
    try:
        return round(float(value), decimal_places)
    except (ValueError, TypeError):
        return 0.0

@register.filter
def get_item(dictionary, key):
    """
    Obtiene un item de un diccionario por clave
    Uso: {{ dict|get_item:key }}
    """
    try:
        return dictionary.get(key)
    except (AttributeError, TypeError):
        return None

@register.filter
def subtract(value, arg):
    """
    Resta dos números
    Uso: {{ value|subtract:arg }}
    """
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def add_float(value, arg):
    """
    Suma dos números float
    Uso: {{ value|add_float:arg }}
    """
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def currency_format(value):
    """
    Formatea como moneda boliviana
    Uso: {{ value|currency_format }}
    """
    try:
        value = float(value)
        return f"Bs. {value:,.2f}"
    except (ValueError, TypeError):
        return "Bs. 0.00"

@register.filter
def percentage_format(value, decimal_places=1):
    """
    Formatea como porcentaje
    Uso: {{ 0.25|percentage_format:2 }} = 25.00%
    """
    try:
        value = float(value) * 100
        return f"{value:.{decimal_places}f}%"
    except (ValueError, TypeError):
        return "0.0%"

@register.filter
def safe_division(dividend, divisor):
    """
    División segura que retorna 0 si el divisor es 0
    Uso: {{ dividend|safe_division:divisor }}
    """
    try:
        if float(divisor) == 0:
            return 0
        return float(dividend) / float(divisor)
    except (ValueError, TypeError):
        return 0