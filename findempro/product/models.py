from django.db import models
from django.urls import reverse
from django.utils import timezone
from business.models import Business
from django.db.models.signals import post_save
from django.dispatch import receiver
from .products_data import products_data
from .areas_data import areas_data
class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(default=timezone.now)
    image_src = models.ImageField(upload_to='images/product', blank=True, null=True)
    fk_business = models.ForeignKey(
        Business, 
        on_delete=models.CASCADE, 
        related_name='fk_business_product', 
        help_text='The business associated with the product',
        default=1)
    TYPE_CHOICES = [
        (1, 'Product'),
        (2, 'Service'),
    ]    
    type = models.IntegerField(default=1, choices=TYPE_CHOICES)
    profit_margin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    earnings = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    inventory_levels = models.PositiveIntegerField(null=True, blank=True)
    production_output = models.PositiveIntegerField(null=True, blank=True)
    demand_forecast = models.PositiveIntegerField(null=True, blank=True)
    costs = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_ready = models.BooleanField(default=False)
    def __str__(self) -> str:
        return self.name

    def get_photo_url(self) -> str:
        if self.image_src and hasattr(self.image_src, 'url'):
            return self.image_src.url
        else:
            return "/static/images/product/product-dummy-img.webp"

class Area(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image_src = models.ImageField(upload_to='images/area', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(default=timezone.now)
    fk_product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='fk_product_area', 
        help_text='The product associated with the area',
        default=1)
    is_checked_for_simulation = models.BooleanField(default=False)
    params = models.JSONField(null=True, blank=True)  # Use JSONField for a list of values
    def __str__(self) -> str:
        return self.name
    def get_photo_url(self) -> str:
        if self.image_src and hasattr(self.image_src, 'url'):
            return self.image_src.url
        else:
            return "/static/images/product/product-dummy-img.webp"
