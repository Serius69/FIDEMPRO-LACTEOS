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
    def __str__(self):
        return f'DataPoint: {self.value}'
class Simulation(models.Model):
    class Meta:
        verbose_name = "Simulation"
        ordering = ['-date'] 
    date = models.DateField()
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='simulations'  
    )
    distributions = models.ManyToManyField(
        FDP,
        related_name='simulations'
    )
    demand_mean = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    questionary_result = models.ForeignKey(
        QuestionaryResult,
        on_delete=models.CASCADE,
        related_name='simulations',
        null=True
    )
    utime = models.CharField(max_length=100)
    date_simulate = models.DateField()
    fk_fdp = models.ManyToManyField(FDP, related_name='fk_fdp_simulation', default=1)
    weight = models.FloatField()
    fk_questionary = models.ForeignKey(
        Questionary, 
        on_delete=models.CASCADE, 
        related_name='fk_product_simulation', null=True)
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    def get_absolute_url(self):
        return reverse('simulation_detail', args=[self.id])
class ResultSimulation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    simulation_date = models.DateField()
    demand_mean = models.DecimalField(max_digits=10, decimal_places=2)
    demand_std_deviation = models.DecimalField(max_digits=10, decimal_places=2)
    fk_simulation = models.ForeignKey(
        Simulation, 
        on_delete=models.CASCADE, 
        null=True, 
        related_name='fk_simulation__result_simulation')
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.product} - {self.simulation_date}"
    @receiver(post_save, sender=Simulation)
    def create_result_simulation(sender, instance, created, **kwargs):
        if created:
            ResultSimulation.objects.create(
                product=instance.product,
                simulation_date=instance.simulation_date,
                # Add other fields as needed
                fk_simulation_scenario=instance
        )
    
    
