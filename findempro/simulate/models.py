# models.py
from datetime import datetime, timedelta
from decimal import Decimal
import json
import math
import random

import numpy as np
from scipy.stats import expon, lognorm, norm, gamma, uniform

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.exceptions import ValidationError

from business.models import Business
from product.models import Product, Area
from questionary.models import QuestionaryResult
from variable.models import Variable


class ProbabilisticDensityFunction(models.Model):
    """Model for storing probability density function parameters"""
    
    DISTRIBUTION_TYPES = [
        (1, 'Normal'),
        (2, 'Exponential'),
        (3, 'Log-Norm'),
        (4, 'Gamma'),  # Nueva distribución Gamma
        (5, 'Uniform'),  # Nueva distribución Uniforme
    ]
    
    name = models.CharField(
        max_length=100, 
        help_text='The name of the distribution', 
        default='Distribution'
    )
    distribution_type = models.IntegerField(
        choices=DISTRIBUTION_TYPES, 
        default=1, 
        help_text='The type of the distribution'
    )
    # Parámetros para diferentes distribuciones
    lambda_param = models.FloatField(
        null=True, 
        blank=True, 
        validators=[MinValueValidator(0.001)], 
        help_text='Lambda parameter for exponential distribution'
    )
    mean_param = models.FloatField(
        null=True, 
        blank=True, 
        help_text='Mean parameter for normal distribution'
    )
    std_dev_param = models.FloatField(
        null=True, 
        blank=True, 
        validators=[MinValueValidator(0.001)], 
        help_text='Standard deviation parameter'
    )
    # Nuevos parámetros para Gamma
    shape_param = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.001)],
        help_text='Shape parameter (α) for gamma distribution'
    )
    scale_param = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.001)],
        help_text='Scale parameter (β) for gamma distribution'
    )
    # Parámetros para Uniforme
    min_param = models.FloatField(
        null=True,
        blank=True,
        help_text='Minimum value for uniform distribution'
    )
    max_param = models.FloatField(
        null=True,
        blank=True,
        help_text='Maximum value for uniform distribution'
    )
    
    cumulative_distribution_function = models.FloatField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text='Cumulative distribution function value'
    )
    fk_business = models.ForeignKey(
        Business, 
        on_delete=models.CASCADE, 
        related_name='probability_distributions', 
        help_text='The business associated with this distribution'
    )
    is_active = models.BooleanField(
        default=True, 
        help_text='Whether the distribution is active'
    )
    date_created = models.DateTimeField(
        default=timezone.now, 
        help_text='Creation date'
    )
    last_updated = models.DateTimeField(
        auto_now=True, 
        help_text='Last update date'
    )
    
    class Meta:
        verbose_name = "Probability Density Function"
        verbose_name_plural = "Probability Density Functions"
        unique_together = ['distribution_type', 'fk_business']
        ordering = ['-date_created']
    
    def __str__(self):
        return f"{self.name} - {self.fk_business.name}"
    
    def clean(self):
        """Validar datos del modelo según el tipo de distribución"""
        super().clean()
        
        errors = {}
        
        if self.distribution_type == 1:  # Normal
            if self.mean_param is None:
                errors['mean_param'] = "La distribución Normal requiere el parámetro de media"
            if self.std_dev_param is None:
                errors['std_dev_param'] = "La distribución Normal requiere el parámetro de desviación estándar"
            elif self.std_dev_param <= 0:
                errors['std_dev_param'] = "La desviación estándar debe ser mayor que 0"
                
        elif self.distribution_type == 2:  # Exponential
            if self.lambda_param is None:
                errors['lambda_param'] = "La distribución Exponencial requiere el parámetro lambda"
            elif self.lambda_param <= 0:
                errors['lambda_param'] = "Lambda debe ser mayor que 0"
                
        elif self.distribution_type == 3:  # Log-Normal
            if self.mean_param is None:
                errors['mean_param'] = "La distribución Log-Normal requiere el parámetro de media"
            if self.std_dev_param is None:
                errors['std_dev_param'] = "La distribución Log-Normal requiere el parámetro de desviación estándar"
            elif self.std_dev_param <= 0:
                errors['std_dev_param'] = "La desviación estándar debe ser mayor que 0"
                
        elif self.distribution_type == 4:  # Gamma
            if self.shape_param is None:
                errors['shape_param'] = "La distribución Gamma requiere el parámetro de forma (α)"
            elif self.shape_param <= 0:
                errors['shape_param'] = "El parámetro de forma debe ser mayor que 0"
            if self.scale_param is None:
                errors['scale_param'] = "La distribución Gamma requiere el parámetro de escala (β)"
            elif self.scale_param <= 0:
                errors['scale_param'] = "El parámetro de escala debe ser mayor que 0"
                
        elif self.distribution_type == 5:  # Uniform
            if self.min_param is None:
                errors['min_param'] = "La distribución Uniforme requiere el valor mínimo"
            if self.max_param is None:
                errors['max_param'] = "La distribución Uniforme requiere el valor máximo"
            elif self.min_param is not None and self.max_param is not None:
                if self.min_param >= self.max_param:
                    errors['max_param'] = "El valor máximo debe ser mayor que el valor mínimo"
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def to_json(self):
        """Convert model to JSON representation"""
        return {
            'id': self.id,
            'name': self.name,
            'distribution_type': self.distribution_type,
            'distribution_type_display': self.get_distribution_type_display(),
            'lambda_param': self.lambda_param,
            'cumulative_distribution_function': self.cumulative_distribution_function,
            'mean_param': self.mean_param,
            'std_dev_param': self.std_dev_param,
            'fk_business': self.fk_business_id,
            'is_active': self.is_active,
            'date_created': self.date_created.isoformat() if self.date_created else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
    
    def to_dict(self):
        """Convert model to dictionary representation"""
        return {
            'id': self.id,
            'name': self.name,
            'distribution_type': self.distribution_type,
            'lambda_param': self.lambda_param,
            'cumulative_distribution_function': self.cumulative_distribution_function,
            'mean_param': self.mean_param,
            'std_dev_param': self.std_dev_param,
            'fk_business': self.fk_business.id,
            'business_name': self.fk_business.name,
            'is_active': self.is_active,
            'date_created': self.date_created.strftime('%Y-%m-%d %H:%M:%S') if self.date_created else None,
            'last_updated': self.last_updated.strftime('%Y-%m-%d %H:%M:%S') if self.last_updated else None,
        }
    
    def get_scipy_distribution(self):
        """Obtener objeto de distribución scipy según los parámetros"""
        try:
            if self.distribution_type == 1:  # Normal
                return norm(loc=self.mean_param, scale=self.std_dev_param)
            elif self.distribution_type == 2:  # Exponential
                return expon(scale=1/self.lambda_param)
            elif self.distribution_type == 3:  # Log-Normal
                return lognorm(s=self.std_dev_param, scale=np.exp(self.mean_param))
            elif self.distribution_type == 4:  # Gamma
                # En scipy, gamma usa 'a' para shape y 'scale' para scale
                return gamma(a=self.shape_param, scale=self.scale_param)
            elif self.distribution_type == 5:  # Uniform
                return uniform(loc=self.min_param, scale=self.max_param - self.min_param)
            else:
                raise ValueError(f"Tipo de distribución desconocido: {self.distribution_type}")
        except Exception as e:
            raise ValidationError(f"Error creando distribución: {str(e)}")
    
    def calculate_pdf(self, x_values):
        """Calculate probability density function values"""
        distribution = self.get_scipy_distribution()
        return distribution.pdf(x_values)
    
    def calculate_cdf(self, x_values):
        """Calculate cumulative distribution function values"""
        distribution = self.get_scipy_distribution()
        return distribution.cdf(x_values)
    
    def generate_random_samples(self, n_samples):
        """Generar muestras aleatorias de la distribución"""
        try:
            distribution = self.get_scipy_distribution()
            return distribution.rvs(size=n_samples)
        except Exception as e:
            raise ValidationError(f"Error generando muestras: {str(e)}")
    def get_distribution_info(self):
        """Obtener información detallada sobre la distribución"""
        info = {
            'name': self.name,
            'type': self.get_distribution_type_display(),
            'parameters': {}
        }
        
        if self.distribution_type == 1:  # Normal
            info['parameters'] = {
                'mean': self.mean_param,
                'std_dev': self.std_dev_param
            }
            info['theoretical_mean'] = self.mean_param
            info['theoretical_variance'] = self.std_dev_param ** 2
            
        elif self.distribution_type == 2:  # Exponential
            info['parameters'] = {'lambda': self.lambda_param}
            info['theoretical_mean'] = 1 / self.lambda_param
            info['theoretical_variance'] = 1 / (self.lambda_param ** 2)
            
        elif self.distribution_type == 3:  # Log-Normal
            info['parameters'] = {
                'log_mean': self.mean_param,
                'log_std_dev': self.std_dev_param
            }
            # Media y varianza de la distribución log-normal
            info['theoretical_mean'] = np.exp(self.mean_param + (self.std_dev_param ** 2) / 2)
            info['theoretical_variance'] = (np.exp(self.std_dev_param ** 2) - 1) * np.exp(2 * self.mean_param + self.std_dev_param ** 2)
            
        elif self.distribution_type == 4:  # Gamma
            info['parameters'] = {
                'shape': self.shape_param,
                'scale': self.scale_param
            }
            info['theoretical_mean'] = self.shape_param * self.scale_param
            info['theoretical_variance'] = self.shape_param * (self.scale_param ** 2)
            
        elif self.distribution_type == 5:  # Uniform
            info['parameters'] = {
                'min': self.min_param,
                'max': self.max_param
            }
            info['theoretical_mean'] = (self.min_param + self.max_param) / 2
            info['theoretical_variance'] = ((self.max_param - self.min_param) ** 2) / 12
        
        return info

    def validate_sample_data(self, data):
        """Validar si los datos de muestra son apropiados para esta distribución"""
        if not isinstance(data, (list, np.ndarray)):
            raise ValidationError("Los datos deben ser una lista o array numpy")
        
        if len(data) < 10:
            raise ValidationError("Se requieren al menos 10 puntos de datos")
        
        data_array = np.array(data)
        
        # Validaciones específicas por distribución
        if self.distribution_type in [2, 3, 4]:  # Exponential, Log-Normal, Gamma
            if np.any(data_array <= 0):
                dist_name = self.get_distribution_type_display()
                raise ValidationError(f"La distribución {dist_name} requiere valores positivos")
        
        # Validar rango razonable
        data_range = np.max(data_array) - np.min(data_array)
        if data_range == 0:
            raise ValidationError("Los datos no tienen variabilidad")
        
        return True
    
class Simulation(models.Model):
    """Model for storing simulation configurations and metadata"""
    
    TIME_UNITS = [
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
    ]
    
    quantity_time = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(365)],
        help_text='Number of time units for simulation'
    )
    unit_time = models.CharField(
        max_length=20,
        choices=TIME_UNITS,
        default='days',
        help_text='Unit of time for simulation'
    )
    fk_fdp = models.ForeignKey(
        ProbabilisticDensityFunction, 
        on_delete=models.CASCADE,
        related_name='simulations',
        help_text='Probability distribution function used'
    )
    demand_history = models.JSONField(
        help_text='Historical demand data (JSON array of numbers)'
    )
    fk_questionary_result = models.ForeignKey(
        QuestionaryResult,
        on_delete=models.CASCADE,
        related_name='simulations',
        help_text='Associated questionary result'
    )
    confidence_level = models.FloatField(
        default=0.95,
        validators=[MinValueValidator(0.1), MaxValueValidator(0.99)],
        help_text='Confidence level for statistical analysis'
    )
    random_seed = models.IntegerField(
        null=True,
        blank=True,
        help_text='Random seed for reproducible results'
    )
    is_completed = models.BooleanField(
        default=False,
        help_text='Whether the simulation has been completed'
    )
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Simulation"
        verbose_name_plural = "Simulations"
        ordering = ['-date_created']
    
    def __str__(self):
        return f"Simulation {self.id} - {self.fk_questionary_result.fk_questionary.fk_product.name}"
    
    def clean(self):
        """Validate simulation data"""
        super().clean()
        
        # Validate demand history
        if self.demand_history:
            try:
                if isinstance(self.demand_history, str):
                    demand_data = json.loads(self.demand_history)
                else:
                    demand_data = self.demand_history
                
                if not isinstance(demand_data, list):
                    raise ValidationError("Demand history must be a list")
                
                if len(demand_data) < 10:
                    raise ValidationError("Demand history must have at least 10 data points")
                
                # Validate all values are numbers
                for i, value in enumerate(demand_data):
                    if not isinstance(value, (int, float)) or value < 0:
                        raise ValidationError(f"Invalid demand value at position {i}: {value}")
                        
            except (json.JSONDecodeError, TypeError) as e:
                raise ValidationError(f"Invalid demand history format: {e}")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def get_demand_history_array(self):
        """Get demand history as numpy array"""
        if isinstance(self.demand_history, str):
            demand_data = json.loads(self.demand_history)
        else:
            demand_data = self.demand_history
        return np.array(demand_data, dtype=float)
    
    def get_demand_statistics(self):
        """Calculate statistics for demand history"""
        demand_array = self.get_demand_history_array()
        return {
            'mean': np.mean(demand_array),
            'std': np.std(demand_array),
            'min': np.min(demand_array),
            'max': np.max(demand_array),
            'median': np.median(demand_array),
            'count': len(demand_array)
        }
    
    @property
    def duration_in_days(self):
        """Calculate total duration in days"""
        if self.unit_time == 'days':
            return self.quantity_time
        elif self.unit_time == 'weeks':
            return self.quantity_time * 7
        elif self.unit_time == 'months':
            return self.quantity_time * 30
        return self.quantity_time


