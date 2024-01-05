from django.db import models
from product.models import Product
from django.db.models.signals import post_save
from django.dispatch import receiver
from product.models import Product
from django.db import models
from product.models import Product
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image
from io import BytesIO
import base64
from django.core.files.base import ContentFile
import matplotlib.pyplot as plt
class Chart(models.Model):
    title = models.CharField(max_length=255, default='Chart', help_text="The title of the chart.")
    chart_type = models.CharField(max_length=50, default='line', help_text="The type of chart to use.")
    chart_data = models.JSONField(default=list, help_text="Structured JSON data for chart configuration.")
    fk_product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='fk_product_charts', 
        default=1,
        help_text="The product associated with the chart."
    )
    widget_config = models.JSONField(
        help_text="Structured JSON data for widget configuration.",
        default=dict 
    )
    layout_config = models.JSONField(
        help_text="Structured JSON data for layout configuration.",
        default=dict 
    )
    is_active = models.BooleanField(default=True, verbose_name='Active', help_text='Whether the chart is active or not')
    date_created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name='Date Created', help_text='The date the chart was created')
    last_updated = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name='Last Updated', help_text='The date the chart was last updated')
    chart_image = models.ImageField(upload_to='chart_images/', blank=True, null=True, help_text="Chart image")

    def save_chart_image(self, image_data):
        try:
            # Generar la imagen con Matplotlib
            plt.legend()
            plt.xlabel(self.chart_data['x_label'])
            plt.ylabel(self.chart_data['y_label'])
            plt.title(self.title)
            
            with BytesIO() as buffer:
                plt.savefig(buffer, format='png')
                buffer.seek(0)

                # Convertir a formato de imagen para guardar en ImageField
                image = Image.open(buffer)
                image_format = 'PNG'  # Especificar el formato de la imagen

                # Guardar la imagen en el campo ImageField
                self.chart_image.save(f"{self.title}_chart.png", ContentFile(buffer.getvalue()), save=False)

            
            # Limpiar el buffer y cerrar el gráfico de Matplotlib
            plt.close()

            # Llamar al método save del modelo para guardar otros campos si es necesario
            super().save()
        except Exception as e:
            print(f"Error saving chart image: {e}")
            
    def get_photo_url(self) -> str:
        if self.chart_image and hasattr(self.chart_image, 'url'):
            return self.chart_image.url
        else:
            return "/static/images/business/business-dummy-img.webp"