from django.urls import path
from pages.views import (

pages_faqs,
pages_maintenance,
pages_coming_soon,
pages_privacy_policy,
pages_terms_conditions,
register_elements,
register_elements_simulation
)
app_name = "pages"
urlpatterns = [       
    path("faqs",view=pages_faqs,name="pages.faqs"),
    path("maintenance",view =pages_maintenance,name="pages.maintenance"),
    path("coming_soon",view =pages_coming_soon,name="pages.coming_soon"),
    path("privacy-policy",view =pages_privacy_policy,name="pages.privacy_policy"),
    path("terms-conditions",view =pages_terms_conditions,name="pages.terms_conditions"),
    path('register_elements/', view=register_elements, name='pages.register_elements'),
    path('register_elements_simulation/', view=register_elements_simulation, name='pages.register_elements_simulation'),
] 

