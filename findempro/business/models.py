from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Business(models.Model):
    name = models.CharField(max_length=255, verbose_name='Name', help_text='The name of the business')
    type = models.IntegerField(default=1, verbose_name='Type', help_text='The type of the business')
    location = models.CharField(max_length=255, verbose_name='Location', help_text='The location of the business')
    image_src = models.ImageField(upload_to='images/business', null=True, blank=True, verbose_name='Image', help_text='The image of the business')
    description = models.TextField(verbose_name='Description', help_text='The description of the business')
    fk_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='fk_user_business', 
        verbose_name='User', 
        help_text='The user associated with the business', 
        default=1)
    is_active = models.BooleanField(default=True, verbose_name='Active', help_text='Whether the business is active or not')
    date_created = models.DateTimeField(default=timezone.now, verbose_name='Date Created', help_text='The date the business was created')
    last_updated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    def get_photo_url(self) -> str:
        if self.image_src and hasattr(self.image_src, 'url'):
            return self.image_src.url
        else:
            return "/static/images/business/business-dummy-img.webp"
    @receiver(post_save, sender=User)
    def create_business(sender, instance, created, **kwargs):
        if created:
            user = User.objects.get(pk=instance.pk)
            Business.objects.create(
                name="Pyme Lactea",
                type= 1,  
                location="La Paz",
                fk_user_id=user.id,
            )

    @receiver(post_save, sender=User)
    def save_business(sender, instance, **kwargs):
        for business in instance.fk_user_business.all():
            business.is_active = instance.is_active
            business.save()
            
    # TYPE_CHOICES = [
    #     (1, 'Dairy'),
    #     (2, 'Agriculture '),
    #     (3, 'Consumer Goods'),
    # ] 