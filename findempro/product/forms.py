from django import forms
from .models import Product  # Import the Product model here if needed

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'type', 'description', 'image_src', 'fk_business']
