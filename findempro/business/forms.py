from django import forms
from .models import *
class BusinessForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = ('name', 'type', 'location', 'image_src')  # Update the fields to match the Business model

        widgets = {
            'name': forms.TextInput(attrs={'class': 'textinputclass'}),
            'type': forms.TextInput(attrs={'class': 'textinputclass'}),
            'location': forms.TextInput(attrs={'class': 'textinputclass'}),
            'image_src': forms.TextInput(attrs={'class': 'textinputclass'}),
        }

    def __init__(self, *args, **kwargs):
        super(BusinessForm, self).__init__(*args, **kwargs)
        self.fields['name'].label = 'Business Name'
        self.fields['type'].label = 'Business Type'
        self.fields['location'].label = 'Location'
        self.fields['image_src'].label = 'Tags'
        
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity < 0:
            raise forms.ValidationError("Quantity cannot be negative.")
        return quantity
