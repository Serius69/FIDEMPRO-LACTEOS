"""
Formularios mejorados para el sistema de usuarios
Incluye validaciones avanzadas, widgets personalizados y mejor UX
"""

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import validate_email
from django.contrib.auth import authenticate, password_validation
from .models import UserProfile, UserPreferences
import re
from datetime import date, timedelta


class UserForm(UserCreationForm):
    """Formulario mejorado para crear/editar usuarios"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu correo electrónico',
            'autocomplete': 'email'
        }),
        help_text="Ingresa un correo electrónico válido"
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu nombre',
            'autocomplete': 'given-name'
        }),
        help_text="Tu nombre"
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu apellido',
            'autocomplete': 'family-name'
        }),
        help_text="Tu apellido"
    )
    
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu nombre de usuario',
            'autocomplete': 'username'
        }),
        help_text="Letras, dígitos y @/./+/-/_ únicamente. Máximo 150 caracteres."
    )
    
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa una contraseña segura',
            'autocomplete': 'new-password'
        }),
        help_text="La contraseña debe tener al menos 8 caracteres."
    )
    
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirma tu contraseña',
            'autocomplete': 'new-password'
        }),
        help_text="Ingresa la misma contraseña para verificación."
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personalizar ayuda para username
        self.fields['username'].help_text = (
            "Requerido. 150 caracteres o menos. "
            "Solo letras, dígitos y @/./+/-/_ "
        )
        
        # Agregar clases CSS a todos los campos
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
    
    def clean_email(self):
        """Validar que el email sea único"""
        email = self.cleaned_data.get('email')
        if email:
            # Normalizar email
            email = email.lower().strip()
            
            # Verificar si ya existe (excluyendo la instancia actual si es actualización)
            qs = User.objects.filter(email=email)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError("Ya existe un usuario con este correo electrónico.")
        
        return email
    
    def clean_username(self):
        """Validar username con reglas personalizadas"""
        username = self.cleaned_data.get('username')
        
        if username:
            # Normalizar username
            username = username.lower().strip()
            
            # Validar longitud mínima
            if len(username) < 3:
                raise ValidationError("El nombre de usuario debe tener al menos 3 caracteres.")
            
            # Validar caracteres permitidos
            if not re.match(r'^[a-zA-Z0-9@.+_-]+$', username):
                raise ValidationError(
                    "El nombre de usuario solo puede contener letras, números y @/./+/-/_"
                )
            
            # Validar que no sea solo números
            if username.isdigit():
                raise ValidationError("El nombre de usuario no puede ser solo números.")
            
            # Verificar unicidad
            qs = User.objects.filter(username=username)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError("Ya existe un usuario con este nombre.")
        
        return username
    
    def clean_first_name(self):
        """Validar nombre"""
        first_name = self.cleaned_data.get('first_name')
        if first_name:
            first_name = first_name.strip().title()
            if len(first_name) < 2:
                raise ValidationError("El nombre debe tener al menos 2 caracteres.")
            if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', first_name):
                raise ValidationError("El nombre solo puede contener letras.")
        return first_name
    
    def clean_last_name(self):
        """Validar apellido"""
        last_name = self.cleaned_data.get('last_name')
        if last_name:
            last_name = last_name.strip().title()
            if len(last_name) < 2:
                raise ValidationError("El apellido debe tener al menos 2 caracteres.")
            if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', last_name):
                raise ValidationError("El apellido solo puede contener letras.")
        return last_name
    
    def save(self, commit=True):
        """Guardar usuario con datos normalizados"""
        user = super().save(commit=False)
        user.email = user.email.lower()
        user.username = user.username.lower()
        
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    """Formulario para el perfil extendido del usuario"""
    
    birth_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'max': date.today().isoformat()
        }),
        help_text="Tu fecha de nacimiento"
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+591 70123456',
            'autocomplete': 'tel'
        }),
        help_text="Número de teléfono con código de país"
    )
    
    bio = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Cuéntanos sobre ti...',
            'maxlength': 500
        }),
        help_text="Descripción personal (máximo 500 caracteres)"
    )
    
    website = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://tu-sitio-web.com'
        }),
        help_text="Tu sitio web personal o profesional"
    )
    
    linkedin = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://linkedin.com/in/tu-perfil'
        }),
        help_text="Tu perfil de LinkedIn"
    )
    
    github = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://github.com/tu-usuario'
        }),
        help_text="Tu perfil de GitHub"
    )
    
    image_src = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        help_text="Imagen de perfil (máximo 5MB, formatos: JPG, PNG, WebP)"
    )
    
    class Meta:
        model = UserProfile
        fields = [
            'bio', 'state', 'country', 'phone', 'birth_date',
            'website', 'linkedin', 'github', 'image_src',
            'timezone', 'language', 'notifications_email',
            'notifications_push', 'privacy_profile'
        ]
        widgets = {
            'state': forms.Select(attrs={'class': 'form-control'}),
            'country': forms.Select(attrs={'class': 'form-control'}),
            'timezone': forms.Select(attrs={'class': 'form-control'}),
            'language': forms.Select(attrs={'class': 'form-control'}),
            'privacy_profile': forms.Select(attrs={'class': 'form-control'}),
            'notifications_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notifications_push': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_birth_date(self):
        """Validar fecha de nacimiento"""
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date:
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            
            if age < 13:
                raise ValidationError("Debes tener al menos 13 años para usar este servicio.")
            if age > 120:
                raise ValidationError("Fecha de nacimiento no válida.")
            if birth_date > today:
                raise ValidationError("La fecha de nacimiento no puede ser en el futuro.")
        
        return birth_date
    
    def clean_phone(self):
        """Validar número de teléfono"""
        phone = self.cleaned_data.get('phone')
        if phone:
            # Limpiar espacios y caracteres especiales
            phone = re.sub(r'[^\d+]', '', phone)
            
            # Validar formato básico
            if not re.match(r'^\+?[1-9]\d{7,14}$', phone):
                raise ValidationError(
                    "Ingresa un número de teléfono válido con código de país. "
                    "Ejemplo: +591 70123456"
                )
        
        return phone
    
    def clean_website(self):
        """Validar URL del sitio web"""
        website = self.cleaned_data.get('website')
        if website:
            if not website.startswith(('http://', 'https://')):
                website = 'https://' + website
        return website
    
    def clean_linkedin(self):
        """Validar URL de LinkedIn"""
        linkedin = self.cleaned_data.get('linkedin')
        if linkedin:
            if not linkedin.startswith(('http://', 'https://')):
                linkedin = 'https://' + linkedin
            if 'linkedin.com' not in linkedin:
                raise ValidationError("Debe ser una URL válida de LinkedIn.")
        return linkedin
    
    def clean_github(self):
        """Validar URL de GitHub"""
        github = self.cleaned_data.get('github')
        if github:
            if not github.startswith(('http://', 'https://')):
                github = 'https://' + github
            if 'github.com' not in github:
                raise ValidationError("Debe ser una URL válida de GitHub.")
        return github
    
    def clean_image_src(self):
        """Validar imagen de perfil"""
        image = self.cleaned_data.get('image_src')
        if image:
            # Validar tamaño (5MB máximo)
            if image.size > 5 * 1024 * 1024:
                raise ValidationError("La imagen no debe superar los 5MB.")
            
            # Validar tipo de archivo
            valid_extensions = ['jpg', 'jpeg', 'png', 'webp']
            extension = image.name.split('.')[-1].lower()
            if extension not in valid_extensions:
                raise ValidationError(
                    f"Formato no válido. Usa: {', '.join(valid_extensions).upper()}"
                )
        
        return image


class UserPreferencesForm(forms.ModelForm):
    """Formulario para preferencias del usuario"""
    
    class Meta:
        model = UserPreferences
        fields = ['theme', 'items_per_page', 'quick_actions']
        widgets = {
            'theme': forms.Select(attrs={'class': 'form-control'}),
            'items_per_page': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 5,
                'max': 100
            }),
            'quick_actions': forms.HiddenInput(),
        }
    
    def clean_items_per_page(self):
        """Validar items por página"""
        items_per_page = self.cleaned_data.get('items_per_page')
        if items_per_page:
            if items_per_page < 5 or items_per_page > 100:
                raise ValidationError("Debe estar entre 5 y 100 elementos por página.")
        return items_per_page


class CustomPasswordChangeForm(PasswordChangeForm):
    """Formulario personalizado para cambio de contraseña"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personalizar widgets
        self.fields['old_password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Contraseña actual',
            'autocomplete': 'current-password'
        })
        
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nueva contraseña',
            'autocomplete': 'new-password'
        })
        
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmar nueva contraseña',
            'autocomplete': 'new-password'
        })
    
    def clean_new_password2(self):
        """Validar que las contraseñas coincidan y cumplan con los requisitos"""
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        
        if password1 and password2:
            if password1 != password2:
                raise ValidationError("Las contraseñas no coinciden.")
            
            # Validar complejidad
            password_validation.validate_password(password2, self.user)
        
        return password2


