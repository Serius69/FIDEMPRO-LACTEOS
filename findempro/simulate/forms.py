from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import Simulation, ProbabilisticDensityFunction
from questionary.models import QuestionaryResult
import json


class SimulationForm(forms.ModelForm):
    """Formulario original - mantenido sin cambios para compatibilidad"""
    
    class Meta:
        model = Simulation
        fields = [
                'quantity_time',    
                'unit_time', 
                'fk_fdp', 
                'fk_questionary_result', 
                'demand_history']


class SimulationConfigForm(forms.Form):
    """Formulario para configuración inicial - SOLO lo que necesita la vista mejorada"""
    
    selected_questionary_result = forms.ModelChoiceField(
        queryset=QuestionaryResult.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-choices': 'true',
            'data-choices-sorting': 'true',
            'required': 'true'
        }),
        empty_label="Seleccione un cuestionario...",
        required=True
    )
    
    selected_quantity_time = forms.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(365)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,
            'max': 365,
            'placeholder': 'Ej: 30',
            'required': 'true'
        }),
        required=True
    )
    
    selected_unit_time = forms.ChoiceField(
        choices=Simulation.TIME_UNITS,
        initial='days',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': 'true'
        }),
        required=True
    )
    
    # Campos opcionales que pueden estar en tu template
    confidence_level = forms.FloatField(
        initial=0.95,
        required=False,
        widget=forms.Select(
            choices=[
                (0.90, '90%'),
                (0.95, '95%'),
                (0.99, '99%')
            ],
            attrs={'class': 'form-select'}
        )
    )
    
    random_seed = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 12345'
        })
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Usar el mismo filtro que probablemente ya tienes en tu código
            self.fields['selected_questionary_result'].queryset = (
                QuestionaryResult.objects.filter(
                    is_active=True,
                    fk_questionary__fk_product__fk_business__fk_user=user
                ).select_related(
                    'fk_questionary__fk_product__fk_business'
                ).order_by('-date_created')
            )

    def clean_selected_quantity_time(self):
        """Validación básica - compatible con tu lógica existente"""
        quantity = self.cleaned_data.get('selected_quantity_time')
        
        if quantity is None:
            raise ValidationError("La duración es requerida.")
        
        if quantity < 1 or quantity > 365:
            raise ValidationError("La duración debe estar entre 1 y 365.")
        
        return quantity

    def clean_selected_questionary_result(self):
        """Validación básica - compatible con tu lógica existente"""
        questionary = self.cleaned_data.get('selected_questionary_result')
        
        if not questionary:
            raise ValidationError("Debe seleccionar un cuestionario válido.")
        
        return questionary