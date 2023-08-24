from django.db import models
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import AbstractUser
from django.db import models

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
        
class User(AbstractUser):
    bio = models.TextField(blank=True)
    profile_pic = models.ImageField(blank=True)

    def __str__(self):
        return self.username
    


# Create your models here.
