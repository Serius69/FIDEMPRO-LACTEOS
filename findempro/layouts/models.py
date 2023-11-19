from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from user.models import User
from .data_instructions import data_instructions
class Instructions(models.Model):
    instruction = models.CharField(max_length=70)
    content = models.TextField(help_text='Detailed instructions content')
    type = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True, verbose_name='Active', help_text='Whether the finance is active or not')
    date_created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name='Date Created', help_text='The date the finance was created')
    last_updated = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name='Date Created', help_text='The date the finance was created')

    def __str__(self):
        return f"Instructions: {self.id}"

    class Meta:
        verbose_name_plural = 'Instructions'
    @receiver(post_save, sender=User)
    def create_variables(sender, instance, created, **kwargs):
        if created:
            for data in data_instructions:
                Instructions.objects.create(
                    instruction=data['instruction'],
                    content=data['content'],
                    is_active=True
                )
    @receiver(post_save, sender=User)
    def save_variables(sender, instance, **kwargs):
        if instance.is_active == 1:
            instance.question_set.all().update(is_active=instance.is_active)