from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash, login
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden, Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count, Prefetch
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction, IntegrityError
from django.conf import settings
from django.core.cache import cache
from django.utils.html import escape
import json
import logging
from typing import Dict, Any, Optional

from .forms import UserForm, UserProfileForm
from .models import UserProfile, ActivityLog
from product.models import Product
from business.models import Business
from variable.models import Variable

# Configurar logger
logger = logging.getLogger(__name__)

# Decorador personalizado para manejo de errores
def handle_errors(view_func):
    """Decorador para manejar errores comunes en las vistas"""
    def wrapped_view(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except PermissionDenied:
            logger.warning(f"Permission denied for user {request.user.id} accessing {request.path}")
            messages.error(request, "No tienes permisos para realizar esta acción.")
            return redirect('user:user.profile')
        except ValidationError as e:
            logger.error(f"Validation error in {view_func.__name__}: {str(e)}")
            messages.error(request, f"Error de validación: {str(e)}")
            return redirect(request.META.get('HTTP_REFERER', 'user:user.profile'))
        except Exception as e:
            logger.exception(f"Unexpected error in {view_func.__name__}: {str(e)}")
            if settings.DEBUG:
                raise
            messages.error(request, "Ha ocurrido un error inesperado. Por favor, intenta de nuevo.")
            return redirect('user:user.profile')
    return wrapped_view

def is_admin(user):
    """Verificar si el usuario es administrador"""
    return user.is_authenticated and user.is_staff

def get_client_ip(request) -> str:
    """Obtener la IP real del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def sanitize_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitizar datos de entrada para prevenir XSS"""
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = escape(value.strip())
        else:
            sanitized[key] = value
    return sanitized

@login_required
@handle_errors
@ensure_csrf_cookie
def pages_profile_settings(request):
    """Vista para configuraciones del perfil del usuario con caché"""
    try:
        user = request.user
        cache_key = f'profile_{user.id}'
        
        # Intentar obtener del caché
        profile = cache.get(cache_key)
        if not profile:
            profile, created = UserProfile.objects.get_or_create(user=user)
            cache.set(cache_key, profile, 300)  # Cache por 5 minutos
        
        if request.method == 'POST':
            # Invalidar caché al actualizar
            cache.delete(cache_key)
            return handle_profile_update(request, user, profile)
        
        # Obtener estados y países para los dropdowns
        states = get_bolivian_states()
        countries = get_south_american_countries()
        
        context = {
            'completeness_percentage': calculate_profile_completeness(profile),
            'user': user,
            'profile': profile,
            'states': states,
            'countries': countries,
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
    """Manejar la actualización del perfil del usuario con validación mejorada"""
    try:
        # Sanitizar datos de entrada
        cleaned_data = sanitize_input({
            'first_name': request.POST.get('first_name', ''),
            'last_name': request.POST.get('last_name', ''),
            'email': request.POST.get('email', ''),
            'state': request.POST.get('state', ''),
            'country': request.POST.get('country', ''),
            'bio': request.POST.get('bio', '')[:500],
        })
        
        # Validar email único con bloqueo optimista
        if cleaned_data['email']:
            if User.objects.filter(email=cleaned_data['email']).exclude(id=user.id).exists():
                return JsonResponse({
                    'success': False,
                    'errors': {'email': ['Este correo electrónico ya está en uso.']}
                }, status=400)
        
        # Actualizar usuario
        user.first_name = cleaned_data['first_name']
        user.last_name = cleaned_data['last_name']
        user.email = cleaned_data['email']
        
        user.full_clean()
        user.save()
        
        # Actualizar perfil
        profile.state = cleaned_data['state']
        profile.country = cleaned_data['country']
        profile.bio = cleaned_data['bio']
        
        # Manejar imagen de perfil con validación
        if 'profile_image' in request.FILES:
            image = request.FILES['profile_image']
            # Validar tamaño y tipo
            if image.size > 5 * 1024 * 1024:  # 5MB
                raise ValidationError("La imagen no debe superar los 5MB.")
            
            allowed_types = ['image/jpeg', 'image/png', 'image/webp']
            if image.content_type not in allowed_types:
                raise ValidationError("Formato de imagen no válido.")
            
            profile.image_src = image
        
        profile.full_clean()
        profile.save()
        
        # Registrar actividad con IP
        ActivityLog.log_activity(
            user=user,
            action="Perfil actualizado",
            details=f"Usuario {user.username} actualizó su perfil",
            ip_address=get_client_ip(request),
            request=request,
            category="profile"
        )
        
        messages.success(request, 'Perfil actualizado correctamente.')
        return JsonResponse({'success': True, 'message': 'Perfil actualizado correctamente'})
        
    except ValidationError as e:
        logger.warning(f"Validation error updating profile for user {user.id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'errors': e.message_dict if hasattr(e, 'message_dict') else {'general': [str(e)]}
        }, status=400)
    except IntegrityError as e:
        logger.error(f"Database integrity error for user {user.id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'errors': {'general': ['Error de integridad en la base de datos.']}
        }, status=500)
    except Exception as e:
        logger.exception(f"Unexpected error updating profile for user {user.id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'errors': {'general': ['Error interno del servidor.']}
        }, status=500)

