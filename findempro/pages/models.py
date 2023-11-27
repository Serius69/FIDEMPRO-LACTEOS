from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from user.models import User
from .data_instructions import data_instructions
class Instructions(models.Model):
    instruction = models.TextField(help_text='Instruction', blank=True, null=True)
    content = models.TextField(help_text='Detailed instructions content', blank=True, null=True)
    type = models.IntegerField(default=1, help_text='The type of the instruction')
    fk_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='fk_user_instructions', 
        verbose_name='User', 
        help_text='The user associated with the instructions', 
        default=1)
    is_active = models.BooleanField(default=True, verbose_name='Active', help_text='Whether the finance is active or not')
    date_created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name='Date Created', help_text='The date the finance was created')
    last_updated = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name='Date Created', help_text='The date the finance was created')
    def __str__(self):
        return f"Instructions: {self.instruction}"
    class Meta:
        verbose_name_plural = 'Instructions'
    @receiver(post_save, sender=User)
    def create_instructions(sender, instance, created, **kwargs):
        if created:
            user = User.objects.get(pk=instance.pk)
            for data in data_instructions:
                Instructions.objects.create(
                    instruction=data.get('instruction'),
                    content=data.get('content'),
                    type=data.get('type', 1),
                    fk_user_id=user.id,
                    is_active=True
                )
    @receiver(post_save, sender=User)
    def save_instructions(sender, instance, **kwargs):
         for instructions in instance.fk_user_instructions.all():
            instructions.is_active = instance.is_active
            instructions.save()
