from django.db import models
from django.urls import reverse  # Import reverse from django.urls
from django.utils import timezone  # Import timezone for date fields
class Product(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    description = models.TextField()
    STATUS_CHOICES = (
        (1, 'Active'),
        (2, 'Inactive'),
        (3, 'Archived'),
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)  # Automatically updated on save


    def __str__(self):
        return self.name

    def get_absolute_url(self):
        # Define the absolute URL for the product detail page
        return reverse('product-detail', args=[str(self.id)])
