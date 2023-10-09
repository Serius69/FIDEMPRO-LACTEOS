from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User  # Ensure User is correctly imported
from django.apps import apps

class Business(models.Model):
    id = models.CharField(max_length=10, primary_key=True)
    image_src = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    date_created = models.DateTimeField(default=timezone.now)
    type = models.CharField(max_length=20)
    location = models.CharField(max_length=255)
    last_updated = models.DateTimeField(auto_now=True)
    description = models.TextField()  # Add this field
    STATUS_CHOICES = (
        (1, 'Active'),
        (2, 'Inactive'),
        (3, 'Archived'),
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)

    # Add a foreign key for User with PROTECT on_delete behavior
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    
    def __str__(self):
        return self.name

class BusinessProduct(models.Model):
    company = models.ForeignKey(Business, on_delete=models.CASCADE)
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.company.name} - {self.product.name}"
