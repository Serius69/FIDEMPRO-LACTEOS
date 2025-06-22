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
    """Formulario para configuración inicial - VERSIÓN CORREGIDA"""
    
    selected_questionary_result = forms.ModelChoiceField(
        queryset=QuestionaryResult.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-choices': 'true',
            'data-choices-sorting': 'true',
            'required': 'true'
        }),
        empty_label="Seleccione un cuestionario...",
        required=True,
        error_messages={
            'required': 'Debe seleccionar un cuestionario',
            'invalid_choice': 'Seleccione un cuestionario válido'
        }
    )
    
    selected_quantity_time = forms.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(365)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,
            'max': 365,
            'placeholder': 'Ej: 30',
            'required': 'true',
            'value': 30  # Valor por defecto
        }),
        required=True,
        initial=30,
        error_messages={
            'required': 'La duración es requerida',
            'invalid': 'Ingrese un número válido',
            'min_value': 'La duración debe ser al menos 1',
            'max_value': 'La duración no puede exceder 365'
        }
    )
    
    selected_unit_time = forms.ChoiceField(
        choices=Simulation.TIME_UNITS,
        initial='days',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': 'true'
        }),
        required=True,
        error_messages={
            'required': 'Debe seleccionar una unidad de tiempo',
            'invalid_choice': 'Seleccione una unidad de tiempo válida'
        }
    )
    
    # Campos para inicio de simulación
    fk_fdp = forms.ModelChoiceField(
        queryset=ProbabilisticDensityFunction.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': 'true'
        }),
        required=False,  # Solo requerido en inicio de simulación
        empty_label="Seleccione una distribución...",
        error_messages={
            'invalid_choice': 'Seleccione una función de densidad válida'
        }
    )
    
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
        ),
        error_messages={
            'invalid': 'Seleccione un nivel de confianza válido'
        }
    )
    
    random_seed = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 12345'
        }),
        error_messages={
            'invalid': 'La semilla debe ser un número entero'
        }
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filtrar cuestionarios del usuario
            self.fields['selected_questionary_result'].queryset = (
                QuestionaryResult.objects.filter(
                    is_active=True,
                    fk_questionary__fk_product__fk_business__fk_user=user
                ).select_related(
                    'fk_questionary__fk_product__fk_business'
                ).order_by('-date_created')
            )
            
            # Filtrar FDPs disponibles para el usuario
            self.fields['fk_fdp'].queryset = (
                ProbabilisticDensityFunction.objects.filter(
                    is_active=True,
                    fk_business__fk_user=user
                ).order_by('distribution_type')
            )

    def clean_selected_quantity_time(self):
        """Validación robusta para cantidad de tiempo"""
        quantity = self.cleaned_data.get('selected_quantity_time')
        
        if quantity is None:
            raise ValidationError("La duración es requerida.")
        
        try:
            quantity_int = int(quantity)
        except (ValueError, TypeError):
            raise ValidationError("La duración debe ser un número entero.")
        
        if quantity_int < 1:
            raise ValidationError("La duración debe ser mayor a 0.")
        
        if quantity_int > 365:
            raise ValidationError("La duración no puede exceder 365 días.")
        
        return quantity_int

    def clean_selected_questionary_result(self):
        """Validación robusta para cuestionario"""
        questionary = self.cleaned_data.get('selected_questionary_result')
        
        if not questionary:
            raise ValidationError("Debe seleccionar un cuestionario válido.")
        
        # Verificar que el cuestionario esté activo
        if not questionary.is_active:
            raise ValidationError("El cuestionario seleccionado no está activo.")
        
        # Verificar que tenga respuestas
        if not questionary.fk_question_result_answer.filter(is_active=True).exists():
            raise ValidationError("El cuestionario seleccionado no tiene respuestas válidas.")
        
        return questionary

    def clean_fk_fdp(self):
        """Validación para función de densidad de probabilidad"""
        fdp = self.cleaned_data.get('fk_fdp')
        
        # Solo validar si se proporcionó
        if fdp:
            if not fdp.is_active:
                raise ValidationError("La función de densidad seleccionada no está activa.")
        
        return fdp

    def clean_random_seed(self):
        """Validación para semilla aleatoria"""
        seed = self.cleaned_data.get('random_seed')
        
        if seed is not None:
            try:
                seed_int = int(seed)
                if seed_int < 0:
                    raise ValidationError("La semilla debe ser un número positivo.")
                return seed_int
            except (ValueError, TypeError):
                raise ValidationError("La semilla debe ser un número entero válido.")
        
        return seed

    def clean_confidence_level(self):
        """Validación para nivel de confianza"""
        confidence = self.cleaned_data.get('confidence_level')
        
        if confidence is not None:
            try:
                confidence_float = float(confidence)
                if not (0.5 <= confidence_float <= 0.99):
                    raise ValidationError("El nivel de confianza debe estar entre 0.5 y 0.99.")
                return confidence_float
            except (ValueError, TypeError):
                raise ValidationError("El nivel de confianza debe ser un número válido.")
        
        return 0.95  # Valor por defecto