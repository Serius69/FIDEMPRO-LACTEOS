from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from social_django.models import UserSocialAuth
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    image_src = models.ImageField(upload_to='images/user', blank=True, null=True)
    state = models.CharField(max_length=100, blank=True)  # Add max_length here
    country = models.CharField(max_length=100, blank=True)  # Add max_length here
    def get_photo_url(self) -> str:
        if self.image_src and hasattr(self.image_src, 'url'):
            return self.image_src.url
        else:
            return "/static/images/users/user-dummy-img.webp"
    def is_profile_complete(self):
        return all(
                field_value is not None and field_value != ''
                for field_value in [getattr(self, field.name) for field in self._meta.get_fields() if field.name != 'id' and field.name != 'user']
            )

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            UserProfile.objects.create(
                user=instance)
    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.userprofile.save()
    @receiver(post_save, sender=UserSocialAuth)
    def save_image_src(sender, instance, **kwargs):
        if instance.provider == 'google-oauth2':
            user_profile, created = UserProfile.objects.get_or_create(user=instance.user)
            user_profile.image_src = instance.extra_data.get('picture', '')
            user_profile.save()
            
class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, null=True)