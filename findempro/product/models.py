from django.db import models
from django.urls import reverse
from django.utils import timezone
from business.models import Business
from django.db.models.signals import post_save
from django.dispatch import receiver
from .products_data import products_data
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
    type = models.CharField(max_length=50, default='Dairy')
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
            return "/static/images/products/user-dummy-img.webp"
    @receiver(post_save, sender=Business)
    def create_product(sender, instance, created, **kwargs):
        if created:
            business = Business.objects.get(pk=instance.pk)
            for data in products_data:
                Product.objects.create(
                    name=data['name'],                    
                    description=data['description'],
                    image_src= data['image_src'],
                    type= data['type'],
                    is_active= True,
                    fk_business_id=business.id,
                )

    @receiver(post_save, sender=Business)
    def save_product(sender, instance, **kwargs):
        for product in instance.fk_business_product.all():
            product.is_active = instance.is_active
            product.save()
