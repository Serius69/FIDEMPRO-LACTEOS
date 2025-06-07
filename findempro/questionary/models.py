from django.db import models
from django.utils import timezone
from product.models import Product
from business.models import Business
from variable.models import Variable
from django.db.models.signals import post_save
from django.dispatch import receiver
from .data.questionary_data import questionary_data,question_data
from .data.questionary_result_data import questionary_result_data
from django.core.exceptions import MultipleObjectsReturned
from django.http import Http404
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
    possible_answers = models.JSONField(null=True, blank=True)
    is_active = models.BooleanField(default=True, help_text='The status of the question')
    date_created = models.DateTimeField(default=timezone.now, help_text='The date the question was created')
    last_updated = models.DateTimeField(default=timezone.now, help_text='The date the question was last updated')

    def __str__(self):
        return self.question

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