@login_required
@handle_errors
def profile_product_variable_list_view(request):
    """Vista principal del perfil con productos, empresas y variables optimizada"""
    try:
        user = request.user
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # Usar select_related y prefetch_related para optimizar consultas
        businesses = Business.objects.filter(
            fk_user=user, 
            is_active=True
        ).select_related('fk_user').prefetch_related(
            Prefetch('products', queryset=Product.objects.filter(is_active=True))
        ).order_by('-last_updated')[:10]  # Limitar a 10 más recientes
        
        products = Product.objects.filter(
            fk_business__fk_user=user, 
            is_active=True
        ).select_related('fk_business').prefetch_related(
            'variables'
        ).order_by('-last_updated')
        
        variables = Variable.objects.filter(
            fk_product__fk_business__fk_user=user, 
            is_active=True
        ).select_related(
            'fk_product__fk_business'
        ).order_by('-date_created')
        
        # Paginación mejorada
        page = request.GET.get('page', 1)
        try:
            products_paginated = paginate_queryset(products, page, 12)
            variables_paginated = paginate_queryset(variables, page, 15)
        except Http404:
            return redirect('user:user.profile')
        
        # Estadísticas con caché
        cache_key = f'user_stats_{user.id}'
        stats = cache.get(cache_key)
        if not stats:
            stats = {
                'business_count': businesses.count(),
                'product_count': products.count(),
                'variable_count': variables.count(),
                'active_products': products.filter(is_ready=True).count(),
            }
            cache.set(cache_key, stats, 600)  # Cache por 10 minutos
        
        context = {
            'products': products_paginated,
            'businesses': businesses,
            'variables': variables_paginated,
            'completeness_percentage': calculate_profile_completeness(profile),
            'profile': profile,
            **stats
        }
        
        return render(request, 'user/profile.html', context)
        
    except Exception as e:
        logger.exception(f"Critical error in profile view for user {request.user.id}: {str(e)}")
        messages.error(request, "Error crítico al cargar el perfil. El equipo técnico ha sido notificado.")
        context = {'error': True, 'profile': None}
        return render(request, 'user/profile.html', context)

def calculate_profile_completeness(profile) -> int:
    """Calcular el porcentaje de completitud del perfil con caché"""
    if not profile:
        return 0
        
    cache_key = f'profile_completeness_{profile.user.id}'
    completeness = cache.get(cache_key)
    
    if completeness is not None:
        return completeness
    
    # Campos requeridos con pesos
    field_weights = {
        # Campos del usuario
        'first_name': 15,
        'last_name': 15,
        'email': 20,
        # Campos del perfil
        'state': 10,
        'country': 10,
        'bio': 10,
        'image_src': 10,
        'phone': 5,
        'birth_date': 5,
    }
    
    total_weight = sum(field_weights.values())
    completed_weight = 0
    
    # Verificar campos del usuario
    for field in ['first_name', 'last_name', 'email']:
        if getattr(profile.user, field, '').strip():
            completed_weight += field_weights[field]
    
    # Verificar campos del perfil
    for field in ['state', 'country', 'bio', 'phone', 'birth_date']:
        if getattr(profile, field, ''):
            if isinstance(getattr(profile, field), str):
                if getattr(profile, field).strip():
                    completed_weight += field_weights[field]
            else:
                completed_weight += field_weights[field]
    
    # Verificar imagen
    if profile.image_src:
        completed_weight += field_weights['image_src']
    
    completeness = int((completed_weight / total_weight) * 100)
    cache.set(cache_key, completeness, 3600)  # Cache por 1 hora
    
    return completeness

