from django import forms
from .models import *
class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ('name', 'type', 'location', 'image_src')  # Update the fields to match the Company model

        widgets = {
            'name': forms.TextInput(attrs={'class': 'textinputclass'}),
            'location': forms.TextInput(attrs={'class': 'textinputclass'}),
            'type': forms.TextInput(attrs={'class': 'textinputclass'}),
            'image_src': forms.TextInput(attrs={'class': 'textinputclass'}),
        }

    def __init__(self, *args, **kwargs):
        super(CompanyForm, self).__init__(*args, **kwargs)
        self.fields['name'].label = 'Company Name'
        self.fields['type'].label = 'Company Type'
        self.fields['location'].label = 'Location'
        self.fields['image_src'].label = 'Tags'
        
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity < 0:
            raise forms.ValidationError("Quantity cannot be negative.")
        return quantity