class BulkUserActionForm(forms.Form):
    """Formulario para acciones masivas en usuarios"""
    
    ACTION_CHOICES = [
        ('activate', 'Activar usuarios'),
        ('deactivate', 'Desactivar usuarios'),
        ('delete', 'Eliminar usuarios'),
        ('export', 'Exportar datos'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    user_ids = forms.CharField(
        widget=forms.HiddenInput()
    )
    
    confirm = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Confirmo que quiero realizar esta acción"
    )
    
    def clean_user_ids(self):
        """Validar IDs de usuarios"""
        user_ids = self.cleaned_data.get('user_ids')
        if user_ids:
            try:
                ids = [int(id.strip()) for id in user_ids.split(',') if id.strip()]
                if not ids:
                    raise ValidationError("Debe seleccionar al menos un usuario.")
                return ids
            except ValueError:
                raise ValidationError("IDs de usuarios no válidos.")
        raise ValidationError("Debe seleccionar usuarios.")


class UserSearchForm(forms.Form):
    """Formulario para búsqueda y filtrado de usuarios"""
    
    search = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, email o username...'
        })
    )
    
    status = forms.ChoiceField(
        choices=[
            ('', 'Todos los estados'),
            ('active', 'Activos'),
            ('inactive', 'Inactivos'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    role = forms.ChoiceField(
        choices=[
            ('', 'Todos los roles'),
            ('admin', 'Administradores'),
            ('user', 'Usuarios'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_joined_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_joined_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    def clean(self):
        """Validar fechas"""
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_joined_from')
        date_to = cleaned_data.get('date_joined_to')
        
        if date_from and date_to:
            if date_from > date_to:
                raise ValidationError("La fecha 'desde' no puede ser mayor que la fecha 'hasta'.")
        
        return cleaned_data


class AccountDeactivationForm(forms.Form):
    """Formulario para desactivación de cuenta"""
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu contraseña actual'
        }),
        label="Contraseña actual",
        help_text="Confirma tu identidad ingresando tu contraseña actual"
    )
    
    reason = forms.ChoiceField(
        choices=[
            ('not_using', 'No uso más el servicio'),
            ('privacy', 'Preocupaciones de privacidad'),
            ('alternative', 'Encontré una alternativa'),
            ('temporary', 'Descanso temporal'),
            ('other', 'Otro motivo'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Motivo (opcional)"
    )
    
    feedback = forms.CharField(
        max_length=1000,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Comparte tus comentarios para ayudarnos a mejorar...'
        }),
        label="Comentarios adicionales (opcional)"
    )
    
    confirm = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Entiendo que mi cuenta será desactivada y mis datos serán preservados"
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_password(self):
        """Validar contraseña actual"""
        password = self.cleaned_data.get('password')
        if password:
            if not self.user.check_password(password):
                raise ValidationError("Contraseña incorrecta.")
        return password