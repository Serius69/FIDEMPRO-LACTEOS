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
from .health import health_check

# Define la vista personalizada para errores 404
def error_404(request, exception):
    return render(request, 'pages/404.html', status=404)

def error_500(request):
    return render(request, 'pages/500.html', status=500)

# Define the schema view for the API
schema_view = get_schema_view(
    openapi.Info(
        title="Findempro API",
        default_version='v1',
        description="Findempro API documentation",
        terms_of_service="https://www.findempro.com/terms/",
        contact=openapi.Contact(email="contact@findempro.com"),
        license=openapi.License(name="Proprietary"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Health check endpoint
    path('health/', health_check, name='health_check'),
    
    # Dashboard
    path('', include('dashboards.urls')),
    
    # Apps
    path('pages/', include('pages.urls')),
    path('business/', include('business.urls')),    
    path('product/', include('product.urls')),
    path('variable/', include('variable.urls')),
    path('questionary/', include('questionary.urls')),
    path('simulate/', include('simulate.urls')),
    path('report/', include('report.urls')),
    path('user/', include('user.urls')),
    
    # Authentication
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
    path('account/', include('allauth.urls')),
    path('social-auth/', include('social_django.urls', namespace='social')),
    
    # API Documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0),
            name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Error handlers
handler404 = 'findempro.urls.error_404'
handler500 = 'findempro.urls.error_500'

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Debug toolbar
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns