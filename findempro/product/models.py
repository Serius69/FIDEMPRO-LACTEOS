from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from business.models import Business
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
import os
from PIL import Image
from django.core.files.storage import default_storage
from .products_data import products_data
from .areas_data import areas_data

def validate_image_size(image):
    """Validar que la imagen no sea muy grande"""
    if image:
        if image.size > 5 * 1024 * 1024:  # 5MB
            raise ValidationError("La imagen no puede ser mayor a 5MB.")

def validate_image_format(image):
    """Validar que la imagen esté en formato correcto"""
    if image:
        allowed_formats = ['JPEG', 'JPG', 'PNG']
        try:
            img = Image.open(image)
            if img.format not in allowed_formats:
                raise ValidationError("Solo se permiten imágenes en formato JPEG, JPG o PNG.")
        except Exception:
            raise ValidationError("El archivo no es una imagen válida.")

class Product(models.Model):
    name = models.CharField(
        max_length=100, 
        help_text="Nombre del producto (máximo 100 caracteres)",
        verbose_name="Nombre del Producto"
    )
    description = models.TextField(
        help_text="Descripción detallada del producto",
        verbose_name="Descripción"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indica si el producto está activo",
        verbose_name="Activo"
    )
    date_created = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha de Creación"
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Actualización"
    )
    image_src = models.ImageField(
        upload_to='images/product', 
        blank=True, 
        null=True,
        validators=[validate_image_size, validate_image_format],
        help_text="Imagen del producto (máximo 5MB, formatos: JPG, PNG)",
        verbose_name="Imagen"
    )
    fk_business = models.ForeignKey(
        Business, 
        on_delete=models.CASCADE, 
        related_name='fk_business_product', 
        help_text='El negocio asociado con el producto',
        verbose_name="Negocio"
    )
    
    TYPE_CHOICES = [
        (1, 'Lácteos'),
        (2, 'Servicio'),
    ]    
    type = models.IntegerField(
        default=1, 
        choices=TYPE_CHOICES,
        verbose_name="Tipo de Producto"
    )
    
    profit_margin = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Margen de ganancia en porcentaje (0-100%)",
        verbose_name="Margen de Ganancia (%)"
    )
    earnings = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Ganancias totales",
        verbose_name="Ganancias"
    )
    inventory_levels = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Nivel actual de inventario",
        verbose_name="Nivel de Inventario"
    )
    production_output = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Producción estimada",
        verbose_name="Producción"
    )
    demand_forecast = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Pronóstico de demanda",
        verbose_name="Pronóstico de Demanda"
    )
    costs = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Costos totales del producto",
        verbose_name="Costos"
    )
    is_ready = models.BooleanField(
        default=False,
        help_text="Indica si el producto está listo para simulación",
        verbose_name="Listo para Simulación"
    )

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['-date_created']
        indexes = [
            models.Index(fields=['is_active', 'fk_business']),
            models.Index(fields=['date_created']),
        ]

    def __str__(self) -> str:
        return f"{self.name} - {self.fk_business.name}"

    def clean(self):
        """Validaciones personalizadas del modelo"""
        errors = {}
        
        if self.profit_margin is not None and self.profit_margin < 0:
            errors['profit_margin'] = 'El margen de ganancia no puede ser negativo.'
        
        if self.costs is not None and self.costs < 0:
            errors['costs'] = 'Los costos no pueden ser negativos.'
        
        if self.earnings is not None and self.earnings < 0:
            errors['earnings'] = 'Las ganancias no pueden ser negativas.'
        
        # Validar que el negocio esté activo
        if self.fk_business and not self.fk_business.is_active:
            errors['fk_business'] = 'No se puede asignar el producto a un negocio inactivo.'
        
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Override del método save para validaciones adicionales"""
        self.full_clean()
        
        # Actualizar la fecha de última modificación
        if self.pk:  # Si es una actualización
            self.last_updated = timezone.now()
        
        super().save(*args, **kwargs)

    def get_photo_url(self) -> str:
        """Obtener URL de la imagen del producto"""
        if self.image_src and hasattr(self.image_src, 'url'):
            return self.image_src.url
        else:
            return "/static/images/product/product-dummy-img.webp"

    def get_absolute_url(self):
        """URL absoluta del producto"""
        return reverse('product:product.overview', kwargs={'pk': self.pk})

    @property
    def areas_count(self):
        """Contar áreas asociadas al producto"""
        return self.fk_product_area.filter(is_active=True).count()

    @property
    def variables_count(self):
        """Contar variables asociadas al producto"""
        return self.fk_product_variable.filter(is_active=True).count()

    def soft_delete(self):
        """Eliminación suave del producto"""
        self.is_active = False
        self.save()

class Area(models.Model):
    name = models.CharField(
        max_length=100,
        help_text="Nombre del área (máximo 100 caracteres)",
        verbose_name="Nombre del Área"
    )
    description = models.TextField(
        help_text="Descripción detallada del área",
        verbose_name="Descripción"
    )
    image_src = models.ImageField(
        upload_to='images/area', 
        blank=True, 
        null=True,
        validators=[validate_image_size, validate_image_format],
        help_text="Imagen del área (máximo 5MB, formatos: JPG, PNG)",
        verbose_name="Imagen"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indica si el área está activa",
        verbose_name="Activa"
    )
    date_created = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha de Creación"
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Actualización"
    )
    fk_product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='fk_product_area', 
        help_text='El producto asociado con el área',
        verbose_name="Producto"
    )
    is_checked_for_simulation = models.BooleanField(
        default=False,
        help_text="Indica si el área está marcada para simulación",
        verbose_name="Marcada para Simulación"
    )
    params = models.JSONField(
        null=True, 
        blank=True,
        help_text="Parámetros del área en formato JSON",
        verbose_name="Parámetros"
    )

    class Meta:
        verbose_name = "Área"
        verbose_name_plural = "Áreas"
        ordering = ['-date_created']
        unique_together = ['name', 'fk_product']  # Evitar áreas duplicadas por producto
        indexes = [
            models.Index(fields=['is_active', 'fk_product']),
            models.Index(fields=['date_created']),
        ]

    def __str__(self) -> str:
        return f"{self.name} - {self.fk_product.name}"

    def clean(self):
        """Validaciones personalizadas del modelo"""
        errors = {}
        
        # Validar que el producto esté activo
        if self.fk_product and not self.fk_product.is_active:
            errors['fk_product'] = 'No se puede asignar el área a un producto inactivo.'
        
        # Validar formato JSON si se proporcionan parámetros
        if self.params:
            try:
                if not isinstance(self.params, (dict, list)):
                    errors['params'] = 'Los parámetros deben estar en formato JSON válido.'
            except Exception:
                errors['params'] = 'Los parámetros deben estar en formato JSON válido.'
        
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Override del método save para validaciones adicionales"""
        self.full_clean()
        
        # Actualizar la fecha de última modificación
        if self.pk:  # Si es una actualización
            self.last_updated = timezone.now()
        
        super().save(*args, **kwargs)

    def get_photo_url(self) -> str:
        """Obtener URL de la imagen del área"""
        if self.image_src and hasattr(self.image_src, 'url'):
            return self.image_src.url
        else:
            return "/static/images/area/area-dummy-img.webp"

    def get_absolute_url(self):
        """URL absoluta del área"""
        return reverse('product:area.overview', kwargs={'pk': self.pk})

    @property
    def equations_count(self):
        """Contar ecuaciones asociadas al área"""
        return self.fk_area_equations.filter(is_active=True).count()

    def soft_delete(self):
        """Eliminación suave del área"""
        self.is_active = False
        self.save()

