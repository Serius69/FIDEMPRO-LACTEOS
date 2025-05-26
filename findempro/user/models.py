from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from social_django.models import UserSocialAuth
from PIL import Image
import os
from io import BytesIO
from django.core.files.base import ContentFile
import logging

logger = logging.getLogger(__name__)

class UserProfile(models.Model):
    """Modelo extendido del perfil de usuario"""
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        verbose_name="Usuario",
        help_text="Usuario asociado al perfil"
    )
    
    bio = models.TextField(
        max_length=500, 
        blank=True, 
        verbose_name="Biografía",
        help_text="Descripción personal del usuario (máximo 500 caracteres)"
    )
    
    image_src = models.ImageField(
        upload_to='images/user/%Y/%m/', 
        blank=True, 
        null=True,
        verbose_name="Imagen de perfil",
        help_text="Imagen de perfil del usuario",
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])]
    )
    
    state = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name="Estado/Departamento",
        help_text="Estado o departamento de residencia"
    )
    
    country = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name="País",
        help_text="País de residencia"
    )
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Teléfono",
        help_text="Número de teléfono de contacto"
    )
    
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de nacimiento",
        help_text="Fecha de nacimiento del usuario"
    )
    
    website = models.URLField(
        blank=True,
        verbose_name="Sitio web",
        help_text="Sitio web personal o profesional"
    )
    
    linkedin = models.URLField(
        blank=True,
        verbose_name="LinkedIn",
        help_text="Perfil de LinkedIn"
    )
    
    github = models.URLField(
        blank=True,
        verbose_name="GitHub",
        help_text="Perfil de GitHub"
    )
    
    timezone = models.CharField(
        max_length=50,
        default='America/La_Paz',
        verbose_name="Zona horaria",
        help_text="Zona horaria del usuario"
    )
    
    language = models.CharField(
        max_length=10,
        default='es',
        choices=[
            ('es', 'Español'),
            ('en', 'English'),
            ('pt', 'Português'),
        ],
        verbose_name="Idioma preferido",
        help_text="Idioma preferido para la interfaz"
    )
    
    notifications_email = models.BooleanField(
        default=True,
        verbose_name="Notificaciones por email",
        help_text="Recibir notificaciones por correo electrónico"
    )
    
    notifications_push = models.BooleanField(
        default=True,
        verbose_name="Notificaciones push",
        help_text="Recibir notificaciones push en el navegador"
    )
    
    privacy_profile = models.CharField(
        max_length=20,
        default='public',
        choices=[
            ('public', 'Público'),
            ('private', 'Privado'),
            ('contacts', 'Solo contactos'),
        ],
        verbose_name="Privacidad del perfil",
        help_text="Nivel de privacidad del perfil"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización"
    )
    
    class Meta:
        verbose_name = "Perfil de usuario"
        verbose_name_plural = "Perfiles de usuarios"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Perfil de {self.user.username}"
    
    def get_photo_url(self) -> str:
        """Obtener URL de la imagen de perfil"""
        if self.image_src and hasattr(self.image_src, 'url'):
            return self.image_src.url
        else:
            return "/static/images/users/user-dummy-img.webp"
    
    def get_full_name(self) -> str:
        """Obtener nombre completo del usuario"""
        if self.user.first_name and self.user.last_name:
            return f"{self.user.first_name} {self.user.last_name}"
        return self.user.username
    
    def get_display_name(self) -> str:
        """Obtener nombre para mostrar"""
        full_name = self.get_full_name()
        return full_name if full_name != self.user.username else f"@{self.user.username}"
    
    def is_profile_complete(self) -> bool:
        """Verificar si el perfil está completo"""
        required_user_fields = ['first_name', 'last_name', 'email']
        required_profile_fields = ['state', 'country', 'bio']
        
        # Verificar campos del usuario
        for field in required_user_fields:
            if not getattr(self.user, field, '').strip():
                return False
        
        # Verificar campos del perfil
        for field in required_profile_fields:
            if not getattr(self, field, '').strip():
                return False
        
        return True
    
    def get_completion_percentage(self) -> int:
        """Obtener porcentaje de completitud del perfil"""
        total_fields = 0
        completed_fields = 0
        
        # Campos obligatorios del usuario
        user_fields = {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'email': self.user.email,
        }
        
        # Campos obligatorios del perfil
        profile_fields = {
            'bio': self.bio,
            'state': self.state,
            'country': self.country,
        }
        
        # Campos opcionales que suman al porcentaje
        optional_fields = {
            'phone': self.phone,
            'birth_date': self.birth_date,
            'website': self.website,
            'image_src': self.image_src,
        }
        
        all_fields = {**user_fields, **profile_fields, **optional_fields}
        
        for field_name, field_value in all_fields.items():
            total_fields += 1
            if field_value:
                completed_fields += 1
        
        return int((completed_fields / total_fields) * 100) if total_fields > 0 else 0
    
    def save(self, *args, **kwargs):
        """Sobrescribir save para optimizar imágenes"""
        if self.image_src:
            self.image_src = self.optimize_image(self.image_src)
        super().save(*args, **kwargs)
    
    def optimize_image(self, image):
        """Optimizar imagen de perfil"""
        try:
            if not image:
                return image
            
            # Abrir imagen
            img = Image.open(image)
            
            # Convertir a RGB si es necesario
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # Redimensionar si es muy grande
            max_size = (400, 400)
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Guardar imagen optimizada
            output = BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)
            
            # Crear nuevo archivo
            return ContentFile(output.read(), name=image.name)
        
        except Exception as e:
            logger.error(f"Error optimizing image: {str(e)}")
            return image
    
    @property
    def age(self):
        """Calcular edad basada en fecha de nacimiento"""
        if self.birth_date:
            today = timezone.now().date()
            return today.year - self.birth_date.year - (
                (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
            )
        return None


class ActivityLog(models.Model):
    """Modelo para registrar actividades del usuario"""
    
    PRIORITY_CHOICES = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('critical', 'Crítica'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        verbose_name="Usuario",
        help_text="Usuario que realizó la acción"
    )
    
    action = models.CharField(
        max_length=255,
        verbose_name="Acción",
        help_text="Descripción de la acción realizada"
    )
    
    details = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Detalles",
        help_text="Detalles adicionales de la acción"
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Dirección IP",
        help_text="Dirección IP desde donde se realizó la acción"
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name="User Agent",
        help_text="Información del navegador/cliente"
    )
    
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name="Prioridad",
        help_text="Nivel de prioridad del evento"
    )
    
    category = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Categoría",
        help_text="Categoría de la actividad (auth, profile, admin, etc.)"
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha y hora"
    )
    
    class Meta:
        verbose_name = "Registro de actividad"
        verbose_name_plural = "Registros de actividades"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['priority', '-timestamp']),
            models.Index(fields=['category', '-timestamp']),
        ]
    
    def __str__(self):
        username = self.user.username if self.user else "Usuario anónimo"
        return f"{username} - {self.action} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"
    
    @classmethod
    def log_activity(cls, user, action, details=None, ip_address=None, user_agent=None, priority='medium', category=''):
        """Método helper para registrar actividades"""
        try:
            return cls.objects.create(
                user=user,
                action=action,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                priority=priority,
                category=category
            )
        except Exception as e:
            logger.error(f"Error logging activity: {str(e)}")
            return None


