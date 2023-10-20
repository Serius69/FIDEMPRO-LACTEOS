from django import forms
from .models import SimulationScenario

class SimulationForm(forms.ModelForm):
    class Meta:
        model = SimulationScenario
        fields = []
