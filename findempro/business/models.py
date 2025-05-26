from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class BusinessQuerySet(models.QuerySet):
    """QuerySet personalizado para el modelo Business."""
    
    def active(self):
        """Retorna solo los negocios activos."""
        return self.filter(is_active=True)
    
    def by_user(self, user):
        """Filtra negocios por usuario."""
        return self.filter(fk_user=user)
    
    def with_related(self):
        """Optimiza las consultas relacionadas."""
        return self.select_related('fk_user').prefetch_related('products')


class BusinessManager(models.Manager):
    """Manager personalizado para el modelo Business."""
    
    def get_queryset(self):
        """Retorna el QuerySet personalizado."""
        return BusinessQuerySet(self.model, using=self._db)
    
    def active(self):
        """Acceso directo a negocios activos."""
        return self.get_queryset().active()
    
    def for_user(self, user):
        """Acceso directo a negocios de un usuario."""
        return self.get_queryset().active().by_user(user)


class Business(models.Model):
    """
    Modelo que representa un negocio en el sistema.
    
    Attributes:
        name: Nombre del negocio
        type: Tipo de negocio (Lácteos, Agricultura, etc.)
        location: Ubicación del negocio
        image_src: Imagen representativa del negocio
        description: Descripción detallada del negocio
        fk_user: Usuario propietario del negocio
        is_active: Estado activo/inactivo del negocio
        date_created: Fecha de creación
        last_updated: Última actualización
    """
    
    class BusinessType(models.IntegerChoices):
        """Tipos de negocio disponibles."""
        DAIRY = 1, _('Lácteos')
        AGRICULTURE = 2, _('Agricultura')
        CONSUMER_GOODS = 3, _('Bienes de Consumo')
        BAKERY = 4, _('Panadería')
        BUTCHER = 5, _('Carnicería')
        GROCERY = 6, _('Verdulería')
        OTHER = 7, _('Otros')
    
    # Campos principales
    name = models.CharField(
        max_length=255,
        verbose_name=_('Nombre'),
        help_text=_('El nombre del negocio'),
        db_index=True
    )
    
    type = models.IntegerField(
        choices=BusinessType.choices,
        default=BusinessType.DAIRY,
        verbose_name=_('Tipo'),
        help_text=_('El tipo de negocio')
    )
    
    location = models.CharField(
        max_length=255,
        verbose_name=_('Ubicación'),
        help_text=_('La ubicación del negocio'),
        db_index=True
    )
    
    image_src = models.ImageField(
        upload_to='images/business/%Y/%m/',
        null=True,
        blank=True,
        verbose_name=_('Imagen'),
        help_text=_('La imagen del negocio')
    )
    
    description = models.TextField(
        verbose_name=_('Descripción'),
        help_text=_('La descripción del negocio'),
        blank=True,
        default=''
    )
    
    # Relaciones
    fk_user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='businesses',
        verbose_name=_('Usuario'),
        help_text=_('El usuario asociado con el negocio'),
        db_index=True
    )
    
    # Campos de control
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Activo'),
        help_text=_('Si el negocio está activo o no'),
        db_index=True
    )
    
    date_created = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('Fecha de Creación'),
        help_text=_('La fecha en que se creó el negocio'),
        db_index=True
    )
    
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Última Actualización'),
        help_text=_('La fecha de la última actualización')
    )
    
    # Manager personalizado
    objects = BusinessManager()
    
    class Meta:
        """Configuración del modelo."""
        verbose_name = _('Negocio')
        verbose_name_plural = _('Negocios')
        ordering = ['-date_created']
        indexes = [
            models.Index(fields=['fk_user', 'is_active']),
            models.Index(fields=['type', 'is_active']),
            models.Index(fields=['location', 'is_active']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'fk_user'],
                condition=models.Q(is_active=True),
                name='unique_active_business_per_user'
            )
        ]

    def __str__(self):
        """Representación en string del negocio."""
        return f"{self.name} - {self.get_type_display()}"

    def __repr__(self):
        """Representación técnica del objeto."""
        return f"<Business: {self.name} (ID: {self.id}, User: {self.fk_user.username})>"

    def get_absolute_url(self):
        """URL canónica del negocio."""
        return reverse('business:business.overview', kwargs={'pk': self.pk})

    def get_photo_url(self) -> str:
        """
        Obtiene la URL de la foto del negocio.
        
        Returns:
            str: URL de la imagen o imagen por defecto
        """
        if self.image_src and hasattr(self.image_src, 'url'):
            return self.image_src.url
        return "/static/images/business/business-dummy-img.webp"

    @property
    def is_dairy(self) -> bool:
        """Verifica si el negocio es de tipo lácteos."""
        return self.type == self.BusinessType.DAIRY

    @property
    def products_count(self) -> int:
        """Cuenta el número de productos activos del negocio."""
        return self.products.filter(is_active=True).count()

    @property
    def owner_name(self) -> str:
        """Obtiene el nombre completo del propietario."""
        if self.fk_user.get_full_name():
            return self.fk_user.get_full_name()
        return self.fk_user.username

    def save(self, *args, **kwargs):
        """Override save para actualizar last_updated automáticamente."""
        # Capitalizar el nombre antes de guardar
        if self.name:
            self.name = self.name.strip().title()
        
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Override delete para implementar eliminación lógica."""
        self.is_active = False
        self.save(update_fields=['is_active', 'last_updated'])

    def hard_delete(self):
        """Eliminación física real del registro."""
        super().delete()

    def clean(self):
        """Validación personalizada del modelo."""
        from django.core.exceptions import ValidationError
        
        if self.name and len(self.name.strip()) < 3:
            raise ValidationError({
                'name': _('El nombre del negocio debe tener al menos 3 caracteres.')
            })
        
        if self.description and len(self.description.strip()) > 1000:
            raise ValidationError({
                'description': _('La descripción no puede exceder 1000 caracteres.')
            })