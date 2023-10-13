from django.contrib import admin
from django.urls import path,include
from django.contrib.auth.decorators import login_required
from .views import MyPasswordChangeView, MyPasswordSetView
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    # Dashboard
    path('',include('dashboards.urls')),
    # Layouts
    path('layouts/',include('layouts.urls')),
    # Pages
    path('pages/',include('pages.urls')),
    # Business
    path('business/', include('business.urls')),    
    # Products    
    path('product/',include('product.urls')),
    # Variables
    path('variable/',include('variable.urls')),
    # Question
    path('question/',include('question.urls')),
    # Simulate
    path('simulate/',include('simulate.urls')),
    # User
    path('user/',include('user.urls')),
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
    path('social-auth/',include('social_django.urls', namespace='social')),
]

if settings.DEBUG:
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
