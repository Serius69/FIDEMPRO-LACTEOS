from django import forms
from .models import Simulation

class SimulationForm(forms.ModelForm):
    class Meta:
        model = SimulationScenario
        fields = []
