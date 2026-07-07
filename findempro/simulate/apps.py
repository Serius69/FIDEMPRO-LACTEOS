import os
from django.apps import AppConfig


class SimulateappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'simulate'
    # Explicit path fixes Windows drive-letter case-sensitivity issue
    # (Django sees both 'E:\...' and 'e:\...' as distinct paths)
    path = os.path.dirname(os.path.abspath(__file__))
