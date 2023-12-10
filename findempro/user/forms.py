from django import forms
from django.contrib.auth.models import User
 # Import the Product model here if needed

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = []
class RegisteerElementsForm(forms.Form):
    # Otras campos de formulario aquí

    ELEMENTOS_CHOICES = [
        ('business', 'Crear Business'),
        ('product', 'Crear Product'),
        ('area', 'Crear Area'),
        ('variable', 'Crear Variable'),
        ('equation', 'Crear Equation'),
    ]

    elementos = forms.MultipleChoiceField(
        choices=ELEMENTOS_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    
