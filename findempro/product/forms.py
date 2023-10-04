from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ('name', 'type', 'quantity', 'description')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'textinputclass'}),
            'description': forms.Textarea(attrs={'class': 'editable medium-editor-textarea postcontent'}),
        }

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        self.fields['name'].label = 'Product Name'
        self.fields['type'].label = 'Product Type'
        self.fields['quantity'].label = 'Quantity'
        self.fields['description'].label = 'Description'
        self.fields['description'].help_text = 'Enter a description for the product.'

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity < 0:
            raise forms.ValidationError("Quantity cannot be negative.")
        return quantity

class ProductAddForm(ProductForm):
    class Meta(ProductForm.Meta):
        exclude = []

class ProductUpdateForm(ProductForm):
    class Meta(ProductForm.Meta):
        exclude = []

class ProductDeleteForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = []  # No fields, as this is a delete form
