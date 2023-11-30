from django.db import models
from product.models import Product
from django.db.models.signals import post_save
from django.dispatch import receiver
from product.models import Product
from django.db import models
from product.models import Product
from django.db.models.signals import post_save
from django.dispatch import receiver
from .dashboard_data import chart_data
class Chart(models.Model):
    title = models.CharField(max_length=255, default='Chart', help_text="The title of the chart.")
    chart_type = models.CharField(max_length=50, default='line', help_text="The type of chart to use.")
    chart_data = models.JSONField(default=list, help_text="Structured JSON data for chart configuration.")
    fk_product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='fk_product_charts', 
        default=1,
        help_text="The product associated with the chart."
    )
    widget_config = models.JSONField(
        help_text="Structured JSON data for widget configuration.",
        default=dict 
    )
    layout_config = models.JSONField(
        help_text="Structured JSON data for layout configuration.",
        default=dict 
    )
    is_active = models.BooleanField(default=True, verbose_name='Active', help_text='Whether the chart is active or not')
    date_created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name='Date Created', help_text='The date the chart was created')
    last_updated = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name='Last Updated', help_text='The date the chart was last updated')
    @receiver(post_save, sender=Product)
    def create_dashboard(sender, instance, created, **kwargs):
        if created:
            product = Product.objects.get(pk=instance.pk)
            for data in chart_data:
                Chart.objects.create(
                    title=data['title'],                    
                    chart_type=data['chart_type'],
                    chart_data= data['chart_data'],
                    widget_config= data['widget_config'],
                    layout_config= data['layout_config'],
                    is_active= True,
                    fk_product_id=product.id,
                )
    @receiver(post_save, sender=Product)
    def save_dashboard(sender, instance, **kwargs):
        for dashboard in instance.fk_product_charts.all():
            dashboard.is_active = instance.is_active
            dashboard.save()
