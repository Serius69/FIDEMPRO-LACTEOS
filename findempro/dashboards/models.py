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
from .dashboard_data import dashboard_data
class Dashboard(models.Model):
    title = models.CharField(max_length=255, default='Dashboard', help_text="The title of the dashboard.")
    chart_type = models.CharField(max_length=50, default='line', help_text="The type of chart to use for the dashboard.")
    chart_data = models.JSONField(default=dict, help_text="Structured JSON data for chart configuration.")
    fk_product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='fk_product_dashboard', 
        default=1,
        help_text="The product associated with the dashboard."
    )
    widget_config = models.JSONField(
        help_text="Structured JSON data for widget configuration.",
        default=dict 
    )
    layout_config = models.JSONField(
        help_text="Structured JSON data for layout configuration.",
        default=dict 
    )
    is_active = models.BooleanField(default=True, verbose_name='Active', help_text='Whether the dashboard is active or not')
    date_created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name='Date Created', help_text='The date the dashboard was created')
    last_updated = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name='Last Updated', help_text='The date the dashboard was last updated')
    def __str__(self):
        return f"Dashboard for {self.product.name}"
    @receiver(post_save, sender=Product)
    def create_dashboard(sender, instance, created, **kwargs):
        if created:
            product = Product.objects.get(pk=instance.pk)
            for data in dashboard_data:
                Dashboard.objects.create(
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
        for dashboard in instance.fk_product_dashboard.all():
            dashboard.is_active = instance.is_active
            dashboard.save()
class Demand(models.Model):
    quantity = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True, verbose_name='Active', help_text='Whether the business is active or not')
    date_created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name='Date Created', help_text='The date the business was created')
    last_updated = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name='Last Updated', help_text='The date the business was last updated')
    is_predicted = models.BooleanField(default=False, verbose_name='Predicted', help_text='Whether the demand is predicted or not')
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
    # @receiver(post_save, sender=Product)
    # def create_demand(sender, instance, created, **kwargs):
    #     if created:
    #         product = Product.objects.get(pk=instance.pk)
    #         Demand.objects.create(
    #             fk_product_id = product.id
    #         )
    # @receiver(post_save, sender=Product)
    # def save_demand(sender, instance, **kwargs):
    #     for business in instance.fk_product_demand.all():
    #         business.is_active = instance.is_active
    #         business.save()

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
    # @receiver(post_save, sender=Demand)
    # def create_demand_behavior(sender, instance, created, **kwargs):
    #     if created:
    #         demand = Product.objects.get(pk=instance.pk)
    #         if demand.is_predicted:
    #             DemandBehavior.objects.create(
    #                 predicted_demand_id = demand.id
    #             )
    # @receiver(post_save, sender=Demand)
    # def update_demand_behavior(self, new_demand):
    #     if new_demand < 0:
    #         raise ValueError("New demand cannot be negative")
    #     self.predicted_demand = new_demand
    #     self.quantity = new_demand
    def predict_demand_behavior(self, prediction_model):
        predicted_demand = self.quantity + 10
        return predicted_demand

