from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class BusinessQuerySet(models.QuerySet):
    """QuerySet personalizado para el modelo Business."""

    def active(self):
        return self.filter(is_active=True)

    def by_user(self, user):
        return self.filter(
            organization__memberships__user=user,
            organization__memberships__is_active=True,
        ).distinct()

    def for_organization(self, organization):
        return self.filter(organization=organization)

    def by_industry(self, industry_type):
        return self.filter(type=industry_type)

    def with_related(self):
        return self.select_related('fk_user', 'organization').prefetch_related('products')


class BusinessManager(models.Manager):
    """Manager personalizado para el modelo Business."""

    def get_queryset(self):
        return BusinessQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def for_user(self, user):
        return self.get_queryset().active().by_user(user)

    def by_industry(self, industry_type):
        return self.get_queryset().active().by_industry(industry_type)


class Business(models.Model):
    """
    Modelo que representa un negocio/PyME en el sistema.
    Genérico para cualquier tipo de industria.
    """

    class BusinessType(models.IntegerChoices):
        """Tipos de industria soportados — multi-sector."""
        # Producción / Manufactura
        DAIRY = 1, _('Lácteos')
        AGRICULTURE = 2, _('Agricultura')
        BAKERY = 4, _('Panadería')
        BUTCHER = 5, _('Carnicería')
        FOOD_MANUFACTURING = 8, _('Manufactura Alimentaria')
        MANUFACTURING = 9, _('Manufactura General')
        # Comercio
        CONSUMER_GOODS = 3, _('Bienes de Consumo')
        GROCERY = 6, _('Verdulería / Minimarket')
        RETAIL = 10, _('Retail / Comercio')
        WHOLESALE = 11, _('Mayorista')
        # Servicios
        SERVICES = 12, _('Servicios Generales')
        HEALTH_SERVICES = 13, _('Salud')
        EDUCATION = 14, _('Educación')
        LOGISTICS = 15, _('Logística / Transporte')
        HOSPITALITY = 16, _('Hotelería / Restaurantes')
        TECH = 17, _('Tecnología / Software')
        CONSTRUCTION = 18, _('Construcción')
        FINANCIAL_SERVICES = 19, _('Servicios Financieros')
        OTHER = 7, _('Otros')

    # Sector macro para agrupación rápida
    class IndustrySector(models.TextChoices):
        PRODUCTION = 'production', _('Producción')
        RETAIL = 'retail', _('Comercio / Retail')
        SERVICES = 'services', _('Servicios')
        AGRO = 'agro', _('Agropecuario')
        MANUFACTURING = 'manufacturing', _('Manufactura')
        OTHER = 'other', _('Otro')

    # Mapping BusinessType → IndustrySector
    SECTOR_MAP = {
        1: 'agro', 2: 'agro', 4: 'production', 5: 'production',
        8: 'production', 9: 'manufacturing', 3: 'retail', 6: 'retail',
        10: 'retail', 11: 'retail', 12: 'services', 13: 'services',
        14: 'services', 15: 'services', 16: 'services', 17: 'services',
        18: 'manufacturing', 19: 'services', 7: 'other',
    }

    name = models.CharField(
        max_length=255,
        verbose_name=_('Nombre'),
        help_text=_('El nombre del negocio'),
        db_index=True
    )

    type = models.IntegerField(
        choices=BusinessType.choices,
        default=BusinessType.OTHER,
        verbose_name=_('Tipo de Industria'),
        help_text=_('El tipo/industria del negocio')
    )

    industry_sector = models.CharField(
        max_length=20,
        choices=IndustrySector.choices,
        default=IndustrySector.OTHER,
        verbose_name=_('Sector'),
        help_text=_('Sector macro del negocio (calculado automáticamente)'),
        db_index=True
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
    organization = models.ForeignKey(
        'tenancy.Organization',
        on_delete=models.PROTECT,
        related_name='businesses',
        null=True,
        blank=True,
        db_index=True,
        help_text=_('Organization comercial propietaria. fk_user se conserva como creador legacy.'),
    )
    
    # Product relation should be defined in Product model with related_name='products'
    # This assumes Product model has: fk_business = ForeignKey(Business, related_name='products', ...)
    
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
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['type', 'is_active']),
            models.Index(fields=['location', 'is_active']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'fk_user'],
                condition=models.Q(is_active=True),
                name='unique_active_business_per_user'
            ),
            models.UniqueConstraint(
                fields=['name', 'organization'],
                condition=models.Q(is_active=True),
                name='unique_active_business_per_org',
            ),
            models.CheckConstraint(
                condition=models.Q(organization__isnull=False),
                name='business_requires_organization',
            ),
        ]

    def __str__(self):
        """Representación en string del negocio."""
        return f"{self.name} - {self.BusinessType(self.type).label}"

    def __repr__(self):
        """Representación técnica del objeto."""
        return f"<Business: {self.name} (ID: {self.pk}, User: {self.fk_user.username})>"

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
        """Compatibilidad retroactiva — verifica si el negocio es de tipo lácteos."""
        return self.type == self.BusinessType.DAIRY

    @property
    def sector_label(self) -> str:
        """Etiqueta legible del sector macro."""
        try:
            return self.IndustrySector(self.industry_sector).label
        except ValueError:
            return 'Otro'

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
        """Override save — normaliza nombre y calcula sector automáticamente."""
        if self.organization_id is None and self.fk_user_id:
            from tenancy.services import ensure_default_organization

            self.organization = ensure_default_organization(self.fk_user)
        if self.name:
            self.name = self.name.strip().title()
        # Auto-asignar sector macro según tipo de industria
        self.industry_sector = self.SECTOR_MAP.get(self.type, self.IndustrySector.OTHER)
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


