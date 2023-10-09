from django.db import models
from django.urls import reverse  # Import reverse from django.urls
from django.utils import timezone
from business.models import Business
from multiselectfield import MultiSelectField

class ProductCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, default='Category Name')  # Fix the default value to a string
    description = models.TextField(blank=True, null=True, default='No description available.')

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    description = models.TextField()
    STATUS_CHOICES = (
        (1, 'Active'),
        (2, 'Inactive'),
        (3, 'Archived'),
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)  # Automatically updated on save
    image = models.ImageField(upload_to='images/job/application', blank=True, null=True)
    # fk_business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='fk_business')
    fk_category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name='fk_category', default=1)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        # Define the absolute URL for the product detail page
        return reverse('product.overview', args=[str(self.id)])

    def get_photo_url(self):
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        else:
            return "/static/images/users/user-dummy-img.jpg"
