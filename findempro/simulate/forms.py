from django import forms
from .models import Simulation

class SimulationForm(forms.ModelForm):
    class Meta:
        model = Simulation
        fields = ['unit_time', 
                  'fk_fdp', 
                  'weight', 
                  'fk_questionary', 
                  'distributions', 
                  'questionary_result', 
                  'is_active']
