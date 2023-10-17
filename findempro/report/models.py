from django.db import models

class Report(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)  # Add the is_active field

    def __str__(self):
        return self.title
