from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from product.models import Product
from .variables_data import variables_data
from sympy import symbols, Eq, solve
from .equations_data import equations_data
from product.models import Area
class Variable(models.Model):
    name = models.CharField(max_length=70)
    initials = models.CharField(max_length=7, default="var")
    TYPE_CHOICES = [
        ('Estado', 'Estado'),
        ('Exogena', 'Exogena'),
        ('Endogena', 'Endogena'),
    ]    
    PARAMETER_CHOICES = [
        ('param1', 'Parameter 1'),
        ('param2', 'Parameter 2'),
    ]
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='Estado')
    parameters = models.CharField(max_length=20, choices=PARAMETER_CHOICES, default='param1')
    unit = models.CharField(max_length=50)
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

    def get_image_url(self):
        if self.image_src and hasattr(self.image_src, 'url'):
            return self.image_src.url
        else:
            return "/media/images/variable/variable-dummy-img.jpg"

@receiver(post_save, sender=Product)
def create_variables(sender, instance, created, **kwargs):
    if created:
        for data in variables_data:
            Variable.objects.create(
                name=data['name'],
                initials=data['initials'],
                type=data['type'],
                unit=data['unit'],
                description=data['description'],
                fk_product=instance,
                is_active=True
            )
@receiver(post_save, sender=Product)
def save_variables(sender, instance, **kwargs):
    for variable in instance.fk_product_variable.all():
        variable.is_active = instance.is_active
        variable.save()

class Equation(models.Model):
    name = models.CharField(max_length=70)
    expression = models.TextField()
    
    fk_variable1 = models.ForeignKey(
        Variable,
        on_delete=models.CASCADE,
        related_name='equations_variable1',
        help_text='The first variable associated with the equation'
    )
    
    fk_variable2 = models.ForeignKey(
        Variable,
        on_delete=models.CASCADE,
        related_name='equations_variable2',
        help_text='The second variable associated with the equation',
        null=True
    )
    
    fk_variable3 = models.ForeignKey(
        Variable,
        on_delete=models.CASCADE,
        related_name='equations_variable3',
        help_text='The third variable associated with the equation',
        null=True
    )
    
    fk_variable4 = models.ForeignKey(
        Variable,
        on_delete=models.CASCADE,
        related_name='equations_variable4',
        help_text='The fourth variable associated with the equation',
        null=True
    )
    
    fk_variable5 = models.ForeignKey(
        Variable,
        on_delete=models.CASCADE,
        related_name='equations_variable5',
        help_text='The fifth variable associated with the equation',
        null=True
    )
    
    area = models.ForeignKey(
        Area,
        on_delete=models.CASCADE,
        related_name='area_equation',
        help_text='The area associated with the equation',
    )
    is_active = models.BooleanField(default=True, verbose_name='Active', help_text='Whether the equation is active or not')
    date_created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name='Date Created', help_text='The date the equation was created')
    last_updated = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name='Last Updated', help_text='The date the equation was last updated')

    def calculate(self):
        x, y, z = symbols('x y z')
        equation_str = self.expression.replace('variable1', str(self.variable1.initials)).replace('variable2', str(self.variable2.initials)).replace('variable3', str(self.variable3.initials))
        
        try:
            equation = Eq(eval(equation_str), 0)
            solution = solve(equation, x, y, z)
            return solution
        except Exception as e:
            # Manejar errores en la evaluación de la ecuación
            return f"Error evaluating equation: {str(e)}"
    @receiver(post_save, sender=Variable)
    def create_equations(sender, instance, created, **kwargs):
        if created:
            for data in equations_data:
                Variable.objects.create(
                    name=data['name'],
                    expression=data['expression'],
                    variable1=data['variable1'],
                    unit=data['unit'],
                    description=data['description'],
                    fk_product=instance,
                    is_active=True
                )

    @receiver(post_save, sender=Variable)
    def save_equations(sender, instance, **kwargs):
        for equation in instance.fk_variable_equation.all():
            equation.is_active = instance.is_active
            equation.save()
            
class EquationResult(models.Model):
    fk_equation = models.ForeignKey(
        Equation,
        on_delete=models.CASCADE,
        related_name='equation_results',
        help_text='The equation associated with the result'
    )
    result = models.TextField()
    is_active = models.BooleanField(
        default=True,
        verbose_name='Active',
        help_text='Whether the equation is active or not'
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
        return f"Result for Equation {self.fk_equation.id}"

    class Meta:
        verbose_name = 'Equation Result'
        verbose_name_plural = 'Equation Results'