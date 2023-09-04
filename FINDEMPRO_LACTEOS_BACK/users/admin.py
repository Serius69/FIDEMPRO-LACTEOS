from django.contrib import admin
from .models import User  # Make sure the import path is correct


admin.site.register(User)