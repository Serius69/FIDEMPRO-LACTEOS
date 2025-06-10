"""
URLs mejoradas para el sistema de usuarios
Incluye rutas optimizadas, API endpoints, middleware de seguridad y mejor organización
"""

from django.urls import path, include, re_path
from django.views.generic import TemplateView, RedirectView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from . import views

app_name = "user"

# Decorador personalizado para vistas de admin
def admin_required(view_func):
    """Decorador que requiere que el usuario sea staff"""
    decorated_view_func = login_required(
        user_passes_test(
            lambda u: u.is_staff,
            login_url='account_login',
            redirect_field_name='next'
        )(view_func)
    )
    return decorated_view_func

# URLs principales de perfil de usuario
profile_patterns = [
    path("", 
        login_required(views.profile_product_variable_list_view), 
        name="user.profile"
    ),
    
    path("settings/", 
        login_required(views.pages_profile_settings), 
        name="user.profile_settings"
    ),
    
    path("edit/", 
        RedirectView.as_view(pattern_name='user:user.profile_settings', permanent=True), 
        name="user.profile_edit"
    ),
    
    # path("public/<str:username>/", 
    #     cache_page(60 * 5)(views.public_profile_view), 
    #     name="user.public_profile"
    # ),
    
    # path("completeness/", 
    #     login_required(views.profile_completeness_api), 
    #     name="user.profile_completeness"
    # ),
]

# URLs de gestión de usuarios (solo para administradores)
user_management_patterns = [
    path("list/", 
        admin_required(views.user_list_view), 
        name="user.list"
    ),
    
    path("create/", 
        admin_required(views.create_user_view), 
        name='user.create'
    ),
    
    path("edit/<int:user_id>/", 
        admin_required(views.update_user_view), 
        name='user.edit'
    ),
    
    path("delete/<int:user_id>/", 
        admin_required(views.delete_user_view_as_admin), 
        name='user.delete'
    ),
    
    path("bulk-delete/", 
        admin_required(views.bulk_delete_users_view), 
        name='user.bulk_delete'
    ),
    
    path("toggle-status/<int:user_id>/", 
        admin_required(views.toggle_user_status_view), 
        name='user.toggle_status'
    ),
    
    # path("export/", 
    #     admin_required(views.export_users_view), 
    #     name='user.export'
    # ),
    
    # path("import/", 
    #     admin_required(views.import_users_view), 
    #     name='user.import'
    # ),
    
    # # Vista de detalles de usuario para admin
    # path("details/<int:user_id>/", 
    #     admin_required(views.user_details_view), 
    #     name='user.details'
    # ),
]

# URLs de autenticación y seguridad
auth_patterns = [
    path("password/change/", 
        login_required(views.change_password), 
        name='password.change'
    ),
    
    path("password/reset/", 
        TemplateView.as_view(template_name='registration/password_reset_form.html'), 
        name='password.reset'
    ),
    
    path("password/reset/done/", 
        TemplateView.as_view(template_name='registration/password_reset_done.html'), 
        name='password.reset.done'
    ),
    
    path("password/reset/<uidb64>/<token>/", 
        TemplateView.as_view(template_name='registration/password_reset_confirm.html'), 
        name='password.reset.confirm'
    ),
    
    path("password/reset/complete/", 
        TemplateView.as_view(template_name='registration/password_reset_complete.html'), 
        name='password.reset.complete'
    ),
    
    path("deactivate/", 
        login_required(views.deactivate_account), 
        name='user.deactivate_account'
    ),
    
    # path("reactivate/", 
    #     views.reactivate_account_view, 
    #     name='user.reactivate_account'
    # ),
    
    path("cancel-deactivation/", 
        login_required(views.cancel_deactivation), 
        name='user.cancel_deactivation'
    ),
    
    # # Seguridad adicional
    # path("security/", 
    #     login_required(views.security_settings_view), 
    #     name='user.security'
    # ),
    
    # path("security/2fa/enable/", 
    #     login_required(views.enable_2fa_view), 
    #     name='user.2fa.enable'
    # ),
    
    # path("security/2fa/disable/", 
    #     login_required(views.disable_2fa_view), 
    #     name='user.2fa.disable'
    # ),
    
    # path("security/sessions/", 
    #     login_required(views.active_sessions_view), 
    #     name='user.sessions'
    # ),
    
    # path("security/sessions/terminate/<str:session_key>/", 
    #     login_required(views.terminate_session_view), 
    #     name='user.session.terminate'
    # ),
]

