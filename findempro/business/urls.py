from django.urls import path
from business.views import (business_list, 
                            business_overview, 
                            create_business_view,
                            update_business_view,
                            delete_business_view,
                            get_business_details
                            )

app_name = 'business'

urlpatterns = [
    path("list/", business_list, name="business.list"),
    path("overview/<int:pk>/", business_overview, name="business.overview"),
    path("create/", create_business_view, name='business.create'),
    path("update/<int:pk>/", view=update_business_view, name='business.edit'),
    path("delete/<int:pk>/", view=delete_business_view, name='business.delete'),
    path('get_business_details/<int:pk>/', get_business_details, name='business.get_business_details'),

]