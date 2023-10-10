from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User  # Ensure User is correctly imported
from django.apps import apps

# class Business(models.Model):
#     name = models.CharField(max_length=255)
#     type = models.CharField(max_length=255, choices=[('Dairy', 'Dairy')])
#     location = models.CharField(max_length=255, choices=[
#         ('LaPaz', 'La Paz'),
#         ('Cochabamba', 'Cochabamba'),
#         ('SantaCruz', 'Santa Cruz')
#     ])
#     image_src = models.ImageField(upload_to='images/', null=True, blank=True)  # 'images/' is the directory where the image will be saved
#     description = models.TextField()
#     date_created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
#     last_updated = models.DateTimeField(auto_now=True, blank=True, null=True)
#     status = models.IntegerField(default=1)
#     # user = models.ForeignKey(User, on_delete=models.PROTECT)
    
#     def __str__(self):
#         return self.name

class Business(models.Model):
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    image_src = models.ImageField(upload_to='business_images', null=True, blank=True)
    description = models.TextField()

    def __str__(self):
        return self.name

class BusinessProduct(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.business.name} - {self.product.name}"
