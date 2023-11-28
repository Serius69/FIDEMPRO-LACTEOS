import math
from django.db import models
from product.models import Product, Area
from variable.models import Variable,EquationResult,Equation
from questionary.models import QuestionaryResult,Questionary,Answer,Question
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.urls import reverse
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import random
import numpy as np
from django.shortcuts import render, redirect, get_object_or_404
from datetime import datetime, timedelta
from scipy.stats import expon, lognorm, norm
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
    mean_param = models.FloatField(null=True, blank=True, help_text='Mean parameter for the normal distribution')
    std_dev_param = models.FloatField(null=True, blank=True, help_text='Standard deviation parameter for the normal distribution')

    is_active = models.BooleanField(default=True, help_text='Whether the distribution is active or not')
    date_created = models.DateTimeField(default=timezone.now, help_text='The date the distribution was created')
    last_updated = models.DateTimeField(auto_now=True, help_text='The date the distribution was last updated')
    
    @receiver(post_save, sender=Product)
    def create_probabilistic_density_functions(sender, instance, created, **kwargs):
        distribution_types = [1, 2, 3]  # Normal, Exponential, Logarithmic
        names = ['Normal Distribution', 'Exponential Distribution', 'Log-Normal Distribution']

        for distribution_type, name in zip(distribution_types, names):
            pdf = ProbabilisticDensityFunction(
                name=name,
                distribution_type=distribution_type,
                is_active=True
            )
            if distribution_type == 1:  # Normal distribution
                pdf.lambda_param = 1.0  # Adjust with your specific values
                pdf.cumulative_distribution_function = 0.5  # Adjust with your specific values
                pdf.mean_param = 450.0
                pdf.std_dev_param = 10.0
            elif distribution_type == 2:  # Exponential distribution
                pdf.lambda_param = 0.5           
                pdf.cumulative_distribution_function = expon.cdf(2.0, scale=1/0.5) 
                pdf.mean_param = 1 / 0.5 
                pdf.std_dev_param = expon(scale=1/pdf.lambda_param).std()
            elif distribution_type == 3:  # Log-Normal distribution
                pdf.lambda_param = 0  # Adjust with your specific values
                pdf.cumulative_distribution_function = lognorm.cdf(2.0, s=0.2, scale=np.exp(0.0))  # Adjust with your specific values
                pdf.mean_param = 50.0
                pdf.std_dev_param = np.exp(0.0 + (0.2 ** 2) / 2)
            pdf.save()
        print('Se crearon las distribuciones')
class DataPoint(models.Model):
    value = models.FloatField()
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    def __str__(self):        
        return f'DataPoint: {self.value}'

class DemandHistorical(models.Model):
    demand = models.IntegerField()
class Simulation(models.Model):
    quantity_time = models.IntegerField(default=1, help_text='The quantity of the simulation')
    unit_time = models.CharField(max_length=100, default='day', help_text='The unit of time for the simulation')
    fk_fdp = models.ForeignKey(ProbabilisticDensityFunction, on_delete=models.CASCADE, default=1)
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
    
    @receiver(post_save, sender=QuestionaryResult)
    def create_simulation(sender, instance, created, **kwargs):
        # Get the related Questionary
        # fk_questionary = instance.fk_questionary

        # Get the Question object based on the question text
        # question_text = 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).'
        # fk_question_object = get_object_or_404(Question, question=question_text, fk_questionary=fk_questionary)

        # Get the related Answer
        # demand = get_object_or_404(Answer, fk_question=fk_question_object, fk_questionary_result=instance)
        demand =[513, 820, 648, 720, 649, 414, 704, 814, 647, 934, 483, 882, 220, 419, 254, 781, 674, 498, 518, 948, 983, 154, 649, 625, 865, 800, 848, 783, 218, 906]
        # Create the Simulation
        simulation = Simulation(
            unit_time='day',
            # fk_fdp_id=1,
            demand_history=demand,
            fk_questionary_result=instance,
            is_active=True
        )
        simulation.save()
    @receiver(post_save, sender=QuestionaryResult)
    def save_question(sender, instance, **kwargs):
        for simulate in instance.simulations.all():
            simulate.is_active = instance.is_active
            simulate.save()

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
    @receiver(post_save, sender=Simulation)
    def create_random_result_simulations(sender, instance, created, **kwargs):
        fk_simulation = Simulation.objects.get(id=instance.id)
        for _ in range(30):
            demand_mean = random.uniform(50, 150)
            demand_std_deviation = random.uniform(5, 20)
            date = [str(datetime.now() + timedelta(days=i)) for i in range(10)]
            variables = {"CPVD": [random.randint(100, 500) for _ in range(10)], "PVP": [random.uniform(1, 2) for _ in range(10)]}
            unit = {"measurement": "kg", "value": random.randint(1, 10)}
            unit_time = {"time_unit": "day", "value": random.randint(1, 30)}
            results = {"result" + str(i): random.randint(20, 60) for i in range(1, 5)}

            result_simulation = ResultSimulation(
                demand_mean=demand_mean,
                demand_std_deviation=demand_std_deviation,
                date=date,
                variables=variables,
                unit=unit,
                unit_time=unit_time,
                results=results,
                fk_simulation=fk_simulation,
                is_active=True
            )
            result_simulation.save()
    

