from django.urls import path
from .views import KSTestView

urlpatterns = [
    path('api/kstest/', KSTestView.as_view(), name='kstest-api'),
]
