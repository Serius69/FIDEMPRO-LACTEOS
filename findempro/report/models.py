from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.core.exceptions import ValidationError
import json

class ReportManager(models.Manager):
    """Manager personalizado para el modelo Report"""
    
    def active(self):
        """Obtiene solo reportes activos"""
        return self.filter(is_active=True)
    
    def by_product(self, product):
        """Filtra reportes por producto"""
        return self.filter(fk_product=product)
    
    def recent(self, days=30):
        """Obtiene reportes recientes"""
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.filter(date_created__gte=cutoff_date)

class Report(models.Model):
    """Modelo para reportes de simulación y análisis"""
    
    # Tipos de reporte
    REPORT_TYPES = [
        ('simulation', 'Simulación'),
        ('analysis', 'Análisis'),
        ('custom', 'Personalizado'),
        ('comparison', 'Comparativo'),
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name='Título',
        help_text='Título descriptivo del reporte'
    )
    
    content = models.JSONField(
        verbose_name='Contenido',
        help_text='Contenido del reporte en formato JSON',
        default=dict
    )
    
    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPES,
        default='simulation',
        verbose_name='Tipo de Reporte'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Indica si el reporte está activo'
    )
    
    date_created = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de Creación'
    )
    
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )
    
    fk_product = models.ForeignKey(
        'product.Product',
        on_delete=models.SET_NULL,
        related_name='reports',
        null=True,
        blank=True,
        verbose_name='Producto Asociado'
    )
    
    # Campos adicionales para metadatos
    tags = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Etiquetas',
        help_text='Etiquetas separadas por comas'
    )
    
    summary = models.TextField(
        blank=True,
        verbose_name='Resumen',
        help_text='Resumen ejecutivo del reporte'
    )
    
    version = models.CharField(
        max_length=10,
        default='1.0',
        verbose_name='Versión'
    )
    
    # Manager personalizado
    objects = ReportManager()
    
    class Meta:
        db_table = 'report_report'
        verbose_name = 'Reporte'
        verbose_name_plural = 'Reportes'
        ordering = ['-date_created']
        indexes = [
            models.Index(fields=['-date_created']),
            models.Index(fields=['is_active']),
            models.Index(fields=['report_type']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.get_report_type_display()}"
    
    def get_absolute_url(self):
        """URL absoluta del reporte"""
        return reverse('report:report.detail', kwargs={'pk': self.pk})
    
    def get_update_url(self):
        """URL para editar el reporte"""
        return reverse('report:report.update', kwargs={'pk': self.pk})
    
    def get_delete_url(self):
        """URL para eliminar el reporte"""
        return reverse('report:report.delete', kwargs={'pk': self.pk})
    
    def get_pdf_url(self):
        """URL para generar PDF"""
        return reverse('report:generar_reporte_pdf', kwargs={'report_id': self.pk})
    
    def clean(self):
        """Validaciones del modelo"""
        super().clean()
        
        # Validar que el contenido sea JSON válido
        if isinstance(self.content, str):
            try:
                json.loads(self.content)
            except json.JSONDecodeError:
                raise ValidationError({'content': 'El contenido debe ser JSON válido'})
        
        # Validar título único por producto (si tiene producto)
        if self.fk_product:
            existing = Report.objects.filter(
                title=self.title,
                fk_product=self.fk_product
            ).exclude(pk=self.pk)
            
            if existing.exists():
                raise ValidationError({
                    'title': f'Ya existe un reporte con este título para el producto {self.fk_product.name}'
                })
    
    def save(self, *args, **kwargs):
        """Override del método save para validaciones adicionales"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def status_display(self):
        """Muestra el estado del reporte de forma amigable"""
        return 'Activo' if self.is_active else 'Inactivo'
    
    @property
    def status_class(self):
        """Clase CSS para el estado"""
        return 'badge bg-success' if self.is_active else 'badge bg-danger'
    
    @property
    def product_name(self):
        """Nombre del producto asociado"""
        return self.fk_product.name if self.fk_product else 'Sin producto'
    
    @property
    def content_summary(self):
        """Resumen del contenido"""
        if not isinstance(self.content, dict):
            return "Contenido no válido"
        
        keys = list(self.content.keys())
        if len(keys) > 3:
            return f"Contiene: {', '.join(keys[:3])}..."
        return f"Contiene: {', '.join(keys)}"
    
    @property
    def age_days(self):
        """Días desde la creación"""
        return (timezone.now() - self.date_created).days
    
    @property
    def is_recent(self):
        """Indica si el reporte es reciente (menos de 7 días)"""
        return self.age_days <= 7
    
    def get_tag_list(self):
        """Obtiene las etiquetas como lista"""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
    
    def add_tag(self, tag):
        """Agrega una etiqueta"""
        current_tags = self.get_tag_list()
        if tag not in current_tags:
            current_tags.append(tag)
            self.tags = ', '.join(current_tags)
    
    def remove_tag(self, tag):
        """Remueve una etiqueta"""
        current_tags = self.get_tag_list()
        if tag in current_tags:
            current_tags.remove(tag)
            self.tags = ', '.join(current_tags)
    
    def get_simulation_results(self):
        """Obtiene resultados de simulación del contenido"""
        if isinstance(self.content, dict):
            return self.content.get('resultados_simulacion', {})
        return {}
    
    def get_chart_data(self):
        """Obtiene datos de gráficas del contenido"""
        if isinstance(self.content, dict):
            return self.content.get('graficas', {})
        return {}
    
    def duplicate(self, new_title=None):
        """Crea una copia del reporte"""
        new_title = new_title or f"Copia de {self.title}"
        
        new_report = Report.objects.create(
            title=new_title,
            content=self.content.copy() if isinstance(self.content, dict) else self.content,
            report_type=self.report_type,
            fk_product=self.fk_product,
            tags=self.tags,
            summary=self.summary,
            version='1.0'  # Nueva versión
        )
        
        return new_report
    
    @classmethod
    def create_from_simulation(cls, product, simulation_params, title=None):
        """Método de clase para crear reporte desde simulación"""
        from .views import process_simulation_data
        
        title = title or f"Simulación {product.name} - {timezone.now().strftime('%Y-%m-%d')}"
        content = process_simulation_data(product, simulation_params)
        
        return cls.objects.create(
            title=title,
            content=content,
            report_type='simulation',
            fk_product=product
        )
    
    def get_metrics_summary(self):
        """Obtiene resumen de métricas principales"""
        results = self.get_simulation_results()
        if not results:
            return {}
        
        return {
            'Utilidad Neta': results.get('utilidad_neta', 'N/A'),
            'Flujo de Caja': results.get('flujo_caja', 'N/A'),
            'ROI': f"{results.get('roi', 0):.2f}%" if results.get('roi') else 'N/A',
            'Punto de Equilibrio': results.get('punto_equilibrio', 'N/A')
        }