class ResultSimulation(models.Model):
    """Model for storing daily simulation results"""
    
    demand_mean = models.DecimalField(
        max_digits=12, 
        decimal_places=4,
        help_text='Mean demand for this day'
    )
    demand_std_deviation = models.DecimalField(
        max_digits=12, 
        decimal_places=4,
        help_text='Standard deviation of demand'
    )
    date = models.DateField(
        help_text='Date of this simulation result'
    )
    variables = models.JSONField(
        default=dict,
        help_text='Variable values for this day'
    )
    areas = models.JSONField(
        default=dict,
        blank=True,
        help_text='Area-specific results'
    )
    confidence_intervals = models.JSONField(
        default=dict,
        blank=True,
        help_text='Confidence intervals for key metrics'
    )
    fk_simulation = models.ForeignKey(
        Simulation, 
        on_delete=models.CASCADE, 
        related_name='results',
        help_text='Parent simulation'
    )
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)   
    
    class Meta:
        verbose_name = "Simulation Result"
        verbose_name_plural = "Simulation Results"
        unique_together = ['fk_simulation', 'date']
        ordering = ['fk_simulation', 'date']
    
    def __str__(self):
        return f"Result {self.fk_simulation.id} - {self.date}"
    
    def get_average_demand_by_date(self):
        """Get average demand data formatted for charts"""
        return [{
            'date': self.date.strftime("%Y-%m-%d"), 
            'average_demand': float(self.demand_mean)
        }]
    
    def get_variables(self):
        """Get variables dictionary"""
        return self.variables or {}
    
    def get_variable_value(self, variable_name, default=0):
        """Get specific variable value with default"""
        variables = self.get_variables()
        return variables.get(variable_name, default)
    
    def calculate_demand_variance(self):
        """Calculate demand variance"""
        return float(self.demand_std_deviation) ** 2
    
    def is_within_confidence_interval(self, variable_name, value, confidence_level=0.95):
        """Check if value is within confidence interval for variable"""
        if not self.confidence_intervals or variable_name not in self.confidence_intervals:
            return None
        
        ci = self.confidence_intervals[variable_name]
        return ci.get('lower', float('-inf')) <= value <= ci.get('upper', float('inf'))


