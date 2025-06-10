"""
Formularios mejorados para el sistema de usuarios
Incluye validaciones avanzadas, widgets personalizados y mejor UX
"""

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import validate_email, RegexValidator
from django.contrib.auth import authenticate, password_validation
from django.utils.safestring import mark_safe
from django.utils.html import escape
from .models import UserProfile, UserPreferences
import re
from datetime import date, timedelta
import unicodedata


class CustomErrorList(forms.utils.ErrorList):
    """Lista de errores personalizada con mejor formato"""
    def as_ul(self):
        if not self:
            return ''
        return mark_safe(
            '<ul class="errorlist list-unstyled mb-0">%s</ul>' % ''.join(
                ['<li class="text-danger small"><i class="ri-error-warning-line me-1"></i>%s</li>' % escape(e) for e in self]
            )
        )


class UserForm(UserCreationForm):
    """Formulario mejorado para crear/editar usuarios con validaciones avanzadas"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'ejemplo@correo.com',
            'autocomplete': 'email',
            'data-bs-toggle': 'tooltip',
            'data-bs-placement': 'right',
            'title': 'Ingresa un correo electrónico válido que usarás para acceder'
        }),
        help_text="Usaremos este correo para notificaciones importantes",
        error_messages={
            'required': 'El correo electrónico es obligatorio.',
            'invalid': 'Por favor, ingresa un correo electrónico válido.'
        }
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Juan',
            'autocomplete': 'given-name',
            'pattern': '[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+',
            'data-bs-toggle': 'tooltip',
            'title': 'Solo letras y espacios permitidos'
        }),
        help_text="Tu nombre real",
        validators=[
            RegexValidator(
                regex=r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$',
                message='El nombre solo puede contener letras y espacios.'
            )
        ]
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Pérez',
            'autocomplete': 'family-name',
            'pattern': '[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+',
            'data-bs-toggle': 'tooltip',
            'title': 'Solo letras y espacios permitidos'
        }),
        help_text="Tu apellido",
        validators=[
            RegexValidator(
                regex=r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$',
                message='El apellido solo puede contener letras y espacios.'
            )
        ]
    )
    
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'usuario123',
            'autocomplete': 'username',
            'data-bs-toggle': 'tooltip',
            'title': 'Será tu identificador único en el sistema'
        }),
        help_text="Solo letras, números y @/./+/-/_ (3-150 caracteres)",
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message='El nombre de usuario solo puede contener letras, números y @/./+/-/_'
            )
        ]
    )
    
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••',
            'autocomplete': 'new-password',
            'data-password-strength': 'true'
        }),
        help_text=password_validation.password_validators_help_text_html()
    )
    
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••',
            'autocomplete': 'new-password'
        }),
        help_text="Ingresa la misma contraseña para verificación."
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        error_classes = {
            'default': CustomErrorList,
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personalizar mensajes de error
        self.fields['username'].error_messages.update({
            'unique': 'Este nombre de usuario ya está registrado. Prueba con otro.',
            'required': 'El nombre de usuario es obligatorio.',
            'max_length': 'El nombre de usuario no puede superar los 150 caracteres.',
        })
        
        # Agregar clases CSS y atributos adicionales
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
            
            # Agregar indicador de campo requerido
            if field.required:
                field.label = mark_safe(f'{field.label} <span class="text-danger">*</span>')
    
    def clean_email(self):
        """Validar que el email sea único y válido"""
        email = self.cleaned_data.get('email')
        if email:
            # Normalizar email
            email = email.lower().strip()
            
            # Validar formato
            try:
                validate_email(email)
            except ValidationError:
                raise ValidationError("Por favor, ingresa un correo electrónico válido.")
            
            # Validar dominio común
            common_typos = {
                'gmial.com': 'gmail.com',
                'gmai.com': 'gmail.com',
                'yahooo.com': 'yahoo.com',
                'hotmial.com': 'hotmail.com',
            }
            
            domain = email.split('@')[1]
            if domain in common_typos:
                raise ValidationError(
                    f"¿Quisiste decir {email.replace(domain, common_typos[domain])}?"
                )
            
            # Verificar unicidad
            qs = User.objects.filter(email__iexact=email)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError(
                    "Ya existe una cuenta con este correo electrónico. "
                    "¿Olvidaste tu contraseña?"
                )
        
        return email
    
    def clean_username(self):
        """Validar username con reglas personalizadas mejoradas"""
        username = self.cleaned_data.get('username')
        
        if username:
            # Normalizar username
            username = username.lower().strip()
            
            # Validar longitud
            if len(username) < 3:
                raise ValidationError("El nombre de usuario debe tener al menos 3 caracteres.")
            
            # Validar que no sea solo números
            if username.isdigit():
                raise ValidationError("El nombre de usuario no puede ser solo números.")
            
            # Validar que no contenga palabras prohibidas
            forbidden_words = ['admin', 'administrator', 'root', 'system', 'user']
            if any(word in username.lower() for word in forbidden_words):
                raise ValidationError(
                    "Este nombre de usuario no está permitido por razones de seguridad."
                )
            
            # Validar caracteres especiales al inicio o final
            if username.startswith(('.', '_')) or username.endswith(('.', '_')):
                raise ValidationError(
                    "El nombre de usuario no puede empezar o terminar con . o _"
                )
            
            # Verificar duplicados con case-insensitive
            qs = User.objects.filter(username__iexact=username)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError("Este nombre de usuario ya está en uso.")
        
        return username
    
    def clean_first_name(self):
        """Validar y normalizar nombre"""
        first_name = self.cleaned_data.get('first_name')
        if first_name:
            # Normalizar
            first_name = ' '.join(first_name.split())  # Eliminar espacios múltiples
            first_name = first_name.strip().title()
            
            # Validar longitud mínima
            if len(first_name) < 2:
                raise ValidationError("El nombre debe tener al menos 2 caracteres.")
            
            # Validar caracteres
            normalized = unicodedata.normalize('NFKD', first_name)
            if not all(c.isalpha() or c.isspace() for c in normalized):
                raise ValidationError("El nombre solo puede contener letras y espacios.")
        
        return first_name
    
    def clean_last_name(self):
        """Validar y normalizar apellido"""
        last_name = self.cleaned_data.get('last_name')
        if last_name:
            # Normalizar
            last_name = ' '.join(last_name.split())
            last_name = last_name.strip().title()
            
            # Validar longitud mínima
            if len(last_name) < 2:
                raise ValidationError("El apellido debe tener al menos 2 caracteres.")
            
            # Validar caracteres
            normalized = unicodedata.normalize('NFKD', last_name)
            if not all(c.isalpha() or c.isspace() for c in normalized):
                raise ValidationError("El apellido solo puede contener letras y espacios.")
        
        return last_name
    
    def clean_password1(self):
        """Validar fortaleza de contraseña con reglas personalizadas"""
        password1 = self.cleaned_data.get('password1')
        
        if password1:
            # Validar longitud
            if len(password1) < 8:
                raise ValidationError("La contraseña debe tener al menos 8 caracteres.")
            
            # Validar complejidad
            has_upper = any(c.isupper() for c in password1)
            has_lower = any(c.islower() for c in password1)
            has_digit = any(c.isdigit() for c in password1)
            has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password1))
            
            complexity_score = sum([has_upper, has_lower, has_digit, has_special])
            
            if complexity_score < 3:
                suggestions = []
                if not has_upper:
                    suggestions.append("una letra mayúscula")
                if not has_lower:
                    suggestions.append("una letra minúscula")
                if not has_digit:
                    suggestions.append("un número")
                if not has_special:
                    suggestions.append("un carácter especial (!@#$%^&*)")
                
                raise ValidationError(
                    f"La contraseña debe incluir al menos: {', '.join(suggestions)}"
                )
            
            # Validar contraseñas comunes
            common_passwords = [
                'password', 'contraseña', '12345678', 'qwerty', 'abc123',
                'password123', 'admin', 'letmein', 'welcome', '123456789'
            ]
            
            if password1.lower() in common_passwords:
                raise ValidationError(
                    "Esta contraseña es muy común. Por favor, elige una más segura."
                )
        
        return password1
    
    def clean(self):
        """Validaciones adicionales del formulario completo"""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        username = cleaned_data.get('username')
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        
        # Validar que las contraseñas coincidan
        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Las contraseñas no coinciden.")
        
        # Validar que la contraseña no contenga el username
        if password1 and username:
            if username.lower() in password1.lower():
                self.add_error(
                    'password1',
                    "La contraseña no puede contener tu nombre de usuario."
                )
        
        # Validar que la contraseña no contenga el nombre
        if password1 and (first_name or last_name):
            name_parts = []
            if first_name:
                name_parts.extend(first_name.lower().split())
            if last_name:
                name_parts.extend(last_name.lower().split())
            
            for part in name_parts:
                if len(part) > 3 and part in password1.lower():
                    self.add_error(
                        'password1',
                        "La contraseña no puede contener tu nombre o apellido."
                    )
                    break
        
        return cleaned_data
    
    def save(self, commit=True):
        """Guardar usuario con datos normalizados"""
        user = super().save(commit=False)
        user.email = user.email.lower()
        user.username = user.username.lower()
        
        if commit:
            user.save()
            # Aquí podrías enviar email de bienvenida
        return user


class UserProfileForm(forms.ModelForm):
    """Formulario para el perfil extendido del usuario con validaciones mejoradas"""
    
    birth_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'max': date.today().isoformat()
        }),
        help_text="Tu fecha de nacimiento (debes tener al menos 13 años)"
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+591 70123456',
            'autocomplete': 'tel',
            'data-bs-toggle': 'tooltip',
            'title': 'Incluye el código de país'
        }),
        help_text="Número de teléfono con código de país",
        validators=[
            RegexValidator(
                regex=r'^\+?[1-9]\d{7,14}$',
                message='Ingresa un número válido con código de país (ej: +591 70123456)'
            )
        ]
    )
    
    bio = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Cuéntanos sobre ti...',
            'maxlength': 500,
            'data-character-counter': 'true'
        }),
        help_text="Breve descripción sobre ti (máximo 500 caracteres)"
    )
    
    website = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://tu-sitio-web.com',
            'data-bs-toggle': 'tooltip',
            'title': 'Debe incluir https:// o http://'
        }),
        help_text="Tu sitio web personal o profesional"
    )
    
    linkedin = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://linkedin.com/in/tu-perfil',
            'pattern': 'https?://([a-z]{2,3}\.)?linkedin\.com/.*'
        }),
        help_text="URL de tu perfil de LinkedIn"
    )
    
    github = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://github.com/tu-usuario',
            'pattern': 'https?://github\.com/.*'
        }),
        help_text="URL de tu perfil de GitHub"
    )
    
    image_src = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/jpeg,image/jpg,image/png,image/webp',
            'data-max-size': '5242880'  # 5MB en bytes
        }),
        help_text="Imagen de perfil (JPG, PNG o WebP, máximo 5MB)"
    )
    
    state = forms.ChoiceField(
        required=False,
        choices=[('', 'Selecciona tu departamento')] + [
            ('La Paz', 'La Paz'),
            ('Santa Cruz', 'Santa Cruz'),
            ('Cochabamba', 'Cochabamba'),
            ('Oruro', 'Oruro'),
            ('Potosí', 'Potosí'),
            ('Tarija', 'Tarija'),
            ('Chuquisaca', 'Chuquisaca'),
            ('Beni', 'Beni'),
            ('Pando', 'Pando'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    country = forms.ChoiceField(
        required=False,
        choices=[('', 'Selecciona tu país')] + [
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
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
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
            'timezone': forms.Select(attrs={
                'class': 'form-select',
                'data-bs-toggle': 'tooltip',
                'title': 'Zona horaria para mostrar fechas correctamente'
            }),
            'language': forms.Select(attrs={
                'class': 'form-select'
            }),
            'privacy_profile': forms.Select(attrs={
                'class': 'form-select',
                'data-bs-toggle': 'tooltip',
                'title': 'Controla quién puede ver tu perfil'
            }),
            'notifications_email': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'role': 'switch'
            }),
            'notifications_push': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'role': 'switch'
            }),
        }
    
    def clean_birth_date(self):
        """Validar fecha de nacimiento con restricciones de edad"""
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date:
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            
            if age < 13:
                raise ValidationError(
                    "Debes tener al menos 13 años para usar este servicio.",
                    code='underage'
                )
            if age > 120:
                raise ValidationError(
                    "Por favor, ingresa una fecha de nacimiento válida.",
                    code='invalid_age'
                )
            if birth_date > today:
                raise ValidationError(
                    "La fecha de nacimiento no puede ser en el futuro.",
                    code='future_date'
                )
        
        return birth_date
    
    def clean_phone(self):
        """Validar y formatear número de teléfono"""
        phone = self.cleaned_data.get('phone')
        if phone:
            # Limpiar caracteres no numéricos excepto +
            phone = re.sub(r'[^\d+]', '', phone)
            
            # Asegurar que tenga formato internacional
            if not phone.startswith('+'):
                # Asumir Bolivia si no tiene código de país
                if len(phone) == 8 and phone[0] in '67':
                    phone = '+591' + phone
                else:
                    raise ValidationError(
                        "Por favor incluye el código de país (ej: +591 para Bolivia)"
                    )
            
            # Validar longitud total
            if len(phone) < 10 or len(phone) > 15:
                raise ValidationError(
                    "Número de teléfono inválido. Verifica el formato."
                )
        
        return phone
    
    def clean_website(self):
        """Validar y normalizar URL del sitio web"""
        website = self.cleaned_data.get('website')
        if website:
            # Agregar protocolo si no lo tiene
            if not website.startswith(('http://', 'https://')):
                website = 'https://' + website
            
            # Validar que sea una URL válida
            url_pattern = re.compile(
                r'^https?://'  # http:// o https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # dominio
                r'localhost|'  # localhost
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
                r'(?::\d+)?'  # puerto opcional
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            
            if not url_pattern.match(website):
                raise ValidationError("Por favor, ingresa una URL válida.")
        
        return website
    
    def clean_linkedin(self):
        """Validar URL de LinkedIn"""
        linkedin = self.cleaned_data.get('linkedin')
        if linkedin:
            if not linkedin.startswith(('http://', 'https://')):
                linkedin = 'https://' + linkedin
            
            # Validar formato de LinkedIn
            linkedin_pattern = re.compile(
                r'^https?://([a-z]{2,3}\.)?linkedin\.com/(in|company|school)/[\w\-]+/?$',
                re.IGNORECASE
            )
            
            if not linkedin_pattern.match(linkedin):
                raise ValidationError(
                    "Por favor, ingresa una URL válida de LinkedIn "
                    "(ej: https://linkedin.com/in/tu-perfil)"
                )
        
        return linkedin
    
    def clean_github(self):
        """Validar URL de GitHub"""
        github = self.cleaned_data.get('github')
        if github:
            if not github.startswith(('http://', 'https://')):
                github = 'https://' + github
            
            # Validar formato de GitHub
            github_pattern = re.compile(
                r'^https?://github\.com/[\w\-]+/?$',
                re.IGNORECASE
            )
            
            if not github_pattern.match(github):
                raise ValidationError(
                    "Por favor, ingresa una URL válida de GitHub "
                    "(ej: https://github.com/tu-usuario)"
                )
        
        return github
    
    def clean_image_src(self):
        """Validar imagen de perfil con restricciones de tamaño y tipo"""
        image = self.cleaned_data.get('image_src')
        if image:
            # Validar tamaño (5MB máximo)
            if image.size > 5 * 1024 * 1024:
                raise ValidationError(
                    f"La imagen es muy grande ({image.size // (1024*1024)}MB). "
                    f"El tamaño máximo es 5MB."
                )
            
            # Validar tipo de archivo por contenido real
            if hasattr(image, 'content_type'):
                valid_types = ['image/jpeg', 'image/png', 'image/webp']
                if image.content_type not in valid_types:
                    raise ValidationError(
                        "Formato de imagen no válido. "
                        "Usa JPG, PNG o WebP."
                    )
            
            # Validar dimensiones mínimas
            try:
                from PIL import Image
                img = Image.open(image)
                width, height = img.size
                
                if width < 100 or height < 100:
                    raise ValidationError(
                        "La imagen es muy pequeña. "
                        "Debe ser al menos de 100x100 píxeles."
                    )
                
                if width > 5000 or height > 5000:
                    raise ValidationError(
                        "La imagen es muy grande. "
                        "Las dimensiones máximas son 5000x5000 píxeles."
                    )
                
                # Resetear el puntero del archivo
                image.seek(0)
                
            except Exception as e:
                raise ValidationError(
                    "No se pudo procesar la imagen. "
                    "Asegúrate de que sea un archivo de imagen válido."
                )
        
        return image
    
    def clean_bio(self):
        """Limpiar y validar biografía"""
        bio = self.cleaned_data.get('bio')
        if bio:
            # Eliminar espacios múltiples y normalizar
            bio = ' '.join(bio.split())
            
            # Validar contenido inapropiado básico
            inappropriate_words = ['spam', 'xxx', 'viagra']
            bio_lower = bio.lower()
            
            for word in inappropriate_words:
                if word in bio_lower:
                    raise ValidationError(
                        "El contenido de la biografía no es apropiado."
                    )
            
            # Validar URLs no deseadas
            url_pattern = re.compile(r'https?://\S+', re.IGNORECASE)
            urls = url_pattern.findall(bio)
            if len(urls) > 2:
                raise ValidationError(
                    "Demasiados enlaces en la biografía. Máximo 2 permitidos."
                )
        
        return bio


class UserPreferencesForm(forms.ModelForm):
    """Formulario para preferencias del usuario con validaciones"""
    
    class Meta:
        model = UserPreferences
        fields = ['theme', 'items_per_page', 'dashboard_layout', 'quick_actions']
        widgets = {
            'theme': forms.Select(attrs={
                'class': 'form-select',
                'data-bs-toggle': 'tooltip',
                'title': 'Elige el tema visual de la interfaz'
            }),
            'items_per_page': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 5,
                'max': 100,
                'step': 5
            }),
            'dashboard_layout': forms.HiddenInput(),
            'quick_actions': forms.HiddenInput(),
        }
    
    def clean_items_per_page(self):
        """Validar items por página"""
        items_per_page = self.cleaned_data.get('items_per_page')
        if items_per_page:
            if items_per_page < 5:
                raise ValidationError("Mínimo 5 elementos por página.")
            if items_per_page > 100:
                raise ValidationError("Máximo 100 elementos por página.")
            
            # Redondear a múltiplo de 5
            items_per_page = round(items_per_page / 5) * 5
        
        return items_per_page
    
    def clean_dashboard_layout(self):
        """Validar estructura del layout del dashboard"""
        layout = self.cleaned_data.get('dashboard_layout')
        if layout and isinstance(layout, dict):
            # Validar estructura básica
            required_keys = ['widgets', 'columns']
            for key in required_keys:
                if key not in layout:
                    raise ValidationError(
                        f"Estructura de dashboard inválida: falta '{key}'"
                    )
            
            # Validar número de columnas
            if not isinstance(layout.get('columns'), int) or layout['columns'] not in [1, 2, 3, 4]:
                raise ValidationError(
                    "Número de columnas inválido. Debe ser entre 1 y 4."
                )
        
        return layout


class CustomPasswordChangeForm(PasswordChangeForm):
    """Formulario personalizado para cambio de contraseña con validaciones mejoradas"""
    
    old_password = forms.CharField(
        label="Contraseña actual",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu contraseña actual',
            'autocomplete': 'current-password',
            'required': True
        }),
        error_messages={
            'required': 'La contraseña actual es obligatoria.',
        }
    )
    
    new_password1 = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Crea una nueva contraseña segura',
            'autocomplete': 'new-password',
            'data-password-strength': 'true',
            'required': True
        }),
        help_text=password_validation.password_validators_help_text_html()
    )
    
    new_password2 = forms.CharField(
        label="Confirmar nueva contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repite la nueva contraseña',
            'autocomplete': 'new-password',
            'required': True
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personalizar mensajes de error
        self.fields['old_password'].error_messages['required'] = 'Debes ingresar tu contraseña actual.'
        self.fields['new_password1'].error_messages['required'] = 'Debes ingresar una nueva contraseña.'
        self.fields['new_password2'].error_messages['required'] = 'Debes confirmar la nueva contraseña.'
    
    def clean_old_password(self):
        """Validar contraseña actual con mejor manejo de errores"""
        old_password = self.cleaned_data.get('old_password')
        if old_password and not self.user.check_password(old_password):
            raise ValidationError(
                "La contraseña actual es incorrecta. Por favor, verifica e intenta nuevamente.",
                code='password_incorrect'
            )
        return old_password
    
    def clean_new_password1(self):
        """Validar nueva contraseña con reglas adicionales"""
        new_password1 = self.cleaned_data.get('new_password1')
        old_password = self.cleaned_data.get('old_password')
        
        if new_password1:
            # Validar que no sea igual a la anterior
            if old_password and new_password1 == old_password:
                raise ValidationError(
                    "La nueva contraseña debe ser diferente a la actual.",
                    code='password_unchanged'
                )
            
            # Validar fortaleza adicional
            if len(new_password1) < 10:
                raise ValidationError(
                    "Para mayor seguridad, usa al menos 10 caracteres.",
                    code='password_too_short'
                )
            
            # Validar entropía básica
            unique_chars = len(set(new_password1))
            if unique_chars < 5:
                raise ValidationError(
                    "La contraseña es muy repetitiva. Usa más variedad de caracteres.",
                    code='password_low_entropy'
                )
        
        return new_password1
    
    def clean(self):
        """Validaciones adicionales del formulario"""
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        
        if new_password1 and new_password2:
            if new_password1 != new_password2:
                self.add_error(
                    'new_password2',
                    ValidationError(
                        "Las contraseñas no coinciden. Por favor, verifica que sean idénticas.",
                        code='password_mismatch'
                    )
                )
        
        return cleaned_data


class BulkUserActionForm(forms.Form):
    """Formulario para acciones masivas en usuarios con validaciones"""
    
    ACTION_CHOICES = [
        ('', '-- Selecciona una acción --'),
        ('activate', 'Activar usuarios seleccionados'),
        ('deactivate', 'Desactivar usuarios seleccionados'),
        ('delete', 'Eliminar usuarios seleccionados'),
        ('export', 'Exportar datos de usuarios'),
        ('send_email', 'Enviar correo masivo'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        error_messages={
            'required': 'Debes seleccionar una acción.',
            'invalid_choice': 'Acción no válida.',
        }
    )
    
    user_ids = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )
    
    confirm = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'required': True
        }),
        label="Confirmo que quiero realizar esta acción y entiendo que puede ser irreversible",
        error_messages={
            'required': 'Debes confirmar la acción antes de continuar.',
        }
    )
    
    # Campo adicional para acciones específicas
    email_subject = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Asunto del correo'
        }),
        label="Asunto del correo (solo para envío masivo)"
    )
    
    email_message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Mensaje del correo'
        }),
        label="Mensaje del correo (solo para envío masivo)"
    )
    
    def clean_user_ids(self):
        """Validar y procesar IDs de usuarios"""
        user_ids = self.cleaned_data.get('user_ids')
        if user_ids:
            try:
                # Convertir string a lista de enteros
                ids = [int(id.strip()) for id in user_ids.split(',') if id.strip()]
                
                if not ids:
                    raise ValidationError("Debes seleccionar al menos un usuario.")
                
                # Validar que los usuarios existan
                existing_ids = User.objects.filter(id__in=ids).values_list('id', flat=True)
                invalid_ids = set(ids) - set(existing_ids)
                
                if invalid_ids:
                    raise ValidationError(
                        f"Los siguientes IDs de usuario no existen: {', '.join(map(str, invalid_ids))}"
                    )
                
                return ids
                
            except ValueError:
                raise ValidationError("IDs de usuarios inválidos. Verifica el formato.")
        
        raise ValidationError("Debes seleccionar usuarios para realizar la acción.")
    
    def clean(self):
        """Validaciones adicionales según la acción"""
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        user_ids = cleaned_data.get('user_ids')
        
        # Validaciones específicas por acción
        if action == 'delete' and user_ids:
            if len(user_ids) > 50:
                raise ValidationError(
                    "No puedes eliminar más de 50 usuarios a la vez por seguridad."
                )
        
        if action == 'send_email':
            if not cleaned_data.get('email_subject'):
                self.add_error('email_subject', 'El asunto es obligatorio para enviar correos.')
            if not cleaned_data.get('email_message'):
                self.add_error('email_message', 'El mensaje es obligatorio para enviar correos.')
        
        return cleaned_data


class UserSearchForm(forms.Form):
    """Formulario avanzado para búsqueda y filtrado de usuarios"""
    
    search = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, email, username o teléfono...',
            'autocomplete': 'off',
            'data-bs-toggle': 'tooltip',
            'title': 'Puedes buscar por múltiples campos'
        })
    )
    
    status = forms.ChoiceField(
        choices=[
            ('', 'Todos los estados'),
            ('active', 'Solo activos'),
            ('inactive', 'Solo inactivos'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    role = forms.ChoiceField(
        choices=[
            ('', 'Todos los roles'),
            ('admin', 'Solo administradores'),
            ('staff', 'Solo staff'),
            ('user', 'Solo usuarios regulares'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_joined_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'Desde'
        }),
        label="Registrado desde"
    )
    
    date_joined_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'Hasta'
        }),
        label="Registrado hasta"
    )
    
    has_profile_image = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('yes', 'Con foto de perfil'),
            ('no', 'Sin foto de perfil'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Foto de perfil"
    )
    
    profile_complete = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('complete', 'Perfil completo'),
            ('incomplete', 'Perfil incompleto'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Estado del perfil"
    )
    
    order_by = forms.ChoiceField(
        choices=[
            ('-date_joined', 'Más recientes primero'),
            ('date_joined', 'Más antiguos primero'),
            ('username', 'Username A-Z'),
            ('-username', 'Username Z-A'),
            ('email', 'Email A-Z'),
            ('-last_login', 'Último acceso reciente'),
        ],
        required=False,
        initial='-date_joined',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Ordenar por"
    )
    
    def clean(self):
        """Validar fechas y otros campos relacionados"""
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_joined_from')
        date_to = cleaned_data.get('date_joined_to')
        
        if date_from and date_to:
            if date_from > date_to:
                raise ValidationError({
                    'date_joined_from': 'La fecha inicial no puede ser mayor que la fecha final.',
                    'date_joined_to': 'La fecha final no puede ser menor que la fecha inicial.',
                })
            
            # Validar rango máximo
            delta = date_to - date_from
            if delta.days > 365:
                raise ValidationError(
                    "El rango de fechas no puede ser mayor a un año."
                )
        
        return cleaned_data


class AccountDeactivationForm(forms.Form):
    """Formulario mejorado para desactivación de cuenta con feedback"""
    
    REASON_CHOICES = [
        ('', '-- Selecciona una razón (opcional) --'),
        ('not_using', 'Ya no uso el servicio'),
        ('privacy', 'Preocupaciones de privacidad'),
        ('too_many_emails', 'Demasiados correos'),
        ('alternative', 'Encontré una mejor alternativa'),
        ('temporary', 'Solo necesito un descanso temporal'),
        ('technical', 'Problemas técnicos con la plataforma'),
        ('other', 'Otro motivo'),
    ]
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu contraseña actual para confirmar',
            'required': True,
            'autocomplete': 'current-password'
        }),
        label="Contraseña actual",
        help_text="Por seguridad, confirma tu identidad ingresando tu contraseña",
        error_messages={
            'required': 'La contraseña es obligatoria para desactivar tu cuenta.',
        }
    )
    
    reason = forms.ChoiceField(
        choices=REASON_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label="¿Por qué te vas? (opcional)",
        help_text="Tu feedback nos ayuda a mejorar"
    )
    
    feedback = forms.CharField(
        max_length=1000,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Si deseas compartir más detalles sobre tu decisión, '
                         'nos encantaría escucharte...',
            'maxlength': 1000
        }),
        label="Comentarios adicionales (opcional)",
        help_text="Máximo 1000 caracteres"
    )
    
    confirm = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'required': True
        }),
        label=mark_safe(
            "Entiendo que mi cuenta será <strong>desactivada permanentemente</strong> "
            "y todos mis datos serán eliminados en 30 días"
        ),
        error_messages={
            'required': 'Debes confirmar que entiendes las consecuencias.',
        }
    )
    
    keep_data = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label="Mantener mis datos por si decido volver (recomendado)",
        help_text="Podrás reactivar tu cuenta contactando al soporte"
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_password(self):
        """Validar contraseña actual"""
        password = self.cleaned_data.get('password')
        if password:
            if not self.user.check_password(password):
                raise ValidationError(
                    "Contraseña incorrecta. Por favor, verifica e intenta nuevamente.",
                    code='invalid_password'
                )
        return password
    
    def clean_feedback(self):
        """Limpiar y validar feedback"""
        feedback = self.cleaned_data.get('feedback')
        if feedback:
            # Eliminar espacios múltiples
            feedback = ' '.join(feedback.split())
        return feedback