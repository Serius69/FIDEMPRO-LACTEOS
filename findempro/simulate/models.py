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
    name = models.CharField(max_length=100, help_text='The name of the distribution', default='Distribution', blank=True, null=True)
    distribution_type = models.IntegerField( 
        choices=DISTRIBUTION_TYPES, 
        default=1, help_text='The type of the distribution')
    lambda_param = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0)], help_text='The lambda parameter for the exponential distribution')
    cumulative_distribution_function = models.FloatField(null=True, blank=True )  # CDF field
    is_active = models.BooleanField(default=True, help_text='Whether the distribution is active or not')
    date_created = models.DateTimeField(default=timezone.now, help_text='The date the distribution was created')
    last_updated = models.DateTimeField(auto_now=True, help_text='The date the distribution was last updated')
    def __str__(self):
        return f"{self.distribution_type()} - {self.name}"
    def calculate_cumulative_distribution_function(self, x):
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
    fk_fdp = models.ForeignKey(
        ProbabilisticDensityFunction, 
        on_delete=models.CASCADE,
        related_name='fk_fdp_simulation', 
        default=1, help_text='The probabilistic density function associated with the simulation')
    # se guardara un archivo JSON con los 30 datos de la demanda historica
    demand_history = models.JSONField(null=True, blank=True, help_text='The demand history for the simulation')
    fk_questionary_result = models.ForeignKey(
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
    demand_mean = models.DecimalField(max_digits=10, decimal_places=2,help_text='The mean of the demand')
    demand_std_deviation = models.DecimalField(max_digits=10, decimal_places=2,help_text='The standard deviation of the demand')
    date = models.JSONField(null=True, blank=True, help_text='The date of the simulation')
    variables = models.JSONField(null=True, blank=True, help_text='The variables of the simulation')
    unit = models.JSONField(null=True, blank=True, help_text='The unit of the simulation')
    unit_time = models.JSONField(null=True, blank=True ,help_text='The unit of time for the simulation')
    results = models.JSONField(null=True, blank=True, help_text='The results of the simulation')
    fk_simulation = models.ForeignKey(
        Simulation, 
        on_delete=models.CASCADE, 
        default=1, 
        related_name='fk_simulation_result_simulation',
        help_text='The simulation associated with the result')
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

