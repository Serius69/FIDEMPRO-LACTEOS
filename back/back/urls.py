from django.conf import settings
from django.urls import path, include, reverse_lazy
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic.base import RedirectView
from rest_framework.routers import DefaultRouter
from users.views import UserViewSet, UserLogIn

# Importa las vistas de tus aplicaciones
from simulate import views as simulate_views
from product import views as product_views
from variable import views as variable_views
from fdp import views as fdp_views

# Crea un router y registra las vistas de usuarios
router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    # Admin site (if needed)
    # path('admin/', admin.site.urls),
    
    # API URLs
    path('api/v1/', include(router.urls)),
    path('api-user-login/', UserLogIn.as_view()),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
       
    # Incluye las URLs de las otras aplicaciones
    path('product/', include('product.urls')),
    path('simulate/', include('simulate.urls')),
    path('variable/', include('variable.urls')),
    path('fdp/', include('fdp.urls')),
    
    # Redirige a la raíz de la API
    path('', RedirectView.as_view(url=reverse_lazy('api-root'), permanent=False)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