class Demand(models.Model):
    """Model for storing demand data points"""
    
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Demand quantity'
    )
    is_predicted = models.BooleanField(
        default=False,
        help_text='Whether this is a predicted value'
    )
    confidence_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text='Confidence score for predictions'
    )
    fk_simulation = models.ForeignKey(
        Simulation, 
        on_delete=models.CASCADE, 
        related_name='demands',
        help_text='Associated simulation'
    )
    fk_product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='demands'
    )
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Demand"
        verbose_name_plural = "Demands"
        ordering = ['-date_created']
    
    def __str__(self):
        prediction_text = "Predicted" if self.is_predicted else "Historical"
        return f"{prediction_text} Demand: {self.quantity} for {self.fk_product.name}"
    
    def clean(self):
        """Validate demand data"""
        super().clean()
        if self.quantity < 0:
            raise ValidationError("Demand quantity cannot be negative")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class DemandBehavior(models.Model):
    """Model for analyzing demand behavior patterns"""
    
    ELASTICITY_TYPES = [
        ('elastic', 'Elastic'),
        ('inelastic', 'Inelastic'), 
        ('neutral', 'Neutral'),
        ('unknown', 'Unknown')
    ]
    
    current_demand = models.OneToOneField(
        Demand, 
        on_delete=models.CASCADE, 
        related_name='current_behavior'
    )
    predicted_demand = models.OneToOneField(
        Demand, 
        on_delete=models.CASCADE, 
        related_name='predicted_behavior'
    )
    elasticity_type = models.CharField(
        max_length=20,
        choices=ELASTICITY_TYPES,
        default='unknown',
        help_text='Type of demand elasticity'
    )
    percentage_change = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
        help_text='Percentage change in demand'
    )
    elasticity_coefficient = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
        help_text='Calculated elasticity coefficient'
    )
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Demand Behavior"
        verbose_name_plural = "Demand Behaviors"
    
    def __str__(self):
        return f"Demand Behavior: {self.elasticity_type}"
    
    def calculate_elasticity(self):
        """Calculate demand elasticity and update fields"""
        if not (self.current_demand and self.predicted_demand):
            return None, None
        
        current_quantity = float(self.current_demand.quantity)
        predicted_quantity = float(self.predicted_demand.quantity)
        
        if current_quantity == 0:
            return None, None
        
        # Calculate percentage change
        percentage_change = ((predicted_quantity - current_quantity) / current_quantity) * 100
        
        # Determine elasticity type
        if abs(percentage_change) > 10:  # More than 10% change
            elasticity_type = 'elastic'
        elif abs(percentage_change) < 1:  # Less than 1% change
            elasticity_type = 'inelastic'
        else:
            elasticity_type = 'neutral'
        
        # Update fields
        self.percentage_change = Decimal(str(round(percentage_change, 4)))
        self.elasticity_type = elasticity_type
        
        # Calculate elasticity coefficient (simplified)
        if current_quantity != predicted_quantity:
            self.elasticity_coefficient = Decimal(str(round(percentage_change / 1, 4)))  # Simplified calculation
        
        return elasticity_type, float(percentage_change)
    
    def save(self, *args, **kwargs):
        # Auto-calculate elasticity when saving
        self.calculate_elasticity()
        super().save(*args, **kwargs)
    
    def get_demand_trend(self):
        """Get demand trend direction"""
        if not self.percentage_change:
            return 'unknown'
        
        if self.percentage_change > 0:
            return 'increasing'
        elif self.percentage_change < 0:
            return 'decreasing'
        else:
            return 'stable'
    
    def predict_future_demand(self, periods=1):
        """Simple prediction based on current trend"""
        if not self.percentage_change:
            return None
        
        current_quantity = float(self.predicted_demand.quantity)
        growth_rate = float(self.percentage_change) / 100
        
        future_demand = current_quantity * ((1 + growth_rate) ** periods)
        return max(0, future_demand)  # Ensure non-negative


