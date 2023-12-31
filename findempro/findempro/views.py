from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from allauth.account.views import PasswordChangeView, PasswordSetView
from django.http import HttpResponseServerError
from PIL import Image

class MyPasswordChangeView(PasswordChangeView):
    success_url = reverse_lazy("dashboard:index")

    def form_valid(self, form):
        try:
            # Attempt to change the user's password
            response = super().form_valid(form)
            # Additional logic to execute if the password change is successful
            return response
        except Exception as e:
            # Handle exceptions here, e.g., log the error or display an error message
            return HttpResponseServerError("An error occurred while changing the password. Please try again later.")

class MyPasswordSetView(PasswordSetView):
    success_url = reverse_lazy("dashboard:index")

    def form_valid(self, form):
        try:
            # Attempt to set the user's password
            response = super().form_valid(form)
            # Additional logic to execute if the password set is successful
            return response
        except Exception as e:
            # Handle exceptions here, e.g., log the error or display an error message
            return HttpResponseServerError("An error occurred while setting the password. Please try again later.")
