from django import forms
from .models import FinancialDecision, FinanceRecommendation  # Import the Business model here if needed

class FinancialDecisionForm(forms.ModelForm):
    class Meta:
        model = FinancialDecision
        fields = ['name', 'type', 'location', 'image_src', 'description']


class FinanceRecommendationForm(forms.ModelForm):
    class Meta:
        model = FinanceRecommendation
        fields = ['name', 'recommendation', 'description']
        
    def clean_name(self):
        name = self.cleaned_data.get('name')
        # Ejemplo de validación: Asegurarse de que el nombre no sea vacío
        if not name:
            raise forms.ValidationError("El campo 'Nombre' no puede estar vacío.")
        return name

    def clean_recommendation(self):
        recommendation = self.cleaned_data.get('recommendation')
        # Ejemplo de validación: Asegurarse de que la recomendación tenga al menos 10 caracteres
        if len(recommendation) < 10:
            raise forms.ValidationError("La recomendación debe tener al menos 10 caracteres.")
        return recommendation

    def clean_description(self):
        description = self.cleaned_data.get('description')
        # Ejemplo de validación: Asegurarse de que la descripción no sea más larga que 200 caracteres
        if len(description) > 200:
            raise forms.ValidationError("La descripción no puede superar los 200 caracteres.")
        return description