def paginate_queryset(queryset, page, items_per_page=10):
    """Función helper para paginación con manejo de errores mejorado"""
    paginator = Paginator(queryset, items_per_page)
    try:
        page_number = int(page)
        if page_number < 1:
            page_number = 1
        return paginator.page(page_number)
    except (PageNotAnInteger, ValueError):
        return paginator.page(1)
    except EmptyPage:
        if page_number > paginator.num_pages:
            raise Http404("Página no encontrada")
        return paginator.page(paginator.num_pages)

@user_passes_test(is_admin)
@handle_errors
def user_list_view(request):
    """Vista de lista de usuarios con filtros avanzados y caché"""
    try:
        # Obtener parámetros de filtro
        search_query = request.GET.get('search', '').strip()
        status_filter = request.GET.get('status', '')
        role_filter = request.GET.get('role', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        
        # Query base optimizada
        users = User.objects.select_related('userprofile').prefetch_related(
            Prefetch('business_set', queryset=Business.objects.filter(is_active=True))
        ).annotate(
            business_count=Count('business', filter=Q(business__is_active=True), distinct=True),
            product_count=Count('business__products', filter=Q(business__products__is_active=True), distinct=True)
        )
        
        # Aplicar filtros
        if search_query:
            users = users.filter(
                Q(username__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(userprofile__phone__icontains=search_query)
            ).distinct()
        
        if status_filter == 'active':
            users = users.filter(is_active=True)
        elif status_filter == 'inactive':
            users = users.filter(is_active=False)
        
        if role_filter == 'admin':
            users = users.filter(is_staff=True)
        elif role_filter == 'user':
            users = users.filter(is_staff=False)
        
        # Filtros de fecha
        if date_from:
            try:
                users = users.filter(date_joined__date__gte=date_from)
            except ValueError:
                messages.warning(request, "Fecha 'desde' inválida")
        
        if date_to:
            try:
                users = users.filter(date_joined__date__lte=date_to)
            except ValueError:
                messages.warning(request, "Fecha 'hasta' inválida")
        
        # Ordenar por fecha de registro descendente
        users = users.order_by('-date_joined')
        
        # Estadísticas con caché
        cache_key = 'admin_user_stats'
        user_stats = cache.get(cache_key)
        if not user_stats:
            user_stats = {
                'total_users': User.objects.count(),
                'active_users': User.objects.filter(is_active=True).count(),
                'inactive_users': User.objects.filter(is_active=False).count(),
                'admin_users': User.objects.filter(is_staff=True).count(),
                'new_users_today': User.objects.filter(
                    date_joined__date=timezone.now().date()
                ).count(),
            }
            cache.set(cache_key, user_stats, 300)  # Cache por 5 minutos
        
        # Paginación
        page = request.GET.get('page', 1)
        users_paginated = paginate_queryset(users, page, 25)
        
        context = {
            'users': users_paginated,
            'search_query': search_query,
            'status_filter': status_filter,
            'role_filter': role_filter,
            'date_from': date_from,
            'date_to': date_to,
            **user_stats
        }
        
        return render(request, 'user/user-list.html', context)
        
    except Exception as e:
        logger.exception(f"Critical error in user list view: {str(e)}")
        messages.error(request, "Error crítico al cargar la lista de usuarios.")
        return render(request, 'user/user-list.html', {'error': True, 'users': []})

@user_passes_test(is_admin)
@require_http_methods(["POST"])
@transaction.atomic
@handle_errors
def create_user_view(request):
    """Crear nuevo usuario con validación mejorada"""
    try:
        # Sanitizar datos
        form_data = sanitize_input({
            'username': request.POST.get('username', ''),
            'email': request.POST.get('email', ''),
            'first_name': request.POST.get('first_name', ''),
            'last_name': request.POST.get('last_name', ''),
            'password': request.POST.get('password', ''),
            'confirm_password': request.POST.get('confirm_password', ''),
            'is_staff': request.POST.get('is_staff', 'false') == 'true',
            'is_active': request.POST.get('is_active', 'true') == 'true',
        })
        
        # Validaciones mejoradas
        errors = validate_user_form(form_data)
        if errors:
            return JsonResponse({'success': False, 'errors': errors}, status=400)
        
        # Verificar permisos especiales para crear admins
        if form_data['is_staff'] and not request.user.is_superuser:
            return JsonResponse({
                'success': False,
                'errors': {'is_staff': ['Solo los superusuarios pueden crear administradores.']}
            }, status=403)
        
        # Crear usuario con manejo de errores
        try:
            user = User.objects.create_user(
                username=form_data['username'].lower(),
                email=form_data['email'].lower(),
                password=form_data['password'],
                first_name=form_data['first_name'].title(),
                last_name=form_data['last_name'].title(),
                is_staff=form_data['is_staff'],
                is_active=form_data['is_active']
            )
        except IntegrityError:
            return JsonResponse({
                'success': False,
                'errors': {'username': ['Este nombre de usuario ya existe.']}
            }, status=400)
        
        # Registrar actividad
        ActivityLog.log_activity(
            user=request.user,
            action="Usuario creado",
            details=f"Administrador {request.user.username} creó el usuario {user.username}",
            ip_address=get_client_ip(request),
            request=request,
            priority="high",
            category="admin"
        )
        
        # Invalidar caché de estadísticas
        cache.delete('admin_user_stats')
        
        messages.success(request, f'Usuario {user.username} creado correctamente.')
        return JsonResponse({
            'success': True, 
            'user_id': user.id,
            'message': f'Usuario {user.username} creado correctamente.'
        })
        
    except Exception as e:
        logger.exception(f"Error creating user: {str(e)}")
        return JsonResponse({
            'success': False, 
            'errors': {'general': ['Error interno del servidor al crear el usuario.']}
        }, status=500)

@user_passes_test(is_admin)
@require_http_methods(["POST"])
@transaction.atomic
@handle_errors
def update_user_view(request, user_id):
    """Actualizar usuario con validaciones mejoradas"""
    try:
        user = get_object_or_404(User, pk=user_id)
        
        # Verificar permisos especiales
        if user.is_superuser and not request.user.is_superuser:
            return JsonResponse({
                'success': False,
                'errors': {'general': ['No puedes modificar un superusuario.']}
            }, status=403)
        
        # Prevenir que un admin se degrade a sí mismo
        if user == request.user:
            if request.POST.get('is_staff') == 'false' or request.POST.get('is_active') == 'false':
                return JsonResponse({
                    'success': False,
                    'errors': {'general': ['No puedes modificar tus propios privilegios.']}
                }, status=400)
        
        # Sanitizar datos
        form_data = sanitize_input({
            'username': request.POST.get('username', ''),
            'email': request.POST.get('email', ''),
            'first_name': request.POST.get('first_name', ''),
            'last_name': request.POST.get('last_name', ''),
            'is_staff': request.POST.get('is_staff', 'false') == 'true',
            'is_active': request.POST.get('is_active', 'true') == 'true',
        })
        
        # Validaciones
        errors = validate_user_form(form_data, user=user, is_update=True)
        if errors:
            return JsonResponse({'success': False, 'errors': errors}, status=400)
        
        # Actualizar usuario
        old_username = user.username
        user.username = form_data['username'].lower()
        user.email = form_data['email'].lower()
        user.first_name = form_data['first_name'].title()
        user.last_name = form_data['last_name'].title()
        user.is_staff = form_data['is_staff']
        user.is_active = form_data['is_active']
        
        user.full_clean()
        user.save()
        
        # Invalidar caché
        cache.delete(f'profile_{user.id}')
        cache.delete('admin_user_stats')
        
        # Registrar actividad
        changes = []
        if old_username != user.username:
            changes.append(f"username: {old_username} → {user.username}")
        if form_data['is_staff'] != user.is_staff:
            changes.append(f"admin: {'Sí' if form_data['is_staff'] else 'No'}")
        
        ActivityLog.log_activity(
            user=request.user,
            action="Usuario actualizado",
            details=f"Admin {request.user.username} actualizó usuario {user.username}. Cambios: {', '.join(changes) if changes else 'Información básica'}",
            ip_address=get_client_ip(request),
            request=request,
            priority="medium",
            category="admin"
        )
        
        messages.success(request, f'Usuario {user.username} actualizado correctamente.')
        return JsonResponse({
            'success': True,
            'message': f'Usuario {user.username} actualizado correctamente.'
        })
        
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'errors': e.message_dict if hasattr(e, 'message_dict') else {'general': [str(e)]}
        }, status=400)
    except Exception as e:
        logger.exception(f"Error updating user {user_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'errors': {'general': ['Error interno del servidor al actualizar el usuario.']}
        }, status=500)

