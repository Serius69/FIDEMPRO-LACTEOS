"""
WSGI config for findempro project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'findempro.settings')

# Para Vercel
app = get_wsgi_application()