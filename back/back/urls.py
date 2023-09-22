# project/urls.py

from django.contrib import admin
from django.urls import path, include, reverse_lazy  # Import reverse_lazy
from rest_framework.routers import DefaultRouter
from users.views import UserViewSet, UserLogIn
from django.views.generic.base import RedirectView  # Import RedirectView
from django.conf import settings
from django.conf.urls.static import static  # Import the 'static' function

# Create a router and register user-related views
router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    # Admin site (if needed)
    # path('admin/', admin.site.urls),
    
    # API URLs
    path('api/v1/', include(router.urls)),
    path('api-user-login/', UserLogIn.as_view()),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    
    # URLs of other applications
    path('users/', include('users.urls')), 
    path('product/', include('product.urls')),
    path('simulate/', include('simulate.urls')),
    path('variable/', include('variable.urls')),
    path('fdp/', include('fdp.urls')),
    
    # Redirect to the root of the API
    path('', RedirectView.as_view(url=reverse_lazy('api-root'), permanent=False)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
