from django import forms
from .models import Business

class BusinessForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = ['name', 'type', 'location', 'image_src', 'description']

