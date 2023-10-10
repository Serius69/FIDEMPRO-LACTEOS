from django.urls import path

from business.views import business_list, business_overview, create_business_view

app_name = 'business'

urlpatterns = [
    # Companies
    path("list/", business_list, name="business.list"),
    path("overview/<int:pk>/", business_overview, name="business.overview"),
    path("new/", create_business_view, name='business.create'),
]
