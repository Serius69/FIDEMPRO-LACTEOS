from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # ... Other fields ...

    # Use unique related_name for groups and user_permissions
    custom_groups = models.ManyToManyField(
        'auth.Group', related_name='user_custom_groups'
    )
    custom_user_permissions = models.ManyToManyField(
        'auth.Permission', related_name='user_custom_user_permissions'
    )

    # ... Other fields ...