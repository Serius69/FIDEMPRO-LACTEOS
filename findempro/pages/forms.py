from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from business.models import Business
from product.models import Area, Product
from simulate.models import Simulation
from variable.models import Equation, Variable


class RegisterElementsForm(forms.Form):
    """
    Formulario para el registro de elementos del negocio
    """
    
    # Campos opcionales que se podrían agregar en el futuro
    business_name = forms.CharField(
        max_length=200,
        required=False,
        label=_('Nombre del Negocio'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Ej: Mi Empresa Láctea')
        }),
        help_text=_('Nombre personalizado para su negocio (opcional)')
    )
    
    business_location = forms.CharField(
        max_length=200,
        required=False,
        label=_('Ubicación'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Ej: La Paz, Bolivia')
        }),
        help_text=_('Ubicación de su negocio (opcional)')
    )
    
    simulation_days = forms.IntegerField(
        required=False,
        initial=30,
        min_value=7,
        max_value=365,
        label=_('Días de Simulación'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '7',
            'max': '365'
        }),
        help_text=_('Número de días para la simulación (7-365)')
    )
    
    accept_terms = forms.BooleanField(
        required=True,
        label=_('Acepto los términos y condiciones'),
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        error_messages={
            'required': _('Debe aceptar los términos y condiciones para continuar.')
        }
    )
    
    def clean_business_name(self):
        """Validar el nombre del negocio"""
        business_name = self.cleaned_data.get('business_name', '').strip()
        
        if business_name:
            # Validar longitud mínima
            if len(business_name) < 3:
                raise ValidationError(
                    _('El nombre del negocio debe tener al menos 3 caracteres.')
                )
            
            # Validar caracteres permitidos
            import re
            if not re.match(r'^[\w\s\-\.]+$', business_name):
                raise ValidationError(
                    _('El nombre del negocio solo puede contener letras, números, espacios, guiones y puntos.')
                )
                
        return business_name
    
    def clean_simulation_days(self):
        """Validar los días de simulación"""
        days = self.cleaned_data.get('simulation_days')
        
        if days is not None:
            if days < 7:
                raise ValidationError(
                    _('El número mínimo de días para la simulación es 7.')
                )
            elif days > 365:
                raise ValidationError(
                    _('El número máximo de días para la simulación es 365.')
                )
                
        return days or 30  # Valor por defecto
    
    def clean(self):
        """Validación general del formulario"""
        cleaned_data = super().clean()
        
        # Aquí se pueden agregar validaciones que involucren múltiples campos
        
        return cleaned_data


class SimulationConfigForm(forms.Form):
    """
    Formulario para configuración avanzada de simulación
    """
    
    UNIT_TIME_CHOICES = [
        ('day', _('Días')),
        ('week', _('Semanas')),
        ('month', _('Meses')),
    ]
    
    unit_time = forms.ChoiceField(
        choices=UNIT_TIME_CHOICES,
        initial='day',
        label=_('Unidad de Tiempo'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    quantity_time = forms.IntegerField(
        initial=30,
        min_value=1,
        max_value=365,
        label=_('Cantidad de Períodos'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '365'
        })
    )
    
    initial_demand = forms.IntegerField(
        required=False,
        min_value=100,
        max_value=10000,
        label=_('Demanda Inicial'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '100',
            'max': '10000',
            'placeholder': _('Ej: 3000')
        }),
        help_text=_('Demanda inicial estimada (opcional)')
    )
    
    demand_variation = forms.FloatField(
        required=False,
        initial=0.15,
        min_value=0.01,
        max_value=0.5,
        label=_('Variación de Demanda'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0.01',
            'max': '0.5',
            'step': '0.01',
            'placeholder': '0.15'
        }),
        help_text=_('Porcentaje de variación de demanda (1-50%)')
    )
    
    def clean_quantity_time(self):
        """Validar cantidad de tiempo según la unidad"""
        quantity = self.cleaned_data.get('quantity_time')
        unit_time = self.cleaned_data.get('unit_time')
        
        if quantity and unit_time:
            # Límites según la unidad de tiempo
            limits = {
                'day': (7, 365),
                'week': (4, 52),
                'month': (1, 12)
            }
            
            min_val, max_val = limits.get(unit_time, (1, 365))
            
            if quantity < min_val or quantity > max_val:
                raise ValidationError(
                    _(f'Para {unit_time}, el valor debe estar entre {min_val} y {max_val}.')
                )
                
        return quantity
    
    def get_total_days(self):
        """Calcular el total de días de la simulación"""
        quantity = self.cleaned_data.get('quantity_time', 30)
        unit_time = self.cleaned_data.get('unit_time', 'day')
        
        multipliers = {
            'day': 1,
            'week': 7,
            'month': 30
        }
        
        return quantity * multipliers.get(unit_time, 1)