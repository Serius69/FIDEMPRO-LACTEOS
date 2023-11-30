from django.urls import path
from product.views import(product_list,
                          product_overview,
                          create_product_view,
                          update_product_view,
                          delete_product_view,
                          get_product_details,
                          area_overview
                        )
app_name = 'product'
urlpatterns = [
    path("list", view=product_list, name="product.list"),
    path("overview/<int:pk>/", view=product_overview, name="product.overview"),
    path("create/", view=create_product_view, name='product.create'),
    path("update/<int:pk>/", view=update_product_view, name='product.edit'),
    path("delete/<int:pk>/", view=delete_product_view, name='product.delete'),
    path("area/overview/<int:pk>/", view=area_overview, name='area.overview'),
    # path('generate-products/', generate_default_products, name='product.generate_default'),
    path('get_product_details/<int:pk>/', get_product_details, name='product.get_product_details'),
]