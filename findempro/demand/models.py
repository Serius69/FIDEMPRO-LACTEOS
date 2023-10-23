from django.db import models

# Create your models here.
class DemandModel(models.Model):
    product = models.ForeignKey('DairyProduct', on_delete=models.CASCADE)
    date = models.DateField()
    quantity = models.PositiveIntegerField()
    related_factor = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)  # Add the is_active field

    def __str__(self):
        return f"Demand for {self.product} on {self.date}"