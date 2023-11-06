from django import forms
from .models import Variable

class VariableForm(forms.ModelForm):
    class Meta:
        model = Variable
        fields = ('name', 'type','unit','description','image_src','fk_product')

