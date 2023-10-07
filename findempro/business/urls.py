from django.urls import path, include
from business.views import(
    business_list,
    business_overview,
)

urlpatterns = [
    # Companies
    path("list", view=business_list, name="business.list"),
    path("overview/<int:pk>", view=business_overview, name="business.overview"),

]
