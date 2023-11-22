from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from product.models import Product
from .variables_data import variables_data
from sympy import symbols, Eq, solve
from .equations_data import equations_data
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
    type = models.IntegerField(default=1, help_text='The type of the variable')
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

    def get_image_url(self):
        if self.image_src and hasattr(self.image_src, 'url'):
            return self.image_src.url
        else:
            return "/media/images/variable/variable-dummy-img.jpg"
    @receiver(post_save, sender=Product)
    def create_variables(sender, instance, created, **kwargs):
        if created:
            product = Product.objects.get(pk=instance.pk)
            for data in variables_data:
                Variable.objects.create(
                    name=data.get('name'),
                    initials=data.get('initials'),
                    type=data.get('type'),
                    unit=data.get('unit'),
                    image_src=f"/media/images/variable/{data.get('name')}.jpg",
                    description=data.get('description'),
                    fk_product_id=product.id,
                    is_active=True
                )
                
            # Verificar si todas las variables se han creado
            def create_equations(instance):
                    for data in equations_data:
                        def get_variable(variable_name):
                            try:
                                if variable_name == None:
                                    return None
                                return Variable.objects.get(initials=variable_name)
                            except Variable.DoesNotExist:
                                raise Http404(f"Variable with initials '{variable_name}' does not exist.")
                            except Variable.MultipleObjectsReturned:
                                return Variable.objects.filter(initials=variable_name).first()
                            
                        def get_area(area_name):
                            try:
                                return Area.objects.get(name=area_name)
                            except Area.DoesNotExist:
                                raise Http404(f"Area with name '{area_name}' does not exist.")
                            except Area.MultipleObjectsReturned:
                                return Area.objects.filter(name=area_name).first()
                            
                        variable1 = get_variable(data['variable1'])
                        variable2 = get_variable(data['variable2'])
                        variable3 = get_variable(data['variable3'])
                        variable4 = get_variable(data.get('variable4', None))
                        variable5 = get_variable(data.get('variable5', None))
                        area = get_area(data['area'])

                        Equation.objects.create(
                            name=data['name'],
                            description=data['description'],
                            expression=data['expression'],
                            fk_variable1=variable1,
                            fk_variable2=variable2,
                            fk_variable3=variable3,
                            fk_variable4=variable4,
                            fk_variable5=variable5,
                            fk_area=area,                            
                            is_active=True
                        )
            variables_created = Variable.objects.filter(fk_product_id=product.id).count()
            total_variables_expected = len(variables_data)

            if variables_created == total_variables_expected:
                print(f"Todas las variables se han creado correctamente para el producto {product.id}.")
                create_equations(instance)
            else:
                print(f"No se han creado todas las variables para el producto {product.id}.")
    @receiver(post_save, sender=Product)
    def save_variables(sender, instance, **kwargs):
        for variable in instance.fk_product_variable.all():
            variable.is_active = instance.is_active
            variable.save()
class Equation(models.Model):
    name = models.CharField(max_length=70)
    description = models.TextField(default="Description predetermined")
    expression = models.TextField(help_text='The expression of the equation',default='var1=var2+var3')
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
        null=True
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
    )
    is_active = models.BooleanField(default=True, verbose_name='Active', help_text='Whether the equation is active or not')
    date_created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name='Date Created', help_text='The date the equation was created')
    last_updated = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name='Last Updated', help_text='The date the equation was last updated')
    # CUANDO SE CREA UNA VARERIABLE SE MANDA UN SIGNAL QUE HACE QUE CREE LAS ECUACIONES PERO ESTO ESTA MAS SE DEBE CREAR CUANDO YA SE TIENE TODAS LAS VARIABLES YA CREADAS NO SOLO LA PRIMERA
    # @receiver(post_save, sender=Product)
    
    # @receiver(post_save, sender=Variable)
    def save_equations(instance, **kwargs):
        for equation in instance.fk_equations_variable1.all():
            equation.is_active = instance.is_active
            equation.save()
            
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
        return f"Result for Equation {self.fk_equation.name}"
    class Meta:
        verbose_name = 'Equation Result'
        verbose_name_plural = 'Equation Results'