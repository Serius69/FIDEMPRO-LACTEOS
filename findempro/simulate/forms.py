from django import forms
from .models import Simulation

class SimulationForm(forms.ModelForm):
    class Meta:
        model = Simulation
        fields = ['unit_time', 
                  'fk_fdp', 
                  'fk_questionary_result', 
                  'demand_history']
