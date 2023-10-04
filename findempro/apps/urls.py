from django.urls import path, include
from apps.views import(
    apps_companies_list,
    apps_companies_grid,
    apps_companies_overview,
    apps_companies_add,
    apps_products_list,
    apps_product_overview,
    apps_product_add,
    apps_products_list,
    apps_product_overview,
    apps_product_add,
    apps_variables_list,
    apps_variables_overview,
    apps_variables_add,
    apps_users_list,
    apps_users_overview,
    apps_users_add,
    apps_simulate_init,
    apps_reports_overview,
    apps_reports_list
)
app_name = "apps"

urlpatterns = [
    # Companies
    path("companies/list", view=apps_companies_list, name="companies.list"),
    path("companies/grid", view=apps_companies_grid, name="companies.grid"),
    path("companies/overview", view=apps_companies_overview, name="companies.overview"),
    path("companies/add", view=apps_companies_add, name="companies.create"),
    # Products
    path("products/list", view=apps_products_list, name="products.list"),
    path("products/overview", view=apps_product_overview, name="products.overview"),
    path("products/add", view=apps_product_add, name="products.create"),
    # path("products/update-products/<int:pk>", view=apps_products_update_products_view, name="products.update_products"),
    # path("products/delete-products/<int:pk>", view=apps_products_delete_products_view, name="products.delete_products"),
    # Variables
    path("variables/list", view=apps_variables_list, name="variables.list"),
    path("variables/overview", view=apps_variables_overview, name="variables.overview"),
    path("variables/create", view=apps_variables_add, name="variables.create"),
    # Users
    path("users/list", view=apps_users_list, name="users.list"),
    path("users/overview", view=apps_users_overview, name="users.overview"),
    path("users/add", view=apps_users_add, name="users.details"),
    # Simualte
    path("simulate/init", view=apps_simulate_init, name="simulate.init"),
    # Reports
    path("reports/list", view=apps_reports_list, name="reports.list"),
    path("reports/overview", view=apps_reports_overview, name="reports.overview"),
    
]
