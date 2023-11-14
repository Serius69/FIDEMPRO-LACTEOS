from django.db import models
from product.models import Product
from django.utils import timezone
class Report(models.Model):
    title = models.CharField(max_length=100)
    content = models.JSONField()
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    fk_product = models.ForeignKey(
            Product, 
            on_delete=models.CASCADE, 
            related_name='fk_product_report', null=True)
    def __str__(self):
        return self.title