class CompanyProfile(models.Model):
    """
    Perfil de configuración por empresa para el motor de simulación.
    Parametriza el comportamiento del modelo matemático según la industria.
    Permite que cada PyME tenga su propio modelo de simulación.
    """

    # Patrones de demanda por sector
    class DemandPattern(models.TextChoices):
        STABLE = 'stable', _('Estable')
        SEASONAL = 'seasonal', _('Estacional')
        TRENDING_UP = 'trending_up', _('Creciente')
        TRENDING_DOWN = 'trending_down', _('Decreciente')
        VOLATILE = 'volatile', _('Volátil')
        CYCLIC = 'cyclic', _('Cíclico')

    # Distribución estadística preferida para la demanda
    class DistributionPreference(models.TextChoices):
        AUTO = 'auto', _('Automática (mejor ajuste)')
        NORMAL = 'normal', _('Normal')
        LOGNORMAL = 'lognormal', _('Log-Normal')
        GAMMA = 'gamma', _('Gamma')
        UNIFORM = 'uniform', _('Uniforme')

    fk_business = models.OneToOneField(
        Business,
        on_delete=models.CASCADE,
        related_name='company_profile',
        verbose_name=_('Negocio')
    )

    # === Variables clave del negocio ===
    primary_cost_driver = models.CharField(
        max_length=100,
        default='costo_produccion',
        verbose_name=_('Variable de Costo Principal'),
        help_text=_('Nombre de la variable que más impacta los costos (ej: costo_produccion, costo_servicio)')
    )
    primary_revenue_driver = models.CharField(
        max_length=100,
        default='precio_venta',
        verbose_name=_('Variable de Ingreso Principal'),
        help_text=_('Variable que determina los ingresos (ej: precio_venta, tarifa_servicio)')
    )
    demand_variable_name = models.CharField(
        max_length=100,
        default='demanda',
        verbose_name=_('Nombre Variable de Demanda'),
        help_text=_('Nombre de la variable de demanda en las ecuaciones')
    )

    # === Parámetros de estacionalidad ===
    demand_pattern = models.CharField(
        max_length=20,
        choices=DemandPattern.choices,
        default=DemandPattern.STABLE,
        verbose_name=_('Patrón de Demanda')
    )
    seasonality_factor = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Factores de Estacionalidad'),
        help_text=_('Lista de 12 factores mensuales [ene..dic]. Ej: [1.2, 0.9, 1.0, ...]')
    )
    peak_months = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Meses Pico'),
        help_text=_('Lista de meses con alta demanda [1=enero..12=diciembre]')
    )

    # === Parámetros del modelo matemático ===
    distribution_preference = models.CharField(
        max_length=20,
        choices=DistributionPreference.choices,
        default=DistributionPreference.AUTO,
        verbose_name=_('Distribución Estadística')
    )
    monte_carlo_iterations = models.PositiveIntegerField(
        default=10000,
        verbose_name=_('Iteraciones Monte Carlo'),
        help_text=_('Número de iteraciones para la simulación (1000-100000)')
    )
    confidence_level = models.FloatField(
        default=0.95,
        verbose_name=_('Nivel de Confianza'),
        help_text=_('Nivel de confianza estadístico (0.80-0.99)')
    )

    # === Umbrales de alerta financiera ===
    min_profit_margin_pct = models.FloatField(
        default=10.0,
        verbose_name=_('Margen de Ganancia Mínimo (%)'),
        help_text=_('Umbral mínimo aceptable de margen de ganancia')
    )
    max_cost_revenue_ratio = models.FloatField(
        default=70.0,
        verbose_name=_('Ratio Costo/Ingreso Máximo (%)'),
        help_text=_('Alerta si los costos superan este % de los ingresos')
    )
    inventory_days_target = models.PositiveIntegerField(
        default=30,
        verbose_name=_('Días de Inventario Objetivo'),
        help_text=_('Días ideales de stock de seguridad')
    )

    # === Metadatos ===
    custom_kpis = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('KPIs Personalizados'),
        help_text=_('Diccionario de KPIs específicos de la industria')
    )
    simulation_notes = models.TextField(
        blank=True,
        default='',
        verbose_name=_('Notas de Configuración')
    )
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Perfil de Empresa')
        verbose_name_plural = _('Perfiles de Empresa')

    def __str__(self):
        return f"Perfil: {self.fk_business.name}"

    def get_seasonality_factors(self):
        """Retorna factores de estacionalidad (12 meses). Si no están configurados, devuelve 1.0."""
        if self.seasonality_factor and len(self.seasonality_factor) == 12:
            return self.seasonality_factor
        return [1.0] * 12

    def get_effective_iterations(self):
        """Retorna iteraciones dentro del rango seguro."""
        return max(1000, min(100000, self.monte_carlo_iterations))

    @classmethod
    def get_or_create_for_business(cls, business):
        """Obtiene o crea un perfil de empresa con defaults según industria."""
        profile, created = cls.objects.get_or_create(fk_business=business)
        if created:
            profile._apply_industry_defaults(business.type, business.industry_sector)
            profile.save()
        return profile

    def _apply_industry_defaults(self, business_type, industry_sector):
        """Aplica configuración por defecto según el sector de la empresa."""
        sector_defaults = {
            'agro': {
                'demand_pattern': self.DemandPattern.SEASONAL,
                'distribution_preference': self.DistributionPreference.LOGNORMAL,
                'min_profit_margin_pct': 15.0,
                'inventory_days_target': 60,
                'peak_months': [6, 7, 8, 12],
            },
            'production': {
                'demand_pattern': self.DemandPattern.STABLE,
                'distribution_preference': self.DistributionPreference.NORMAL,
                'min_profit_margin_pct': 20.0,
                'inventory_days_target': 30,
            },
            'retail': {
                'demand_pattern': self.DemandPattern.SEASONAL,
                'distribution_preference': self.DistributionPreference.NORMAL,
                'min_profit_margin_pct': 12.0,
                'inventory_days_target': 15,
                'peak_months': [11, 12, 1],
            },
            'services': {
                'demand_pattern': self.DemandPattern.STABLE,
                'distribution_preference': self.DistributionPreference.GAMMA,
                'min_profit_margin_pct': 25.0,
                'inventory_days_target': 0,
                'primary_cost_driver': 'costo_personal',
                'primary_revenue_driver': 'tarifa_servicio',
            },
            'manufacturing': {
                'demand_pattern': self.DemandPattern.STABLE,
                'distribution_preference': self.DistributionPreference.NORMAL,
                'min_profit_margin_pct': 18.0,
                'inventory_days_target': 45,
            },
        }
        defaults = sector_defaults.get(industry_sector, {})
        for field, value in defaults.items():
            setattr(self, field, value)
