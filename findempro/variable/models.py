from django.db import models
from django.urls import reverse 
from django.utils import timezone
from product.models import Product
# from fontawesomepicker.fields import FontAwesomeIconField
class VariableCategory(models.Model):
    category = models.CharField(max_length = 70, unique=True, default=1)
    description = models.CharField(max_length = 20, default='No description available.')
    def __str__(self):
        return self.name
class Variable(models.Model):
    name = models.CharField(max_length = 70)
    unit = models.CharField(max_length = 20)
    quantity = models.IntegerField()
    STATUS_CHOICES2 = (
        (1, 'Endogen'),
        (2, 'Exogen'),
        (3, 'Estado'),
    )
    type = models.IntegerField(choices=STATUS_CHOICES2, default=1)
    STATUS_CHOICES = (
        (1, 'Active'),
        (2, 'Inactive'),
        (3, 'Archived'),
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    # icon = FontAwesomeIconField(blank=True, null=True)

    fk_category = models.ForeignKey(VariableCategory, on_delete=models.CASCADE, related_name='fk_category', default=1)
    fk_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='fk_product', default=1)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        # Define the absolute URL for the product detail page
        return reverse('variable-overview', args=[str(self.id)])

    def get_photo_url(self):
        if self.icon and hasattr(self.icon, 'url'):
            return self.icon.url
        else:
            return "/static/images/users/user-dummy-img.jpg"
class Node(models.Model):
    name = models.CharField(max_length=100)
    # Otros campos según tus necesidades

class Edge(models.Model):
    source = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='source_edges')
    target = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='target_edges')
    # Otros campos según tus necesidades

