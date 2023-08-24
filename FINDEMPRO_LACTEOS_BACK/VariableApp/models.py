from django.db import models

class Variable(models.Model):
    name = models.CharField(max_length = 70)
    unity = models.CharField(max_length = 20)
    quantity = models.IntegerField()
