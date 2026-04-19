#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    # Seleccionar settings según DJANGO_ENV — nunca apuntar a findempro.settings (no existe)
    _env = os.environ.get('DJANGO_ENV', 'development')
    _settings_map = {
        'production': 'findempro.settings.production',
        'staging': 'findempro.settings.staging',
        'development': 'findempro.settings.development',
    }
    os.environ.setdefault(
        'DJANGO_SETTINGS_MODULE',
        _settings_map.get(_env, 'findempro.settings.development')
    )

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. "
            "Verifica que esté instalado y que el virtualenv esté activado."
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
