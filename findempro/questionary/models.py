from django.db import models
from django.utils import timezone
from product.models import Product
from business.models import Business
from variable.models import Variable
from django.db.models.signals import post_save
from django.dispatch import receiver
from .questionary_data import questionary_data,question_data
from django.core.exceptions import MultipleObjectsReturned
class Questionary(models.Model):
    questionary = models.CharField(max_length=255)
    fk_product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='fk_product_questionary', 
        help_text='The product associated with the questionnaire',
        default=1)
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.questionary
    @receiver(post_save, sender=Product)
    def create_questionary(sender, instance, created, **kwargs):
        if created:
            for data in questionary_data:  # Assuming products_data is defined somewhere
                Questionary.objects.create(
                    questionary=f"{data['questionary']} {instance.name}",
                    fk_product=instance,
                    is_active=True
                )
    @receiver(post_save, sender=Product)
    def save_questionary(sender, instance, **kwargs):
        for questionary in instance.fk_product.fk_product_questionary.all():
            questionary.is_active = instance.is_active
            questionary.save()
class QuestionaryResult(models.Model):
    fk_questionary = models.ForeignKey(
        Questionary, 
        on_delete=models.CASCADE, 
        related_name='fk_questionary_questionary_result',
        help_text='The questionnaire associated with the question',
        default=1
        )
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now, help_text='The date the question was created')
    last_updated = models.DateTimeField(default=timezone.now, help_text='The date the question was last updated')

class Question(models.Model):
    question = models.TextField()
    fk_questionary = models.ForeignKey(
        Questionary, 
        on_delete=models.CASCADE, 
        related_name='fk_questionary_question',
        help_text='The questionnaire associated with the question'
        )
    fk_variable = models.ForeignKey(
        Variable, 
        on_delete=models.CASCADE, 
        related_name='fk_variable_question',
        help_text='The variable associated with the question'
        )
    type = models.IntegerField(default=1, help_text='The type of question')
    posible_answers = models.JSONField(null=True, blank=True)
    is_active = models.BooleanField(default=True, help_text='The status of the question')
    date_created = models.DateTimeField(default=timezone.now, help_text='The date the question was created')
    last_updated = models.DateTimeField(default=timezone.now, help_text='The date the question was last updated')

    def __str__(self):
        return self.question
    @receiver(post_save, sender=Questionary)
    def create_question(sender, instance, created, **kwargs):
        if created:
            for data in question_data:
                if data['type'] == 1: 
                    try:
                        variable = Variable.objects.get(initials=data['initials_variable'])
                    except MultipleObjectsReturned:
                        variable = Variable.objects.filter(initials=data['initials_variable']).first()
                    
                    Question.objects.create(
                        question=data['question'],
                        type=data['type'],
                        fk_questionary_id=instance.id,
                        fk_variable_id=variable.id,
                        is_active=True
                    )
    @receiver(post_save, sender=Questionary)
    def save_question(sender, instance, **kwargs):
        for question in instance.fk_questionary_question.all():
            question.is_active = instance.is_active
            question.save()
class Answer(models.Model):
    answer = models.TextField()
    fk_question = models.ForeignKey(
        Question, on_delete=models.CASCADE, 
        related_name='fk_question_answer', help_text='The question associated with the answer', default=1)
    fk_questionary_result = models.ForeignKey(
        QuestionaryResult, on_delete=models.CASCADE, related_name='fk_question_result_answer', 
        help_text='The questionary result associated with the answer', default=1)
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.answer
