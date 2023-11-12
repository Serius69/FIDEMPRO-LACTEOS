from typing import Optional
from django.db import models
from simulate.models import ResultSimulation  # Make sure the import statement is correct.
from django.utils import timezone
from django.dispatch import receiver
from .finance_data import finance_data
from django.db.models.signals import post_save
from product.models import Product
class FinanceRecommendation(models.Model):
    name = models.CharField(max_length=255)
    recommendation = models.TextField()
    description = models.TextField()

    is_active = models.BooleanField(default=True, verbose_name='Active', help_text='Whether the finance is active or not')
    date_created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name='Date Created', help_text='The date the finance was created')
    last_updated = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name='Date Created', help_text='The date the finance was created')

    def __str__(self):
        return self.name
    @receiver(post_save, sender=Product)
    def create_finance_recommendation(sender, instance, created, **kwargs):
        if created:
            for data in finance_data:
                FinanceRecommendation.objects.create(
                    name=data['name'],
                    recommendation=data['recommendation'],
                    description=data['description'],
                    is_active=True
                )
    @receiver(post_save, sender=Product)
    def save_finance_recommendation(sender, instance, **kwargs):
        if instance.type == 1:
            instance.question_set.all().update(is_active=instance.is_active)
            
class FinancialDecision(models.Model):
    decision_date = models.DateField()
    quantity_to_produce = models.PositiveIntegerField()
    revenue = models.DecimalField(max_digits=10, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    fk_result_simulation = models.ForeignKey(
        ResultSimulation, 
        on_delete=models.CASCADE,  # Added a comma here
        related_name='fk_result_simulation',
        default=ResultSimulation.objects.first(),
    )
    fk_finance_recommendation = models.ForeignKey(
        FinanceRecommendation,
        on_delete=models.CASCADE,  # Adjust the on_delete behavior as needed
        related_name='fk_finance_recommendation',
        default=FinanceRecommendation.objects.first(),
    )    
    is_active = models.BooleanField(default=True, verbose_name='Active', help_text='Whether the finance is active or not')
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"Decision for {self.fk_result_simulation.product.name} on {self.decision_date}"


