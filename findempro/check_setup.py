import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'findempro.settings')
django.setup()

from django.conf import settings
from django.core.management import call_command

print("="*60)
print("VERIFICACIÓN DE CONFIGURACIÓN")
print("="*60)

# Verificar configuración básica
print(f"✓ DEBUG: {settings.DEBUG}")
print(f"✓ BASE_DIR: {settings.BASE_DIR}")
print(f"✓ STATIC_URL: {settings.STATIC_URL}")
print(f"✓ STATICFILES_DIRS: {settings.STATICFILES_DIRS}")

# Verificar que las carpetas existen
checks = [
    ('static', os.path.join(settings.BASE_DIR, 'static')),
    ('templates', os.path.join(settings.BASE_DIR, 'templates')),
    ('media', settings.MEDIA_ROOT),
]

print("\nVerificando directorios:")
for name, path in checks:
    exists = os.path.exists(path)
    print(f"{'✓' if exists else '✗'} {name}: {path}")

# Verificar base de datos
print("\nVerificando base de datos:")
try:
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    print("✓ Conexión a base de datos: OK")
except Exception as e:
    print(f"✗ Error de base de datos: {e}")

# Verificar archivos estáticos
print("\nVerificando archivos estáticos:")
try:
    from django.contrib.staticfiles import finders
    css_file = finders.find('css/bootstrap.min.css')
    if css_file:
        print(f"✓ Bootstrap CSS encontrado: {css_file}")
    else:
        print("✗ Bootstrap CSS no encontrado")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "="*60)
print("Verificación completada")