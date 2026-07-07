from django.db import models
from django.core.validators import MinLengthValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
from product.models import Product
from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Usar backend no interactivo
import json
import logging

logger = logging.getLogger(__name__)

class ChartManager(models.Manager):
    """Manager personalizado para Chart con queries optimizadas"""
    
    def active(self):
        """Retorna solo los charts activos"""
        return self.filter(is_active=True)
    
    def for_product(self, product):
        """Retorna charts para un producto específico"""
        return self.active().filter(fk_product=product)
    
    def latest_by_product(self, product_ids):
        """Obtiene el último chart de cada producto"""
        from django.db.models import Max
        
        latest_ids = self.active().filter(
            fk_product_id__in=product_ids
        ).values('fk_product_id').annotate(
            latest_id=Max('id')
        ).values_list('latest_id', flat=True)
        
        return self.filter(id__in=latest_ids).select_related('fk_product')

class Chart(models.Model):
    """Modelo mejorado para almacenar configuraciones de gráficos"""
    
    CHART_TYPES = [
        ('line', 'Línea'),
        ('bar', 'Barras'),
        ('pie', 'Circular'),
        ('donut', 'Dona'),
        ('area', 'Área'),
        ('scatter', 'Dispersión'),
        ('heatmap', 'Mapa de calor'),
        ('candlestick', 'Velas'),
    ]
    
    title = models.CharField(
        max_length=255,
        validators=[MinLengthValidator(3)],
        help_text="Título descriptivo del gráfico"
    )
    
    chart_type = models.CharField(
        max_length=50,
        choices=CHART_TYPES,
        default='line',
        help_text="Tipo de visualización del gráfico"
    )
    
    chart_data = models.JSONField(
        default=dict,
        help_text="Datos del gráfico en formato JSON"
    )
    
    fk_product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='charts',
        help_text="Producto asociado al gráfico"
    )
    
    widget_config = models.JSONField(
        default=dict,
        help_text="Configuración del widget (tamaño, colores, etc.)"
    )
    
    layout_config = models.JSONField(
        default=dict,
        help_text="Configuración de diseño del gráfico"
    )
    
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name='Activo',
        help_text='Indica si el gráfico está activo'
    )
    
    date_created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    
    chart_image = models.ImageField(
        upload_to='chart_images/%Y/%m/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['png', 'jpg', 'jpeg'])],
        help_text="Imagen renderizada del gráfico"
    )
    
    # Campos adicionales para mejorar el rendimiento
    cache_key = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Clave de caché para el gráfico"
    )
    
    render_priority = models.IntegerField(
        default=0,
        help_text="Prioridad de renderizado (mayor = más prioritario)"
    )
    
    objects = ChartManager()
    
    class Meta:
        ordering = ['-render_priority', '-date_created']
        indexes = [
            models.Index(fields=['fk_product', 'is_active']),
            models.Index(fields=['chart_type', 'is_active']),
            models.Index(fields=['-date_created']),
        ]
        verbose_name = 'Gráfico'
        verbose_name_plural = 'Gráficos'
    
    def __str__(self):
        return f"{self.title} - {self.get_chart_type_display()}"
    
    def clean(self):
        """Validación del modelo"""
        super().clean()
        
        # Validar estructura de chart_data
        if self.chart_data:
            required_fields = self._get_required_fields_by_type()
            missing_fields = required_fields - set(self.chart_data.keys())
            if missing_fields:
                raise ValidationError({
                    'chart_data': f'Campos requeridos faltantes: {", ".join(missing_fields)}'
                })
    
    def _get_required_fields_by_type(self):
        """Retorna campos requeridos según el tipo de gráfico"""
        base_fields = {'labels', 'datasets'}
        
        type_specific_fields = {
            'line': {'x_label', 'y_label'},
            'bar': {'x_label', 'y_label'},
            'pie': {'values'},
            'donut': {'values'},
            'candlestick': {'ohlc_data'},
        }
        
        return base_fields.union(type_specific_fields.get(self.chart_type, set()))
    
    def generate_chart_image(self):
        """Genera y guarda la imagen del gráfico de forma optimizada"""
        try:
            plt.figure(figsize=(10, 6))
            
            # Aplicar configuración de diseño
            if self.layout_config:
                self._apply_layout_config()
            
            # Generar el gráfico según el tipo
            if self.chart_type == 'line':
                self._generate_line_chart()
            elif self.chart_type == 'bar':
                self._generate_bar_chart()
            elif self.chart_type in ['pie', 'donut']:
                self._generate_pie_chart()
            else:
                logger.warning(f"Tipo de gráfico no soportado: {self.chart_type}")
                return False
            
            # Configurar el gráfico
            plt.title(self.title, fontsize=16, fontweight='bold')
            plt.tight_layout()
            
            # Guardar la imagen
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            
            # Guardar en el campo ImageField
            from django.core.files.base import ContentFile
            self.chart_image.save(
                f"{self.pk}_{self.chart_type}_chart.png",
                ContentFile(buffer.getvalue()),
                save=False
            )
            
            plt.close()
            self.save(update_fields=['chart_image'])
            
            return True
            
        except Exception as e:
            logger.error(f"Error generando imagen del gráfico {self.pk}: {e}")
            plt.close()
            return False
    
    def _apply_layout_config(self):
        """Aplica la configuración de diseño al gráfico"""
        config = self.layout_config
        
        if 'style' in config:
            plt.style.use(config['style'])
        
        if 'figsize' in config:
            plt.gcf().set_size_inches(config['figsize'])
        
        if 'colors' in config:
            plt.rcParams['axes.prop_cycle'] = plt.cycler(color=config['colors'])
    
    def _generate_line_chart(self):
        """Genera un gráfico de líneas"""
        data = self.chart_data
        
        for dataset in data.get('datasets', []):
            plt.plot(
                data['labels'],
                dataset['data'],
                label=dataset.get('label', ''),
                linewidth=2,
                marker='o'
            )
        
        plt.xlabel(data.get('x_label', 'X'))
        plt.ylabel(data.get('y_label', 'Y'))
        plt.legend()
        plt.grid(True, alpha=0.3)
    
    def _generate_bar_chart(self):
        """Genera un gráfico de barras"""
        data = self.chart_data
        labels = data['labels']
        
        x = range(len(labels))
        width = 0.8 / len(data.get('datasets', []))
        
        for i, dataset in enumerate(data.get('datasets', [])):
            offset = (i - len(data['datasets'])/2) * width + width/2
            plt.bar(
                [xi + offset for xi in x],
                dataset['data'],
                width,
                label=dataset.get('label', '')
            )
        
        plt.xlabel(data.get('x_label', 'X'))
        plt.ylabel(data.get('y_label', 'Y'))
        plt.xticks(x, labels)
        plt.legend()
    
    def _generate_pie_chart(self):
        """Genera un gráfico circular o de dona"""
        data = self.chart_data
        
        wedgeprops = {}
        if self.chart_type == 'donut':
            wedgeprops = {'width': 0.5}
        
        plt.pie(
            data.get('values', []),
            labels=data.get('labels', []),
            autopct='%1.1f%%',
            startangle=90,
            wedgeprops=wedgeprops
        )
        
        plt.axis('equal')
    
    def get_photo_url(self) -> str:
        """Retorna la URL de la imagen del gráfico"""
        if self.chart_image and hasattr(self.chart_image, 'url'):
            return self.chart_image.url
        return "/static/images/charts/default-chart.png"
    
    def get_cache_key(self) -> str:
        """Genera una clave de caché única para el gráfico"""
        import hashlib
        
        data_str = json.dumps(self.chart_data, sort_keys=True)
        hash_object = hashlib.md5(data_str.encode())
        
        return f"chart_{self.pk}_{self.chart_type}_{hash_object.hexdigest()}"
    
    def invalidate_cache(self):
        """Invalida la caché del gráfico"""
        from django.core.cache import cache
        
        if self.cache_key:
            cache.delete(self.cache_key)
    
    def save(self, *args, **kwargs):
        """Override save para generar cache_key y otras operaciones"""
        # Generar cache_key si no existe
        if not self.cache_key:
            self.cache_key = self.get_cache_key()
        
        # Invalidar caché si el gráfico ya existe
        if self.pk:
            self.invalidate_cache()
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Override delete para limpiar recursos"""
        # Eliminar imagen si existe
        if self.chart_image:
            self.chart_image.delete(save=False)
        
        # Invalidar caché
        self.invalidate_cache()
        
        super().delete(*args, **kwargs)


class ChartTemplate(models.Model):
    """Plantillas predefinidas para gráficos"""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nombre de la plantilla"
    )
    
    description = models.TextField(
        blank=True,
        help_text="Descripción de la plantilla"
    )
    
    chart_type = models.CharField(
        max_length=50,
        choices=Chart.CHART_TYPES,
        help_text="Tipo de gráfico de la plantilla"
    )
    
    default_config = models.JSONField(
        default=dict,
        help_text="Configuración por defecto de la plantilla"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Indica si la plantilla está activa"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Plantilla de Gráfico'
        verbose_name_plural = 'Plantillas de Gráficos'
    
    def __str__(self):
        return f"{self.name} ({self.get_chart_type_display()})"
    
    def create_chart_from_template(self, product, title, data):
        """Crea un nuevo gráfico basado en esta plantilla"""
        config = self.default_config.copy()
        config['chart_data'] = data
        
        return Chart.objects.create(
            title=title,
            chart_type=self.chart_type,
            chart_data=data,
            fk_product=product,
            widget_config=config.get('widget_config', {}),
            layout_config=config.get('layout_config', {})
        )