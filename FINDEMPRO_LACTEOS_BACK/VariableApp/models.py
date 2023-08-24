from django.db import models

class Variable(models.Model):
    name = models.CharField(max_length = 70)
    unity = models.CharField(max_length = 20)
    quantity = models.IntegerField()
class Node(models.Model):
    name = models.CharField(max_length=100)
    # Otros campos según tus necesidades

class Edge(models.Model):
    source = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='source_edges')
    target = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='target_edges')
    # Otros campos según tus necesidades
