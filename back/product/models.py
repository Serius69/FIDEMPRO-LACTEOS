from django.db import models
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import AbstractUser

class Product(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()  # Usar PositiveIntegerField para cantidades
    description = models.TextField()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        # Define la URL absoluta para el detalle de un producto
        from django.urls import reverse
        return reverse('product-detail', args=[str(self.id)])
