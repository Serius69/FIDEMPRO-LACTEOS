from django import forms
from django.core.exceptions import ValidationError
from .models import Product, Area
from business.models import Business

class ProductForm(forms.ModelForm):
    """Formulario mejorado para productos con validaciones adicionales"""
    
    class Meta:
        model = Product
        fields = ['name', 'type', 'description', 'image_src', 'fk_business']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el nombre del producto',
                'maxlength': '100',
                'required': True,
                'autocomplete': 'off'
            }),
            'type': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describa el producto detalladamente',
                'rows': 4,
                'required': True,
                'maxlength': '1000'
            }),
            'image_src': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/jpeg,image/jpg,image/png'
            }),
            'fk_business': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            })
        }
        labels = {
            'name': 'Nombre del Producto',
            'type': 'Tipo de Producto',
            'description': 'Descripción',
            'image_src': 'Imagen del Producto',
            'fk_business': 'Negocio'
        }
        help_texts = {
            'name': 'Máximo 100 caracteres',
            'description': 'Proporcione una descripción clara y detallada',
            'image_src': 'Formatos: JPG, PNG. Tamaño máximo: 5MB',
            'fk_business': 'Seleccione el negocio al que pertenece este producto'
        }
    
    def __init__(self, *args, **kwargs):
        # Extraer el usuario si se proporciona
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Personalizar campos
        self.fields['name'].widget.attrs.update({
            'autofocus': True,
            'data-validation': 'required'
        })
        
        # Filtrar negocios solo del usuario actual si se proporciona
        if self.user:
            self.fields['fk_business'].queryset = Business.objects.filter(
                fk_user=self.user,
                is_active=True
            ).order_by('name')
        
        # Agregar placeholders dinámicos
        for field_name, field in self.fields.items():
            if field.help_text:
                field.widget.attrs['title'] = field.help_text
    
    def clean_name(self):
        """Validar y normalizar el nombre del producto"""
        name = self.cleaned_data.get('name')
        if name:
            # Normalizar espacios y capitalizar
            name = ' '.join(name.split()).strip().title()
            
            # Validar longitud mínima
            if len(name) < 3:
                raise ValidationError("El nombre debe tener al menos 3 caracteres.")
            
            # Validar caracteres especiales
            import re
            if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\-\.0-9]+$', name):
                raise ValidationError("El nombre solo puede contener letras, números, espacios, guiones y puntos.")
                
        return name
    
    def clean_description(self):
        """Validar la descripción"""
        description = self.cleaned_data.get('description')
        if description:
            # Normalizar espacios
            description = ' '.join(description.split()).strip()
            
            # Validar longitud mínima
            if len(description) < 10:
                raise ValidationError("La descripción debe tener al menos 10 caracteres.")
                
        return description
    
    def clean_image_src(self):
        """Validación adicional para la imagen"""
        image = self.cleaned_data.get('image_src')
        if image:
            # Validar tamaño
            if image.size > 5 * 1024 * 1024:
                raise ValidationError("La imagen no puede ser mayor a 5MB.")
            
            # Validar tipo MIME
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png']
            if hasattr(image, 'content_type') and image.content_type not in allowed_types:
                raise ValidationError("Solo se permiten imágenes JPG o PNG.")
                
        return image
    
    def clean(self):
        """Validaciones que involucran múltiples campos"""
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        fk_business = cleaned_data.get('fk_business')
        
        if name and fk_business:
            # Verificar unicidad del nombre en el negocio
            qs = Product.objects.filter(
                name__iexact=name,
                fk_business=fk_business,
                is_active=True
            )
            
            # Si estamos editando, excluir el producto actual
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
                
            if qs.exists():
                raise ValidationError({
                    'name': f'Ya existe un producto llamado "{name}" en este negocio.'
                })
        
        return cleaned_data
    
    def save(self, commit=True):
        """Guardar el formulario con procesamiento adicional"""
        product = super().save(commit=False)
        
        # Asegurar que el nombre esté capitalizado
        if product.name:
            product.name = product.name.title()
        
        if commit:
            product.save()
            
        return product


