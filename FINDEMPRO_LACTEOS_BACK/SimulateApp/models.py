from django.db import models

class FDP(models.Model):
    name = models.CharField(max_length=100)
    lambda_param = models.FloatField()

    def __str__(self):
        return self.name
class DataPoint(models.Model):
    value = models.FloatField()  # Assuming your data points are floating-point numbers

    def __str__(self):
        return f'DataPoint: {self.value}'