from django.shortcuts import render
from django.views.generic import TemplateView
class PagesView(TemplateView):
    pass
def pages_faqs(request):
    template_name = "pages/faqs.html"
    return render(request, template_name)
pages_maintenance= PagesView.as_view(template_name="pages/maintenance.html")
pages_coming_soon= PagesView.as_view(template_name="pages/coming-soon.html")
pages_privacy_policy= PagesView.as_view(template_name="pages/privacy-policy.html")
pages_terms_conditions= PagesView.as_view(template_name="pages/term-conditions.html")
def pagina_error_404(request, exception):
    return render(request, 'pages/404.html', status=404)
