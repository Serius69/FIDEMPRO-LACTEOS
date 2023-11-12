from django.db import models
from product.models import Product
from questionary.models import QuestionaryResult
from django.utils import timezone

class FDP(models.Model):
    DISTRIBUTION_TYPES = [
        (1, 'Normal'),
        (2, 'Exponential'),
        (3, 'Logarithmic'),
    ]
    name = models.CharField(max_length=100)
    distribution_type = models.IntegerField( 
        choices=DISTRIBUTION_TYPES, 
        default=1)
    lambda_param = models.FloatField()
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.distribution_type()} - {self.name}"
class DataPoint(models.Model):
    value = models.FloatField()
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f'DataPoint: {self.value}'
class SimulationScenario(models.Model):
    utime = models.CharField(max_length=100)
    date_simulate = models.DateField()
    fk_fdp = models.ManyToManyField(FDP, related_name='fk_fdp_simulation', default=1)
    fk_product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='fk_product_simulation', null=True)
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
class ScenarioFDP(models.Model):
    scenario = models.ForeignKey(SimulationScenario, on_delete=models.CASCADE)
    fdp = models.ForeignKey(
        FDP, 
        on_delete=models.CASCADE)
    weight = models.FloatField()
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.scenario} - {self.fdp}"
class ResultSimulation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    simulation_date = models.DateField()
    demand_mean = models.DecimalField(max_digits=10, decimal_places=2)
    demand_std_deviation = models.DecimalField(max_digits=10, decimal_places=2)
    fk_questionary_result = models.ForeignKey(
        QuestionaryResult, 
        on_delete=models.CASCADE, 
        null=True, 
        related_name='fk_questionary_result')
    fk_simulation_scenario = models.ForeignKey(
        SimulationScenario, 
        on_delete=models.CASCADE, 
        null=True, 
        related_name='fk_simulation_scenario_result_simulation')
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.product} - {self.simulation_date}"