# Signal handlers actualizados
@receiver(post_save, sender=Business)
def create_probabilistic_density_functions(sender, instance, created, **kwargs):
    """Crear distribuciones de probabilidad por defecto cuando se crea un negocio"""
    if not created:
        return
    
    distribution_configs = [
        {
            'name': 'Distribución Normal',
            'distribution_type': 1,
            'mean_param': 2500.0,
            'std_dev_param': 10.0
        },
        {
            'name': 'Distribución Exponencial', 
            'distribution_type': 2,
            'lambda_param': 0.5,
        },
        {
            'name': 'Distribución Log-Normal',
            'distribution_type': 3,
            'mean_param': 50.0,
            'std_dev_param': 0.2
        },
        {
            'name': 'Distribución Gamma',
            'distribution_type': 4,
            'shape_param': 2.0,  # α = 2
            'scale_param': 1000.0  # β = 1000
        },
        {
            'name': 'Distribución Uniforme',
            'distribution_type': 5,
            'min_param': 1000.0,
            'max_param': 4000.0
        }
    ]
    
    for config in distribution_configs:
        # Calcular CDF para x=2.0 como ejemplo
        config['fk_business'] = instance
        config['is_active'] = True
        
        # Calcular CDF inicial
        try:
            pdf_instance = ProbabilisticDensityFunction(**config)
            distribution = pdf_instance.get_scipy_distribution()
            config['cumulative_distribution_function'] = distribution.cdf(2.0)
        except:
            config['cumulative_distribution_function'] = 0.5  # Valor por defecto
        
        ProbabilisticDensityFunction.objects.get_or_create(
            distribution_type=config['distribution_type'],
            fk_business=instance,
            defaults=config
        )


@receiver(post_save, sender=Business)
def update_business_distributions(sender, instance, **kwargs):
    """Update distributions when business is modified"""
    # Update all related distributions' active status
    instance.probability_distributions.update(is_active=instance.is_active)
    
    if not instance.is_active:
        # Also deactivate related simulations
        simulations = Simulation.objects.filter(
            fk_questionary_result__fk_questionary__fk_product__fk_business=instance
        )
        simulations.update(is_active=False)


@receiver(post_save, sender=Simulation)
def update_simulation_results(sender, instance, **kwargs):
    """Update related results when simulation is modified"""
    if not instance.is_active:
        instance.results.update(is_active=False)
        instance.demands.update(is_active=False)