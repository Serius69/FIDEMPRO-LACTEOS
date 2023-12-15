from django import forms
from .models import Product,Area
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'type', 'description', 'image_src', 'fk_business']
        
class AreaForm(forms.ModelForm):
    class Meta:
        model = Area
        fields = ['name', 'description', 'image_src', 'fk_product']
