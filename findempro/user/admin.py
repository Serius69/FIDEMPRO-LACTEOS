"""
Configuración mejorada del panel de administración Django
Incluye interfaces avanzadas para gestión de usuarios y actividades
"""

from django.contrib import admin

# Register your models here.

# Personalizar el sitio de administración
admin.site.site_header = "Panel de Administración"
admin.site.site_title = "Admin"
admin.site.index_title = "Bienvenido al panel de administración"