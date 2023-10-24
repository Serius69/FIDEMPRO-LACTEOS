from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User  # Ensure User is correctly imported
from django.apps import apps

class Business(models.Model):
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    image_src = models.ImageField(upload_to='images/business', null=True, blank=True)
    description = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True, blank=True, null=True)
    is_active = models.BooleanField(default=True)  # Add the is_active field
    fk_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='fk_business', default=1)
    
    def __str__(self):
        return self.name