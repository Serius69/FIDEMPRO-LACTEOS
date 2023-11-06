from django import forms
from .models import Business

class BusinessForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = ['name', 'type', 'location', 'image_src', 'description']

    def clean_name(self):
        name = self.cleaned_data.get('name')
        # Ejemplo de validación: Asegurarse de que el nombre no sea vacío
        if not name:
            raise forms.ValidationError("El campo 'Nombre' no puede estar vacío.")
        return name

    def clean_location(self):
        location = self.cleaned_data.get('location')
        # Ejemplo de validación: Asegurarse de que la ubicación tenga al menos 5 caracteres
        if len(location) < 5:
            raise forms.ValidationError("La ubicación debe tener al menos 5 caracteres.")
        return location
