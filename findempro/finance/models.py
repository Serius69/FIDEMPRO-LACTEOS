from django.db import models

# Create your models here.
class Supporter(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class Expense(models.Model):
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)  
    date = models.DateField()

    def __str__(self):
        return self.title