"""
Configuración modular de Django
"""
import os

# DJANGO_ENV se fija desde el entorno del sistema (scripts .bat) o por defecto 'development'.
# La carga del archivo .env.{ENV} la hace base.py para evitar que un .env genérico
# bloquee las variables específicas de cada entorno.
ENVIRONMENT = os.getenv('DJANGO_ENV', 'development')

if ENVIRONMENT == 'production':
    from .production import *
elif ENVIRONMENT == 'staging':
    from .staging import *
elif ENVIRONMENT in ('testing', 'test'):
    from .testing import *
else:
    from .development import *