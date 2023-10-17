from django.db import models
from product.models import Product
from question.models import Question
class FDP(models.Model):
    name = models.CharField(max_length=100)
    lambda_param = models.FloatField()
    is_active = models.BooleanField(default=True)  # Add the is_active field

    def __str__(self):
        return self.name

class NormalFDP(FDP):
    mean = models.FloatField()
    std_deviation = models.FloatField()
    is_active = models.BooleanField(default=True)  # Add the is_active field

    def __str__(self):
        return f"Normal - {self.name}"

class ExponentialFDP(FDP):
    is_active = models.BooleanField(default=True)  # Add the is_active field

    def __str__(self):
        return f"Exponential - {self.name}"

class LogarithmicFDP(FDP):
    is_active = models.BooleanField(default=True)  # Add the is_active field

    def __str__(self):
        return f"Logarithmic - {self.name}"

class DataPoint(models.Model):
    is_active = models.BooleanField(default=True)  # Add the is_active field

    value = models.FloatField()

    def __str__(self):
        return f'DataPoint: {self.value}'

class SimulationScenario(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    utime = models.CharField(max_length=100)  # Add max_length for CharField
    fdps = models.ManyToManyField(FDP)  # Use ManyToManyField to link with PDFs
    date_simulate = models.DateField()  # Add a DateField for the simulation date
    is_active = models.BooleanField(default=True)  # Add the is_active field


class ScenarioPDF(models.Model):
    scenario = models.ForeignKey(SimulationScenario, on_delete=models.CASCADE)
    fdp = models.ForeignKey(FDP, on_delete=models.CASCADE)
    weight = models.FloatField()  # Define the 'weight' field here if it's intended to be part of the model

    def __str__(self):
        return f"{self.scenario.name} - {self.fdp.name}"

class DemandSimulation(models.Model):
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    fk_simulation_scenario = models.ForeignKey(SimulationScenario, on_delete=models.CASCADE)
    fk_questionary = models.ForeignKey(SimulationScenario, on_delete=models.CASCADE)
    simulation_date = models.DateField()
    demand_mean = models.DecimalField(max_digits=10, decimal_places=2)
    demand_std_deviation = models.DecimalField(max_digits=10, decimal_places=2)
    # Add more fields to represent demand simulation parameters

    def __str__(self):
        return f"{self.product.name} - {self.simulation_date}"

