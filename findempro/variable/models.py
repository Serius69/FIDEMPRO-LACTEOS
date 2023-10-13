from django.db import models
from django.utils import timezone
from django.urls import reverse  # Import reverse from django.urls
from business.models import Business
from product.models import Product  # Import the Product model
from multiselectfield import MultiSelectField

class Variable(models.Model):
    name = models.CharField(max_length=70)
    initials = models.CharField(max_length=7, default="var")
    type = models.IntegerField(default=1)
    unit = models.CharField(max_length=20)
    description = models.TextField(default="Descripción predeterminada")
    status = models.IntegerField(default=1)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    image_src = models.ImageField(upload_to='images/variables', blank=True, null=True)
    fk_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='fk_product')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        # Define the absolute URL for the variable detail page
        return reverse('variable-detail', args=[str(self.id)])

    def get_photo_url(self):
        if self.image_src and hasattr(self.image_src, 'url'):
            return self.image_src.url
        else:
            return "/images/variable/variable-dummy-img.jpg"
