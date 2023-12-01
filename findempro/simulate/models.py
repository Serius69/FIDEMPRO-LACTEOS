# Standard library imports
from datetime import datetime, timedelta
from decimal import Decimal
import math
import random
import json
# Third-party imports
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
import numpy as np
from scipy.stats import expon, lognorm, norm

# Local application imports
from business.models import Business
from product.models import Product, Area
from questionary.models import QuestionaryResult, Questionary, Answer, Question
from variable.models import Variable, EquationResult, Equation
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
    
    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'distribution_type': self.distribution_type,
            'lambda_param': self.lambda_param,
            'cumulative_distribution_function': self.cumulative_distribution_function,
            'mean_param': self.mean_param,
            'std_dev_param': self.std_dev_param,
            'fk_business': self.fk_business_id,
            'is_active': self.is_active,
            'date_created': self.date_created,
            'last_updated': self.last_updated
        }
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'distribution_type': self.distribution_type,
            'lambda_param': self.lambda_param,
            'cumulative_distribution_function': self.cumulative_distribution_function,
            'mean_param': self.mean_param,
            'std_dev_param': self.std_dev_param,
            'fk_business': self.fk_business.id,
            'is_active': self.is_active,
            'date_created': self.date_created.strftime('%Y-%m-%d %H:%M:%S'),
            'last_updated': self.last_updated.strftime('%Y-%m-%d %H:%M:%S'),
        }
    @receiver(post_save, sender=Business)
    def create_probabilistic_density_functions(sender, instance, **kwargs):
        distribution_types = [1, 2, 3]  # Normal, Exponential, Logarithmic
        names = ['Normal Distribution', 'Exponential Distribution', 'Log-Normal Distribution']

        
        for distribution_type, name in zip(distribution_types, names):
            defaults = {
                "name": name,
                "distribution_type": distribution_type,
                "is_active": True,
                "fk_business": instance,
            }

            if distribution_type == 1:  # Normal distribution
                defaults["lambda_param"] = 1.0
                defaults["cumulative_distribution_function"] = 0.5
                defaults["mean_param"] = 2500.0
                defaults["std_dev_param"] = 10.0
            elif distribution_type == 2:  # Exponential distribution
                defaults["lambda_param"] = 0.5
                defaults["cumulative_distribution_function"] = expon.cdf(2.0, scale=1/0.5)
                defaults["mean_param"] = 1 / 0.5
                defaults["std_dev_param"] = expon(scale=1/defaults["lambda_param"]).std()
            elif distribution_type == 3:  # Log-Normal distribution
                defaults["lambda_param"] = 0
                defaults["cumulative_distribution_function"] = lognorm.cdf(2.0, s=0.2, scale=np.exp(0.0))
                defaults["mean_param"] = 50.0
                defaults["std_dev_param"] = np.exp(0.0 + (0.2 ** 2) / 2)

            ProbabilisticDensityFunction.objects.get_or_create(distribution_type=distribution_type, fk_business=instance, defaults=defaults)
    @receiver(post_save, sender=Business)
    def save_probabilistic_density_functions(sender, instance, **kwargs):
        # Asumiendo que 'fk_business_fdp' es el campo relacionado entre Business y ProbabilisticDensityFunction
        for probabilistic_density_function in instance.fk_business_fdp.all():
            probabilistic_density_function.is_active = instance.is_active
            probabilistic_density_function.save()
        print('Se guardaron las fdps')

        # Desactivar todas las fdps si el business se desactiva
        if not instance.is_active:
            instance.fk_business_fdp.update(is_active=False)
            print('Se desactivaron las fdps debido a que el business se desactivó')

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
         # Verifica si ya existe una simulación para este cuestionario
        existing_simulation = Simulation.objects.filter(fk_questionary_result=instance).first()        
        if not existing_simulation:
            # Get the first ProbabilisticDensityFunction related to the Business
            fdp_instance = instance.fk_questionary.fk_product.fk_business.fk_business_fdp.first()
            if fdp_instance is not None:
                demand = [random.randint(1000, 5000) for _ in range(30)]
                
                simulation = Simulation(
                    unit_time='day',
                    fk_fdp=fdp_instance,
                    demand_history=demand,
                    quantity_time=30,
                    fk_questionary_result=instance,
                    is_active=True
                )
                simulation.save()
                # create_random_result_simulations(simulation)         
    # @receiver(post_save, sender=QuestionaryResult)
    # def save_simulation(sender, instance, **kwargs):
    #     for simulate in instance.simulations.all():
    #         simulate.is_active = instance.is_active
    #         simulate.save()

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
    def get_average_demand_by_date(self):
        average_demand_data = []
        # Asegúrate de que self.demand_mean sea una lista
        demand_mean_values = [self.demand_mean] if isinstance(self.demand_mean, Decimal) else self.demand_mean
        # Convertir self.date a un objeto datetime.date si no lo es
        date_obj = datetime.strptime(str(self.date), "%Y-%m-%d").date()
        # Recorre las fechas y calcula el promedio de la demanda
        for demand_mean_value in demand_mean_values:
            # Para calcular el promedio, simplemente usa 'demand_mean_value' directamente
            average_demand = float(demand_mean_value)
            # Añade el resultado a la lista
            average_demand_data.append({'date': date_obj.strftime("%Y-%m-%d"), 'average_demand': average_demand})
        
        return average_demand_data
    
    def get_variables(self):
        return self.variables
    
    # @receiver(post_save, sender=Simulation)
    def create_random_result_simulations(sender, instance, created, **kwargs):
        # Obtén la fecha inicial de la instancia de Simulation
        current_date = instance.date_created
        fk_simulation_instance = instance
        result_simulation = None
        print(f'Number of ResultSimulation instances to be created by the Simulate: {instance.quantity_time}')
        # por que se esta creando 4 veces ResultSimulation por Simulation
        for _ in range(instance.quantity_time):
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
            current_date += timedelta(days=1)
            result_simulation = ResultSimulation(
                demand_mean=demand_mean,
                demand_std_deviation=demand_std_deviation,
                date=current_date,
                variables=means,
                fk_simulation=fk_simulation_instance,
                is_active=True
            )
            result_simulation.save()
            # aqui acaba el for 
        # Verifica si ya existe una instancia de demand_instance
        demand_instance = None
        demand_predicted_instance = None

        # Verifica si ya existe una instancia de demand_instance
        if not Demand.objects.filter(fk_simulation=fk_simulation_instance, is_predicted=False).exists():
            demand_instance = Demand(
                quantity=fk_simulation_instance.demand_history[0],
                is_predicted=False,
                fk_simulation=fk_simulation_instance,
                fk_product=fk_simulation_instance.fk_questionary_result.fk_questionary.fk_product,
                is_active=True
            )
            demand_instance.save()

        # Verifica si ya existe una instancia de demand_predicted_instance
        if not Demand.objects.filter(fk_simulation=fk_simulation_instance, is_predicted=True).exists():
            demand_predicted_instance = Demand(
                quantity=demand_mean,  # Puedes ajustar esto según tus necesidades
                is_predicted=True,
                fk_simulation=fk_simulation_instance,
                fk_product=fk_simulation_instance.fk_questionary_result.fk_questionary.fk_product,
                is_active=True
            )
            demand_predicted_instance.save()

        # Verifica si tanto demand_instance como demand_predicted_instance tienen valores antes de crear DemandBehavior
        if demand_instance is not None and demand_predicted_instance is not None:
            # Verifica si ya existe una instancia de demand_behavior
            if not DemandBehavior.objects.filter(current_demand=demand_instance, predicted_demand=demand_predicted_instance).exists():
                demand_behavior = DemandBehavior(
                    current_demand=demand_instance,
                    predicted_demand=demand_predicted_instance,
                    is_active=True
                )
                demand_behavior.save()

