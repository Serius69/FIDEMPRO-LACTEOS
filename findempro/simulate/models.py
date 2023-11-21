import math
from django.db import models
from product.models import Product, Area
from variable.models import Variable,EquationResult,Equation
from questionary.models import QuestionaryResult,Questionary,Answer
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.urls import reverse
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
class ProbabilisticDensityFunction(models.Model):
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
    def calculate_cdf(self, x):
        """
        Calculate the cumulative distribution function (CDF) for the given x value.
        """
        if self.distribution_type == 1:  # Normal distribution
            # Implement CDF calculation for normal distribution
            cdf = 0.5 * (1 + math.erf((x) / (math.sqrt(2))))
        elif self.distribution_type == 2:  # Exponential distribution
            # Implement CDF calculation for exponential distribution
            cdf = 1 - math.exp(-self.lambda_param * x)
        elif self.distribution_type == 3:  # Logarithmic distribution
            # Implement CDF calculation for logarithmic distribution
            cdf = math.log(1 + x)
        else:
            raise ValueError("Invalid distribution type")

        return cdf
class DataPoint(models.Model):
    value = models.FloatField()
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    def __str__(self):        return f'DataPoint: {self.value}'

class DemandHistorical(models.Model):
    unit_time = models.IntegerField()
    demand = models.IntegerField()
class Simulation(models.Model):
    unit_time = models.CharField(max_length=100, default='day', help_text='The unit of time for the simulation')
    
    fk_fdp = models.ManyToManyField(ProbabilisticDensityFunction, related_name='fk_fdp_simulation', default=1)
    # se guardara un archivo JSON con los 30 datos de la demanda historica
    demand_history = models.JSONField(null=True, blank=True)
    
    weight = models.FloatField(default=1, help_text='The weight of the simulation')
    
    fk_questionary = models.ForeignKey(
        Questionary, 
        on_delete=models.CASCADE, 
        related_name='fk_product_simulation', null=True)
    distributions = models.ManyToManyField(
        ProbabilisticDensityFunction,
        related_name='simulations',
        help_text='The ProbabilisticDensityFunctions associated with the simulation',
    )
    
    questionary_result = models.ForeignKey(
        QuestionaryResult,
        on_delete=models.CASCADE,
        related_name='simulations',
        null=True,
        help_text='The questionary result associated with the simulation',
    )
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

class ResultSimulation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, help_text='The product associated with the result')
    demand_mean = models.DecimalField(max_digits=10, decimal_places=2,help_text='The mean of the demand')
    demand_std_deviation = models.DecimalField(max_digits=10, decimal_places=2,help_text='The standard deviation of the demand')
    
    date = models.JSONField(null=True, blank=True)
    variables = models.JSONField(null=True, blank=True)
    unit = models.JSONField(null=True, blank=True)
    unit_time = models.JSONField(null=True, blank=True)
    results = models.JSONField(null=True, blank=True)
    
    
    fk_simulation = models.ForeignKey(
        Simulation, 
        on_delete=models.CASCADE, 
        null=True, 
        related_name='fk_simulation_result_simulation')
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.product} - {self.simulation_date}"
    