# URLs de API para AJAX y funcionalidades avanzadas
api_patterns = [
    # API v1
    path("api/v1/profile/<int:user_id>/", 
        views.user_api_detail, 
        name='user.api.detail'
    ),
    
    # path("api/v1/profile/update/", 
    #     login_required(views.profile_api_update), 
    #     name='user.api.profile_update'
    # ),
    
    # path("api/v1/preferences/", 
    #     login_required(views.preferences_api_view), 
    #     name='user.api.preferences'
    # ),
    
    # path("api/v1/preferences/update/", 
    #     login_required(views.preferences_api_update), 
    #     name='user.api.preferences_update'
    # ),
    
    # path("api/v1/activity/", 
    #     login_required(views.activity_api_view), 
    #     name='user.api.activity'
    # ),
    
    # path("api/v1/search/", 
    #     login_required(views.user_search_api), 
    #     name='user.api.search'
    # ),
    
    # path("api/v1/upload/avatar/", 
    #     login_required(views.upload_avatar_api), 
    #     name='user.api.upload_avatar'
    # ),
    
    # path("api/v1/notifications/", 
    #     login_required(views.notifications_api_view), 
    #     name='user.api.notifications'
    # ),
    
    # path("api/v1/notifications/mark-read/<int:notification_id>/", 
    #     login_required(views.mark_notification_read_api), 
    #     name='user.api.notification_read'
    # ),
    
    # # Webhooks (requieren autenticación especial)
    # path("api/webhooks/github/", 
    #     csrf_exempt(views.github_webhook_view), 
    #     name='user.webhook.github'
    # ),
    
    # path("api/webhooks/stripe/", 
    #     csrf_exempt(views.stripe_webhook_view), 
    #     name='user.webhook.stripe'
    # ),
]

# URLs de administración avanzada
admin_patterns = [
    # path("admin/dashboard/", 
    #     admin_required(views.admin_dashboard_view), 
    #     name='user.admin_dashboard'
    # ),
    
    path("admin/activity/", 
        admin_required(views.UserActivityLogView.as_view()), 
        name='user.admin_activity'
    ),
    
    # path("admin/analytics/", 
    #     admin_required(views.admin_analytics_view), 
    #     name='user.admin_analytics'
    # ),
    
    # path("admin/reports/", 
    #     admin_required(views.admin_reports_view), 
    #     name='user.admin_reports'
    # ),
    
    # path("admin/reports/generate/", 
    #     admin_required(views.generate_report_view), 
    #     name='user.admin_reports_generate'
    # ),
    
    # path("admin/bulk-actions/", 
    #     admin_required(views.admin_bulk_actions_view), 
    #     name='user.admin_bulk_actions'
    # ),
    
    # path("admin/audit-log/", 
    #     admin_required(views.audit_log_view), 
    #     name='user.admin_audit_log'
    # ),
    
    # path("admin/system-health/", 
    #     admin_required(views.system_health_view), 
    #     name='user.admin_system_health'
    # ),
]

# URLs de configuración y preferencias
settings_patterns = [
    path("settings/profile/", 
        login_required(views.pages_profile_settings), 
        name='user.settings_profile'
    ),
    
    # path("settings/security/", 
    #     login_required(views.security_settings_view), 
    #     name='user.settings_security'
    # ),
    
    # path("settings/privacy/", 
    #     login_required(views.privacy_settings_view), 
    #     name='user.settings_privacy'
    # ),
    
    # path("settings/notifications/", 
    #     login_required(views.notification_settings_view), 
    #     name='user.settings_notifications'
    # ),
    
    # path("settings/preferences/", 
    #     login_required(views.preferences_settings_view), 
    #     name='user.settings_preferences'
    # ),
    
    # path("settings/integrations/", 
    #     login_required(views.integrations_settings_view), 
    #     name='user.settings_integrations'
    # ),
    
    # path("settings/data/", 
    #     login_required(views.data_settings_view), 
    #     name='user.settings_data'
    # ),
    
    # path("settings/data/export/", 
    #     login_required(views.export_user_data_view), 
    #     name='user.settings_data_export'
    # ),
    
    # path("settings/data/delete/", 
    #     login_required(views.delete_user_data_view), 
    #     name='user.settings_data_delete'
    # ),
]

# # URLs de utilidades y helpers
# utility_patterns = [
#     path("avatar/upload/", 
#         login_required(views.avatar_upload_view), 
#         name='user.avatar_upload'
#     ),
    
#     path("avatar/remove/", 
#         login_required(views.avatar_remove_view), 
#         name='user.avatar_remove'
#     ),
    
#     path("export/data/", 
#         login_required(views.export_user_data_view), 
#         name='user.export_data'
#     ),
    
#     path("import/contacts/", 
#         login_required(views.import_contacts_view), 
#         name='user.import_contacts'
#     ),
    
#     path("search/", 
#         login_required(views.user_search_view), 
#         name='user.search'
#     ),
    
#     path("autocomplete/", 
#         login_required(views.user_autocomplete_view), 
#         name='user.autocomplete'
#     ),
    
#     path("validate/username/", 
#         views.validate_username_view, 
#         name='user.validate_username'
#     ),
    
#     path("validate/email/", 
#         views.validate_email_view, 
#         name='user.validate_email'
#     ),
# ]

# URLs de funcionalidades sociales
# social_patterns = [
#     path("following/", 
#         login_required(views.following_list_view), 
#         name='user.following'
#     ),
    
#     path("followers/", 
#         login_required(views.followers_list_view), 
#         name='user.followers'
#     ),
    
#     path("follow/<int:user_id>/", 
#         login_required(views.follow_user_view), 
#         name='user.follow'
#     ),
    
#     path("unfollow/<int:user_id>/", 
#         login_required(views.unfollow_user_view), 
#         name='user.unfollow'
#     ),
    
#     path("block/<int:user_id>/", 
#         login_required(views.block_user_view), 
#         name='user.block'
#     ),
    
#     path("unblock/<int:user_id>/", 
#         login_required(views.unblock_user_view), 
#         name='user.unblock'
#     ),
    
#     path("blocked/", 
#         login_required(views.blocked_users_view), 
#         name='user.blocked'
#     ),
# ]

# URLs principales - consolidando todos los patrones
urlpatterns = [
    # Raíz - redirige al perfil
    path("", RedirectView.as_view(pattern_name='user:user.profile', permanent=False)),
    
    # Perfil de usuario
    path("profile/", include(profile_patterns)),
    
    # Gestión de usuarios (administradores)
    path("manage/", include(user_management_patterns)),
    
    # Autenticación y seguridad
    path("auth/", include(auth_patterns)),
    
    # API endpoints
    path("", include(api_patterns)),
    
    # Administración avanzada
    path("", include(admin_patterns)),
    
    # Configuraciones
    path("", include(settings_patterns)),
    
    # # Utilidades
    # path("utils/", include(utility_patterns)),
    
    # # Funcionalidades sociales
    # path("social/", include(social_patterns)),
    
    # URLs de compatibilidad y aliases
    path("update/<int:user_id>/", 
        RedirectView.as_view(pattern_name='user:user.edit', permanent=True), 
        name='user.update'
    ),
    
    path("overview/", 
        RedirectView.as_view(pattern_name='user:user.profile', permanent=True), 
        name='user.overview'
    ),
    
    # Gestión directa (sin prefijo manage/)
    path("list/", 
        RedirectView.as_view(pattern_name='user:user.list', permanent=False)
    ),
    
    path("create/", 
        RedirectView.as_view(pattern_name='user:user.create', permanent=False)
    ),
]

# URLs adicionales para funcionalidades específicas
extended_patterns = [
    # Gestión de sesiones
    # path("sessions/", 
    #     login_required(views.sessions_list_view), 
    #     name='user.sessions_list'
    # ),
    
    # path("sessions/terminate/<str:session_key>/", 
    #     login_required(views.session_terminate_view), 
    #     name='user.session_terminate'
    # ),
    
    # path("sessions/terminate-all/", 
    #     login_required(views.sessions_terminate_all_view), 
    #     name='user.sessions_terminate_all'
    # ),
    
    # Logs de actividad
    path("activity/", 
        login_required(views.UserActivityLogView.as_view()), 
        name='user.activity'
    ),
    
    # path("activity/<int:log_id>/", 
    #     login_required(views.activity_detail_view), 
    #     name='user.activity_detail'
    # ),
    
    # path("activity/export/", 
    #     login_required(views.export_activity_log_view), 
    #     name='user.activity_export'
    # ),
    
    # # Configuración avanzada
    # path("advanced/", 
    #     login_required(views.advanced_settings_view), 
    #     name='user.advanced_settings'
    # ),
    
    # path("developer/", 
    #     login_required(views.developer_settings_view), 
    #     name='user.developer_settings'
    # ),
    
    # path("developer/tokens/", 
    #     login_required(views.api_tokens_view), 
    #     name='user.api_tokens'
    # ),
    
    # path("developer/tokens/create/", 
    #     login_required(views.create_api_token_view), 
    #     name='user.api_token_create'
    # ),
    
    # path("developer/tokens/revoke/<int:token_id>/", 
    #     login_required(views.revoke_api_token_view), 
    #     name='user.api_token_revoke'
    # ),
    
    # # Integraciones
    # path("integrations/", 
    #     login_required(views.integrations_list_view), 
    #     name='user.integrations_list'
    # ),
    
    # path("integrations/connect/<str:provider>/", 
    #     login_required(views.connect_integration_view), 
    #     name='user.integration_connect'
    # ),
    
    # path("integrations/disconnect/<str:provider>/", 
    #     login_required(views.disconnect_integration_view), 
    #     name='user.integration_disconnect'
    # ),
    
    # path("integrations/oauth/callback/<str:provider>/", 
    #     views.oauth_callback_view, 
    #     name='user.oauth_callback'
    # ),
    
    # Estadísticas y analytics
    # path("stats/", 
    #     login_required(cache_page(60 * 15)(views.user_stats_view)), 
    #     name='user.stats'
    # ),
    
    # path("analytics/", 
    #     login_required(views.user_analytics_view), 
    #     name='user.analytics'
    # ),
    
    # path("analytics/export/", 
    #     login_required(views.export_analytics_view), 
    #     name='user.analytics_export'
    # ),
    
    # Ayuda y soporte
    path("help/", 
        cache_page(60 * 60)(TemplateView.as_view(template_name='user/help.html')), 
        name='user.help'
    ),
    
    # path("support/", 
    #     login_required(views.support_view), 
    #     name='user.support'
    # ),
    
    # path("support/ticket/create/", 
    #     login_required(views.create_support_ticket_view), 
    #     name='user.support_ticket_create'
    # ),
    
    # path("feedback/", 
    #     login_required(views.feedback_view), 
    #     name='user.feedback'
    # ),
    
    # path("feedback/submit/", 
    #     login_required(views.submit_feedback_view), 
    #     name='user.feedback_submit'
    # ),
    
    # # Onboarding y tours
    # path("onboarding/", 
    #     login_required(views.onboarding_view), 
    #     name='user.onboarding'
    # ),
    
    # path("onboarding/complete/", 
    #     login_required(views.complete_onboarding_view), 
    #     name='user.onboarding_complete'
    # ),
    
    # path("tour/", 
    #     login_required(views.tour_view), 
    #     name='user.tour'
    # ),
    
    # path("tour/skip/", 
    #     login_required(views.skip_tour_view), 
    #     name='user.tour_skip'
    # ),
    
    # # Backup y recuperación
    # path("backup/", 
    #     login_required(views.backup_view), 
    #     name='user.backup'
    # ),
    
    # path("backup/create/", 
    #     login_required(views.create_backup_view), 
    #     name='user.backup_create'
    # ),
    
    # path("backup/download/<int:backup_id>/", 
    #     login_required(views.download_backup_view), 
    #     name='user.backup_download'
    # ),
    
    # path("restore/", 
    #     login_required(views.restore_view), 
    #     name='user.restore'
    # ),
    
    # # Notificaciones
    # path("notifications/", 
    #     login_required(views.notifications_view), 
    #     name='user.notifications'
    # ),
    
    # path("notifications/unread/", 
    #     login_required(views.unread_notifications_view), 
    #     name='user.notifications_unread'
    # ),
    
    # path("notifications/mark-all-read/", 
    #     login_required(views.mark_all_notifications_read_view), 
    #     name='user.notifications_mark_all_read'
    # ),
]

# Agregar las URLs extendidas a las principales
# urlpatterns.extend(extended_patterns)

# # URLs de webhook y API externa (para integraciones)
# webhook_patterns = [
#     path("webhooks/social/<str:provider>/", 
#         csrf_exempt(views.social_webhook_view), 
#         name='user.webhook_social'
#     ),
    
#     path("webhooks/payment/", 
#         csrf_exempt(views.payment_webhook_view), 
#         name='user.webhook_payment'
#     ),
    
#     path("webhooks/notification/", 
#         csrf_exempt(views.notification_webhook_view), 
#         name='user.webhook_notification'
#     ),
# ]

# URLs para testing y desarrollo (solo en DEBUG)
# if settings.DEBUG:
#     debug_patterns = [
#         path("debug/profile/", 
#             login_required(views.debug_profile_view), 
#             name='user.debug_profile'
#         ),
        
#         path("debug/permissions/", 
#             login_required(views.debug_permissions_view), 
#             name='user.debug_permissions'
#         ),
        
#         path("debug/sessions/", 
#             login_required(views.debug_sessions_view), 
#             name='user.debug_sessions'
#         ),
        
#         path("debug/cache/", 
#             admin_required(views.debug_cache_view), 
#             name='user.debug_cache'
#         ),
        
#         path("debug/email/test/", 
#             admin_required(views.test_email_view), 
#             name='user.test_email'
#         ),
        
#         path("debug/notifications/test/", 
#             login_required(views.test_notifications_view), 
#             name='user.test_notifications'
#         ),
        
#         path("debug/error/404/", 
#             TemplateView.as_view(template_name='404.html'), 
#             name='user.test_404'
#         ),
        
#         path("debug/error/500/", 
#             views.test_500_view, 
#             name='user.test_500'
#         ),
#     ]
#     urlpatterns.extend(debug_patterns)

# # Agregar webhooks
# urlpatterns.extend(webhook_patterns)

# # Handlers personalizados para errores
# handler404 = 'user.views.custom_404'
# handler500 = 'user.views.custom_500'
# handler403 = 'user.views.custom_403'
# handler400 = 'user.views.custom_400'

# # Metadata para documentación automática y API discovery
# urlpatterns_metadata = {
#     'version': '2.1.0',
#     'api_version': 'v1',
#     'description': 'Sistema completo de gestión de usuarios con funcionalidades avanzadas',
#     'endpoints': {
#         'profile': {
#             'description': 'Gestión del perfil de usuario',
#             'authentication': 'required',
#             'methods': ['GET', 'POST', 'PUT', 'PATCH']
#         },
#         'admin': {
#             'description': 'Administración de usuarios',
#             'authentication': 'admin',
#             'methods': ['GET', 'POST', 'PUT', 'DELETE']
#         },
#         'api': {
#             'description': 'Endpoints de API REST',
#             'authentication': 'token_or_session',
#             'rate_limit': '100/hour',
#             'version': 'v1'
#         },
#         'auth': {
#             'description': 'Autenticación y seguridad',
#             'authentication': 'varies',
#             'methods': ['GET', 'POST']
#         },
#         'webhooks': {
#             'description': 'Endpoints para webhooks externos',
#             'authentication': 'signature',
#             'methods': ['POST']
#         }
#     },
#     'permissions': {
#         'user.profile': 'Login requerido',
#         'user.list': 'Permisos de administrador requeridos',
#         'user.admin_*': 'Permisos de super usuario requeridos',
#         'api.*': 'Autenticación por token o sesión',
#         'webhooks.*': 'Verificación de firma requerida'
#     },
#     'rate_limits': {
#         'default': '60/hour',
#         'authenticated': '100/hour',
#         'admin': '1000/hour',
#         'api': '100/hour'
#     },
#     'cache_policies': {
#         'public_profiles': '5 minutes',
#         'user_stats': '15 minutes',
#         'help_pages': '1 hour'
#     }
# }

# # Configuración de API versioning
# API_VERSIONS = {
#     'v1': {
#         'status': 'stable',
#         'deprecated': False,
#         'sunset': None
#     },
#     'v2': {
#         'status': 'beta',
#         'deprecated': False,
#         'sunset': None
#     }
# }