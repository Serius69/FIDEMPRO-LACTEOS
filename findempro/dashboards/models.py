from django.db import models
from product.models import Product
from django.db.models.signals import post_save
from django.dispatch import receiver
class Dashboard(models.Model):
    fk_product = models.OneToOneField(
        Product, 
        on_delete=models.CASCADE, 
        related_name='fk_product_dashboard', 
        null=True  # Donde 1 es el ID del producto por defecto.
)
    widget_config = models.JSONField(
        help_text="Structured JSON data for widget configuration.",
        default=dict 
    )
    layout_config = models.JSONField(
        help_text="Structured JSON data for layout configuration.",
        default=dict 
    )
    
    is_active = models.BooleanField(default=True, verbose_name='Active', help_text='Whether the business is active or not')
    date_created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name='Date Created', help_text='The date the business was created')
    last_updated = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name='Last Updated', help_text='The date the business was last updated')

    def __str__(self):
        return f"Dashboard for {self.product.name}"

    @receiver(post_save, sender=Product)
    def create_dashboard(sender, instance, created, **kwargs):
        if created:
            product = Product.objects.get(pk=instance.pk)
            Dashboard.objects.create(
                fk_product_id = product.id
            )
    @receiver(post_save, sender=Product)
    def save_product(sender, instance, **kwargs):
        try:
            dashboard = instance.fk_product_dashboard
            dashboard.is_active = instance.is_active
            dashboard.save()
        except Dashboard.DoesNotExist:
            # Handle the case where the related dashboard does not exist
            pass
    def clean(self):
        # You can add custom validation logic here for widget and layout configurations.
        # Ensure they follow a specific schema if needed.
        pass
