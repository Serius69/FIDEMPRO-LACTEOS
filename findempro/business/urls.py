from django.urls import path
from business.views import (business_list_view, 
                            read_business_view, 
                            create_or_update_business_view,
                            delete_business_view,
                            get_business_details_view
                            )

app_name = 'business'

urlpatterns = [
    path("list/", business_list_view, name="business.list"),
    path("overview/<int:pk>/", read_business_view, name="business.overview"),
    path('create/', create_or_update_business_view, name='business.create'),
    path('<int:pk>/update/', create_or_update_business_view, name='business.update'),
    path("delete/<int:pk>/", view=delete_business_view, name='business.delete'),
    path('get_details/<int:pk>/', get_business_details_view, name='business.get_business_details_view'),
]