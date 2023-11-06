from django.db import models
from product.models import Product

class Dashboard(models.Model):
    """
    A model for storing dashboard configurations for demand data of a product.
    """
    product = models.OneToOneField(
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

    def clean(self):
        # You can add custom validation logic here for widget and layout configurations.
        # Ensure they follow a specific schema if needed.
        pass
