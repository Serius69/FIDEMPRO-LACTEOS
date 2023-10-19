from django.db import models
from simulate.models import DemandSimulation
# Create your models here.

class FinancialDecision(models.Model):
    simulation = models.ForeignKey(DemandSimulation, on_delete=models.CASCADE)
    decision_date = models.DateField()
    quantity_to_produce = models.PositiveIntegerField()
    revenue = models.DecimalField(max_digits=10, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)  # Add the is_active field

    # Add more fields to capture financial decision details

    def __str__(self):
        return f"Decision for {self.simulation.product.name} on {self.decision_date}"