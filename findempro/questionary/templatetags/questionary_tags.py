from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Template filter para acceder a elementos de un diccionario usando una clave variable.
    Uso: {{ dictionary|get_item:key }}
    """
    return dictionary.get(key)