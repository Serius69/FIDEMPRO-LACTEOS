from django.db import models
from django.urls import reverse  # Import reverse from django.urls

class Product(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    description = models.TextField()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        # Define the absolute URL for the product detail page
        return reverse('product-detail', args=[str(self.id)])
