from django.db import models
class VariableCategory(models.Model):
    name = models.CharField(max_length = 70)
    unity = models.CharField(max_length = 20)
    quantity = models.IntegerField()
class Variable(models.Model):
    name = models.CharField(max_length = 70)
    unit = models.CharField(max_length = 20)
    quantity = models.IntegerField()
    STATUS_CHOICES = (
        (1, 'Endogen'),
        (2, 'Exogen'),
        (3, 'Estado'),
    )
    type = models.IntegerField(choices=STATUS_CHOICES, default=1)
    STATUS_CHOICES = (
        (1, 'Active'),
        (2, 'Inactive'),
        (3, 'Archived'),
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    fk_variablecategory = models.ForeignKey(VariableCategory, on_delete=models.CASCADE, related_name='target_edges')
class Node(models.Model):
    name = models.CharField(max_length=100)
    # Otros campos según tus necesidades

class Edge(models.Model):
    source = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='source_edges')
    target = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='target_edges')
    # Otros campos según tus necesidades

