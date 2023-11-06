from typing import Optional
from django.db import models
from simulate.models import ResultSimulation  # Make sure the import statement is correct.

class FinancialDecision(models.Model):
    decision_date = models.DateField()
    quantity_to_produce = models.PositiveIntegerField()
    revenue = models.DecimalField(max_digits=10, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    simulation = models.ForeignKey(ResultSimulation, on_delete=models.CASCADE)
    
    is_active = models.BooleanField(default=True, verbose_name='Active', help_text='Whether the finance is active or not')
    date_created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name='Date Created', help_text='The date the finance was created')
    last_updated = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name='Last Updated', help_text='The date the finance was last updated')

    def __str__(self) -> str:
        return f"Decision for {self.simulation.product.name} on {self.decision_date}" 
class FinanceRecommendation(models.Model):
    name = models.CharField(max_length=255)
    recommendation = models.TextField()
    description = models.TextField()

    is_active = models.BooleanField(default=True, verbose_name='Active', help_text='Whether the finance is active or not')
    date_created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name='Date Created', help_text='The date the finance was created')
    last_updated = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name='Last Updated', help_text='The date the finance was last updated')

    def __str__(self):
        return self.name