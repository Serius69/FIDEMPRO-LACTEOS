# users/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # User registration URL
    path('register/', views.UserRegister.as_view(), name='user-register'),
    # Other user-related URLs, e.g., profile, password change, etc.
]