class AreaForm(forms.ModelForm):
    """Formulario mejorado para áreas con validaciones adicionales"""
    
    class Meta:
        model = Area
        fields = ['name', 'description', 'image_src', 'fk_product']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el nombre del área',
                'maxlength': '100',
                'required': True,
                'autocomplete': 'off'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describa el área y su función',
                'rows': 4,
                'required': True,
                'maxlength': '1000'
            }),
            'image_src': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/jpeg,image/jpg,image/png'
            }),
            'fk_product': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            })
        }
        labels = {
            'name': 'Nombre del Área',
            'description': 'Descripción',
            'image_src': 'Imagen del Área',
            'fk_product': 'Producto Asociado'
        }
        help_texts = {
            'name': 'Máximo 100 caracteres',
            'description': 'Explique la función de esta área en el producto',
            'image_src': 'Formatos: JPG, PNG. Tamaño máximo: 5MB',
            'fk_product': 'Seleccione el producto al que pertenece esta área'
        }
    
    def __init__(self, *args, **kwargs):
        # Extraer el usuario si se proporciona
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Personalizar campos
        self.fields['name'].widget.attrs.update({
            'autofocus': True,
            'data-validation': 'required'
        })
        
        # Filtrar productos solo del usuario actual si se proporciona
        if self.user:
            self.fields['fk_product'].queryset = Product.objects.filter(
                fk_business__fk_user=self.user,
                is_active=True
            ).select_related('fk_business').order_by('name')
            
            # Personalizar la visualización del producto
            self.fields['fk_product'].label_from_instance = lambda obj: f"{obj.name} ({obj.fk_business.name})"
    
    def clean_name(self):
        """Validar y normalizar el nombre del área"""
        name = self.cleaned_data.get('name')
        if name:
            # Normalizar espacios y capitalizar
            name = ' '.join(name.split()).strip().title()
            
            # Validar longitud mínima
            if len(name) < 3:
                raise ValidationError("El nombre debe tener al menos 3 caracteres.")
            
            # Validar caracteres especiales
            import re
            if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\-\.0-9]+$', name):
                raise ValidationError("El nombre solo puede contener letras, números, espacios, guiones y puntos.")
                
        return name
    
    def clean_description(self):
        """Validar la descripción"""
        description = self.cleaned_data.get('description')
        if description:
            # Normalizar espacios
            description = ' '.join(description.split()).strip()
            
            # Validar longitud mínima
            if len(description) < 10:
                raise ValidationError("La descripción debe tener al menos 10 caracteres.")
                
        return description
    
    def clean_image_src(self):
        """Validación adicional para la imagen"""
        image = self.cleaned_data.get('image_src')
        if image:
            # Validar tamaño
            if image.size > 5 * 1024 * 1024:
                raise ValidationError("La imagen no puede ser mayor a 5MB.")
            
            # Validar tipo MIME
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png']
            if hasattr(image, 'content_type') and image.content_type not in allowed_types:
                raise ValidationError("Solo se permiten imágenes JPG o PNG.")
                
        return image
    
    def clean(self):
        """Validaciones que involucran múltiples campos"""
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        fk_product = cleaned_data.get('fk_product')
        
        if name and fk_product:
            # Verificar unicidad del nombre en el producto
            qs = Area.objects.filter(
                name__iexact=name,
                fk_product=fk_product,
                is_active=True
            )
            
            # Si estamos editando, excluir el área actual
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
                
            if qs.exists():
                raise ValidationError({
                    'name': f'Ya existe un área llamada "{name}" en este producto.'
                })
        
        return cleaned_data
    
    def save(self, commit=True):
        """Guardar el formulario con procesamiento adicional"""
        area = super().save(commit=False)
        
        # Asegurar que el nombre esté capitalizado
        if area.name:
            area.name = area.name.title()
        
        if commit:
            area.save()