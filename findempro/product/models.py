from django.db import models
from django.urls import reverse
from django.utils import timezone
from business.models import Business

# Define the ProductCategory model
class ProductCategory(models.Model):
    category = models.CharField(max_length=100, unique=True, default='Category Name')

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    is_active = models.BooleanField(default=True)  # Add the is_active field
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    image_src = models.ImageField(upload_to='images/product', blank=True, null=True)
    fk_business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='fk_business',default=1)
    fk_category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name='products', default=1)

    def __str__(self):
        return self.name

    def get_photo_url(self):
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        else:
            return "/static/images/users/user-dummy-img.jpg"
