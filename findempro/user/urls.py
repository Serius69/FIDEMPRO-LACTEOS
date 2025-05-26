"""
URLs mejoradas para el sistema de usuarios
Incluye rutas optimizadas, API endpoints y mejor organización
"""

from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from . import views

app_name = "user"

# URLs principales de perfil de usuario
profile_patterns = [
    path("", views.profile_product_variable_list_view, name="user.profile"),
    path("settings/", views.pages_profile_settings, name="user.profile_settings"),
    path("edit/", views.pages_profile_settings, name="user.profile_edit"),  # Alias para compatibilidad
]

# URLs de gestión de usuarios (solo para administradores)
user_management_patterns = [
    path("list/", views.user_list_view, name="user.list"),
    path("create/", views.create_user_view, name='user.create'),
    path("edit/<int:user_id>/", views.update_user_view, name='user.edit'),
    path("delete/<int:user_id>/", views.delete_user_view_as_admin, name='user.delete'),
    path("admin/delete/<int:user_id>/", views.delete_user_view_as_admin, name='admin.delete'),  # Alias para compatibilidad
    path("bulk-delete/", views.bulk_delete_users_view, name='user.bulk_delete'),
    path("toggle-status/<int:user_id>/", views.toggle_user_status_view, name='user.toggle_status'),
    path("export/", views.user_list_view, name='user.export'),  # Para exportación futura
]

# URLs de autenticación y seguridad
auth_patterns = [
    path("password/change/", views.change_password, name='password.change'),
    path("password/reset/", TemplateView.as_view(template_name='registration/password_reset_form.html'), name='password.reset'),
    path("deactivate/", views.deactivate_account, name='user.deactivate_account'),
    path("cancel/", views.cancel_deactivation, name='cancel'),
    path("logout/", TemplateView.as_view(template_name='registration/logged_out.html'), name='user.logout'),
]

# URLs de API para AJAX y funcionalidades avanzadas
api_patterns = [
    path("api/<int:user_id>/", views.user_api_detail, name='user.api_detail'),
    path("api/profile/update/", views.pages_profile_settings, name='user.api_profile_update'),
    path("api/preferences/", TemplateView.as_view(template_name='user/preferences.html'), name='user.api_preferences'),
    path("api/sessions/", TemplateView.as_view(template_name='user/sessions.html'), name='user.api_sessions'),
    path("api/activity/", views.UserActivityLogView.as_view(), name='user.api_activity'),
]

# URLs de administración avanzada
admin_patterns = [
    path("admin/dashboard/", TemplateView.as_view(template_name='user/admin_dashboard.html'), name='user.admin_dashboard'),
    path("admin/activity/", views.UserActivityLogView.as_view(), name='user.admin_activity'),
    path("admin/sessions/", TemplateView.as_view(template_name='user/admin_sessions.html'), name='user.admin_sessions'),
    path("admin/bulk-actions/", TemplateView.as_view(template_name='user/bulk_actions.html'), name='user.admin_bulk_actions'),
    path("admin/reports/", TemplateView.as_view(template_name='user/reports.html'), name='user.admin_reports'),
]

# URLs de configuración y preferencias
settings_patterns = [
    path("settings/profile/", views.pages_profile_settings, name='user.settings_profile'),
    path("settings/security/", TemplateView.as_view(template_name='user/security_settings.html'), name='user.settings_security'),
    path("settings/privacy/", TemplateView.as_view(template_name='user/privacy_settings.html'), name='user.settings_privacy'),
    path("settings/notifications/", TemplateView.as_view(template_name='user/notification_settings.html'), name='user.settings_notifications'),
    path("settings/preferences/", TemplateView.as_view(template_name='user/preferences.html'), name='user.settings_preferences'),
]

# URLs de utilidades y helpers
utility_patterns = [
    path("avatar/upload/", TemplateView.as_view(template_name='user/avatar_upload.html'), name='user.avatar_upload'),
    path("export/data/", TemplateView.as_view(template_name='user/export_data.html'), name='user.export_data'),
    path("import/contacts/", TemplateView.as_view(template_name='user/import_contacts.html'), name='user.import_contacts'),
    path("search/", TemplateView.as_view(template_name='user/search.html'), name='user.search'),
]

# URLs principales - consolidando todos los patrones
urlpatterns = [
    # Perfil de usuario
    path("profile/", include(profile_patterns)),
    
    # Gestión de usuarios (administradores)
    path("", include(user_management_patterns)),
    
    # Autenticación y seguridad
    path("auth/", include(auth_patterns)),
    
    # API endpoints
    path("", include(api_patterns)),
    
    # Administración avanzada
    path("", include(admin_patterns)),
    
    # Configuraciones
    path("", include(settings_patterns)),
    
    # Utilidades
    path("utils/", include(utility_patterns)),
    
    # URLs de compatibilidad y redirects
    path("update/<int:user_id>/", views.update_user_view, name='user.update'),  # Alias para compatibilidad
    path("overview/", views.profile_product_variable_list_view, name='user.overview'),  # Alias para compatibilidad
]

