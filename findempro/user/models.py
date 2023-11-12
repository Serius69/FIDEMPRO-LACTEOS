from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, default='images/users/user-dummy-img.webp')
    # Agrega otros campos de perfil que desees

    def is_profile_complete(self):
        # Define tu lógica para determinar si el perfil está completo
        return all(
                field_value is not None and field_value != ''
                for field_value in [getattr(self, field.name) for field in self._meta.get_fields() if field.name != 'id' and field.name != 'user']
            )

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()
