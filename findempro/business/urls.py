from django.urls import path, include
from business.views import(
    apps_companies_list,
    apps_companies_overview,
)

urlpatterns = [
    # Companies
    path("company/list", view=apps_companies_list, name="company.list"),
    path("company/overview/<int:pk>", view=apps_companies_overview, name="company.overview"),

]