# Signals para optimización de imágenes
@receiver(pre_save, sender=Product)
@receiver(pre_save, sender=Area)
def optimize_image(sender, instance, **kwargs):
    """Optimizar imágenes antes de guardar"""
    if instance.image_src:
        try:
            img = Image.open(instance.image_src)
            # Redimensionar si es muy grande
            if img.width > 1200 or img.height > 1200:
                img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
                
            # Convertir a RGB si es necesario
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # Guardar la imagen optimizada
            from io import BytesIO
            import sys
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=85, optimize=True)
            buffer.seek(0)
            
            from django.core.files import File
            instance.image_src.save(
                instance.image_src.name,
                File(buffer),
                save=False
            )
        except Exception as e:
            # Si hay error en la optimización, continuar con la imagen original
            pass

@receiver(post_save, sender=Product)
def update_product_ready_status(sender, instance, **kwargs):
    """Actualizar el estado 'listo' del producto basado en áreas y variables"""
    if instance.is_active:
        areas_count = instance.fk_product_area.filter(is_active=True).count()
        variables_count = instance.fk_product_variable.filter(is_active=True).count()
        
        # Un producto está listo si tiene al menos 1 área y 1 variable
        is_ready = areas_count > 0 and variables_count > 0
        
        if instance.is_ready != is_ready:
            Product.objects.filter(pk=instance.pk).update(is_ready=is_ready)