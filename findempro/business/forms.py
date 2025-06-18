from django import forms
from .models import Business
from django.core.exceptions import ValidationError

class BusinessForm(forms.ModelForm):
    """
    Formulario para crear y actualizar negocios.
    Incluye validaciones personalizadas y configuración de widgets.
    """
    
    class Meta:
        model = Business
        fields = ['name', 'type', 'location', 'image_src', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Mi Tienda Favorita',
                'minlength': '2',
                'maxlength': '255',
                'required': True
            }),
            'type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'location': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }, choices=[
                ('', 'Selecciona una ciudad'),
                ('La Paz', 'La Paz'),
                ('Santa Cruz', 'Santa Cruz'),
                ('Cochabamba', 'Cochabamba'),
                ('Sucre', 'Sucre'),
                ('Oruro', 'Oruro'),
                ('Potosí', 'Potosí'),
                ('Tarija', 'Tarija'),
                ('Beni', 'Beni'),
                ('Pando', 'Pando'),
            ]),
            'image_src': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/png, image/jpeg, image/jpg, image/webp'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe tu negocio, productos principales, servicios que ofreces...',
                'minlength': '10',
                'maxlength': '1000',
                'required': True
            })
        }
        labels = {
            'name': 'Nombre del Negocio',
            'type': 'Tipo de Negocio',
            'location': 'Ubicación',
            'image_src': 'Imagen del Negocio',
            'description': 'Descripción'
        }
        error_messages = {
            'name': {
                'required': 'El nombre del negocio es obligatorio.',
                'max_length': 'El nombre no puede exceder 255 caracteres.',
            },
            'type': {
                'required': 'Debes seleccionar un tipo de negocio.',
            },
            'location': {
                'required': 'La ubicación es obligatoria.',
            },
            'description': {
                'required': 'La descripción es obligatoria.',
                'min_length': 'La descripción debe tener al menos 10 caracteres.',
            }
        }
    
    def clean_name(self):
        """Valida y limpia el nombre del negocio."""
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            if len(name) < 2:
                raise ValidationError('El nombre debe tener al menos 2 caracteres.')
        return name
    
    def clean_description(self):
        """Valida y limpia la descripción."""
        description = self.cleaned_data.get('description')
        if description:
            description = description.strip()
            if len(description) < 10:
                raise ValidationError('La descripción debe tener al menos 10 caracteres.')
            if len(description) > 1000:
                raise ValidationError('La descripción no puede exceder 1000 caracteres.')
        return description
    
    def clean_image_src(self):
        """Valida el archivo de imagen."""
        image = self.cleaned_data.get('image_src')
        if image:
            # Validar tamaño (5MB máximo)
            if image.size > 5 * 1024 * 1024:
                raise ValidationError('La imagen no debe superar los 5MB.')
            
            # Validar tipo de archivo
            valid_types = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp']
            if hasattr(image, 'content_type') and image.content_type not in valid_types:
                raise ValidationError('Formato de imagen no válido. Use PNG, JPG o WEBP.')
        
        return image
    
    def clean(self):
        """Validaciones adicionales del formulario completo."""
        cleaned_data = super().clean()
        
        # Verificar que location no esté vacío
        location = cleaned_data.get('location')
        if not location or location == '':
            self.add_error('location', 'Debes seleccionar una ubicación.')
        
        return cleaned_data