def validate_user_form(form_data, user=None, is_update=False):
    """Validar datos del formulario de usuario con reglas mejoradas"""
    errors = {}
    
    # Validar username
    if not form_data['username']:
        errors['username'] = ['El nombre de usuario es requerido.']
    else:
        username = form_data['username'].lower().strip()
        if len(username) < 3:
            errors['username'] = ['El nombre de usuario debe tener al menos 3 caracteres.']
        elif len(username) > 30:
            errors['username'] = ['El nombre de usuario no puede exceder 30 caracteres.']
        elif not username.replace('_', '').replace('-', '').isalnum():
            errors['username'] = ['El nombre de usuario solo puede contener letras, números, guiones y guiones bajos.']
        elif User.objects.filter(username=username).exclude(id=user.id if user else None).exists():
            errors['username'] = ['Este nombre de usuario ya está en uso.']
    
    # Validar email
    if not form_data['email']:
        errors['email'] = ['El correo electrónico es requerido.']
    else:
        email = form_data['email'].lower().strip()
        # Validación básica de email
        if '@' not in email or '.' not in email.split('@')[1]:
            errors['email'] = ['Ingrese un correo electrónico válido.']
        elif User.objects.filter(email=email).exclude(id=user.id if user else None).exists():
            errors['email'] = ['Este correo electrónico ya está en uso.']
    
    # Validar nombres
    if form_data['first_name'] and len(form_data['first_name']) > 30:
        errors['first_name'] = ['El nombre no puede exceder 30 caracteres.']
    
    if form_data['last_name'] and len(form_data['last_name']) > 30:
        errors['last_name'] = ['El apellido no puede exceder 30 caracteres.']
    
    # Validar contraseña (solo para creación)
    if not is_update:
        if not form_data.get('password'):
            errors['password'] = ['La contraseña es requerida.']
        else:
            password = form_data['password']
            if len(password) < 8:
                errors['password'] = ['La contraseña debe tener al menos 8 caracteres.']
            elif len(password) > 128:
                errors['password'] = ['La contraseña es demasiado larga.']
            elif password.isdigit():
                errors['password'] = ['La contraseña no puede ser solo números.']
            elif password.lower() == password:
                errors['password'] = ['La contraseña debe contener al menos una mayúscula.']
            elif form_data['password'] != form_data.get('confirm_password'):
                errors['confirm_password'] = ['Las contraseñas no coinciden.']
    
    return errors