class UserSession(models.Model):
    """Modelo para rastrear sesiones de usuario"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Usuario"
    )
    
    session_key = models.CharField(
        max_length=40,
        unique=True,
        verbose_name="Clave de sesión"
    )
    
    ip_address = models.GenericIPAddressField(
        verbose_name="Dirección IP"
    )
    
    user_agent = models.TextField(
        verbose_name="User Agent"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Inicio de sesión"
    )
    
    last_activity = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actividad"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Sesión activa"
    )
    
    class Meta:
        verbose_name = "Sesión de usuario"
        verbose_name_plural = "Sesiones de usuarios"
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"{self.user.username} - {self.ip_address} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"


class UserPreferences(models.Model):
    """Modelo para preferencias del usuario"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name="Usuario"
    )
    
    theme = models.CharField(
        max_length=20,
        default='light',
        choices=[
            ('light', 'Claro'),
            ('dark', 'Oscuro'),
            ('auto', 'Automático'),
        ],
        verbose_name="Tema"
    )
    
    items_per_page = models.PositiveIntegerField(
        default=10,
        verbose_name="Elementos por página"
    )
    
    dashboard_layout = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Diseño del dashboard"
    )
    
    quick_actions = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Acciones rápidas"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización"
    )
    
    class Meta:
        verbose_name = "Preferencias de usuario"
        verbose_name_plural = "Preferencias de usuarios"
    
    def __str__(self):
        return f"Preferencias de {self.user.username}"


