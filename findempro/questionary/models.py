from django.db import models
from django.utils import timezone
from product.models import Product
from variable.models import Variable
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

    class Meta:
        indexes = [
            models.Index(fields=['fk_product', 'is_active'], name='idx_quest_prod_active'),
        ]

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
    last_updated = models.DateTimeField(auto_now=True, help_text='The date the question was last updated')

    class Meta:
        indexes = [
            models.Index(fields=['fk_questionary', 'is_active'], name='idx_questresult_q_active'),
        ]

    def __str__(self):
        return f"Resultado: {self.fk_questionary}"


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

    class Meta:
        indexes = [
            models.Index(fields=['fk_questionary', 'is_active'], name='idx_question_q_active'),
        ]

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

    class Meta:
        indexes = [
            models.Index(fields=['fk_questionary_result', 'is_active'], name='idx_answer_qresult_active'),
            models.Index(fields=['fk_question', 'is_active'], name='idx_answer_question_active'),
        ]

    def __str__(self):
        return self.answer