@user_passes_test(is_admin)
@require_http_methods(["POST"])
@transaction.atomic
@handle_errors
def delete_user_view_as_admin(request, user_id):
    """Eliminar usuario con verificaciones de seguridad mejoradas"""
    try:
        user = get_object_or_404(User, pk=user_id)
        
        # Verificaciones de seguridad
        if user == request.user:
            return JsonResponse({
                'success': False,
                'error': 'No puedes eliminar tu propia cuenta.'
            }, status=400)
        
        if user.is_superuser and not request.user.is_superuser:
            return JsonResponse({
                'success': False,
                'error': 'No tienes permisos para eliminar un superusuario.'
            }, status=403)
        
        # Guardar información antes de eliminar
        username = user.username
        email = user.email
        user_id_str = str(user.id)
        
        # Verificar si tiene datos asociados importantes
        has_businesses = Business.objects.filter(fk_user=user).exists()
        if has_businesses:
            # Opción: transferir o archivar datos en lugar de eliminar
            return JsonResponse({
                'success': False,
                'error': 'Este usuario tiene empresas asociadas. Contacta al administrador del sistema.'
            }, status=400)
        
        # Eliminar usuario
        user.delete()
        
        # Invalidar caché
        cache.delete(f'profile_{user_id}')
        cache.delete('admin_user_stats')
        
        # Registrar actividad
        ActivityLog.objects.create(
            user=request.user,
            action="Usuario eliminado",
            details=f"Admin {request.user.username} eliminó usuario {username} (ID: {user_id_str}, Email: {email})",
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            priority="critical",
            category="admin"
        )
        
        messages.success(request, f"Usuario {username} eliminado correctamente.")
        return JsonResponse({
            'success': True,
            'message': f"Usuario {username} eliminado correctamente."
        })
        
    except Exception as e:
        logger.exception(f"Error deleting user {user_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor al eliminar el usuario.'
        }, status=500)

