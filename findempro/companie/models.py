from django.db import models

# Create your models here.
class Companie(models.Model):
    id = models.CharField(max_length=10, primary_key=True)
    image_src = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)
    date = models.DateField()
    leads_score = models.IntegerField()
    phone = models.CharField(max_length=20)
    location = models.CharField(max_length=255)
    tags = models.JSONField()
    def __str__(self):
            return self.name