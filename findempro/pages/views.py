from django.shortcuts import render
from django.views.generic import TemplateView
# Create your views here.

class PagesView(TemplateView):
    pass

# Authenticatin
authentication_signin= PagesView.as_view(template_name="account/login.html")
# authentication_signup= PagesView.as_view(template_name="pages/authentication/auth-signup-cover.html")
# authentication_pass_reset= PagesView.as_view(template_name="pages/authentication/auth-pass-reset-cover.html")
# authentication_lockscreen= PagesView.as_view(template_name="pages/authentication/auth-lockscreen-cover.html")
# authentication_logout= PagesView.as_view(template_name="pages/authentication/auth-logout-cover.html")
# authentication_success_msg= PagesView.as_view(template_name="pages/authentication/auth-success-msg-cover.html")
# authentication_twostep= PagesView.as_view(template_name="pages/authentication/auth-twostep-cover.html")
# authentication_404_cover= PagesView.as_view(template_name="pages/authentication/auth-404-cover.html")
# authentication_500= PagesView.as_view(template_name="pages/authentication/auth-500.html")
# authentication_pass_change= PagesView.as_view(template_name="pages/authentication/auth-pass-change-cover.html")
# authentication_offline= PagesView.as_view(template_name="pages/authentication/auth-offline.html")

# Pages 
pages_profile_settings= PagesView.as_view(template_name="user/profile-settings.html")
pages_faqs= PagesView.as_view(template_name="pages/faqs.html")
pages_maintenance= PagesView.as_view(template_name="pages/maintenance.html")
pages_coming_soon= PagesView.as_view(template_name="pages/coming-soon.html")
pages_privacy_policy= PagesView.as_view(template_name="pages/privacy-policy.html")
pages_terms_conditions= PagesView.as_view(template_name="pages/term-conditions.html")


# Define la vista personalizada para errores 404
def pagina_error_404(request, exception):
    return render(request, 'pages/404.html', status=404)
