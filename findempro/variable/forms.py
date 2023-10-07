from django import forms
from .models import Variable, Node, Edge

class VariableForm(forms.ModelForm):
    class Meta:
        model = Variable
        fields = ('name', 'unit', 'quantity')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'textinputclass'}),
        }
    
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity < 0:
            raise forms.ValidationError("Quantity cannot be negative.")
        return quantity

class NodeForm(forms.ModelForm):
    class Meta:
        model = Node
        fields = ('name',)  # Add other fields as needed
        widgets = {
            'name': forms.TextInput(attrs={'class': 'textinputclass'}),
        }

class EdgeForm(forms.ModelForm):
    class Meta:
        model = Edge
        fields = ('source', 'target')  # Add other fields as needed

    def __init__(self, *args, **kwargs):
        super(EdgeForm, self).__init__(*args, **kwargs)
        self.fields['source'].label = 'Source Node'
        self.fields['target'].label = 'Target Node'