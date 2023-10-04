from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User  # Import User model
from product.models import Product  # Import the Product model from the simulate app

class Company(models.Model):
    id = models.CharField(max_length=10, primary_key=True)
    image_src = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    date_created = models.DateTimeField(default=timezone.now)
    leads_score = models.IntegerField()
    phone = models.CharField(max_length=20)
    location = models.CharField(max_length=255)
    last_updated = models.DateTimeField(auto_now=True)

    # Add foreign keys for User and Product
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, blank=True)  # Many-to-many relationship with Product

    tags = models.JSONField()
    def __str__(self):
            return self.name
    
class CompanieProduct(models.Model):
    companie = models.ForeignKey(Company, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.companie.name} - {self.product.name}"