from django.db import models
from django.utils import timezone
from product.models import Product
from variable.models import Variable

class QuestionaryResult(models.Model):
    answer = models.TextField()
    fk_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='questionary_results', null=True)
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.answer

class Questionary(models.Model):
    questionary = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.questionary

class Question(models.Model):
    question = models.TextField()
    fk_questionary = models.ForeignKey(Questionary, on_delete=models.CASCADE, related_name='fk_questionary')
    # fk_variable = models.ForeignKey(Variable, on_delete=models.CASCADE, related_name='fk_variable')
    type = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.question

class Answer(models.Model):
    answer = models.TextField()
    fk_question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='fk_question')
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.answer
