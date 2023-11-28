from django.db import models
from product.models import Product
from django.db.models.signals import post_save
from django.dispatch import receiver
from product.models import Product
from django.db import models
from product.models import Product
from simulate.models import ResultSimulation
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
class Demand(models.Model):
    quantity = models.IntegerField(default=0, help_text='The quantity of the demand')
    is_active = models.BooleanField(
        default=True, verbose_name='Active', help_text='Whether the business is active or not')
    date_created = models.DateTimeField(
        auto_now_add=True, blank=True, null=True, verbose_name='Date Created', help_text='The date the business was created')
    last_updated = models.DateTimeField(
        auto_now=True, blank=True, null=True, verbose_name='Last Updated', help_text='The date the business was last updated')
    is_predicted = models.BooleanField(
        default=False, verbose_name='Predicted', 
        help_text='Whether the demand is predicted or not')
    fk_result_simulation = models.ForeignKey(
        ResultSimulation, 
        default=1, 
        on_delete=models.CASCADE, 
        related_name='fk_result_simulation_demand', 
        verbose_name='Result Simulation', 
        help_text='The result simulation associated with the demand')
    fk_product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='fk_product_demand_behavior', 
        default=1
    )
    def __str__(self):
        return f"Demand of {self.fk_product.name}"
    def create_demand(sender, instance, created, **kwargs):
        if created:
            product = Product.objects.get(pk=instance.pk)
            Demand.objects.create(
                fk_product_id = product.id
            )
    def save_demand(sender, instance, **kwargs):
        for business in instance.fk_product_demand.all():
            business.is_active = instance.is_active
            business.save()

class DemandBehavior(models.Model):
    current_demand = models.OneToOneField(
        Demand, 
        on_delete=models.CASCADE, 
        related_name='fk_demand_behavior_current_demand', 
        default=1,
        blank=  True,
    )
    predicted_demand = models.OneToOneField(
        Demand, 
        on_delete=models.CASCADE, 
        related_name='fk_demand_behavior_predicted_demand', 
        blank=True,
    )
    is_active = models.BooleanField(default=True, verbose_name='Active', help_text='Whether the business is active or not')
    date_created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name='Date Created', help_text='The date the business was created')
    last_updated = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name='Last Updated', help_text='The date the business was last updated')

    def __str__(self):
        return f"Demand Behavior of {self.product.name}"
    def calculate_elasticity(self):
            if self.current_demand and self.predicted_demand:
                current_quantity = self.current_demand.quantity
                predicted_quantity = self.predicted_demand.quantity
                percentage_change = ((predicted_quantity - current_quantity) / current_quantity) * 100
                if percentage_change > 0:
                    elasticity_type = 'Elastica'
                elif percentage_change < 0:
                    elasticity_type = 'Inelastica'
                else:
                    elasticity_type = 'Neutral'

                return elasticity_type, percentage_change
            else:
                # Devolver valores por defecto o manejar el caso donde no hay datos disponibles
                return None, None
    def create_demand_behavior(sender, instance, created, **kwargs):
        if created:
            demand = Product.objects.get(pk=instance.pk)
            if demand.is_predicted:
                DemandBehavior.objects.create(
                    predicted_demand_id = demand.id
                )
    def update_demand_behavior(self, new_demand):
        if new_demand < 0:
            raise ValueError("New demand cannot be negative")
        self.predicted_demand = new_demand
        self.quantity = new_demand
    def predict_demand_behavior(self, prediction_model):
        predicted_demand = self.quantity + 10
        return predicted_demand

