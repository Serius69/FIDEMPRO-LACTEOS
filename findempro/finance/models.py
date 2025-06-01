from typing import Optional
from django.db import models
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

from simulate.models import Simulation
from product.models import Product
from business.models import Business
from .finance_data import recommendation_data


class FinancialDecision(models.Model):
    """
    Modelo para gestionar decisiones financieras empresariales.
    
    Este modelo representa las decisiones financieras tomadas por una empresa,
    incluyendo información sobre montos, categorías, prioridades y estados.
    """
    
    CATEGORY_CHOICES = [
        ('inversion', 'Inversión'),
        ('gasto', 'Gasto'),
        ('ingreso', 'Ingreso'),
        ('financiamiento', 'Financiamiento'),
        ('ahorro', 'Ahorro'),
        ('otro', 'Otro'),
    ]
    
    PRIORITY_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    ]
    
    STATUS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
        ('implementada', 'Implementada'),
        ('cancelada', 'Cancelada'),
    ]
    
    # Campos principales
    name = models.CharField(
        max_length=255,
        verbose_name='Nombre de la Decisión',
        help_text='Nombre descriptivo de la decisión financiera'
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Descripción',
        help_text='Descripción detallada de la decisión'
    )
    
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Monto',
        help_text='Monto asociado a la decisión en la moneda local'
    )
    
    # Categorización
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='otro',
        verbose_name='Categoría',
        help_text='Categoría de la decisión financiera'
    )
    
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='media',
        verbose_name='Prioridad',
        help_text='Nivel de prioridad de la decisión'
    )
    
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='pendiente',
        verbose_name='Estado',
        help_text='Estado actual de la decisión'
    )
    
    # Fechas
    decision_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Fecha de Decisión',
        help_text='Fecha en que se tomó la decisión'
    )
    
    implementation_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Fecha de Implementación',
        help_text='Fecha prevista o real de implementación'
    )
    
    # Relaciones
    fk_business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='financial_decisions',
        verbose_name='Empresa',
        help_text='Empresa asociada a la decisión'
    )
    
    # Campos adicionales
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Notas Adicionales',
        help_text='Observaciones y notas relevantes'
    )
    
    expected_impact = models.TextField(
        blank=True,
        null=True,
        verbose_name='Impacto Esperado',
        help_text='Descripción del impacto esperado de la decisión'
    )
    
    risk_assessment = models.TextField(
        blank=True,
        null=True,
        verbose_name='Evaluación de Riesgo',
        help_text='Análisis de riesgos asociados'
    )
    
    # Control y auditoría
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Indica si la decisión está activa'
    )
    
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_financial_decisions',
        verbose_name='Creado por',
        help_text='Usuario que creó la decisión'
    )
    
    approved_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_financial_decisions',
        verbose_name='Aprobado por',
        help_text='Usuario que aprobó la decisión'
    )
    
    # Timestamps
    date_created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )
    
    class Meta:
        verbose_name = 'Decisión Financiera'
        verbose_name_plural = 'Decisiones Financieras'
        ordering = ['-date_created']
        indexes = [
            models.Index(fields=['fk_business', 'category']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['decision_date']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.get_category_display()}"
    
    @property
    def formatted_amount(self):
        """Retorna el monto formateado como string"""
        if self.amount:
            return f"${self.amount:,.2f}"
        return "No especificado"
    
    @property
    def days_since_created(self):
        """Retorna los días transcurridos desde la creación"""
        return (timezone.now().date() - self.date_created.date()).days
    
    @property
    def is_overdue(self):
        """Determina si la decisión está vencida"""
        if self.implementation_date and self.status != 'implementada':
            return timezone.now().date() > self.implementation_date
        return False
    
    @property
    def priority_color(self):
        """Retorna el color asociado a la prioridad"""
        colors = {
            'baja': 'secondary',
            'media': 'primary',
            'alta': 'warning',
            'critica': 'danger'
        }
        return colors.get(self.priority, 'secondary')
    
    @property
    def status_color(self):
        """Retorna el color asociado al estado"""
        colors = {
            'pendiente': 'warning',
            'aprobada': 'success',
            'rechazada': 'danger',
            'implementada': 'primary',
            'cancelada': 'secondary'
        }
        return colors.get(self.status, 'secondary')
    
    def can_be_edited(self):
        """Determina si la decisión puede ser editada"""
        return self.status in ['pendiente', 'aprobada'] and self.is_active
    
    def can_be_approved(self):
        """Determina si la decisión puede ser aprobada"""
        return self.status == 'pendiente' and self.is_active
    
    def approve(self, user=None):
        """Aprueba la decisión"""
        if self.can_be_approved():
            self.status = 'aprobada'
            self.approved_by = user
            self.save()
            return True
        return False
    
    def reject(self, user=None):
        """Rechaza la decisión"""
        if self.status == 'pendiente':
            self.status = 'rechazada'
            self.approved_by = user
            self.save()
            return True
        return False
    
    def implement(self):
        """Marca la decisión como implementada"""
        if self.status == 'aprobada':
            self.status = 'implementada'
            self.implementation_date = timezone.now().date()
            self.save()
            return True
        return False
    
    def get_absolute_url(self):
        """Retorna la URL absoluta de la decisión"""
        from django.urls import reverse
        return reverse('finance:finance.details', kwargs={'pk': self.pk})


class FinanceRecommendation(models.Model):
    """
    FinanceRecommendation Model

    This model represents a finance recommendation associated with a business. It includes details such as the name, 
    variable name, threshold value, recommendation text, and its association with a business. The model also tracks 
    whether the recommendation is active and includes timestamps for creation and updates.

    Attributes:
        name (CharField): The name of the finance recommendation (optional).
        variable_name (CharField): The variable name of the finance recommendation (optional).
        threshold_value (DecimalField): The threshold value associated with the finance recommendation (optional).
        recommendation (TextField): The recommendation text (optional).
        description (TextField): Descripción adicional de la recomendación.
        fk_business (ForeignKey): A foreign key linking the recommendation to a Business instance.
        is_active (BooleanField): Indicates whether the recommendation is active (default is True).
        date_created (DateTimeField): The timestamp when the recommendation was created (auto-generated).
        last_updated (DateTimeField): The timestamp when the recommendation was last updated (auto-generated).

    Methods:
        __str__(): Returns the string representation of the finance recommendation, which is the name.
        
    Signals:
        create_finance_recommendation (post_save): Triggered when a Business instance is created. Automatically 
            creates finance recommendations based on predefined data.
        save_finance_recommendation (post_save): Triggered when a Business instance is saved. Updates the 
            `is_active` status of associated finance recommendations based on the business's status.
    """
    name = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        verbose_name='Nombre', 
        help_text='El nombre de la recomendación financiera'
    )
    
    variable_name = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        verbose_name='Nombre de Variable', 
        help_text='El nombre de variable de la recomendación financiera'
    )
    
    threshold_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True, 
        verbose_name='Valor Umbral', 
        help_text='El valor umbral de la recomendación financiera'
    )
    
    recommendation = models.TextField(
        blank=True, 
        null=True, 
        verbose_name='Recomendación', 
        help_text='El texto de la recomendación financiera'
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Descripción',
        help_text='Descripción adicional de la recomendación'
    )
    
    fk_business = models.ForeignKey(
        Business, 
        on_delete=models.CASCADE, 
        related_name='fk_business_finance_recommendation', 
        help_text='La empresa asociada con la recomendación financiera',
        default=1
    )
    
    is_active = models.BooleanField(
        default=True, 
        verbose_name='Activo', 
        help_text='Si la recomendación financiera está activa o no'
    )
    
    date_created = models.DateTimeField(
        auto_now_add=True, 
        blank=True, 
        null=True, 
        verbose_name='Fecha de Creación', 
        help_text='La fecha en que se creó la recomendación'
    )
    
    last_updated = models.DateTimeField(
        auto_now=True, 
        blank=True, 
        null=True, 
        verbose_name='Última Actualización', 
        help_text='La fecha en que se actualizó la recomendación por última vez'
    )
    
    class Meta:
        verbose_name = 'Recomendación Financiera'
        verbose_name_plural = 'Recomendaciones Financieras'
        ordering = ['-date_created']
    
    def __str__(self):
        return self.name or f"Recomendación {self.id}"
    
    @receiver(post_save, sender=Business)
    def create_finance_recommendation(sender, instance, created, **kwargs):
        """Crea recomendaciones financieras automáticamente cuando se crea un negocio"""
        if created:
            business = Business.objects.get(pk=instance.pk)
            for data in recommendation_data:
                FinanceRecommendation.objects.create(
                    name=data['name'],
                    recommendation=data['recommendation'],
                    threshold_value=data['threshold_value'],
                    variable_name=data['variable_name'],
                    fk_business_id=business.id,
                    is_active=True
                )
        print('Se crearon las recomendaciones financieras')
    
    @receiver(post_save, sender=Business)
    def save_finance_recommendation(sender, instance, **kwargs):
        """Actualiza el estado de las recomendaciones cuando cambia el estado del negocio"""
        for finance_recommendation in instance.fk_business_finance_recommendation.all():
            finance_recommendation.is_active = instance.is_active
            finance_recommendation.save()


class FinanceRecommendationSimulation(models.Model):
    """
    Modelo para almacenar simulaciones de recomendaciones financieras
    """
    data = models.FloatField(
        verbose_name='Datos',
        help_text='Datos numéricos de la simulación'
    )
    fk_simulation = models.ForeignKey(
        Simulation,
        on_delete=models.CASCADE,
        related_name='finance_recommendation_simulations',
        verbose_name='Simulación',
        help_text='Simulación asociada a la recomendación financiera'
    )