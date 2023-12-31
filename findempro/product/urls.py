from django.urls import path
from product.views import(product_list,
                          read_product_view,
                          create_or_update_product_view,
                          delete_product_view,
                          get_product_details,
                          area_overview,
                          create_or_update_area_view,
                          delete_area_view,
                          get_area_details_view,
                        )
app_name = 'product'
urlpatterns = [
    path("list", view=product_list, name="product.list"),
    path("overview/<int:pk>/", view=read_product_view, name="product.overview"),
    path("create/", view=create_or_update_product_view, name='product.create'),
    path('<int:pk>/update/', view=create_or_update_product_view, name='product.edit'),
    path("delete/<int:pk>/", view=delete_product_view, name='product.delete'),
    path('get_details/<int:pk>/', get_product_details, name='product.get_details'),
    path("area/overview/<int:pk>/", view=area_overview, name='area.overview'),
    path("area/create/", view=create_or_update_area_view, name='area.create'),
    path("area/update/<int:pk>/", view=create_or_update_area_view, name='area.edit'),
    path("area/delete/<int:pk>/", view=delete_area_view, name='area.delete'),
    path('area/get_details/<int:pk>/', get_area_details_view, name='area.get_details'),
]