# URLs adicionales para funcionalidades específicas
extended_patterns = [
    # Gestión de sesiones
    path("sessions/", TemplateView.as_view(template_name='user/sessions.html'), name='user.sessions'),
    path("sessions/terminate/<str:session_key>/", TemplateView.as_view(template_name='user/session_terminate.html'), name='user.session_terminate'),
    path("sessions/terminate-all/", TemplateView.as_view(template_name='user/sessions_terminate_all.html'), name='user.sessions_terminate_all'),
    
    # Logs de actividad
    path("activity/", views.UserActivityLogView.as_view(), name='user.activity'),
    path("activity/<int:log_id>/", TemplateView.as_view(template_name='user/activity_detail.html'), name='user.activity_detail'),
    
    # Configuración avanzada
    path("advanced/", TemplateView.as_view(template_name='user/advanced_settings.html'), name='user.advanced_settings'),
    path("developer/", TemplateView.as_view(template_name='user/developer_settings.html'), name='user.developer_settings'),
    
    # Integraciones
    path("integrations/", TemplateView.as_view(template_name='user/integrations.html'), name='user.integrations'),
    path("integrations/social/", TemplateView.as_view(template_name='user/social_integrations.html'), name='user.social_integrations'),
    
    # Estadísticas y analytics
    path("stats/", TemplateView.as_view(template_name='user/stats.html'), name='user.stats'),
    path("analytics/", TemplateView.as_view(template_name='user/analytics.html'), name='user.analytics'),
    
    # Ayuda y soporte
    path("help/", TemplateView.as_view(template_name='user/help.html'), name='user.help'),
    path("support/", TemplateView.as_view(template_name='user/support.html'), name='user.support'),
    path("feedback/", TemplateView.as_view(template_name='user/feedback.html'), name='user.feedback'),
    
    # Onboarding y tours
    path("onboarding/", TemplateView.as_view(template_name='user/onboarding.html'), name='user.onboarding'),
    path("tour/", TemplateView.as_view(template_name='user/tour.html'), name='user.tour'),
    
    # Backup y recuperación
    path("backup/", TemplateView.as_view(template_name='user/backup.html'), name='user.backup'),
    path("restore/", TemplateView.as_view(template_name='user/restore.html'), name='user.restore'),
]

# Agregar las URLs extendidas a las principales
urlpatterns.extend(extended_patterns)

# URLs de webhook y API externa (para integraciones futuras)
webhook_patterns = [
    path("webhooks/social/", TemplateView.as_view(template_name='user/webhook_social.html'), name='user.webhook_social'),
    path("webhooks/payment/", TemplateView.as_view(template_name='user/webhook_payment.html'), name='user.webhook_payment'),
    path("webhooks/notification/", TemplateView.as_view(template_name='user/webhook_notification.html'), name='user.webhook_notification'),
]

# URLs para testing y desarrollo (solo en DEBUG)
# from django.conf import settings
# if settings.DEBUG:
#     debug_patterns = [
#         path("debug/profile/", TemplateView.as_view(template_name='user/debug_profile.html'), name='user.debug_profile'),
#         path("debug/permissions/", TemplateView.as_view(template_name='user/debug_permissions.html'), name='user.debug_permissions'),
#         path("debug/sessions/", TemplateView.as_view(template_name='user/debug_sessions.html'), name='user.debug_sessions'),
#         path("test/email/", TemplateView.as_view(template_name='user/test_email.html'), name='user.test_email'),
#         path("test/notifications/", TemplateView.as_view(template_name='user/test_notifications.html'), name='user.test_notifications'),
#     ]
#     urlpatterns.extend(debug_patterns)

# # Agregar webhooks
# urlpatterns.extend(webhook_patterns)

# # Handler personalizado para errores 404 en URLs de usuario
# handler404 = 'user.views.custom_404'

# # Metadata para documentación automática
# urlpatterns_metadata = {
#     'version': '2.0',
#     'description': 'Sistema completo de gestión de usuarios',
#     'endpoints': {
#         'profile': 'Gestión del perfil de usuario',
#         'admin': 'Administración de usuarios',
#         'api': 'Endpoints de API',
#         'auth': 'Autenticación y seguridad',
#         'settings': 'Configuraciones del usuario',
#         'utils': 'Utilidades y helpers',
#     },
#     'permissions': {
#         'user.profile': 'Requiere login',
#         'user.list': 'Requiere permisos de administrador',
#         'user.admin_*': 'Requiere permisos de super usuario',
#         'api.*': 'Requiere autenticación API',
#     }
# }