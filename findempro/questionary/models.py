from django.db import models
from django.utils import timezone
from product.models import Product
from business.models import Business
from variable.models import Variable
from django.db.models.signals import post_save
from django.dispatch import receiver
from .questionary_data import questionary_data,question_data
class QuestionaryResult(models.Model):
    answer = models.TextField()
    fk_product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='questionary_results', 
        null=True)
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.answer
class Questionary(models.Model):
    questionary = models.CharField(max_length=255)
    fk_business = models.ForeignKey(
        Business, 
        on_delete=models.CASCADE, 
        related_name='fk_business_questionary', 
        default=1)
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.questionary

@receiver(post_save, sender=Business)
def create_questionary(sender, instance, created, **kwargs):
    if created:
        for data in questionary_data:  # Assuming products_data is defined somewhere
            Questionary.objects.create(
                questionary=data['questionary'],
                fk_business=instance,
                is_active=True
            )

@receiver(post_save, sender=Product)
def save_questionary(sender, instance, **kwargs):
    Questionary.objects.update_or_create(
            fk_business=instance,
            defaults={'is_active': instance.is_active}
        )


class Question(models.Model):
    question = models.TextField()
    fk_questionary = models.ForeignKey(Questionary, on_delete=models.CASCADE, related_name='fk_questionary')
    type = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.question
    @receiver(post_save, sender=Questionary)
    def create_question(sender, instance, created, **kwargs):
        if created:
            for data in question_data:
                if question_data.type == 1:
                    Question.objects.create(
                        question=data['question'],
                        type=data['type'],                
                        fk_questionary=instance,
                        is_active=True
                    )
    @receiver(post_save, sender=Questionary)
    def save_question(sender, instance, **kwargs):
        instance.fk_questionary.all().update(is_active=instance.is_active)

class Answer(models.Model):
    answer = models.TextField()
    fk_question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='fk_question')
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.answer