@user_passes_test(is_admin)
@require_http_methods(["POST"])
@transaction.atomic
@handle_errors
def bulk_delete_users_view(request):
    """Eliminar múltiples usuarios con verificaciones"""
    try:
        data = json.loads(request.body)
        user_ids = data.get('user_ids', [])
        
        if not user_ids:
            return JsonResponse({
                'success': False, 
                'error': 'No se seleccionaron usuarios.'
            }, status=400)
        
        # Convertir a enteros y validar
        try:
            user_ids = [int(uid) for uid in user_ids]
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'IDs de usuario inválidos.'
            }, status=400)
        
        # Prevenir eliminar al usuario actual
        if request.user.id in user_ids:
            return JsonResponse({
                'success': False,
                'error': 'No puedes eliminar tu propia cuenta.'
            }, status=400)
        
        # Obtener usuarios a eliminar
        users = User.objects.filter(id__in=user_ids)
        
        # Verificar superusuarios
        if not request.user.is_superuser:
            if users.filter(is_superuser=True).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'No tienes permisos para eliminar superusuarios.'
                }, status=403)
        
        # Verificar usuarios con datos críticos
        users_with_businesses = users.filter(business__isnull=False).distinct()
        if users_with_businesses.exists():
            return JsonResponse({
                'success': False,
                'error': f'{users_with_businesses.count()} usuarios tienen empresas asociadas. Revisa individualmente.',
                'users_with_data': list(users_with_businesses.values_list('username', flat=True))
            }, status=400)
        
        # Guardar información para el log
        count = users.count()
        usernames = list(users.values_list('username', flat=True))
        user_details = [f"{u.username} (ID: {u.id})" for u in users]
        
        # Eliminar usuarios
        users.delete()
        
        # Invalidar caché
        cache.delete('admin_user_stats')
        for uid in user_ids:
            cache.delete(f'profile_{uid}')
        
        # Registrar actividad
        ActivityLog.objects.create(
            user=request.user,
            action="Eliminación masiva de usuarios",
            details=f"Admin {request.user.username} eliminó {count} usuarios: {', '.join(user_details[:10])}{'...' if count > 10 else ''}",
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            priority="critical",
            category="admin"
        )
        
        messages.success(request, f"{count} usuarios eliminados correctamente.")
        return JsonResponse({
            'success': True, 
            'deleted_count': count,
            'message': f"{count} usuarios eliminados correctamente."
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos.'
        }, status=400)
    except Exception as e:
        logger.exception(f"Error in bulk delete: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor al eliminar usuarios.'
        }, status=500)

@user_passes_test(is_admin)
@require_http_methods(["POST"])
@transaction.atomic
@handle_errors
def toggle_user_status_view(request, user_id):
    """Cambiar estado activo/inactivo de usuario con verificaciones"""
    try:
        data = json.loads(request.body)
        active = data.get('active', True)
        
        user = get_object_or_404(User, pk=user_id)
        
        # Verificaciones de seguridad
        if user == request.user and not active:
            return JsonResponse({
                'success': False,
                'error': 'No puedes desactivar tu propia cuenta.'
            }, status=400)
        
        if user.is_superuser and not request.user.is_superuser:
            return JsonResponse({
                'success': False,
                'error': 'No tienes permisos para modificar un superusuario.'
            }, status=403)
        
        # Cambiar estado
        old_status = user.is_active
        user.is_active = active
        user.save()
        
        # Invalidar caché
        cache.delete(f'profile_{user.id}')
        cache.delete('admin_user_stats')
        
        # Si se desactiva, cerrar sesiones activas del usuario
        if not active:
            # Django no tiene una forma directa de cerrar sesiones de otros usuarios
            # pero puedes implementar tu propio sistema de tracking de sesiones
            pass
        
        # Registrar actividad
        action = "activado" if active else "desactivado"
        ActivityLog.log_activity(
            user=request.user,
            action=f"Usuario {action}",
            details=f"Admin {request.user.username} {action} usuario {user.username}",
            ip_address=get_client_ip(request),
            request=request,
            priority="high" if not active else "medium",
            category="admin"
        )
        
        messages.success(request, f"Usuario {user.username} {action} correctamente.")
        return JsonResponse({
            'success': True,
            'message': f"Usuario {user.username} {action} correctamente.",
            'new_status': 'active' if active else 'inactive'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos.'
        }, status=400)
    except Exception as e:
        logger.exception(f"Error toggling user status {user_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor al cambiar el estado del usuario.'
        }, status=500)

