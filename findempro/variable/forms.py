from django import forms
from .models import Variable
from .models import Equation
class VariableForm(forms.ModelForm):
    class Meta:
        model = Variable
        fields = ('name', 'type','unit','description','image_src','fk_product')

class EquationForm(forms.ModelForm):
    class Meta:
        model = Equation
        fields = ['name', 'description', 'expression', 'fk_variable1', 'fk_variable2', 'fk_variable3', 'fk_variable4', 'fk_variable5', 'fk_area']