class Demand(models.Model):
    quantity = models.IntegerField(default=0, help_text='The quantity of the demand')
    is_active = models.BooleanField(
        default=True, verbose_name='Active', help_text='Whether the business is active or not')
    date_created = models.DateTimeField(
        auto_now_add=True, blank=True, null=True, verbose_name='Date Created', help_text='The date the business was created')
    last_updated = models.DateTimeField(
        auto_now=True, blank=True, null=True, verbose_name='Last Updated', help_text='The date the business was last updated')
    is_predicted = models.BooleanField(
        default=False, verbose_name='Predicted', 
        help_text='Whether the demand is predicted or not')
    fk_simulation = models.ForeignKey(
        Simulation, 
        default=1, 
        on_delete=models.CASCADE, 
        related_name='fk_result_simulation_demand', 
        verbose_name='Result Simulation', 
        help_text='The result simulation associated with the demand')
    fk_product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='fk_product_demand_behavior', 
        default=1
    )
    def __str__(self):
        return f"Demand of {self.fk_product.name}"
    def create_demand(sender, instance, created, **kwargs):
        if created:
            product = Product.objects.get(pk=instance.pk)
            Demand.objects.create(
                fk_product_id = product.id
            )
    def save_demand(sender, instance, **kwargs):
        for business in instance.fk_product_demand.all():
            business.is_active = instance.is_active
            business.save()

class DemandBehavior(models.Model):
    current_demand = models.OneToOneField(
        Demand, 
        on_delete=models.CASCADE, 
        related_name='fk_demand_behavior_current_demand', 
        blank=  True,
    )
    predicted_demand = models.OneToOneField(
        Demand, 
        on_delete=models.CASCADE, 
        related_name='fk_demand_behavior_predicted_demand', 
        blank=True,
    )
    is_active = models.BooleanField(default=True, verbose_name='Active', help_text='Whether the business is active or not')
    date_created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name='Date Created', help_text='The date the business was created')
    last_updated = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name='Last Updated', help_text='The date the business was last updated')

    def __str__(self):
        return f"Demand Behavior of {self.product.name}"
    def calculate_elasticity(self):
            if self.current_demand and self.predicted_demand:
                current_quantity = self.current_demand.quantity
                predicted_quantity = self.predicted_demand.quantity
                percentage_change = ((predicted_quantity - current_quantity) / current_quantity) * 100
                if percentage_change > 0:
                    elasticity_type = 'Elastica'
                elif percentage_change < 0:
                    elasticity_type = 'Inelastica'
                else:
                    elasticity_type = 'Neutral'

                return elasticity_type, percentage_change
            else:
                # Devolver valores por defecto o manejar el caso donde no hay datos disponibles
                return None, None
    def create_demand_behavior(sender, instance, created, **kwargs):
        if created:
            demand = Product.objects.get(pk=instance.pk)
            if demand.is_predicted:
                DemandBehavior.objects.create(
                    predicted_demand_id = demand.id
                )
    def update_demand_behavior(self, new_demand):
        if new_demand < 0:
            raise ValueError("New demand cannot be negative")
        self.predicted_demand = new_demand
        self.quantity = new_demand
    def predict_demand_behavior(self, prediction_model):
        predicted_demand = self.quantity + 10
        return predicted_demand
