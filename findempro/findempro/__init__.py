"""
Configuración modular de Django
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Determinar qué configuración usar
ENVIRONMENT = os.getenv('DJANGO_ENV', 'development')

if ENVIRONMENT == 'production':
    from .production import *
elif ENVIRONMENT == 'staging':
    from .staging import *
elif ENVIRONMENT == 'vercel':
    from .vercel import *
else:
    from .development import *