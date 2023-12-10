from django.urls import path
from . import views

app_name = "user"

urlpatterns = [
    path("profile/", views.profile_product_variable_list_view, name="user.profile"),
    path("profile-settings",views.pages_profile_settings,name="user.profile_settings"),
    path("list/", views.user_list_view, name="user.list"),
    path("create/", views.create_user_view, name='user.create'),
    path("update/<int:user_id>", views.update_user_view, name='user.edit'),
    path("delete/<int:user_id>", views.delete_user_view, name='user.delete'),
    path("admin/delete/<int:user_id>", views.delete_user_view_as_admin, name='admin.delete'),
    path("password/", views.change_password, name='password.change'),
    path('deactivate/', views.deactivate_account, name='user.deactivate_account'),
    path('cancel/', views.cancel_deactivation, name='cancel'),
    path('register_elements/', registro_con_elementos, name='registro_con_elementos'),

]
