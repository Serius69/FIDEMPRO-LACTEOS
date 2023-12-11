from django import forms
from django.contrib.auth.models import User
 # Import the Product model here if needed

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = []

