from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash, login
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError
from django.db import transaction
from django.conf import settings
import json
import logging

from .forms import UserForm, UserProfileForm
from .models import UserProfile, ActivityLog
from product.models import Product
from business.models import Business
from variable.models import Variable

# Configurar logger
logger = logging.getLogger(__name__)

def is_admin(user):
    """Verificar si el usuario es administrador"""
    return user.is_authenticated and user.is_staff

@login_required
def pages_profile_settings(request):
    """Vista para configuraciones del perfil del usuario"""
    try:
        user = request.user
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        if request.method == 'POST':
            return handle_profile_update(request, user, profile)
        
        context = {
            'completeness_percentage': calculate_profile_completeness(profile),
            'user': user,
            'profile': profile,
            'selected_state': profile.state,
            'selected_country': profile.country,
        }
        return render(request, 'user/profile-settings.html', context)
    
    except Exception as e:
        logger.error(f"Error in profile settings for user {request.user.id}: {str(e)}")
        messages.error(request, "Error al cargar la configuración del perfil.")
        return redirect('user:user.profile')

@transaction.atomic
def handle_profile_update(request, user, profile):
    """Manejar la actualización del perfil del usuario"""
    try:
        # Actualizar datos del usuario
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.email = request.POST.get('email', '').strip()
        
        # Validar email único
        if User.objects.filter(email=user.email).exclude(id=user.id).exists():
            return JsonResponse({
                'success': False,
                'errors': {'email': ['Este correo electrónico ya está en uso.']}
            })
        
        user.full_clean()
        user.save()
        
        # Actualizar perfil
        profile.state = request.POST.get('state', '').strip()
        profile.country = request.POST.get('country', '').strip()
        profile.bio = request.POST.get('bio', '').strip()[:500]  # Limitar a 500 caracteres
        
        # Manejar imagen de perfil
        if 'profile_image' in request.FILES:
            profile.image_src = request.FILES['profile_image']
        
        profile.full_clean()
        profile.save()
        
        # Registrar actividad
        ActivityLog.objects.create(
            user=user,
            action="Perfil actualizado",
            details=f"Usuario {user.username} actualizó su perfil"
        )
        
        messages.success(request, 'Perfil actualizado correctamente.')
        return JsonResponse({'success': True})
        
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'errors': e.message_dict if hasattr(e, 'message_dict') else {'general': [str(e)]}
        })
    except Exception as e:
        logger.error(f"Error updating profile for user {user.id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'errors': {'general': ['Error interno del servidor.']}
        })

@login_required
def profile_product_variable_list_view(request):
    """Vista principal del perfil con productos, empresas y variables"""
    try:
        user = request.user
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # Obtener datos con optimización de consultas
        businesses = Business.objects.filter(
            fk_user=user, 
            is_active=True
        ).select_related('fk_user').prefetch_related('products').order_by('-last_updated')
        
        products = Product.objects.filter(
            fk_business__fk_user=user, 
            is_active=True
        ).select_related('fk_business').order_by('-last_updated')
        
        variables = Variable.objects.filter(
            fk_product__fk_business__fk_user=user, 
            is_active=True
        ).select_related('fk_product', 'fk_product__fk_business').order_by('-date_created')
        
        # Paginación
        page = request.GET.get('page', 1)
        products_paginated = paginate_queryset(products, page, 10)
        variables_paginated = paginate_queryset(variables, page, 10)
        
        # Contadores
        counts = {
            'business_count': businesses.count(),
            'product_count': products.count(),
            'variable_count': variables.count(),
        }
        
        context = {
            'products': products_paginated,
            'businesses': businesses,
            'variables': variables_paginated,
            'completeness_percentage': calculate_profile_completeness(profile),
            **counts
        }
        
        return render(request, 'user/profile.html', context)
        
    except Exception as e:
        logger.error(f"Error in profile view for user {request.user.id}: {str(e)}")
        messages.error(request, "Error al cargar el perfil.")
        return render(request, 'user/profile.html', {'error': True})

def calculate_profile_completeness(profile):
    """Calcular el porcentaje de completitud del perfil"""
    if profile.is_profile_complete():
        return 100
    
    # Campos requeridos para un perfil completo
    required_fields = ['state', 'country', 'bio']
    user_fields = ['first_name', 'last_name', 'email']
    
    total_fields = len(required_fields) + len(user_fields)
    completed_fields = 0
    
    # Verificar campos del perfil
    for field in required_fields:
        if getattr(profile, field, '').strip():
            completed_fields += 1
    
    # Verificar campos del usuario
    for field in user_fields:
        if getattr(profile.user, field, '').strip():
            completed_fields += 1
    
    return int((completed_fields / total_fields) * 100)

def paginate_queryset(queryset, page, items_per_page=10):
    """Función helper para paginación"""
    paginator = Paginator(queryset, items_per_page)
    try:
        return paginator.page(page)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)

@user_passes_test(is_admin)
def user_list_view(request):
    """Vista de lista de usuarios (solo para administradores)"""
    try:
        # Filtros
        search_query = request.GET.get('search', '').strip()
        status_filter = request.GET.get('status', '')
        
        users = User.objects.select_related('userprofile').annotate(
            business_count=Count('business', filter=Q(business__is_active=True)),
            product_count=Count('business__products', filter=Q(business__products__is_active=True))
        )
        
        # Aplicar filtros
        if search_query:
            users = users.filter(
                Q(username__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query)
            )
        
        if status_filter == 'active':
            users = users.filter(is_active=True)
        elif status_filter == 'inactive':
            users = users.filter(is_active=False)
        
        users = users.order_by('-date_joined')
        
        # Paginación
        page = request.GET.get('page', 1)
        users_paginated = paginate_queryset(users, page, 20)
        
        context = {
            'users': users_paginated,
            'search_query': search_query,
            'status_filter': status_filter,
            'total_users': users.count(),
            'active_users': users.filter(is_active=True).count(),
            'inactive_users': users.filter(is_active=False).count(),
        }
        
        return render(request, 'user/user-list.html', context)
        
    except Exception as e:
        logger.error(f"Error in user list view: {str(e)}")
        messages.error(request, "Error al cargar la lista de usuarios.")
        return render(request, 'user/user-list.html', {'error': True})

@user_passes_test(is_admin)
@require_http_methods(["POST"])
@transaction.atomic
def create_user_view(request):
    """Crear nuevo usuario (solo para administradores)"""
    try:
        form_data = {
            'username': request.POST.get('username', '').strip(),
            'email': request.POST.get('email', '').strip(),
            'first_name': request.POST.get('first_name', '').strip(),
            'last_name': request.POST.get('last_name', '').strip(),
            'password': request.POST.get('password', ''),
            'confirm_password': request.POST.get('confirm_password', ''),
            'is_staff': request.POST.get('is_staff', 'false') == 'true',
            'is_active': request.POST.get('is_active', 'true') == 'true',
        }
        
        # Validaciones
        errors = validate_user_form(form_data)
        if errors:
            return JsonResponse({'success': False, 'errors': errors})
        
        # Crear usuario
        user = User.objects.create_user(
            username=form_data['username'],
            email=form_data['email'],
            password=form_data['password'],
            first_name=form_data['first_name'],
            last_name=form_data['last_name'],
            is_staff=form_data['is_staff'],
            is_active=form_data['is_active']
        )
        
        # Registrar actividad
        ActivityLog.objects.create(
            user=request.user,
            action="Usuario creado",
            details=f"Administrador {request.user.username} creó el usuario {user.username}"
        )
        
        messages.success(request, f'Usuario {user.username} creado correctamente.')
        return JsonResponse({'success': True, 'user_id': user.id})
        
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return JsonResponse({
            'success': False, 
            'errors': {'general': ['Error interno del servidor.']}
        })

@user_passes_test(is_admin)
@require_http_methods(["POST"])
@transaction.atomic
def update_user_view(request, user_id):
    """Actualizar usuario existente (solo para administradores)"""
    try:
        user = get_object_or_404(User, pk=user_id)
        
        # Prevenir que un admin se degrade a sí mismo
        if user == request.user and request.POST.get('is_staff') == 'false':
            return JsonResponse({
                'success': False,
                'errors': {'is_staff': ['No puedes quitarte los privilegios de administrador.']}
            })
        
        form_data = {
            'username': request.POST.get('username', '').strip(),
            'email': request.POST.get('email', '').strip(),
            'first_name': request.POST.get('first_name', '').strip(),
            'last_name': request.POST.get('last_name', '').strip(),
            'is_staff': request.POST.get('is_staff', 'false') == 'true',
            'is_active': request.POST.get('is_active', 'true') == 'true',
        }
        
        # Validaciones (sin contraseña para actualización)
        errors = validate_user_form(form_data, user=user, is_update=True)
        if errors:
            return JsonResponse({'success': False, 'errors': errors})
        
        # Actualizar usuario
        for field, value in form_data.items():
            setattr(user, field, value)
        
        user.full_clean()
        user.save()
        
        # Registrar actividad
        ActivityLog.objects.create(
            user=request.user,
            action="Usuario actualizado",
            details=f"Administrador {request.user.username} actualizó el usuario {user.username}"
        )
        
        messages.success(request, f'Usuario {user.username} actualizado correctamente.')
        return JsonResponse({'success': True})
        
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'errors': e.message_dict if hasattr(e, 'message_dict') else {'general': [str(e)]}
        })
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'errors': {'general': ['Error interno del servidor.']}
        })

def validate_user_form(form_data, user=None, is_update=False):
    """Validar datos del formulario de usuario"""
    errors = {}
    
    # Validar username
    if not form_data['username']:
        errors['username'] = ['El nombre de usuario es requerido.']
    elif len(form_data['username']) < 3:
        errors['username'] = ['El nombre de usuario debe tener al menos 3 caracteres.']
    elif User.objects.filter(username=form_data['username']).exclude(id=user.id if user else None).exists():
        errors['username'] = ['Este nombre de usuario ya está en uso.']
    
    # Validar email
    if not form_data['email']:
        errors['email'] = ['El correo electrónico es requerido.']
    elif User.objects.filter(email=form_data['email']).exclude(id=user.id if user else None).exists():
        errors['email'] = ['Este correo electrónico ya está en uso.']
    
    # Validar contraseña (solo para creación)
    if not is_update:
        if not form_data.get('password'):
            errors['password'] = ['La contraseña es requerida.']
        elif len(form_data['password']) < 8:
            errors['password'] = ['La contraseña debe tener al menos 8 caracteres.']
        elif form_data['password'] != form_data.get('confirm_password'):
            errors['confirm_password'] = ['Las contraseñas no coinciden.']
    
    return errors

@user_passes_test(is_admin)
@require_http_methods(["POST"])
@transaction.atomic
def delete_user_view_as_admin(request, user_id):
    """Eliminar usuario como administrador"""
    try:
        user = get_object_or_404(User, pk=user_id)
        
        # Prevenir que un admin se elimine a sí mismo
        if user == request.user:
            return JsonResponse({
                'success': False,
                'error': 'No puedes eliminar tu propia cuenta.'
            })
        
        username = user.username
        user.delete()
        
        # Registrar actividad
        ActivityLog.objects.create(
            user=request.user,
            action="Usuario eliminado",
            details=f"Administrador {request.user.username} eliminó el usuario {username}"
        )
        
        messages.success(request, f"Usuario {username} eliminado correctamente.")
        return JsonResponse({'success': True})
        
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor.'
        })

@user_passes_test(is_admin)
@require_http_methods(["POST"])
@transaction.atomic
def bulk_delete_users_view(request):
    """Eliminar múltiples usuarios"""
    try:
        data = json.loads(request.body)
        user_ids = data.get('user_ids', [])
        
        if not user_ids:
            return JsonResponse({'success': False, 'error': 'No se seleccionaron usuarios.'})
        
        # Prevenir eliminar al usuario actual
        if str(request.user.id) in user_ids:
            return JsonResponse({
                'success': False,
                'error': 'No puedes eliminar tu propia cuenta.'
            })
        
        users = User.objects.filter(id__in=user_ids)
        count = users.count()
        usernames = list(users.values_list('username', flat=True))
        
        users.delete()
        
        # Registrar actividad
        ActivityLog.objects.create(
            user=request.user,
            action="Eliminación masiva de usuarios",
            details=f"Administrador {request.user.username} eliminó {count} usuarios: {', '.join(usernames)}"
        )
        
        messages.success(request, f"{count} usuarios eliminados correctamente.")
        return JsonResponse({'success': True, 'deleted_count': count})
        
    except Exception as e:
        logger.error(f"Error in bulk delete: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor.'
        })

@user_passes_test(is_admin)
@require_http_methods(["POST"])
@transaction.atomic
def toggle_user_status_view(request, user_id):
    """Cambiar estado activo/inactivo de usuario"""
    try:
        data = json.loads(request.body)
        active = data.get('active', True)
        
        user = get_object_or_404(User, pk=user_id)
        
        # Prevenir desactivar al usuario actual
        if user == request.user and not active:
            return JsonResponse({
                'success': False,
                'error': 'No puedes desactivar tu propia cuenta.'
            })
        
        user.is_active = active
        user.save()
        
        # Registrar actividad
        action = "activado" if active else "desactivado"
        ActivityLog.objects.create(
            user=request.user,
            action=f"Usuario {action}",
            details=f"Administrador {request.user.username} {action} el usuario {user.username}"
        )
        
        messages.success(request, f"Usuario {user.username} {action} correctamente.")
        return JsonResponse({'success': True})
        
    except Exception as e:
        logger.error(f"Error toggling user status {user_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor.'
        })

@login_required
@require_http_methods(["POST"])
def change_password(request):
    """Cambiar contraseña del usuario actual"""
    try:
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            
            # Registrar actividad
            ActivityLog.objects.create(
                user=user,
                action="Contraseña cambiada",
                details=f"Usuario {user.username} cambió su contraseña"
            )
            
            messages.success(request, 'Tu contraseña fue cambiada correctamente.')
            return JsonResponse({'success': True})
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    except Exception as e:
        logger.error(f"Error changing password for user {request.user.id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor.'
        })

@login_required
@require_http_methods(["POST"])
@transaction.atomic
def deactivate_account(request):
    """Desactivar cuenta del usuario actual"""
    try:
        password = request.POST.get('password')
        
        if not password:
            messages.error(request, 'La contraseña es requerida.')
            return redirect('user:user.profile_settings')
        
        if not request.user.check_password(password):
            messages.error(request, 'Contraseña incorrecta. Inténtalo de nuevo.')
            return redirect('user:user.profile_settings')
        
        # Registrar actividad antes de desactivar
        ActivityLog.objects.create(
            user=request.user,
            action="Cuenta desactivada",
            details=f"Usuario {request.user.username} desactivó su propia cuenta"
        )
        
        request.user.is_active = False
        request.user.save()
        
        messages.success(request, 'Tu cuenta ha sido desactivada correctamente.')
        return redirect('account_logout')
        
    except Exception as e:
        logger.error(f"Error deactivating account for user {request.user.id}: {str(e)}")
        messages.error(request, 'Error al desactivar la cuenta.')
        return redirect('user:user.profile_settings')

@login_required
def cancel_deactivation(request):
    """Cancelar desactivación de cuenta"""
    messages.info(request, 'Operación cancelada.')
    return redirect('user:user.profile_settings')

@login_required
def user_api_detail(request, user_id):
    """API endpoint para obtener detalles de usuario"""
    try:
        # Solo permitir ver datos propios o ser admin
        if request.user.id != user_id and not request.user.is_staff:
            return JsonResponse({'error': 'No autorizado'}, status=403)
        
        user = get_object_or_404(User, pk=user_id)
        profile = getattr(user, 'userprofile', None)
        
        data = {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'is_active': user.is_active,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
        }
        
        if profile:
            data.update({
                'state': profile.state,
                'country': profile.country,
                'bio': profile.bio,
                'image_url': profile.get_photo_url(),
            })
        
        return JsonResponse(data)
        
    except Exception as e:
        logger.error(f"Error in user API detail for user {user_id}: {str(e)}")
        return JsonResponse({'error': 'Error interno del servidor'}, status=500)

# Class-based views para funcionalidades avanzadas
class UserActivityLogView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Vista de logs de actividad (solo para administradores)"""
    model = ActivityLog
    template_name = 'user/activity_log.html'
    context_object_name = 'activities'
    paginate_by = 50
    ordering = ['-timestamp']
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('user')
        
        # Filtros
        user_filter = self.request.GET.get('user')
        action_filter = self.request.GET.get('action')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if user_filter:
            queryset = queryset.filter(user__username__icontains=user_filter)
        
        if action_filter:
            queryset = queryset.filter(action__icontains=action_filter)
        
        if date_from:
            queryset = queryset.filter(timestamp__date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(timestamp__date__lte=date_to)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'user_filter': self.request.GET.get('user', ''),
            'action_filter': self.request.GET.get('action', ''),
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
        })
        return context
    
def custom_404(request, exception):
    return render(request, '404.html', status=404)