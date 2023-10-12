from django.urls import path
from product.views import(
    product_list, product_overview,create_product_view,update_product_view
)
app_name = 'product'
urlpatterns = [
    # Companies
    path("list", view=product_list, name="product.list"),
    path("overview/<int:pk>", view=product_overview, name="product.overview"),
    path("new/", view=create_product_view, name='product.create'),
    path("edit/", view=update_product_view, name='product.edit'),
]
