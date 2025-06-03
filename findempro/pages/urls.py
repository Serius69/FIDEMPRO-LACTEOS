from django.urls import path
from django.views.generic import RedirectView
from pages.views import (
    pages_faqs,
    pages_maintenance,
    pages_coming_soon,
    pages_privacy_policy,
    pages_terms_conditions,
    register_elements,
    register_elements_simulation,
    register_elements_create
)

app_name = "pages"

urlpatterns = [
    # Páginas informativas
    path("faqs/", pages_faqs, name="pages.faqs"),
    path("maintenance/", pages_maintenance, name="pages.maintenance"),
    path("coming-soon/", pages_coming_soon, name="pages.coming_soon"),
    path("privacy-policy/", pages_privacy_policy, name="pages.privacy_policy"),
    path("terms-conditions/", pages_terms_conditions, name="pages.terms_conditions"),
    
    # Registro de elementos
    path("register-elements/", register_elements, name="pages.register_elements"),
    path("register-simulation/", register_elements_simulation, name="pages.register_elements_simulation"),
    path("register-elements/create/", register_elements_create, name="pages.register_elements_create"), 

    # Redirecciones para URLs antiguas (compatibilidad hacia atrás)
    path("coming_soon/", RedirectView.as_view(pattern_name="pages:coming_soon", permanent=True)),
    path("privacy-policy", RedirectView.as_view(pattern_name="pages:privacy_policy", permanent=True)),
    path("terms-conditions", RedirectView.as_view(pattern_name="pages:terms_conditions", permanent=True)),
]
