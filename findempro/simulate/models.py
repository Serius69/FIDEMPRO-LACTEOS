from decimal import Decimal
import math
from django.db import models
from product.models import Product, Area
from business.models import Business
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
    fk_business = models.ForeignKey(
        Business, 
        on_delete=models.CASCADE, 
        related_name='fk_business_fdp', 
        help_text='The business associated with the fdp',
        default=1)
    is_active = models.BooleanField(default=True, help_text='Whether the distribution is active or not')
    date_created = models.DateTimeField(default=timezone.now, help_text='The date the distribution was created')
    last_updated = models.DateTimeField(auto_now=True, help_text='The date the distribution was last updated')
    
    @receiver(post_save, sender=Business)
    def create_probabilistic_density_functions(sender, instance, **kwargs):
        distribution_types = [1, 2, 3]  # Normal, Exponential, Logarithmic
        names = ['Normal Distribution', 'Exponential Distribution', 'Log-Normal Distribution']            
        for distribution_type, name in zip(distribution_types, names):
            pdf = ProbabilisticDensityFunction(
                name=name,
                distribution_type=distribution_type,
                is_active=True,
                fk_business_id=instance.id
            )
            if distribution_type == 1:  # Normal distribution
                pdf.lambda_param = 1.0
                pdf.cumulative_distribution_function = 0.5
                pdf.mean_param = 450.0
                pdf.std_dev_param = 10.0
            elif distribution_type == 2:  # Exponential distribution
                pdf.lambda_param = 0.5
                pdf.cumulative_distribution_function = expon.cdf(2.0, scale=1/0.5)
                pdf.mean_param = 1 / 0.5
                pdf.std_dev_param = expon(scale=1/pdf.lambda_param).std()
            elif distribution_type == 3:  # Log-Normal distribution
                pdf.lambda_param = 0
                pdf.cumulative_distribution_function = lognorm.cdf(2.0, s=0.2, scale=np.exp(0.0))
                pdf.mean_param = 50.0
                pdf.std_dev_param = np.exp(0.0 + (0.2 ** 2) / 2)
            pdf.save()
    @receiver(post_save, sender=Business)
    def save_probabilistic_density_functions(sender, instance, **kwargs):
        # Asumiendo que 'fk_business_fdp' es el campo relacionado entre Business y ProbabilisticDensityFunction
        for probabilistic_density_function in instance.fk_business_fdp.all():
            probabilistic_density_function.is_active = instance.is_active
            probabilistic_density_function.save()
            print('Se guardaron las fdps')

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
        # Get the first ProbabilisticDensityFunction related to the Business
        fdp_instance = instance.fk_questionary.fk_product.fk_business.fk_business_fdp.first()
        if fdp_instance is not None:
            demand = [513, 820, 648, 720, 649, 414, 704, 814, 647, 934, 483, 882, 220, 419, 254, 781, 674, 498, 518, 948, 983, 154, 649, 625, 865, 800, 848, 783, 218, 906]
            # Create the Simulation
            current_date = datetime.now()
            simulation = Simulation(
                unit_time='day',
                fk_fdp=fdp_instance,
                demand_history=demand,
                quantity_time=30,
                fk_questionary_result=instance,
                is_active=True
            )
            simulation.save()
            create_random_result_simulations(simulation, current_date)

            def create_random_result_simulations(sender, instance, created, **kwargs):
                # Obtén la fecha inicial de la instancia de Simulation
                current_date = instance.date_created
                fk_simulation = Simulation.objects.get(id=instance.id)
                days = 30
                for _ in range(days):
                    demand_mean = 0
                    demand = [random.uniform(1000, 5000) for _ in range(10)]
                    demand_std_deviation = random.uniform(5, 20)            
                    variables = {
                        "CTR": [random.uniform(1000, 5000) for _ in range(10)],
                        "CTAI": [random.uniform(5000, 20000) for _ in range(10)],
                        "TPV": [random.uniform(1000, 5000) for _ in range(10)],
                        "TPPRO": [random.uniform(800, 4000) for _ in range(10)],
                        "DI": [random.uniform(50, 200) for _ in range(10)],
                        "VPC": [random.uniform(500, 1500) for _ in range(10)],
                        "IT": [random.uniform(5000, 20000) for _ in range(10)],
                        "GT": [random.uniform(3000, 12000) for _ in range(10)],
                        "TCA": [random.uniform(500, 2000) for _ in range(10)],
                        "NR": [random.uniform(0.1, 0.5) for _ in range(10)],
                        "GO": [random.uniform(1000, 5000) for _ in range(10)],
                        "GG": [random.uniform(1000, 5000) for _ in range(10)],
                        "GT": [random.uniform(2000, 8000) for _ in range(10)],
                        "CTT": [random.uniform(1000, 5000) for _ in range(10)],
                        "CPP": [random.uniform(500, 2000) for _ in range(10)],
                        "CPV": [random.uniform(500, 2000) for _ in range(10)],
                        "CPI": [random.uniform(500, 2000) for _ in range(10)],
                        "CPMO": [random.uniform(500, 2000) for _ in range(10)],
                        "CUP": [random.uniform(500, 2000) for _ in range(10)],
                        "FU": [random.uniform(0.1, 0.5) for _ in range(10)],
                        "TG": [random.uniform(2000, 8000) for _ in range(10)],
                        "IB": [random.uniform(3000, 12000) for _ in range(10)],
                        "MB": [random.uniform(2000, 8000) for _ in range(10)],
                        "RI": [random.uniform(1000, 5000) for _ in range(10)],
                        "RTI": [random.uniform(1000, 5000) for _ in range(10)],
                        "RTC": [random.uniform(0.1, 0.5) for _ in range(10)],
                        "PM": [random.uniform(500, 1500) for _ in range(10)],
                        "PE": [random.uniform(1000, 5000) for _ in range(10)],
                        "HO": [random.uniform(10, 50) for _ in range(10)],
                        "CHO": [random.uniform(1000, 5000) for _ in range(10)],
                        "CA": [random.uniform(1000, 5000) for _ in range(10)],
                    }
                    demand_mean = np.mean(demand)
                    means = {variable: np.mean(values) for variable, values in variables.items()}
                    result_simulation = ResultSimulation(
                        demand_mean=demand_mean,
                        demand_std_deviation=demand_std_deviation,
                        date=current_date,
                        variables=means,
                        fk_simulation=fk_simulation,
                        is_active=True
                    )
                    result_simulation.save()
    
    @receiver(post_save, sender=QuestionaryResult)
    def save_question(sender, instance, **kwargs):
        for simulate in instance.simulations.all():
            simulate.is_active = instance.is_active
            simulate.save()

