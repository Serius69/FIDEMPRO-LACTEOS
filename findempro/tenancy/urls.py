from django.urls import path

from . import views

app_name = "tenancy"

urlpatterns = [
    path("context/", views.context, name="context"),
    path("change-plan/", views.plan_change, name="change-plan"),
    path("start-trial/", views.trial_start, name="start-trial"),
    path("cancel/", views.subscription_cancel, name="cancel"),
    path("usage/", views.usage, name="usage"),
]
