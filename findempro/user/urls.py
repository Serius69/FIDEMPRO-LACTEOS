from django.urls import path
from .views import (
    profile_product_variable_list_view,create_user_view,
    update_user_view,delete_user_view,user_list_view,
    change_password, delete_user_view_as_admin)

app_name = "user"

urlpatterns = [
    # Companies
    path("profile/", view=profile_product_variable_list_view, name="user.profile"),
    path("list/", view=user_list_view, name="user.list"),
    path("create/", view=create_user_view, name='user.create'),
    path("update/<int:user_id>", view=update_user_view, name='user.edit'),
    path("delete/<int:user_id>", view=delete_user_view_as_admin, name='user.delete'),
    path("password/", view=change_password, name='password.change'),
]