# se tienen que guardar de 30 dias no 30 dias en una solafila o campo
class ResultSimulation(models.Model):
    demand_mean = models.DecimalField(max_digits=10, decimal_places=2,help_text='The mean of the demand')
    demand_std_deviation = models.DecimalField(max_digits=10, decimal_places=2,help_text='The standard deviation of the demand')
    date = models.DateField(null=True, blank=True, help_text='The date of the simulation')
    variables = models.JSONField(null=True, blank=True, help_text='The variables of the simulation')
    areas = models.JSONField(null=True, blank=True, help_text='The areas of the simulation')
    fk_simulation = models.ForeignKey(
        Simulation, 
        on_delete=models.CASCADE, 
        default=1, 
        related_name='fk_simulation_result_simulation',
        help_text='The simulation associated with the result')
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    # @receiver(post_save, sender=Simulation)
    
    def get_average_demand_by_date(self):
        average_demand_data = []
        # Asegúrate de que self.demand_mean sea una lista, incluso si contiene un solo elemento
        demand_mean_values = [self.demand_mean] if isinstance(self.demand_mean, Decimal) else self.demand_mean
        # Convertir self.date a un objeto datetime.date si no lo es
        date_obj = datetime.strptime(str(self.date), "%Y-%m-%d").date()
        # Recorre las fechas y calcula el promedio de la demanda
        for demand_mean_value in demand_mean_values:
            # Para calcular el promedio, simplemente usa 'demand_mean_value' directamente
            average_demand = float(demand_mean_value)
            # Añade el resultado a la lista
            average_demand_data.append({'date': date_obj, 'average_demand': average_demand})
        return average_demand_data

    