# Signals
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Crear perfil automáticamente cuando se crea un usuario"""
    if created:
        try:
            UserProfile.objects.create(user=instance)
            UserPreferences.objects.create(user=instance)
            
            # Registrar actividad
            ActivityLog.log_activity(
                user=instance,
                action="Perfil creado",
                details=f"Perfil automático creado para {instance.username}",
                category="profile"
            )
        except Exception as e:
            logger.error(f"Error creating user profile for {instance.username}: {str(e)}")


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Guardar perfil cuando se guarda el usuario"""
    try:
        if hasattr(instance, 'userprofile'):
            instance.userprofile.save()
        if hasattr(instance, 'userpreferences'):
            instance.userpreferences.save()
    except Exception as e:
        logger.error(f"Error saving user profile for {instance.username}: {str(e)}")


@receiver(post_save, sender=UserSocialAuth)
def save_social_image(sender, instance, **kwargs):
    """Guardar imagen de perfil desde redes sociales"""
    try:
        if instance.provider == 'google-oauth2':
            user_profile, created = UserProfile.objects.get_or_create(user=instance.user)
            
            # Solo actualizar si no tiene imagen o es nueva
            picture_url = instance.extra_data.get('picture', '')
            if picture_url and not user_profile.image_src:
                # Aquí podrías descargar y guardar la imagen
                # Por ahora solo registramos la URL
                ActivityLog.log_activity(
                    user=instance.user,
                    action="Imagen de perfil de Google obtenida",
                    details=f"URL de imagen: {picture_url}",
                    category="social"
                )
        
        elif instance.provider == 'facebook':
            user_profile, created = UserProfile.objects.get_or_create(user=instance.user)
            picture_data = instance.extra_data.get('picture', {})
            if picture_data and not user_profile.image_src:
                picture_url = picture_data.get('data', {}).get('url', '')
                if picture_url:
                    ActivityLog.log_activity(
                        user=instance.user,
                        action="Imagen de perfil de Facebook obtenida",
                        details=f"URL de imagen: {picture_url}",
                        category="social"
                    )
    except Exception as e:
        logger.error(f"Error saving social image for user {instance.user.username}: {str(e)}")


@receiver(pre_delete, sender=User)
def log_user_deletion(sender, instance, **kwargs):
    """Registrar eliminación de usuario"""
    try:
        ActivityLog.log_activity(
            user=None,  # Usuario será eliminado
            action="Usuario eliminado",
            details=f"Usuario {instance.username} ({instance.email}) fue eliminado del sistema",
            priority="high",
            category="admin"
        )
    except Exception as e:
        logger.error(f"Error logging user deletion for {instance.username}: {str(e)}")


@receiver(post_save, sender=ActivityLog)
def clean_old_activity_logs(sender, instance, created, **kwargs):
    """Limpiar logs antiguos automáticamente"""
    if created:
        try:
            # Mantener solo los últimos 10000 registros
            total_logs = ActivityLog.objects.count()
            if total_logs > 10000:
                old_logs = ActivityLog.objects.order_by('timestamp')[:(total_logs - 10000)]
                old_log_ids = list(old_logs.values_list('id', flat=True))
                ActivityLog.objects.filter(id__in=old_log_ids).delete()
        except Exception as e:
            logger.error(f"Error cleaning old activity logs: {str(e)}")