@login_required
@require_http_methods(["POST"])
@handle_errors
def change_password(request):
    """Cambiar contraseña con validaciones mejoradas"""
    try:
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Mantener la sesión activa después del cambio
            update_session_auth_hash(request, user)
            
            # Invalidar caché
            cache.delete(f'profile_{user.id}')
            
            # Registrar actividad
            ActivityLog.log_activity(
                user=user,
                action="Contraseña cambiada",
                details=f"Usuario {user.username} cambió su contraseña",
                ip_address=get_client_ip(request),
                request=request,
                priority="high",
                category="security"
            )
            
            messages.success(request, 'Tu contraseña fue cambiada correctamente.')
            return JsonResponse({
                'success': True,
                'message': 'Contraseña cambiada correctamente.'
            })
        else:
            # Formatear errores para mejor presentación
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]
            
            return JsonResponse({
                'success': False,
                'errors': errors
            }, status=400)
            
    except Exception as e:
        logger.exception(f"Error changing password for user {request.user.id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'errors': {'general': ['Error interno al cambiar la contraseña.']}
        }, status=500)

@login_required
@require_http_methods(["POST"])
@transaction.atomic
@handle_errors
def deactivate_account(request):
    """Desactivar cuenta con verificación de contraseña y feedback"""
    try:
        password = request.POST.get('password')
        reason = request.POST.get('reason', '')
        feedback = request.POST.get('feedback', '')
        
        if not password:
            messages.error(request, 'La contraseña es requerida para confirmar la desactivación.')
            return redirect('user:user.profile_settings')
        
        if not request.user.check_password(password):
            messages.error(request, 'Contraseña incorrecta. Por favor, intenta de nuevo.')
            return redirect('user:user.profile_settings')
        
        # Guardar feedback si se proporciona
        feedback_details = []
        if reason:
            feedback_details.append(f"Razón: {reason}")
        if feedback:
            feedback_details.append(f"Comentarios: {feedback[:500]}")
        
        # Registrar actividad antes de desactivar
        ActivityLog.objects.create(
            user=request.user,
            action="Cuenta desactivada por usuario",
            details=f"Usuario {request.user.username} desactivó su cuenta. {' '.join(feedback_details)}",
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            priority="critical",
            category="account"
        )
        
        # Desactivar cuenta
        request.user.is_active = False
        request.user.save()
        
        # Invalidar caché
        cache.delete(f'profile_{request.user.id}')
        cache.delete('admin_user_stats')
        
        # Cerrar sesión
        from django.contrib.auth import logout
        logout(request)
        
        messages.success(request, 'Tu cuenta ha sido desactivada. Esperamos verte pronto de nuevo.')
        return redirect('account_login')
        
    except Exception as e:
        logger.exception(f"Error deactivating account for user {request.user.id}: {str(e)}")
        messages.error(request, 'Error al desactivar la cuenta. Por favor, contacta al soporte.')
        return redirect('user:user.profile_settings')

@login_required
def cancel_deactivation(request):
    """Cancelar desactivación de cuenta"""
    messages.info(request, 'Desactivación de cuenta cancelada.')
    return redirect('user:user.profile_settings')

