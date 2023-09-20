from django.conf import settings
from django.urls import path, include, reverse_lazy
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic.base import RedirectView
from rest_framework.routers import DefaultRouter
from users.views import UserViewSet, UserLogIn

# views
from simulate import views
from product import views
from variable import views
from fdp import views


# Create a router and register the UserViewSet
router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    # Admin site (if needed)
    # path('admin/', admin.site.urls),
    
    # API URLs
    path('api/v1/', include(router.urls)),
    path('api-user-login/', UserLogIn.as_view()),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    
    # Your custom view
    path('ks-test/', views.ks_test_view, name='ks_test_view'),
    path('product/', views.ks_test_view, name='ks_test_view'),
   
    path('api/', include('api.urls')),
    
    # Redirect to the API root
    path('', RedirectView.as_view(url=reverse_lazy('api-root'), permanent=False)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
