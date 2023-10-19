from django.urls import path
from pages.views import (
authentication_signin,
pages_profile_settings,
pages_faqs,
pages_maintenance,
pages_coming_soon,
pages_privacy_policy,
pages_terms_conditions

)

app_name = "pages"

urlpatterns = [
    # Authentication    
    # path("authentication/signin",view =authentication_signin,name="authentication.signin"),
    
    # Pages              
    path("profile-settings",view =pages_profile_settings,name="pages.profile_settings"),
    path("faqs",view =pages_faqs,name="pages.faqs"),
    path("maintenance",view =pages_maintenance,name="pages.maintenance"),
    path("coming_soon",view =pages_coming_soon,name="pages.coming_soon"),
    path("privacy-policy",view =pages_privacy_policy,name="pages.privacy_policy"),
    path("terms-conditions",view =pages_terms_conditions,name="pages.terms_conditions"),
] 

