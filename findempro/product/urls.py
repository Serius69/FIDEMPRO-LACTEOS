from django.urls import path, include
from product.views import(
    product_list,
    product_overview,
)

urlpatterns = [
    # Companies
    path("list", view=product_list, name="product.list"),
    path("overview/<int:pk>", view=product_overview, name="product.overview"),

]
