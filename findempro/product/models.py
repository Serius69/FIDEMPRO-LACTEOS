from django.db import models
from django.urls import reverse
from django.utils import timezone
from business.models import Business

class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    image_src = models.ImageField(upload_to='images/product', blank=True, null=True)
    fk_business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='fk_business', default=1)
    type = models.CharField(max_length=50, default='Dairy')
    profit_margin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    earnings = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    inventory_levels = models.PositiveIntegerField(null=True, blank=True)
    production_output = models.PositiveIntegerField(null=True, blank=True)
    demand_forecast = models.PositiveIntegerField(null=True, blank=True)
    costs = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_ready = models.BooleanField(default=False)
    def __str__(self) -> str:
        """
        Returns the name of the product as a string.
        """
        return self.name

    def get_photo_url(self) -> str:
        """
        Returns the URL of the product's image, if available.
        """
        if self.image_src and hasattr(self.image_src, 'url'):
            return self.image_src.url
        else:
            return "/static/images/products/user-dummy-img.webp"
