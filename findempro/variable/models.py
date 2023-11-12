from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from product.models import Product
from .variables_data import variables_data

class Variable(models.Model):
    name = models.CharField(max_length=70)
    initials = models.CharField(max_length=7, default="var")
    type = models.CharField(max_length=20, default='Estado')
    unit = models.CharField(max_length=50)
    description = models.TextField(default="Description predetermined")
    image_src = models.ImageField(upload_to='images/variables', blank=True, null=True)
    fk_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='fk_product')
    is_active = models.BooleanField(default=True, verbose_name='Active', help_text='Whether the variable is active or not')
    date_created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name='Date Created', help_text='The date the variable was created')
    last_updated = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name='Last Updated', help_text='The date the variable was last updated')

    def __str__(self):
        return self.name

@receiver(post_save, sender=Product)
def create_variables(sender, instance, created, **kwargs):
    if created:
        for data in variables_data:
            Variable.objects.create(
                name=data['name'],
                initials=data['initials'],
                type=data['type'],
                unit=data['unit'],
                description=data['description'],
                fk_product=instance,
                is_active=True
            )

@receiver(post_save, sender=Product)
def save_variables(sender, instance, **kwargs):
    instance.fk_product.all().update(is_active=instance.is_active)
