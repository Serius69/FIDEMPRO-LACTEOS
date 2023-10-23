from django.db import models
from django.contrib.auth.models import User

class Dashboard(models.Model):
    fk_user = models.OneToOneField(User, on_delete=models.CASCADE)
    widgets = models.JSONField()
    layout = models.JSONField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Dashboard for {self.user.username}"
