from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from product.models import Product
from .data.variable_test_data import variables_data
from sympy import symbols, Eq, solve
from .data.equation_test_data import equations_data
from product.models import Area
from django.core.exceptions import MultipleObjectsReturned
from django.http import Http404

class Variable(models.Model):
    name = models.CharField(max_length=70)
    initials = models.CharField(max_length=50, default='var1')
    TYPE_CHOICES = [
        (1, 'Exogena'),
        (2, 'Estado'),
        (3, 'Endogena'),
    ]    
    type = models.IntegerField(choices=TYPE_CHOICES, default=1, help_text='The type of the variable')
    unit = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(default="Description predetermined")
    image_src = models.ImageField(upload_to='images/variable', blank=True, null=True)
    fk_product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='fk_product_variable',
        help_text='The product associated with the variable',
        default=1)
    is_active = models.BooleanField(default=True, verbose_name='Active', help_text='Whether the variable is active or not')
    date_created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name='Date Created', help_text='The date the variable was created')
    last_updated = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name='Last Updated', help_text='The date the variable was last updated')

    def __str__(self):
        return self.name
    
    def get_photo_url(self):
        if self.image_src and hasattr(self.image_src, 'url'):
            return self.image_src.url
        else:
            return "/media/images/variable/variable-dummy-img.jpg"
    
    def get_type_display(self):
        """Return the display name for the type"""
        type_dict = dict(self.TYPE_CHOICES)
        return type_dict.get(self.type, 'Unknown')
    
    def get_parameters_display(self):
        """Return parameters for display"""
        params = []
        if self.unit:
            params.append(f"unit='{self.unit}'")
        if self.description:
            params.append(f"help_text='{self.description[:50]}...'")
        return ', '.join(params) if params else 'null=True, blank=True'

class Equation(models.Model):
    name = models.CharField(max_length=70)
    description = models.TextField(default="Description predetermined")
    expression = models.TextField(help_text='The expression of the equation', default='var1=var2+var3')
    fk_variable1 = models.ForeignKey(
        Variable,
        on_delete=models.CASCADE,
        related_name='fk_equations_variable1',
        help_text='The first variable associated with the equation'
    )
    fk_variable2 = models.ForeignKey(
        Variable,
        on_delete=models.CASCADE,
        related_name='equations_variable2',
        help_text='The second variable associated with the equation',
        null=True,
        blank=True
    )
    fk_variable3 = models.ForeignKey(
        Variable,
        on_delete=models.CASCADE,
        related_name='equations_variable3',
        help_text='The third variable associated with the equation',
        null=True,
        blank=True
    )
    fk_variable4 = models.ForeignKey(
        Variable,
        on_delete=models.CASCADE,
        related_name='equations_variable4',
        help_text='The fourth variable associated with the equation',
        null=True,
        blank=True
    )
    fk_variable5 = models.ForeignKey(
        Variable,
        on_delete=models.CASCADE,
        related_name='equations_variable5',
        help_text='The fifth variable associated with the equation',
        null=True,
        blank=True
    )
    fk_area = models.ForeignKey(
        Area,
        on_delete=models.CASCADE,
        related_name='area_equation',
        help_text='The area associated with the equation',
        null=True,  # Made nullable in case Area is optional
        blank=True
    )
    is_active = models.BooleanField(default=True, verbose_name='Active', help_text='Whether the equation is active or not')
    date_created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name='Date Created', help_text='The date the equation was created')
    last_updated = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name='Last Updated', help_text='The date the equation was last updated')
    
    def __str__(self):
        return self.name

class EquationResult(models.Model):
    fk_equation = models.ForeignKey(
        Equation,
        on_delete=models.CASCADE,
        related_name='equation_results',
        help_text='The equation associated with the result'
    )
    result = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    is_active = models.BooleanField(
        default=True,
        verbose_name='Active',
        help_text='Whether the equation result is active or not'
    )
    date_created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Date Created',
        help_text='The date the equation result was created'
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name='Last Updated',
        help_text='The date the equation result was last updated'
    )

    def __str__(self) -> str:
        return f"Result for Equation {self.fk_equation.name}"