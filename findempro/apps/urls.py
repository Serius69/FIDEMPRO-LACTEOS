from django.urls import path, include
from apps.views import(
    apps_companies_list,
    apps_companies_overview,
    apps_products_list,
    apps_product_overview,
    apps_products_list,
    apps_product_overview,
    apps_variables_list,
    apps_variables_overview,
    apps_users_list,
    apps_users_overview,
    apps_simulate_init,
    apps_reports_overview,
    apps_reports_list
)
app_name = "apps"

urlpatterns = [
    # Companies
    path("company/list", view=apps_companies_list, name="company.list"),
    path("company/overview/<int:pk>", view=apps_companies_overview, name="company.overview"),
    # Products
    path("products/list", view=apps_products_list, name="products.list"),
    path("products/overview/<int:pk>", view=apps_product_overview, name="products.overview"),
    # path("products/update-products/<int:pk>", view=apps_products_update_products_view, name="products.update_products"),
    # path("products/delete-products/<int:pk>", view=apps_products_delete_products_view, name="products.delete_products"),
    # Variables
    path("variables/list", view=apps_variables_list, name="variables.list"),
    path("variables/overview/<int:pk>", view=apps_variables_overview, name="variables.overview"),
    # Users
    path("users/list", view=apps_users_list, name="users.list"),
    path("users/overview/<int:pk>", view=apps_users_overview, name="users.overview"),
    # Simualte
    path("simulate/init", view=apps_simulate_init, name="simulate.init"),
    # Reports
    path("reports/list", view=apps_reports_list, name="reports.list"),
    path("reports/overview/<int:pk>", view=apps_reports_overview, name="reports.overview"),
    
]