@login_required
@handle_errors
def user_api_detail(request, user_id):
    """API endpoint para obtener detalles de usuario con caché"""
    try:
        # Verificar permisos
        if request.user.id != user_id and not request.user.is_staff:
            return JsonResponse({'error': 'No autorizado'}, status=403)
        
        # Intentar obtener del caché
        cache_key = f'user_api_{user_id}'
        cached_data = cache.get(cache_key)
        if cached_data and not request.user.is_staff:  # Admin siempre obtiene datos frescos
            return JsonResponse(cached_data)
        
        user = get_object_or_404(User, pk=user_id)
        profile = getattr(user, 'userprofile', None)
        
        data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.get_full_name() or user.username,
            'is_staff': user.is_staff,
            'is_active': user.is_active,
            'is_superuser': user.is_superuser,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
        }
        
        if profile:
            data.update({
                'profile': {
                    'state': profile.state,
                    'country': profile.country,
                    'bio': profile.bio,
                    'phone': profile.phone,
                    'birth_date': profile.birth_date.isoformat() if profile.birth_date else None,
                    'website': profile.website,
                    'linkedin': profile.linkedin,
                    'github': profile.github,
                    'image_url': request.build_absolute_uri(profile.get_photo_url()),
                    'timezone': profile.timezone,
                    'language': profile.language,
                    'profile_complete': profile.is_profile_complete(),
                    'completion_percentage': profile.get_completion_percentage(),
                }
            })
        
        # Agregar estadísticas si es admin
        if request.user.is_staff:
            business_count = Business.objects.filter(fk_user=user, is_active=True).count()
            product_count = Product.objects.filter(fk_business__fk_user=user, is_active=True).count()
            
            data['stats'] = {
                'business_count': business_count,
                'product_count': product_count,
                'last_activity': ActivityLog.objects.filter(user=user).order_by('-timestamp').first().timestamp.isoformat() if ActivityLog.objects.filter(user=user).exists() else None,
            }
        
        # Cachear por 5 minutos
        cache.set(cache_key, data, 300)
        
        return JsonResponse(data)
        
    except Http404:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        logger.exception(f"Error in user API detail for user {user_id}: {str(e)}")
        return JsonResponse({'error': 'Error interno del servidor'}, status=500)

# Vistas basadas en clases mejoradas
class UserActivityLogView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Vista de logs de actividad con filtros avanzados y exportación"""
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
        category_filter = self.request.GET.get('category')
        priority_filter = self.request.GET.get('priority')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if user_filter:
            queryset = queryset.filter(
                Q(user__username__icontains=user_filter) |
                Q(user__email__icontains=user_filter)
            )
        
        if action_filter:
            queryset = queryset.filter(action__icontains=action_filter)
        
        if category_filter:
            queryset = queryset.filter(category=category_filter)
        
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
        
        if date_from:
            try:
                queryset = queryset.filter(timestamp__date__gte=date_from)
            except ValueError:
                pass
        
        if date_to:
            try:
                queryset = queryset.filter(timestamp__date__lte=date_to)
            except ValueError:
                pass
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas
        total_logs = self.get_queryset().count()
        today_logs = self.get_queryset().filter(timestamp__date=timezone.now().date()).count()
        
        # Categorías y prioridades únicas para filtros
        categories = ActivityLog.objects.values_list('category', flat=True).distinct()
        priorities = ActivityLog.PRIORITY_CHOICES
        
        context.update({
            'user_filter': self.request.GET.get('user', ''),
            'action_filter': self.request.GET.get('action', ''),
            'category_filter': self.request.GET.get('category', ''),
            'priority_filter': self.request.GET.get('priority', ''),
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
            'total_logs': total_logs,
            'today_logs': today_logs,
            'categories': [c for c in categories if c],
            'priorities': priorities,
        })
        return context

# Funciones auxiliares
def get_bolivian_states():
    """Obtener lista de departamentos de Bolivia"""
    return [
        ('La Paz', 'La Paz'),
        ('Santa Cruz', 'Santa Cruz'),
        ('Cochabamba', 'Cochabamba'),
        ('Oruro', 'Oruro'),
        ('Potosí', 'Potosí'),
        ('Tarija', 'Tarija'),
        ('Chuquisaca', 'Chuquisaca'),
        ('Beni', 'Beni'),
        ('Pando', 'Pando'),
    ]

def get_south_american_countries():
    """Obtener lista de países de Sudamérica"""
    return [
        ('Argentina', 'Argentina'),
        ('Bolivia', 'Bolivia'),
        ('Brasil', 'Brasil'),
        ('Chile', 'Chile'),
        ('Colombia', 'Colombia'),
        ('Ecuador', 'Ecuador'),
        ('Paraguay', 'Paraguay'),
        ('Perú', 'Perú'),
        ('Uruguay', 'Uruguay'),
        ('Venezuela', 'Venezuela'),
    ]

def custom_404(request, exception):
    """Vista personalizada para errores 404"""
    return render(request, '404.html', status=404)

def custom_500(request):
    """Vista personalizada para errores 500"""
    return render(request, '500.html', status=500)