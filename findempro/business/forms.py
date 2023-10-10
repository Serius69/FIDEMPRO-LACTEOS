from django import forms
from .models import Business  # Import the Business model here if needed

class BusinessForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = ('name', 'type', 'location', 'image_src', 'description')

    def __init__(self, *args, **kwargs):
        super(BusinessForm, self).__init__(*args, **kwargs)
        self.fields['name'].label = 'name'
        self.fields['type'].label = 'type'
        self.fields['location'].label = 'location'
        self.fields['image_src'].label = 'image_src'
        self.fields['description'].label = 'description'