from django.db import models

class FDP(models.Model):
    name = models.CharField(max_length=100)
    lambda_param = models.FloatField()

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'simulate'

class DataPoint(models.Model):
    value = models.FloatField()

    def __str__(self):
        return f'DataPoint: {self.value}'
    class Meta:
            app_label = 'simulate'
