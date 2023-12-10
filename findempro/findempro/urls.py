from django.contrib import admin
from django.urls import path, re_path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.contrib.auth.decorators import login_required
from .views import MyPasswordChangeView, MyPasswordSetView
from django.conf.urls.static import static
from django.conf import settings
from django.shortcuts import render

# Define la vista personalizada para errores 404
def error_404(request, exception):
    return render(request, 'pages/404.html', status=404)

def error_500(request):
    return render(request, 'pages/500.html', status=500)

schema_view = get_schema_view(
    openapi.Info(
        title="Findempro",
        default_version='v1',
        description="Findempro API description",
        terms_of_service="https://www.findempro.com/terms/",
        contact=openapi.Contact(email="contact@yourapp.com"),
        license=openapi.License(name="Your License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # Dashboard
    path('', include('dashboards.urls')),
    # Pages
    path('pages/', include('pages.urls')),
    # Business
    path('business/', include('business.urls')),    
    # Products    
    path('product/', include('product.urls')),
    # Variables
    path('variable/', include('variable.urls')),
    # Question
    path('questionary/', include('questionary.urls')),
    # Simulates
    path('simulate/', include('simulate.urls')),
    # Report
    path('report/', include('report.urls')),
    # User
    path('user/', include('user.urls')),
    path(
        "account/password/change/",
        login_required(MyPasswordChangeView.as_view()),
        name="account_change_password",
    ),
    path(
        "account/password/set/",
        login_required(MyPasswordSetView.as_view()),
        name="account_set_password",
    ),
    # All Auth 
    path('account/', include('allauth.urls')),
    path('social-auth/', include('social_django.urls', namespace='social')),
    # path('api/', include('your_app.urls')),  # Include your app's URLs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0),
            name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path
]

# Maneja todos los errores 404
handler404 = 'findempro.urls.error_404'
handler500 = 'findempro.urls.error_500'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
