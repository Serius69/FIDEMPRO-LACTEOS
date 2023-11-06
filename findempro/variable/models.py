from django.db import models
from django.utils import timezone
from django.urls import reverse  # Import reverse from django.urls
from product.models import Product  # Import the Product model
from multiselectfield import MultiSelectField

class Variable(models.Model):
    name = models.CharField(max_length=70)
    initials = models.CharField(max_length=7, default="var")
    type = models.IntegerField(default=1)
    unit = models.CharField(max_length=20)
    description = models.TextField(default="Descripción predeterminada")
    image_src = models.ImageField(upload_to='images/variables', blank=True, null=True)
    fk_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='fk_product')
    is_active = models.BooleanField(default=True, verbose_name='Active', help_text='Whether the variable is active or not')
    date_created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name='Date Created', help_text='The date the variable was created')
    last_updated = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name='Last Updated', help_text='The date the variable was last updated')

    def __str__(self):
        return self.name