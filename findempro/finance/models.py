from typing import Optional
from django.db import models
from simulate.models import Simulation
from django.utils import timezone
from django.dispatch import receiver
from .finance_data import recommendation_data
from django.db.models.signals import post_save
from product.models import Product
from business.models import Business
class FinanceRecommendation(models.Model):
    """
    FinanceRecommendation Model

    This model represents a finance recommendation associated with a business. It includes details such as the name, 
    variable name, threshold value, recommendation text, and its association with a business. The model also tracks 
    whether the recommendation is active and includes timestamps for creation and updates.

    Attributes:
        name (CharField): The name of the finance recommendation (optional).
        variable_name (CharField): The variable name of the finance recommendation (optional).
        threshold_value (DecimalField): The threshold value associated with the finance recommendation (optional).
        recommendation (TextField): The recommendation text (optional).
        fk_business (ForeignKey): A foreign key linking the recommendation to a Business instance.
        is_active (BooleanField): Indicates whether the recommendation is active (default is True).
        date_created (DateTimeField): The timestamp when the recommendation was created (auto-generated).
        last_updated (DateTimeField): The timestamp when the recommendation was last updated (auto-generated).

    Methods:
        __str__(): Returns the string representation of the finance recommendation, which is the name.
        
    Signals:
        create_finance_recommendation (post_save): Triggered when a Business instance is created. Automatically 
            creates finance recommendations based on predefined data.
        save_finance_recommendation (post_save): Triggered when a Business instance is saved. Updates the 
            `is_active` status of associated finance recommendations based on the business's status.
    """
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Name', help_text='The name of the finance')
    variable_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Variable Name', help_text='The variable name of the finance')
    threshold_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name='Threshold Value', help_text='The threshold value of the finance')
    recommendation = models.TextField(blank=True, null=True, verbose_name='Recommendation', help_text='The recommendation of the finance')
    fk_business = models.ForeignKey(
        Business, 
        on_delete=models.CASCADE, 
        related_name='fk_business_finance_recommendation', 
        help_text='The business associated with the finance recomendation',
        default=1)
    is_active = models.BooleanField(default=True, verbose_name='Active', help_text='Whether the finance is active or not')
    date_created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name='Date Created', help_text='The date the finance was created')
    last_updated = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name='Date Created', help_text='The date the finance was created')
    def __str__(self):
        return self.name
    @receiver(post_save, sender=Business)
    def create_finance_recommendation(sender, instance, created, **kwargs):
        if created:
            business = Business.objects.get(pk=instance.pk)
            for data in recommendation_data:
                FinanceRecommendation.objects.create(
                    name=data['name'],
                    recommendation=data['recommendation'],
                    threshold_value=data['threshold_value'],
                    variable_name=data['variable_name'],
                    fk_business_id=business.id,
                    is_active=True
                )
        print('Se crearon las recomendaciones')
    @receiver(post_save, sender=Business)
    def save_finance_recommendation(sender, instance, **kwargs):
        for finance_recommendation in instance.fk_business_finance_recommendation.all():
            finance_recommendation.is_active = instance.is_active
            finance_recommendation.save()
class FinanceRecommendationSimulation(models.Model):
    data = models.FloatField()
    fk_simulation = models.ForeignKey(
        Simulation, 
        on_delete=models.CASCADE, 
        related_name='fk_simulation_decision',
        default=1
    )
    fk_finance_recommendation = models.ForeignKey(
        FinanceRecommendation,
        on_delete=models.CASCADE,  # Adjust the on_delete behavior as needed
        related_name='fk_finance_recommendation_decision',
        default=1
    )    
    is_active = models.BooleanField(default=True, verbose_name='Active', help_text='Whether the finance is active or not')
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"Decision for {self.fk_simulation.fk_product.name} on {self.decision_date}"


